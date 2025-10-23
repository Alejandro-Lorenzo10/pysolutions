import json
from pathlib import Path
from threading import Lock

class Storage:
    def __init__(self, path: Path):
        self.path = path
        self.lock = Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self):
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get(self, key, default=None):
        with self.lock:
            data = self._read()
            return data.get(key, default)

    def set(self, key, value):
        with self.lock:
            data = self._read()
            data[key] = value
            self._write(data)

    def delete(self, key):
        with self.lock:
            data = self._read()
            if key in data:
                del data[key]
                self._write(data)
