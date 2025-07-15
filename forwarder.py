import socket
import threading
import time
import os
from pyngrok import ngrok
from dotenv import load_dotenv
import requests

# Load env variables from .env file if present
load_dotenv()

LOCAL_PORT = int(os.getenv("LOCAL_PORT", 1433))
TARGET_IP = os.getenv("TARGET_IP", "147.50.150.227")
TARGET_PORT = int(os.getenv("TARGET_PORT", 1433))
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Optional: Telegram messaging (commented out if you don't want Telegram)
def send_telegram_message(message):
    # Uncomment below to enable telegram
    # if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    #     print("Telegram token or chat id not set.")
    #     return
    # url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    # try:
    #     requests.post(url, data=data)
    # except Exception as e:
    #     print("Telegram send error:", e)
    pass

# Start
print(f"Start With NGROK_AUTHTOKEN = {NGROK_AUTHTOKEN} TELEGRAM_BOT_TOKEN = {TELEGRAM_BOT_TOKEN}")

# ─── Start ngrok tunnel (with error handling) ───────────────────────────────
try:
    if not NGROK_AUTHTOKEN:
        raise ValueError("NGROK_AUTHTOKEN is missing in environment")

    ngrok.set_auth_token(NGROK_AUTHTOKEN)
    tunnel = ngrok.connect(addr=LOCAL_PORT, proto="tcp")  # may raise PyngrokError
    print(f" Ngrok tunnel → {tunnel.public_url}  ⇢  localhost:{LOCAL_PORT}")
    send_telegram_message(f"🚀 Ngrok tunnel started:\n{tunnel.public_url}")

except (PyngrokError, ValueError) as err:
    print(f"  Failed to start ngrok tunnel: {err}")
    sys.exit(1)

send_telegram_message(f"🚀 Ngrok tunnel started:\n{tunnel.public_url}")

# Socket forwarding logic inline

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(("0.0.0.0", LOCAL_PORT))
listener.listen(5)
print(f"Waiting for connections on 0.0.0.0:{LOCAL_PORT}...")

def forward(src, dst):
    while True:
        try:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
        except Exception:
            break
    src.close()
    dst.close()

while True:
    client_socket, client_addr = listener.accept()
    print(f"Accepted connection from {client_addr}")

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((TARGET_IP, TARGET_PORT))
    except Exception as e:
        print(f"Failed to connect to target {TARGET_IP}:{TARGET_PORT} - {e}")
        client_socket.close()
        continue

    Print("Start Socket ...")
    threading.Thread(target=forward, args=(client_socket, server_socket), daemon=True).start()
    threading.Thread(target=forward, args=(server_socket, client_socket), daemon=True).start()
