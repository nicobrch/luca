# syntax=docker/dockerfile:1

# 1. Build stage
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: sync exactly from uv.lock
# --no-install-project: do not install the project itself yet
RUN uv sync --frozen --no-install-project --no-dev

# 2. Run stage
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the application
# Using fastapi-cli which is included in fastapi[standard]
CMD ["fastapi", "run", "app/main.py", "--port", "8080"]
