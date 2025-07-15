import os, socket, threading, sys
from pyngrok import ngrok
from dotenv import load_dotenv

# ── load .env ────────────────────────────────────────────────────────────────
load_dotenv()
LOCAL_PORT      = int(os.getenv("LOCAL_PORT", 1433))
TARGET_IP       = os.getenv("TARGET_IP", "147.50.150.227")
TARGET_PORT     = int(os.getenv("TARGET_PORT", 1433))
NGROK_TOKEN     = os.getenv("NGROK_AUTHTOKEN")

print(f"env NGROK_TOKEN : {NGROK_AUTHTOKEN} TELEGRAM_BOT_TOKEN : {TELEGRAM_BOT_TOKEN}")
if not NGROK_TOKEN:
    sys.exit("NGROK_AUTHTOKEN missing in env")

# ── start ngrok exactly once ────────────────────────────────────────────────
try:
    ngrok.set_auth_token("2VLMZ4oBIu3VXGKWhP5SNkaXEbh_27rMTdT2efum4AzpZJDis")          # ← ONE single call
    tunnel = ngrok.connect(1433, "tcp")  # ← ONE single tunnel
    print(f"Ngrok tunnel → {tunnel.public_url} ⇢ localhost:{LOCAL_PORT}")
except (Exception) as e:
    sys.exit(f"Can't start ngrok tunnel: {e}")

# ── set up listener ─────────────────────────────────────────────────────────
listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(("0.0.0.0", LOCAL_PORT))
listener.listen(50)
print(f"Waiting for connections on 0.0.0.0:{LOCAL_PORT} …")

# ── helper to pipe data ─────────────────────────────────────────────────────
def pipe(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    finally:
        src.close()
        dst.close()

# ── main loop ───────────────────────────────────────────────────────────────
while True:
    client, addr = listener.accept()
    print(f"Accepted {addr}")
    try:
        server = socket.create_connection((TARGET_IP, TARGET_PORT))
    except Exception as err:
        print(f"Can't reach {TARGET_IP}:{TARGET_PORT} – {err}")
        client.close()
        continue
    threading.Thread(target=pipe, args=(client, server), daemon=True).start()
    threading.Thread(target=pipe, args=(server, client), daemon=True).start()
