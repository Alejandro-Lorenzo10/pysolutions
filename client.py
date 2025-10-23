import socket

HOST = "127.0.0.1"
PORT = 7777

def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            msg = input("Enter message (or 'quit' to exit): ")
            if msg.lower() == "quit":
                break
            s.sendall(msg.encode())
            data = s.recv(1024)
            print("Server says:", data.decode())

if __name__ == "__main__":
    start_client()
