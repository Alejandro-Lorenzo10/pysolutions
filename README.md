# 🥧PYchat🥧

PYchat is a secure direct-messaging (DM) app built in Python using a Tkinter GUI.

It uses a simple client–server setup:

- **Server (`secure_server.py`)** – handles user accounts, login, encrypted messages, conversations, search, typing status, and message exporting.  
- **Client (`secure_client_gui.py`)** – the desktop chat app with login/register, inbox, conversation list, chat window, themes, and font-size options.

PYchat uses **AES-256 symmetric encryption** to protect stored messages and sensitive data in the local database.

You can run PYchat with Python installed, or build it into standalone macOS apps with PyInstaller.

---

## ✨ Main Features

- User **registration & login** with 3-strike lockout  
- **Private DMs**  
- **AES-256 encrypted message storage**  
- **Inbox** with timestamps and last-message previews  
- **Conversation list** with unread counts  
- Live-ish **auto-refresh chat window**  
- **Typing indicator**  
- **Search messages** by keyword  
- **Clear chat** per conversation  
- **Export chat to .txt**  
- Multiple themes:  
  - Solar Night  
  - Carbon Grey  
  - Ocean Teal  
  - Classic Light  
  - Minimal White  
- Font sizes: Small, Medium, Large, Extra-Large  
- Bigger chat window + improved readability  

---

## 🧱 Project Structure

```text
pysolutions/
├── secure_server.py          # Server (run this first)
├── secure_client_gui.py      # GUI client (PYchat)
├── README.md                 # This file
└── requirements.txt          # Python dependencies

🖥️ Platform & Usage Notes
PYchat currently works only on macOS when packaged as an app.
This is because PyInstaller generates a .app bundle that is macOS-only and cannot run on Windows or Linux unless separate platform-specific builds are made.
To make PYchat work on multiple computers over the internet, you would need:
A public server (VPS) to host secure_server.py
Change the client’s HOST = "127.0.0.1" to your server’s public IP
Allow port 7777 through the server firewall
Right now, PYchat runs locally on:
127.0.0.1
Port 7777
Standard Python socket communication
This means the app works only on your own Mac unless you host the server online.
🎓 Educational Purpose
PYchat was created solely as a school project and for learning purposes.
It is not designed for commercial use or production security.
This project demonstrates:
Client-server communication
Tkinter GUI design
Real-time messaging basics
Search, themes, user sessions
JSON-based data storage
AES-256 message encryption
PYchat is intended for:
Practicing Python
Understanding networking
Learning about GUIs
Seeing how messaging apps work internally
Not for real-world secure communication.
