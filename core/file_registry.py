"""File registry for duplicate detection based on path + file size."""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

REGISTRY_PATH = Path.home() / ".assetreflector" / "import_registry.json"


@dataclass
class FileRecord:
    source_path: str
    file_size: int
    mtime: float
    imported_at: str  # ISO format datetime


class FileRegistry:
    def __init__(self):
        self._records: dict[str, FileRecord] = {}  # key: "abs_path|size"
        self._load()

    def _load(self):
        try:
            if REGISTRY_PATH.exists():
                with open(REGISTRY_PATH, encoding="utf-8") as f:
                    data = json.load(f)
                    for key, rec in data.items():
                        self._records[key] = FileRecord(**rec)
        except (json.JSONDecodeError, Exception):
            self._records = {}

    def _save(self):
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump({k: asdict(v) for k, v in self._records.items()}, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _make_key(abs_path: str, size: int) -> str:
        return f"{abs_path}|{size}"

    def is_duplicate(self, filepath: Path) -> bool:
        """Check if a file has been previously imported.
        Strategy: match by absolute path + file size, or by filename + file size."""
        try:
            size = filepath.stat().st_size
        except OSError:
            return False

        # Exact match: same absolute path + same size
        abs_key = self._make_key(str(filepath.resolve()), size)
        if abs_key in self._records:
            return True

        # Heuristic: same filename + same size (detects renamed/moved duplicates)
        target_name = filepath.name
        for rec in self._records.values():
            if rec.file_size == size and Path(rec.source_path).name == target_name:
                return True

        return False

    def find_duplicates(self, filepaths: list[Path]) -> list[Path]:
        """Return a list of files that have been previously imported."""
        return [p for p in filepaths if self.is_duplicate(p)]

    def register_files(self, filepaths: list[Path]):
        """Record a list of files as imported."""
        for p in filepaths:
            try:
                resolve_path = str(p.resolve())
                size = p.stat().st_size
                key = self._make_key(resolve_path, size)
                self._records[key] = FileRecord(
                    source_path=str(p),
                    file_size=size,
                    mtime=p.stat().st_mtime,
                    imported_at=datetime.now().isoformat(),
                )
            except OSError:
                pass
        self._save()