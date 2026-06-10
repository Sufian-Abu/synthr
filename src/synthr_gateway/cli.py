"""synthr CLI: init (scaffold config), keygen (make a project key), status (ping gateway)."""

from __future__ import annotations

import argparse
import secrets
import shutil
from pathlib import Path


def keygen(args: argparse.Namespace) -> None:
    prefix = "pk_proj_" if args.public else "sk_proj_"
    print(prefix + secrets.token_hex(16))


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
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synthr", description="Synthr gateway CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Scaffold synthr.config.yaml and .env").set_defaults(func=init)

    kg = sub.add_parser("keygen", help="Generate a project key")
    kg.add_argument("--public", action="store_true", help="Make a public (pk_proj_) browser key")
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
