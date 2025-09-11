#!/bin/bash
# Add trading bot to crontab
# Runs at: 03:05, 07:05, 11:05, 15:05, 19:05, 23:05 (Vietnam time)

CURRENT_DIR=$(pwd)
CRON_JOB="5 3,7,11,15,19,23 * * * cd $CURRENT_DIR && timeout 300s uv run python main.py >> logs/cron_runs.log 2>&1"

# Add to crontab if not already present
(crontab -l 2>/dev/null | grep -v "$CURRENT_DIR.*main.py"; echo "$CRON_JOB") | crontab -

echo "✅ Cron job added:"
echo "$CRON_JOB"
echo ""
echo "📋 Current crontab:"
crontab -l
