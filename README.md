# 🥧PYchat🥧

PYchat is a secure direct-messaging (DM) app built in Python with a Tkinter GUI.

It uses a client–server architecture:

- **Server (`secure_server.py`)** – handles user accounts, logins, messages, conversations, search, typing status, and file sending.
- **Client (`secure_client_gui.py`)** – a desktop chat app with login/register, inbox, conversations view, live-ish chat window, search, theme settings, and file attachments.

You can run it directly with Python, or build standalone Mac apps with PyInstaller so it works on machines without Python installed.

---

## ✨ Main Features

- User **registration & login** with basic lockout after failed attempts
- **Private DMs** between users
- **Inbox** view and **conversation list** (totals, unread, last message time)
- **Chat window** with live-ish auto refresh
- **Typing indicator** (“X is typing…”)
- **Search** messages by keyword
- **Send files** (base64-encoded) between users
- **Clear chat** for a conversation
- **Export chat to .txt**
- **Light / dark themes**, accent color and font size settings
- Bigger chat window + improved readability
- Simple, desktop-style UI built with Tkinter

---

## 🧱 Project Structure

pysolutions/
├── secure_server.py          # Server (run this first)
├── secure_client_gui.py      # GUI client (PYchat)
├── README.md                 # This file
└── requirements.txt          # Python dependencies

---

## 🖥️ Running PYchat

1. **Start the server**

   cd ~/Desktop/pysolutions  
   python3 secure_server.py

2. **Start the client**

   cd ~/Desktop/pysolutions  
   python3 secure_client_gui.py

The client connects to **127.0.0.1:7777**.

---

## 📌 Notes

- Local files like `settings.json`, `secure_db.json`, and key files are ignored using `.gitignore`.
- Build folders and PyInstaller output are not synced to GitHub.
- This project is for local use, testing, and learning.
