# forwarder.py
import socket
import threading

LOCAL_PORT = 1433
TARGET_IP = "147.50.150.227"
TARGET_PORT = 1433

def forward(src, dst):
    while True:
        data = src.recv(4096)
        if not data:
            break
        dst.sendall(data)

def handler(client_socket):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((TARGET_IP, TARGET_PORT))

    threading.Thread(target=forward, args=(client_socket, server_socket)).start()
    threading.Thread(target=forward, args=(server_socket, client_socket)).start()

def main():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('0.0.0.0', LOCAL_PORT))
    listener.listen(5)
    print(f"Forwarding localhost:{LOCAL_PORT} -> {TARGET_IP}:{TARGET_PORT}")

    while True:
        client_socket, _ = listener.accept()
        threading.Thread(target=handler, args=(client_socket,)).start()

main()
