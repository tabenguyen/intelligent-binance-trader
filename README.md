# Coin Gemini Trading Bot

An automated trading bot for Binance that uses technical analysis to identify buy signals and execute trades.

## Setup

### 1. Environment Variables

This project uses python-dotenv to manage environment variables securely.

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your actual Binance API credentials:

   ```
   BINANCE_API_KEY=your_actual_api_key_here
   BINANCE_API_SECRET=your_actual_secret_key_here
   ```

3. Optional: Configure trading parameters in `.env`:
   ```
   USE_TESTNET=True
   TRADE_AMOUNT_USDT=15.0
   RISK_REWARD_RATIO=1.5
   MIN_USDT_BALANCE=100.0
   ```

### 2. API Keys

- **For testing**: Get testnet keys from https://testnet.binance.vision/
- **For live trading**: Get live keys from https://www.binance.com/
- **Security**: Only enable "Enable Spot & Margin Trading" permissions, DO NOT enable withdrawals

### 3. Installation

Install dependencies:

```bash
uv sync
```

### 4. Watchlist

Create a `watchlist.txt` file with the trading pairs you want to monitor (one per line):

```
BTCUSDT
ETHUSDT
ADAUSDT
```

### 5. Running

#### Option A: Direct Python Execution

Start the trading bot:

```bash
uv run python trading_bot.py
```

#### Option B: Docker (Recommended for Production)

1. Copy Docker environment file:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. Start with Docker Compose:

   ```bash
   # Using the management script (recommended)
   ./docker.sh start

   # Or manually
   docker-compose up -d
   ```

3. View logs:

   ```bash
   ./docker.sh logs
   # Or manually
   docker-compose logs -f
   ```

4. Stop the bot:
   ```bash
   ./docker.sh stop
   # Or manually
   docker-compose down
   ```

## Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already included in `.gitignore`
- Always test with testnet first before using live API keys
- Restrict your API keys to your IP address on Binance for additional security

## Features

### 🔄 **Persistent Active Trade Tracking**

- Active OCO orders are automatically saved to `active_trades.txt`
- Bot can be safely restarted without losing track of ongoing trades
- Prevents duplicate trades on the same symbol until OCO order completes
- Automatic cleanup when trades are completed (profit or stop loss hit)

### 📊 **Technical Analysis Strategy**

- Uses EMA (9, 21, 50) for trend confirmation
- RSI for momentum analysis
- Swing high/low detection for stop loss placement
- Risk-reward ratio calculation for take profit

### 🛡️ **Risk Management**

- **Early Balance Validation** - Checks USDT balance first before any analysis to save processing time
- One active trade per symbol maximum
- Automatic OCO orders (take profit + stop loss)
- **Balance verification after buy orders** - Ensures asset balance is updated before placing OCO
- Minimum notional value validation
- Automatic quantity adjustment for exchange requirements
- Configurable trade amounts and risk parameters

### 🔍 **Advanced Safety Features**

- **Efficient Processing**: Balance validation moved to first condition to avoid unnecessary analysis when funds are insufficient
- **Balance Verification**: After each market buy order, the bot waits and verifies that the purchased asset balance has been properly updated before placing the OCO sell order
- **Retry Mechanism**: Up to 10 attempts with 3-second delays to ensure balance synchronization
- **Graceful Failure Handling**: If balance verification fails, the trade is logged and manual intervention is suggested
- **Actual Balance Usage**: OCO orders use the verified actual balance rather than theoretical quantities
- **Safe Quantity Formatting**: Uses round-down formatting for sell quantities to ensure we never exceed available balance
- **Executed Quantity Tracking**: Uses actual executed quantity from buy orders instead of requested quantity

## Configuration

All configuration can be done through environment variables in the `.env` file:

- `BINANCE_API_KEY`: Your Binance API key
- `BINANCE_API_SECRET`: Your Binance API secret
- `USE_TESTNET`: Set to `True` for testnet, `False` for live trading (default: True)
- `TRADE_AMOUNT_USDT`: Amount in USDT to spend per trade (default: 15.0)
- `RISK_REWARD_RATIO`: Risk-to-reward ratio for take profit (default: 1.5)
- `MIN_USDT_BALANCE`: Minimum USDT balance required to trade (default: 100.0)

## 🐳 Docker Deployment

### Quick Start with Docker

1. **Setup Environment**:

   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

2. **Start the Bot**:

   ```bash
   ./docker.sh start
   ```

3. **Monitor Logs**:
   ```bash
   ./docker.sh logs
   ```

### Docker Management Commands

The `docker.sh` script provides convenient commands:

```bash
./docker.sh build    # Build Docker image
./docker.sh start    # Start the trading bot
./docker.sh stop     # Stop the trading bot
./docker.sh restart  # Restart the trading bot
./docker.sh logs     # View real-time logs
./docker.sh status   # Check bot status
./docker.sh update   # Update and restart
./docker.sh clean    # Remove all Docker resources
```

### Docker Features

- **🔄 Automatic Restart**: Bot restarts automatically if it crashes
- **📊 Resource Limits**: Memory and CPU limits for stable operation
- **💾 Persistent Data**: Active trades and logs are preserved
- **🏥 Health Checks**: Container health monitoring
- **📝 Log Management**: Automatic log rotation and management
- **🔒 Security**: Runs as non-root user inside container

### Manual Docker Commands

If you prefer manual control:

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f trading-bot

# Stop
docker-compose down

# Restart specific service
docker-compose restart trading-bot
```
