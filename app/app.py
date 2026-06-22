from __future__ import annotations

import html
import os
import sqlite3
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from app.crypto_legacy import (
    DEMO_API_KEY,
    LEGACY_JWT,
    create_legacy_session_token,
    legacy_password_hash,
    legacy_sha1_signature,
)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "app" / "agilesec_demo.db"
STATIC_DIR = ROOT / "app" / "static"


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
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
        if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                ("demo", legacy_password_hash("Password123")),
            )
        if connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO customers (name, email, notes) VALUES (?, ?, ?)",
                [
                    ("Acme Bank", "pki-admin@acme.example", "Legacy TLS terminator renewal due."),
                    ("Northwind IoT", "ops@northwind.example", "Device fleet uses embedded certs."),
                    ("Contoso Health", "security@contoso.example", "Code signing key inventory pending."),
                ],
            )


def render_layout(title: str, body: str) -> bytes:
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - AgileSec V1 Demo</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <header>
    <div>
      <p class="eyebrow">Keyfactor AgileSec demo target</p>
      <h1>Insecure Crypto Portal</h1>
    </div>
    <span class="badge">V1 vulnerable</span>
  </header>
  <main>{body}</main>
</body>
</html>"""
    return page.encode("utf-8")


class DemoHandler(BaseHTTPRequestHandler):
    server_version = "AgileSecVulnerableDemo/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        routes = {
            "/": self.handle_home,
            "/customers": self.handle_customers,
            "/notes": self.handle_notes,
            "/download": self.handle_download,
            "/api/token": self.handle_token,
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
        password_hash = legacy_password_hash(password)

        with sqlite3.connect(DB_PATH) as connection:
            row = connection.execute(
                "SELECT username FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash),
            ).fetchone()

        if row is None:
            self.respond_html(render_layout("Login failed", "<section><h2>Login failed</h2><p>Try demo / Password123.</p></section>"), HTTPStatus.UNAUTHORIZED)
            return

        cookie = SimpleCookie()
        cookie["session"] = create_legacy_session_token(username, password)
        cookie["session"]["path"] = "/"
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", cookie.output(header=""))
        self.end_headers()

    def handle_home(self, parsed) -> None:
        session = self.headers.get("Cookie", "")
        body = f"""
<section class="panel hero">
  <div>
    <h2>Crypto asset service desk</h2>
    <p>This intentionally vulnerable portal gives AgileSec obvious cryptographic assets and weak policy signals to inventory.</p>
  </div>
  <dl>
    <div><dt>Committed key</dt><dd>RSA 1024</dd></div>
    <div><dt>Hashing</dt><dd>SHA-1 / MD5</dd></div>
    <div><dt>TLS policy</dt><dd>TLS 1.0</dd></div>
  </dl>
</section>
<section class="grid">
  <form class="panel" method="post" action="/login">
    <h2>Demo login</h2>
    <label>Username <input name="username" value="demo"></label>
    <label>Password <input name="password" type="password" value="Password123"></label>
    <button type="submit">Sign in</button>
    <p class="muted">Session cookie currently received: {html.escape(session or "none")}</p>
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
  <h2>Weak signature sample</h2>
  <code>{legacy_sha1_signature("demo payload")}</code>
</section>
"""
        self.respond_html(render_layout("Home", body))

    def handle_customers(self, parsed) -> None:
        query = parse_qs(parsed.query).get("q", [""])[0]
        sql = (
            "SELECT id, name, email, notes FROM customers "
            f"WHERE name LIKE '%{query}%' OR email LIKE '%{query}%'"
        )
        with sqlite3.connect(DB_PATH) as connection:
            rows = connection.execute(sql).fetchall()

        list_items = "".join(
            f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
            for row in rows
        )
        body = f"""
<section class="panel">
  <h2>Customer search results</h2>
  <p class="muted">Executed SQL: <code>{html.escape(sql)}</code></p>
  <table><thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Notes</th></tr></thead><tbody>{list_items}</tbody></table>
</section>
"""
        self.respond_html(render_layout("Customers", body))

    def handle_notes(self, parsed) -> None:
        message = parse_qs(parsed.query).get("message", [""])[0]
        body = f"""
<section class="panel">
  <h2>Support note preview</h2>
  <div class="note">{unquote(message)}</div>
</section>
"""
        self.respond_html(render_layout("Notes", body))

    def handle_download(self, parsed) -> None:
        requested = parse_qs(parsed.query).get("file", ["readme.txt"])[0]
        target = ROOT / "app" / "downloads" / requested
        try:
            data = target.read_bytes()
        except OSError as exc:
            self.respond_text(f"Could not read {target}: {exc}", HTTPStatus.NOT_FOUND)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f"attachment; filename={Path(requested).name}")
        self.end_headers()
        self.wfile.write(data)

    def handle_token(self, parsed) -> None:
        self.respond_json(
            f'{{"api_key":"{DEMO_API_KEY}","jwt":"{LEGACY_JWT}","algorithm":"HS256","warning":"hardcoded demo secrets"}}'
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

    def respond_json(self, content: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def respond_text(self, content: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))


def main() -> None:
    initialize_database()
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("127.0.0.1", port), DemoHandler)
    print(f"AgileSec vulnerable demo running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

