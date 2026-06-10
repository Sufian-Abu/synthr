# Next.js + Synthr — the dual-key flow

A minimal Next.js (App Router) app showing the two ways a real product talks to Synthr,
and **why there are two key types**:

1. **Server → secret key (`sk_proj_…`).** A Route Handler (`app/api/summarize/route.ts`)
   runs on the server, holds the secret key, and calls Synthr. The key never reaches the
   browser. Use this for backend-only features (e.g. `image`) and anything sensitive.

2. **Browser → public key (`pk_proj_…`).** A client component calls Synthr **directly** with
   a public key. Public keys only work from an allow-listed `Origin` and only for features
   marked `frontend_safe: true` in `synthr.config.yaml` — so it's safe to ship in client JS.

```
Browser ──(public pk_)────────────────► Synthr   (frontend_safe features only, origin-checked)
Browser ──► Next.js route ──(secret sk_)► Synthr   (everything; secret key stays server-side)
```

## Run it

1. Start a Synthr gateway (from the repo root): `docker compose up` — the shipped demo config
   already defines `sk_proj_demo_secret`, `pk_proj_demo_public` (origin `http://localhost:3000`),
   and a `summarize` + `fillForm` feature.
2. In this folder:
   ```bash
   cp .env.local.example .env.local
   npm install        # pulls synthr-sdk from ../../sdk/typescript
   npm run dev        # http://localhost:3000
   ```
3. Click **Summarize (via server)** and **Fill form (browser, public key)**.

## What to notice

- `SYNTHR_SECRET_KEY` has **no** `NEXT_PUBLIC_` prefix — Next.js keeps it server-only. The
  secret key is never in the bundle.
- `NEXT_PUBLIC_SYNTHR_PUBLIC_KEY` *is* exposed to the browser — that's fine, because it's a
  public key restricted by origin + `frontend_safe`. Try calling a backend-only feature
  (like `image`) with it and Synthr returns `feature_not_allowed`.
