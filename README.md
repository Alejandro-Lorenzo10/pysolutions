🥧PYchat🥧

PYchat is a secure direct-messaging (DM) app built in Python using a Tkinter GUI.

It uses a simple client–server setup:

- **Server (`secure_server.py`)** – handles user accounts, login, encrypted messages, conversations, search, typing status, and message exporting.  
- **Client (`secure_client_gui.py`)** – the desktop chat app with login/register, inbox, conversation list, chat window, themes, and font-size options.

PYchat uses **AES-256 symmetric encryption** to protect stored messages and sensitive data in the local database.

You can run PYchat with Python installed, or build it into standalone Mac apps with PyInstaller.

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

## 🧱 **Project Structure**

pysolutions/
├── secure_server.py          # **Server backend (run this first)**
├── secure_client_gui.py      # **GUI client app (PYchat)**
├── README.md                 # **Project documentation**
└── requirements.txt          # **Python dependencies**

---

## 🖥️ Platform & Usage Notes

PYchat currently works **only on macOS** when built as a standalone app.  
This is because the packaged `.app` files produced by **PyInstaller** are macOS-specific and cannot run on Windows or Linux without rebuilding separate versions for each platform.

To make PYchat work on **multiple computers over the internet**, you would still need:

- A **publicly hosted server** (VPS or cloud server)  
- Change the client `HOST` value from `127.0.0.1` to your server’s public IP  
- Open port **7777** on the server firewall  

Right now, PYchat runs locally using:

- `127.0.0.1`  
- Port `7777`  
- Local socket communication  

So it works **only on your own Mac**, unless you host your server online.

---

## 🎓 Educational Purpose

PYchat was created **only as a school project and for learning purposes**.  
It is **not intended for commercial use**, real-world deployment, or production-grade security.

The app demonstrates:

- Basic client–server design  
- Tkinter GUI development  
- Messaging, search, and themes  
- User session handling  
- Simple JSON-based storage  
- Basic encryption for message transfer and storage  

This project is meant for:

- Practicing Python  
- Learning networking concepts  
- Understanding GUI development  
- Exploring how chat apps work internally  

It is **not meant for real-world secure communication.**
