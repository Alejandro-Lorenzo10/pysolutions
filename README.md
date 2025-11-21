# 🥧PYchat🥧

PYchat is a secure direct-messaging (DM) app built in Python with a Tkinter GUI.

It uses a simple client–server setup:

- **Server (`secure_server.py`)** – handles user accounts, logins, messages, conversations, search, typing status, and encrypted file sending.  
- **Client (`secure_client_gui.py`)** – a desktop chat app with login/register, inbox, conversations, auto-refresh chat window, search, themes, and larger font options.

You can run it with Python, or package it into a standalone macOS app using PyInstaller.

---

## ✨ Main Features

- **User registration & login** with 3-strike lockout  
- **Private DMs**  
- **Inbox** with timestamps  
- **Conversation list** (totals, unread counts, last message preview)  
- **Chat window** with live-ish auto refresh  
- **Typing indicator**  
- **Search messages** by keyword  
- **Clear conversation**  
- **Export chat to .txt**  
- **Multiple themes**, including:
  - Solar Night  
  - Carbon Grey  
  - Ocean Teal  
  - Classic Light  
  - Minimal White  
- **Font sizes:** Small, Medium, Large, Extra-Large  
- **Bigger chat window** + improved readability  

---

## 🧱 Project Structure

```text
pysolutions/
├── secure_server.py
├── secure_client_gui.py
├── README.md
├── requirements.txt
├── PySolutions Server.spec
└── PySolutions Client.spec
```

---

## 🖥️ Running PYchat

### 1. Start the server

```bash
cd ~/Desktop/pysolutions
python3 secure_server.py
```

### 2. Start the client

```bash
cd ~/Desktop/pysolutions
python3 secure_client_gui.py
```

The client connects to `127.0.0.1:7777`.

---

## 📌 Notes

- Local files like `settings.json`, `secure_db.json`, and keys are ignored using `.gitignore`.  
- Build folders and PyInstaller output aren’t synced to GitHub.  
- This project is for local testing and learning.

---
