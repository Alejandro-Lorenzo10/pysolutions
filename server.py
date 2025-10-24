import json, logging, socket, threading
from pathlib import Path
from auth import AuthManager
from storage import Storage

HOST, PORT = "127.0.0.1", 7777

# logging
LOG_DIR = Path("logs"); LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=LOG_DIR/"server.log", level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# deps
USERS = AuthManager(Path("data/users.json"))
STORE = Storage(Path("data/store.json"))   # keys like items:<username>

def send(conn, obj): conn.sendall(json.dumps(obj).encode("utf-8"))

def handle(conn, addr):
    logging.info(f"Client connected: {addr}")
    with conn:
        while True:
            raw = conn.recv(65536)
            if not raw: break
            try:
                req = json.loads(raw.decode("utf-8"))
            except Exception:
                send(conn, {"ok": False, "error": "invalid_json"}); continue

            action = req.get("action"); data = req.get("data", {}); username = req.get("username")

            if action == "ping":
                send(conn, {"ok": True, "data": {"pong": True}}); continue

            if action == "register":
                ok, err = USERS.register(data.get("username"), data.get("password"))
                logging.info(f"register {data.get('username')} -> {ok}")
                send(conn, {"ok": ok, "data": {"registered": ok}, "error": err}); continue

            if action == "login":
                ok = USERS.verify(data.get("username"), data.get("password"))
                logging.info(f"login {data.get('username')} -> {ok}")
                send(conn, {"ok": ok, "data": {"login": ok}, "error": None if ok else "bad_credentials"}); continue

            # auth required below
            if not username:
                send(conn, {"ok": False, "error": "auth_required"}); continue

            if action == "add":
                item = data.get("item")
                if not item: send(conn, {"ok": False, "error": "missing_item"}); continue
                key = f"items:{username}"
                items = STORE.get(key, [])
                items.append(item)
                STORE.set(key, items)
                logging.info(f"add {username}: {item}")
                send(conn, {"ok": True, "data": {"added": item}}); continue

            if action == "list":
                key = f"items:{username}"
                items = STORE.get(key, [])
                send(conn, {"ok": True, "data": {"items": items}}); continue

            if action == "remove":
                item = data.get("item")
                key = f"items:{username}"
                items = STORE.get(key, [])
                if item in items:
                    items.remove(item)
                    STORE.set(key, items)
                    logging.info(f"remove {username}: {item}")
                    send(conn, {"ok": True, "data": {"removed": item}})
                else:
                    send(conn, {"ok": False, "error": "not_found"})
                continue

            if action == "help":
                send(conn, {"ok": True, "data": {"commands": [
                    "register <u> <p>", "login <u> <p>",
                    "add <item>", "list", "remove <item>", "help", "exit"
                ]}}); continue

            send(conn, {"ok": False, "error": "unknown_action"})

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT)); s.listen()
        logging.info(f"Server listening on {HOST}:{PORT}")
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    start_server()
