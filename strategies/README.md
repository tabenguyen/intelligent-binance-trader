# Trading Strategies

This module contains abstract base classes and concrete implementations for trading strategies used by the automated trading bot.

## Architecture

### Base Strategy (`base_strategy.py`)

The `BaseStrategy` abstract base class defines the interface that all trading strategies must implement:

- `check_buy_signal()`: Abstract method to determine when to enter a trade
- `get_strategy_description()`: Abstract method to describe the strategy rules
- `validate_analysis_data()`: Helper method to validate required analysis data

### EMA Cross Strategy (`ema_cross_strategy.py`)

The default strategy implementation that uses EMA crossovers with RSI confirmation:

**Strategy Rules:**

1. **Trend Confirmation**: Price must be above the 50-EMA
2. **Bullish Momentum**: The 9-EMA must be above the 21-EMA
3. **Healthy Momentum**: RSI must be between 50 and 70
4. **Good Entry**: Price must be within 2% of the 21-EMA (support level)

## Usage

### Using the Default Strategy

```python
from strategies import EMACrossStrategy

# Initialize strategy
strategy = EMACrossStrategy()

# Use in trading logic
if strategy.check_buy_signal(symbol, analysis, current_price):
    # Execute trade
    pass
```

### Creating a Custom Strategy

To create a new trading strategy, inherit from `BaseStrategy`:

```python
from strategies.base_strategy import BaseStrategy
import logging

class MyCustomStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My Custom Strategy")
        self.required_indicators = ['RSI_14', 'MACD']

    def check_buy_signal(self, symbol: str, analysis: dict, current_price: float) -> bool:
        """Implement your custom buy signal logic here."""
        if not self.validate_analysis_data(analysis, self.required_indicators):
            return False

        # Your custom logic here
        if analysis['RSI_14'] < 30:  # Oversold condition
            logging.info(f"[{symbol}] Buy signal: RSI oversold")
            return True

        return False

    def get_strategy_description(self) -> str:
        return "Buys when RSI is oversold (< 30)"
```

### Switching Strategies

To use a different strategy in the main trading bot, modify `trading_bot.py`:

```python
# Instead of:
from strategies import EMACrossStrategy
trading_strategy = EMACrossStrategy()

# Use:
from strategies.my_custom_strategy import MyCustomStrategy
trading_strategy = MyCustomStrategy()
```

## Required Analysis Data

Strategies receive an `analysis` dictionary containing technical indicators. The EMA Cross Strategy expects:

- `'50_EMA'`: 50-period Exponential Moving Average
- `'21_EMA'`: 21-period Exponential Moving Average
- `'9_EMA'`: 9-period Exponential Moving Average
- `'RSI_14'`: 14-period Relative Strength Index
- `'Last_Swing_High'`: Recent swing high price
- `'Last_Swing_Low'`: Recent swing low price

## Configuration

The EMA Cross Strategy supports parameter configuration:

```python
strategy = EMACrossStrategy()
strategy.configure_parameters(
    rsi_lower=45,      # Lower RSI bound (default: 50)
    rsi_upper=75,      # Upper RSI bound (default: 70)
    ema_tolerance=0.03 # EMA distance tolerance (default: 0.02 = 2%)
)
```

## Benefits of This Architecture

1. **Separation of Concerns**: Trading logic is separated from execution logic
2. **Testability**: Strategies can be unit tested independently
3. **Flexibility**: Easy to switch between different strategies
4. **Extensibility**: New strategies can be added without modifying core bot logic
5. **Maintainability**: Each strategy is self-contained and documented
