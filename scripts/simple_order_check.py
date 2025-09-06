#!/usr/bin/env python3
"""
Simple order status check using the same approach as the trading bot.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import the trading bot components
from utils.env_loader import load_environment
from services.trade_execution_service import BinanceTradeExecutor

def main():
    try:
        # Load environment the same way the trading bot does
        env = load_environment()
        
        # Initialize trade executor (testnet=True as per bot config)
        trade_executor = BinanceTradeExecutor(
            api_key=env.binance_api_key,
            api_secret=env.binance_api_secret,
            testnet=True  # Same as the bot configuration
        )
        
        # Load active trades
        trades_file = project_root / "data" / "active_trades.json"
        with open(trades_file, "r") as f:
            trades = json.load(f)
        
        print("🔍 Checking order statuses for active positions...")
        print("=" * 60)
        
        for symbol, trade in trades.items():
            print(f"\n📊 {symbol}")
            print(f"   Position: {trade['quantity']} @ ${trade['entry_price']:.4f}")
            
            oco_order_id = trade.get('oco_order_id')
            if oco_order_id:
                print(f"   OCO Order ID: {oco_order_id}")
                
                # Use the same method the trading bot uses
                order_status = trade_executor.get_order_status(symbol, str(oco_order_id))
                
                if order_status is None:
                    print(f"   ❌ Order status check failed (order likely doesn't exist)")
                    print(f"   🗑️  This is the same error the trading bot is experiencing")
                    
                    # Check for any open orders on this symbol
                    open_orders = trade_executor.get_open_orders(symbol)
                    if open_orders:
                        print(f"   📋 Found {len(open_orders)} open orders:")
                        for order in open_orders:
                            print(f"      ID: {order['orderId']} | Type: {order['type']} | Status: {order['status']}")
                    else:
                        print(f"   📋 No open orders found for {symbol}")
                        
                else:
                    print(f"   ✅ Order Status: {order_status}")
        
        print("\n" + "=" * 60)
        print("💡 SOLUTION:")
        print("The order 13636395733 no longer exists on Binance.")
        print("This usually means it was:")
        print("  1. ✅ Executed (stop loss or take profit triggered)")
        print("  2. ❌ Cancelled manually or by system")
        print("  3. 🕒 Expired (if it had a time limit)")
        print("\nThe trading bot should detect this and clean up the position record.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
