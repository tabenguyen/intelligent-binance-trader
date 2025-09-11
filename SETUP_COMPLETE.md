# 🎯 Trading Bot Setup Complete - Enhanced Quality Over Quantity

## ✅ Dependencies Fixed

The dependency issues have been resolved:

- **Python Version**: Updated to 3.12+ (required for pandas-ta)
- **pandas**: Updated to >=2.3.2 (required for pandas-ta compatibility)
- **numpy**: Updated to >=2.2.6 (required for pandas-ta compatibility)
- **pandas-ta**: Using >=0.3.14 with pre-release support
- **schedule**: Successfully added for Python-based scheduling

## 🚀 Bot Execution Modes

### Default Mode: Single Execution (Scheduler-Controlled)

```bash
# Single execution - runs once and exits (default)
uv run python main.py
```

**Perfect for scheduled execution via cron or external schedulers**

### Legacy Mode: Continuous Loop

```bash
# Continuous mode with internal 1-hour loop (legacy)
uv run python main.py --continuous
```

**Only use for manual testing or special cases**

## 🎯 Optimal 4H Candle Scheduling - Vietnam Time (UTC+7)

### Schedule Overview

The bot is configured to run **5 minutes after each 4H candle close** for optimal data synchronization:

- **03:05** - After 03:00 candle close
- **07:05** - After 07:00 candle close
- **11:05** - After 11:00 candle close
- **15:05** - After 15:00 candle close
- **19:05** - After 19:00 candle close
- **23:05** - After 23:00 candle close

### Available Scheduling Options

#### 1. 🚀 Cron Jobs (Recommended - Most Reliable)

```bash
# Setup cron job
./setup_cron.sh

# View current cron jobs
crontab -l

# Remove cron job (if needed)
crontab -e  # Then delete the trading bot line
```

#### 2. 🐍 Python Scheduler (Advanced Features)

```bash
# Run Python scheduler in background
nohup python3 scheduler.py > logs/scheduler.log 2>&1 &

# Check scheduler status
ps aux | grep scheduler.py

# Test scheduler
python3 scheduler.py --test
```

#### 3. 🛠️ Manual/Testing

```bash
# Single run for testing
./run_scheduled.sh --test

# Manual execution (no timeout)
uv run python main.py
```

## 🏗️ Setup Instructions

### Step 1: Verify Dependencies

```bash
# Test bot execution (single run)
uv run python main.py
# Should complete one cycle and exit cleanly

# Test continuous mode (legacy)
timeout 10s uv run python main.py --continuous
# Should start loop and be terminated by timeout

# View help
uv run python main.py --help
```

### Step 2: Choose Scheduling Method

#### Option A: Cron (Recommended)

```bash
./setup_cron.sh
```

#### Option B: Python Scheduler

```bash
# Start scheduler daemon
nohup python3 scheduler.py > logs/scheduler.log 2>&1 &
echo $! > scheduler.pid
```

### Step 3: Monitor Execution

```bash
# View scheduled run logs
tail -f logs/scheduled_runs.log

# View bot output logs
tail -f logs/output_testnet.log

# Check cron logs (if using cron)
tail -f logs/cron_runs.log
```

## 📊 Enhanced Strategy Features

### Quality Over Quantity Focus

- **ATR Filter**: Only trades with ATR percentile 0.5%-5% (controlled volatility)
- **Volume Filter**: Requires 1.2x average volume (strong interest)
- **Enhanced Core Analysis**: 4 conditions, needs 3+ to pass:
  - Price well above 55-EMA (>2%)
  - Strong EMA uptrend (12>26 by >0.5%)
  - RSI optimal range (50-70)
  - Price very close to 26-EMA (≤2%)

### Risk Management

- **Fixed R:R Ratio**: 1.5:1 (Quality over Quantity)
- **Position Size**: $15 per trade (configurable)
- **Timeout Protection**: 300-second max execution time

## 🔧 Configuration Files

### Scheduling Scripts

- `run_scheduled.sh` - Main scheduler runner with timeout protection
- `setup_cron.sh` - Automated cron job setup
- `scheduler.py` - Advanced Python scheduler with health checks
- `setup_scheduler.sh` - Complete systemd service setup

### Logs

- `logs/scheduled_runs.log` - Scheduler execution logs
- `logs/cron_runs.log` - Cron job specific logs
- `logs/output_testnet.log` - Bot execution logs
- `logs/scheduler.log` - Python scheduler daemon logs

## 🚀 Quick Start

1. **Immediate Setup (Cron)**:

   ```bash
   ./setup_cron.sh
   ```

2. **Verify Next Run**:

   ```bash
   # Check when next scheduled run will occur
   ./run_scheduled.sh --test
   ```

3. **Monitor**:
   ```bash
   # Watch live logs
   tail -f logs/scheduled_runs.log
   ```

## 📈 Expected Behavior

- **Scan Frequency**: Every 4 hours at optimal times
- **Quality Focus**: Fewer but higher-quality trades
- **Auto Recovery**: Fallback mechanisms for failed executions
- **Comprehensive Logging**: Full audit trail of all operations

The bot is now ready for optimal 4H candle-based trading with enhanced quality filters!
