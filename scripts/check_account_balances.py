#!/usr/bin/env python3
"""
Quick Account Balance Check
Shows current Binance account balances to verify API connection.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from binance.spot import Spot as Client
from binance.error import ClientError

# Try to load environment
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
try:
    from src.utils.env_loader import load_environment
    load_environment()  # Ensure environment is loaded
    use_env_loader = True
except ImportError:
    use_env_loader = False


def check_account_balances():
    """Check current account balances."""
    
    # Load environment first
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    try:
        from utils.env_loader import load_environment, get_env
        load_environment()
        print("✅ Environment loader imported and loaded successfully")
        
        api_key = get_env('BINANCE_API_KEY')
        api_secret = get_env('BINANCE_API_SECRET')
        
        print(f"🔑 API Key present: {bool(api_key)}")
        print(f"🔑 API Secret present: {bool(api_secret)}")
        
    except Exception as e:
        print(f"❌ Error loading environment: {e}")
        print("Falling back to os.getenv...")
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Missing API credentials!")
        print("Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
        print("\nExample:")
        print("export BINANCE_API_KEY='your_api_key'")
        print("export BINANCE_API_SECRET='your_secret_key'")
        return
    
    try:
        # Initialize live client
        client = Client(api_key=api_key, api_secret=api_secret)
        
        print("🔍 Checking LIVE account balances...")
        print("=" * 50)
        
        # Get account info
        account_info = client.account()
        
        # Filter and display meaningful balances
        meaningful_balances = []
        
        for balance in account_info['balances']:
            asset = balance['asset']
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            total_balance = free_balance + locked_balance
            
            # Only show assets with meaningful balances
            if total_balance > 0.001:
                meaningful_balances.append({
                    'asset': asset,
                    'free': free_balance,
                    'locked': locked_balance,
                    'total': total_balance
                })
        
        # Sort by total balance (descending)
        meaningful_balances.sort(key=lambda x: x['total'], reverse=True)
        
        print(f"💰 Account Balances ({len(meaningful_balances)} assets):")
        print(f"{'Asset':<8} {'Total':<15} {'Free':<15} {'Locked':<15}")
        print("-" * 65)
        
        for balance in meaningful_balances:
            print(f"{balance['asset']:<8} {balance['total']:<15.6f} {balance['free']:<15.6f} {balance['locked']:<15.6f}")
        
        # Identify tradeable assets (excluding stablecoins)
        excluded_assets = {'USDT', 'BUSD', 'USDC', 'DAI', 'TUSD', 'PAX', 'USDS', 'BNB'}
        tradeable_assets = []
        
        for balance in meaningful_balances:
            if (balance['asset'] not in excluded_assets and 
                balance['total'] >= 1.0):  # Minimum meaningful balance
                tradeable_assets.append(balance['asset'])
        
        print(f"\n🎯 Tradeable Assets (>= 1.0 balance): {', '.join(tradeable_assets) if tradeable_assets else 'None'}")
        
        # Show comparison with current active trades file
        trades_file = Path("data/active_trades_live.json")
        if trades_file.exists():
            try:
                import json
                with open(trades_file, 'r') as f:
                    content = f.read().strip()
                    if content and not content.startswith('2025-'):
                        current_trades = json.loads(content)
                        
                        print(f"\n📄 Current Active Trades File:")
                        if current_trades:
                            for symbol, trade_data in current_trades.items():
                                base_asset = symbol.replace('USDT', '')
                                print(f"   {symbol}: {trade_data['quantity']} {base_asset}")
                        else:
                            print("   (Empty)")
                        
                        # Show sync recommendations
                        print(f"\n💡 Sync Recommendations:")
                        
                        # Assets in account but not in trades file
                        recorded_assets = {symbol.replace('USDT', '') for symbol in current_trades.keys()}
                        missing_in_file = set(tradeable_assets) - recorded_assets
                        if missing_in_file:
                            print(f"   🆕 Add to trades file: {', '.join(missing_in_file)}")
                        
                        # Assets in trades file but not in account
                        missing_in_account = recorded_assets - set(tradeable_assets)
                        if missing_in_account:
                            print(f"   🗑️  Remove from trades file: {', '.join(missing_in_account)}")
                        
                        if not missing_in_file and not missing_in_account:
                            print(f"   ✅ Account and trades file are in sync!")
                    else:
                        print(f"\n📄 Active trades file contains logs, not trade data")
            except Exception as e:
                print(f"\n⚠️  Could not read active trades file: {e}")
        else:
            print(f"\n📄 No active trades file found")
        
        print(f"\n✅ Account check complete!")
        
    except ClientError as e:
        print(f"❌ Binance API Error: {e}")
        if "Invalid API-key" in str(e):
            print("💡 Check your API key and secret")
        elif "Signature" in str(e):
            print("💡 Check your API secret")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_account_balances()
