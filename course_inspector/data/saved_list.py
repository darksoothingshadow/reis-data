import json
from pathlib import Path


class SavedEntry:
    """One saved course: its code and an optional user note."""

    def __init__(self, code: str, note: str = ""):
        self.code = code
        self.note = note


class SavedList:
    """Persists a list of saved courses with notes to a JSON file."""

    def __init__(self, path: Path):
        self._path = path
        self._entries: list[SavedEntry] = []
        self._load()

    def add(self, code: str) -> None:
        if not any(e.code == code for e in self._entries):
            self._entries.append(SavedEntry(code))
            self._save()

    def remove(self, code: str) -> None:
        self._entries = [e for e in self._entries if e.code != code]
        self._save()

    def set_note(self, code: str, note: str) -> None:
        for entry in self._entries:
            if entry.code == code:
                entry.note = note
                self._save()
                return

    def get_all(self) -> list[SavedEntry]:
        return list(self._entries)

    def contains(self, code: str) -> bool:
        return any(e.code == code for e in self._entries)

    def get_note(self, code: str) -> str:
        for entry in self._entries:
            if entry.code == code:
                return entry.note
        return ""

    def _load(self) -> None:
        if self._path.exists():
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._entries = [SavedEntry(d["code"], d.get("note", "")) for d in data]

    def _save(self) -> None:
        data = [{"code": e.code, "note": e.note} for e in self._entries]
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
