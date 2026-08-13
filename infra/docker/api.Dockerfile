# Build context is the repo root (see docker-compose.yml) — required so
# `uv sync` can resolve apps/api/pyproject.toml + uv.lock in one COPY.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# git: required at runtime by GitPython (infrastructure/vcs/git_service.py)
# to clone/fetch repositories — not present in python:3.12-slim by default.
#
# deb.debian.org's Fastly edge 403s from some networks (ISP-level CDN
# block). ftp.debian.org mirrors the main archive on non-Fastly infra but
# doesn't carry /debian-security — that one goes to security.debian.org,
# which does.
RUN sed -i \
        -e 's#//deb\.debian\.org/debian-security#//security.debian.org/debian-security#g' \
        -e 's#//deb\.debian\.org/debian#//ftp.debian.org/debian#g' \
        /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Install dependencies before copying source so this layer is cached across
# source-only changes.
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY apps/api ./
RUN uv sync --frozen --no-dev

RUN useradd --create-home --uid 1000 lumora && chown -R lumora:lumora /app

# repo_storage mounts here (see docker-compose.yml). A fresh named volume
# is initialized from this path's ownership at first mount — without
# this, it comes up root-owned and every clone fails with EACCES since
# the process runs as lumora, not root.
RUN mkdir -p /data/repos && chown -R lumora:lumora /data/repos

USER lumora

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "lumora_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
