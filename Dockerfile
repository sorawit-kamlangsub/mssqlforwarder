# Dockerfile for Ngrok-enabled MSSQL forwarder
FROM python:3.11-slim

WORKDIR /app
COPY forwarder.py .

# Install all required Python dependencies
RUN pip install --no-cache-dir pyngrok python-dotenv requests

EXPOSE 1433
CMD ["python", "forwarder.py"]
