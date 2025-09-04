#!/usr/bin/env python3
"""
Script to clean up legacy positions that have no OCO order protection.
This handles the case where OCO orders were cancelled externally but positions still tracked.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig
from src.services.position_management_service import PositionManagementService
from src.services.trade_execution_service import BinanceTradeExecutor

def main():
    """Clean up legacy positions without OCO protection."""
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
    
    print(f"Found {len(positions)} active positions. Checking for exit protection...\n")
    
    positions_to_remove = []
    
    for position in positions:
        print(f"📊 {position.symbol} (Entry: ${position.entry_price:.4f}, Current: ${position.current_price:.4f})")
        
        has_protection = False
        
        # Check if position has OCO order ID
        if position.oco_order_id:
            try:
                order_status = trade_executor.get_order_status(position.symbol, position.oco_order_id)
                if order_status in ["NEW", "PARTIALLY_FILLED"]:
                    print(f"   ✅ Has active OCO order (ID: {position.oco_order_id})")
                    has_protection = True
                elif order_status == "CANCELED":
                    print(f"   ❌ OCO order {position.oco_order_id} was cancelled")
                elif order_status in ["FILLED"]:
                    print(f"   ✅ OCO order {position.oco_order_id} was executed")
                    positions_to_remove.append((position, "OCO Executed"))
                    continue
            except Exception as e:
                print(f"   ⚠️  Could not check OCO order status: {e}")
        
        # Check for any open OCO orders for this symbol
        if not has_protection:
            try:
                open_orders = trade_executor.get_open_orders(position.symbol)
                oco_orders = [order for order in open_orders if order.get('type') == 'OCO']
                
                if oco_orders:
                    print(f"   ✅ Has {len(oco_orders)} open OCO order(s)")
                    has_protection = True
                else:
                    print(f"   ❌ No OCO orders found - no exit protection!")
                    
            except Exception as e:
                print(f"   ⚠️  Could not check open orders: {e}")
        
        # If no protection found, mark for potential removal
        if not has_protection:
            unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
            pnl_percent = ((position.current_price - position.entry_price) / position.entry_price) * 100
            
            print(f"   💰 Unrealized P&L: ${unrealized_pnl:.2f} ({pnl_percent:+.2f}%)")
            positions_to_remove.append((position, "No Exit Protection"))
    
    print(f"\n" + "="*50)
    
    if positions_to_remove:
        print(f"Found {len(positions_to_remove)} positions that need attention:")
        
        for position, reason in positions_to_remove:
            print(f"\n📊 {position.symbol} - {reason}")
            print(f"   Entry: ${position.entry_price:.4f} → Current: ${position.current_price:.4f}")
            
            unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
            pnl_percent = ((position.current_price - position.entry_price) / position.entry_price) * 100
            print(f"   P&L: ${unrealized_pnl:.2f} ({pnl_percent:+.2f}%)")
            
            if reason == "OCO Executed":
                print("   ✅ This position should be automatically cleaned up")
                trade = position_manager.close_position(position.symbol, position.current_price)
                print(f"   ✅ Position removed: P&L ${trade.pnl:.2f}")
            else:
                response = input(f"   Remove {position.symbol} position? (y/N): ")
                if response.lower() == 'y':
                    trade = position_manager.close_position(position.symbol, position.current_price)
                    print(f"   ✅ Position removed: P&L ${trade.pnl:.2f}")
                else:
                    print(f"   ⏭️  Keeping position - consider adding manual exit orders")
    else:
        print("✅ All positions have proper exit protection!")

if __name__ == "__main__":
    main()
