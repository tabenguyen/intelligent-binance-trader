#!/usr/bin/env python3
"""
Test script for the simplified MarketWatcher (2-criteria system).
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.market_watcher import MarketWatcher
from src.models import TradingConfig

def test_simplified_market_watcher():
    """Test the simplified 2-criteria MarketWatcher."""
    print("🧪 Testing Simplified MarketWatcher (2-criteria system)")
    print("="*60)
    
    try:
        # Load config
        config = TradingConfig.from_env()
        
        # Create MarketWatcher instance
        watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet, quote="USDT")
        
        # Test getting top movers
        print("1. Getting top movers...")
        top_movers = watcher.get_top_movers(limit=5)
        print(f"   Found {len(top_movers)} top movers: {top_movers}")
        
        if not top_movers:
            print("❌ No top movers found, skipping ranking test")
            return
        
        # Test simplified ranking
        print("\n2. Testing simplified 2-criteria ranking...")
        ranked_symbols = watcher.get_ranked_symbols(top_movers[:3])  # Test with 3 symbols
        
        print(f"\n3. Ranking Results:")
        for i, data in enumerate(ranked_symbols, 1):
            print(f"   {i}. {data['symbol']} - Score: {data['composite_score']:.2f}")
            print(f"      RelStr: {data['relative_strength_vs_btc']:.2f}% vs BTC")
            print(f"      ADX: {data['trend_strength_adx']:.2f}")
            print()
        
        # Test composite score calculation directly
        print("4. Testing composite score calculation...")
        test_score = watcher._calculate_composite_score(rel_strength=5.0, adx=30.0)
        print(f"   Test score (RelStr=5.0%, ADX=30.0): {test_score:.2f}")
        
        # Test with None values
        test_score_none = watcher._calculate_composite_score(rel_strength=None, adx=25.0)
        print(f"   Test score (RelStr=None, ADX=25.0): {test_score_none:.2f}")
        
        print("\n✅ Simplified MarketWatcher test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simplified_market_watcher()
    sys.exit(0 if success else 1)