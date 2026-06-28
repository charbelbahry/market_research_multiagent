# syntax=docker/dockerfile:1

# ─────────────────────────────────────────────
# Stage 1: builder
# Install all dependencies into an isolated venv.
# This stage is discarded in the final image — build
# tools, compilers, and pip cache never reach production.
# ─────────────────────────────────────────────
FROM python:3.13-slim AS builder

# Prevent Python from writing .pyc files and buffering stdout.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv — the fastest dependency resolver/installer.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy only the dependency manifests first.
# Docker caches this layer and only re-runs `uv sync` when
# pyproject.toml or uv.lock actually changes — not on every
# code edit. This makes rebuilds dramatically faster.
COPY pyproject.toml uv.lock ./

# Install production dependencies only (no dev group).
# --no-install-project: skip installing the project itself
#   (we copy the source code next, so no need to install it here).
# --no-cache: don't store uv's download cache inside the image layer.
RUN uv sync --frozen --no-dev --no-install-project --no-cache

# Copy the application source code.
COPY app/ ./app/

# ─────────────────────────────────────────────
# Stage 2: runtime
# Lean final image. Only contains the venv + app code.
# ─────────────────────────────────────────────
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root system user with no shell and no home directory.
# Running as root inside a container is a security risk: if an attacker
# exploits the app they get root access to the container filesystem.
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --create-home --shell /sbin/nologin appuser

WORKDIR /app

# Copy the pre-built venv from the builder stage.
COPY --from=builder /app/.venv /app/.venv

# Copy the application source code, owned by the non-root user.
COPY --chown=appuser:appgroup --from=builder /app/app ./app

# Add the venv binaries to PATH so Python finds uvicorn directly.
ENV PATH="/app/.venv/bin:$PATH"

# Drop privileges — all subsequent commands run as appuser.
USER appuser

EXPOSE 8000

# Healthcheck: Docker/orchestrators can query this to know
# if the container is actually ready to serve traffic.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Use exec form (JSON array) to ensure signals (SIGTERM) reach uvicorn
# directly and not a shell wrapper — this allows graceful shutdown.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
