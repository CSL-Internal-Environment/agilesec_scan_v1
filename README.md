# AgileSec Vulnerable Demo App

This repository is **V1: intentionally insecure code** for a Keyfactor AgileSec Analytics demo. It is designed to be uploaded to GitHub and scanned with the AgileSec GitHub or Git sensor so the first scan has clear cryptographic and application-security findings.

Do not deploy this app outside a local demo environment.

## Why This Exists

Keyfactor AgileSec documentation describes AgileSec as a security scanning and compliance platform for discovering and inventorying cryptography. The GitHub and Git sensor guides state that repository scans discover items such as X.509 certificates, private keys, JWT/JWE tokens, cryptographic libraries, and code artifacts embedded in source repositories.

This app deliberately includes those signals so a demo scan can show a before state. A later V2 should keep the same app behavior while removing or replacing the vulnerable patterns.

## Vulnerabilities Intentionally Included

| Area | V1 insecure implementation | Expected V2 direction |
| --- | --- | --- |
| Private key material | Demo RSA private key committed under `certs/` | Remove key from repo; use managed secrets/KMS |
| Certificate policy | 1024-bit SHA-1 self-signed demo certificate | Use CA-issued certs, modern key sizes, SHA-256+ |
| Password storage | Unsalted SHA-1 password hashes | PBKDF2, bcrypt, scrypt, or Argon2 with salt |
| Token signing | Hardcoded HMAC secret and SHA-1 signatures | Environment-backed secret and SHA-256+ |
| Session cookies | No `Secure`, `HttpOnly`, or `SameSite` flags | Hardened cookie attributes |
| TLS configuration | TLS 1.0 and legacy cipher strings in config | TLS 1.2/1.3 only and modern ciphers |
| SQL access | String-concatenated SQL query | Parameterized queries |
| XSS | Reflected user input is rendered unescaped | HTML escaping/templates |
| File access | Path traversal through unvalidated file input | Allowlisted paths |
| Secrets | API key and JWT-like token in source/config | Secret manager or environment variables |

## Run Locally

Requires Python 3.10+.

```powershell
.\run.ps1
```

Then open:

```text
http://127.0.0.1:8080
```

Useful demo URLs:

```text
http://127.0.0.1:8080/customers?q=Acme
http://127.0.0.1:8080/notes?message=<script>alert(1)</script>
http://127.0.0.1:8080/download?file=../config/secrets.env
http://127.0.0.1:8080/api/token
```

## AgileSec Scan Notes

For GitHub-hosted demos, use the AgileSec GitHub Sensor and include this repository path in `include_paths`. For local or generic Git demos, use the Git Sensor against the repository URL. The repo intentionally contains first-class crypto artifacts in `certs/`, weak algorithm references in `app/crypto_legacy.py`, and TLS/secrets configuration in `config/`.

## V2 Remediation Plan

V2 should keep the same user-facing pages and routes while:

1. Removing committed keys, certificates, API keys, and tokens.
2. Replacing SHA-1/MD5 usage with approved hashing/signing approaches.
3. Moving secrets to environment variables or a managed secret store.
4. Enforcing secure cookie flags.
5. Parameterizing database access.
6. Escaping output.
7. Restricting file downloads to an allowlisted directory.
8. Updating TLS policy to TLS 1.2/1.3 and modern cipher suites.
