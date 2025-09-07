#!/bin/bash

# Trading Bot Start/Restart Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="nohup.pid"
LOG_FILE="logs/output.log"
PYTHON_CMD="uv run python main.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if bot is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            # PID file exists but process is not running
            rm -f "$PID_FILE"
            return 1  # Not running
        fi
    else
        return 1  # Not running
    fi
}

# Function to start the bot
start_bot() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_message $YELLOW "⚠️  Trading bot is already running (PID: $pid)"
        return 1
    fi
    
    print_message $BLUE "🚀 Starting trading bot..."
    
    # Create backup of previous log if it exists
    if [ -f "$LOG_FILE" ]; then
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        cp "$LOG_FILE" "${LOG_FILE}.backup_${timestamp}"
        print_message $BLUE "📋 Previous log backed up as ${LOG_FILE}.backup_${timestamp}"
    fi
    
    # Start the bot
    nohup $PYTHON_CMD >> "$LOG_FILE" 2>&1 & echo $! > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_message $GREEN "✅ Trading bot started successfully (PID: $pid)"
        print_message $BLUE "📋 Logs: tail -f $LOG_FILE"
        return 0
    else
        print_message $RED "❌ Failed to start trading bot"
        return 1
    fi
}

# Function to start the bot in development mode (foreground)
start_dev() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_message $YELLOW "⚠️  Trading bot is already running in background (PID: $pid)"
        print_message $YELLOW "     Please stop it first with: $0 stop"
        return 1
    fi
    
    print_message $BLUE "🚀 Starting trading bot in DEVELOPMENT mode..."
    print_message $YELLOW "⚠️  Running in foreground - Press Ctrl+C to stop"
    print_message $BLUE "📋 Logs will be displayed in real-time"
    echo ""
    
    # Run directly in foreground with real-time output
    exec $PYTHON_CMD
}

# Function to stop the bot
stop_bot() {
    if ! is_running; then
        print_message $YELLOW "⚠️  Trading bot is not running"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    print_message $BLUE "🛑 Stopping trading bot (PID: $pid)..."
    
    # Try graceful shutdown first
    kill "$pid" 2>/dev/null
    
    # Wait up to 10 seconds for graceful shutdown
    local count=0
    while [ $count -lt 10 ] && ps -p "$pid" > /dev/null 2>&1; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        print_message $YELLOW "⚠️  Forcing shutdown..."
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi
    
    # Clean up PID file
    rm -f "$PID_FILE"
    
    if ps -p "$pid" > /dev/null 2>&1; then
        print_message $RED "❌ Failed to stop trading bot"
        return 1
    else
        print_message $GREEN "✅ Trading bot stopped successfully"
        return 0
    fi
}

# Function to restart the bot
restart_bot() {
    print_message $BLUE "🔄 Restarting trading bot..."
    stop_bot
    sleep 2
    start_bot
}

# Function to show bot status
status_bot() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_message $GREEN "✅ Trading bot is running (PID: $pid)"
        
        # Show some basic stats
        if [ -f "$LOG_FILE" ]; then
            local log_lines=$(wc -l < "$LOG_FILE" 2>/dev/null || echo "0")
            local log_size=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1 || echo "0B")
            print_message $BLUE "📋 Log file: $log_lines lines, $log_size"
            
            # Show last few log entries
            print_message $BLUE "📋 Recent log entries:"
            tail -n 3 "$LOG_FILE" 2>/dev/null | sed 's/^/   /'
        fi
    else
        print_message $RED "❌ Trading bot is not running"
    fi
}

# Function to show logs
logs_bot() {
    if [ -f "$LOG_FILE" ]; then
        print_message $BLUE "📋 Following log file (Press Ctrl+C to exit):"
        tail -f "$LOG_FILE"
    else
        print_message $YELLOW "⚠️  Log file not found: $LOG_FILE"
    fi
}

# Function to show usage
usage() {
    echo "Trading Bot Control Script"
    echo ""
    echo "Usage: $0 {start|dev|stop|restart|status|logs}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the trading bot in background"
    echo "  dev      - Start the trading bot in development mode (foreground)"
    echo "  stop     - Stop the trading bot"
    echo "  restart  - Restart the trading bot"
    echo "  status   - Show bot status"
    echo "  logs     - Follow log output"
    echo ""
    echo "Development Mode:"
    echo "  ./start.sh dev   - Run in foreground with real-time logs"
    echo "                   - Press Ctrl+C to stop"
    echo "                   - No background process created"
    echo ""
}

# Main script logic
case "${1:-start}" in
    start)
        start_bot
        ;;
    dev)
        start_dev
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    logs)
        logs_bot
        ;;
    *)
        usage
        exit 1
        ;;
esac