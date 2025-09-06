#!/usr/bin/env python3
"""
Script to check OCO order status for all active positions and clean up cancelled orders.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig
from src.services.position_management_service import PositionManagementService
from src.services.trade_execution_service import BinanceTradeExecutor

def main():
    """Check OCO status for all active positions."""
    load_environment()
    
    # Load configuration
    config = TradingConfig.from_env()
    
    # Initialize services with mode-specific file
    active_trades_file = config.get_mode_specific_active_trades_file()
    position_manager = PositionManagementService(active_trades_file)
    trade_executor = BinanceTradeExecutor(
        api_key=config.api_key,
        api_secret=config.api_secret,
        testnet=config.testnet
    )
    
    positions = position_manager.get_positions()
    
    if not positions:
        print("No active positions found.")
        return
    
    print(f"Checking {len(positions)} active positions for OCO order status...\n")
    
    for position in positions:
        print(f"📊 {position.symbol}:")
        print(f"   Entry: ${position.entry_price:.4f}")
        print(f"   Current: ${position.current_price:.4f}")
        print(f"   Quantity: {position.quantity}")
        
        if position.oco_order_id:
            print(f"   OCO Order ID: {position.oco_order_id}")
            
            try:
                order_status = trade_executor.get_oco_order_status(position.symbol, position.oco_order_id)
                print(f"   OCO Status: {order_status}")
                
                if order_status == "ALL_DONE":
                    print(f"   ✅ OCO order completed - removing from active trades")
                    position_manager.remove_position(position.symbol)
                elif order_status == "REJECT":
                    print(f"   ❌ OCO order rejected - removing from active trades")
                    position_manager.remove_position(position.symbol)
                elif order_status in ["EXECUTING", "EXEC_STARTED"]:
                    print(f"   🔄 OCO order is active and executing")
                else:
                    print(f"   ⚠️  Unknown OCO status: {order_status}")
            except Exception as e:
                print(f"   ❌ Error checking OCO status: {e}")
        else:
            print(f"   ⚠️  No OCO order ID - position has no automated exit protection")
            
        print()

if __name__ == "__main__":
    main()
