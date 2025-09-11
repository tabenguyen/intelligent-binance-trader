#!/bin/bash

# 2-Component Architecture Setup Script
# Professional Trading Bot Architecture

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🏗️ 2-COMPONENT ARCHITECTURE SETUP                        ║"
    echo "║                     Professional Trading Bot System                        ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_step() {
    local step=$1
    local message=$2
    echo -e "${BLUE}${BOLD}[STEP $step]${NC} ${message}"
}

setup_permissions() {
    print_step "1" "Setting up script permissions..."
    
    chmod +x signal_scanner.sh
    chmod +x order_monitor.sh
    chmod +x setup_cron.sh
    
    print_message $GREEN "✅ Script permissions configured"
}

setup_directories() {
    print_step "2" "Creating directory structure..."
    
    mkdir -p logs
    mkdir -p config
    
    print_message $GREEN "✅ Directory structure created"
}

setup_cron_jobs() {
    print_step "3" "Setting up cron jobs for Signal Scanner..."
    
    # Remove existing cron jobs for this project
    crontab -l 2>/dev/null | grep -v "$SCRIPT_DIR" | crontab -
    
    # Add Signal Scanner cron job (4H schedule)
    CRON_JOB="5 3,7,11,15,19,23 * * * cd $SCRIPT_DIR && ./signal_scanner.sh >> logs/cron_signal_scanner.log 2>&1"
    
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    
    print_message $GREEN "✅ Signal Scanner scheduled for 4H intervals:"
    print_message $YELLOW "   🕐 03:05, 07:05, 11:05, 15:05, 19:05, 23:05 (Vietnam Time)"
}

show_architecture_info() {
    print_step "4" "Architecture Overview"
    
    echo ""
    print_message $CYAN "🏗️ 2-COMPONENT PROFESSIONAL ARCHITECTURE:"
    echo ""
    
    print_message $BLUE "📊 COMPONENT #1: Signal Scanner"
    print_message $NC "   • Task: Analyze 4H charts and find new BUY signals"
    print_message $NC "   • Frequency: Every 4 hours (scheduled via cron)"
    print_message $NC "   • Trigger: Also triggered immediately when orders complete"
    print_message $NC "   • Logic: Market analysis + Place buy orders when USDT available"
    echo ""
    
    print_message $BLUE "👁️  COMPONENT #2: Order Monitor"
    print_message $NC "   • Task: Continuously monitor order status"
    print_message $NC "   • Frequency: Every minute (background daemon)"
    print_message $NC "   • Logic: Detect order completion and trigger Signal Scanner"
    print_message $NC "   • Magic: Immediate reinvestment when TP/SL orders fill"
    echo ""
    
    print_message $YELLOW "🔄 THE MAGIC CONNECTION:"
    print_message $NC "   When Order Monitor detects a completed order (TP/SL filled),"
    print_message $NC "   it immediately triggers Signal Scanner to look for new opportunities"
    print_message $NC "   without waiting for the 4H schedule!"
    echo ""
}

show_usage_instructions() {
    print_step "5" "Usage Instructions"
    
    echo ""
    print_message $GREEN "🚀 STARTING THE SYSTEM:"
    echo ""
    
    print_message $CYAN "1. Start Order Monitor (runs continuously):"
    print_message $NC "   ./order_monitor.sh start"
    echo ""
    
    print_message $CYAN "2. Signal Scanner runs automatically via cron"
    print_message $NC "   Next scheduled runs: $(date -d 'today 03:05' '+%Y-%m-%d %H:%M'), $(date -d 'today 07:05' '+%Y-%m-%d %H:%M'), $(date -d 'today 11:05' '+%Y-%m-%d %H:%M')"
    echo ""
    
    print_message $CYAN "3. Test Signal Scanner manually (optional):"
    print_message $NC "   ./signal_scanner.sh"
    echo ""
    
    print_message $GREEN "📊 MONITORING THE SYSTEM:"
    echo ""
    
    print_message $CYAN "• Monitor Order Monitor:"
    print_message $NC "   ./order_monitor.sh status"
    print_message $NC "   ./order_monitor.sh logs"
    echo ""
    
    print_message $CYAN "• Monitor Signal Scanner:"
    print_message $NC "   tail -f logs/signal_scanner.log"
    print_message $NC "   tail -f logs/cron_signal_scanner.log"
    echo ""
    
    print_message $GREEN "🛑 STOPPING THE SYSTEM:"
    echo ""
    
    print_message $CYAN "• Stop Order Monitor:"
    print_message $NC "   ./order_monitor.sh stop"
    echo ""
    
    print_message $CYAN "• Remove cron jobs (if needed):"
    print_message $NC "   crontab -e  # Delete the signal scanner line"
    echo ""
}

verify_setup() {
    print_step "6" "Verifying setup..."
    
    # Check if bot can run
    print_message $YELLOW "🧪 Testing bot execution..."
    
    # Create a temporary log file to capture output
    TEMP_LOG=$(mktemp)
    
    if timeout 15s uv run python main.py > "$TEMP_LOG" 2>&1; then
        # Check if the bot actually started and ran successfully
        if grep -q "Starting bot in SCHEDULED mode" "$TEMP_LOG" && grep -q "STOPPING TRADING BOT" "$TEMP_LOG"; then
            print_message $GREEN "✅ Bot execution test passed"
            # Show key stats from the test
            SIGNALS_FOUND=$(grep -o "Found [0-9]* valid signals" "$TEMP_LOG" | grep -o "[0-9]*" || echo "0")
            CYCLE_TIME=$(grep -o "CYCLE #1 COMPLETED in [0-9.]*s" "$TEMP_LOG" | grep -o "[0-9.]*s" || echo "unknown")
            print_message $CYAN "   📊 Test results: $SIGNALS_FOUND signals found, completed in $CYCLE_TIME"
        else
            print_message $RED "❌ Bot execution incomplete - check logs for issues"
            echo "Last few lines of output:"
            tail -5 "$TEMP_LOG"
            rm -f "$TEMP_LOG"
            return 1
        fi
    else
        print_message $RED "❌ Bot execution failed - check dependencies"
        echo "Error output:"
        tail -10 "$TEMP_LOG"
        rm -f "$TEMP_LOG"
        return 1
    fi
    
    rm -f "$TEMP_LOG"
    
    # Check cron job
    if crontab -l 2>/dev/null | grep -q "signal_scanner.sh"; then
        print_message $GREEN "✅ Cron job configured"
    else
        print_message $RED "❌ Cron job not found"
        return 1
    fi
    
    print_message $GREEN "✅ Setup verification complete"
}

main() {
    print_header
    
    echo -e "${YELLOW}This will set up the professional 2-component trading bot architecture.${NC}"
    echo -e "${YELLOW}Components: Signal Scanner (4H scheduled) + Order Monitor (continuous)${NC}"
    echo ""
    read -p "Continue with setup? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message $YELLOW "Setup cancelled."
        exit 0
    fi
    
    echo ""
    
    setup_permissions
    setup_directories
    setup_cron_jobs
    show_architecture_info
    show_usage_instructions
    
    if verify_setup; then
        echo ""
        print_message $GREEN "${BOLD}🎉 2-COMPONENT ARCHITECTURE SETUP COMPLETE!"
        print_message $CYAN "Your professional trading bot system is ready to use."
        echo ""
        print_message $YELLOW "Next steps:"
        print_message $NC "1. Start Order Monitor: ./order_monitor.sh start"
        print_message $NC "2. Signal Scanner will run automatically via cron"
        print_message $NC "3. Monitor logs: ./order_monitor.sh logs"
        echo ""
    else
        print_message $RED "❌ Setup completed with errors. Please check the issues above."
        exit 1
    fi
}

main "$@"