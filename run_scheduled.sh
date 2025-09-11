#!/bin/bash

# Simple Trading Bot Runner for Cron
# Optimal timing for 4H candles: runs 5 minutes after candle close
# Vietnam Time Schedule: 03:05, 07:05, 11:05, 15:05, 19:05, 23:05

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/scheduled_runs.log"
TIMEOUT_SECONDS=300

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to run trading bot
run_trading_bot() {
    log_message "🚀 Starting scheduled trading bot run..."
    log_message "📂 Working directory: $SCRIPT_DIR"
    
    # Change to script directory
    cd "$SCRIPT_DIR" || {
        log_message "❌ Failed to change to script directory"
        exit 1
    }
    
    # Check if main.py exists
    if [[ ! -f "main.py" ]]; then
        log_message "❌ main.py not found in $SCRIPT_DIR"
        exit 1
    fi
    
    # Run the bot with timeout
    log_message "⏰ Running bot with ${TIMEOUT_SECONDS}s timeout..."
    
    # Try to run with uv first, fallback to direct python3 if uv fails
    if timeout "${TIMEOUT_SECONDS}s" bash -c "cd '$SCRIPT_DIR' && uv run --frozen python main.py" >> "$LOG_FILE" 2>&1; then
        exit_code=$?
        if [[ $exit_code -eq 0 ]]; then
            log_message "✅ Trading bot completed successfully"
        elif [[ $exit_code -eq 124 ]]; then
            log_message "⏰ Trading bot timed out after ${TIMEOUT_SECONDS}s"
        else
            log_message "⚠️ Trading bot exited with code: $exit_code"
        fi
    else
        log_message "❌ Failed to run trading bot with uv, trying direct python3..."
        # Fallback to python3 if uv fails
        if timeout "${TIMEOUT_SECONDS}s" bash -c "cd '$SCRIPT_DIR' && python3 main.py" >> "$LOG_FILE" 2>&1; then
            exit_code=$?
            if [[ $exit_code -eq 0 ]]; then
                log_message "✅ Trading bot completed successfully (fallback)"
            elif [[ $exit_code -eq 124 ]]; then
                log_message "⏰ Trading bot timed out after ${TIMEOUT_SECONDS}s (fallback)"
            else
                log_message "⚠️ Trading bot exited with code: $exit_code (fallback)"
            fi
        else
            log_message "❌ Failed to run trading bot with both uv and python3"
            exit 1
        fi
    fi
    
    log_message "🏁 Trading bot run completed"
    log_message "=================================="
}

# Main execution
main() {
    log_message "🎯 ENHANCED TRADING BOT - QUALITY OVER QUANTITY"
    log_message "⏰ Optimal 4H Candle Timing (Vietnam Time UTC+7)"
    log_message "📊 Running 5 minutes after candle close for complete data sync"
    
    # System checks
    if ! command -v uv &> /dev/null; then
        log_message "❌ UV package manager not found"
        exit 1
    fi
    
    # Run the bot
    run_trading_bot
}

# Execute main function
main "$@"
