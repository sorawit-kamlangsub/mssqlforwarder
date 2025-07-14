#!/usr/bin/env python3
"""
Expose a remote SQL Server (or any TCP service) through a local forwarder
plus an Ngrok TCP tunnel.

• Listens on LOCAL_PORT (default 1433) inside the container/host.
• Forwards every connection to TARGET_IP:TARGET_PORT.
• Starts an Ngrok tunnel that maps a public TCP address → LOCAL_PORT.
• Prints the public Ngrok URL and streams basic connection logs.

Configuration is taken from environment variables or a .env file:
    NGROK_AUTHTOKEN  (required) – your Ngrok token
    LOCAL_PORT       (optional) – local listen port, default 1433
    TARGET_IP        (optional) – upstream server IP, default 147.50.150.227
    TARGET_PORT      (optional) – upstream port, default 1433
"""

import os, socket, threading, time, sys
from pyngrok import ngrok
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────
load_dotenv()  # read values from .env if present
# ─────────────────────────────────────────────────────────────────────

LOCAL_PORT   = int(os.getenv("LOCAL_PORT",   1433))
TARGET_IP    = os.getenv("TARGET_IP",       "147.50.150.227")
TARGET_PORT  = int(os.getenv("TARGET_PORT", 1433))
AUTH_TOKEN   = os.getenv("NGROK_AUTHTOKEN")

if not AUTH_TOKEN:
    sys.exit("❌  Set NGROK_AUTHTOKEN in the environment or .env file")

# ──────────────────────────  TCP forwarder  ─────────────────────────

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

# ─────────────────────────────  main  ───────────────────────────────

def main():
    # 1️⃣  Start forwarder in background
    threading.Thread(target=start_forwarder, daemon=True).start()

    # 2️⃣  Create Ngrok tunnel
    ngrok.set_auth_token(AUTH_TOKEN)
    tunnel = ngrok.connect(addr=LOCAL_PORT, proto="tcp")
    print(f"🌐  Ngrok tunnel →  {tunnel.public_url}  ⇢  localhost:{LOCAL_PORT}")

    # 3️⃣  Keep process alive
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nShutting down…")
        ngrok.disconnect(tunnel.public_url)
        ngrok.kill()

if __name__ == "__main__":
    main()
