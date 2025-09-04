#!/usr/bin/env python3
"""
Check open orders to see if any assets are locked in other orders
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
    
    print("📋 Checking open orders...")
    
    try:
        # Get all open orders
        open_orders = client.get_open_orders()
        
        if not open_orders:
            print("✅ No open orders found")
            return
        
        print(f"📊 Found {len(open_orders)} open orders:")
        print()
        
        # Group orders by symbol
        orders_by_symbol = {}
        for order in open_orders:
            symbol = order['symbol']
            if symbol not in orders_by_symbol:
                orders_by_symbol[symbol] = []
            orders_by_symbol[symbol].append(order)
        
        for symbol, orders in orders_by_symbol.items():
            print(f"🔸 {symbol}:")
            for order in orders:
                order_id = order['orderId']
                side = order['side']
                order_type = order['type']
                qty = float(order['origQty'])
                executed_qty = float(order['executedQty'])
                price = order.get('price', 'N/A')
                stop_price = order.get('stopPrice', 'N/A')
                status = order['status']
                
                print(f"   📋 Order {order_id}: {side} {qty:.8f} {symbol.replace('USDT', '')} | Type: {order_type} | Status: {status}")
                if price != 'N/A':
                    print(f"      💰 Price: {price}")
                if stop_price != 'N/A':
                    print(f"      🛑 Stop Price: {stop_price}")
                print()
        
        # Check specific symbols from active_trades
        check_symbols = ['GNOUSDT', 'PUNDIXUSDT', 'MKRUSDT']
        
        print("🔍 Checking specific symbols from active_trades.txt...")
        for symbol in check_symbols:
            if symbol in orders_by_symbol:
                print(f"⚠️  {symbol}: Has {len(orders_by_symbol[symbol])} open orders")
            else:
                print(f"✅ {symbol}: No open orders")
        
    except Exception as e:
        print(f"❌ Error checking open orders: {e}")

if __name__ == "__main__":
    main()
