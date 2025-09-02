# Testing Guide for Trading Bot

This directory contains comprehensive test suites for the trading bot. We provide multiple testing approaches to suit different needs.

## Quick Testing (No Dependencies)

For immediate testing without installing additional libraries:

```bash
# Run basic tests
python test_simple.py
```

This will test core functionality using only Python standard library.

## Full Testing Suite (Recommended)

For comprehensive testing with mocking and coverage:

```bash
# Install test dependencies
uv sync --group test

# Run all tests with coverage
pytest test_trading_bot.py -v --cov=trading_bot --cov=strategies

# Run tests with HTML coverage report
pytest test_trading_bot.py --cov=trading_bot --cov=strategies --cov-report=html

# Run specific test class
pytest test_trading_bot.py::TestEMACrossStrategy -v

# Run tests matching pattern
pytest test_trading_bot.py -k "test_buy_signal" -v
```

## Test Structure

### 1. Core Bot Tests (`TestTradingBotCore`)

- ✅ Data fetching from Binance API
- ✅ Technical analysis calculations
- ✅ Error handling for API failures
- ✅ Data validation and edge cases

### 2. Strategy Tests (`TestEMACrossStrategy`)

- ✅ Buy signal generation logic
- ✅ Individual condition testing (RSI, EMA, MACD)
- ✅ Filter combinations (daily trend, volume, volatility)
- ✅ Edge cases and boundary conditions

### 3. Trade Execution Tests (`TestTradingExecution`)

- ✅ Order formatting and validation
- ✅ Minimum notional requirements
- ✅ Symbol filter handling
- ✅ OCO order placement simulation
- ✅ Balance checks

### 4. Active Trades Tests (`TestActiveTradesManagement`)

- ✅ Trade tracking persistence
- ✅ Status monitoring
- ✅ Cleanup of completed trades
- ✅ File I/O operations

### 5. Ranking Tests (`TestRelativeStrengthRankings`)

- ✅ Performance calculations
- ✅ Ranking algorithms
- ✅ Top performer identification
- ✅ Multi-symbol analysis

### 6. Configuration Tests (`TestConfigurationAndEnvironment`)

- ✅ Environment variable handling
- ✅ Default value fallbacks
- ✅ Configuration validation

## Mock Testing Approach

Our tests use extensive mocking to:

- **Avoid Real API Calls**: All Binance API interactions are mocked
- **Control Test Data**: Predictable responses for consistent testing
- **Test Error Scenarios**: Simulate API failures and edge cases
- **Fast Execution**: Tests run quickly without network dependencies

## Sample Test Data

Tests use realistic market data patterns:

```python
# Bullish scenario
{
    '12_EMA': 47200.0,    # Fast EMA above slow EMA
    '26_EMA': 46800.0,
    '55_EMA': 46500.0,    # Price above long-term trend
    'RSI_21': 62.5,       # Healthy momentum
    'Volume_Ratio': 1.25, # Above average volume
    'Volatility_State': 'NORMAL'
}

# Bearish scenario
{
    '12_EMA': 46000.0,    # Fast EMA below slow EMA
    '26_EMA': 46800.0,
    '55_EMA': 47500.0,    # Price below long-term trend
    'RSI_21': 35.0,       # Oversold
    'Volume_Ratio': 0.8,  # Low volume
    'Volatility_State': 'HIGH'
}
```

## Expected Test Results

### ✅ Pass Scenarios

- All strategy conditions met with bullish signals
- Proper order formatting and validation
- Successful trade tracking and persistence
- Correct ranking calculations

### ❌ Fail Scenarios

- Missing required indicators
- RSI outside healthy range (45-75)
- Price below long-term trend (55-EMA)
- Insufficient volume or high volatility
- Trade amount below minimum notional

## Integration Testing

To test with real (testnet) data:

```bash
# Set testnet environment
export USE_TESTNET=True
export BINANCE_API_KEY=your_testnet_key
export BINANCE_API_SECRET=your_testnet_secret

# Run integration tests (coming soon)
pytest test_integration.py -v
```

## Coverage Reports

After running tests with coverage:

```bash
# View terminal coverage
cat htmlcov/index.html

# Open HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Continuous Testing

For development, use watch mode:

```bash
# Install pytest-watch
pip install pytest-watch

# Watch for changes and re-run tests
ptw test_trading_bot.py
```

## Performance Testing

For strategy backtesting (future enhancement):

```bash
# Backtest with historical data
python backtest_strategy.py --symbol BTCUSDT --days 30
```

## Test Environment Variables

Tests respect these environment variables:

```bash
# Test configuration
export TEST_MODE=True
export LOG_LEVEL=DEBUG
export TRADE_AMOUNT_USDT=10.0

# Mock data sources
export USE_MOCK_DATA=True
export MOCK_DATA_PATH=./test_data/
```

## Debugging Failed Tests

1. **Enable Debug Logging**:

   ```bash
   pytest test_trading_bot.py -v -s --log-level=DEBUG
   ```

2. **Run Single Test**:

   ```bash
   pytest test_trading_bot.py::TestEMACrossStrategy::test_buy_signal_all_conditions_met -v -s
   ```

3. **Use PDB Debugger**:

   ```bash
   pytest test_trading_bot.py --pdb
   ```

4. **Check Mock Calls**:
   Tests include detailed mock verification to ensure API calls are made correctly.

## Adding New Tests

When adding new functionality:

1. **Create Test Class**: Follow existing patterns
2. **Mock External Dependencies**: Especially API calls
3. **Test Both Success and Failure**: Edge cases are important
4. **Use Realistic Data**: Match actual market conditions
5. **Document Expected Behavior**: Clear test names and docstrings

Example:

```python
def test_new_feature_success(self):
    """Test new feature under normal conditions"""
    # Setup
    mock_data = {...}

    # Execute
    result = function_under_test(mock_data)

    # Assert
    assert result.is_successful
    assert result.value > expected_threshold
```

## Best Practices

- ✅ **Test One Thing**: Each test should verify one specific behavior
- ✅ **Use Descriptive Names**: Test names should explain what they test
- ✅ **Mock External Dependencies**: Don't rely on external services
- ✅ **Test Edge Cases**: Boundary conditions and error scenarios
- ✅ **Keep Tests Fast**: Use mocks to avoid slow operations
- ✅ **Make Tests Deterministic**: Same input should always give same output
