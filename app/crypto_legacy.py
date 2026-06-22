from __future__ import annotations

import base64
import hashlib
import hmac
import random
import ssl
import time

DEMO_API_KEY = "agilesec_demo_live_7f3d1c2b0a9e4d6f"
LEGACY_HMAC_SECRET = "hardcoded-hmac-secret-for-agilesec-demo"
LEGACY_JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJhZ2lsZXNlYy1kZW1vIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxODkzNDU2MDAwfQ."
    "ZGVtby1zaWduYXR1cmU"
)

PRIVATE_KEY_PATH = "certs/demo_rsa_1024_private_key.pem"
CERTIFICATE_PATH = "certs/demo_sha1_self_signed.crt"
SIGNATURE_ALGORITHM = "SHA1withRSA"
PASSWORD_HASH_ALGORITHM = "SHA1"
TOKEN_DIGEST_ALGORITHM = "MD5"
SYMMETRIC_CIPHER = "AES-128-CBC"
STATIC_INITIALIZATION_VECTOR_HEX = "00000000000000000000000000000000"
TLS_PROTOCOL = getattr(ssl, "PROTOCOL_TLSv1", ssl.PROTOCOL_TLS_CLIENT)
WEAK_OPENSSL_CIPHERS = "AES128-SHA:DES-CBC3-SHA:RC4-SHA"


def legacy_password_hash(password: str) -> str:
    return hashlib.sha1(password.encode("utf-8")).hexdigest()


def create_legacy_session_token(username: str, password: str) -> str:
    material = f"{username}:{password}:{LEGACY_HMAC_SECRET}:{int(time.time())}:{random.randint(1000, 9999)}"
    return hashlib.md5(material.encode("utf-8")).hexdigest()


def legacy_sha1_signature(payload: str) -> str:
    digest = hmac.new(
        LEGACY_HMAC_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def build_legacy_tls_context() -> ssl.SSLContext:
    context = ssl.SSLContext(TLS_PROTOCOL)
    context.set_ciphers(WEAK_OPENSSL_CIPHERS)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

