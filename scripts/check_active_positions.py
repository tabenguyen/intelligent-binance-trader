#!/usr/bin/env python3
"""
Get current status of active positions with live prices.
"""

import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from binance.client import Client
    from src.utils.env_loader import load_environment
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This script requires API access. Showing active trades data only.")

def get_current_prices_simple():
    """Get current prices using direct API call."""
    try:
        load_environment()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            print("❌ API credentials not found")
            return {}
            
        client = Client(api_key, api_secret)
        
        # Get active trades
        with open('data/active_trades_live.json', 'r') as f:
            active_trades = json.load(f)
        
        prices = {}
        for symbol in active_trades.keys():
            try:
                ticker = client.get_symbol_ticker(symbol=symbol)
                prices[symbol] = float(ticker['price'])
                print(f"✅ {symbol}: ${prices[symbol]:.4f}")
            except Exception as e:
                print(f"❌ Error getting price for {symbol}: {e}")
                prices[symbol] = 0.0
        
        return prices
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def analyze_active_positions():
    """Analyze current active positions."""
    
    # Load active trades
    try:
        with open('data/active_trades_live.json', 'r') as f:
            active_trades = json.load(f)
    except Exception as e:
        print(f"❌ Error loading active trades: {e}")
        return
    
    if not active_trades:
        print("No active positions found.")
        return
    
    print(f"\n🔍 Getting current prices for {len(active_trades)} active positions...")
    current_prices = get_current_prices_simple()
    
    print(f"\n" + "="*80)
    print("📊 CURRENT ACTIVE POSITIONS STATUS")
    print("="*80)
    
    total_invested = 0
    total_current_value = 0
    total_unrealized_pnl = 0
    
    for symbol, trade in active_trades.items():
        entry_price = trade.get('entry_price', 0)
        quantity = trade.get('quantity', 0)
        entry_time = trade.get('entry_time', 'N/A')
        stop_loss = trade.get('stop_loss', 0)
        take_profit = trade.get('take_profit', 0)
        oco_order_id = trade.get('oco_order_id', 'N/A')
        
        current_price = current_prices.get(symbol, 0)
        
        if entry_price > 0 and quantity > 0:
            entry_value = entry_price * quantity
            current_value = current_price * quantity if current_price > 0 else 0
            unrealized_pnl = current_value - entry_value if current_price > 0 else 0
            pnl_percent = ((current_price - entry_price) / entry_price) * 100 if current_price > 0 and entry_price > 0 else 0
            
            total_invested += entry_value
            total_current_value += current_value
            total_unrealized_pnl += unrealized_pnl
            
            status_emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
            
            print(f"\n{status_emoji} {symbol}")
            print(f"   Entry Price:      ${entry_price:.4f}")
            print(f"   Current Price:    ${current_price:.4f}")
            print(f"   Quantity:         {quantity:.4f}")
            print(f"   Entry Value:      ${entry_value:.2f}")
            print(f"   Current Value:    ${current_value:.2f}")
            print(f"   Unrealized P&L:   ${unrealized_pnl:.2f} ({pnl_percent:.2f}%)")
            print(f"   Stop Loss:        ${stop_loss:.4f}")
            print(f"   Take Profit:      ${take_profit:.4f}")
            print(f"   Entry Time:       {entry_time}")
            print(f"   OCO Order ID:     {oco_order_id}")
            
            # Risk analysis
            if current_price > 0:
                stop_distance = abs(current_price - stop_loss) / current_price * 100
                tp_distance = abs(take_profit - current_price) / current_price * 100
                print(f"   Stop Loss Dist:   {stop_distance:.1f}% away")
                print(f"   Take Profit Dist: {tp_distance:.1f}% away")
    
    print(f"\n📈 ACTIVE PORTFOLIO SUMMARY:")
    print(f"   Total Active Positions:    {len(active_trades)}")
    print(f"   Total Invested:            ${total_invested:.2f}")
    print(f"   Total Current Value:       ${total_current_value:.2f}")
    print(f"   Total Unrealized P&L:      ${total_unrealized_pnl:.2f}")
    if total_invested > 0:
        total_return_percent = (total_unrealized_pnl / total_invested) * 100
        print(f"   Total Return %:            {total_return_percent:.2f}%")

def main():
    """Main function."""
    print("🔍 Analyzing current active positions...")
    analyze_active_positions()
    print(f"\n🏁 Analysis complete!")

if __name__ == "__main__":
    main()
