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
    
    # Initialize services
    position_manager = PositionManagementService(config.active_trades_file)
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
                order_status = trade_executor.get_order_status(position.symbol, position.oco_order_id)
                print(f"   OCO Status: {order_status}")
                
                if order_status == "CANCELED":
                    print(f"   ⚠️  OCO order was cancelled - position has no exit protection!")
                    
                    response = input(f"   Remove {position.symbol} position? (y/N): ")
                    if response.lower() == 'y':
                        trade = position_manager.close_position(position.symbol, position.current_price)
                        print(f"   ✅ Position removed: P&L ${trade.pnl:.2f}")
                    else:
                        print(f"   ⏭️  Keeping position")
                        
                elif order_status in ["FILLED", "PARTIALLY_FILLED"]:
                    print(f"   ✅ OCO order was executed - removing position record")
                    trade = position_manager.close_position(position.symbol, position.current_price)
                    print(f"   ✅ Position cleaned up: P&L ${trade.pnl:.2f}")
                    
                elif order_status in ["NEW", "PARTIALLY_FILLED"]:
                    print(f"   ✅ OCO order is still active")
                    
            except Exception as e:
                print(f"   ❌ Error checking OCO status: {e}")
        else:
            print(f"   ⚠️  No OCO order ID - position has no automated exit protection")
            
        print()

if __name__ == "__main__":
    main()
