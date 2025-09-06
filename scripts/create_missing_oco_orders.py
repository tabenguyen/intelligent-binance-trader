#!/usr/bin/env python3
"""
Create Missing OCO Orders
Automatically creates OCO orders for positions that don't have them or have invalid/cancelled ones.
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
    from src.services.trade_execution_service import BinanceTradeExecutor
    from src.services.position_management_service import PositionManagementService
    api_available = True
    print("✅ Trading services loaded successfully")
except ImportError as e:
    print(f"⚠️  Could not load trading services: {e}")
    api_available = False
    exit(1)


def check_and_create_oco_orders():
    """Check all positions and create OCO orders for unprotected ones."""
    
    print("🛡️  Checking and Creating Missing OCO Orders")
    print("=" * 50)
    
    if not api_available or not config:
        print("❌ Cannot create OCO orders without proper configuration")
        return
    
    # Initialize services
    active_trades_file = config.get_mode_specific_active_trades_file()
    position_manager = PositionManagementService(active_trades_file)
    trade_executor = BinanceTradeExecutor(
        api_key=config.api_key,
        api_secret=config.api_secret,
        testnet=config.testnet
    )
    
    positions = position_manager.get_positions()
    
    if not positions:
        print("📄 No active positions found")
        return
    
    print(f"📊 Found {len(positions)} active positions")
    
    created_orders = 0
    
    for position in positions:
        print(f"\n📊 Checking {position.symbol}:")
        print(f"   Entry: ${position.entry_price:.6f}")
        print(f"   Quantity: {position.quantity}")
        print(f"   Stop Loss: ${position.stop_loss:.6f}")
        print(f"   Take Profit: ${position.take_profit:.6f}")
        
        needs_oco = False
        
        # Check if position has OCO order ID
        if not position.oco_order_id:
            print(f"   ⚠️  No OCO order ID - needs protection")
            needs_oco = True
        else:
            # Check if OCO order is still valid
            print(f"   🔍 Checking OCO order {position.oco_order_id}...")
            oco_status = trade_executor.get_oco_order_status(position.symbol, position.oco_order_id)
            
            if oco_status == "EXECUTING":
                print(f"   ✅ OCO order is active and executing")
                continue
            elif oco_status in ["ALL_DONE", "REJECT", None]:
                print(f"   ❌ OCO order is invalid/completed (status: {oco_status}) - needs new protection")
                needs_oco = True
            else:
                print(f"   ⚠️  Unknown OCO status: {oco_status} - assuming needs protection")
                needs_oco = True
        
        if needs_oco:
            print(f"   🛡️  Creating OCO order...")
            
            try:
                # Execute OCO order with enhanced retry logic
                result = trade_executor.execute_oco_order(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    stop_price=position.stop_loss,
                    limit_price=position.take_profit
                )
                
                if result.success and result.order_id:
                    print(f"   ✅ OCO order created successfully!")
                    print(f"   📋 OCO Order ID: {result.order_id}")
                    
                    # Update position with new OCO order ID
                    position.oco_order_id = result.order_id
                    position_manager.update_position_oco_id(position.symbol, result.order_id)
                    
                    created_orders += 1
                    
                    print(f"   💾 Position updated with OCO ID")
                    
                else:
                    print(f"   ❌ Failed to create OCO order: {result.error}")
                    if result.retry_info:
                        print(f"   🔄 Retry attempts: {result.retry_info}")
                        
            except Exception as e:
                print(f"   ❌ Error creating OCO order: {e}")
                continue
    
    print(f"\n📊 SUMMARY:")
    print(f"=" * 40)
    print(f"🛡️  Created {created_orders} new OCO orders")
    
    if created_orders > 0:
        print(f"✅ All positions are now protected with OCO orders!")
        print(f"\n🚀 WHAT'S NEXT:")
        print(f"1. 📊 Check status: python scripts/check_oco_status.py")
        print(f"2. 🤖 Monitor: python main.py")
        print(f"3. 🔄 Enhanced retry logic will handle any balance issues")
    else:
        print(f"📄 No new OCO orders needed - all positions already protected")


if __name__ == "__main__":
    try:
        check_and_create_oco_orders()
    except KeyboardInterrupt:
        print(f"\n❌ Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
