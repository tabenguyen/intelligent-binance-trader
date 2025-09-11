# Optimal Trading Bot Scheduling

## 4-Hour Candle Schedule (Vietnam Time - UTC+7)

The 4-hour candles on Binance close at the following times in Vietnam timezone:

- **07:00** (7:00 AM)
- **11:00** (11:00 AM)
- **15:00** (3:00 PM)
- **19:00** (7:00 PM)
- **23:00** (11:00 PM)
- **03:00** (3:00 AM)

## Recommended Bot Execution Times

**Run the bot 5 minutes after each candle close** to ensure all exchange data is fully updated:

- **07:05** (7:05 AM)
- **11:05** (11:05 AM)
- **15:05** (3:05 PM)
- **19:05** (7:05 PM)
- **23:05** (11:05 PM)
- **03:05** (3:05 AM)

## Why 5-Minute Delay?

The 5-minute delay ensures:

1. All market data from the exchange is fully synchronized
2. Technical indicators are calculated with complete candle data
3. No partial or incomplete data affects trading decisions
4. Reduces risk of execution based on preliminary data

## Implementation Options

### Option 1: Cron Job (Recommended)

Create a cron job to run the bot at optimal times:

```bash
# Edit crontab
crontab -e

# Add these lines for 4-hour schedule (Vietnam time)
5 3,7,11,15,19,23 * * * cd /home/tam/Workspaces/trading-bot-ai && /usr/bin/timeout 300s uv run python main.py >> logs/scheduled_runs.log 2>&1
```

### Option 2: Systemd Timer

Create a systemd service and timer:

```ini
# /etc/systemd/system/trading-bot.service
[Unit]
Description=Enhanced Trading Bot
After=network.target

[Service]
Type=oneshot
User=tam
WorkingDirectory=/home/tam/Workspaces/trading-bot-ai
ExecStart=/usr/bin/timeout 300s uv run python main.py
StandardOutput=append:/home/tam/Workspaces/trading-bot-ai/logs/scheduled_runs.log
StandardError=append:/home/tam/Workspaces/trading-bot-ai/logs/scheduled_runs.log

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/trading-bot.timer
[Unit]
Description=Run Enhanced Trading Bot every 4 hours
Requires=trading-bot.service

[Timer]
OnCalendar=*-*-* 03,07,11,15,19,23:05:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Option 3: Python Scheduler Script

Create a dedicated scheduler script:

```python
# scheduler.py
import schedule
import time
import subprocess
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_trading_bot():
    """Run the trading bot with timeout."""
    try:
        logging.info("🚀 Starting scheduled trading bot run...")
        result = subprocess.run(
            ['timeout', '300s', 'uv', 'run', 'python', 'main.py'],
            cwd='/home/tam/Workspaces/trading-bot-ai',
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logging.info("✅ Trading bot completed successfully")
        else:
            logging.warning(f"⚠️ Trading bot exited with code: {result.returncode}")

    except Exception as e:
        logging.error(f"❌ Error running trading bot: {e}")

# Schedule bot runs at optimal times (Vietnam timezone)
schedule.every().day.at("03:05").do(run_trading_bot)
schedule.every().day.at("07:05").do(run_trading_bot)
schedule.every().day.at("11:05").do(run_trading_bot)
schedule.every().day.at("15:05").do(run_trading_bot)
schedule.every().day.at("19:05").do(run_trading_bot)
schedule.every().day.at("23:05").do(run_trading_bot)

if __name__ == "__main__":
    logging.info("📅 Trading Bot Scheduler Started")
    logging.info("⏰ Scheduled times: 03:05, 07:05, 11:05, 15:05, 19:05, 23:05 (Vietnam time)")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
```

## Timezone Considerations

- **Vietnam Time (VTC)**: UTC+7
- **Binance Server Time**: Usually UTC
- **Important**: Ensure your server timezone is set correctly

```bash
# Check current timezone
timedatectl

# Set to Vietnam timezone if needed
sudo timedatectl set-timezone Asia/Ho_Chi_Minh
```

## Monitoring and Logs

### Check Bot Execution

```bash
# View recent scheduled runs
tail -f logs/scheduled_runs.log

# Check if bot is running
ps aux | grep python | grep main.py

# View system logs
journalctl -u trading-bot.service -f
```

### Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# Create logrotate config
sudo vim /etc/logrotate.d/trading-bot
```

```
/home/tam/Workspaces/trading-bot-ai/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 tam tam
}
```

## Best Practices

1. **Test Scheduling**: Run manually first to ensure everything works
2. **Monitor Resources**: Ensure server has sufficient resources
3. **Backup Strategy**: Keep backups of configuration and data
4. **Error Handling**: Implement proper error handling and notifications
5. **Health Checks**: Regular monitoring of bot performance

## Quick Start Commands

```bash
# 1. Test manual run
cd /home/tam/Workspaces/trading-bot-ai
uv run python main.py

# 2. Set up cron job (simplest option)
crontab -e
# Add: 5 3,7,11,15,19,23 * * * cd /home/tam/Workspaces/trading-bot-ai && timeout 300s uv run python main.py >> logs/scheduled_runs.log 2>&1

# 3. Create log directory if not exists
mkdir -p logs

# 4. Test cron timing
# Run this to see when next execution would be:
crontab -l
```

## Performance Optimization

Since the bot runs every 4 hours:

- **Cold Start**: Each run starts fresh (good for memory management)
- **Data Freshness**: Always uses latest market data
- **Resource Efficient**: No continuous resource consumption
- **Fault Tolerant**: Individual run failures don't affect subsequent runs

This schedule aligns perfectly with your enhanced "Quality over Quantity" strategy, ensuring the bot analyzes markets at optimal times when fresh 4-hour candle data is available!
