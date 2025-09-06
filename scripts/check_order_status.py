#!/usr/bin/env python3
"""
Check the actual status of OCO orders and open orders for debugging.
"""

import os
import sys
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils.env_loader import load_environment
from binance.spot import Spot as Client
from binance.error import ClientError

def main():
    # Load environment
    env = load_environment()
    
    # Initialize client (using testnet as per config)
    client = Client(
        api_key=env.binance_api_key,
        api_secret=env.binance_api_secret,
        base_url="https://testnet.binance.vision"
    )
    
    # Load active trades
    with open("data/active_trades.json", "r") as f:
        trades = json.load(f)
    
    print("🔍 Checking order statuses for active positions...")
    print("=" * 60)
    
    for symbol, trade in trades.items():
        print(f"\n📊 {symbol}")
        print(f"   Position: {trade['quantity']} @ ${trade['entry_price']:.4f}")
        
        oco_order_id = trade.get('oco_order_id')
        if oco_order_id:
            print(f"   OCO Order ID: {oco_order_id}")
            
            # Try to get order status
            try:
                order = client.get_order(symbol=symbol, orderId=int(oco_order_id))
                print(f"   ✅ Order Status: {order.get('status', 'UNKNOWN')}")
                print(f"   📅 Order Time: {order.get('time')}")
                print(f"   💰 Original Qty: {order.get('origQty', 'N/A')}")
                print(f"   ⚡ Executed Qty: {order.get('executedQty', 'N/A')}")
            except ClientError as e:
                print(f"   ❌ Order Check Failed: {e}")
                if e.error_code == -2013:
                    print(f"   🗑️  Order does not exist (likely executed or cancelled)")
        
        # Check for any open orders on this symbol
        try:
            open_orders = client.get_open_orders(symbol=symbol)
            if open_orders:
                print(f"   📋 Open Orders: {len(open_orders)}")
                for order in open_orders:
                    print(f"      ID: {order['orderId']} | Type: {order['type']} | Status: {order['status']}")
            else:
                print(f"   📋 Open Orders: None")
        except ClientError as e:
            print(f"   ❌ Open Orders Check Failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Order status check complete")

if __name__ == "__main__":
    main()
