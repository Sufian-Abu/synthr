# Synthr Playground (Next.js)

An interactive demo of **every Synthr feature**, called by name. Type a prompt, watch it work —
the app writes no prompts, holds no provider keys, and does no parsing. It just calls the gateway.

Features on the page:

- **Form autofill** — describe something in plain words; an actual form fills in (brand, size, color, in-stock).
- **Summarize**, **Translate**, **Rewrite**, **Generate**, **SEO metadata** — text in, result out.
- **Chat** — the OpenAI-compatible `/v1/chat/completions` endpoint.
- **Image generation** — prompt → image. Needs a **paid** image plan (Imagen on a paid Gemini account, or an OpenAI `gpt-image-1` key) — the free Gemini tier can't generate images.
- **Background removal** — upload an image → transparent PNG. Local & free via `rembg`; install the gateway's `vision` extra (`pip install -e '.[vision]'`, which now pulls `onnxruntime`).

## How it talks to the gateway

The browser only ever calls this app's own `app/api/run/route.ts`, which proxies to the gateway
**server-side with the secret key** — so the secret never reaches the browser:

```
Browser ──► /api/run (Next server, holds sk_) ──► Synthr gateway ──► provider
```

> **The dual-key model:** you can also call the gateway **directly from the browser** with a
> *public* key (`pk_proj_…`), which only works from an allow-listed origin and only for
> `frontend_safe` features. The gateway sends CORS for exactly those origins. This demo uses
> the server proxy for simplicity, but `pk_` + CORS is what makes browser-direct calls safe.

## Run it

1. Start a Synthr gateway from the repo root (`synthr-gateway` or `docker compose up`). It needs
   the demo keys and the features the page uses — the shipped `synthr.config.example.yaml` has
   them (text features run on any provider you've keyed; Groq/Gemini both work).
2. In this folder:
   ```bash
   cp .env.local.example .env.local      # points at the demo keys
   npm install                           # next + react (first run is slow)
   npm run dev                           # wait for: ✓ Ready ... http://localhost:3000
   ```
3. Open **http://localhost:3000** and try the cards — start with **Form autofill**.

## Troubleshooting

- **`http://localhost:3000` won't connect.** The dev server isn't running. Run `npm install` then
  `npm run dev`, and wait for `✓ Ready` before opening it.
- **`TypeError: Failed to fetch`.** The gateway isn't reachable or lacks CORS. Make sure it's
  running on `:8000`; if you call it browser-direct with a public key, restart it after editing
  `allowed_origins`.
- **A card returns `502` / provider error.** The gateway can't reach that feature's provider —
  add the provider's key to the gateway's `.env`, or set the feature's `provider: mock`.
  (Image needs an image-capable provider; text features work on Groq/Gemini.)
- **`401 invalid_key`.** The key in `.env.local` doesn't match the gateway config — use
  `sk_proj_demo_secret` or your own.
