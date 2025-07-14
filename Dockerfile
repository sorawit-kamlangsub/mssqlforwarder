# Dockerfile for Ngrok‑enabled MSSQL forwarder
FROM python:3.11-slim

WORKDIR /app
COPY forwarder.py .

# Install dependencies
RUN pip install --no-cache-dir pyngrok python-dotenv

# Listen on the same port we’ll expose (default 1433)
EXPOSE 1433

CMD ["python", "forwarder.py"]
