# Multi-stage build: Use uv official image for dependencies
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Set environment variables for uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from builder stage
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN useradd --create-home --shell /bin/bash --uid 1000 trading-bot && \
    mkdir -p /app/data /app/logs && \
    chown -R trading-bot:trading-bot /app

# Switch to non-root user
USER trading-bot

# Activate the virtual environment by default
ENV PATH="/app/.venv/bin:$PATH"

# Run the trading bot using the virtual environment directly
CMD ["python", "trading_bot.py"]
