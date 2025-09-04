#!/usr/bin/env python3
"""
Script to retry placing OCO orders for positions that are missing them.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.position_management_service import PositionManagementService
from src.services.trade_execution_service import BinanceTradeExecutor
from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig
from src.models.trade_models import Position
import json

def retry_missing_oco_orders():
    """Retry placing OCO orders for positions that don't have them."""
    print("🔄 Retrying OCO orders for positions missing them...")
    
    # Load environment and config
    load_environment()
    config = TradingConfig.from_env()
    
    # Initialize services
    position_manager = PositionManagementService(config.active_trades_file)
    trade_executor = BinanceTradeExecutor(config.api_key, config.api_secret, config.testnet)
    
    # Get all active positions
    positions = position_manager.get_positions()
    
    if not positions:
        print("ℹ️  No active positions found.")
        return
    
    print(f"📋 Found {len(positions)} active positions")
    
    # Find positions without OCO orders
    positions_without_oco = []
    for position in positions:
        if not position.oco_order_id:
            positions_without_oco.append(position)
            print(f"   ❌ {position.symbol}: Missing OCO order")
        else:
            print(f"   ✅ {position.symbol}: Has OCO order {position.oco_order_id}")
    
    if not positions_without_oco:
        print("🎉 All positions already have OCO orders!")
        return
    
    print(f"\n🔧 Attempting to place OCO orders for {len(positions_without_oco)} positions...")
    
    success_count = 0
    failed_count = 0
    
    for position in positions_without_oco:
        print(f"\n📍 Processing {position.symbol}...")
        print(f"   Quantity: {position.quantity}")
        print(f"   Stop Loss: ${position.stop_loss:.4f}")
        print(f"   Take Profit: ${position.take_profit:.4f}")
        
        try:
            # Attempt to place OCO order
            print(f"   🔄 Placing OCO order...")
            
            oco_result = trade_executor.execute_oco_order(
                symbol=position.symbol,
                quantity=position.quantity,
                stop_price=position.stop_loss,
                limit_price=position.take_profit
            )
            
            if oco_result.success:
                print(f"   ✅ OCO order placed successfully!")
                print(f"   📋 OCO Order ID: {oco_result.order_id}")
                
                # Update position with OCO order ID
                position.oco_order_id = oco_result.order_id
                position_manager.update_position_data(position.symbol, position)
                
                print(f"   💾 Position updated with OCO order ID")
                success_count += 1
            else:
                print(f"   ❌ Failed to place OCO order: {oco_result.error_message}")
                failed_count += 1
                
                # Check if it's an insufficient balance error
                if "insufficient balance" in str(oco_result.error_message).lower():
                    print(f"   ⚠️  This might be due to insufficient balance in the account")
                    print(f"   💡 Suggestion: Check if you have {position.quantity} {position.symbol.replace('USDT', '')} available")
        
        except Exception as e:
            print(f"   ❌ Error processing {position.symbol}: {e}")
            failed_count += 1
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   ✅ Successfully placed OCO orders: {success_count}")
    print(f"   ❌ Failed to place OCO orders: {failed_count}")
    
    if success_count > 0:
        print(f"\n💾 Position data has been updated with new OCO order IDs")
    
    if failed_count > 0:
        print(f"\n⚠️  Some OCO orders failed. Common reasons:")
        print(f"   - Insufficient balance (you don't own enough of the asset)")
        print(f"   - Invalid stop/limit prices (too close to current price)")
        print(f"   - Market conditions (symbol temporarily unavailable)")
        print(f"   - Exchange-specific restrictions")

def check_account_balances():
    """Check account balances for positions that need OCO orders."""
    print("\n💰 Checking account balances...")
    
    # Load environment and config
    load_environment()
    config = TradingConfig.from_env()
    
    # Initialize services
    position_manager = PositionManagementService(config.active_trades_file)
    trade_executor = BinanceTradeExecutor(config.api_key, config.api_secret, config.testnet)
    
    # Get positions without OCO orders
    positions = position_manager.get_positions()
    positions_without_oco = [p for p in positions if not p.oco_order_id]
    
    if not positions_without_oco:
        print("ℹ️  No positions missing OCO orders.")
        return
    
    for position in positions_without_oco:
        asset = position.symbol.replace('USDT', '')
        print(f"\n📍 {position.symbol}:")
        print(f"   Required: {position.quantity} {asset}")
        
        try:
            # Get account info (this would show balances)
            # Note: This is a simplified check - in a real implementation,
            # you'd parse the account response to check specific asset balances
            print(f"   💡 Check your exchange account for {asset} balance")
        except Exception as e:
            print(f"   ❌ Error checking balance: {e}")

if __name__ == "__main__":
    retry_missing_oco_orders()
    
    # Optionally check balances
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--check-balances":
        check_account_balances()
