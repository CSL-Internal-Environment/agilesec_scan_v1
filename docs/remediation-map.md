# Remediation Map

Use this V2 directory as the "after" scan target.

## AgileSec-Focused Fixes

- Removed committed private keys and certificate fixtures.
- Replaced static source-code secrets with runtime environment variables or generated runtime values.
- Removed JWT-like fixture tokens and static API credentials from code and configuration.
- Updated TLS policy documentation to TLS 1.2+ with managed certificate and key sources.
- Replaced fast legacy digest usage with PBKDF2-HMAC-SHA256 for password storage.
- Uses HMAC-SHA256 for local demo session signing.

## App Security Fixes

- Customer search now uses parameterized SQL.
- Support note previews HTML-escape reflected content.
- Downloads are restricted to an explicit allowlist.
- Session cookies are `HttpOnly` and `SameSite=Strict`; set `AGILESEC_COOKIE_SECURE=true` when running behind HTTPS.
- `/api/token` reports redacted runtime status instead of returning secret material.

## Comparison Flow

1. Scan the repository root or V1 paths to show crypto assets, weak algorithms, and static secret material.
2. Scan `v2-secure/` to show the remediated state.
3. Compare the absence of repository keys, certificate fixtures, static tokens, and legacy TLS policy in V2.
