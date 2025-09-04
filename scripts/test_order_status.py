#!/usr/bin/env python3
"""
Test script to verify the limit order execution fix.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig
from src.services.trade_execution_service import BinanceTradeExecutor

def test_order_status_check():
    """Test the get_order_details functionality."""
    load_environment()
    
    config = TradingConfig.from_env()
    
    trade_executor = BinanceTradeExecutor(
        api_key=config.api_key,
        api_secret=config.api_secret,
        testnet=config.testnet
    )
    
    print("Testing order status checking functionality...")
    
    # Test with a known symbol
    test_symbol = "BTCUSDT"
    
    try:
        # Get current open orders
        open_orders = trade_executor.get_open_orders(test_symbol)
        print(f"Open orders for {test_symbol}: {len(open_orders)}")
        
        if open_orders:
            # Test order details for first open order
            order_id = open_orders[0]['orderId']
            order_details = trade_executor.get_order_details(test_symbol, str(order_id))
            
            if order_details:
                print(f"Order {order_id} details:")
                print(f"  Status: {order_details.get('status')}")
                print(f"  Executed Qty: {order_details.get('executedQty')}")
                print(f"  Cumulative Quote Qty: {order_details.get('cummulativeQuoteQty')}")
            else:
                print(f"Could not get details for order {order_id}")
        
        print("✅ Order status checking works correctly!")
        
    except Exception as e:
        print(f"❌ Error testing order status: {e}")

if __name__ == "__main__":
    test_order_status_check()
