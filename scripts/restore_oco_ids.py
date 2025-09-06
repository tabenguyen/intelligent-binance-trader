#!/usr/bin/env python3
"""
Restore OCO Order IDs to active trades file by mapping existing open orders.
"""

import json
import sys
from pathlib import Path

# Add src to path  
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from src.utils import load_config
    config = load_config()
    print("✅ Config loaded successfully")
except ImportError as e:
    print(f"⚠️  Could not load config: {e}")
    config = None
    exit(1)

try:
    from binance.spot import Spot as Client
    from binance.error import ClientError
    api_available = True
    print("✅ Binance API loaded successfully")
except ImportError as e:
    print(f"⚠️  Could not load Binance API: {e}")
    api_available = False
    exit(1)


def get_open_orders(symbol):
    """Get current open orders for a symbol."""
    if not api_available or not config:
        return []
        
    try:
        if config.testnet:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret,
                base_url="https://testnet.binance.vision"
            )
        else:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
        
        # Get current open orders only
        orders = client.get_open_orders(symbol=symbol)
        return orders
        
    except Exception as e:
        print(f"❌ Error getting open orders for {symbol}: {e}")
        return []


def find_current_oco_order_id(orders):
    """Find current OCO order ID from open orders."""
    for order in orders:
        if order.get('orderListId') and order.get('orderListId') != -1:
            # This is an active OCO order
            if order['status'] in ['NEW', 'PARTIALLY_FILLED']:
                return order['orderListId']
    return None


def restore_oco_ids():
    """Restore OCO order IDs to active trades file."""
    
    print("🔄 Restoring OCO Order IDs to Active Trades")
    print("=" * 50)
    
    trades_file = Path("data/active_trades_live.json")
    
    if not trades_file.exists():
        print("❌ Active trades file not found")
        return
    
    # Load current trades
    try:
        with open(trades_file, 'r') as f:
            trades = json.load(f)
    except Exception as e:
        print(f"❌ Error reading trades file: {e}")
        return
    
    print(f"📄 Found {len(trades)} active trades")
    
    updated_trades = {}
    changes_made = False
    
    for symbol, trade in trades.items():
        print(f"\n📊 Checking {symbol}...")
        
        # Get current open orders for this symbol
        orders = get_open_orders(symbol)
        
        if not orders:
            print(f"   ❌ No open orders found")
            updated_trades[symbol] = trade
            continue
        
        # Find current OCO order ID
        oco_id = find_current_oco_order_id(orders)
        
        if oco_id:
            print(f"   ✅ Found OCO Order ID: {oco_id}")
            trade_copy = trade.copy()
            trade_copy['oco_order_id'] = oco_id
            updated_trades[symbol] = trade_copy
            
            if trade.get('oco_order_id') != oco_id:
                changes_made = True
                print(f"   🔄 Updated OCO ID: {trade.get('oco_order_id')} → {oco_id}")
        else:
            print(f"   ⚠️  No active OCO orders found")
            updated_trades[symbol] = trade
    
    if changes_made:
        # Create backup
        backup_file = trades_file.with_suffix('.json.backup_oco')
        import shutil
        shutil.copy2(trades_file, backup_file)
        print(f"\n📄 Backup created: {backup_file}")
        
        # Save updated trades
        with open(trades_file, 'w') as f:
            json.dump(updated_trades, f, indent=2)
        
        print(f"✅ OCO Order IDs restored successfully!")
        print(f"📁 File updated: {trades_file}")
    else:
        print(f"\n📄 No changes needed - OCO IDs already correct")


if __name__ == "__main__":
    try:
        restore_oco_ids()
    except KeyboardInterrupt:
        print(f"\n❌ Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
