# Fake Bank LLC — HTTP vs HTTPS Demonstration

Fake Bank LLC is a **fictional banking login page** built for a network-security demonstration. Its purpose is to show how HTTP and HTTPS handle submitted information differently when traffic is inspected with Wireshark.

- **HTTP:** A network capture can reveal the submitted username and password in plaintext.
- **HTTPS:** TLS encrypts the traffic in transit, so a normal passive packet capture cannot read the submitted credentials.

The page displays a prominent warning to **never enter real credentials**. Only use invented usernames and passwords on a lab network that you own or are authorized to test.

## Requirements

- Python 3.8 or later (standard library only)
- OpenSSL, if you need to create a demonstration certificate
- Wireshark, for packet inspection
- Two terminals if you want to serve HTTP and HTTPS simultaneously

No database, Docker setup, or external Python packages are required.

## Project structure

```text
MitMDemo/
├── server.py
├── README.md
├── .gitignore
└── certs/
    ├── cert.pem       # Public TLS certificate
    └── key.pem        # Private TLS key: do not commit
```

Run the commands below from the project root so the relative `certs/` paths resolve correctly.

## TLS certificate setup

If you do not already have a certificate for this demonstration, create a temporary self-signed certificate:

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 30 -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 600 certs/key.pem
```

This example covers local connections to `localhost` or `127.0.0.1`. If accessing the demo from another device, generate a certificate containing the hostname or IP address used by that device. Browsers will generally warn that a self-signed certificate is not trusted unless you explicitly configure trust for the demonstration.

## Starting the server

The server uses `PORT`, `BIND_HOST`, `CERT_FILE`, and `KEY_FILE` environment variables to select its network interface, port, and protocol.

### Option A: Ports 80 and 443

These are the standard HTTP and HTTPS ports. Run each command in a **separate terminal**:

**Terminal 1 — HTTP**

```bash
sudo PORT=80 python3 server.py
```

**Terminal 2 — HTTPS**

```bash
sudo PORT=443 CERT_FILE=certs/cert.pem KEY_FILE=certs/key.pem python3 server.py
```

Open:

- HTTP: `http://localhost`
- HTTPS: `https://localhost`

On Linux, binding directly to ports below 1024 usually requires elevated privileges or another port-binding mechanism. For a simpler demo without running Python as root, use Option B.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `8080` | TCP port on which the server listens |
| `BIND_HOST` | `0.0.0.0` | IPv4 address/interface on which the server listens; `0.0.0.0` means all IPv4 interfaces |
| `CERT_FILE` | Unset | Path to the TLS certificate |
| `KEY_FILE` | Unset | Path to the TLS private key |

Set **both** `CERT_FILE` and `KEY_FILE` to enable HTTPS. Otherwise, the script serves HTTP.

## Wireshark demonstration

Capture only traffic from systems and networks you have permission to inspect. A two-computer lab makes the difference especially clear because the traffic crosses a real network interface.

1. Start Wireshark on the interface carrying traffic between the demonstration client and server. If testing only on one computer, use its loopback capture interface.
2. Open the **HTTP** site and submit made-up credentials, such as `testuser` and `notmyrealpassword`.
3. Filter for the HTTP traffic using `tcp.port == 80` Locate the `POST /login` request and select **Follow → HTTP Stream**. The form data will be readable in the request body, for example:

   ```text
   username=testuser&password=notmyrealpassword
   ```

4. Repeat with the **HTTPS** site. Filter with `tcp.port == 443` (or `tcp.port == 8443`). TLS protects the HTTP request body in transit; without the TLS session keys, the same form data will not be readable in an ordinary packet capture.
5. Compare the two captures: **HTTP sends form data without transport encryption; HTTPS protects it with TLS.**

The server prints each submitted username and password in the terminal and also echoes them on its confirmation page. That is **intentional for this demonstration**: the server can see data after receiving and decrypting it, while an ordinary passive observer of HTTPS traffic cannot.

## Security and limitations

- **Use fake credentials only.** The site is not a real banking or authentication system.
- **No database is used.** Submissions are not intentionally written to a database or file, but they are displayed in the response and printed to server stdout, where redirected output or external logging tools could retain them.
- **Do not deploy this as a public login service.** It has no real authentication, rate limiting, or production security controls.
- **Protect the TLS private key.** Keep `certs/key.pem` out of version control and do not reuse demonstration keys for real services.
- **Use an isolated lab network when possible.** The script's default bind address is `0.0.0.0`, so specify `BIND_HOST` if you want to limit access.
- **Self-signed certificates are for demonstration here.** Encryption and server identity verification are distinct concepts; a self-signed certificate does not automatically establish that the server is trustworthy.

## Learning objectives

By completing the demonstration, you should be able to:

1. Identify an HTTP form submission in Wireshark.
2. Explain why HTTP request bodies can be read in a plaintext capture.
3. Observe that HTTPS encrypts HTTP application data during transmission.
4. Explain the difference between data visible to the receiving server and data visible to a passive network observer.
5. Describe the role of TLS certificates and why private keys must be protected.

---

**Disclaimer:** Fake Bank LLC is a fictional educational project. It is not affiliated with a real financial institution and must never be used to collect actual usernames, passwords, or banking information.
