# 🥧PYchat🥧

PYchat is a secure direct-messaging (DM) app built in Python using a Tkinter GUI.

It uses a simple client–server setup:

- **Server (`secure_server.py`)** – handles user accounts, login, messages, conversations, search, typing status, and message exporting.
- **Client (`secure_client_gui.py`)** – the desktop chat app with login/register, inbox, conversation list, chat window, themes, and font-size options.

You can run PYchat with Python installed, or build it into standalone Mac apps with PyInstaller.

---

## ✨ Main Features

- User **registration & login** with 3-strike lockout  
- **Private DMs**  
- **Inbox** with timestamps and last-message previews  
- **Conversation list** with unread counts  
- **Chat window** with live-ish auto refresh  
- **Typing indicator**  
- **Search messages**  
- **Clear chat** per conversation  
- **Export chat to .txt**  
- **Multiple themes:**
  - Solar Night  
  - Carbon Grey  
  - Ocean Teal  
  - Classic Light  
  - Minimal White  
- **Font sizes:** Small, Medium, Large, Extra-Large  
- **Bigger chat window + improved readability**

---

## 🧱 Project Structure

```text
pysolutions/
├── secure_server.py          # Server (run this first)
├── secure_client_gui.py      # GUI client (PYchat)
├── README.md                 # This file
└── requirements.txt          # Python dependencies
