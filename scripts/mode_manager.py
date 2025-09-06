#!/usr/bin/env python3
"""
Trading Mode Manager - Utility to manage testnet/live mode configurations
"""

import os
import sys
from pathlib import Path

def show_current_config():
    """Show current trading mode configuration."""
    testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'
    mode = "TESTNET" if testnet else "LIVE"
    
    print(f"🔧 Current Trading Mode: {mode}")
    print("=" * 50)
    
    if testnet:
        print("📁 Testnet Mode Files:")
        print("   Watchlist: config/watchlist_testnet.txt")
        print("   Active Trades: data/active_trades_testnet.json")
        print("   Logs: logs/output_testnet.log")
    else:
        print("📁 Live Mode Files:")
        print("   Watchlist: config/watchlist_live.txt")
        print("   Active Trades: data/active_trades_live.json")
        print("   Logs: logs/output_live.log")
    
    print(f"\n📊 Environment Configuration:")
    print(f"   USE_TESTNET={os.getenv('USE_TESTNET', 'true')}")
    print(f"   BINANCE_API_KEY={'SET' if os.getenv('BINANCE_API_KEY') else 'NOT SET'}")
    print(f"   BINANCE_API_SECRET={'SET' if os.getenv('BINANCE_API_SECRET') else 'NOT SET'}")
    
    # Check if mode-specific files exist
    print(f"\n📂 File Status:")
    files_to_check = [
        ("config/watchlist_testnet.txt", "Testnet Watchlist"),
        ("config/watchlist_live.txt", "Live Watchlist"),
        ("data/active_trades_testnet.json", "Testnet Active Trades"),
        ("data/active_trades_live.json", "Live Active Trades")
    ]
    
    for file_path, description in files_to_check:
        exists = Path(file_path).exists()
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"   {description}: {status}")

def show_help():
    """Show help information."""
    print("🤖 Trading Mode Manager")
    print("=" * 50)
    print("Usage: python3 scripts/mode_manager.py [command]")
    print("\nCommands:")
    print("  status    - Show current mode configuration (default)")
    print("  help      - Show this help message")
    print("\nFile Structure:")
    print("  Testnet Mode:")
    print("    - config/watchlist_testnet.txt")
    print("    - data/active_trades_testnet.json")
    print("    - logs/output_testnet.log")
    print("\n  Live Mode:")
    print("    - config/watchlist_live.txt")
    print("    - data/active_trades_live.json")
    print("    - logs/output_live.log")
    print("\nTo switch modes, update the USE_TESTNET environment variable:")
    print("  Testnet: export USE_TESTNET=true")
    print("  Live:    export USE_TESTNET=false")

def main():
    """Main entry point."""
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if command == "help":
        show_help()
    elif command == "status":
        show_current_config()
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
