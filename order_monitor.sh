#!/bin/bash

# Order Monitor Launcher  
# Component #2: Continuously monitors order status
# Usage: ./order_monitor.sh [start|stop|status|logs]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/order_monitor.log"
PID_FILE="order_monitor.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if monitor is running
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

# Function to start the monitor
start_monitor() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_message $YELLOW "⚠️  Order Monitor is already running (PID: $pid)"
        return 1
    fi
    
    print_message $BLUE "👁️ Starting Order Monitor..."
    print_message $BLUE "🔄 Continuous monitoring of order status"
    print_message $BLUE "🎯 Will trigger Signal Scanner when orders complete"
    
    # Create backup of previous log if it exists
    if [ -f "$LOG_FILE" ]; then
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        cp "$LOG_FILE" "${LOG_FILE}.backup_${timestamp}"
        print_message $BLUE "📋 Previous log backed up as ${LOG_FILE}.backup_${timestamp}"
    fi
    
    # Start the monitor
    nohup uv run python -m src.components.order_monitor >> "$LOG_FILE" 2>&1 & echo $! > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_message $GREEN "✅ Order Monitor started successfully (PID: $pid)"
        print_message $BLUE "📋 Logs: tail -f $LOG_FILE"
        print_message $YELLOW "💡 Monitor will run continuously until stopped"
        return 0
    else
        print_message $RED "❌ Failed to start Order Monitor"
        return 1
    fi
}

# Function to stop the monitor
stop_monitor() {
    if ! is_running; then
        print_message $YELLOW "⚠️  Order Monitor is not running"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    print_message $BLUE "🛑 Stopping Order Monitor (PID: $pid)..."
    
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
        print_message $RED "❌ Failed to stop Order Monitor"
        return 1
    else
        print_message $GREEN "✅ Order Monitor stopped successfully"
        return 0
    fi
}

# Function to show monitor status
status_monitor() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_message $GREEN "✅ Order Monitor is running (PID: $pid)"
        
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
        print_message $RED "❌ Order Monitor is not running"
    fi
}

# Function to show logs
logs_monitor() {
    if [ -f "$LOG_FILE" ]; then
        print_message $BLUE "📋 Following Order Monitor logs (Press Ctrl+C to exit):"
        tail -f "$LOG_FILE"
    else
        print_message $YELLOW "⚠️  Log file not found: $LOG_FILE"
    fi
}

# Function to show usage
usage() {
    echo "Order Monitor Control Script"
    echo ""
    echo "Usage: $0 {start|stop|status|logs}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the Order Monitor"
    echo "  stop     - Stop the Order Monitor"
    echo "  status   - Show monitor status"
    echo "  logs     - Follow log output"
    echo ""
    echo "The Order Monitor:"
    echo "  - Runs continuously in the background"
    echo "  - Monitors order status every minute"
    echo "  - Automatically triggers Signal Scanner when orders complete"
    echo "  - This is Component #2 of the 2-Component Architecture"
    echo ""
}

# Main script logic
case "${1:-start}" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    status)
        status_monitor
        ;;
    logs)
        logs_monitor
        ;;
    *)
        usage
        exit 1
        ;;
esac