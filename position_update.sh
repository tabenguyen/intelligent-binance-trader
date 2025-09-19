#!/bin/bash
#
# Position Update Script for Cronjob
# This script runs the trading bot in position-only mode
# Designed to be executed every 15 minutes via crontab
#
# Usage: ./position_update.sh
# Crontab example: */15 * * * * /path/to/trading-bot-ai/position_update.sh

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the trading bot directory
cd "$SCRIPT_DIR" || exit 1

# Set environment for cronjob (optional)
export PATH="/usr/bin:/bin:/usr/local/bin:$HOME/.local/bin"

# Try to find uv or python3
if command -v uv >/dev/null 2>&1; then
    PYTHON_CMD="uv run python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "$(date): ERROR: No Python interpreter found" >> "$POSITION_LOG"
    exit 1
fi

# Log file for position updates
POSITION_LOG="logs/position_updates.log"

# Ensure logs directory exists
mkdir -p logs

# Run the trading bot in position-only mode
echo "$(date): Starting position update..." >> "$POSITION_LOG"

# Use timeout to prevent hanging processes (max 4 minutes for 5-minute cron)
timeout 240 $PYTHON_CMD main.py --positions-only >> "$POSITION_LOG" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date): Position update completed successfully" >> "$POSITION_LOG"
elif [ $EXIT_CODE -eq 124 ]; then
    echo "$(date): Position update timed out after 4 minutes" >> "$POSITION_LOG"
else
    echo "$(date): Position update failed with exit code $EXIT_CODE" >> "$POSITION_LOG"
fi

# Optional: Rotate log file if it gets too large (keep last 1000 lines)
if [ -f "$POSITION_LOG" ] && [ $(wc -l < "$POSITION_LOG") -gt 1000 ]; then
    tail -500 "$POSITION_LOG" > "${POSITION_LOG}.tmp" && mv "${POSITION_LOG}.tmp" "$POSITION_LOG"
fi

exit $EXIT_CODE