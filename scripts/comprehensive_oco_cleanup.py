#!/usr/bin/env python3
"""
Comprehensive position cleanup and OCO order placement script
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
        return symbol[:-4]
    elif symbol.endswith('BUSD'):
        return symbol[:-4]
    elif symbol.endswith('BTC'):
        return symbol[:-3]
    elif symbol.endswith('ETH'):
        return symbol[:-3]
    else:
        return symbol

def cleanup_stale_positions(position_manager, balances):
    """Remove positions for assets we no longer hold"""
    positions = position_manager.get_positions()
    valid_positions = []
    removed_positions = []
    
    for position in positions:
        base_asset = extract_base_asset(position.symbol)
        
        if base_asset in balances and balances[base_asset]['total'] > 0:
            valid_positions.append(position)
        else:
            removed_positions.append(position)
    
    if removed_positions:
        print(f"🧹 Cleaning up {len(removed_positions)} stale positions:")
        for pos in removed_positions:
            print(f"   ❌ Removing {pos.symbol} - no balance for {extract_base_asset(pos.symbol)}")
            position_manager.positions.pop(pos.symbol, None)
        
        # Save the cleaned positions
        position_manager._save_positions()
        print(f"   ✅ Cleaned up {len(removed_positions)} stale positions")
    
    return valid_positions

def find_valid_trading_opportunities(balances, client):
    """Find assets we hold that could have OCO orders placed"""
    trading_opportunities = []
    
    print(f"🔍 Analyzing {len(balances)} available assets for trading opportunities:")
    
    for asset, balance_info in balances.items():
        if asset == 'USDT' or asset == 'BUSD':  # Skip quote currencies
            continue
            
        # Try common trading pairs
        possible_symbols = [f"{asset}USDT", f"{asset}BUSD"]
        
        for symbol in possible_symbols:
            try:
                # Check if symbol exists and get current price
                ticker = client.ticker_price(symbol)
                current_price = float(ticker['price'])
                
                # Calculate notional value
                total_value = balance_info['total'] * current_price
                free_value = balance_info['free'] * current_price
                
                print(f"   💰 {asset}: {balance_info['free']:.6f} free, ${free_value:.2f} value")
                
                if balance_info['free'] > 0 and free_value >= 5.0:  # Minimum $5 value
                    trading_opportunities.append({
                        'symbol': symbol,
                        'asset': asset,
                        'available_qty': balance_info['free'],
                        'current_price': current_price,
                        'value': free_value
                    })
                    break  # Found a valid trading pair, no need to check others
                    
            except ClientError:
                # Symbol doesn't exist or other API error
                continue
    
    return trading_opportunities

def place_protective_oco_orders(client, opportunities):
    """Place protective OCO orders for assets we hold"""
    success_count = 0
    
    for opp in opportunities:
        print(f"\n📍 Setting up protective OCO order for {opp['symbol']}...")
        print(f"   💰 Available: {opp['available_qty']:.6f} {opp['asset']}")
        print(f"   💵 Current Price: ${opp['current_price']:.6f}")
        print(f"   💎 Total Value: ${opp['value']:.2f}")
        
        # Use conservative stop loss and take profit
        # Stop loss: 5% below current price
        # Take profit: 10% above current price
        stop_loss = opp['current_price'] * 0.95
        take_profit = opp['current_price'] * 1.10
        
        print(f"   🎯 Stop Loss: ${stop_loss:.6f} (-5%)")
        print(f"   🎯 Take Profit: ${take_profit:.6f} (+10%)")
        
        # Use all available balance
        quantity = opp['available_qty']
        
        # Format according to exchange filters
        formatted_qty, formatted_stop_loss, formatted_take_profit = format_order_values(
            client, opp['symbol'], quantity, stop_loss, take_profit
        )
        
        if formatted_qty <= 0:
            print(f"   ❌ Cannot place order - quantity/notional requirements not met")
            continue
        
        try:
            print(f"   🔧 Placing OCO order:")
            print(f"      Quantity: {formatted_qty}")
            print(f"      Stop Loss: ${formatted_stop_loss}")
            print(f"      Take Profit: ${formatted_take_profit}")
            
            order = client.new_oco_order(
                symbol=opp['symbol'],
                side='SELL',
                quantity=formatted_qty,
                price=formatted_take_profit,
                stopPrice=formatted_stop_loss,
                stopLimitPrice=formatted_stop_loss,
                stopLimitTimeInForce='GTC'
            )
            
            print(f"   ✅ OCO order placed successfully!")
            print(f"      Order List ID: {order['orderListId']}")
            success_count += 1
            
        except ClientError as e:
            print(f"   ❌ Failed to place OCO order: {e}")
    
    return success_count

def format_order_values(client, symbol, quantity, stop_loss, take_profit):
    """Format order values according to exchange filters"""
    try:
        exchange_info = client.exchange_info()
        symbol_info = None
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                symbol_info = s
                break
        
        if not symbol_info:
            return 0, 0, 0
        
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
        min_notional = float(notional_filter.get('minNotional', 5.0))
        
        stop_loss_notional = formatted_qty * formatted_stop_loss
        take_profit_notional = formatted_qty * formatted_take_profit
        
        if stop_loss_notional < min_notional or take_profit_notional < min_notional:
            # Try to adjust quantity to meet minimum notional
            required_qty = min_notional / formatted_stop_loss
            if step_size > 0:
                required_qty = math.ceil(required_qty / step_size) * step_size
            
            if required_qty > quantity:
                print(f"   ❌ Need {required_qty:.6f} but only have {quantity:.6f} for min notional ${min_notional:.2f}")
                return 0, 0, 0
            
            formatted_qty = required_qty
        
        # Final formatting
        formatted_qty = float(f"{formatted_qty:.12f}")
        formatted_stop_loss = float(f"{formatted_stop_loss:.12f}")
        formatted_take_profit = float(f"{formatted_take_profit:.12f}")
        
        return formatted_qty, formatted_stop_loss, formatted_take_profit
        
    except Exception as e:
        print(f"   ❌ Error formatting values: {e}")
        return 0, 0, 0

def main():
    print("🔧 Comprehensive position cleanup and OCO order placement...")
    
    # Load environment and config
    load_environment()
    config = TradingConfig.from_env()
    
    # Initialize services
    position_manager = PositionManagementService(config.active_trades_file)
    client = Client(config.api_key, config.api_secret)
    
    # Get actual account balances
    print("💰 Fetching account balances...")
    balances = get_actual_balances(client)
    
    if not balances:
        print("❌ Could not fetch account balances")
        return
    
    print(f"📊 Found {len(balances)} assets with available balance")
    for asset, info in list(balances.items())[:10]:  # Show top 10
        print(f"   💎 {asset}: {info['free']:.6f} free, {info['locked']:.6f} locked")
    
    # Clean up stale positions
    print(f"\n🧹 Cleaning up stale positions...")
    valid_positions = cleanup_stale_positions(position_manager, balances)
    
    if valid_positions:
        print(f"✅ Found {len(valid_positions)} valid positions that match current balances")
        # TODO: Handle existing valid positions if needed
    else:
        print("ℹ️  No existing positions match current balances")
    
    # Find trading opportunities for assets we hold
    print(f"\n🎯 Finding trading opportunities...")
    opportunities = find_valid_trading_opportunities(balances, client)
    
    if not opportunities:
        print("❌ No suitable trading opportunities found")
        print("💡 This could mean:")
        print("   - Asset values are too small for minimum trade requirements")
        print("   - Trading pairs don't exist for your assets")
        print("   - Assets are already locked in existing orders")
        return
    
    print(f"📈 Found {len(opportunities)} trading opportunities:")
    for opp in opportunities:
        print(f"   🎯 {opp['symbol']}: ${opp['value']:.2f} value")
    
    # Place protective OCO orders
    success_count = place_protective_oco_orders(client, opportunities)
    
    print(f"\n📊 Final Summary:")
    print(f"   🧹 Cleaned up stale positions: {len(position_manager.get_positions()) != len(valid_positions)}")
    print(f"   ✅ Successfully placed OCO orders: {success_count}")
    print(f"   🎯 Total opportunities: {len(opportunities)}")

if __name__ == "__main__":
    main()
