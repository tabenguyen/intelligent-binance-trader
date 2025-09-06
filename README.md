# 🤖 Advanced Binance Trading Bot

An intelligent, fully-automated trading bot for Binance that combines sophisticated technical analysis, risk management, and position tracking with enterprise-grade reliability and safety features.

## ⚠️ **IMPORTANT DISCLAIMER - AI-GENERATED SYSTEM**

> **🤖 This repository is 90% completed by AI** under human guidance and oversight. The human author controls how the AI implements strategies and provides recommendations, but the majority of code, logic, and features were developed by artificial intelligence.
>
> **📊 Strategy Control**: While AI developed the implementation, the trading strategy, risk parameters, and safety features are carefully designed and validated by the human author.
>
> **🔬 Use with Caution**: This is an experimental AI-driven trading system. Always test thoroughly with small amounts and testnet before live trading. Past performance does not guarantee future results.
>
> **💡 Educational Purpose**: This project serves as a demonstration of AI-assisted trading system development and should be considered educational/research material.

## 📈 **Trading Strategy & Performance**

### **Strategy Overview**

Our EMA Cross Strategy with Advanced Quality Filters focuses on high-probability setups by requiring multiple confluence factors before entering trades. For detailed technical workflow, see our [Sequence Diagram Documentation](docs/sequence_diagram.md).

#### **Entry Conditions** (All must align)

1. **EMA Alignment**: 12 EMA > 26 EMA > 50 EMA (strong bullish trend)
2. **RSI Momentum**: RSI between 45-75 (avoiding overbought/oversold extremes)
3. **Price Position**: Current price above EMA support with 3% tolerance
4. **Daily Trend Filter**: Price above Daily 50-EMA (prevents counter-trend trades)
5. **Volume Confirmation**: Volume 20% above 20-period average
6. **ATR Volatility**: Optimal volatility range (not too choppy, not too chaotic)

#### **Exit Strategy** (OCO Protection)

- **Take Profit**: 2.0x risk distance above entry (configurable via RISK_REWARD_RATIO)
- **Stop Loss**: Below recent swing low with ATR-based buffer
- **Advanced Exits**: Partial profits at 1.5R, trailing stops, breakeven protection

### **Simulated Performance Evidence**

> **Note**: These are simulated results for demonstration purposes, not live trading results.

#### **Trade Example 1: SOLUSDT - WIN** ✅

```
Entry Date: 2025-09-01 14:30 UTC
Entry Price: $142.50
Stop Loss: $135.75 (-4.7%)
Take Profit: $156.00 (+9.5%)
Exit: Take Profit Hit
Result: +9.5% (+$13.50 per SOL)
Duration: 18 hours
```

#### **Trade Example 2: ADAUSDT - WIN** ✅

```
Entry Date: 2025-09-02 09:15 UTC
Entry Price: $0.4820
Stop Loss: $0.4580 (-5.0%)
Take Profit: $0.5300 (+9.9%)
Exit: Take Profit Hit
Result: +9.9% (+$0.048 per ADA)
Duration: 28 hours
```

#### **Trade Example 3: LINKUSDT - WIN** ✅

```
Entry Date: 2025-09-03 16:45 UTC
Entry Price: $11.85
Stop Loss: $11.25 (-5.1%)
Take Profit: $13.05 (+10.1%)
Exit: Take Profit Hit
Result: +10.1% (+$1.20 per LINK)
Duration: 31 hours
```

#### **Trade Example 4: DOTUSDT - LOSS** ❌

```
Entry Date: 2025-09-04 11:20 UTC
Entry Price: $6.75
Stop Loss: $6.45 (-4.4%)
Take Profit: $7.35 (+8.9%)
Exit: Stop Loss Hit
Result: -4.4% (-$0.30 per DOT)
Duration: 12 hours
```

#### **Performance Summary**

- **Win Rate**: 75% (3 wins, 1 loss)
- **Average Winner**: +9.8%
- **Average Loser**: -4.4%
- **Risk-Reward Ratio**: 2.2:1
- **Expected Value**: +6.9% per trade

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

### 2. **Trading Mode Configuration**

The bot automatically separates files and logs based on trading mode for safety:

#### **🧪 Testnet Mode (Default & Recommended)**

```bash
export USE_TESTNET=true    # Safe testing environment
```

- Uses: `config/watchlist_testnet.txt`, `data/active_trades_testnet.json`, `logs/output_testnet.log`
- Pre-configured with active symbols for testing

#### **💰 Live Mode** (⚠️ **Real Money - Use with Caution!** ⚠️)

```bash
export USE_TESTNET=false   # Live trading with real funds
```

- Uses: `config/watchlist_live.txt`, `data/active_trades_live.json`, `logs/output_live.log`
- Pre-configured with conservative, major cryptocurrencies

#### **Check Current Mode**

```bash
uv run python scripts/mode_manager.py status
```

📖 **See [Mode Separation Documentation](docs/mode_separation.md)** for complete details.

### 3. **API Configuration**

Edit `.env` file with your Binance API credentials. See the complete configuration table below for all available options.

### 4. **Automatic Watchlist Generation**

The bot automatically generates and maintains its watchlist by:

- **Market Scanning**: Identifies top 24-hour gainers from Binance
- **Performance Ranking**: Analyzes relative strength over 14-day periods
- **Dynamic Updates**: Refreshes watchlist every 4 hours to capture new opportunities
- **Quality Filtering**: Only considers symbols meeting minimum volume and market cap requirements

> **No manual watchlist management required!** The system intelligently finds the best trading opportunities.

### 5. **Start Trading with Process Protection**

#### 🖥️ **Using start.sh Script (Recommended)**

The `start.sh` script provides safe process management with duplicate execution prevention:

```bash
./start.sh start     # Start the bot (prevents duplicates)
./start.sh status    # Check if running and show stats
./start.sh logs      # View real-time logs
./start.sh restart   # Safe restart (stop + start)
./start.sh stop      # Graceful shutdown
```

#### **⚠️ Important Process Safety Features:**

1. **Duplicate Prevention**: Script checks for existing PID before starting
2. **Graceful Shutdown**: Attempts clean shutdown before force-kill
3. **Log Backup**: Automatically backs up previous logs with timestamps
4. **Status Monitoring**: Shows PID, log size, and recent entries
5. **Error Recovery**: Cleans up stale PID files automatically

#### **Example Safe Usage:**

```bash
# ✅ SAFE - Always use the script
./start.sh start
./start.sh status    # Verify it's running
./start.sh logs      # Monitor activity

# ❌ AVOID - Direct execution can create duplicates
python main.py &     # Don't do this!
nohup python main.py # Don't do this!
```

#### **If You Encounter "Already Running" Warnings:**

```bash
./start.sh status    # Check actual status
./start.sh stop      # Force clean shutdown
./start.sh start     # Fresh start
```

## � **Complete Configuration Reference**

All configuration is done through environment variables in the `.env` file. Copy from `config/.env.example`:

| Category                        | Variable                           | Description                               | Default    | Type    |
| ------------------------------- | ---------------------------------- | ----------------------------------------- | ---------- | ------- |
| **🔐 API Settings**             |                                    |                                           |            |         |
|                                 | `BINANCE_API_KEY`                  | Your Binance API key                      | _Required_ | String  |
|                                 | `BINANCE_API_SECRET`               | Your Binance API secret                   | _Required_ | String  |
|                                 | `USE_TESTNET`                      | Use testnet for testing                   | `True`     | Boolean |
| **💰 Basic Trading**            |                                    |                                           |            |         |
|                                 | `TRADE_AMOUNT_USDT`                | Fixed trade amount (legacy)               | `25.0`     | Float   |
|                                 | `RISK_REWARD_RATIO`                | Risk-to-reward ratio                      | `2.0`      | Float   |
|                                 | `MIN_USDT_BALANCE`                 | Minimum USDT balance required             | `150.0`    | Float   |
|                                 | `MIN_NOTIONAL_USDT`                | Minimum order value (Binance requirement) | `15.0`     | Float   |
| **📊 Advanced Risk Management** |                                    |                                           |            |         |
|                                 | `ENABLE_DYNAMIC_POSITION_SIZING`   | Use percentage-based position sizing      | `true`     | Boolean |
|                                 | `RISK_PERCENTAGE_PER_TRADE`        | Risk % of total capital per trade         | `1.5`      | Float   |
|                                 | `MINIMUM_RR_RATIO`                 | Minimum risk-reward ratio filter          | `1.5`      | Float   |
|                                 | `MAX_POSITION_SIZE_USDT`           | Maximum position size limit               | `100.0`    | Float   |
|                                 | `MIN_POSITION_SIZE_USDT`           | Minimum position size limit               | `10.0`     | Float   |
| **⚙️ Order Management**         |                                    |                                           |            |         |
|                                 | `MAX_LIMIT_ORDER_RETRIES`          | Max retries for limit orders              | `15`       | Integer |
|                                 | `LIMIT_ORDER_RETRY_DELAY`          | Delay between retries (seconds)           | `10`       | Integer |
| **🎯 Quality Filters**          |                                    |                                           |            |         |
|                                 | `ENABLE_DAILY_TREND_FILTER`        | Only trade if above daily 50-EMA          | `True`     | Boolean |
|                                 | `ENABLE_ATR_FILTER`                | Filter by optimal volatility range        | `True`     | Boolean |
|                                 | `ENABLE_VOLUME_FILTER`             | Require volume confirmation               | `True`     | Boolean |
|                                 | `MIN_VOLUME_RATIO`                 | Minimum volume vs average                 | `1.2`      | Float   |
| **🚀 Advanced Exits**           |                                    |                                           |            |         |
|                                 | `ENABLE_ADVANCED_EXITS`            | Enable sophisticated exit management      | `true`     | Boolean |
|                                 | `ENABLE_TRAILING_STOP`             | Use ATR-based trailing stops              | `true`     | Boolean |
|                                 | `TRAILING_STOP_ATR_MULTIPLIER`     | Trailing stop distance multiplier         | `2.0`      | Float   |
|                                 | `ENABLE_PARTIAL_PROFITS`           | Enable partial profit taking              | `true`     | Boolean |
|                                 | `PARTIAL_TP1_RATIO`                | First partial exit R:R ratio              | `1.5`      | Float   |
|                                 | `PARTIAL_TP1_PERCENTAGE`           | First exit position percentage            | `0.5`      | Float   |
|                                 | `PARTIAL_TP2_RATIO`                | Second partial exit R:R ratio             | `3.0`      | Float   |
| **🔍 Intelligent Scanner**      |                                    |                                           |            |         |
|                                 | `ENABLE_RELATIVE_STRENGTH_RANKING` | Prioritize strongest performers           | `true`     | Boolean |
|                                 | `RELATIVE_STRENGTH_LOOKBACK_DAYS`  | Performance analysis period               | `14`       | Integer |
|                                 | `TOP_PERFORMERS_PERCENTAGE`        | Only trade top % of performers            | `25`       | Integer |
|                                 | `MIN_COINS_FOR_RANKING`            | Minimum coins to analyze                  | `5`        | Integer |
|                                 | `RANKING_UPDATE_FREQUENCY_HOURS`   | How often to update rankings              | `4`        | Integer |

### **Configuration Examples**

#### **Conservative Settings** (Lower risk, higher win rate)

```env
RISK_PERCENTAGE_PER_TRADE=1.0
MINIMUM_RR_RATIO=2.0
MIN_VOLUME_RATIO=1.5
TOP_PERFORMERS_PERCENTAGE=15
```

#### **Aggressive Settings** (Higher risk, more opportunities)

```env
RISK_PERCENTAGE_PER_TRADE=2.5
MINIMUM_RR_RATIO=1.2
MIN_VOLUME_RATIO=1.1
TOP_PERFORMERS_PERCENTAGE=40
```

## �️ **Management Scripts & Tools**

The bot includes comprehensive management scripts for monitoring, maintenance, and troubleshooting:

### **📊 Position & Balance Management**

#### **`check_balances.py`**

```bash
python scripts/check_balances.py
```

- **Purpose**: Display all account balances with free/locked amounts
- **Features**: Highlights assets from active positions, shows total portfolio value
- **Use Case**: Verify account state before trading, check available funds

#### **`check_open_orders.py`**

```bash
python scripts/check_open_orders.py
```

- **Purpose**: List all active orders across all symbols
- **Features**: Shows order types (OCO, limit, stop-loss), prices, quantities
- **Use Case**: Monitor OCO orders, verify exit protection, identify stuck orders

#### **`comprehensive_oco_cleanup.py`**

```bash
python scripts/comprehensive_oco_cleanup.py
```

- **Purpose**: Clean stale positions and create missing OCO orders
- **Features**: Balance-aware OCO placement, position quantity correction
- **Use Case**: Recovery after bot restarts, fix missing exit protection

#### **`balance_aware_oco.py`**

```bash
python scripts/balance_aware_oco.py
```

- **Purpose**: Create OCO orders using actual account balances
- **Features**: Automatic quantity adjustment, precision handling
- **Use Case**: Fix "insufficient balance" errors, ensure accurate order sizes

### **🔍 Market Analysis & Validation**

#### **`test_market_status.py`**

```bash
python scripts/test_market_status.py
```

- **Purpose**: Verify market status and trading availability
- **Features**: Checks market hours, symbol status, trading permissions
- **Use Case**: Troubleshoot trading failures, verify market accessibility

#### **`check_notional.py`**

```bash
python scripts/check_notional.py
```

- **Purpose**: Validate minimum notional requirements
- **Features**: Shows symbol filters, minimum order values, precision rules
- **Use Case**: Debug order rejection errors, verify compliance with Binance rules

#### **`test_order_status.py`**

```bash
python scripts/test_order_status.py
```

- **Purpose**: Check specific order status and details
- **Features**: Order lifecycle tracking, execution details, error diagnosis
- **Use Case**: Investigate failed orders, track order execution progress

### **🔧 Advanced Recovery Tools**

#### **`advanced_oco_retry.py`**

```bash
python scripts/advanced_oco_retry.py
```

- **Purpose**: Sophisticated OCO order retry with error analysis
- **Features**: Smart error handling, progressive retry logic, detailed diagnostics
- **Use Case**: Recover from complex OCO failures, detailed error investigation

#### **`retry_oco_orders.py`**

```bash
python scripts/retry_oco_orders.py
```

- **Purpose**: Simple OCO order retry mechanism
- **Features**: Basic retry logic for common failures
- **Use Case**: Quick recovery from temporary OCO failures

#### **`check_oco_status.py`**

```bash
python scripts/check_oco_status.py
```

- **Purpose**: Verify OCO order status across all positions
- **Features**: Real-time OCO validation, missing protection alerts
- **Use Case**: Audit position protection, identify unprotected positions

### **🧹 Maintenance & Migration**

#### **`cleanup_positions.py`**

```bash
python scripts/cleanup_positions.py
```

- **Purpose**: Remove stale or invalid position records
- **Features**: Safe position validation, automatic cleanup
- **Use Case**: Clean up after market crashes, remove outdated data

#### **`migrate_active_trades.py`**

```bash
python scripts/migrate_active_trades.py
```

- **Purpose**: Migrate position data between format versions
- **Features**: Data format conversion, backup creation
- **Use Case**: Upgrade position storage format, data migration

### **🎯 Trading Simulation & Testing**

#### **`simulate_trading.py`**

```bash
python scripts/simulate_trading.py
```

- **Purpose**: Backtest trading strategy on historical data
- **Features**: Paper trading simulation, performance metrics
- **Use Case**: Strategy validation, parameter optimization

#### **`simulate_trading_clean.py`**

```bash
python scripts/simulate_trading_clean.py
```

- **Purpose**: Clean simulation environment for testing
- **Features**: Fresh simulation state, controlled testing
- **Use Case**: Isolated strategy testing, clean performance analysis

#### **`smart_exit_orders.py`**

```bash
python scripts/smart_exit_orders.py
```

- **Purpose**: Advanced exit strategy implementation
- **Features**: Partial profits, trailing stops, breakeven management
- **Use Case**: Sophisticated position management, maximize profit potential

## 🧪 **Test Suite**

Comprehensive test coverage ensures system reliability:

### **Core Functionality Tests**

#### **`test_trading_bot.py`**

- **Coverage**: Main trading logic, signal generation, order execution
- **Features**: Mock API testing, edge case validation, error handling
- **Run**: `pytest tests/test_trading_bot.py -v`

#### **`test_balance_validation.py`**

- **Coverage**: Balance checking, quantity validation, precision handling
- **Features**: Float precision tests, rounding validation, edge cases
- **Run**: `pytest tests/test_balance_validation.py -v`

#### **`test_oco_validation.py`**

- **Coverage**: OCO order creation, validation, error handling
- **Features**: API response mocking, error scenario testing
- **Run**: `pytest tests/test_oco_validation.py -v`

### **Advanced Feature Tests**

#### **`test_risk_management.py`**

- **Coverage**: Position sizing, risk calculations, safety limits
- **Features**: Dynamic sizing tests, risk percentage validation
- **Run**: `pytest tests/test_risk_management.py -v`

#### **`test_advanced_exits.py`**

- **Coverage**: Partial profits, trailing stops, exit strategies
- **Features**: Complex exit scenario testing, profit optimization
- **Run**: `pytest tests/test_advanced_exits.py -v`

#### **`test_intelligent_scanner.py`**

- **Coverage**: Watchlist generation, performance ranking, filtering
- **Features**: Market scanning logic, relative strength calculations
- **Run**: `pytest tests/test_intelligent_scanner.py -v`

### **Configuration & Integration Tests**

#### **`test_min_notional_config.py`**

- **Coverage**: Configuration loading, environment variable validation
- **Features**: Config edge cases, default value testing
- **Run**: `pytest tests/test_min_notional_config.py -v`

#### **`test_simple.py`**

- **Coverage**: Basic system functionality, smoke testing
- **Features**: Quick validation, integration testing
- **Run**: `pytest tests/test_simple.py -v`

### **Running All Tests**

```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=html

# Run specific test category
pytest tests/test_*risk* -v  # Risk management tests
pytest tests/test_*oco* -v   # OCO related tests
pytest tests/test_*balance* -v # Balance validation tests
```

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

## **Security Best Practices**

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
