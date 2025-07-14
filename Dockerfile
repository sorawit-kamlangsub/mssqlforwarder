# Dockerfile for Ngrok‑enabled MSSQL forwarder
FROM python:3.11‑slim

WORKDIR /app
COPY forwarder.py .

# ⬇️  install every dependency the script needs
RUN pip install --no-cache-dir pyngrok python-dotenv requests

EXPOSE 1433
CMD ["python", "forwarder.py"]
