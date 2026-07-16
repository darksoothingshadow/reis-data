#!/usr/bin/env python3
"""
fetch-mendelu-map.py
--------------------
Regenerates the reIS indoor-map datasets from the public My MENDELU map API.

Source API (no auth, public; undocumented internal endpoint — treat as such):
    https://api.mm.mendelu.cz/v1/map/buildings/   -> building footprints + floor ids
    https://api.mm.mendelu.cz/v1/map/floors/      -> floors (level, building, name)
    https://api.mm.mendelu.cz/v1/map/places/      -> 9k+ places (rooms, corridors,
                                                     walls/doors, + exterior pins)

Outputs (written next to this script):
    mendelu-rooms.geojson      FeatureCollection of room/corridor polygons (7 buildings)
    mendelu-buildings.json     building + floor metadata, outlines, campus bounds
    mendelu-pois.geojson       exterior point places (dorms, FRRMS, sports, tram, gates…)

Run:  python3 fetch-mendelu-map.py
Refresh whenever MENDELU updates the underlying survey.
"""
import json, urllib.request, os, sys

API = "https://api.mm.mendelu.cz/v1/map"
HERE = os.path.dirname(os.path.abspath(__file__))

# type -> (display category, human label).  Categories drive the room colours in reIS.
CATEGORY = {
    "classroom_and_laboratory": ("teaching", "Classroom / lab"),
    "boardroom": ("teaching", "Boardroom"), "study_room": ("teaching", "Study room"),
    "library": ("teaching", "Library"),
    "office": ("office", "Office"), "department": ("office", "Department"),
    "room": ("other", "Room"), "empty": ("other", "Room"),
    "toilet": ("service", "Toilet"), "toilet_female": ("service", "Toilet (W)"),
    "toilet_male": ("service", "Toilet (M)"), "toilet_handicapped": ("service", "Toilet (accessible)"),
    "storage": ("service", "Storage"), "utility_room": ("service", "Utility"),
    "kitchen": ("service", "Kitchen"), "coatroom": ("service", "Cloakroom"),
    "engine_room": ("service", "Engine room"), "shaft": ("service", "Shaft"),
    "archive": ("service", "Archive"), "bistro": ("service", "Bistro"),
    "garage": ("service", "Garage"), "gatehouse": ("service", "Gatehouse"),
    "locker": ("service", "Lockers"), "shower": ("service", "Shower"),
    "sink": ("service", "Sink"), "bathroom": ("service", "Bathroom"),
    "preparatory": ("service", "Preparatory"),
    "stairs": ("circulation", "Stairs"), "emergency_stairs": ("circulation", "Emergency stairs"),
    "elevator": ("circulation", "Elevator"), "lobby": ("circulation", "Lobby"),
    "terrace": ("circulation", "Terrace"),
    "floor": ("structure", "Corridor"), "emergency_floor": ("structure", "Corridor"),
    "ground": ("structure", "Corridor"), "walk": ("structure", "Walkway"),
}
# Micro-detail dropped from the display dataset (kept in the raw API if you ever want routing):
DROP = {"wall", "door", "window_frame", "base", "outline"}
# Building display order
ORDER = {n: i for i, n in enumerate("A B C E M Q X".split())}


def get(path):
    req = urllib.request.Request(f"{API}/{path}", headers={"User-Agent": "reIS-map-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def cz(p, k):
    return ((p.get("localizedAttributes", {}) or {}).get("cz", {}) or {}).get(k)


def ring(pts):
    r = [[round(v["lon"], 6), round(v["lat"], 6)] for v in pts]
    if r and r[0] != r[-1]:
        r.append(r[0])
    return r


def main():
    print("Fetching buildings / floors / places …", file=sys.stderr)
    buildings = get("buildings/")["items"]
    floors = get("floors/")["items"]
    places = get("places/")["items"]
    fl_by_id = {f["id"]: f for f in floors}

    # ---- rooms.geojson ----
    feats = []
    for p in places:
        bid = p.get("buildingId")
        if bid is None:
            continue
        t = p.get("type")
        if t in DROP:
            continue
        pts = p.get("position") or []
        if len(pts) < 3:
            continue
        cat, label = CATEGORY.get(t, ("other", (t or "Space").replace("_", " ")))
        fl = fl_by_id.get(p.get("floorId"))
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring(pts)]},
            "properties": {
                "id": p["id"],
                "buildingId": bid,
                "floorId": p.get("floorId"),
                "floorLevel": fl["level"] if fl else None,
                "name": cz(p, "name") or "",
                # Human hall label ("A01" for BA01N1052). For most buildings the
                # `name` above is just the passport code and this nickname carries
                # the friendly name; for PEF (Q) it's the reverse. reIS resolves
                # the display label from both (see roomLabel in the extension).
                "nickname": cz(p, "nickname") or None,
                "type": t,
                "category": cat,
                "label": label,
                "passportNumber": p.get("passportNumber"),  # JOIN KEY to IS pasportizace
                "seats": p.get("numberOfSeats"),
                "hasProjector": bool(p.get("computerWithProjector")),
                "hasWhiteboard": bool(p.get("whiteboard")),
                "code": p.get("code"),
            },
        })
    rooms_fc = {"type": "FeatureCollection", "features": feats}

    # ---- buildings.json (meta + outlines + campus bounds) ----
    all_lat, all_lon = [], []
    bmeta = []
    for b in buildings:
        out = sorted(b.get("outline", []), key=lambda v: v["order"])
        oring = ring(out)
        lat = [c[1] for c in oring]
        lon = [c[0] for c in oring]
        all_lat += lat
        all_lon += lon
        fls = sorted([f for f in floors if f["buildingId"] == b["id"]], key=lambda f: -f["level"])
        flist = [{
            "id": f["id"], "level": f["level"], "name": cz(f, "name"),
            "roomCount": sum(1 for ft in feats
                             if ft["properties"]["buildingId"] == b["id"]
                             and ft["properties"]["floorId"] == f["id"]
                             and ft["properties"]["category"] != "structure"),
        } for f in fls]
        default = next((f["id"] for f in fls if f["level"] == 0),
                       flist[len(flist) // 2]["id"] if flist else None)
        bmeta.append({
            "id": b["id"], "name": cz(b, "name"), "description": cz(b, "description"),
            "outline": {"type": "Polygon", "coordinates": [oring]},  # GeoJSON [lon,lat]
            "center": [sum(lat) / len(lat), sum(lon) / len(lon)],     # [lat,lon]
            "bounds": [[min(lat), min(lon)], [max(lat), max(lon)]],   # [[S,W],[N,E]]
            "defaultFloorId": default,
            "floors": flist,
        })
    bmeta.sort(key=lambda x: ORDER.get(x["name"], 99))
    buildings_meta = {
        "buildings": bmeta,
        "campus": {
            "bounds": [[min(all_lat), min(all_lon)], [max(all_lat), max(all_lon)]],
            "center": [sum(all_lat) / len(all_lat), sum(all_lon) / len(all_lon)],
        },
    }

    # ---- pois.geojson (exterior points: dorms, FRRMS, sports, tram, gates, parking…) ----
    pois = []
    for p in places:
        if p.get("buildingId") is not None:
            continue
        pts = p.get("position") or []
        if not pts:
            continue
        pois.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(pts[0]["lon"], 6), round(pts[0]["lat"], 6)]},
            "properties": {
                "id": p["id"], "name": cz(p, "name") or "", "type": p.get("type"),
                "url": p.get("url"), "phone": p.get("phone"), "email": p.get("email"),
            },
        })
    pois_fc = {"type": "FeatureCollection", "features": pois}

    def dump(name, obj):
        path = os.path.join(HERE, name)
        json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print(f"  wrote {name}  ({os.path.getsize(path):,} B)", file=sys.stderr)

    dump("mendelu-rooms.geojson", rooms_fc)
    dump("mendelu-buildings.json", buildings_meta)
    dump("mendelu-pois.geojson", pois_fc)
    print(f"Done: {len(feats)} room features, {len(bmeta)} buildings, {len(pois)} POIs.", file=sys.stderr)


if __name__ == "__main__":
    main()
