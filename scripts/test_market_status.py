#!/usr/bin/env python3
"""
Test script to check market status filtering functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.market_watcher import MarketWatcher, check_symbol_tradeable
from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig

def test_market_status_filtering():
    """Test the market status filtering functionality."""
    print("🧪 Testing Market Status Filtering...")
    
    # Load environment and config
    load_environment()
    config = TradingConfig.from_env()
    
    # Create market watcher
    watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet)
    
    # Test getting active symbols
    print("\n1. Testing active symbols retrieval...")
    active_symbols = watcher.get_active_symbols()
    print(f"✅ Found {len(active_symbols)} actively trading symbols")
    
    # Test some common symbols
    test_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT"]
    
    print("\n2. Testing individual symbol status...")
    for symbol in test_symbols:
        is_tradeable = check_symbol_tradeable(symbol)
        status = "✅ TRADEABLE" if is_tradeable else "❌ NOT TRADEABLE"
        print(f"   {symbol}: {status}")
    
    # Test getting top movers with filtering
    print("\n3. Testing top movers with market status filtering...")
    top_movers = watcher.get_top_movers(limit=10)
    print(f"✅ Found {len(top_movers)} top movers (filtered for active markets)")
    
    for i, symbol in enumerate(top_movers[:5], 1):
        print(f"   {i}. {symbol}")
    
    print("\n🎉 Market status filtering test completed!")

if __name__ == "__main__":
    test_market_status_filtering()
