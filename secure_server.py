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
        db = {"users": {}, "messages": {}, "typing": {}}
        return db
    with open(DB_FILE, "r") as f:
        db = json.load(f)
    if "users" not in db:
        db["users"] = {}
    if "messages" not in db:
        db["messages"] = {}
    if "typing" not in db:
        db["typing"] = {}
    # migrate old user structure (plain password string)
    for user, rec in list(db["users"].items()):
        if isinstance(rec, str):
            db["users"][user] = {"pw": rec, "strikes": 0, "locked_until": None}
    return db


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def password_valid(pw: str) -> bool:
    return len(pw) >= MIN_PASSWORD_LENGTH


def can_attempt_login(user_record: dict):
    locked_until = user_record.get("locked_until")
    if not locked_until:
        return True
    locked_dt = datetime.fromisoformat(locked_until)
    if datetime.now() >= locked_dt:
        user_record["locked_until"] = None
        user_record["strikes"] = 0
        return True
    return False


def record_failed_attempt(user_record: dict):
    strikes = user_record.get("strikes", 0) + 1
    user_record["strikes"] = strikes
    if strikes >= 3:
        lock_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        user_record["locked_until"] = lock_until.isoformat(timespec="seconds")
        user_record["strikes"] = 0
        return True, 3
    return False, strikes


def handle_client(conn, addr):
    log(f"New connection from {addr}")
    db = load_db()
    try:
        while True:
            data = conn.recv(65536)
            if not data:
                break
            try:
                req = json.loads(data.decode())
            except Exception:
                conn.send(b'{"ok": false, "error": "invalid_json"}')
                continue
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
                    resp = {"ok": False, "error": "no_such_user"}
                    conn.send(json.dumps(resp).encode())
                    continue
                if not can_attempt_login(rec):
                    resp = {"ok": False, "error": "locked_out"}
                    conn.send(json.dumps(resp).encode())
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
                        resp = {"ok": False, "error": "locked_after_3", "strike": strikes}
                    else:
                        resp = {"ok": False, "error": "bad_credentials", "strike": strikes}
                    conn.send(json.dumps(resp).encode())

            # -------- SEND TEXT MESSAGE --------
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

            # -------- SEND FILE (encrypted, stored) --------
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

            # -------- INBOX (marks read) --------
            elif action == "inbox":
                inbox_data = db["messages"].get(username, [])
                decrypted_msgs = []
                for msg in inbox_data:
                    kind = msg.get("kind", "text")
                    ts = msg.get("ts", "")
                    from_user = msg.get("from", "?")
                    if kind == "file":
                        filename = msg.get("filename", "(file)")
                        decrypted_text = f"[file] {filename} (stored securely)"
                    else:
                        try:
                            decrypted_text = fernet.decrypt(msg["msg"].encode()).decode()
                        except Exception:
                            decrypted_text = "[decrypt error]"
                    decrypted_msgs.append({
                        "from": from_user,
                        "msg": decrypted_text,
                        "timestamp": ts,
                        "read": msg.get("read", False),
                        "kind": kind
                    })
                for msg in inbox_data:
                    msg["read"] = True
                save_db(db)
                resp = {"ok": True, "messages": decrypted_msgs}
                conn.send(json.dumps(resp).encode())

            # -------- CONVERSATIONS SUMMARY --------
            elif action == "conversations":
                inbox_data = db["messages"].get(username, [])
                conv = {}
                for msg in inbox_data:
                    sender = msg.get("from", "?")
                    ts = msg.get("ts", "")
                    read_flag = msg.get("read", False)
                    if sender not in conv:
                        conv[sender] = {
                            "total": 0,
                            "unread": 0,
                            "last_ts": "",
                            "last_preview": ""
                        }
                    conv[sender]["total"] += 1
                    if not read_flag:
                        conv[sender]["unread"] += 1
                    if not conv[sender]["last_ts"] or ts > conv[sender]["last_ts"]:
                        kind = msg.get("kind", "text")
                        if kind == "file":
                            preview = f"[file] {msg.get('filename', '(file)')}"
                        else:
                            try:
                                preview = fernet.decrypt(msg["msg"].encode()).decode()
                            except Exception:
                                preview = "[decrypt error]"
                        conv[sender]["last_ts"] = ts
                        conv[sender]["last_preview"] = preview
                conversations = []
                for sender, info in conv.items():
                    conversations.append({
                        "peer": sender,
                        "total": info["total"],
                        "unread": info["unread"],
                        "last_ts": info["last_ts"],
                        "last_preview": info["last_preview"]
                    })
                resp = {"ok": True, "conversations": conversations}
                conn.send(json.dumps(resp).encode())

            # -------- FULL CONVERSATION DETAIL (for chat window) --------
            elif action == "conversation_detail":
                if not username:
                    resp = {"ok": False, "error": "not_logged_in"}
                    conn.send(json.dumps(resp).encode())
                    continue
                peer = payload.get("peer")
                if not peer:
                    resp = {"ok": False, "error": "missing_peer"}
                    conn.send(json.dumps(resp).encode())
                    continue
                if peer not in db["users"]:
                    resp = {"ok": False, "error": "no_such_user"}
                    conn.send(json.dumps(resp).encode())
                    continue

                history = []

                # inbound messages (peer -> username)
                for msg in db["messages"].get(username, []):
                    if msg.get("from") == peer:
                        ts = msg.get("ts", "")
                        kind = msg.get("kind", "text")
                        if kind == "file":
                            filename = msg.get("filename", "(file)")
                            text = f"[file] {filename} (stored securely)"
                        else:
                            try:
                                text = fernet.decrypt(msg["msg"].encode()).decode()
                            except Exception:
                                text = "[decrypt error]"
                        history.append({
                            "from": peer,
                            "to": username,
                            "msg": text,
                            "timestamp": ts,
                            "kind": kind,
                            "filename": msg.get("filename")
                        })

                # outbound messages (username -> peer)
                for msg in db["messages"].get(peer, []):
                    if msg.get("from") == username:
                        ts = msg.get("ts", "")
                        kind = msg.get("kind", "text")
                        if kind == "file":
                            filename = msg.get("filename", "(file)")
                            text = f"[file] {filename} (stored securely)"
                        else:
                            try:
                                text = fernet.decrypt(msg["msg"].encode()).decode()
                            except Exception:
                                text = "[decrypt error]"
                        history.append({
                            "from": username,
                            "to": peer,
                            "msg": text,
                            "timestamp": ts,
                            "kind": kind,
                            "filename": msg.get("filename")
                        })

                try:
                    history.sort(key=lambda m: m.get("timestamp", ""))
                except Exception:
                    pass

                # mark inbound read
                for msg in db["messages"].get(username, []):
                    if msg.get("from") == peer:
                        msg["read"] = True
                save_db(db)

                resp = {"ok": True, "history": history}
                conn.send(json.dumps(resp).encode())

            # -------- DELETE CONVERSATION (both sides) --------
            elif action == "delete_conversation":
                if not username:
                    resp = {"ok": False, "error": "not_logged_in"}
                    conn.send(json.dumps(resp).encode())
                    continue
                peer = payload.get("peer")
                if not peer:
                    resp = {"ok": False, "error": "missing_peer"}
                    conn.send(json.dumps(resp).encode())
                    continue
                # remove from username inbox
                msgs_u = db["messages"].get(username, [])
                msgs_u = [m for m in msgs_u if m.get("from") != peer]
                db["messages"][username] = msgs_u
                # remove from peer inbox where sender == username
                msgs_p = db["messages"].get(peer, [])
                msgs_p = [m for m in msgs_p if m.get("from") != username]
                db["messages"][peer] = msgs_p
                save_db(db)
                log(f"Conversation cleared between {username} and {peer}")
                resp = {"ok": True}
                conn.send(json.dumps(resp).encode())

            # -------- SEARCH MESSAGES --------
            elif action == "search":
                if not username:
                    resp = {"ok": False, "error": "not_logged_in"}
                    conn.send(json.dumps(resp).encode())
                    continue
                query = (payload.get("query") or "").lower()
                if not query:
                    resp = {"ok": False, "error": "empty_query"}
                    conn.send(json.dumps(resp).encode())
                    continue

                results = []

                # inbound (to username)
                for msg in db["messages"].get(username, []):
                    kind = msg.get("kind", "text")
                    if kind != "text":
                        continue
                    try:
                        text = fernet.decrypt(msg["msg"].encode()).decode()
                    except Exception:
                        continue
                    if query in text.lower():
                        results.append({
                            "from": msg.get("from", "?"),
                            "to": username,
                            "msg": text,
                            "timestamp": msg.get("ts", "")
                        })

                # outbound (from username to others)
                for other, inbox in db["messages"].items():
                    if other == username:
                        continue
                    for msg in inbox:
                        if msg.get("from") != username:
                            continue
                        kind = msg.get("kind", "text")
                        if kind != "text":
                            continue
                        try:
                            text = fernet.decrypt(msg["msg"].encode()).decode()
                        except Exception:
                            continue
                        if query in text.lower():
                            results.append({
                                "from": username,
                                "to": other,
                                "msg": text,
                                "timestamp": msg.get("ts", "")
                            })

                try:
                    results.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
                except Exception:
                    pass

                resp = {"ok": True, "results": results}
                conn.send(json.dumps(resp).encode())

            # -------- TYPING INDICATOR (update state) --------
            elif action == "typing":
                if not username:
                    resp = {"ok": False, "error": "not_logged_in"}
                    conn.send(json.dumps(resp).encode())
                    continue
                peer = payload.get("peer")
                is_typing = bool(payload.get("is_typing"))
                if not peer:
                    resp = {"ok": False, "error": "missing_peer"}
                    conn.send(json.dumps(resp).encode())
                    continue
                db["typing"].setdefault(peer, {})
                db["typing"][peer][username] = {
                    "typing": is_typing,
                    "ts": datetime.now().isoformat(timespec="seconds")
                }
                save_db(db)
                resp = {"ok": True}
                conn.send(json.dumps(resp).encode())

            # -------- TYPING STATUS (read state) --------
            elif action == "typing_status":
                if not username:
                    resp = {"ok": False, "error": "not_logged_in"}
                    conn.send(json.dumps(resp).encode())
                    continue
                peer = payload.get("peer")
                if not peer:
                    resp = {"ok": False, "error": "missing_peer"}
                    conn.send(json.dumps(resp).encode())
                    continue
                state = db["typing"].get(username, {}).get(peer)
                typing_now = False
                if state and state.get("typing"):
                    try:
                        ts = datetime.fromisoformat(state.get("ts"))
                        if (datetime.now() - ts).total_seconds() < 8:
                            typing_now = True
                    except Exception:
                        pass
                resp = {"ok": True, "typing": typing_now}
                conn.send(json.dumps(resp).encode())

            # -------- UNKNOWN --------
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
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    main()
