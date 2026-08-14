# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /build
RUN python -m venv /opt/venv
COPY pyproject.toml README.md ./
COPY living_objects ./living_objects
COPY evolution ./evolution
COPY production ./production
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir ".[production]"

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=prod \
    PORT=8000
RUN groupadd --system --gid 10001 living && \
    useradd --system --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin living
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY living_objects ./living_objects
COPY evolution ./evolution
COPY production ./production
COPY pyproject.toml README.md ./
RUN mkdir -p /app/state && chown -R living:living /app
USER living
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "production.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

