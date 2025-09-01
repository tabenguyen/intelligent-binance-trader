#!/usr/bin/env python3
"""
Test script for Advanced Exit Strategies

This script tests the logic and calculations for:
1. Trailing stop loss based on ATR
2. Partial take profits at TP1 (1.5:1 R:R) and TP2 (3:1 R:R)
3. Risk-reward calculations
4. Breakeven stop management
"""

import pandas as pd

def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range manually."""
    tr_list = []
    for i in range(1, len(high)):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i-1])
        tr3 = abs(low[i] - close[i-1])
        tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    
    # Calculate ATR as simple moving average of TR
    if len(tr_list) >= period:
        return sum(tr_list[-period:]) / period
    else:
        return sum(tr_list) / len(tr_list) if tr_list else 0

def test_advanced_exit_logic():
    """Test the advanced exit strategy calculations."""
    print("🧪 Testing Advanced Exit Strategy Logic")
    print("=" * 60)
    
    # Test trade parameters
    entry_price = 100.0
    initial_stop_loss = 95.0  # 5% stop loss
    risk_per_share = entry_price - initial_stop_loss  # $5.00
    quantity = 10.0
    total_risk = risk_per_share * quantity  # $50.00
    
    print(f"📊 Test Trade Setup:")
    print(f"  Entry Price: ${entry_price:.2f}")
    print(f"  Initial Stop: ${initial_stop_loss:.2f}")
    print(f"  Risk per Share: ${risk_per_share:.2f}")
    print(f"  Quantity: {quantity:.2f}")
    print(f"  Total Risk: ${total_risk:.2f}")
    print()
    
    # Test TP1 calculation (1.5:1 R:R)
    tp1_ratio = 1.5
    tp1_profit_target = risk_per_share * tp1_ratio  # $7.50 profit per share
    tp1_price = entry_price + tp1_profit_target  # $107.50
    tp1_percentage = 0.5  # 50%
    tp1_quantity = quantity * tp1_percentage  # 5 shares
    tp1_profit = tp1_profit_target * tp1_quantity  # $37.50
    
    print(f"🎯 Take Profit 1 (TP1) - {tp1_ratio}:1 R:R:")
    print(f"  Target Price: ${tp1_price:.2f}")
    print(f"  Quantity to Sell: {tp1_quantity:.2f} ({tp1_percentage*100}%)")
    print(f"  Profit from TP1: ${tp1_profit:.2f}")
    print()
    
    # Test TP2 calculation (3:1 R:R)
    tp2_ratio = 3.0
    tp2_profit_target = risk_per_share * tp2_ratio  # $15.00 profit per share
    tp2_price = entry_price + tp2_profit_target  # $115.00
    tp2_quantity = quantity - tp1_quantity  # 5 shares remaining
    tp2_profit = tp2_profit_target * tp2_quantity  # $75.00
    
    print(f"🎯 Take Profit 2 (TP2) - {tp2_ratio}:1 R:R:")
    print(f"  Target Price: ${tp2_price:.2f}")
    print(f"  Remaining Quantity: {tp2_quantity:.2f}")
    print(f"  Profit from TP2: ${tp2_profit:.2f}")
    print(f"  Total Profit: ${tp1_profit + tp2_profit:.2f}")
    print()
    
    # Test ATR trailing stop
    current_price = 108.0  # Price after TP1
    atr_value = 2.5
    atr_multiplier = 2.0
    trailing_stop = current_price - (atr_value * atr_multiplier)  # $103.00
    
    print(f"📈 Trailing Stop Loss (ATR-based):")
    print(f"  Current Price: ${current_price:.2f}")
    print(f"  ATR Value: {atr_value:.2f}")
    print(f"  ATR Multiplier: {atr_multiplier:.1f}")
    print(f"  Trailing Stop: ${trailing_stop:.2f}")
    print(f"  Stop Distance: ${current_price - trailing_stop:.2f}")
    print()
    
    # Test breakeven stop after TP1
    breakeven_stop = entry_price * 1.001  # Slightly above entry for fees
    remaining_risk = max(0, (entry_price - breakeven_stop) * tp2_quantity)
    
    print(f"🛡️ Risk Management After TP1:")
    print(f"  Breakeven Stop: ${breakeven_stop:.2f}")
    print(f"  Remaining Risk: ${remaining_risk:.2f}")
    print(f"  Risk Reduction: {((total_risk - remaining_risk) / total_risk) * 100:.1f}%")
    print()
    
    # Test scenario outcomes
    print(f"📊 Scenario Analysis:")
    print(f"  Scenario 1 - Hit TP1 only (stopped at breakeven):")
    print(f"    Profit: ${tp1_profit:.2f} | ROI: {(tp1_profit / (entry_price * quantity)) * 100:.1f}%")
    print()
    print(f"  Scenario 2 - Hit both TP1 and TP2:")
    print(f"    Total Profit: ${tp1_profit + tp2_profit:.2f} | ROI: {((tp1_profit + tp2_profit) / (entry_price * quantity)) * 100:.1f}%")
    print()
    print(f"  Scenario 3 - Hit TP1, then trailing stop at $110:")
    trailing_exit_price = 110.0
    trailing_profit = (trailing_exit_price - entry_price) * tp2_quantity
    total_trailing_profit = tp1_profit + trailing_profit
    print(f"    TP1 Profit: ${tp1_profit:.2f}")
    print(f"    Trailing Exit Profit: ${trailing_profit:.2f}")
    print(f"    Total Profit: ${total_trailing_profit:.2f} | ROI: {(total_trailing_profit / (entry_price * quantity)) * 100:.1f}%")


def test_atr_calculation():
    """Test ATR calculation for trailing stops."""
    print("\n🧮 Testing ATR Calculation for Trailing Stops")
    print("=" * 60)
    
    # Create sample price data
    high_prices = [102, 104, 106, 105, 108, 110, 109, 112, 115, 113]
    low_prices = [98, 100, 102, 101, 104, 106, 105, 108, 111, 109]
    close_prices = [100, 102, 104, 103, 106, 108, 107, 110, 113, 111]
    
    current_atr = calculate_atr(high_prices, low_prices, close_prices)
    current_price = close_prices[-1]
    
    print(f"Sample Price Data (last 10 periods):")
    print(f"  Current Price: ${current_price:.2f}")
    print(f"  Current ATR: {current_atr:.2f}")
    print()
    
    # Test different ATR multipliers
    multipliers = [1.5, 2.0, 2.5, 3.0]
    
    print(f"Trailing Stop Distances with Different ATR Multipliers:")
    for mult in multipliers:
        stop_distance = current_atr * mult
        trailing_stop = current_price - stop_distance
        distance_pct = (stop_distance / current_price) * 100
        
        print(f"  {mult:.1f}x ATR: ${trailing_stop:.2f} (distance: {distance_pct:.2f}%)")
    print()


def test_risk_reward_calculations():
    """Test risk-reward ratio calculations."""
    print("⚖️ Testing Risk-Reward Calculations")
    print("=" * 60)
    
    entry_price = 50.0
    stop_loss = 47.5  # 5% stop
    
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Risk per Share: ${entry_price - stop_loss:.2f}")
    print()
    
    # Test different current prices
    test_prices = [52.5, 55.0, 57.5, 60.0, 62.5, 65.0]
    
    print("Risk-Reward Ratios at Different Price Levels:")
    for price in test_prices:
        profit_per_share = price - entry_price
        risk_per_share = entry_price - stop_loss
        rr_ratio = profit_per_share / risk_per_share
        
        action = ""
        if rr_ratio >= 3.0:
            action = "→ Execute TP2 (Final Exit)"
        elif rr_ratio >= 1.5:
            action = "→ Execute TP1 (50% Exit)"
        
        print(f"  ${price:.2f}: {rr_ratio:.2f}:1 R:R {action}")


if __name__ == "__main__":
    test_advanced_exit_logic()
    test_atr_calculation()
    test_risk_reward_calculations()
    
    print("\n✅ All Advanced Exit Strategy Tests Completed!")
    print("\nThe advanced exit system provides:")
    print("• Early profit taking at 1.5:1 R:R (reduces risk)")
    print("• Breakeven stop after TP1 (risk-free position)")
    print("• ATR-based trailing stops (adapts to volatility)")
    print("• Maximum profit capture at 3:1 R:R")
    print("• Superior risk management vs fixed stop/target")
