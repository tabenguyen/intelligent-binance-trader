# 🤖 Advanced Binance Trading Bot

An intelligent, fully-automated trading bot for Binance that combines sophisticated technical analysis, risk management, and position tracking with enterprise-grade reliability and safety features.

## 🌟 Key Features

### 🧠 **Intelligent Trading Engine**

- **Multi-Strategy Analysis**: EMA crossovers, RSI momentum, support/resistance levels
- **Smart Signal Generation**: Only trades when multiple confluence conditions align
- **Market Status Filtering**: Automatically filters out closed/suspended trading pairs
- **Adaptive Risk Management**: Dynamic stop-loss and take-profit calculations

### 🛡️ **Enterprise-Grade Safety**

- **Balance-Aware Orders**: Uses actual account balances, not stale position data
- **OCO Order Protection**: Automatic stop-loss and take-profit orders for every position
- **Position Persistence**: Survives bot restarts with complete position tracking
- **Duplicate Order Prevention**: Intelligent checks to prevent multiple orders on same symbol
- **Order Status Verification**: Comprehensive order tracking and status validation

### 🔧 **Advanced Position Management**

- **Real-Time Balance Sync**: Verifies asset balances before placing orders
- **OCO Order Recovery**: Automatic retry for failed OCO order placements
- **Position Cleanup**: Removes stale positions for assets no longer held
- **Smart Quantity Adjustment**: Respects all Binance filters (LOT_SIZE, PRICE_FILTER, NOTIONAL)

### 📊 **Comprehensive Monitoring**

- **Live Position Tracking**: Real-time P&L and position status
- **Market Data Integration**: Current prices, 24h volume, market trends
- **Order Book Analysis**: Deep market analysis for optimal entry points
- **Performance Analytics**: Trade success rates, profit/loss tracking

## 🚀 Quick Start

### 1. **Environment Setup**

```bash
# Clone and setup
git clone <repository-url>
cd trading-bot-ai

# Install dependencies
uv sync

# Setup environment
cp config/.env.example .env
# Edit .env with your Binance API credentials
```

### 2. **API Configuration**

Edit `.env` file with your Binance API credentials:

```env
# Binance API Configuration
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_secret_key_here
USE_TESTNET=True  # Set to False for live trading

# Trading Parameters
TRADE_AMOUNT_USDT=15.0
RISK_REWARD_RATIO=1.5
MIN_USDT_BALANCE=100.0

# Safety Settings
MAX_POSITIONS=5
ENABLE_OCO_ORDERS=True
POSITION_TRACKING=True
```

### 3. **Configure Watchlist**

Create your trading watchlist in `config/watchlist.txt`:

```
BTCUSDT
ETHUSDT
ADAUSDT
SOLUSDT
DOTUSDT
```

### 4. **Start Trading**

#### 🖥️ **Direct Execution**

```bash
./start.sh start     # Start the bot
./start.sh status    # Check status
./start.sh logs      # View logs
./start.sh stop      # Stop the bot
```

#### 🐳 **Docker Deployment**

```bash
./docker.sh start    # Start with Docker
./docker.sh logs     # Monitor logs
./docker.sh stop     # Stop container
```

## 🛠️ **Management Tools**

### **Position Management**

```bash
# Check current positions
python scripts/check_balances.py

# Verify OCO orders
python scripts/check_open_orders.py

# Clean up stale positions
python scripts/comprehensive_oco_cleanup.py

# Retry failed OCO orders
python scripts/balance_aware_oco.py
```

### **Market Analysis**

```bash
# Test market status
python scripts/test_market_status.py

# Analyze trading opportunities
python scripts/check_notional.py

# Monitor order status
python scripts/test_order_status.py
```

### **System Control**

```bash
# Bot lifecycle management
./start.sh start|stop|restart|status|logs

# Docker management
./docker.sh build|start|stop|restart|logs|clean
```

## 📈 **Trading Strategy**

### **Entry Conditions** (All must be met)

1. **EMA Alignment**: 9 EMA > 21 EMA > 50 EMA (bullish trend)
2. **RSI Momentum**: RSI between 30-70 (avoiding overbought/oversold)
3. **Volume Confirmation**: Above-average trading volume
4. **Market Status**: Symbol actively trading (not suspended)
5. **Balance Validation**: Sufficient USDT available
6. **Position Limit**: No existing position for the symbol

### **Exit Strategy** (OCO Orders)

- **Take Profit**: 1.5x risk distance above entry (configurable)
- **Stop Loss**: Based on recent swing low with buffer
- **Order Types**: OCO (One-Cancels-Other) for automatic execution

### **Risk Management**

- Maximum 1 position per symbol
- Configurable position sizing
- Automatic balance verification
- Emergency stop mechanisms

## 🏗️ **Architecture**

### **Core Services**

```
src/
├── core/              # Interface definitions and base classes
├── models/            # Data models and configurations
├── services/          # Business logic services
│   ├── market_data_service.py      # Market data fetching
│   ├── trade_execution_service.py  # Order execution
│   ├── position_management_service.py # Position tracking
│   ├── risk_management_service.py  # Risk controls
│   └── technical_analysis_service.py # TA indicators
├── strategies/        # Trading strategies
└── utils/            # Utilities and configuration
```

### **Key Components**

#### **Trading Bot** (`src/trading_bot.py`)

- Main orchestration engine
- Market scanning and signal generation
- Order execution and position tracking

#### **Market Watcher** (`src/market_watcher.py`)

- Real-time market data collection
- Symbol filtering and validation
- Market status monitoring

#### **Position Management** (`src/services/position_management_service.py`)

- Active position tracking
- OCO order management
- Position persistence and recovery

#### **Trade Execution** (`src/services/trade_execution_service.py`)

- Binance API integration
- Order placement and monitoring
- Balance verification and validation

## 🔧 **Configuration**

### **Environment Variables**

| Variable             | Description                  | Default  |
| -------------------- | ---------------------------- | -------- |
| `BINANCE_API_KEY`    | Binance API key              | Required |
| `BINANCE_API_SECRET` | Binance API secret           | Required |
| `USE_TESTNET`        | Use testnet for testing      | `True`   |
| `TRADE_AMOUNT_USDT`  | Amount per trade             | `15.0`   |
| `RISK_REWARD_RATIO`  | Risk/reward ratio            | `1.5`    |
| `MIN_USDT_BALANCE`   | Minimum balance required     | `100.0`  |
| `MAX_POSITIONS`      | Maximum concurrent positions | `5`      |
| `ENABLE_OCO_ORDERS`  | Enable OCO protection        | `True`   |

### **Trading Parameters**

```python
# In your .env file
TRADE_AMOUNT_USDT=25.0        # Larger position sizes
RISK_REWARD_RATIO=2.0         # More aggressive profit targets
MIN_USDT_BALANCE=200.0        # Higher minimum balance
MAX_POSITIONS=3               # Fewer concurrent positions
```

## 🚨 **Safety Features**

### **Balance Protection**

- ✅ Real-time balance verification before orders
- ✅ Order quantity adjustment based on available funds
- ✅ Minimum notional value compliance
- ✅ Exchange filter adherence (LOT_SIZE, PRICE_FILTER)

### **Position Safety**

- ✅ Automatic OCO order placement
- ✅ Position persistence across restarts
- ✅ Duplicate position prevention
- ✅ Stale position cleanup

### **Order Safety**

- ✅ Order status verification and retry logic
- ✅ Market status validation before trading
- ✅ API error handling and recovery
- ✅ Rate limiting and request management

### **System Safety**

- ✅ Comprehensive logging and monitoring
- ✅ Graceful shutdown handling
- ✅ Automatic restart capabilities
- ✅ Health check monitoring

## 📊 **Monitoring & Analytics**

### **Real-Time Monitoring**

```bash
# Check active positions
tail -f logs/output.log | grep "Position"

# Monitor OCO orders
python scripts/check_open_orders.py

# Balance overview
python scripts/check_balances.py
```

### **Performance Tracking**

- Position P&L tracking
- Win/loss ratio calculation
- Average holding period analysis
- Risk-adjusted returns

## 🐳 **Docker Deployment**

### **Production Deployment**

```bash
# Build and deploy
./docker.sh build
./docker.sh start

# Monitor
./docker.sh logs
./docker.sh status

# Maintenance
./docker.sh restart
./docker.sh update
```

### **Docker Features**

- 🔄 **Auto-restart**: Automatic recovery from crashes
- 📊 **Resource limits**: Memory and CPU constraints
- 💾 **Data persistence**: Logs and positions preserved
- 🏥 **Health checks**: Container health monitoring
- 🔒 **Security**: Non-root execution

## 🔒 **Security Best Practices**

### **API Security**

- Use testnet for development and testing
- Restrict API keys to specific IP addresses
- Enable only necessary permissions (Spot Trading only)
- Never commit API keys to version control

### **Operational Security**

- Regular balance monitoring
- Position limit enforcement
- Emergency stop procedures
- Backup and recovery plans

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **"Insufficient Balance" Errors**

```bash
# Check actual balances
python scripts/check_balances.py

# Clean up stale positions
python scripts/comprehensive_oco_cleanup.py
```

#### **OCO Order Failures**

```bash
# Retry OCO orders with balance validation
python scripts/balance_aware_oco.py

# Check open orders
python scripts/check_open_orders.py
```

#### **Market Status Issues**

```bash
# Verify market status
python scripts/test_market_status.py

# Check symbol availability
python scripts/check_notional.py
```

### **Log Analysis**

```bash
# View recent errors
tail -100 logs/output.log | grep ERROR

# Monitor position changes
tail -f logs/output.log | grep "Position\|OCO\|Balance"

# Check order execution
tail -f logs/output.log | grep "Order\|Executed\|Placed"
```

## 📚 **Advanced Usage**

### **Custom Strategies**

Extend the bot with custom strategies by implementing the `BaseStrategy` interface:

```python
from src.strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def generate_signal(self, market_data):
        # Your custom logic here
        pass
```

### **Risk Management Customization**

Implement custom risk management rules:

```python
from src.services.risk_management_service import RiskManagementService

class CustomRiskManager(RiskManagementService):
    def validate_trade(self, signal, current_positions):
        # Your custom risk logic
        pass
```

### **Notification Integration**

Add custom notifications for important events:

```python
from src.services.notification_service import NotificationService

# Implement Telegram, Discord, or email notifications
```

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request

## ⚠️ **Disclaimer**

This trading bot is for educational and research purposes. Cryptocurrency trading involves substantial risk of loss. Past performance does not guarantee future results. Use at your own risk and never invest more than you can afford to lose.

## 📞 **Support**

- 📖 **Documentation**: Check this README and inline code documentation
- 🐛 **Issues**: Report bugs via GitHub issues
- 💬 **Discussions**: Join community discussions
- 📧 **Contact**: Reach out for enterprise support

---

**Built with ❤️ for the crypto trading community**

## Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already included in `.gitignore`
- Always test with testnet first before using live API keys
- Restrict your API keys to your IP address on Binance for additional security

## Features

### 🔄 **Persistent Active Trade Tracking**

- Active OCO orders are automatically saved to `active_trades.json`
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
