import os
import socket
import threading
import time
import sys
import requests
from pyngrok import ngrok
from dotenv import load_dotenv

load_dotenv()

LOCAL_PORT = int(os.getenv("LOCAL_PORT", 1433))
TARGET_IP = os.getenv("TARGET_IP", "147.50.150.227")
TARGET_PORT = int(os.getenv("TARGET_PORT", 1433))
AUTH_TOKEN = os.getenv("NGROK_AUTHTOKEN")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not AUTH_TOKEN:
    sys.exit("❌  Set NGROK_AUTHTOKEN in the environment or .env file")

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("[!] Telegram bot token or chat id not set, skipping notification")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print("[✓] Telegram notification sent")
        else:
            print(f"[!] Telegram API returned {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[!] Telegram send error: {e}")

def pipe(src, dst):
    try:
        while data := src.recv(4096):
            dst.sendall(data)
    finally:
        src.close()
        dst.close()

def handle_client(client_sock, client_addr):
    print(f"[>] Incoming {client_addr}")
    try:
        server_sock = socket.create_connection((TARGET_IP, TARGET_PORT))
        print(f"[+] Bridged → {TARGET_IP}:{TARGET_PORT}")
    except Exception as exc:
        print(f"[!] Upstream connect error: {exc}")
        client_sock.close()
        return

    threading.Thread(target=pipe, args=(client_sock, server_sock), daemon=True).start()
    threading.Thread(target=pipe, args=(server_sock, client_sock), daemon=True).start()

def start_forwarder():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", LOCAL_PORT))
    listener.listen(100)
    print(f"[✓] Forwarding 0.0.0.0:{LOCAL_PORT}  →  {TARGET_IP}:{TARGET_PORT}")

    while True:
        client, addr = listener.accept()
        threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()

def monitor_tunnel(tunnel):
    last_url = None
    while True:
        current_url = tunnel.public_url
        if current_url != last_url:
            msg = f"🚨 Ngrok tunnel URL updated:\n{current_url}"
            print(msg)
            send_telegram_message(msg)
            last_url = current_url
        time.sleep(60)  # check every 60 seconds

def main():
    threading.Thread(target=start_forwarder, daemon=True).start()

    ngrok.set_auth_token(AUTH_TOKEN)
    tunnel = ngrok.connect(addr=LOCAL_PORT, proto="tcp")
    print(f"🌐  Ngrok tunnel →  {tunnel.public_url}  ⇢  localhost:{LOCAL_PORT}")

    send_telegram_message(f"🚀 Ngrok tunnel started:\n{tunnel.public_url}")

    threading.Thread(target=monitor_tunnel, args=(tunnel,), daemon=True).start()

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nShutting down…")
        ngrok.disconnect(tunnel.public_url)
        ngrok.kill()

if __name__ == "__main__":
    main()
