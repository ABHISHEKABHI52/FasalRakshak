# 12 · Security Architecture

Security posture for a system holding farmer PII, location data and photos. [PROPOSED DESIGN / ARCHITECT INFERENCE; aligned docs/00 §30–31]

## 1. Identity & Access

- **Authentication:** JWT access tokens (15 min, in-memory client) + rotating refresh tokens (httpOnly, Secure, SameSite=Strict cookie; hashed at rest; revocation on logout/rotation; reuse detection → revoke family).
- **Password hashing:** Argon2id (memory-hard); per-user salt; no password hints; generic login-failure messages.
- **RBAC:** five roles (farmer, extension_worker, expert, district_officer, admin); permissions matrix in docs/03 §2; enforced server-side by middleware + **row-level scoping in every service query** (owner | assigned | district | admin scopes). Frontend guards are UX only — never the enforcement point.
- **Least privilege:** experts see only assigned/queued cases; officers default to aggregates; identity-annotated officer access is a distinct audited permission; service-to-service calls use scoped internal tokens **[ADVANCED when services split]**.

## 2. Transport & API Hardening

| Control | Implementation |
|---|---|
| HTTPS | Nginx TLS 1.2+; HSTS; HTTP→HTTPS redirect; Let's Encrypt in deployment guide |
| Rate limiting | Nginx `limit_req` (global) + app-level per-user limits; stricter: login 5/min/IP, AI analyze 10/min/user, upload 20/h/user |
| CORS | Explicit origin allowlist; no wildcard + credentials |
| Headers | X-Content-Type-Options:nosniff, X-Frame-Options:DENY, Referrer-Policy:strict-origin-when-cross-origin, CSP (script-src 'self'; img-src 'self' data: tiles), Permissions-Policy (geolocation self) |
| Body limits | 10 MB upload cap (nginx + app); JSON depth/size limits |
| Injection prevention | SQLAlchemy ORM / bound parameters only; no dynamic SQL string building; PostGIS params bound; ORM guards NoSQL-style issues n/a |
| SSRF | Weather provider fixed allowlist of hosts; no user-supplied URLs fetched server-side |

## 3. File & Upload Security

1. **Type validation:** magic-byte check (JPEG/PNG/WebP only) — never trust client MIME/extension.
2. **Size cap:** 10 MB pre-decompression check; image dimensions capped.
3. **Re-encoding:** server-side decode→re-encode (strips EXIF including GPS, and any embedded payloads/polyglot tricks).
4. **Dedupe & storage keys:** SHA-256 checksum (also UX dedupe); random UUID storage keys; no user-controlled paths (path-traversal prevention).
5. **Serving:** images served through authenticated backend routes (signed short-lived URLs pattern when object store is adopted); no directory listing; no direct object-store public URLs at MVP.

## 4. Secrets & Configuration

`.env` per environment; secrets never in code or git; `.env.example` documents names only; production secrets via environment injection or a secret store; DB credentials least-privilege (app role without DDL in prod); model artifacts integrity via SHA-256 verification at boot; CI secret-scanning (gitleaks) **[P2]**.

## 5. Audit & Logging

- `audit_logs` append-only: auth events (login, refresh, logout, failures), permission denials (sampled), admin actions, expert verdicts, KB/model changes, data exports.
- Structured application logs exclude PII (phone hashed, names absent); request-id correlation; log retention documented.
- Expert/officer access to identity-annotated data produces audit rows (who/when/what).

## 6. Data-Access Rules (what farmers can and cannot access)

**Farmers CAN:** their own profile, farms, fields, scans, predictions, diagnoses, risks, advisories, notifications, feedback.
**Farmers CANNOT:** any other farmer's data (no listing endpoints exist), other users' data, expert queues, officer dashboards, GIS identity layers, audit logs, admin APIs, model registry.
**Enforcement:** no endpoint exists that returns cross-farmer lists to a farmer role; IDOR testing (docs/16) verifies ownership checks on every `/id` route; 404 (not 403) returned for out-of-scope resources to avoid enumeration.

## 7. Secure Error Handling

Generic client messages; stack traces only server-side; error envelope codes are stable and enumerated (docs/08 §11); no internal hostnames/SQL in responses; 5xx always correlated with request-id in logs.

## 8. Privacy Architecture

- **Data minimization:** collect only — phone (or email), name, preferred language, district/state, farm/field locations, crop images, answers. **Never:** Aadhaar/government IDs, precise home address, contacts, continuous location tracking, biometrics.
- **Location granularity:** GPS only at explicit registration/scan moments (not background); officer maps show pseudonymized fields; district aggregation default; exact coordinates = audited role permission.
- **Image privacy:** EXIF stripped client-side + server re-encode; ML-use consent flag per user (ask-on-first-scan default); images retained for scan lifetime; deletion request removes/anonymizes.
- **Consent & rights:** plain-language localized consent at registration; account deletion → personal data removed, artifacts anonymized (scan rows retained as research data without identity) or fully deleted on request [PROPOSED DESIGN]; data-export capability **[P2]**.
- **ML anonymization:** training exports carry no names/phones; region bucketing; farmer identity never enters datasets.
- **Third parties:** weather providers receive rounded coordinates (~2 dp ≈ 1 km) only; no identity; tile servers receive IP-based requests only (standard).
- **Residency:** deploy on Indian cloud region / on-prem (district server) — documented in docs/15.
