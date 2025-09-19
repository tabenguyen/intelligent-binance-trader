# Position-Only Mode

The trading bot supports a special "position-only" mode designed for frequent monitoring of existing positions without scanning for new trading opportunities.

## Overview

Position-only mode performs only the "UPDATING EXISTING POSITIONS" functionality:

- Checks current prices for all active positions
- Updates P&L calculations
- Monitors OCO order status
- Executes position exits when conditions are met
- Sends notifications for completed trades

**What it DOES:**

- ✅ Update existing position prices and P&L
- ✅ Check OCO order status
- ✅ Close positions when stop-loss/take-profit is hit
- ✅ Send trade completion notifications
- ✅ Create missing OCO orders for unprotected positions

**What it DOES NOT do:**

- ❌ Refresh watchlist
- ❌ Scan for new trading signals
- ❌ Execute new trades
- ❌ Run technical analysis on new symbols

## Usage

### Command Line

```bash
# Run position update once
python main.py --positions-only

# Or using uv
uv run python main.py --positions-only
```

### Environment Variable

```bash
# Set in .env file
POSITION_ONLY_MODE=true

# Then run normally
python main.py
```

### Cronjob Setup (Recommended)

For automated position monitoring every 5 minutes:

1. **Make the script executable:**

   ```bash
   chmod +x position_update.sh
   ```

2. **Add to crontab:**

   ```bash
   crontab -e
   ```

3. **Add this line to run every 5 minutes:**

   ```
   */5 * * * * /path/to/trading-bot-ai/position_update.sh
   ```

4. **Alternative: Run every 2 minutes for more responsive monitoring:**
   ```
   */2 * * * * /path/to/trading-bot-ai/position_update.sh
   ```

## Configuration

### Environment Variables

```bash
# Enable position-only mode
POSITION_ONLY_MODE=true

# Telegram notifications (recommended for position updates)
ENABLE_TELEGRAM_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Minimal required configuration
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
USE_TESTNET=true  # or false for live trading
```

### Logging

Position updates are logged to:

- Main log file: `logs/output_testnet.log` (or `output_live.log`)
- Position-specific log: `logs/position_updates.log` (when using the script)

## Benefits

### 1. **Responsive Position Management**

- Quick response to market movements
- Faster exit execution
- Reduced slippage on stop-losses

### 2. **Resource Efficient**

- Minimal API calls
- Fast execution (typically < 10 seconds)
- Low system resource usage

### 3. **Reliable Monitoring**

- Handles network interruptions gracefully
- Automatic OCO order recovery
- Comprehensive error handling

### 4. **Safe for Frequent Execution**

- No risk of creating duplicate positions
- Read-only market data operations
- Minimal rate limit impact

## Monitoring and Troubleshooting

### Log Analysis

Check position update logs:

```bash
# View recent position updates
tail -f logs/position_updates.log

# Check for errors
grep -i error logs/position_updates.log

# Monitor OCO order status
grep -i "OCO" logs/output_testnet.log
```

### Common Scenarios

#### No Active Positions

```
📊 No active positions to update
```

This is normal when no trades are active.

#### OCO Order Completed

```
✅ OCO order completed for BTCUSDT (Status: ALL_DONE)
📡 Trade notification sent
```

Position was automatically closed by stop-loss or take-profit.

#### Missing OCO Order

```
⚠️ No OCO orders found for BTCUSDT - position has no exit protection
🔧 Attempting to create missing OCO order...
```

Bot will try to recreate missing protection orders.

## Performance

### Typical Execution Times

- **1-2 positions**: 3-5 seconds
- **3-5 positions**: 5-10 seconds
- **5+ positions**: 10-15 seconds

### Resource Usage

- **Memory**: ~50-100MB
- **CPU**: Minimal (brief spikes during execution)
- **Network**: 1-5 API calls per position

## Best Practices

### 1. **Frequency Selection**

- **High-frequency trading**: Every 1-2 minutes
- **Swing trading**: Every 5-10 minutes
- **Position trading**: Every 15-30 minutes

### 2. **Error Handling**

The script includes automatic timeout (4 minutes) to prevent hanging processes in cronjobs.

### 3. **Log Management**

Position update logs are automatically rotated to prevent disk space issues.

### 4. **Notifications**

Enable Telegram notifications for real-time position updates and trade completions.

## Integration with Main Bot

Position-only mode works seamlessly with the main trading bot:

1. **Main bot** (hourly/daily): Scans for new opportunities
2. **Position monitor** (every 5 minutes): Manages existing positions
3. **Both use the same**: Configuration, position files, and notification system

This separation allows for:

- More responsive position management
- Reduced resource usage for signal scanning
- Better error isolation
- Flexible scheduling strategies
