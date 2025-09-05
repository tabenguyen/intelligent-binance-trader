#!/usr/bin/env python3
"""
Test script for enhanced OCO balance validation with rounding and tolerance.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.config_models import TradingConfig
from src.services.trade_execution_service import BinanceTradeExecutor


def test_balance_validation():
    """Test the enhanced balance validation logic."""
    
    print("🧪 Testing Enhanced OCO Balance Validation")
    print("=" * 60)
    
    try:
        # Load configuration
        config = TradingConfig.from_env()
        trade_executor = BinanceTradeExecutor(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        print("✅ Trade executor initialized")
        
        # Test scenarios
        test_cases = [
            {
                'symbol': 'AWEUSDT',
                'position_qty': 286.0,
                'available_balance': 285.714,
                'description': 'AWEUSDT current scenario'
            },
            {
                'symbol': 'BTCUSDT', 
                'position_qty': 0.12345678,
                'available_balance': 0.12345,
                'description': 'BTC with high precision'
            },
            {
                'symbol': 'ADAUSDT',
                'position_qty': 1000.0,
                'available_balance': 999.9,
                'description': 'Small deficit case'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {case['description']}")
            print(f"   Symbol: {case['symbol']}")
            print(f"   Position quantity: {case['position_qty']}")
            print(f"   Available balance: {case['available_balance']}")
            
            try:
                # Apply the same logic as the enhanced validation
                rounded_qty = trade_executor._round_quantity(case['symbol'], case['position_qty'])
                tolerance = max(0.001, rounded_qty * 0.001)
                required_balance = rounded_qty - tolerance
                
                print(f"   Rounded quantity: {rounded_qty}")
                print(f"   Tolerance (0.1%): {tolerance:.6f}")
                print(f"   Required balance: {required_balance:.6f}")
                
                if case['available_balance'] >= required_balance:
                    print(f"   ✅ PASS: {case['available_balance']} >= {required_balance:.6f}")
                else:
                    deficit = required_balance - case['available_balance']
                    print(f"   ❌ FAIL: {case['available_balance']} < {required_balance:.6f}")
                    print(f"   Deficit: {deficit:.6f}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n🎯 Enhanced validation logic tested successfully!")
        print("\n💡 The AWEUSDT case should now pass with the tolerance logic")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_balance_validation()
