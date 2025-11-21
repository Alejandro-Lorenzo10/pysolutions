import socket
import threading
import json
from cryptography.fernet import Fernet
import os
from datetime import datetime, timedelta

HOST = "127.0.0.1"
PORT = 7777

DB_FILE = "secure_db.json"
KEY_FILE = "secret.key"
LOG_FILE = "server_log.txt"

LOCKOUT_MINUTES = 10
MIN_PASSWORD_LENGTH = 6


def log(msg: str):
    ts = datetime.now().isoformat(timespec="seconds")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")


def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        log("Generated new secret.key")
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)


fernet = load_key()


def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "messages": {}, "typing": {}}

    with open(DB_FILE, "r") as f:
        db = json.load(f)

    db.setdefault("users", {})
    db.setdefault("messages", {})
    db.setdefault("typing", {})

    # migrate old user structure
    for u, rec in list(db["users"].items()):
        if isinstance(rec, str):
            db["users"][u] = {"pw": rec, "strikes": 0, "locked_until": None}

    return db


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def password_valid(pw: str) -> bool:
    return len(pw) >= MIN_PASSWORD_LENGTH


def can_attempt_login(rec: dict):
    locked_until = rec.get("locked_until")
    if not locked_until:
        return True
    locked_dt = datetime.fromisoformat(locked_until)
    if datetime.now() >= locked_dt:
        rec["locked_until"] = None
        rec["strikes"] = 0
        return True
    return False


def record_failed_attempt(rec: dict):
    strikes = rec.get("strikes", 0) + 1
    rec["strikes"] = strikes
    if strikes >= 3:
        lock_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        rec["locked_until"] = lock_until.isoformat(timespec="seconds")
        rec["strikes"] = 0
        return True, 3
    return False, strikes


# ====================================================================== #
#                           FIXED CLIENT HANDLER                         #
# ====================================================================== #

def handle_client(conn, addr):
    log(f"New connection from {addr}")
    db = load_db()

    try:
        while True:
            data = conn.recv(65536)
            if not data:
                break

            # ignore whitespace packets
            if len(data.strip()) == 0:
                continue

            try:
                decoded = data.decode()
            except UnicodeDecodeError:
                log("Non-text binary data ignored")
                continue

            try:
                req = json.loads(decoded)
            except json.JSONDecodeError:
                log(f"Invalid JSON from client: {decoded!r}")
                continue  # do NOT send error back

            action = req.get("action")
            username = req.get("username")
            payload = req.get("data", {})

            # -------- REGISTER --------
            if action == "register":
                user = payload.get("user")
                pw = payload.get("pw")

                if not user or not pw:
                    conn.send(b'{"ok": false, "error": "missing_fields"}')
                    continue

                if not password_valid(pw):
                    conn.send(b'{"ok": false, "error": "pw_too_short"}')
                    continue

                if user in db["users"]:
                    conn.send(b'{"ok": false, "error": "user_exists"}')
                    continue

                db["users"][user] = {"pw": pw, "strikes": 0, "locked_until": None}
                db["messages"].setdefault(user, [])

                save_db(db)
                log(f"User registered: {user}")
                conn.send(b'{"ok": true}')

            # -------- LOGIN --------
            elif action == "login":
                user = payload.get("user")
                pw = payload.get("pw")

                rec = db["users"].get(user)
                if not rec:
                    conn.send(b'{"ok": false, "error": "no_such_user"}')
                    continue

                if not can_attempt_login(rec):
                    conn.send(b'{"ok": false, "error": "locked_out"}')
                    continue

                if rec["pw"] == pw:
                    rec["strikes"] = 0
                    rec["locked_until"] = None
                    save_db(db)
                    log(f"User logged in: {user}")
                    conn.send(b'{"ok": true}')
                else:
                    locked, strikes = record_failed_attempt(rec)
                    save_db(db)
                    if locked:
                        log(f"User locked out: {user}")
                        resp = {"ok": False, "error": "locked_after_3"}
                    else:
                        resp = {"ok": False, "error": "bad_credentials", "strike": strikes}
                    conn.send(json.dumps(resp).encode())

            # -------- SEND TEXT --------
            elif action == "send":
                sender = username
                receiver = payload.get("to")
                message = payload.get("msg")

                if not sender or not receiver or not message:
                    conn.send(b'{"ok": false, "error": "missing_fields"}')
                    continue

                if receiver not in db["users"]:
                    conn.send(b'{"ok": false, "error": "no_such_user"}')
                    continue

                encrypted = fernet.encrypt(message.encode()).decode()
                ts = datetime.now().isoformat(timespec="seconds")

                db["messages"].setdefault(receiver, []).append({
                    "from": sender,
                    "msg": encrypted,
                    "ts": ts,
                    "read": False,
                    "kind": "text"
                })

                save_db(db)
                log(f"Message sent: {sender} -> {receiver}")
                conn.send(b'{"ok": true}')

            # -------- SEND FILE --------
            elif action == "send_file":
                sender = username
                receiver = payload.get("to")
                filename = payload.get("filename")
                content_b64 = payload.get("content_b64")

                if not sender or not receiver or not filename or not content_b64:
                    conn.send(b'{"ok": false, "error": "missing_fields"}')
                    continue

                if receiver not in db["users"]:
                    conn.send(b'{"ok": false, "error": "no_such_user"}')
                    continue

                encrypted = fernet.encrypt(content_b64.encode()).decode()
                ts = datetime.now().isoformat(timespec="seconds")

                db["messages"].setdefault(receiver, []).append({
                    "from": sender,
                    "msg": encrypted,
                    "ts": ts,
                    "read": False,
                    "kind": "file",
                    "filename": filename
                })

                save_db(db)
                log(f"File sent: {sender} -> {receiver} ({filename})")
                conn.send(b'{"ok": true}')

            # -------- INBOX --------
            elif action == "inbox":
                inbox_data = db["messages"].get(username, [])
                out = []

                for msg in inbox_data:
                    kind = msg.get("kind", "text")
                    ts = msg.get("ts")
                    from_user = msg.get("from")

                    if kind == "file":
                        decrypted = f"[file] {msg.get('filename')}"
                    else:
                        try:
                            decrypted = fernet.decrypt(msg["msg"].encode()).decode()
                        except Exception:
                            decrypted = "[decrypt error]"

                    out.append({
                        "from": from_user,
                        "msg": decrypted,
                        "timestamp": ts,
                        "kind": kind
                    })

                for msg in inbox_data:
                    msg["read"] = True

                save_db(db)

                conn.send(json.dumps({"ok": True, "messages": out}).encode())

            # -------- CONVERSATIONS SUMMARY --------
            elif action == "conversations":
                inbox_data = db["messages"].get(username, [])
                conv = {}

                for msg in inbox_data:
                    sender = msg.get("from")
                    ts = msg.get("ts")
                    read_flag = msg.get("read", False)

                    conv.setdefault(sender, {
                        "total": 0,
                        "unread": 0,
                        "last_ts": "",
                        "last_preview": ""
                    })

                    conv[sender]["total"] += 1
                    if not read_flag:
                        conv[sender]["unread"] += 1

                    if not conv[sender]["last_ts"] or ts > conv[sender]["last_ts"]:
                        kind = msg.get("kind", "text")
                        if kind == "file":
                            preview = f"[file] {msg.get('filename')}"
                        else:
                            try:
                                preview = fernet.decrypt(msg["msg"].encode()).decode()
                            except:
                                preview = "[decrypt error]"

                        conv[sender]["last_ts"] = ts
                        conv[sender]["last_preview"] = preview

                convs = []
                for sender, info in conv.items():
                    convs.append({
                        "peer": sender,
                        "total": info["total"],
                        "unread": info["unread"],
                        "last_ts": info["last_ts"],
                        "last_preview": info["last_preview"]
                    })

                conn.send(json.dumps({"ok": True, "conversations": convs}).encode())

            # -------- FULL CONVERSATION DETAIL --------
            elif action == "conversation_detail":
                peer = payload.get("peer")
                if not peer:
                    conn.send(b'{"ok": false, "error": "missing_peer"}')
                    continue

                if peer not in db["users"]:
                    conn.send(b'{"ok": false, "error": "no_such_user"}')
                    continue

                history = []

                # inbound (peer → username)
                for msg in db["messages"].get(username, []):
                    if msg.get("from") == peer:
                        ts = msg.get("ts")
                        kind = msg.get("kind", "text")

                        if kind == "file":
                            text = f"[file] {msg.get('filename')}"
                        else:
                            try:
                                text = fernet.decrypt(msg["msg"].encode()).decode()
                            except:
                                text = "[decrypt error]"

                        history.append({
                            "from": peer,
                            "to": username,
                            "msg": text,
                            "timestamp": ts,
                            "kind": kind,
                            "filename": msg.get("filename")
                        })

                # outbound (username → peer)
                for msg in db["messages"].get(peer, []):
                    if msg.get("from") == username:
                        ts = msg.get("ts")
                        kind = msg.get("kind", "text")

                        if kind == "file":
                            text = f"[file] {msg.get('filename')}"
                        else:
                            try:
                                text = fernet.decrypt(msg["msg"].encode()).decode()
                            except:
                                text = "[decrypt error]"

                        history.append({
                            "from": username,
                            "to": peer,
                            "msg": text,
                            "timestamp": ts,
                            "kind": kind,
                            "filename": msg.get("filename")
                        })

                # sort by timestamp
                try:
                    history.sort(key=lambda m: m["timestamp"])
                except:
                    pass

                # mark inbound read
                for msg in db["messages"].get(username, []):
                    if msg.get("from") == peer:
                        msg["read"] = True

                save_db(db)

                conn.send(json.dumps({"ok": True, "history": history}).encode())

            # -------- DELETE CONVERSATION --------
            elif action == "delete_conversation":
                peer = payload.get("peer")
                if not peer:
                    conn.send(b'{"ok": false, "error": "missing_peer"}')
                    continue

                # remove inbound
                msgs_u = db["messages"].get(username, [])
                msgs_u = [m for m in msgs_u if m.get("from") != peer]
                db["messages"][username] = msgs_u

                # remove outbound
                msgs_p = db["messages"].get(peer, [])
                msgs_p = [m for m in msgs_p if m.get("from") != username]
                db["messages"][peer] = msgs_p

                save_db(db)
                log(f"Conversation cleared between {username} and {peer}")

                conn.send(b'{"ok": true}')

            # -------- SEARCH --------
            elif action == "search":
                query = (payload.get("query") or "").lower()
                if not query:
                    conn.send(b'{"ok": false, "error": "empty_query"}')
                    continue

                results = []

                # inbound
                for msg in db["messages"].get(username, []):
                    if msg.get("kind") != "text":
                        continue
                    try:
                        text = fernet.decrypt(msg["msg"].encode()).decode()
                    except:
                        continue

                    if query in text.lower():
                        results.append({
                            "from": msg.get("from"),
                            "to": username,
                            "msg": text,
                            "timestamp": msg.get("ts")
                        })

                # outbound
                for other, inbox in db["messages"].items():
                    if other == username:
                        continue
                    for msg in inbox:
                        if msg.get("from") != username:
                            continue
                        if msg.get("kind") != "text":
                            continue
                        try:
                            text = fernet.decrypt(msg["msg"].encode()).decode()
                        except:
                            continue

                        if query in text.lower():
                            results.append({
                                "from": username,
                                "to": other,
                                "msg": text,
                                "timestamp": msg.get("ts")
                            })

                try:
                    results.sort(key=lambda m: m["timestamp"], reverse=True)
                except:
                    pass

                conn.send(json.dumps({"ok": True, "results": results}).encode())

            # -------- SET TYPING --------
            elif action == "typing":
                peer = payload.get("peer")
                is_typing = bool(payload.get("is_typing"))

                db["typing"].setdefault(peer, {})
                db["typing"][peer][username] = {
                    "typing": is_typing,
                    "ts": datetime.now().isoformat(timespec="seconds")
                }

                save_db(db)
                conn.send(b'{"ok": true}')

            # -------- GET TYPING STATUS --------
            elif action == "typing_status":
                peer = payload.get("peer")
                state = db["typing"].get(username, {}).get(peer)

                typing_now = False
                if state and state.get("typing"):
                    try:
                        ts = datetime.fromisoformat(state["ts"])
                        if (datetime.now() - ts).total_seconds() < 8:
                            typing_now = True
                    except:
                        pass

                conn.send(json.dumps({"ok": True, "typing": typing_now}).encode())

            # -------- UNKNOWN ACTION --------
            else:
                conn.send(b'{"ok": false, "error": "unknown_action"}')

    finally:
        conn.close()
        log(f"Disconnected: {addr}")


def main():
    log("Server started")
    print(f"[server] Listening on {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
