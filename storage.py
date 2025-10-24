# storage.py
import json
from pathlib import Path
from threading import Lock

class Storage:
    """
    Simple thread-safe JSON key-value store.
    Example keys:
      - "user:erika" -> { ... }
      - "items:erika" -> ["homework", "buy milk"]
    """
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get(self, key: str, default=None):
        with self.lock:
            data = self._read()
            return data.get(key, default)

    def set(self, key: str, value) -> None:
        with self.lock:
            data = self._read()
            data[key] = value
            self._write(data)

    def delete(self, key: str) -> None:
        with self.lock:
            data = self._read()
            if key in data:
                del data[key]
                self._write(data)
