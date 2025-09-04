#!/usr/bin/env python3
"""
Balance-aware OCO order placement that uses actual account balances
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

def get_actual_balances(client):
    """Get actual account balances"""
    try:
        account_info = client.account()
        balances = {}
        
        for balance in account_info['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            
            if free > 0:  # Only include assets with available balance
                balances[asset] = {
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                }
        
        return balances
    except Exception as e:
        print(f"❌ Error getting balances: {e}")
        return {}

def extract_base_asset(symbol):
    """Extract base asset from trading pair symbol"""
    if symbol.endswith('USDT'):
        return symbol[:-4]  # Remove 'USDT'
    elif symbol.endswith('BUSD'):
        return symbol[:-4]  # Remove 'BUSD'
    elif symbol.endswith('BTC'):
        return symbol[:-3]   # Remove 'BTC'
    elif symbol.endswith('ETH'):
        return symbol[:-3]   # Remove 'ETH'
    else:
        return symbol  # Return as-is if no known quote asset

def calculate_oco_prices(entry_price, current_price, position_type="long", risk_reward_ratio=1.5):
    """Calculate appropriate stop loss and take profit prices"""
    if position_type == "long":
        # For long positions
        # Stop loss below entry/current price, take profit above
        stop_loss_distance = abs(entry_price - current_price) * 1.2  # 20% more than current loss
        stop_loss = min(entry_price * 0.95, current_price * 0.97)  # Whichever is lower
        
        take_profit_distance = stop_loss_distance * risk_reward_ratio
        take_profit = current_price + take_profit_distance
        
        return stop_loss, take_profit
    else:
        # For short positions (not commonly used in this bot)
        return None, None

def place_balance_aware_oco(client, symbol, position_entry_price, position_quantity, balances):
    """Place OCO order using actual available balance"""
    try:
        # Extract base asset from symbol
        base_asset = extract_base_asset(symbol)
        
        print(f"📍 Processing {symbol} (Base Asset: {base_asset})...")
        
        # Check if we have the asset
        if base_asset not in balances:
            print(f"   ❌ No balance found for {base_asset}")
            return False
        
        available_qty = balances[base_asset]['free']
        print(f"   💰 Available Balance: {available_qty} {base_asset}")
        print(f"   📊 Position Quantity: {position_quantity} {base_asset}")
        
        # Use the minimum of available balance and position quantity
        actual_qty = min(available_qty, position_quantity)
        
        if actual_qty <= 0:
            print(f"   ❌ No available quantity to trade")
            return False
        
        if actual_qty < position_quantity:
            print(f"   ⚠️  Using available balance {actual_qty} instead of position quantity {position_quantity}")
        
        # Get current price
        ticker = client.ticker_price(symbol)
        current_price = float(ticker['price'])
        print(f"   💰 Current Price: ${current_price:.6f}")
        print(f"   📊 Entry Price: ${position_entry_price:.6f}")
        
        # Calculate P&L
        pnl_pct = ((current_price - position_entry_price) / position_entry_price) * 100
        print(f"   📈 Current P&L: {pnl_pct:.2f}%")
        
        # Calculate stop loss and take profit
        stop_loss, take_profit = calculate_oco_prices(position_entry_price, current_price)
        
        print(f"   🎯 Calculated Stop Loss: ${stop_loss:.6f}")
        print(f"   🎯 Calculated Take Profit: ${take_profit:.6f}")
        
        # Validate prices
        if take_profit <= current_price:
            print(f"   ❌ Take profit {take_profit:.6f} must be above current price {current_price:.6f}")
            return False
            
        if stop_loss >= current_price:
            print(f"   ❌ Stop loss {stop_loss:.6f} must be below current price {current_price:.6f}")
            return False
        
        # Format according to exchange filters
        formatted_qty, formatted_stop_loss, formatted_take_profit = format_order_values(
            client, symbol, actual_qty, stop_loss, take_profit
        )
        
        if formatted_qty <= 0:
            print(f"   ❌ Quantity too small after formatting")
            return False
        
        print(f"   🔧 Placing OCO order:")
        print(f"      Quantity: {formatted_qty}")
        print(f"      Stop Loss: ${formatted_stop_loss}")
        print(f"      Take Profit: ${formatted_take_profit}")
        
        # Place OCO order
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
        
        # Display order details
        orders = order.get('orders', [])
        for order_detail in orders:
            order_type = order_detail.get('type', '')
            order_id = order_detail.get('orderId', '')
            price = order_detail.get('price', '')
            stop_price = order_detail.get('stopPrice', '')
            print(f"      {order_type} Order ID: {order_id}")
            if price and price != '0.00000000':
                print(f"        Price: {price}")
            if stop_price and stop_price != '0.00000000':
                print(f"        Stop Price: {stop_price}")
        
        return order['orderListId']
        
    except ClientError as e:
        print(f"   ❌ Binance API Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def format_order_values(client, symbol, quantity, stop_loss, take_profit):
    """Format order values according to exchange filters"""
    try:
        # Get symbol info
        exchange_info = client.exchange_info()
        symbol_info = None
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                symbol_info = s
                break
        
        if not symbol_info:
            return 0, 0, 0
        
        # Get filters
        filters = {f['filterType']: f for f in symbol_info['filters']}
        
        # Format quantity
        lot_size = filters.get('LOT_SIZE', {})
        step_size = float(lot_size.get('stepSize', 0.1))
        min_qty = float(lot_size.get('minQty', 0))
        
        if step_size > 0:
            formatted_qty = math.floor(quantity / step_size) * step_size
        else:
            formatted_qty = quantity
            
        if formatted_qty < min_qty:
            print(f"   ❌ Quantity {formatted_qty} below minimum {min_qty}")
            return 0, 0, 0
        
        # Format prices
        price_filter = filters.get('PRICE_FILTER', {})
        tick_size = float(price_filter.get('tickSize', 0.001))
        
        if tick_size > 0:
            formatted_stop_loss = math.floor(stop_loss / tick_size) * tick_size
            formatted_take_profit = math.floor(take_profit / tick_size) * tick_size
        else:
            formatted_stop_loss = stop_loss
            formatted_take_profit = take_profit
        
        # Check NOTIONAL filter
        notional_filter = filters.get('NOTIONAL', {})
        min_notional = float(notional_filter.get('minNotional', 5.0))  # Default 5 USDT
        
        # Calculate notional values
        stop_loss_notional = formatted_qty * formatted_stop_loss
        take_profit_notional = formatted_qty * formatted_take_profit
        
        print(f"   📊 Order Values:")
        print(f"      Stop Loss Notional: ${stop_loss_notional:.2f} (min: ${min_notional:.2f})")
        print(f"      Take Profit Notional: ${take_profit_notional:.2f} (min: ${min_notional:.2f})")
        
        if stop_loss_notional < min_notional or take_profit_notional < min_notional:
            print(f"   ❌ Order notional value below minimum ${min_notional:.2f}")
            
            # Try to increase quantity to meet minimum notional
            required_qty_for_stop = min_notional / formatted_stop_loss
            required_qty_for_take = min_notional / formatted_take_profit
            min_required_qty = max(required_qty_for_stop, required_qty_for_take)
            
            # Round up to next valid step
            if step_size > 0:
                min_required_qty = math.ceil(min_required_qty / step_size) * step_size
            
            print(f"   💡 Minimum quantity needed: {min_required_qty:.8f}")
            
            if min_required_qty > quantity:
                print(f"   ❌ Available balance insufficient for minimum trade size")
                return 0, 0, 0
            else:
                print(f"   🔧 Adjusting quantity to meet minimum notional")
                formatted_qty = min_required_qty
        
        # Format to avoid floating point precision issues
        formatted_qty = float(f"{formatted_qty:.12f}")
        formatted_stop_loss = float(f"{formatted_stop_loss:.12f}")
        formatted_take_profit = float(f"{formatted_take_profit:.12f}")
        
        return formatted_qty, formatted_stop_loss, formatted_take_profit
        
    except Exception as e:
        print(f"   ❌ Error formatting values: {e}")
        return 0, 0, 0

def main():
    print("💰 Balance-aware OCO order placement...")
    
    # Load environment and config
    load_environment()
    config = TradingConfig.from_env()
    
    # Initialize services
    position_manager = PositionManagementService(config.active_trades_file)
    client = Client(config.api_key, config.api_secret)
    
    # Get actual account balances
    print("🔍 Fetching account balances...")
    balances = get_actual_balances(client)
    
    if not balances:
        print("❌ Could not fetch account balances")
        return
    
    print(f"📊 Found {len(balances)} assets with available balance")
    
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
        oco_order_id = place_balance_aware_oco(
            client, 
            position.symbol, 
            position.entry_price, 
            position.quantity, 
            balances
        )
        
        if oco_order_id:
            # Update position with OCO order ID
            position.oco_order_id = oco_order_id
            position_manager.update_position_data(position.symbol, position)
            success_count += 1
            print(f"   ✅ Updated position with OCO order ID: {oco_order_id}")
        else:
            print(f"   ❌ Could not place OCO order for {position.symbol}")
    
    print()
    print(f"📊 Summary:")
    print(f"   ✅ Successfully placed OCO orders: {success_count}")
    print(f"   ❌ Failed to place OCO orders: {len(positions_without_oco) - success_count}")

if __name__ == "__main__":
    main()
