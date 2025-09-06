#!/usr/bin/env python3
"""
Emergency OCO placement script for BIOUSDT position.
This script will check the current balance and place appropriate OCO orders.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from binance.spot import Spot as Client
from binance.error import ClientError


def main():
    """Place OCO order for unprotected BIOUSDT position."""
    
    # Get API credentials from environment
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Missing API credentials. Please set BINANCE_API_KEY and BINANCE_API_SECRET")
        return
    
    # Initialize client (LIVE mode based on the logs)
    client = Client(api_key=api_key, api_secret=api_secret)
    
    symbol = "BIOUSDT"
    base_asset = "BIO"
    
    print(f"🔍 Checking {symbol} position and placing OCO order...")
    
    try:
        # Check current balance
        account = client.account()
        bio_balance = 0.0
        
        for balance in account['balances']:
            if balance['asset'] == base_asset:
                bio_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                print(f"💰 Current {base_asset} Balance:")
                print(f"   Available: {bio_balance}")
                print(f"   Locked: {locked_balance}")
                break
        
        if bio_balance <= 0:
            print(f"❌ No {base_asset} balance available")
            return
        
        # Check active trades file for position details
        trades_file = Path("data/active_trades_live.json")
        position_found = False
        
        if trades_file.exists():
            try:
                with open(trades_file, 'r') as f:
                    content = f.read().strip()
                    if content and not content.startswith('2025-'):  # Check if it's JSON, not logs
                        trades_data = json.loads(content)
                        if symbol in trades_data:
                            position = trades_data[symbol]
                            entry_price = float(position['entry_price'])
                            print(f"📊 Found position data:")
                            print(f"   Entry Price: ${entry_price:.6f}")
                            print(f"   Position Quantity: {position['quantity']}")
                            position_found = True
            except (json.JSONDecodeError, KeyError):
                print("⚠️  Could not parse position data from active trades file")
        
        if not position_found:
            print("⚠️  No position data found, using current market price as reference")
            # Get current market price
            ticker = client.ticker_24hr(symbol=symbol)
            entry_price = float(ticker['lastPrice'])
            print(f"📊 Current market price: ${entry_price:.6f}")
        
        # Calculate stop loss and take profit (5% stop loss, 11% take profit based on logs)
        stop_loss = entry_price * 0.95  # 5% below entry
        take_profit = entry_price * 1.11  # 11% above entry
        
        # Adjust quantity to available balance with safety buffer
        safety_buffer = max(0.001, bio_balance * 0.001)  # 0.1% buffer
        oco_quantity = bio_balance - safety_buffer
        
        # Round quantity to proper precision (no decimals for BIO)
        oco_quantity = int(oco_quantity)
        
        if oco_quantity <= 0:
            print(f"❌ Quantity too small after adjustment: {oco_quantity}")
            return
        
        # Round prices to proper precision
        stop_loss = round(stop_loss, 5)
        take_profit = round(take_profit, 5)
        
        print(f"🎯 OCO Order Parameters:")
        print(f"   Quantity: {oco_quantity} {base_asset}")
        print(f"   Stop Loss: ${stop_loss:.5f}")
        print(f"   Take Profit: ${take_profit:.5f}")
        print(f"   Safety Buffer: {safety_buffer:.6f}")
        
        # Confirm before placing order
        response = input("\n🤔 Place OCO order? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return
        
        # Place OCO order
        print(f"🚀 Placing OCO order...")
        
        oco_response = client.new_oco_order(
            symbol=symbol,
            side="SELL",
            quantity=oco_quantity,
            price=take_profit,
            stopPrice=stop_loss,
            stopLimitPrice=stop_loss,
            stopLimitTimeInForce="GTC"
        )
        
        order_list_id = oco_response.get('orderListId')
        print(f"✅ OCO order placed successfully!")
        print(f"   Order List ID: {order_list_id}")
        print(f"   Quantity: {oco_quantity} {base_asset}")
        print(f"   Stop Loss: ${stop_loss:.5f}")
        print(f"   Take Profit: ${take_profit:.5f}")
        
        # Update active trades file if it exists and is in JSON format
        if trades_file.exists() and position_found:
            try:
                with open(trades_file, 'r') as f:
                    content = f.read().strip()
                    if content and not content.startswith('2025-'):
                        trades_data = json.loads(content)
                        if symbol in trades_data:
                            trades_data[symbol]['oco_order_id'] = str(order_list_id)
                            with open(trades_file, 'w') as f:
                                json.dump(trades_data, f, indent=2)
                            print(f"📝 Updated active trades file with OCO order ID")
            except Exception as e:
                print(f"⚠️  Could not update active trades file: {e}")
        
        print(f"\n🎉 BIOUSDT position is now protected!")
        print(f"💡 You can monitor the order in Binance or check order status with:")
        print(f"   Order List ID: {order_list_id}")
        
    except ClientError as e:
        print(f"❌ Binance API Error: {e}")
        if e.error_code == -2010:
            print(f"💡 Insufficient balance. Current available: {bio_balance}")
            print(f"💡 Try reducing quantity or wait for balance to update")
        elif e.error_code == -1013:
            print(f"💡 Filter failure. Check price/quantity precision")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
