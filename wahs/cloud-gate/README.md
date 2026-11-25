# WAHS Cloud Auth Gate & Workspace Portal (`wahs/cloud-gate`)

Standalone zero-dependency Python 3.12 HTTP service providing server-enforced Google account whitelist gating (`forward_auth`) and a workspace landing portal for the Google Cloud WA Health Summary deployment (`harness-chartsearch`).

## Endpoints

- `GET /healthz`: Container readiness check.
- `GET /auth/verify`: Caddy `forward_auth` verification endpoint checking HMAC-signed `wahs_gate_session` HttpOnly cookies against `WAHS_AUTH_WHITELIST_EMAILS`.
  - Returns `200` with `X-WAHS-Auth-Email` / `X-WAHS-Auth-Name` when authorized.
  - Returns `302` to `https://openclinai.org/wahs/gate/?next=...` for browser navigations or `401` JSON for `/api/*`, `/fhir/*`, `/shl-server/*`, or `Accept: application/json` requests when unauthorized.
- `GET /wahs/gate/`: Google Sign-In UI served under `https://openclinai.org/wahs/gate/` (authorized Firebase domain).
- `POST /wahs/gate/api/session`: Verifies Google/Firebase ID token against the whitelist and sets the cross-subdomain `.openclinai.org` session cookie.
- `GET /wahs/gate/logout` / `POST /wahs/gate/api/logout`: Clears the session cookie.
- `GET /` and `GET /api/portal-status`: Authenticated workspace landing page (`https://wahealth.openclinai.org/`) linking whitelisted users to the WA Health Summary Web App and Mobile Companion with live backend status and the 12 seeded demo patient credentials.
