#!/usr/bin/env python3
"""
Fake Bank LLC -- an HTTP vs HTTPS teaching tool.

Serves a FAKE bank login page for a network-security classroom demo.
When the form is submitted, the username and password travel in the body of
the HTTP request. Capture that traffic in Wireshark and compare:

  - Over HTTP  -> the credentials are visible in plaintext
                  (right-click a packet -> Follow -> HTTP Stream)
  - Over HTTPS -> the exact same bytes are encrypted and unreadable

No third-party packages. Python 3.8+ standard library only.

*** THIS IS A DEMONSTRATION. NEVER ENTER A REAL USERNAME OR PASSWORD. ***
"""

import os
import ssl
import html
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

HOST = os.environ.get("BIND_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
# Set BOTH of these (to readable cert/key file paths) to serve over HTTPS.
CERT_FILE = os.environ.get("CERT_FILE")
KEY_FILE = os.environ.get("KEY_FILE")

PAGE_STYLE = """
  :root {
    --ink: #ece7f5;
    --field: #1b1026;
    --field-border: #3d2a52;
    --surface: #241433;
    --surface-border: #37214d;
    --page: #120718;
    --brand: #7c3aed;
    --brand-2: #a855f7;
    --brand-ink: #ffffff;
    --warn-bg: #ffcf33;
    --warn-border: #b8860b;
    --warn-ink: #3a2a00;
    --muted: #a494bf;
    --code-bg: #0c0417;
    --code-ink: #e9d5ff;
    color-scheme: dark;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    font-family: "Segoe UI", system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif;
    color: var(--ink);
    background:
      radial-gradient(1100px 600px at 50% -10%, rgba(124, 58, 237, 0.22), transparent 70%),
      var(--page);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 16px 48px;
  }
  .warning {
    width: 100%;
    max-width: 760px;
    margin-bottom: 20px;
    padding: 14px 18px;
    background: var(--warn-bg);
    border: 2px solid var(--warn-border);
    border-radius: 10px;
    color: var(--warn-ink);
    line-height: 1.5;
  }
  .warning strong { font-size: 1.05rem; }
  .chip {
    display: inline;
    padding: 2px 6px;
    background: var(--code-bg);
    color: var(--code-ink);
    border-radius: 4px;
  }
  .card {
    width: 100%;
    max-width: 420px;
    background: var(--surface);
    border: 1px solid var(--surface-border);
    border-radius: 14px;
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.55);
    overflow: hidden;
  }
  .brand {
    background: linear-gradient(135deg, var(--brand), var(--brand-2));
    color: var(--brand-ink);
    padding: 22px 28px;
  }
  .brand .logo { font-size: 1.4rem; font-weight: 700; letter-spacing: 0.3px; }
  .brand .tag { opacity: 0.9; font-size: 0.85rem; margin-top: 2px; }
  form, .result { padding: 26px 28px 30px; }
  label { display: block; font-size: 0.85rem; color: var(--muted); margin: 14px 0 6px; }
  input[type=text], input[type=password] {
    width: 100%;
    padding: 11px 12px;
    font-size: 1rem;
    border: 1px solid var(--field-border);
    border-radius: 8px;
    background: var(--field);
    color: var(--ink);
  }
  input:focus-visible { outline: 3px solid rgba(168, 85, 247, 0.5); outline-offset: 1px; }
  button {
    width: 100%;
    margin-top: 22px;
    padding: 12px;
    font-size: 1rem;
    font-weight: 600;
    color: var(--brand-ink);
    background: linear-gradient(135deg, var(--brand), var(--brand-2));
    border: none;
    border-radius: 8px;
    cursor: pointer;
  }
  button:hover { filter: brightness(1.1); }
  .foot { text-align: center; color: var(--muted); font-size: 0.78rem; margin-top: 22px; }
  .result h2 { margin: 0 0 10px; }
  .result code {
    display: block;
    background: var(--code-bg);
    color: var(--code-ink);
    padding: 12px 14px;
    border-radius: 8px;
    font-size: 0.95rem;
    word-break: break-all;
    margin: 6px 0 16px;
  }
  .result a { color: var(--brand-2); font-weight: 600; }
  @media (prefers-reduced-motion: no-preference) { button { transition: filter 0.15s; } }
"""

WARNING_BANNER = """
  <div class="warning" role="alert">
    <strong>&#9888; Demonstration only.</strong><br>
    This is a fake bank page built to show how network traffic can be captured.
    <strong>Do not type a real username or password.</strong>
    Use made-up values such as <span class="chip">testuser / notmyrealpassword</span>.
  </div>
"""


def page(title, body):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{PAGE_STYLE}</style>
</head>
<body>
{WARNING_BANNER}
{body}
</body>
</html>"""


def login_body(scheme):
    note = (
        "You are connected over <strong>HTTPS</strong>, so what you send is encrypted."
        if scheme == "https"
        else "You are connected over <strong>HTTP</strong>, so what you send is sent in the clear."
    )
    return f"""
  <div class="card">
    <div class="brand">
      <div class="logo">Fake Bank LLC</div>
      <div class="tag">Online banking &middot; secure sign in (pretend)</div>
    </div>
    <form method="POST" action="/login">
      <label for="username">Username</label>
      <input id="username" name="username" type="text" autocomplete="off" required>
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="off" required>
      <button type="submit">Sign in</button>
      <p class="foot">{note}</p>
    </form>
  </div>
"""


def result_body(scheme, username, password):
    captured = (
        "Because this was sent over <strong>HTTPS</strong>, anyone sniffing the "
        "network sees only encrypted bytes &mdash; not the values below."
        if scheme == "https"
        else "Because this was sent over <strong>HTTP</strong>, anyone sniffing the "
        "network just saw exactly this, in plaintext. In Wireshark, right-click the "
        "packet and choose <strong>Follow &rarr; HTTP Stream</strong>."
    )
    return f"""
  <div class="card">
    <div class="brand">
      <div class="logo">Fake Bank LLC</div>
      <div class="tag">Sign-in received</div>
    </div>
    <div class="result">
      <h2>Thanks, that was transmitted.</h2>
      <p>Your browser just sent this to the server in the request body:</p>
      <code>username={html.escape(username)}<br>password={html.escape(password)}</code>
      <p>{captured}</p>
      <p><a href="/">&larr; Back to the sign-in page</a></p>
    </div>
  </div>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "FakeBankLLC/1.0"

    @property
    def scheme(self):
        return "https" if isinstance(self.server.socket, ssl.SSLSocket) else "http"

    def _send(self, body, status=200):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        # Keep this demo cache-free and framing-free; not a security exercise in itself.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/", "/login"):
            self._send(page("Fake Bank LLC - Sign in", login_body(self.scheme)))
        else:
            self._send(page("Not found", '<div class="card"><div class="result">'
                            '<h2>404</h2><p>Nothing here. Try '
                            '<a href="/">the sign-in page</a>.</p></div></div>'),
                       status=404)

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/login":
            self._send(page("Not found", '<div class="card"><div class="result">'
                            '<h2>404</h2></div></div>'), status=404)
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        fields = parse_qs(raw, keep_blank_values=True)
        username = fields.get("username", [""])[0]
        password = fields.get("password", [""])[0]

        # Log to the container's stdout so the instructor can see captures land.
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] {self.scheme.upper()} login submitted from "
              f"{self.client_address[0]} -> username={username!r} password={password!r}",
              flush=True)

        self._send(page("Fake Bank LLC - Received",
                        result_body(self.scheme, username, password)))

    def log_message(self, fmt, *args):
        # Quieter default access log; the POST handler prints what matters.
        pass


def main():
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    scheme = "http"
    if CERT_FILE and KEY_FILE:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        scheme = "https"
    print(f"Fake Bank LLC serving on {scheme}://{HOST}:{PORT}", flush=True)
    print("Reminder: this is a demo. Do not enter real credentials.", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
        httpd.shutdown()


if __name__ == "__main__":
    main()
