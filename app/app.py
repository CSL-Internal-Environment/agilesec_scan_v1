from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import os
import secrets
import sqlite3
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "app" / "agilesec_secure_demo.db"
STATIC_DIR = ROOT / "app" / "static"
DOWNLOADS = {
    "readme.txt": ROOT / "app" / "downloads" / "readme.txt",
}

SESSION_SECRET = os.environ.get("AGILESEC_SESSION_SECRET") or secrets.token_urlsafe(48)
DEMO_PASSWORD = os.environ.get("AGILESEC_DEMO_PASSWORD") or secrets.token_urlsafe(16)
PBKDF2_ITERATIONS = 220_000
COOKIE_SECURE = os.environ.get("AGILESEC_COOKIE_SECURE", "false").lower() == "true"


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, salt_text: str, expected_text: str) -> bool:
    salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
    _, candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, expected_text)


def sign_session(username: str, issued_at: int | None = None) -> str:
    issued_at = issued_at or int(time.time())
    payload = json.dumps({"sub": username, "iat": issued_at}, separators=(",", ":"))
    signature = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return ".".join(
        [
            base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii"),
            base64.urlsafe_b64encode(signature).decode("ascii"),
        ]
    )


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    salt, password_hash = hash_password(DEMO_PASSWORD)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                notes TEXT NOT NULL
            )
            """
        )
        connection.execute("DELETE FROM users")
        connection.execute(
            "INSERT INTO users (username, password_salt, password_hash) VALUES (?, ?, ?)",
            ("demo", salt, password_hash),
        )
        if connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO customers (name, email, notes) VALUES (?, ?, ?)",
                [
                    ("Acme Bank", "pki-admin@acme.example", "Certificate automation migrated."),
                    ("Northwind IoT", "ops@northwind.example", "Device crypto inventory complete."),
                    ("Contoso Health", "security@contoso.example", "Signing keys moved to managed storage."),
                ],
            )


def render_layout(title: str, body: str) -> bytes:
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - AgileSec V2 Demo</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <header>
    <div>
      <p class="eyebrow">Keyfactor AgileSec demo target</p>
      <h1>Remediated Crypto Portal</h1>
    </div>
    <span class="badge">V2 fixed</span>
  </header>
  <main>{body}</main>
</body>
</html>"""
    return page.encode("utf-8")


class SecureDemoHandler(BaseHTTPRequestHandler):
    server_version = "AgileSecSecureDemo/2.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        routes = {
            "/": self.handle_home,
            "/customers": self.handle_customers,
            "/notes": self.handle_notes,
            "/download": self.handle_download,
            "/api/token": self.handle_token_status,
            "/static/styles.css": self.handle_styles,
        }
        handler = routes.get(parsed.path)
        if handler is None:
            self.respond_text("Not found", HTTPStatus.NOT_FOUND)
            return
        handler(parsed)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/login":
            self.respond_text("Not found", HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        username = form.get("username", [""])[0]
        password = form.get("password", [""])[0]

        with sqlite3.connect(DB_PATH) as connection:
            row = connection.execute(
                "SELECT password_salt, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if row is None or not verify_password(password, row[0], row[1]):
            self.respond_html(
                render_layout(
                    "Login failed",
                    "<section><h2>Login failed</h2><p>Check the one-time demo password printed by the server.</p></section>",
                ),
                HTTPStatus.UNAUTHORIZED,
            )
            return

        cookie = SimpleCookie()
        cookie["session"] = sign_session(username)
        cookie["session"]["path"] = "/"
        cookie["session"]["httponly"] = True
        cookie["session"]["samesite"] = "Strict"
        if COOKIE_SECURE:
            cookie["session"]["secure"] = True

        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", cookie.output(header=""))
        self.end_headers()

    def handle_home(self, parsed) -> None:
        session_present = "yes" if "session=" in self.headers.get("Cookie", "") else "no"
        body = f"""
<section class="panel hero">
  <div>
    <h2>Crypto asset service desk</h2>
    <p>This remediated portal keeps the same workflow while removing repository-stored cryptographic assets and unsafe implementation patterns.</p>
  </div>
  <dl>
    <div><dt>Private keys</dt><dd>Externalized</dd></div>
    <div><dt>Hashing</dt><dd>PBKDF2-HMAC-SHA256</dd></div>
    <div><dt>TLS policy</dt><dd>TLS 1.2+</dd></div>
  </dl>
</section>
<section class="grid">
  <form class="panel" method="post" action="/login">
    <h2>Demo login</h2>
    <label>Username <input name="username" value="demo" autocomplete="username"></label>
    <label>Password <input name="password" type="password" autocomplete="current-password"></label>
    <button type="submit">Sign in</button>
    <p class="muted">Session cookie present: {session_present}</p>
  </form>
  <form class="panel" method="get" action="/customers">
    <h2>Customer search</h2>
    <label>Query <input name="q" placeholder="Acme"></label>
    <button type="submit">Search</button>
  </form>
  <form class="panel" method="get" action="/notes">
    <h2>Support note preview</h2>
    <label>Message <input name="message" placeholder="Paste note text"></label>
    <button type="submit">Preview</button>
  </form>
  <form class="panel" method="get" action="/download">
    <h2>Config download</h2>
    <label>File <input name="file" value="readme.txt"></label>
    <button type="submit">Download</button>
  </form>
</section>
<section class="panel">
  <h2>Runtime security state</h2>
  <code>secrets=runtime-only; repository_keys=none; legacy_tls=disabled</code>
</section>
"""
        self.respond_html(render_layout("Home", body))

    def handle_customers(self, parsed) -> None:
        query = parse_qs(parsed.query).get("q", [""])[0]
        like_query = f"%{query}%"
        with sqlite3.connect(DB_PATH) as connection:
            rows = connection.execute(
                """
                SELECT id, name, email, notes FROM customers
                WHERE name LIKE ? OR email LIKE ?
                ORDER BY name
                """,
                (like_query, like_query),
            ).fetchall()

        list_items = "".join(
            "<tr>"
            f"<td>{row[0]}</td>"
            f"<td>{html.escape(row[1])}</td>"
            f"<td>{html.escape(row[2])}</td>"
            f"<td>{html.escape(row[3])}</td>"
            "</tr>"
            for row in rows
        )
        body = f"""
<section class="panel">
  <h2>Customer search results</h2>
  <p class="muted">Query: <code>{html.escape(query)}</code></p>
  <table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Notes</th></tr></thead><tbody>{list_items}</tbody></table>
</section>
"""
        self.respond_html(render_layout("Customers", body))

    def handle_notes(self, parsed) -> None:
        message = parse_qs(parsed.query).get("message", [""])[0]
        body = f"""
<section class="panel">
  <h2>Support note preview</h2>
  <div class="note">{html.escape(message)}</div>
</section>
"""
        self.respond_html(render_layout("Notes", body))

    def handle_download(self, parsed) -> None:
        requested = Path(parse_qs(parsed.query).get("file", ["readme.txt"])[0]).name
        target = DOWNLOADS.get(requested)
        if target is None:
            self.respond_text("Download is not allowed", HTTPStatus.FORBIDDEN)
            return

        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f"attachment; filename={requested}")
        self.end_headers()
        self.wfile.write(data)

    def handle_token_status(self, parsed) -> None:
        self.respond_json(
            {
                "api_key": "externalized",
                "session_signing": "runtime-only",
                "algorithm": "HMAC-SHA256",
                "repository_secret_material": "none",
            }
        )

    def handle_styles(self, parsed) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/css; charset=utf-8")
        self.end_headers()
        self.wfile.write((STATIC_DIR / "styles.css").read_bytes())

    def respond_html(self, content: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content)

    def respond_json(self, content: dict[str, str], status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(content).encode("utf-8"))

    def respond_text(self, content: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))


def main() -> None:
    initialize_database()
    port = int(os.environ.get("PORT", "8082"))
    print(f"AgileSec secure demo running at http://127.0.0.1:{port}")
    if "AGILESEC_DEMO_PASSWORD" not in os.environ:
        print(f"One-time demo password for user demo: {DEMO_PASSWORD}")
    server = ThreadingHTTPServer(("127.0.0.1", port), SecureDemoHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()

