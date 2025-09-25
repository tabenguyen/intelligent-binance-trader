#!/usr/bin/env python3
"""
Simple test script to verify strategy mode configuration refactoring.

This test validates that the strategy_mode field exists and can be accessed
without requiring heavy dependencies like pandas.
"""

import os
import sys
from pathlib import Path

def test_strategy_mode_field():
    """Test that TradingConfig has strategy_mode field."""
    print("🧪 Testing TradingConfig Strategy Mode Field")
    print("=" * 50)
    
    try:
        # Add src to path
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))
        
        # Import the dataclass directly to check field existence
        from src.models.config_models import TradingConfig
        
        # Check if strategy_mode field exists in the dataclass
        import dataclasses
        fields = dataclasses.fields(TradingConfig)
        field_names = [f.name for f in fields]
        
        if 'strategy_mode' in field_names:
            print("   ✅ strategy_mode field exists in TradingConfig")
            
            # Find the field and check its default value
            strategy_field = next(f for f in fields if f.name == 'strategy_mode')
            if strategy_field.default == 'enhanced_ema':
                print("   ✅ strategy_mode has correct default value: 'enhanced_ema'")
                return True
            else:
                print(f"   ❌ strategy_mode has wrong default: {strategy_field.default}")
                return False
        else:
            print("   ❌ strategy_mode field missing from TradingConfig")
            print(f"   Available fields: {field_names}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_source_code_changes():
    """Test that source code has been properly updated."""
    print("\n🔍 Testing Source Code Changes")
    print("=" * 35)
    
    try:
        # Test config_models.py
        config_path = Path(__file__).parent / "src" / "models" / "config_models.py"
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        if 'strategy_mode: str = "enhanced_ema"' in config_content:
            print("   ✅ config_models.py: strategy_mode field added")
        else:
            print("   ❌ config_models.py: strategy_mode field missing")
            return False
        
        if 'strategy_mode=get_env("STRATEGY_MODE", "enhanced_ema").lower()' in config_content:
            print("   ✅ config_models.py: from_env() loads STRATEGY_MODE")
        else:
            print("   ❌ config_models.py: from_env() missing STRATEGY_MODE loading")
            return False
        
        # Test trading_bot.py
        bot_path = Path(__file__).parent / "src" / "trading_bot.py"
        with open(bot_path, 'r') as f:
            bot_content = f.read()
        
        if 'strategy_mode = self.config.strategy_mode' in bot_content:
            print("   ✅ trading_bot.py: uses self.config.strategy_mode")
        else:
            print("   ❌ trading_bot.py: missing self.config.strategy_mode usage")
            return False
        
        if "os.getenv('STRATEGY_MODE'" not in bot_content:
            print("   ✅ trading_bot.py: no direct os.getenv('STRATEGY_MODE') calls")
            return True
        else:
            print("   ❌ trading_bot.py: still has direct os.getenv('STRATEGY_MODE') calls")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR reading source files: {e}")
        return False

def main():
    """Run all tests."""
    print("🔧 Simple Strategy Mode Configuration Test")
    print("=" * 50)
    print("Testing basic functionality without heavy dependencies.")
    print("=" * 50)
    
    all_passed = True
    
    # Test 1: Field exists
    if not test_strategy_mode_field():
        all_passed = False
    
    # Test 2: Source code changes
    if not test_source_code_changes():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("🎯 Strategy mode successfully moved to config:")
        print("   • strategy_mode field added to TradingConfig")
        print("   • STRATEGY_MODE env var loaded in from_env()")  
        print("   • TradingBot uses config.strategy_mode")
        print("   • No direct os.getenv() calls remaining")
        print("\nConfiguration is now centralized in TradingConfig! 🎉")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🚨 Please check the implementation.")
    
    print("=" * 50)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())