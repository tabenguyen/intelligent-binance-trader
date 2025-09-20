# Simulation Bot Usage Guide

## Overview

The simulation bot (`simulate_bot.py`) is a complete trading simulation system that operates with virtual balance and Telegram notifications to a signal group instead of real trading.

## Key Differences from Real Trading Bot

| Feature           | Real Trading Bot     | Simulation Bot                          |
| ----------------- | -------------------- | --------------------------------------- |
| **Account**       | Real Binance account | Virtual balance simulation              |
| **Trading**       | Executes real trades | Simulates trades with virtual positions |
| **Notifications** | Telegram chat        | Telegram signal group                   |
| **Balance**       | Real USDT balance    | Configurable virtual balance            |
| **Risk**          | Real money at risk   | No real money involved                  |

## Setup Instructions

### 1. Environment Configuration

Create or update your `.env` file with these variables:

```bash
# Simulation Mode
SIMULATION_MODE=true
SIMULATION_BALANCE=10000.0

# Binance API (for market data only - no real trading)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
USE_TESTNET=true

# Trading Configuration
SYMBOLS=BTCUSDT,ETHUSDT,ADAUSDT,BNBUSDT
TRADE_AMOUNT=100.0
SCAN_INTERVAL=60

# Telegram Notifications (for signal group)
ENABLE_TELEGRAM_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_SIGNAL_GROUP_ID=your_signal_group_id
SIMULATION_USE_SIGNAL_GROUP=true
```

### 2. Telegram Bot Setup

To enable Telegram notifications for simulation:

1. Create a Telegram bot:

   - Message @BotFather on Telegram
   - Use `/newbot` command and follow instructions
   - Get your bot token

2. Set up signal group:

   - Create a Telegram group for trading signals
   - Add your bot to the group
   - Get the group ID (use @userinfobot or check bot logs)

3. Configure environment variables:
   - Set `TELEGRAM_BOT_TOKEN` with your bot token
   - Set `TELEGRAM_SIGNAL_GROUP_ID` with your group ID
   - Set `ENABLE_TELEGRAM_NOTIFICATIONS=true`

If you don't want notifications, set `ENABLE_TELEGRAM_NOTIFICATIONS=false`.

### 3. Running the Simulation Bot

#### Basic Usage

```bash
# Run continuous simulation (like the real bot)
python simulate_bot.py

# Run single simulation cycle (for testing)
python simulate_bot.py --once

# Use custom balance
python simulate_bot.py --balance 5000
```

#### Example Commands

```bash
# Start simulation with default settings
./simulate_bot.py

# Test with one cycle and custom balance
./simulate_bot.py --once --balance 1000

# Run with specific balance override
./simulate_bot.py --balance 50000
```

## How It Works

### 1. Market Analysis

- Connects to Binance API for real market data
- Analyzes price movements using same technical indicators as real bot
- Generates trading signals based on EMA crossover strategy

### 2. Virtual Trading

- Maintains virtual balance (starts with `SIMULATION_BALANCE`)
- Simulates position entries and exits
- Tracks profit/loss without real money

### 3. Telegram Notifications

- **Signal Messages**: When entering a position, sends a message to the signal group with:
  - Trading signal (BUY/SELL)
  - Symbol and price
  - Stop loss and take profit levels
  - Trade amount
- **Completion Messages**: When closing a position, sends another message with:
  - Final result (profit/loss)
  - Exit price and reason
  - Performance summary

### 4. Performance Tracking

- Tracks virtual balance changes
- Calculates win rate and total P&L
- Shows active positions and completed trades

## Sample Output

```
🎯 Starting Simulated Trading Bot...
✅ Configuration loaded:
   Simulation Balance: $10,000.00
   Trading Symbols: 4 symbols
   Trade Amount: $100.00
   Telegram Notifications: ✅ Enabled
   Testnet Mode: ✅ Enabled

🚀 Starting continuous simulation...
Press Ctrl+C to stop the simulation

📊 SIMULATION CYCLE COMPLETED
============================================================
Balance: $10,150.00 (Change: +$150.00)
Active Positions: 2
Completed Trades: 5
Win Rate: 80.0%
```

## Twitter Notification Examples

## Telegram Notification Examples

### Signal Message

```
🚀 TRADING SIGNAL: BUY BTCUSDT

💰 Entry: $43,250.00 ($100.00)
🛡️ Stop Loss: $41,162.50 (-4.8%)
🎯 Take Profit: $45,337.50 (+4.8%)

#TradingBot #Bitcoin #BUY
```

### Completion Message

```
✅ TRADE COMPLETED

📈 BTCUSDT BUY: +$7.50 (+7.5%)
💰 Exit: $43,575.00
📊 Balance: $10,107.50

Reason: Take profit hit
#Profit #TradingBot
```

## Testing and Validation

### Run Tests

```bash
# Run component validation
python quick_test.py

# Run comprehensive test suite
python test_simulation_bot.py
```

### Verify Setup

```bash
# Test single cycle without notifications
ENABLE_TELEGRAM_NOTIFICATIONS=false python simulate_bot.py --once

# Test with Telegram notifications
python simulate_bot.py --once
```

## Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   # Make sure you're in the project root directory
   cd /path/to/trading-bot-ai
   python simulate_bot.py
   ```

2. **Missing Dependencies**

   ```bash
   # Install required packages
   pip install -r requirements.txt
   ```

3. **Configuration Issues**

   - Check `.env` file exists and has correct format
   - Verify Binance API credentials are valid (for market data)
   - For Telegram: ensure bot token and group ID are set correctly

4. **Telegram Bot Errors**
   - Verify bot token is correct
   - Check that bot is added to the signal group
   - Ensure bot has permission to send messages in the group

### Debug Mode

Enable detailed logging by setting:

```bash
export LOG_LEVEL=DEBUG
python simulate_bot.py --once
```

## Safety Features

- ✅ **No Real Trading**: Never executes actual trades
- ✅ **Virtual Balance**: All transactions are simulated
- ✅ **Testnet Only**: Uses Binance testnet for API calls
- ✅ **Read-Only Market Data**: Only fetches prices, never places orders
- ✅ **Configurable Limits**: Set custom balance and trade amounts

## Integration with Real Bot

The simulation bot is designed to test strategies before using the real trading bot:

1. **Test Strategy**: Use simulation to validate trading logic
2. **Tune Parameters**: Adjust settings based on simulation results
3. **Deploy Real Bot**: Switch to real bot with confidence

To switch from simulation to real trading:

1. Set `SIMULATION_MODE=false` in `.env`
2. Configure real Binance account (not testnet)
3. Set up Telegram notifications for signal group
4. Run `python main.py` instead of `python simulate_bot.py`

## Support

If you encounter issues:

1. Check this guide first
2. Run the test scripts to validate setup
3. Check logs for detailed error messages
4. Verify all environment variables are correctly set
