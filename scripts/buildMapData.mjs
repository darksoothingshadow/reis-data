// Splits the pinned MENDELU map snapshot into:
//   - per-building room geometry  -> reis-data/map/rooms-<id>.geojson   (served via CDN)
//   - bundled meta (buildings/pois/rooms-index) -> ../reis-extension/src/data/map/
//   - curated data (landmarks/remotePlaces) copied verbatim -> same bundle dir
// The curated inputs (source/mendelu-landmarks.json, source/mendelu-remote-places.json)
// are NOT fetched by fetch-mendelu-map.py — landmark footprints are OSM-sourced +
// enriched with SKM contact info, and the remote places are off-campus (outside the
// Brno-campus API). reis-data is their single source of truth; the extension just
// bundles the copies this script emits. Edit them here, then rerun this script.
// Run: node scripts/buildMapData.mjs   (from the reis-data repo root)
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const ext = resolve(root, '..', 'reis-extension', 'src', 'data', 'map');
const read = (p) => JSON.parse(readFileSync(resolve(root, p), 'utf8'));

const buildings = read('source/mendelu-buildings.json');
const rooms = read('source/mendelu-rooms.geojson');
const pois = read('source/mendelu-pois.geojson');

const buildingIds = new Set(buildings.buildings.map((b) => b.id));
const buildingNames = new Set(buildings.buildings.map((b) => b.name)); // "A".."X"

// 1) Per-building room geometry -> CDN dir
mkdirSync(resolve(root, 'map'), { recursive: true });
for (const id of buildingIds) {
  const fc = { type: 'FeatureCollection',
    features: rooms.features.filter((f) => f.properties.buildingId === id) };
  writeFileSync(resolve(root, `map/rooms-${id}.geojson`), JSON.stringify(fc));
}

// 2) Lightweight room search index (no geometry) -> bundled
mkdirSync(ext, { recursive: true });
const index = rooms.features
  .filter((f) => f.properties.category !== 'structure' && (f.properties.name || '').trim() !== '')
  .map((f) => {
    const p = f.properties;
    return { code: p.passportNumber ?? p.name, name: p.name, nickname: p.nickname ?? null,
      buildingId: p.buildingId, floorId: p.floorId, floorLevel: p.floorLevel, placeId: p.id };
  });
writeFileSync(resolve(ext, 'rooms-index.json'), JSON.stringify(index));

// 3) Bundled buildings meta (verbatim) + POIs with academic-building duplicates removed
writeFileSync(resolve(ext, 'buildings.json'), JSON.stringify(buildings));
const cleanPois = { type: 'FeatureCollection',
  features: pois.features.filter((f) => {
    const t = f.properties.type, n = f.properties.name;
    // drop the academic-building pins (drawn as footprints already)
    return !(t === 'indoor_building' || (t === 'building' && buildingNames.has(n)));
  }) };
writeFileSync(resolve(ext, 'pois.json'), JSON.stringify(cleanPois));

// 4) Curated map data (landmarks + off-campus remote places) copied verbatim.
// These are hand-maintained here (not derived from the API), so preserve exact
// bytes/formatting rather than parse+reserialize.
copyFileSync(resolve(root, 'source/mendelu-landmarks.json'), resolve(ext, 'landmarks.json'));
copyFileSync(resolve(root, 'source/mendelu-remote-places.json'), resolve(ext, 'remotePlaces.json'));

console.log(
  `buildings=${buildings.buildings.length} pois=${cleanPois.features.length} index=${index.length} +landmarks +remotePlaces`
);
