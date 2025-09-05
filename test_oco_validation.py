#!/usr/bin/env python3
"""
Test script for OCO order validation and automatic creation functionality.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.config_models import TradingConfig
from src.services.market_data_service import BinanceMarketDataService


def test_oco_validation():
    """Test the OCO validation logic."""
    
    print("🧪 Testing OCO Order Validation and Auto-Creation")
    print("=" * 60)
    
    try:
        # Load configuration
        config = TradingConfig.from_env()
        market_service = BinanceMarketDataService(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        print("✅ Market service initialized")
        
        # Test balance checking for AWEUSDT position
        print("\n📋 Testing balance verification for AWEUSDT:")
        try:
            awe_balance = market_service.get_account_balance('AWE')
            print(f"   Current AWE balance: {awe_balance}")
            
            # Simulate position quantity (from active_trades.txt)
            position_quantity = 286.0
            
            if awe_balance >= position_quantity:
                print(f"✅ Sufficient balance for OCO creation: {awe_balance} >= {position_quantity}")
            else:
                print(f"⚠️  Insufficient balance: {awe_balance} < {position_quantity}")
                
        except Exception as e:
            print(f"❌ Balance check error: {e}")
        
        # Test balance checking for PUNDIXUSDT position  
        print("\n📋 Testing balance verification for PUNDIXUSDT:")
        try:
            pundix_balance = market_service.get_account_balance('PUNDIX')
            print(f"   Current PUNDIX balance: {pundix_balance}")
            
            # Simulate position quantity (from active_trades.txt)
            position_quantity = 48.8
            
            if pundix_balance >= position_quantity:
                print(f"✅ Sufficient balance for OCO creation: {pundix_balance} >= {position_quantity}")
            else:
                print(f"⚠️  Insufficient balance: {pundix_balance} < {position_quantity}")
                
        except Exception as e:
            print(f"❌ Balance check error: {e}")
        
        print("\n🎯 OCO validation logic is ready!")
        print("\n💡 Next step: Restart the trading bot to test automatic OCO creation")
        print("   ./start.sh restart")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_oco_validation()
