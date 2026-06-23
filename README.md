# AgileSec Secure Demo App

This directory is **V2: remediated code** for the Keyfactor AgileSec Analytics before-and-after demo. It keeps the same user-facing workflow as the vulnerable V1 app while removing the static cryptographic assets and insecure patterns that should produce policy findings.

## What Changed From V1

| Area | V1 vulnerable state | V2 fixed state |
| --- | --- | --- |
| Private key material | Private key committed in `certs/` | No private keys in the repository |
| Certificate handling | Expired self-signed certificate in source | Certificates are managed outside source control |
| Password storage | Fast unsalted digest | PBKDF2-HMAC-SHA256 with a per-user salt |
| Token signing | Hardcoded static secret | Runtime-generated or environment-provided secret |
| API/token endpoint | Returned static key and token | Returns only redacted runtime status |
| Session cookie | Missing security flags | `HttpOnly`, `SameSite=Strict`, and `Secure` when TLS is enabled |
| SQL access | String-concatenated query | Parameterized query |
| Reflected content | Unescaped user input | HTML escaped output |
| File access | Traversal through request parameter | Allowlisted downloads only |
| TLS policy | Legacy protocol and ciphers | TLS 1.2+ policy guidance |

## Run Locally

```powershell
.\v2-secure\run.ps1
```

Then open:

```text
http://127.0.0.1:8082
```

The server prints a one-time demo password at startup unless `AGILESEC_DEMO_PASSWORD` is set.

## Demo URLs

```text
http://127.0.0.1:8082/customers?q=Acme
http://127.0.0.1:8082/notes?message=<script>alert(1)</script>
http://127.0.0.1:8082/download?file=readme.txt
http://127.0.0.1:8082/api/token
```

The traversal URL that worked in V1 should fail in V2:

```text
http://127.0.0.1:8082/download?file=../../config/secrets.env
```

## AgileSec Demo Positioning

Scan V1 first to show cryptographic assets and policy issues. Scan `v2-secure/` after remediation to show that committed keys, certificate fixtures, static tokens, weak crypto references, and legacy TLS config have been removed from the fixed application path.
