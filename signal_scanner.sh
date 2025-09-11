#!/bin/bash

# Signal Scanner Launcher
# Component #1: Analyzes 4H charts for new BUY signals
# Usage: ./signal_scanner.sh [--triggered-by-order]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/signal_scanner.log"
TIMEOUT_SECONDS=300

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check for triggered flag
TRIGGERED_FLAG=""
if [[ "$1" == "--triggered-by-order" ]]; then
    TRIGGERED_FLAG="--triggered-by-order"
    log_message "🔄 Signal Scanner triggered by ORDER COMPLETION"
else
    log_message "⏰ Signal Scanner triggered by SCHEDULE"
fi

log_message "🎯 SIGNAL SCANNER - Enhanced Quality over Quantity"
log_message "📊 4H Candle Analysis for Premium Trading Opportunities"
log_message "🚀 Starting signal scan..."

# Run Signal Scanner with timeout
if timeout "${TIMEOUT_SECONDS}s" uv run python -m src.components.signal_scanner $TRIGGERED_FLAG >> "$LOG_FILE" 2>&1; then
    exit_code=$?
    case $exit_code in
        0)
            log_message "✅ Signal Scanner completed successfully"
            ;;
        124)
            log_message "⏰ Signal Scanner timed out after ${TIMEOUT_SECONDS}s"
            ;;
        *)
            log_message "⚠️ Signal Scanner exited with code: $exit_code"
            ;;
    esac
else
    log_message "❌ Signal Scanner failed to start"
    exit 1
fi

log_message "🏁 Signal Scanner execution completed"