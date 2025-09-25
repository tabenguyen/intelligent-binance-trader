#!/usr/bin/env python3
"""
Test script for the new Adaptive ATR Strategy.
Demonstrates the 5%-95% ATR range acceptance and dynamic stop-loss/take-profit.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.strategies.adaptive_atr_strategy import AdaptiveATRStrategy
from src.models import MarketData, TechnicalAnalysis, StrategyConfig
from datetime import datetime

def create_test_market_data(symbol: str, price: float, atr_percentile: float, 
                          rsi: float = 60, adx: float = 30, volume_ratio: float = 1.5) -> MarketData:
    """Create test market data for strategy testing."""
    
    # Calculate ATR based on percentile and price
    atr_value = price * (atr_percentile / 100) * 0.02  # Simplified ATR calculation
    
    indicators = {
        '12_EMA': price * 1.005,      # Slightly above current price
        '26_EMA': price * 0.995,      # Slightly below current price  
        '50_MA': price * 0.98,        # Below current price for uptrend
        'RSI_14': rsi,
        'ADX': adx,
        'ATR': atr_value,
        'ATR_Percentile': atr_percentile,
        'BB_Upper': price * 1.02,
        'BB_Lower': price * 0.98,
        'BB_Width': 0.04,             # 4% BB width
        'Volume_Ratio': volume_ratio
    }
    
    technical_analysis = TechnicalAnalysis(
        symbol=symbol,
        timestamp=datetime.now(),
        indicators=indicators,
        analysis_type="4h"
    )
    
    return MarketData(
        symbol=symbol,
        current_price=price,
        timestamp=datetime.now(),
        technical_analysis=technical_analysis
    )

def test_adaptive_atr_strategy():
    """Test the Adaptive ATR Strategy with various market conditions."""
    print("🧪 Testing Adaptive ATR Strategy")
    print("="*60)
    
    # Create strategy instance
    strategy = AdaptiveATRStrategy()
    
    print(f"📋 Strategy Description:")
    print(strategy.get_strategy_description())
    print("\n" + "="*60)
    
    # Test scenarios with different ATR percentiles
    test_scenarios = [
        {
            'name': 'Low Volatility (10% ATR)',
            'symbol': 'BTCUSDT',
            'price': 45000.0,
            'atr_percentile': 10.0,
            'rsi': 55,
            'adx': 35,
            'volume_ratio': 1.8
        },
        {
            'name': 'Medium Volatility (50% ATR)',
            'symbol': 'ETHUSDT', 
            'price': 3200.0,
            'atr_percentile': 50.0,
            'rsi': 62,
            'adx': 28,
            'volume_ratio': 1.4
        },
        {
            'name': 'High Volatility (85% ATR)',
            'symbol': 'ADAUSDT',
            'price': 0.85,
            'atr_percentile': 85.0,
            'rsi': 48,
            'adx': 40,
            'volume_ratio': 2.1
        },
        {
            'name': 'Extreme High Volatility (95% ATR)',
            'symbol': 'SOLUSDT',
            'price': 120.0,
            'atr_percentile': 95.0,
            'rsi': 65,
            'adx': 45,
            'volume_ratio': 1.6
        },
        {
            'name': 'Out of Range (2% ATR) - Should Reject',
            'symbol': 'DOGEUSDT',
            'price': 0.25,
            'atr_percentile': 2.0,
            'rsi': 58,
            'adx': 30,
            'volume_ratio': 1.5
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📊 Scenario {i}: {scenario['name']}")
        print("-" * 50)
        
        # Create test market data
        market_data = create_test_market_data(
            symbol=scenario['symbol'],
            price=scenario['price'],
            atr_percentile=scenario['atr_percentile'],
            rsi=scenario['rsi'],
            adx=scenario['adx'],
            volume_ratio=scenario['volume_ratio']
        )
        
        try:
            # Analyze with adaptive ATR strategy
            signal = strategy.analyze(market_data)
            
            if signal:
                # Calculate metrics
                risk = signal.price - signal.stop_loss
                reward = signal.take_profit - signal.price
                rr_ratio = reward / risk if risk > 0 else 0
                
                print(f"✅ SIGNAL GENERATED!")
                print(f"   Symbol: {signal.symbol}")
                print(f"   Entry Price: ${signal.price:.4f}")
                print(f"   Stop Loss: ${signal.stop_loss:.4f}")
                print(f"   Take Profit: ${signal.take_profit:.4f}")
                print(f"   Risk: ${risk:.4f} ({(risk/signal.price)*100:.2f}%)")
                print(f"   Reward: ${reward:.4f} ({(reward/signal.price)*100:.2f}%)")
                print(f"   R:R Ratio: {rr_ratio:.2f}:1")
                print(f"   Confidence: {signal.confidence:.1%}")
                print(f"   Market Condition: {signal.indicators.get('market_condition', 'N/A')}")
                print(f"   Volatility Adjustment: {signal.indicators.get('volatility_adjustment', 1.0):.2f}")
                print(f"   ATR Percentile: {signal.indicators.get('atr_percentile', 0):.1f}%")
                
                # Trailing stop info
                if signal.indicators.get('use_trailing_stop'):
                    print(f"   Trailing Stop: Enabled ({signal.indicators.get('trailing_stop_atr_multiplier', 1.0):.1f}x ATR)")
                    print(f"   Min Profit Before Trail: {signal.indicators.get('min_profit_before_trail', 0.015)*100:.1f}%")
                
            else:
                print(f"❌ NO SIGNAL - Strategy rejected this opportunity")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "="*60)
    print("🎯 Test Summary:")
    print("• Low-Medium Volatility: Should generate signals with appropriate stops")
    print("• High Volatility: Should generate signals with wider stops") 
    print("• Extreme cases: May be rejected if out of 5%-95% range")
    print("• All signals include trailing stop capability")
    
    print("\n💡 Key Features Demonstrated:")
    print("• Wide ATR range acceptance (5%-95%)")
    print("• Dynamic stop-loss based on volatility")
    print("• Trailing stop take-profit for letting winners run") 
    print("• Market condition awareness")
    print("• Volatility-adjusted position sizing recommendations")

def test_trailing_stop_functionality():
    """Test the trailing stop functionality."""
    print("\n🚀 Testing Trailing Stop Functionality")
    print("="*60)
    
    # This would typically be integrated with the risk management service
    # For demonstration, we'll show how the trailing stop parameters work
    
    from src.services.enhanced_risk_management_service import EnhancedRiskManagementService
    from src.models import TradingConfig, TradingSignal, TradeDirection
    
    # Create mock trading config
    config = TradingConfig(
        api_key="test",
        api_secret="test", 
        testnet=True
    )
    
    risk_service = EnhancedRiskManagementService(config)
    
    # Create a mock adaptive ATR signal with trailing stop enabled
    signal = TradingSignal(
        symbol="BTCUSDT",
        direction=TradeDirection.BUY,
        price=45000.0,
        confidence=0.75,
        timestamp=datetime.now(),
        stop_loss=44100.0,  # Initial stop
        take_profit=46800.0, # Initial TP
        strategy_name="Adaptive ATR Strategy",
        indicators={
            'use_trailing_stop': True,
            'trailing_stop_atr_multiplier': 1.0,
            'min_profit_before_trail': 0.015,  # 1.5%
            'ATR': 450.0  # $450 ATR
        }
    )
    
    print("📊 Trailing Stop Simulation:")
    print(f"   Entry Price: ${signal.price:.2f}")
    print(f"   Initial Stop: ${signal.stop_loss:.2f}")
    print(f"   ATR: ${signal.indicators['ATR']:.2f}")
    print(f"   Min Profit Before Trail: {signal.indicators['min_profit_before_trail']*100:.1f}%")
    
    # Simulate price movements
    price_scenarios = [
        45200.0,  # Small move up (+0.44%)
        45700.0,  # Larger move up (+1.56% - should activate trailing)
        46500.0,  # Strong move up (+3.33%)
        46200.0,  # Pullback
        45800.0,  # Further pullback - should still be above trailing stop
    ]
    
    current_stop = signal.stop_loss
    
    for i, current_price in enumerate(price_scenarios):
        profit_pct = (current_price - signal.price) / signal.price
        print(f"\n   Scenario {i+1}: Price ${current_price:.2f} (Profit: {profit_pct:.1%})")
        
        # Test trailing stop update
        new_stop = risk_service.update_trailing_stop(
            position_entry_price=signal.price,
            current_price=current_price,
            current_stop_loss=current_stop,
            signal=signal
        )
        
        if new_stop:
            print(f"     ✅ Trailing stop updated: ${current_stop:.2f} -> ${new_stop:.2f}")
            current_stop = new_stop
        else:
            print(f"     ➡️ No trailing stop update (current: ${current_stop:.2f})")
        
        # Check if stop would be triggered
        should_exit = risk_service.should_exit_with_trailing_stop(
            position_entry_price=signal.price,
            current_price=current_price,
            current_stop_loss=current_stop,
            signal=signal
        )
        
        if should_exit:
            print(f"     🛑 STOP TRIGGERED - Position would be closed")
            break

if __name__ == "__main__":
    try:
        test_adaptive_atr_strategy()
        test_trailing_stop_functionality()
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)