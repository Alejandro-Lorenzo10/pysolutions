# 🥧PYchat🥧

PYchat is a secure direct-messaging (DM) app built in Python with a Tkinter GUI.

It uses a client–server architecture:

- **Server (`secure_server.py`)** – handles user accounts, logins, messages, conversations, search, typing status, and file sending.
- **Client (`secure_client_gui.py`)** – a desktop chat app with login/register, inbox, conversations view, live-ish chat window, search, theme settings, and file attachments.

You can run it directly with Python, or build standalone Mac apps with PyInstaller.

---

## ✨ Main Features

- User **registration & login** with basic lockout  
- **Private DMs**  
- **Inbox** with unread count and last message preview  
- **Chat window** with live-ish auto refresh  
- **Typing indicator**  
- **Search** messages  
- **File sending** (base64)  
- **Clear chat**  
- **Export chat to .txt**  
- **Themes & font sizes**  
- **Bigger chat window & improved readability**  
- Desktop-style UI (Tkinter)

---

## 🧱 Project Structure

```text
pysolutions/
├── secure_server.py          # Server (run this first)
├── secure_client_gui.py      # GUI client (PYchat)
├── README.md                 # This file
└── requirements.txt          # Python dependencies
