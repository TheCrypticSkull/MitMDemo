# Northwind Demo Bank — HTTP vs HTTPS packet-capture demo

A deliberately fake bank login page for teaching why HTTPS matters. Submit the
form while Wireshark is capturing, then compare:

- **HTTP** — the username and password appear in plaintext in the capture.
- **HTTPS** — the same submission is encrypted and unreadable.

The page carries a loud banner telling anyone not to enter real credentials.
No third-party Python packages are used, so it builds and runs offline.

> This is a lab tool for a network you own and control. The page uses the
> fictional name "Northwind Demo Bank" and does not imitate any real institution.

## Run it

### Option A — docker compose (serves HTTP and HTTPS at once)

```bash
# 1. Create a self-signed cert for the HTTPS service
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=demo-bank.local"

# 2. Build and start both services
docker compose up --build
```

- HTTP:  `http://<docker-host-ip>:8080`
- HTTPS: `https://<docker-host-ip>:8443` (browser will warn about the self-signed
  cert — that's expected; click through for the demo)

### Option B — plain docker, one container

```bash
docker build -t northwind-demo-bank .

# HTTP
docker run --rm -p 8080:8080 northwind-demo-bank

# HTTPS (mount a cert directory as /certs first)
docker run --rm -p 8443:8443 \
  -e PORT=8443 -e CERT_FILE=/certs/cert.pem -e KEY_FILE=/certs/key.pem \
  -v "$PWD/certs:/certs:ro" northwind-demo-bank
```

### Option C — no Docker

```bash
python3 server.py                       # HTTP on :8080
PORT=8443 CERT_FILE=certs/cert.pem KEY_FILE=certs/key.pem python3 server.py   # HTTPS
```

## Configuration (environment variables)

| Variable    | Default   | Purpose                                            |
|-------------|-----------|----------------------------------------------------|
| `PORT`      | `8080`    | Port to listen on                                  |
| `BIND_HOST` | `0.0.0.0` | Interface to bind                                  |
| `CERT_FILE` | *(unset)* | Path to TLS cert — set with `KEY_FILE` for HTTPS   |
| `KEY_FILE`  | *(unset)* | Path to TLS private key                            |

If both `CERT_FILE` and `KEY_FILE` are set, the server starts in HTTPS mode;
otherwise it serves plain HTTP.

## The Wireshark walkthrough

1. Start the capture in Wireshark on the interface your victim laptop's traffic
   crosses. A useful display filter: `http` (for the plaintext run) or
   `tcp.port == 8080 || tcp.port == 8443`.
2. On the victim laptop, open the **HTTP** page and sign in with fake values,
   e.g. `testuser` / `notmyrealpassword`.
3. In Wireshark, find the `POST /login` packet, right-click it, and choose
   **Follow → HTTP Stream**. You'll see `username=testuser&password=notmyrealpassword`
   sitting in the clear.
4. Now repeat on the **HTTPS** page. Filter on `tls` or the HTTPS port. Follow the
   TLS stream and you'll see only encrypted application data — the credentials
   are gone from view.

The container also prints every submission to its stdout
(`docker compose logs -f bank-http`), which is handy for confirming the request
landed while you hunt for the packet.

## Notes

- Nothing is stored. Submitted values are echoed back to the browser and logged
  to stdout only, to make the capture tangible.
- For a clean capture, prefer the plaintext HTTP run on an isolated lab network.
- Keep the warning banner intact if you adapt the page.
