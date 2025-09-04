#!/usr/bin/env python3
"""
Advanced OCO order placement with detailed validation and error handling
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig
from src.services.position_management_service import PositionManagementService
from binance.client import Client
from binance.exceptions import BinanceAPIException
import json
from decimal import Decimal, ROUND_DOWN

def get_symbol_info(client, symbol):
    """Get trading rules for a symbol"""
    try:
        exchange_info = client.get_exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                return s
        return None
    except Exception as e:
        print(f"❌ Error getting symbol info for {symbol}: {e}")
        return None

def format_quantity(quantity, step_size):
    """Format quantity according to step size"""
    try:
        step_decimal = Decimal(str(step_size))
        quantity_decimal = Decimal(str(quantity))
        
        # Calculate precision from step size
        if step_decimal == 1:
            precision = 0
        else:
            precision = abs(step_decimal.as_tuple().exponent)
        
        # Round down to step size
        multiplier = quantity_decimal / step_decimal
        rounded_multiplier = int(multiplier)
        formatted_quantity = float(rounded_multiplier * step_decimal)
        
        return round(formatted_quantity, precision)
    except Exception as e:
        print(f"❌ Error formatting quantity {quantity} with step size {step_size}: {e}")
        return quantity

def format_price(price, tick_size):
    """Format price according to tick size"""
    try:
        tick_decimal = Decimal(str(tick_size))
        price_decimal = Decimal(str(price))
        
        # Calculate precision from tick size
        if tick_decimal == 1:
            precision = 0
        else:
            precision = abs(tick_decimal.as_tuple().exponent)
        
        # Round to tick size
        multiplier = price_decimal / tick_decimal
        rounded_multiplier = round(multiplier)
        formatted_price = float(rounded_multiplier * tick_decimal)
        
        return round(formatted_price, precision)
    except Exception as e:
        print(f"❌ Error formatting price {price} with tick size {tick_size}: {e}")
        return price

def place_oco_order_with_validation(client, position):
    """Place OCO order with proper validation"""
    symbol = position.symbol  # Use symbol as-is (already includes USDT)
    quantity = position.quantity
    stop_loss = position.stop_loss
    take_profit = position.take_profit
    
    print(f"📍 Processing {position.symbol}...")
    print(f"   Quantity: {quantity}")
    print(f"   Stop Loss: ${stop_loss}")
    print(f"   Take Profit: ${take_profit}")
    
    # Get symbol trading rules
    symbol_info = get_symbol_info(client, symbol)
    if not symbol_info:
        print(f"❌ Could not get trading rules for {symbol}")
        return False
    
    # Extract filters
    filters = {f['filterType']: f for f in symbol_info['filters']}
    
    # Get lot size filter
    lot_size = filters.get('LOT_SIZE', {})
    min_qty = float(lot_size.get('minQty', 0))
    max_qty = float(lot_size.get('maxQty', 0))
    step_size = float(lot_size.get('stepSize', 0))
    
    # Get price filter
    price_filter = filters.get('PRICE_FILTER', {})
    min_price = float(price_filter.get('minPrice', 0))
    max_price = float(price_filter.get('maxPrice', 0))
    tick_size = float(price_filter.get('tickSize', 0))
    
    # Get notional filter
    notional_filter = filters.get('NOTIONAL', {})
    min_notional = float(notional_filter.get('minNotional', 0))
    
    print(f"   📏 Trading Rules:")
    print(f"      Min Qty: {min_qty}, Max Qty: {max_qty}, Step Size: {step_size}")
    print(f"      Min Price: {min_price}, Max Price: {max_price}, Tick Size: {tick_size}")
    print(f"      Min Notional: {min_notional}")
    
    # Format quantity and prices
    formatted_qty = format_quantity(quantity, step_size)
    formatted_stop_loss = format_price(stop_loss, tick_size)
    formatted_take_profit = format_price(take_profit, tick_size)
    
    print(f"   🔧 Formatted Values:")
    print(f"      Quantity: {formatted_qty}")
    print(f"      Stop Loss: {formatted_stop_loss}")
    print(f"      Take Profit: {formatted_take_profit}")
    
    # Validate quantity
    if formatted_qty < min_qty:
        print(f"❌ Quantity {formatted_qty} is below minimum {min_qty}")
        return False
    
    if max_qty > 0 and formatted_qty > max_qty:
        print(f"❌ Quantity {formatted_qty} is above maximum {max_qty}")
        return False
    
    # Validate notional value
    stop_loss_notional = formatted_qty * formatted_stop_loss
    take_profit_notional = formatted_qty * formatted_take_profit
    
    if stop_loss_notional < min_notional:
        print(f"❌ Stop loss notional {stop_loss_notional} is below minimum {min_notional}")
        return False
    
    if take_profit_notional < min_notional:
        print(f"❌ Take profit notional {take_profit_notional} is below minimum {min_notional}")
        return False
    
    print(f"   ✅ All validations passed")
    print(f"   🔄 Placing OCO order...")
    
    try:
        # Get current price
        current_price_response = client.get_symbol_ticker(symbol=symbol)
        current_price = float(current_price_response['price'])
        
        print(f"   💰 Current Price: ${current_price}")
        print(f"   📊 Position Analysis:")
        print(f"      Entry Price: ${position.entry_price}")
        
        # Check if position is in profit or loss
        pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
        print(f"      Current P&L: {pnl_pct:.2f}%")
        
        # For positions in loss, we need to be more careful about exit strategy
        if current_price < position.entry_price:
            print(f"   ⚠️  Position is currently at a loss")
        
        # Validate stop loss and take profit relative to current price
        # For SELL orders (exiting long positions):
        # - Take profit should be above current price
        # - Stop loss should be below current price
        
        if formatted_take_profit <= current_price:
            print(f"   ❌ Take profit {formatted_take_profit} must be above current price {current_price}")
            return False
            
        if formatted_stop_loss >= current_price:
            print(f"   ❌ Stop loss {formatted_stop_loss} must be below current price {current_price}")
            return False
        
        # Use the simpler OCO order creation method
        order = client.create_oco_order(
            symbol=symbol,
            side='SELL',
            quantity=formatted_qty,
            price=str(formatted_take_profit),  # Limit order (take profit)
            stopPrice=str(formatted_stop_loss),  # Stop price
            stopLimitPrice=str(formatted_stop_loss),  # Stop limit price
            stopLimitTimeInForce='GTC'
        )
        
        print(f"   ✅ OCO order placed successfully!")
        print(f"      Order List ID: {order['orderListId']}")
        
        # Display order details
        orders = order.get('orders', [])
        for order_detail in orders:
            order_type = order_detail.get('type', '')
            order_id = order_detail.get('orderId', '')
            price = order_detail.get('price', '')
            stop_price = order_detail.get('stopPrice', '')
            print(f"      {order_type} Order ID: {order_id}")
            if price:
                print(f"        Price: {price}")
            if stop_price:
                print(f"        Stop Price: {stop_price}")
        
        return order['orderListId']
        
    except BinanceAPIException as e:
        print(f"   ❌ Binance API Error: {e}")
        print(f"      Error Code: {e.code}")
        print(f"      Error Message: {e.message}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    print("🔧 Advanced OCO order placement with validation...")
    
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
        oco_order_id = place_oco_order_with_validation(client, position)
        
        if oco_order_id:
            # Update position with OCO order ID
            position.oco_order_id = oco_order_id
            position_manager.save_positions(positions)
            success_count += 1
            print(f"   ✅ Updated position with OCO order ID: {oco_order_id}")
        else:
            print(f"   ❌ Failed to place OCO order for {position.symbol}")
    
    print()
    print(f"📊 Summary:")
    print(f"   ✅ Successfully placed OCO orders: {success_count}")
    print(f"   ❌ Failed to place OCO orders: {len(positions_without_oco) - success_count}")

if __name__ == "__main__":
    main()
