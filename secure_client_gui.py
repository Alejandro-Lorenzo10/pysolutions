import socket
import json
import os
import base64
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from tkinter import ttk
from datetime import datetime

HOST = "127.0.0.1"
PORT = 7777

SETTINGS_FILE = "settings.json"


def send_request(action: str, username: str | None, data: dict | None = None) -> dict:
    payload = {
        "action": action,
        "username": username,
        "data": data or {},
    }
    try:
        with socket.create_connection((HOST, PORT)) as sock:
            sock.sendall(json.dumps(payload).encode("utf-8"))
            resp_bytes = sock.recv(65536)
            if not resp_bytes:
                return {"ok": False, "error": "no_response"}
            return json.loads(resp_bytes.decode("utf-8"))
    except OSError as e:
        return {"ok": False, "error": f"connection_error: {e}"}
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json_response"}


class SecureDMApp:
    def __init__(self, master):
        self.master = master
        self.master.title("🥧PYchat🥧")

        self.username: str | None = None

        # ========== SETTINGS / THEME ==========
        self.settings = self.load_settings()

        self.ACCENT_COLORS = {
            "royal_blue": ("Royal Blue", "#4169E1"),
            "emerald_green": ("Emerald Green", "#2ECC71"),
            "tech_purple": ("Tech Purple", "#9B59B6"),
            "hot_pink": ("Hot Pink", "#FF69B4"),
        }
        self.FONT_SIZES = {
            "small": 9,
            "medium": 10,
            "large": 11,
        }

        self.apply_settings_to_theme_vars()

        self.master.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use("default")

        self.style.configure(
            "TLabel",
            background=self.bg_color,
            foreground=self.text_fg,
            font=("Helvetica", self.font_size),
        )
        self.style.configure(
            "Accent.TButton",
            padding=6,
            font=("Helvetica", self.font_size, "bold"),
            foreground="white",
        )
        self.style.configure(
            "TLabelframe",
            background=self.section_bg,
            foreground=self.text_fg,
            font=("Helvetica", self.font_size, "bold"),
        )
        self.style.configure(
            "TLabelframe.Label",
            background=self.section_bg,
            foreground=self.text_fg,
            font=("Helvetica", self.font_size, "bold"),
        )

        # ===== HEADER =====
        self.header_frame = tk.Frame(self.master, bg=self.header_color, height=55)
        self.header_frame.pack(fill="x")

        self.title_label = tk.Label(
            self.header_frame,
            text="🥧PYchat🥧",
            fg=self.header_text,
            bg=self.header_color,
            font=("Helvetica", 17, "bold"),
            pady=10,
        )
        self.title_label.pack(side="left", padx=12, pady=4)

        self.header_right = tk.Frame(self.header_frame, bg=self.header_color)
        self.header_right.pack(side="right", padx=10)

        self.settings_btn = tk.Button(
            self.header_right,
            text="⚙️ Settings",
            bg=self.header_color,
            fg=self.header_text,
            bd=0,
            font=("Helvetica", self.font_size),
            activebackground=self.header_color,
            activeforeground=self.header_text,
            cursor="hand2",
            command=self.open_settings_window,
        )
        self.settings_btn.pack(side="right", padx=4, pady=8)

        self.logout_btn = tk.Button(
            self.header_right,
            text="Logout",
            bg=self.header_color,
            fg=self.header_text,
            bd=0,
            font=("Helvetica", self.font_size),
            activebackground=self.header_color,
            activeforeground=self.header_text,
            cursor="hand2",
            command=self.logout_user,
        )
        self.logout_btn.pack(side="right", padx=4, pady=8)

        self.user_label = tk.Label(
            self.header_right,
            text="",
            bg=self.header_color,
            fg=self.header_text,
            font=("Helvetica", self.font_size, "bold"),
        )
        self.user_label.pack(side="right", padx=4, pady=8)

        # hide user + logout until logged in
        self.user_label.pack_forget()
        self.logout_btn.pack_forget()

        # ===== MAIN AREA =====
        self.main_frame = tk.Frame(self.master, bg=self.bg_color)
        self.main_frame.pack(padx=15, pady=10, fill="both", expand=True)

        # --- Account box (LOGIN PAGE) ---
        self.acc_box = ttk.Labelframe(self.main_frame, text="Account")
        self.acc_box.pack(fill="x", pady=(0, 10))

        ttk.Label(self.acc_box, text="Username:").grid(row=0, column=0, sticky="e", pady=3, padx=4)
        self.username_entry = ttk.Entry(self.acc_box, width=20)
        self.username_entry.grid(row=0, column=1, padx=6, pady=3)

        ttk.Label(self.acc_box, text="Password:").grid(row=1, column=0, sticky="e", pady=3, padx=4)
        self.password_entry = ttk.Entry(self.acc_box, width=20, show="*")
        self.password_entry.grid(row=1, column=1, padx=6, pady=3)

        self.register_btn = ttk.Button(self.acc_box, text="Register", command=self.register_user, style="Accent.TButton")
        self.register_btn.grid(row=0, column=2, padx=6)
        self.login_btn = ttk.Button(self.acc_box, text="Login", command=self.login_user, style="Accent.TButton")
        self.login_btn.grid(row=1, column=2, padx=6)

        # --- Message box (CHAT UI, hidden until login) ---
        self.msg_box = ttk.Labelframe(self.main_frame, text="Send Message")

        ttk.Label(self.msg_box, text="To:").grid(row=0, column=0, sticky="e", pady=3, padx=4)
        self.to_entry = ttk.Entry(self.msg_box, width=20)
        self.to_entry.grid(row=0, column=1, padx=6)

        ttk.Label(self.msg_box, text="Message:").grid(row=1, column=0, sticky="e", pady=3, padx=4)
        self.msg_entry = ttk.Entry(self.msg_box, width=45)
        self.msg_entry.grid(row=1, column=1, padx=6)

        self.send_btn = ttk.Button(self.msg_box, text="Send", command=self.send_message, style="Accent.TButton")
        self.send_btn.grid(row=1, column=2, padx=8)

        # --- Inbox / conversations (CHAT UI, hidden until login) ---
        self.inbox_box = ttk.Labelframe(self.main_frame, text="Inbox / Conversations")

        self.inbox_btn = ttk.Button(self.inbox_box, text="Inbox", command=self.load_inbox, style="Accent.TButton")
        self.inbox_btn.grid(row=0, column=0, padx=5, pady=6)

        self.conv_btn = ttk.Button(self.inbox_box, text="Conversations", command=self.load_conversations, style="Accent.TButton")
        self.conv_btn.grid(row=0, column=1, padx=5, pady=6)

        self.chat_btn = ttk.Button(self.inbox_box, text="Open Chat", command=self.open_chat_with_peer, style="Accent.TButton")
        self.chat_btn.grid(row=0, column=2, padx=5, pady=6)

        self.search_btn = ttk.Button(self.inbox_box, text="Search", command=self.open_search_window, style="Accent.TButton")
        self.search_btn.grid(row=0, column=3, padx=5, pady=6)

        self.output = scrolledtext.ScrolledText(
            self.inbox_box,
            width=85,
            height=18,
            state="disabled",
            font=("Menlo", self.font_size),
        )
        self.output.grid(row=1, column=0, columnspan=6, pady=10, padx=4)

        # START: only login visible (chat UI hidden)
        self.hide_chat_ui()

        self.append_output("• Secure DM Client ready. Make sure secure_server.py is running.")

        # Status bar
        self.status_bar = tk.Label(
            self.master,
            text="Status: Idle",
            bg=self.header_color,
            fg=self.header_text,
            anchor="w",
            padx=10,
            font=("Helvetica", self.font_size),
        )
        self.status_bar.pack(fill="x")

        self.apply_theme_to_widgets()
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    # ========== SETTINGS / THEME ==========
    def default_settings(self) -> dict:
        return {
            "theme": "light",
            "accent": "royal_blue",
            "font_size": "medium",
        }

    def load_settings(self) -> dict:
        if not os.path.exists(SETTINGS_FILE):
            return self.default_settings()
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            return self.default_settings()
        defaults = self.default_settings()
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        return data

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass

    def apply_settings_to_theme_vars(self):
        theme = self.settings.get("theme", "light")
        accent_key = self.settings.get("accent", "royal_blue")
        font_size_key = self.settings.get("font_size", "medium")

        accent_hex = self.ACCENT_COLORS.get(accent_key, ("Royal Blue", "#4169E1"))[1]

        if theme == "dark":
            # Discord-style dark
            self.bg_color = "#2C2F33"
            self.header_color = "#23272A"
            self.header_text = accent_hex  # header text = same blue as accent
            self.section_bg = "#2C2F33"
            self.output_bg = "#23272A"
            self.output_fg = "#FFFFFF"
            self.text_fg = "#FFFFFF"
        else:
            # Light + navy
            self.bg_color = "#F7F7F7"
            self.header_color = "#0D1B2A"
            self.header_text = accent_hex  # header text = same blue as accent
            self.section_bg = "#FFFFFF"
            self.output_bg = "#FFFFFF"
            self.output_fg = "#000000"
            self.text_fg = "#000000"

        self.accent_color = accent_hex
        self.font_size = self.FONT_SIZES.get(font_size_key, 10)

    def apply_theme_to_widgets(self):
        self.master.configure(bg=self.bg_color)
        self.header_frame.configure(bg=self.header_color)
        self.title_label.configure(bg=self.header_color, fg=self.header_text)
        self.header_right.configure(bg=self.header_color)
        for btn in (self.settings_btn, self.logout_btn):
            btn.configure(
                bg=self.header_color,
                fg=self.header_text,
                activebackground=self.header_color,
                activeforeground=self.header_text,
            )
        self.user_label.configure(bg=self.header_color, fg=self.header_text)

        self.main_frame.configure(bg=self.bg_color)
        self.style.configure("TLabelframe", background=self.section_bg, foreground=self.text_fg)
        self.style.configure("TLabelframe.Label", background=self.section_bg, foreground=self.text_fg)
        self.style.configure(
            "TLabel",
            background=self.bg_color,
            foreground=self.text_fg,
            font=("Helvetica", self.font_size),
        )
        self.style.configure(
            "Accent.TButton",
            background=self.accent_color,
            foreground="white",
            font=("Helvetica", self.font_size, "bold"),
        )
        self.output.configure(
            bg=self.output_bg,
            fg=self.output_fg,
            insertbackground=self.output_fg,
            font=("Menlo", self.font_size),
        )
        self.status_bar.configure(
            bg=self.header_color,
            fg=self.header_text,
            font=("Helvetica", self.font_size),
        )

    def open_settings_window(self):
        win = tk.Toplevel(self.master)
        win.title("Settings")
        win.configure(bg=self.bg_color)
        win.resizable(False, False)
        self.center_window_over_parent(win, width=380, height=220)

        tk.Label(win, text="Theme:", bg=self.bg_color, fg=self.text_fg,
                 font=("Helvetica", self.font_size)).grid(row=0, column=0, sticky="e", padx=8, pady=8)
        tk.Label(win, text="Accent color:", bg=self.bg_color, fg=self.text_fg,
                 font=("Helvetica", self.font_size)).grid(row=1, column=0, sticky="e", padx=8, pady=8)
        tk.Label(win, text="Font size:", bg=self.bg_color, fg=self.text_fg,
                 font=("Helvetica", self.font_size)).grid(row=2, column=0, sticky="e", padx=8, pady=8)

        theme_values = ["Light (Navy Blue)", "Dark (Discord)"]
        self.theme_var = tk.StringVar()
        self.theme_box = ttk.Combobox(win, textvariable=self.theme_var, values=theme_values,
                                      state="readonly", width=22)
        self.theme_box.grid(row=0, column=1, padx=8, pady=8)
        if self.settings["theme"] == "dark":
            self.theme_var.set("Dark (Discord)")
        else:
            self.theme_var.set("Light (Navy Blue)")

        accent_values = [v[0] for v in self.ACCENT_COLORS.values()]
        self.accent_var = tk.StringVar()
        self.accent_box = ttk.Combobox(win, textvariable=self.accent_var, values=accent_values,
                                       state="readonly", width=22)
        self.accent_box.grid(row=1, column=1, padx=8, pady=8)
        cur_key = self.settings.get("accent", "royal_blue")
        cur_label = self.ACCENT_COLORS[cur_key][0]
        self.accent_var.set(cur_label)

        font_values = ["Small", "Medium", "Large"]
        self.font_var = tk.StringVar()
        self.font_box = ttk.Combobox(win, textvariable=self.font_var, values=font_values,
                                     state="readonly", width=22)
        self.font_box.grid(row=2, column=1, padx=8, pady=8)
        if self.settings["font_size"] == "small":
            self.font_var.set("Small")
        elif self.settings["font_size"] == "large":
            self.font_var.set("Large")
        else:
            self.font_var.set("Medium")

        btn_frame = tk.Frame(win, bg=self.bg_color)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=16)

        save_btn = ttk.Button(btn_frame, text="Save & Apply", style="Accent.TButton",
                              command=lambda: self.save_settings_from_ui(win))
        save_btn.grid(row=0, column=0, padx=6)
        reset_btn = ttk.Button(btn_frame, text="Reset to Default", style="Accent.TButton",
                               command=lambda: self.reset_settings(win))
        reset_btn.grid(row=0, column=1, padx=6)
        close_btn = ttk.Button(btn_frame, text="Close", command=win.destroy)
        close_btn.grid(row=0, column=2, padx=6)

    def save_settings_from_ui(self, win: tk.Toplevel):
        t = self.theme_var.get()
        self.settings["theme"] = "dark" if "Dark" in t else "light"

        label = self.accent_var.get()
        for key, (lbl, _) in self.ACCENT_COLORS.items():
            if lbl == label:
                self.settings["accent"] = key
                break

        f = self.font_var.get()
        if f == "Small":
            self.settings["font_size"] = "small"
        elif f == "Large":
            self.settings["font_size"] = "large"
        else:
            self.settings["font_size"] = "medium"

        self.save_settings()
        self.apply_settings_to_theme_vars()
        self.apply_theme_to_widgets()
        self.set_status("Settings applied")
        win.destroy()

    def reset_settings(self, win: tk.Toplevel):
        self.settings = self.default_settings()
        self.save_settings()
        self.apply_settings_to_theme_vars()
        self.apply_theme_to_widgets()
        self.set_status("Settings reset")

        if self.settings["theme"] == "dark":
            self.theme_var.set("Dark (Discord)")
        else:
            self.theme_var.set("Light (Navy Blue)")

        cur_key = self.settings.get("accent", "royal_blue")
        cur_label = self.ACCENT_COLORS[cur_key][0]
        self.accent_var.set(cur_label)

        if self.settings["font_size"] == "small":
            self.font_var.set("Small")
        elif self.settings["font_size"] == "large":
            self.font_var.set("Large")
        else:
            self.font_var.set("Medium")

    def center_window_over_parent(self, win: tk.Toplevel, width: int, height: int):
        self.master.update_idletasks()
        px = self.master.winfo_rootx()
        py = self.master.winfo_rooty()
        pw = self.master.winfo_width()
        ph = self.master.winfo_height()
        x = px + (pw - width) // 2
        y = py + (ph - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")

    # ========== UI SHOW/HIDE (LOGIN PAGE vs CHAT UI) ==========
    def show_chat_ui(self):
        """Show the Send Message + Inbox sections after login."""
        if not self.msg_box.winfo_manager():
            self.msg_box.pack(fill="x", pady=(0, 10))
        if not self.inbox_box.winfo_manager():
            self.inbox_box.pack(fill="both", expand=True)

    def hide_chat_ui(self):
        """Hide chat UI (used at startup and on logout)."""
        self.msg_box.pack_forget()
        self.inbox_box.pack_forget()

    # ========== GENERAL HELPERS ==========
    def set_status(self, text: str):
        self.status_bar.configure(text=f"Status: {text}")

    def append_output(self, text: str):
        self.output.config(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.config(state="disabled")

    def format_friendly_time(self, ts: str) -> str:
        if not ts:
            return ""
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            return ts
        now = datetime.now()
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            m = seconds // 60
            return f"{m} minute(s) ago"
        if delta.days == 0:
            return dt.strftime("Today %I:%M %p").lstrip("0")
        if delta.days == 1:
            return dt.strftime("Yesterday %I:%M %p").lstrip("0")
        if delta.days < 7:
            return dt.strftime("%A %I:%M %p").lstrip("0")
        return dt.strftime("%Y-%m-%d %I:%M %p").lstrip("0")

    # ========== ACCOUNT ==========
    def register_user(self):
        user = self.username_entry.get().strip()
        pw = self.password_entry.get().strip()
        if not user or not pw:
            messagebox.showwarning("Missing info", "Please enter username and password.")
            return
        resp = send_request("register", None, {"user": user, "pw": pw})
        if resp.get("ok"):
            self.append_output(f"✔ Registered {user}")
            self.set_status("User registered")
        else:
            err = resp.get("error")
            if err == "pw_too_short":
                messagebox.showerror("Password too short", "Password must be at least 6 characters.")
            elif err == "user_exists":
                messagebox.showerror("User exists", "Username already taken.")
            else:
                messagebox.showerror("Registration failed", str(err))
            self.append_output("✘ " + str(err))
            self.set_status("Registration failed")

    def login_user(self):
        user = self.username_entry.get().strip()
        pw = self.password_entry.get().strip()
        if not user or not pw:
            messagebox.showwarning("Missing info", "Please enter username and password.")
            return
        resp = send_request("login", None, {"user": user, "pw": pw})
        if resp.get("ok"):
            self.username = user
            self.append_output(f"✔ Logged in as {user}")
            self.set_status("Logged in")

            # hide login box, show chat UI
            self.acc_box.pack_forget()
            self.show_chat_ui()

            self.user_label.configure(text=f"User: {user}")
            self.user_label.pack(side="right", padx=4, pady=8)
            self.logout_btn.pack(side="right", padx=4, pady=8)
        else:
            err = resp.get("error")
            strike = resp.get("strike")
            if err in ("locked_out", "locked_after_3"):
                msg = "Too many failed login attempts.\nYoooou're out!! 🔒\n\nYour account is locked for 10 minutes."
                messagebox.showerror("Account locked", msg)
                self.append_output("✘ locked_out")
            elif err == "bad_credentials":
                if strike in (1, 2):
                    messagebox.showerror(
                        "Login failed",
                        f"Strike {strike}/3: Incorrect password."
                    )
                    self.append_output(f"✘ bad_credentials (strike {strike}/3)")
                else:
                    messagebox.showerror("Login failed", "Incorrect password.")
                    self.append_output("✘ bad_credentials")
            elif err == "no_such_user":
                messagebox.showerror("Login failed", "User does not exist.")
                self.append_output("✘ no_such_user")
            else:
                messagebox.showerror("Login failed", str(err))
                self.append_output("✘ " + str(err))
            self.set_status("Login failed")

    def logout_user(self):
        if not self.username:
            return
        self.username = None
        self.set_status("Logged out")
        self.append_output("• Logged out. Please log in again.")
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.user_label.pack_forget()
        self.logout_btn.pack_forget()

        # hide chat UI and show only login box again
        self.hide_chat_ui()
        self.acc_box.pack(fill="x", pady=(0, 10))

    # ========== MESSAGING ==========
    def send_message(self):
        if not self.username:
            messagebox.showwarning("Not logged in", "Please log in first.")
            return
        to_user = self.to_entry.get().strip()
        msg = self.msg_entry.get().strip()
        if not to_user or not msg:
            messagebox.showwarning("Missing info", "Enter a recipient and a message.")
            return
        resp = send_request("send", self.username, {"to": to_user, "msg": msg})
        if resp.get("ok"):
            self.append_output(f"✔ Message sent to {to_user}")
            self.set_status("Message sent")
            self.msg_entry.delete(0, "end")
        else:
            self.append_output("✘ " + str(resp.get("error")))
            self.set_status("Send failed")

    # ========== INBOX / CONVERSATIONS ==========
    def load_inbox(self):
        if not self.username:
            messagebox.showwarning("Not logged in", "Please log in first.")
            return
        resp = send_request("inbox", self.username, {})
        if not resp.get("ok"):
            self.append_output("✘ " + str(resp.get("error")))
            return
        messages = resp.get("messages", [])
        if not messages:
            self.append_output("• Inbox: (empty)")
            return
        self.append_output("• Inbox:")
        for i, msg in enumerate(messages, start=1):
            sender = msg.get("from", "?")
            text = msg.get("msg", "")
            ts = msg.get("timestamp", "")
            friendly = self.format_friendly_time(ts)
            self.append_output(f"  {i}. [{friendly}] from {sender}: {text}")

    def load_conversations(self):
        if not self.username:
            messagebox.showwarning("Not logged in", "Please log in first.")
            return
        resp = send_request("conversations", self.username, {})
        if not resp.get("ok"):
            self.append_output("✘ " + str(resp.get("error")))
            return
        conversations = resp.get("conversations", [])
        if not conversations:
            self.append_output("• No conversations yet")
            return
        self.append_output("• Conversations:")
        for i, conv in enumerate(conversations, start=1):
            peer = conv.get("peer", "?")
            total = conv.get("total", 0)
            unread = conv.get("unread", 0)
            last_ts = conv.get("last_ts", "")
            preview = conv.get("last_preview", "")
            friendly = self.format_friendly_time(last_ts) if last_ts else ""
            self.append_output(
                f"  {i}. {peer} | total: {total}, unread: {unread}, last: {friendly}"
            )
            if preview:
                self.append_output(f"       last msg: {preview}")

    # ========== SEARCH ==========
    def open_search_window(self):
        if not self.username:
            messagebox.showwarning("Not logged in", "Please log in first.")
            return
        win = tk.Toplevel(self.master)
        win.title("Search Messages")
        win.configure(bg=self.bg_color)
        self.center_window_over_parent(win, width=600, height=400)

        tk.Label(win, text="Keyword:", bg=self.bg_color, fg=self.text_fg,
                 font=("Helvetica", self.font_size)).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        query_entry = tk.Entry(win, width=30)
        query_entry.grid(row=0, column=1, padx=6, pady=6)

        result_box = scrolledtext.ScrolledText(
            win,
            width=70,
            height=18,
            state="disabled",
            font=("Menlo", self.font_size),
            bg=self.output_bg,
            fg=self.output_fg,
            insertbackground=self.output_fg,
        )
        result_box.grid(row=1, column=0, columnspan=3, padx=8, pady=8)

        def do_search():
            q = query_entry.get().strip()
            if not q:
                messagebox.showwarning("Missing info", "Type a keyword to search.")
                return
            resp = send_request("search", self.username, {"query": q})
            if not resp.get("ok"):
                messagebox.showerror("Search error", str(resp.get("error")))
                return
            results = resp.get("results", [])
            result_box.config(state="normal")
            result_box.delete("1.0", "end")
            if not results:
                result_box.insert("end", "No results found.\n")
            else:
                for r in results:
                    frm = r.get("from", "?")
                    to = r.get("to", "?")
                    msg = r.get("msg", "")
                    ts = r.get("timestamp", "")
                    friendly = self.format_friendly_time(ts)
                    result_box.insert("end", f"[{friendly}] {frm} → {to}: {msg}\n")
            result_box.config(state="disabled")

        search_btn = ttk.Button(win, text="Search", style="Accent.TButton", command=do_search)
        search_btn.grid(row=0, column=2, padx=6, pady=6)

        query_entry.bind("<Return>", lambda e: do_search())

    # ========== CHAT WINDOW (AUTO-REFRESH, TYPING, FILES, CLEAR, EXPORT) ==========
    def open_chat_with_peer(self):
        if not self.username:
            messagebox.showwarning("Not logged in", "Please log in first.")
            return
        peer = self.to_entry.get().strip()
        if not peer:
            messagebox.showwarning("Missing info", "Type a username in 'To:' first.")
            return

        resp = send_request("conversation_detail", self.username, {"peer": peer})
        if not resp.get("ok"):
            messagebox.showerror("Chat error", str(resp.get("error")))
            return

        history = resp.get("history", [])

        win = tk.Toplevel(self.master)
        win.title(f"Chat with {peer}")
        win.configure(bg=self.bg_color)
        self.center_window_over_parent(win, width=650, height=480)

        chat_text = scrolledtext.ScrolledText(
            win,
            width=72,
            height=18,
            state="normal",
            font=("Menlo", self.font_size),
            bg=self.output_bg,
            fg=self.output_fg,
            insertbackground=self.output_fg,
        )
        chat_text.pack(padx=10, pady=(10, 5), fill="both", expand=True)

        history_holder = {"history": history}

        def render_history():
            chat_text.config(state="normal")
            chat_text.delete("1.0", "end")
            for msg in history_holder["history"]:
                sender = msg.get("from", "?")
                text = msg.get("msg", "")
                ts = msg.get("timestamp", "")
                friendly = self.format_friendly_time(ts)
                label = "You" if sender == self.username else sender
                chat_text.insert("end", f"[{friendly}] {label}: {text}\n")
            chat_text.config(state="disabled")

        render_history()

        bottom_frame = tk.Frame(win, bg=self.bg_color)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        entry = tk.Entry(bottom_frame, width=40)
        entry.grid(row=0, column=0, padx=4)

        typing_label = tk.Label(
            bottom_frame,
            text="",
            bg=self.bg_color,
            fg=self.text_fg,
            font=("Helvetica", self.font_size - 1),
        )
        typing_label.grid(row=1, column=0, columnspan=4, sticky="w", padx=4, pady=(2, 0))

        def refresh_history():
            resp_r = send_request("conversation_detail", self.username, {"peer": peer})
            if not resp_r.get("ok"):
                return
            history_holder["history"] = resp_r.get("history", [])
            render_history()

        def send_from_chat(event=None):
            msg = entry.get().strip()
            if not msg:
                return
            resp2 = send_request("send", self.username, {"to": peer, "msg": msg})
            if resp2.get("ok"):
                entry.delete(0, "end")
                send_request("typing", self.username, {"peer": peer, "is_typing": False})
                refresh_history()
            else:
                messagebox.showerror("Send failed", str(resp2.get("error")))

        send_btn = ttk.Button(bottom_frame, text="Send", style="Accent.TButton", command=send_from_chat)
        send_btn.grid(row=0, column=1, padx=4)

        def send_file():
            if not self.username:
                return
            filepath = filedialog.askopenfilename(parent=win, title="Choose file to send")
            if not filepath:
                return
            try:
                with open(filepath, "rb") as f:
                    data = f.read()
                content_b64 = base64.b64encode(data).decode("utf-8")
                filename = os.path.basename(filepath)
                respf = send_request(
                    "send_file",
                    self.username,
                    {"to": peer, "filename": filename, "content_b64": content_b64},
                )
                if respf.get("ok"):
                    messagebox.showinfo("File sent", f"Encrypted file sent to {peer}:\n{filename}")
                    refresh_history()
                else:
                    messagebox.showerror("File send failed", str(respf.get("error")))
            except Exception as e:
                messagebox.showerror("File error", str(e))

        file_btn = ttk.Button(bottom_frame, text="Send File", style="Accent.TButton", command=send_file)
        file_btn.grid(row=0, column=2, padx=4)

        def clear_conversation():
            if messagebox.askyesno(
                "Clear conversation",
                f"Delete all messages between you and {peer}?\nThis cannot be undone.",
            ):
                respd = send_request("delete_conversation", self.username, {"peer": peer})
                if respd.get("ok"):
                    history_holder["history"] = []
                    render_history()
                    messagebox.showinfo("Cleared", "Conversation cleared.")
                else:
                    messagebox.showerror("Delete failed", str(respd.get("error")))

        clear_btn = ttk.Button(bottom_frame, text="Clear Chat", command=clear_conversation)
        clear_btn.grid(row=0, column=3, padx=4)

        def export_chat():
            default_name = f"chat_{self.username}_with_{peer}.txt"
            filepath = filedialog.asksaveasfilename(
                parent=win,
                title="Export conversation to TXT",
                defaultextension=".txt",
                initialfile=default_name,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if not filepath:
                return
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    for msg in history_holder["history"]:
                        sender = msg.get("from", "?")
                        text = msg.get("msg", "")
                        ts = msg.get("timestamp", "")
                        friendly = self.format_friendly_time(ts)
                        label = "You" if sender == self.username else sender
                        f.write(f"[{friendly}] {label}: {text}\n")
                messagebox.showinfo("Exported", f"Conversation saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export failed", str(e))

        export_btn = ttk.Button(bottom_frame, text="Export to TXT", command=export_chat)
        export_btn.grid(row=0, column=4, padx=4)

        def poll_typing_and_refresh():
            # auto-refresh chat history (live-ish)
            refresh_history()
            # typing indicator
            resp_t = send_request("typing_status", self.username, {"peer": peer})
            if resp_t.get("ok") and resp_t.get("typing"):
                typing_label.config(text=f"{peer} is typing...")
            else:
                typing_label.config(text="")
            if win.winfo_exists():
                win.after(3000, poll_typing_and_refresh)

        def on_keypress(event):
            if entry.get().strip() or event.char.strip():
                send_request("typing", self.username, {"peer": peer, "is_typing": True})

        def on_focus_out(event):
            send_request("typing", self.username, {"peer": peer, "is_typing": False})

        entry.bind("<Return>", send_from_chat)
        entry.bind("<KeyPress>", on_keypress)
        entry.bind("<FocusOut>", on_focus_out)

        poll_typing_and_refresh()

    # ========== CLOSE ==========
    def on_close(self):
        self.master.destroy()


def main():
    root = tk.Tk()
    app = SecureDMApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
