#!/usr/bin/env python3
"""
Test script to verify the configurable minimum notional value is working correctly.
"""

import os
import sys
import tempfile

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.config_models import TradingConfig
from src.services.risk_management_service import RiskManagementService
from src.models.trade_models import TradingSignal, TradeDirection
from datetime import datetime


def test_min_notional_config():
    """Test that minimum notional configuration is properly used."""
    
    print("🧪 Testing Configurable Minimum Notional Value")
    print("=" * 60)
    
    # Test 1: Default configuration (15.0)
    print("\n📋 Test 1: Default MIN_NOTIONAL_USDT (15.0)")
    config = TradingConfig.from_env()
    risk_service = RiskManagementService(config)
    
    print(f"   ✅ Default min_notional_usdt: ${risk_service.config.min_notional_usdt:.2f}")
    assert risk_service.config.min_notional_usdt == 15.0, "Default should be 15.0"
    
    # Test 2: Position sizing with balance below minimum
    print("\n📋 Test 2: Position sizing with balance below minimum notional")
    signal = TradingSignal(
        symbol="BTCUSDT",
        direction=TradeDirection.BUY,
        price=50000.0,
        confidence=0.8,
        timestamp=datetime.now(),
        strategy_name="test",
        indicators={},
        stop_loss=49000.0,
        take_profit=52000.0
    )
    
    # Balance below minimum notional
    low_balance = 10.0
    position_size = risk_service.calculate_position_size(signal, low_balance)
    print(f"   Balance: ${low_balance:.2f}")
    print(f"   Min notional: ${risk_service.config.min_notional_usdt:.2f}")
    print(f"   Position size: {position_size}")
    assert position_size == 0.0, "Should return 0 when balance is below minimum notional"
    print("   ✅ Correctly returned 0 for insufficient balance")
    
    # Test 3: Position sizing with balance above minimum
    print("\n📋 Test 3: Position sizing with balance above minimum notional")
    good_balance = 100.0
    position_size = risk_service.calculate_position_size(signal, good_balance)
    print(f"   Balance: ${good_balance:.2f}")
    print(f"   Min notional: ${risk_service.config.min_notional_usdt:.2f}")
    print(f"   Position size: {position_size:.6f}")
    assert position_size > 0, "Should return positive position size for sufficient balance"
    print("   ✅ Correctly calculated position size for sufficient balance")
    
    # Test 4: Custom minimum notional via environment
    print("\n📋 Test 4: Custom MIN_NOTIONAL_USDT via environment")
    
    # Set custom value
    original_value = os.environ.get('MIN_NOTIONAL_USDT', '')
    os.environ['MIN_NOTIONAL_USDT'] = '25.0'
    
    try:
        # Reload configuration
        custom_config = TradingConfig.from_env()
        custom_risk_service = RiskManagementService(custom_config)
        
        print(f"   ✅ Custom min_notional_usdt: ${custom_risk_service.config.min_notional_usdt:.2f}")
        assert custom_risk_service.config.min_notional_usdt == 25.0, "Should use custom value"
        
        # Test with balance between old and new minimum
        test_balance = 20.0
        position_size = custom_risk_service.calculate_position_size(signal, test_balance)
        print(f"   Balance: ${test_balance:.2f} (between old min 15.0 and new min 25.0)")
        print(f"   Position size: {position_size}")
        assert position_size == 0.0, "Should return 0 when balance is below new minimum"
        print("   ✅ Correctly enforces custom minimum notional")
        
    finally:
        # Restore original environment
        if original_value:
            os.environ['MIN_NOTIONAL_USDT'] = original_value
        elif 'MIN_NOTIONAL_USDT' in os.environ:
            del os.environ['MIN_NOTIONAL_USDT']
    
    print("\n🎉 All tests passed! Configurable minimum notional is working correctly.")
    print("\n💡 Usage:")
    print("   Set MIN_NOTIONAL_USDT=20.0 in your .env file to use $20 minimum")
    print("   Default is $15.00 if not specified")


if __name__ == "__main__":
    test_min_notional_config()
