"""Console entrypoint: `python -m synthr_gateway` / `synthr-gateway`."""

from __future__ import annotations

import sys

import uvicorn

from .app import create_app
from .config import ConfigError


def main() -> None:
    try:
        app = create_app()
    except ConfigError as exc:
        print(f"\nConfiguration error:\n{exc}\n", file=sys.stderr)
        raise SystemExit(2) from None
    uvicorn.run(app, host="0.0.0.0", port=app.state.config.gateway.port)


if __name__ == "__main__":
    main()
