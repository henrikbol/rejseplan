# Base image
FROM python:3.12-slim AS python-base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Add uv venv location to path
ENV PATH="/app/.venv/bin:$PATH"

###########################
FROM python-base AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen --no-dev --no-install-project

# ###############################
FROM python-base AS development

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=builder /app /app

WORKDIR /app
COPY ./app /app

RUN --mount=type=cache,target=/root/.cache uv sync --frozen

EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8088", "--log-level", "info", "--access-log"]