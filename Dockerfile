# Use official Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy your app code
COPY forwarder.py .
COPY .env .

# Download and install ngrok binary inside container
ADD https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz /tmp
RUN tar -C /usr/local/bin -xzf /tmp/ngrok-v3-stable-linux-amd64.tgz ngrok \
    && rm /tmp/ngrok-v3-stable-linux-amd64.tgz \
    && chmod +x /usr/local/bin/ngrok

# Install Python dependencies
RUN pip install --no-cache-dir pyngrok python-dotenv requests

# Set env var so pyngrok uses the bundled ngrok binary
ENV PYNGROK_CONFIG=/usr/local/bin/ngrok

# Expose port 1433 for SQL forwarding
EXPOSE 1433

# Run your forwarder
CMD ["python", "forwarder.py"]
