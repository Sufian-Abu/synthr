# Synthr gateway — single-stage, slim, non-root.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SYNTHR_CONFIG=/app/synthr.config.yaml

WORKDIR /app

# Install the package (pyproject + src layout). README is referenced by pyproject.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

# A baked default config so `docker run` boots out of the box; override by mounting your own.
COPY synthr.config.example.yaml /app/synthr.config.yaml

# Non-root + a writable data dir for the SQLite store.
RUN useradd --create-home app && mkdir -p /data && chown -R app /app /data
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

# __main__ binds 0.0.0.0 and reads the port from config (default 8000).
CMD ["python", "-m", "synthr_gateway"]
