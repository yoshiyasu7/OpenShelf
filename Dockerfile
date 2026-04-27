# syntax=docker/dockerfile:1.10

ARG PYTHON_VERSION=3.14.0
ARG PYTHON_IMAGE_VARIANT=slim-bookworm

# ===== Builder Stage =====
# Export lock-based requirements and build runtime virtualenv.
FROM python:${PYTHON_VERSION}-${PYTHON_IMAGE_VARIANT} AS builder

# Base environment
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.2.1 \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependency export tooling
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install "poetry==${POETRY_VERSION}" "poetry-plugin-export>=1.9.0,<2.0.0"

COPY pyproject.toml poetry.lock ./

# Requirements export
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry export --only main --without-hashes -f requirements.txt --output requirements.txt

# Runtime venv assembly
RUN python -m venv /app/.venv

RUN --mount=type=cache,target=/root/.cache/pip \
    /app/.venv/bin/pip install --upgrade pip && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt


# ===== Runtime Stage =====
# Run app from prebuilt virtualenv under non-root user.
FROM python:${PYTHON_VERSION}-${PYTHON_IMAGE_VARIANT} AS runtime

# Base environment
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Service user
RUN groupadd --system app && useradd --system --gid app --home-dir /app --create-home app

WORKDIR /app

# Application payload
COPY --from=builder /app/.venv /app/.venv
COPY src /app/src
COPY static /app/static
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Bytecode + writable dirs
RUN python -m compileall -q /app/src && \
    mkdir -p /app/logs && \
    chown -R app:app /app

# Non-root execution
USER app

EXPOSE 8000

CMD ["python", "-m", "src.interfaces.main"]
