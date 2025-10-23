import json
import hashlib
from pathlib import Path
from threading import Lock

class AuthManager:
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

    @staticmethod
    def _hash(pw: str) -> str:
        return hashlib.sha256(pw.encode("utf-8")).hexdigest()

    def register(self, username: str, password: str):
        if not username or not password:
            return False, "missing_username_or_password"
        with self.lock:
            users = self._read()
            if username in users:
                return False, "user_exists"
            users[username] = {"hash": self._hash(password)}
            self._write(users)
            return True, None

    def verify(self, username: str, password: str) -> bool:
        with self.lock:
            users = self._read()
            u = users.get(username)
            if not u:
                return False
            return u.get("hash") == self._hash(password)
