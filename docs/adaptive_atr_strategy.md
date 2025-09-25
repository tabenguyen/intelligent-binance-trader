# Adaptive ATR Strategy Documentation

## Overview

The **Adaptive ATR Strategy** implements a "Flexibility over Rigidity" approach to trading, designed to adapt to various market conditions by accepting a wide range of volatility levels (5%-95% ATR percentile) and using dynamic risk management based on ATR (Average True Range).

## Key Features

### 🎯 Wide ATR Range Acceptance

- **ATR Range:** 5%-95% percentile (vs previous 30%-70%)
- **Philosophy:** Accept more trading opportunities across different volatility regimes
- **Benefit:** Allows trading in both calm and volatile market conditions

### 📊 Dynamic Stop-Loss (ATR-Based)

Instead of fixed percentage stops, the strategy uses volatility-adaptive stops:

- **Low Volatility (5%-30% ATR):** 1.0x ATR stop-loss
- **Medium Volatility (30%-70% ATR):** 1.5x ATR stop-loss
- **High Volatility (70%-95% ATR):** 2.0x ATR stop-loss

### 🚀 Flexible Take-Profit (Trailing Stops)

- **Initial Take-Profit:** 2.0x ATR above entry
- **Trailing Stop:** 1.0x ATR below peak price
- **Activation:** Only after minimum 1.5% profit achieved
- **Benefit:** Let winning trades run while protecting profits

### 🌊 Market Condition Awareness

The strategy adapts entry conditions based on market type:

#### Trending Markets (ADX > 25)

- **RSI Range:** 40-80 (more lenient)
- **Stop Adjustment:** 20% tighter stops
- **Logic:** Follow trends with appropriate risk management

#### Consolidating Markets (BB Width < 2%)

- **RSI Range:** 30-60 (oversold bounces)
- **Stop Adjustment:** Standard stops
- **Logic:** Trade range bounces with measured risk

#### Volatile Markets (High ATR)

- **RSI Range:** 35-75 (standard)
- **Stop Adjustment:** 20% wider stops
- **Logic:** Account for increased price swings

### 💰 Volatility-Adjusted Position Sizing

- **High Volatility (80%+ ATR):** Reduce position by 30%
- **Medium-High Volatility (60%+ ATR):** Reduce position by 15%
- **Low Volatility (20%- ATR):** Increase position by 15%
- **Standard Volatility:** No adjustment

## Configuration Parameters

### ATR Flexibility

```python
'atr_min_percentile': 5.0,     # Accept from 5th percentile
'atr_max_percentile': 95.0,    # Accept up to 95th percentile
'enable_atr_adaptation': True,  # Enable ATR-based adaptations
```

### Dynamic Stop-Loss

```python
'use_dynamic_stop_loss': True,
'low_volatility_stop_multiplier': 1.0,    # 1.0x ATR for low vol
'medium_volatility_stop_multiplier': 1.5, # 1.5x ATR for medium vol
'high_volatility_stop_multiplier': 2.0,   # 2.0x ATR for high vol
```

### Trailing Stop

```python
'use_trailing_stop': True,
'initial_tp_atr_multiplier': 2.0,        # Initial TP: 2x ATR
'trailing_stop_atr_multiplier': 1.0,     # Trailing: 1x ATR from peak
'min_profit_before_trail': 0.015,        # Minimum 1.5% profit before trailing
```

### Entry Conditions

```python
'rsi_oversold_threshold': 35,            # More flexible RSI
'rsi_overbought_threshold': 75,          # More flexible RSI
'ema_cross_confirmation': True,          # Still need EMA cross
'volume_confirmation_ratio': 1.2,        # Lower volume requirement
```

## Usage

### Environment Variables

Set the strategy mode via environment variable:

```bash
export STRATEGY_MODE="adaptive_atr"
```

### Startup Script

Use the provided startup script:

```bash
./start_adaptive_atr.sh
```

### Manual Configuration

```python
from src.strategies.adaptive_atr_strategy import AdaptiveATRStrategy

# Create with default config
strategy = AdaptiveATRStrategy()

# Create with custom config
custom_config = StrategyConfig(
    name="Custom Adaptive ATR",
    parameters={
        'atr_min_percentile': 10.0,  # Slightly narrower range
        'atr_max_percentile': 90.0,
        'use_trailing_stop': True,
        # ... other parameters
    }
)
strategy = AdaptiveATRStrategy(custom_config)
```

## Comparison with Enhanced EMA Strategy

| Aspect                   | Enhanced EMA               | Adaptive ATR              |
| ------------------------ | -------------------------- | ------------------------- |
| **Philosophy**           | Quality over Quantity      | Flexibility over Rigidity |
| **ATR Range**            | 30%-70% (narrow)           | 5%-95% (wide)             |
| **Stop-Loss**            | Fixed % + ATR              | Dynamic ATR-based         |
| **Take-Profit**          | Fixed ATR multiple         | Trailing stop             |
| **Entry Conditions**     | Very strict (3/4 required) | Flexible (3/4 required)   |
| **Confidence Threshold** | 80% (high)                 | 65% (moderate)            |
| **Position Sizing**      | Quality-based bonus        | Volatility-adjusted       |
| **Market Adaptation**    | Limited                    | Comprehensive             |

## Risk Management Integration

The Adaptive ATR Strategy integrates with the Enhanced Risk Management Service:

### Trailing Stop Management

```python
# Update trailing stop as price moves favorably
new_stop = risk_service.update_trailing_stop(
    position_entry_price=entry_price,
    current_price=current_price,
    current_stop_loss=current_stop,
    signal=original_signal
)

# Check if trailing stop should trigger exit
should_exit = risk_service.should_exit_with_trailing_stop(
    position_entry_price=entry_price,
    current_price=current_price,
    current_stop_loss=current_stop,
    signal=original_signal
)
```

### Signal Metadata

Each signal includes metadata for risk management:

```python
signal.indicators.update({
    'strategy_type': 'adaptive_atr',
    'market_condition': 'trending_medium_vol',
    'volatility_adjustment': 0.85,
    'use_trailing_stop': True,
    'trailing_stop_atr_multiplier': 1.0,
    'min_profit_before_trail': 0.015
})
```

## Testing

### Unit Tests

Run the test script to validate functionality:

```bash
python3 test_adaptive_atr_strategy.py
```

### Integration Tests

Test with live market data:

```bash
# Set test mode
export STRATEGY_MODE="adaptive_atr"
export TESTNET="true"

# Run bot in simulation
python3 main.py
```

## Expected Outcomes

### More Trading Opportunities

- **Before:** Limited to 30%-70% ATR range
- **After:** Accept 5%-95% ATR range (3x wider acceptance)

### Better Risk Management

- **Dynamic Stops:** Adapt to market volatility instead of fixed %
- **Trailing Profits:** Let winners run while protecting gains
- **Position Sizing:** Reduce risk in high volatility environments

### Market Adaptability

- **Trending Markets:** Follow trends with appropriate stops
- **Consolidating Markets:** Trade bounces with measured risk
- **Volatile Markets:** Wider stops to avoid premature exits

## Evolution Path

This strategy represents the evolution from rigid rules to adaptive systems:

1. **Stop-Loss Evolution:** Fixed % → Dynamic ATR-based
2. **Take-Profit Evolution:** Fixed targets → Flexible trailing stops
3. **Entry Evolution:** Strict conditions → Market-adaptive conditions
4. **Risk Evolution:** One-size-fits-all → Volatility-adjusted

The goal is to create a more robust system that can perform well across different market regimes while maintaining appropriate risk controls.
