# Northwind Demo Bank — fake login page for an HTTP-vs-HTTPS Wireshark demo.
# No third-party packages, so the build works fully offline.
FROM python:3.12-slim

WORKDIR /app
COPY server.py /app/server.py

# Default to HTTP on 8080. Override PORT / CERT_FILE / KEY_FILE to serve HTTPS.
ENV PORT=8080
EXPOSE 8080

# Run as a non-root user.
RUN useradd --create-home --uid 10001 demo
USER demo

CMD ["python", "server.py"]
