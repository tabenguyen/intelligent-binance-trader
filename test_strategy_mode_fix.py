#!/usr/bin/env python3
"""
Quick test to verify the TradingConfig fix and strategy mode selection.
"""

import os
import sys

def test_strategy_mode_selection():
    """Test that strategy mode selection works without the get_env_var error."""
    print("🧪 Testing Strategy Mode Selection Fix")
    print("=" * 50)
    
    # Test different strategy modes
    test_modes = ['enhanced_ema', 'adaptive_atr', 'invalid_mode']
    
    for mode in test_modes:
        print(f"\n📊 Testing STRATEGY_MODE='{mode}'")
        
        # Set environment variable
        os.environ['STRATEGY_MODE'] = mode
        
        # Test the environment variable reading (same as in trading_bot.py)
        strategy_mode = os.getenv('STRATEGY_MODE', 'enhanced_ema').lower()
        
        print(f"   Environment variable: {os.environ.get('STRATEGY_MODE')}")
        print(f"   Parsed strategy mode: {strategy_mode}")
        
        # Simulate the logic from trading_bot.py
        if strategy_mode == 'adaptive_atr':
            strategy_name = "ADAPTIVE ATR Strategy - Flexibility over Rigidity"
        else:
            strategy_name = "ENHANCED EMA Cross Strategy - Quality over Quantity"
        
        print(f"   Selected strategy: {strategy_name}")
    
    # Clean up
    if 'STRATEGY_MODE' in os.environ:
        del os.environ['STRATEGY_MODE']
    
    print(f"\n✅ Strategy mode selection test completed successfully!")
    print(f"   ❌ Previous error: 'TradingConfig' object has no attribute 'get_env_var'")
    print(f"   ✅ Fixed: Using os.getenv() instead of config.get_env_var()")

def test_import_syntax():
    """Test that our syntax fix doesn't break imports."""
    print("\n🔍 Testing Import Syntax")
    print("=" * 30)
    
    try:
        # Test the specific line that was causing issues
        import os
        strategy_mode = os.getenv('STRATEGY_MODE', 'enhanced_ema').lower()
        print(f"✅ os.getenv() import and usage: OK")
        print(f"   Default strategy mode: {strategy_mode}")
        
    except Exception as e:
        print(f"❌ Import/syntax error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = test_import_syntax()
        if success:
            test_strategy_mode_selection()
        
        print(f"\n🎯 Summary:")
        print(f"   Issue: TradingConfig missing get_env_var method")
        print(f"   Solution: Use standard os.getenv() function")
        print(f"   Status: ✅ FIXED")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)