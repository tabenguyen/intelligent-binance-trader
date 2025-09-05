#!/usr/bin/env python3
"""
Check account balances to verify available assets
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig
from binance.client import Client
import json

def main():
    # Load environment variables and config
    load_environment()
    config = TradingConfig.from_env()
    
    # Initialize Binance client
    client = Client(config.api_key, config.api_secret)
    
    print("💰 Checking account balances...")
    
    try:
        # Get account info
        account_info = client.get_account()
        balances = account_info['balances']
        
        # Filter balances with assets > 0
        non_zero_balances = []
        for balance in balances:
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                non_zero_balances.append({
                    'asset': balance['asset'],
                    'free': free,
                    'locked': locked,
                    'total': total
                })
        
        # Sort by total balance descending
        non_zero_balances.sort(key=lambda x: x['total'], reverse=True)
        
        print(f"📊 Found {len(non_zero_balances)} assets with non-zero balance:")
        print()
        
        for i, balance in enumerate(non_zero_balances[:20], 1):  # Show top 20
            asset = balance['asset']
            free = balance['free']
            locked = balance['locked']
            total = balance['total']
            
            print(f"{i:2d}. {asset:>8} | Free: {free:>12.8f} | Locked: {locked:>12.8f} | Total: {total:>12.8f}")
        
        if len(non_zero_balances) > 20:
            print(f"... and {len(non_zero_balances) - 20} more assets")
        
        print()
        print("🔍 Checking specific assets from active_trades.json...")
        
        # Check specific assets mentioned in active_trades
        check_assets = ['GNO', 'PUNDIX', 'MKR']
        
        for asset in check_assets:
            found = False
            for balance in non_zero_balances:
                if balance['asset'] == asset:
                    print(f"✅ {asset}: {balance['total']:.8f} available")
                    found = True
                    break
            
            if not found:
                print(f"❌ {asset}: 0.00000000 available")
        
    except Exception as e:
        print(f"❌ Error checking balances: {e}")

if __name__ == "__main__":
    main()
