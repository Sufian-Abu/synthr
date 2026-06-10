"""synthr CLI: init (scaffold config), keygen (make a project key), status (ping gateway)."""

from __future__ import annotations

import argparse
import hashlib
import secrets
import shutil
from pathlib import Path


def keygen(args: argparse.Namespace) -> None:
    public = getattr(args, "public", False)
    key = ("pk_proj_" if public else "sk_proj_") + secrets.token_hex(16)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    ktype = "public" if public else "secret"
    label = getattr(args, "label", None)
    scopes = getattr(args, "scopes", None)
    expires = getattr(args, "expires", None)

    # Line 1 is the raw key (shown once). The rest is a ready-to-paste config entry that
    # stores only the HASH — so the secret never has to live in synthr.config.yaml.
    print(key)
    print()
    print("# Shown once — copy the key above now. Add this under a project's `keys:`")
    print("# in synthr.config.yaml (it stores the hash, not the key):")
    print(f"  - type: {ktype}")
    print(f"    hash: {digest}")
    if label:
        print(f"    label: {label}")
    if public:
        print('    allowed_origins: ["https://your-app.example"]')
    if scopes:
        print(f"    scopes: [{', '.join(scopes)}]")
    if expires:
        print(f'    expires: "{expires}"')


def init(args: argparse.Namespace) -> None:
    for src, dst in [("synthr.config.example.yaml", "synthr.config.yaml"), (".env.example", ".env")]:
        target = Path(dst)
        if target.exists():
            print(f"• {dst} already exists — skipped")
        elif Path(src).exists():
            shutil.copy(src, dst)
            print(f"✓ created {dst} (from {src})")
        else:
            print(f"! {src} not found — run from the repo root")
    print("\nNext: add provider keys to .env, then `synthr-gateway` (or docker compose up).")


def status(args: argparse.Namespace) -> None:
    import httpx

    try:
        resp = httpx.get(f"{args.url.rstrip('/')}/health", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        print(f"✓ gateway up at {args.url}")
        print(f"  features:  {', '.join(data.get('features', []))}")
        print(f"  providers: {', '.join(data.get('providers', []))}")
    except Exception as exc:  # noqa: BLE001
        print(f"✗ gateway not reachable at {args.url}: {exc}")
        raise SystemExit(1) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synthr", description="Synthr gateway CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Scaffold synthr.config.yaml and .env").set_defaults(func=init)

    kg = sub.add_parser("keygen", help="Generate a project key (prints the key + a hashed config entry)")
    kg.add_argument("--public", action="store_true", help="Make a public (pk_proj_) browser key")
    kg.add_argument("--label", help="Human label for logs / audit (not secret)")
    kg.add_argument("--scopes", nargs="*", metavar="FEATURE", help="Restrict the key to these features")
    kg.add_argument("--expires", metavar="ISO_DATE", help="Expiry date, e.g. 2026-12-31")
    kg.set_defaults(func=keygen)

    st = sub.add_parser("status", help="Check a running gateway")
    st.add_argument("--url", default="http://localhost:8000", help="Gateway URL")
    st.set_defaults(func=status)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
