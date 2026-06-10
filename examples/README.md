# Using Synthr from any stack

The same gateway, consumed three ways. Start it first:

```bash
uvicorn "synthr_gateway.app:create_app" --factory --port 8000
```

Then:

| Client | File | Run |
|---|---|---|
| REST / curl | `rest.sh` | `bash examples/rest.sh` |
| Backend (Python) | `backend.py` | `python examples/backend.py` |
| Frontend (JS `fetch`) | `frontend.mjs` / `frontend.html` | `node examples/frontend.mjs` — or open the HTML |

Backend/REST use the **secret** key (`sk_proj_…`). The browser uses the **public** key
(`pk_proj_…`) and only works from an allowed origin (here `http://localhost:3000`).
