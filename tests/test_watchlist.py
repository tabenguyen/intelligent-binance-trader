#!/usr/bin/env python3
"""
Test script to verify watchlist generation works for both testnet and live mode
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.config_models import TradingConfig
from src.market_watcher import update_watchlist_from_top_movers

def test_watchlist_generation():
    """Test watchlist generation for both modes."""
    
    # Test with current environment (should be testnet based on .env)
    print("=== Testing current mode (from .env) ===")
    try:
        config = TradingConfig.from_env()
        print(f"Mode: {'Testnet' if config.testnet else 'Live'}")
        print(f"Expected watchlist file: {config.get_mode_specific_watchlist_file()}")
        
        # Test the watchlist update
        symbols = update_watchlist_from_top_movers(limit=10)
        if symbols:
            print(f"✅ Successfully generated {len(symbols)} symbols:")
            for symbol in symbols[:5]:  # Show first 5
                print(f"  - {symbol}")
            if len(symbols) > 5:
                print(f"  ... and {len(symbols) - 5} more")
        else:
            print("❌ Failed to generate watchlist")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()
    
    # Test live mode by temporarily setting testnet=False
    print("=== Testing live mode ===")
    try:
        # Temporarily override for live mode test
        original_testnet = os.environ.get('TESTNET', 'true')
        os.environ['TESTNET'] = 'false'
        
        config_live = TradingConfig.from_env()
        print(f"Mode: {'Testnet' if config_live.testnet else 'Live'}")
        print(f"Expected watchlist file: {config_live.get_mode_specific_watchlist_file()}")
        
        # Check if the live watchlist file exists
        live_watchlist_path = Path(config_live.get_mode_specific_watchlist_file())
        if live_watchlist_path.exists():
            print(f"✅ Live watchlist file exists: {live_watchlist_path}")
            with open(live_watchlist_path, 'r') as f:
                symbols = [line.strip() for line in f.readlines() if line.strip()]
            print(f"✅ Contains {len(symbols)} symbols")
        else:
            print(f"❌ Live watchlist file doesn't exist: {live_watchlist_path}")
        
        # Restore original setting
        os.environ['TESTNET'] = original_testnet
        
    except Exception as e:
        print(f"❌ Error testing live mode: {e}")
        # Restore original setting
        if 'original_testnet' in locals():
            os.environ['TESTNET'] = original_testnet

if __name__ == "__main__":
    test_watchlist_generation()
