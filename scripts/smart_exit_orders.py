#!/usr/bin/env python3
"""
Smart OCO order placement that handles positions in loss appropriately
"""
import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig
from src.services.position_management_service import PositionManagementService
from binance.spot import Spot as Client
from binance.error import ClientError
import json

def place_smart_exit_orders(client, position):
    """Place appropriate exit orders based on current market situation"""
    symbol = position.symbol
    quantity = position.quantity
    original_stop_loss = position.stop_loss
    take_profit = position.take_profit
    
    print(f"📍 Processing {position.symbol}...")
    
    try:
        # Get current price
        ticker = client.ticker_price(symbol)
        current_price = float(ticker['price'])
        
        print(f"   💰 Current Price: ${current_price:.6f}")
        print(f"   📊 Entry Price: ${position.entry_price:.6f}")
        
        # Calculate current P&L
        pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
        print(f"   📈 Current P&L: {pnl_pct:.2f}%")
        
        print(f"   🎯 Original Stop Loss: ${original_stop_loss:.6f}")
        print(f"   🎯 Take Profit: ${take_profit:.6f}")
        
        # Determine the best strategy based on current situation
        if current_price > original_stop_loss and current_price < take_profit:
            # Normal case: can place OCO order as planned
            print(f"   ✅ Normal case: Current price between stop loss and take profit")
            return place_oco_order(client, symbol, quantity, original_stop_loss, take_profit)
            
        elif current_price <= original_stop_loss:
            # Price has fallen below original stop loss
            print(f"   ⚠️  Price has fallen below original stop loss")
            print(f"   💡 Options:")
            print(f"      1. Cut losses immediately (market sell)")
            print(f"      2. Set new stop loss below current price")
            print(f"      3. Wait for recovery and place take profit only")
            
            # Option 2: Set new stop loss 2% below current price
            new_stop_loss = current_price * 0.98
            print(f"   🔧 Setting new stop loss 2% below current: ${new_stop_loss:.6f}")
            
            if take_profit > current_price:
                return place_oco_order(client, symbol, quantity, new_stop_loss, take_profit)
            else:
                print(f"   ❌ Take profit ${take_profit:.6f} is also below current price")
                print(f"   💡 Consider manual intervention - position needs review")
                return False
                
        else:
            # Price is above take profit (shouldn't happen often)
            print(f"   🎉 Price is above take profit target!")
            print(f"   💡 Consider taking profit immediately")
            return False
            
    except Exception as e:
        print(f"   ❌ Error analyzing position: {e}")
        return False

def place_oco_order(client, symbol, quantity, stop_loss, take_profit):
    """Place OCO order with proper formatting"""
    try:
        # Get symbol info for formatting
        exchange_info = client.exchange_info()
        symbol_info = None
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                symbol_info = s
                break
        
        if not symbol_info:
            print(f"   ❌ Symbol info not found for {symbol}")
            return False
        
        # Get filters
        filters = {f['filterType']: f for f in symbol_info['filters']}
        
        # Format quantity using LOT_SIZE filter
        lot_size = filters.get('LOT_SIZE', {})
        step_size = float(lot_size.get('stepSize', 0.1))
        min_qty = float(lot_size.get('minQty', 0))
        
        if step_size > 0:
            formatted_qty = math.floor(quantity / step_size) * step_size
        else:
            formatted_qty = quantity
            
        if formatted_qty < min_qty:
            print(f"   ❌ Quantity {formatted_qty} below minimum {min_qty}")
            return False
        
        # Format prices using PRICE_FILTER
        price_filter = filters.get('PRICE_FILTER', {})
        tick_size = float(price_filter.get('tickSize', 0.001))
        
        if tick_size > 0:
            formatted_stop_loss = math.floor(stop_loss / tick_size) * tick_size
            formatted_take_profit = math.floor(take_profit / tick_size) * tick_size
        else:
            formatted_stop_loss = stop_loss
            formatted_take_profit = take_profit
        
        # Format to avoid floating point precision issues
        formatted_qty = float(f"{formatted_qty:.12f}")
        formatted_stop_loss = float(f"{formatted_stop_loss:.12f}")
        formatted_take_profit = float(f"{formatted_take_profit:.12f}")
        
        print(f"   🔧 Placing OCO order:")
        print(f"      Quantity: {formatted_qty}")
        print(f"      Stop Loss: ${formatted_stop_loss}")
        print(f"      Take Profit: ${formatted_take_profit}")
        
        # Place OCO order using the correct method
        order = client.new_oco_order(
            symbol=symbol,
            side='SELL',
            quantity=formatted_qty,
            price=formatted_take_profit,
            stopPrice=formatted_stop_loss,
            stopLimitPrice=formatted_stop_loss,
            stopLimitTimeInForce='GTC'
        )
        
        print(f"   ✅ OCO order placed successfully!")
        print(f"      Order List ID: {order['orderListId']}")
        
        return order['orderListId']
        
    except ClientError as e:
        print(f"   ❌ Binance API Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    print("🧠 Smart exit order placement for underwater positions...")
    
    # Load environment and config
    load_environment()
    config = TradingConfig.from_env()
    
    # Initialize services
    position_manager = PositionManagementService(config.active_trades_file)
    client = Client(config.api_key, config.api_secret)
    
    # Get positions without OCO orders
    positions = position_manager.get_positions()
    positions_without_oco = [pos for pos in positions if pos.oco_order_id is None]
    
    print(f"📋 Found {len(positions_without_oco)} positions without OCO orders")
    
    if not positions_without_oco:
        print("✅ All positions have OCO orders")
        return
    
    success_count = 0
    
    for position in positions_without_oco:
        print()
        oco_order_id = place_smart_exit_orders(client, position)
        
        if oco_order_id:
            # Update position with OCO order ID
            position.oco_order_id = oco_order_id
            position_manager.update_position_data(position.symbol, position)
            success_count += 1
            print(f"   ✅ Updated position with OCO order ID: {oco_order_id}")
        else:
            print(f"   ❌ Could not place exit orders for {position.symbol}")
    
    print()
    print(f"📊 Summary:")
    print(f"   ✅ Successfully placed OCO orders: {success_count}")
    print(f"   ❌ Failed to place OCO orders: {len(positions_without_oco) - success_count}")
    
    if success_count < len(positions_without_oco):
        print()
        print("💡 Recommendations for failed positions:")
        print("   - Review positions that are deeply underwater")
        print("   - Consider manual stop loss adjustment")
        print("   - Monitor for recovery opportunities")

if __name__ == "__main__":
    main()
