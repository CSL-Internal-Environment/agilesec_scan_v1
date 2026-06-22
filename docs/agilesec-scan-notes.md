# AgileSec Scan Notes

The current repository is intentionally vulnerable and should be scanned as the "before" state.

## Public Documentation Checked

The Keyfactor documentation landing page lists AgileSec as a product for security scanning and compliance that discovers and inventories cryptography. The AgileSec GitHub Sensor guide says it analyzes repositories for X.509 certificates, private keys, JWT/JWE tokens, cryptographic libraries, and embedded code artifacts. The generic Git Sensor guide lists the same repository crypto discovery goals for standard Git providers.

## Suggested Demo Scan Setup

Use the GitHub Sensor after pushing this repository to GitHub:

```yaml
sensorName: agilesec-vulnerable-demo
sensorType: Github Sensor
sensorConfig:
  url: https://api.github.com
  branch: main
  include_paths:
    - your-org/agilesec
incrementalScan: false
autoResolutionInterval: 5
```

Use the Git Sensor if scanning a direct Git URL:

```yaml
scan_config:
  plugins:
    - isg_git
    - trigger_discover
    - export
  config:
    isg_git:
      name: git
      plugin_config:
        url: https://github.com/your-org/agilesec.git
        branch: main
```

## V1 Findings To Look For

- Committed RSA private key in `certs/demo_rsa_1024_private_key.pem`
- Expired 1024-bit self-signed certificate in `certs/demo_sha1_self_signed.crt`
- TLS 1.0/1.1 and legacy cipher configuration in `config/tls-policy.conf`
- JWT-like token and hardcoded HMAC/API secrets in `app/crypto_legacy.py` and `config/secrets.env`
- SHA-1 and MD5 usage in `app/crypto_legacy.py`
- Insecure cookie flags, SQL injection, XSS, and path traversal in `app/app.py`
