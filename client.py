import json
import socket
from colorama import Fore, Style, init as color_init
from utils import ok, err, info, prompt, ALIASES
from help_menu import HELP_TEXT

color_init(autoreset=True)

HOST = "127.0.0.1"
PORT = 7777

def send(sock, payload: dict):
    sock.sendall(json.dumps(payload).encode("utf-8"))
    raw = sock.recv(65536)
    return json.loads(raw.decode("utf-8"))

def make_request(action: str, username: str | None = None, data: dict | None = None) -> dict:
    return {"action": action, "username": username, "data": data or {}}

def main():
    username = None
    with socket.create_connection((HOST, PORT)) as sock:
        info("Connected. Type 'help' for commands.")
        while True:
            try:
                raw = input(prompt(username))
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not raw.strip():
                continue

            parts = raw.strip().split()
            cmd, args = ALIASES.get(parts[0], parts[0]), parts[1:]

            if cmd == "exit":
                info("Bye!")
                break

            if cmd == "help":
                print(HELP_TEXT)
                continue

            if cmd == "register":
                if len(args) != 2:
                    err("Usage: register <username> <password>")
                    continue
                resp = send(sock, make_request("register", None, {"username": args[0], "password": args[1]}))
                ok("Registered") if resp.get("ok") else err(resp.get("error"))
                continue

            if cmd == "login":
                if len(args) != 2:
                    err("Usage: login <username> <password>")
                    continue
                resp = send(sock, make_request("login", None, {"username": args[0], "password": args[1]}))
                if resp.get("ok"):
                    username = args[0]
                    ok("Logged in")
                else:
                    err("bad_credentials")
                continue

            if cmd == "add":
                if not username:
                    err("Please login first")
                    continue
                if not args:
                    err("Usage: add <item>")
                    continue
                item = " ".join(args)
                resp = send(sock, make_request("add", username, {"item": item}))
                ok(f"Added: {item}") if resp.get("ok") else err(resp.get("error"))
                continue

            if cmd == "list":
                if not username:
                    err("Please login first")
                    continue
                resp = send(sock, make_request("list", username))
                if resp.get("ok"):
                    items = resp["data"]["items"]
                    if items:
                        for i, it in enumerate(items, 1):
                            print(f"{i}. {it}")
                    else:
                        info("(no items)")
                else:
                    err(resp.get("error"))
                continue

            if cmd == "remove":
                if not username:
                    err("Please login first")
                    continue
                if not args:
                    err("Usage: remove <item>")
                    continue
                item = " ".join(args)
                resp = send(sock, make_request("remove", username, {"item": item}))
                ok(f"Removed: {item}") if resp.get("ok") else err(resp.get("error"))
                continue

            err("Unknown command. Type 'help'.")

if __name__ == "__main__":
    main()
