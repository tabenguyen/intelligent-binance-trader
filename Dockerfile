# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package installer)
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Copy application files
COPY trading_bot.py .
COPY watchlist.txt .

# Create directory for persistent data
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash trading-bot
RUN chown -R trading-bot:trading-bot /app
USER trading-bot

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=1m --retries=3 \
    CMD python -c "import trading_bot; print('Bot is healthy')" || exit 1

# Run the trading bot
CMD ["uv", "run", "python", "trading_bot.py"]
