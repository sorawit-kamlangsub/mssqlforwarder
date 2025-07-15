import socket
import threading
from pyngrok import ngrok
import os

# Load config from environment variables
AUTH_TOKEN = os.getenv("NGROK_AUTHTOKEN")
LOCAL_PORT = int(os.getenv("LOCAL_PORT", "1433"))
TARGET_IP = os.getenv("TARGET_IP", "147.50.150.227")
TARGET_PORT = int(os.getenv("TARGET_PORT", "1433"))

if not AUTH_TOKEN:
    print("Error: NGROK_AUTHTOKEN not set in environment")
else:
    def forward(src, dst):
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    break
                dst.sendall(data)
        except Exception as e:
            print(f"Forward error: {e}")
        finally:
            src.close()
            dst.close()

    def handler(client_socket):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((TARGET_IP, TARGET_PORT))

            threading.Thread(target=forward, args=(client_socket, server_socket), daemon=True).start()
            threading.Thread(target=forward, args=(server_socket, client_socket), daemon=True).start()
        except Exception as e:
            print(f"Handler error: {e}")
            client_socket.close()

    # Set ngrok token and start tunnel
    ngrok.set_auth_token(AUTH_TOKEN)
    tunnel = ngrok.connect(LOCAL_PORT, "tcp")
    print(f"🌐 Ngrok tunnel → {tunnel.public_url} ⇢ localhost:{LOCAL_PORT}")

    # Start listening locally to forward to target IP:port
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(('0.0.0.0', LOCAL_PORT))
    listener.listen(5)
    print(f"Waiting for connections on 0.0.0.0:{LOCAL_PORT}...")

    try:
        while True:
            client_socket, addr = listener.accept()
            print(f"Accepted connection from {addr}")
            handler(client_socket)
    except KeyboardInterrupt:
        print("Forwarder stopped by user.")
