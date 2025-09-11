#!/usr/bin/env python3
"""
Extract and analyze completed trades from logs to calculate actual profit/loss.
"""

import re
import os
from datetime import datetime

def analyze_completed_trades():
    """Analyze completed trades and calculate P&L."""
    
    log_file = "logs/output_live.log"
    if not os.path.exists(log_file):
        print(f"❌ Log file {log_file} not found")
        return
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # Find executed trades with entry details
    executed_pattern = r'🎉 TRADE EXECUTED SUCCESSFULLY!\n.*?Symbol: ([A-Z]+USDT)\n.*?Quantity: ([0-9.]+)\n.*?Entry Price: \$([0-9.]+)\n.*?Total Value: \$([0-9.]+)'
    executed_matches = re.findall(executed_pattern, content, re.MULTILINE | re.DOTALL)
    
    # Find completed trades (exits)
    completed_pattern = r'✅ Position closed: ([A-Z]+USDT) @ \$([0-9.]+) \(OCO Completed\)'
    completed_matches = re.findall(completed_pattern, content)
    
    # Build trade pairs
    trades = {}
    for symbol, quantity, entry_price, total_value in executed_matches:
        if symbol not in trades:
            trades[symbol] = []
        trades[symbol].append({
            'quantity': float(quantity),
            'entry_price': float(entry_price),
            'total_value': float(total_value),
            'exit_price': None,
            'pnl': None,
            'status': 'open'
        })
    
    # Match exits to entries
    for symbol, exit_price in completed_matches:
        exit_price = float(exit_price)
        if symbol in trades:
            # Find the first open trade for this symbol
            for trade in trades[symbol]:
                if trade['status'] == 'open':
                    trade['exit_price'] = exit_price
                    trade['status'] = 'closed'
                    
                    # Calculate P&L
                    entry_value = trade['quantity'] * trade['entry_price']
                    exit_value = trade['quantity'] * exit_price
                    trade['pnl'] = exit_value - entry_value
                    trade['pnl_percent'] = ((exit_price - trade['entry_price']) / trade['entry_price']) * 100
                    break
    
    return trades

def print_completed_trades_analysis(trades):
    """Print analysis of completed trades."""
    
    print("\n" + "="*80)
    print("💰 COMPLETED TRADES ANALYSIS")
    print("="*80)
    
    completed_trades = []
    total_pnl = 0
    total_invested = 0
    winning_trades = 0
    losing_trades = 0
    
    for symbol, symbol_trades in trades.items():
        for trade in symbol_trades:
            if trade['status'] == 'closed':
                completed_trades.append((symbol, trade))
                total_pnl += trade['pnl']
                total_invested += trade['total_value']
                
                if trade['pnl'] > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
    
    if not completed_trades:
        print("No completed trades found.")
        return
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total Completed Trades:     {len(completed_trades)}")
    print(f"   Winning Trades:             {winning_trades}")
    print(f"   Losing Trades:              {losing_trades}")
    print(f"   Win Rate:                   {(winning_trades / len(completed_trades) * 100):.1f}%")
    print(f"   Total Amount Invested:      ${total_invested:.2f}")
    print(f"   Total P&L:                  ${total_pnl:.2f}")
    print(f"   Total Return:               {(total_pnl / total_invested * 100):.2f}%")
    
    print(f"\n📈 INDIVIDUAL COMPLETED TRADES:")
    print("-" * 80)
    
    # Sort trades by P&L (best to worst)
    completed_trades.sort(key=lambda x: x[1]['pnl'], reverse=True)
    
    for i, (symbol, trade) in enumerate(completed_trades, 1):
        status_emoji = "🟢" if trade['pnl'] > 0 else "🔴"
        
        print(f"\n{i:2d}. {status_emoji} {symbol}")
        print(f"     Entry Price:    ${trade['entry_price']:.4f}")
        print(f"     Exit Price:     ${trade['exit_price']:.4f}")
        print(f"     Quantity:       {trade['quantity']:.4f}")
        print(f"     Investment:     ${trade['total_value']:.2f}")
        print(f"     P&L:            ${trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")

def print_open_positions_summary(trades):
    """Print summary of still open positions."""
    
    open_trades = []
    total_open_value = 0
    
    for symbol, symbol_trades in trades.items():
        for trade in symbol_trades:
            if trade['status'] == 'open':
                open_trades.append((symbol, trade))
                total_open_value += trade['total_value']
    
    if open_trades:
        print(f"\n🔄 STILL OPEN POSITIONS:")
        print("-" * 40)
        print(f"   Total Open Positions:   {len(open_trades)}")
        print(f"   Total Open Value:       ${total_open_value:.2f}")
        
        print(f"\n   Open Positions:")
        for symbol, trade in open_trades:
            print(f"   • {symbol}: ${trade['total_value']:.2f} @ ${trade['entry_price']:.4f}")

def main():
    """Main function."""
    print("🔍 Analyzing completed trades from logs...")
    
    trades = analyze_completed_trades()
    print_completed_trades_analysis(trades)
    print_open_positions_summary(trades)
    
    print(f"\n🏁 Analysis complete!")

if __name__ == "__main__":
    main()
