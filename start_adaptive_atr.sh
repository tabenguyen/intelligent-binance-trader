#!/bin/bash

# Adaptive ATR Strategy Mode Startup Script
# This script demonstrates how to run the trading bot with the new adaptive ATR strategy

echo "🚀 Starting Trading Bot with Adaptive ATR Strategy"
echo "=============================================="

# Set environment variables for adaptive ATR mode
export STRATEGY_MODE="adaptive_atr"

# Optional: Override specific ATR strategy parameters
export ATR_MIN_PERCENTILE="5.0"
export ATR_MAX_PERCENTILE="95.0" 
export USE_DYNAMIC_STOP_LOSS="true"
export USE_TRAILING_STOP="true"
export INITIAL_TP_ATR_MULTIPLIER="2.0"
export TRAILING_STOP_ATR_MULTIPLIER="1.0"
export MIN_PROFIT_BEFORE_TRAIL="0.015"

echo "📊 Adaptive ATR Strategy Configuration:"
echo "   Strategy Mode: $STRATEGY_MODE"
echo "   ATR Range: $ATR_MIN_PERCENTILE% - $ATR_MAX_PERCENTILE%"
echo "   Dynamic Stop-Loss: $USE_DYNAMIC_STOP_LOSS"
echo "   Trailing Stop: $USE_TRAILING_STOP"
echo "   Initial TP Multiplier: ${INITIAL_TP_ATR_MULTIPLIER}x ATR"
echo "   Trailing Stop Distance: ${TRAILING_STOP_ATR_MULTIPLIER}x ATR"
echo "   Min Profit Before Trail: $(echo "$MIN_PROFIT_BEFORE_TRAIL * 100" | bc -l)%"

echo ""
echo "🎯 Key Features of Adaptive ATR Strategy:"
echo "   • Wide ATR acceptance (5%-95% vs previous 30%-70%)"
echo "   • Dynamic stop-loss based on market volatility"
echo "   • Trailing stop take-profit to let winners run"
echo "   • Market condition awareness (trending/consolidating/volatile)"
echo "   • Volatility-adjusted position sizing"
echo "   • Lower confidence threshold (65% vs 80%) for more opportunities"

echo ""
echo "💡 Strategy Differences vs Enhanced EMA:"
echo "   Enhanced EMA: Quality over quantity (fewer, higher quality trades)"
echo "   Adaptive ATR: Flexibility over rigidity (more opportunities, adaptive)"

echo ""
echo "⚡ Starting bot with adaptive ATR strategy..."

# Run the trading bot with adaptive ATR strategy
python3 main.py