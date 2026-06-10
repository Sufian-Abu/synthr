"""Console entrypoint: `python -m synthr_gateway` / `synthr-gateway`."""

from __future__ import annotations

import uvicorn

from .app import create_app


def main() -> None:
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=app.state.config.gateway.port)


if __name__ == "__main__":
    main()
