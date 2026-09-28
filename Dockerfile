# ── Build ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .[dev]

# ── Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: non-root user
RUN groupadd --gid 1001 tremor \
    && useradd --uid 1001 --gid tremor --shell /bin/false tremor

WORKDIR /app

# Install production deps only
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && rm -rf /root/.cache

COPY app/ ./app/
COPY simulator/ ./simulator/
COPY eval/ ./eval/

# Create dirs for data
RUN mkdir -p /app/sample /app/data \
    && chown -R tremor:tremor /app

USER tremor

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
