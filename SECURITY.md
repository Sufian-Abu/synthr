# Security

Synthr is a **working MVP**, not a hardened production system. This document is an honest
account of its security model — what it protects, what it does not yet protect, and how to
report a problem. Read it before exposing a gateway to untrusted traffic.

## What Synthr is designed to protect

- **Provider keys never leave the gateway.** Real API keys (Gemini, OpenAI, …) live only in
  `synthr.config.yaml` / `.env` on the server. Client apps hold *project keys*, not provider keys.
- **Project keys are stored hashed** (sha256), compared in constant time, and can carry
  **scopes** (limit a key to specific features), an **expiry**, and a **revoke** flag.
- **Two key types.**
  - `sk_proj_…` (secret) — backend/server use, full access.
  - `pk_proj_…` (public) — browser-safe; usable only from an allow-listed `Origin` and only for
    features marked `frontend_safe: true`.
- **Per-user / per-feature rate limits** to contain abuse and runaway cost.
- **Input guardrails** (PII / keyword / length) run *before* the model is called; **output PII
  redaction** runs before the response is returned. Blocks are logged.
- **Per-request cost logging** so spend is visible per project.

## Known limitations — do NOT assume these are handled

These are tracked in [ROADMAP.md](ROADMAP.md) under "Production hardening". Until they land:

| Area | Current state | Risk |
|---|---|---|
| **Key storage** | Keys are matched by sha256 **hash** (constant-time); production configs store only the hash. Keys support **scopes, expiry, and revoke**. | No *online* rotation or secret-manager integration; rotating means editing the config. |
| **Guardrails** | Regex PII/keyword only. | Will miss many real PII formats and adversarial inputs. **Not** a compliance control. |
| **Storage** | SQLite, single connection + lock. | Not built for concurrent multi-tenant write load. |
| **Transport** | The gateway speaks plain HTTP. | **Terminate TLS in front of it** (reverse proxy / load balancer). Never expose it directly. |
| **Multi-tenancy** | Projects share one process and one database. | Not isolation-hardened for *untrusted* tenants. |
| **DoS** | Rate limits are per user/feature, in-process. | No global throughput protection or circuit breaking yet. |
| **Audit** | Usage + guardrail/redaction events are logged. | No tamper-evident audit trail. |
| **Secrets** | Keys read from env / config files. | No KMS / secret-manager integration. |

## Deployment guidance

- Put Synthr **behind a TLS-terminating reverse proxy**; do not expose port 8000 directly.
- Treat `synthr.config.yaml` and `.env` as secrets — never commit them (the repo `.gitignore`
  excludes both). Rotate any key that has been shared in chat, logs, or screenshots.
- Use **public keys** (`pk_proj_`) for anything that reaches a browser, with a tight
  `allowed_origins` list. Use **secret keys** only on servers.
- Scope a deployment to a **single trusted team** until the production-hardening items ship.

## Production checklist

Before exposing a gateway beyond local dev, confirm:

- [ ] **Strong signing secret** — `SYNTHR_SECRET` set to a long random value (not `dev-secret`).
- [ ] **Hashed keys only** — every project key uses `hash:` (from `synthr keygen`), no plaintext `id:`.
- [ ] **Origins locked** — every public (`pk_proj_`) key has a tight `allowed_origins` list.
- [ ] **TLS in front** — a reverse proxy terminates HTTPS; port 8000 is not exposed directly.
- [ ] **Secrets uncommitted** — `.env` / `synthr.config.yaml` are git-ignored; provider keys live only on the server.
- [ ] **Limits set** — sensible per-user / per-feature rate limits for each project.
- [ ] **Preflight clean** — boot with `SYNTHR_ENV=production` (escalates warnings) and, in CI/CD, `SYNTHR_STRICT=1` (refuses to start on any of the above).

Synthr runs a security preflight on every boot and logs anything from this list that's still in dev mode.

## Key rotation

There is no online rotation yet (it's on the roadmap); rotate by editing config:

1. `synthr keygen --label <name>` → mint a new key; it prints the key once plus a `hash:` entry.
2. Add the new key entry to the project's `keys:` and deploy.
3. Update the client(s) to the new key.
4. Remove the old entry (or set `revoked: true` on it to kill it immediately and keep an audit trail).

Use `scopes:` to limit a key to specific features and `expires:` to force periodic rotation.

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Email the maintainer (see the
GitHub profile on the repo) with steps to reproduce. As a pre-1.0 MVP there is no formal SLA,
but reports are taken seriously and credited.
