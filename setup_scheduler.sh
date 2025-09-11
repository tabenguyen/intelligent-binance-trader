#!/bin/bash
"""
Setup script for Trading Bot Scheduler
Installs dependencies and sets up optimal scheduling
"""

echo "🔧 Setting up Trading Bot Scheduler..."

# Install Python schedule library
echo "📦 Installing schedule dependency..."
uv add schedule

# Make scheduler executable
chmod +x scheduler.py

# Create systemd service (optional)
create_systemd_service() {
    echo "⚙️ Creating systemd service..."
    
    cat > /tmp/trading-bot-scheduler.service << EOF
[Unit]
Description=Enhanced Trading Bot Scheduler
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which python3) $(pwd)/scheduler.py
Restart=always
RestartSec=10
StandardOutput=append:$(pwd)/logs/scheduler.log
StandardError=append:$(pwd)/logs/scheduler.log

[Install]
WantedBy=multi-user.target
EOF

    echo "📋 Systemd service file created at /tmp/trading-bot-scheduler.service"
    echo "To install system-wide, run:"
    echo "  sudo cp /tmp/trading-bot-scheduler.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable trading-bot-scheduler"
    echo "  sudo systemctl start trading-bot-scheduler"
}

# Create simple cron setup
create_cron_setup() {
    echo "⏰ Creating cron job setup..."
    
    cat > setup_cron.sh << 'EOF'
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
EOF
    
    chmod +x setup_cron.sh
    echo "📋 Cron setup script created: ./setup_cron.sh"
}

# Create logs directory
mkdir -p logs

# Setup options
echo ""
echo "🚀 Setup completed! Choose your preferred scheduling method:"
echo ""
echo "1️⃣ Python Scheduler (Recommended)"
echo "   • Run: python3 scheduler.py"
echo "   • Advanced error handling and logging"
echo "   • Easy to monitor and control"
echo ""
echo "2️⃣ Systemd Service (Linux servers)"
create_systemd_service
echo ""
echo "3️⃣ Cron Job (Simple setup)"
create_cron_setup
echo "   • Run: ./setup_cron.sh"
echo ""
echo "⏰ OPTIMAL TIMING (Vietnam Time):"
echo "   Bot runs 5 minutes after each 4H candle close:"
echo "   03:05, 07:05, 11:05, 15:05, 19:05, 23:05"
echo ""
echo "🎯 Enhanced Strategy: Quality over Quantity with 1.5:1 R:R minimum"
echo ""
echo "🔄 To start Python scheduler now:"
echo "   python3 scheduler.py"
