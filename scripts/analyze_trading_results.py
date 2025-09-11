#!/usr/bin/env python3
"""
Comprehensive trading analysis script to list all traded coins, profit/loss, and risk management results.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.env_loader import load_environment
from src.services.trade_execution_service import TradeExecutionService
from src.models.config_models import TradingConfig

def load_active_trades() -> Dict:
    """Load active trades from JSON files."""
    data_dir = "data"
    trades = {}
    
    # Check for different active trades files
    trade_files = [
        "active_trades_live.json",
        "active_trades_testnet.json", 
        "active_trades.json"
    ]
    
    for filename in trade_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            print(f"📂 Loading {filename}...")
            try:
                with open(filepath, 'r') as f:
                    file_trades = json.load(f)
                    trades.update(file_trades)
                    print(f"   Found {len(file_trades)} active positions")
            except Exception as e:
                print(f"   ❌ Error loading {filename}: {e}")
    
    return trades

def parse_logs_for_trades() -> List[Dict]:
    """Parse log files to extract trading information."""
    log_files = [
        "logs/output_live.log",
        "logs/output.log"
    ]
    
    trades = []
    
    for log_file in log_files:
        if not os.path.exists(log_file):
            continue
            
        print(f"📂 Parsing {log_file}...")
        
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                
            # Extract successful trades
            trade_pattern = r'🎉 TRADE EXECUTED SUCCESSFULLY!\n.*?Symbol: ([A-Z]+USDT)\n.*?Quantity: ([0-9.]+)\n.*?Entry Price: \$([0-9.]+)\n.*?Total Value: \$([0-9.]+)'
            
            matches = re.findall(trade_pattern, content, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                symbol, quantity, entry_price, total_value = match
                trades.append({
                    'symbol': symbol,
                    'quantity': float(quantity),
                    'entry_price': float(entry_price),
                    'total_value': float(total_value),
                    'status': 'executed',
                    'source': log_file
                })
                
            # Extract risk management rejections
            risk_pattern = r'❌ Signal for ([A-Z]+USDT) rejected by risk manager'
            risk_matches = re.findall(risk_pattern, content)
            
            for symbol in risk_matches:
                trades.append({
                    'symbol': symbol,
                    'status': 'rejected_by_risk_management',
                    'source': log_file
                })
                
        except Exception as e:
            print(f"   ❌ Error parsing {log_file}: {e}")
    
    return trades

def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    """Get current prices for symbols."""
    try:
        # Load environment and create trade service
        load_environment()
        config = TradingConfig()
        trade_service = TradeExecutionService(config)
        
        prices = {}
        for symbol in symbols:
            try:
                ticker = trade_service.client.get_symbol_ticker(symbol=symbol)
                prices[symbol] = float(ticker['price'])
            except Exception as e:
                print(f"   ⚠️  Could not get price for {symbol}: {e}")
                prices[symbol] = 0.0
                
        return prices
        
    except Exception as e:
        print(f"❌ Error getting current prices: {e}")
        return {symbol: 0.0 for symbol in symbols}

def calculate_pnl(trades_data: Dict, current_prices: Dict[str, float]) -> Dict:
    """Calculate profit/loss for active trades."""
    pnl_data = {}
    
    for symbol, trade in trades_data.items():
        entry_price = trade.get('entry_price', 0)
        quantity = trade.get('quantity', 0)
        current_price = current_prices.get(symbol, 0)
        
        if entry_price > 0 and quantity > 0 and current_price > 0:
            entry_value = entry_price * quantity
            current_value = current_price * quantity
            pnl_dollar = current_value - entry_value
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            
            pnl_data[symbol] = {
                'entry_price': entry_price,
                'current_price': current_price,
                'quantity': quantity,
                'entry_value': entry_value,
                'current_value': current_value,
                'pnl_dollar': pnl_dollar,
                'pnl_percent': pnl_percent,
                'stop_loss': trade.get('stop_loss', 0),
                'take_profit': trade.get('take_profit', 0),
                'entry_time': trade.get('entry_time', 'N/A'),
                'oco_order_id': trade.get('oco_order_id', 'N/A')
            }
    
    return pnl_data

def analyze_risk_management(log_trades: List[Dict]) -> Dict:
    """Analyze risk management results."""
    risk_stats = {
        'total_signals': 0,
        'executed': 0,
        'rejected_by_risk': 0,
        'rejected_symbols': [],
        'executed_symbols': [],
        'execution_rate': 0.0
    }
    
    for trade in log_trades:
        risk_stats['total_signals'] += 1
        
        if trade['status'] == 'executed':
            risk_stats['executed'] += 1
            risk_stats['executed_symbols'].append(trade['symbol'])
        elif trade['status'] == 'rejected_by_risk_management':
            risk_stats['rejected_by_risk'] += 1
            risk_stats['rejected_symbols'].append(trade['symbol'])
    
    if risk_stats['total_signals'] > 0:
        risk_stats['execution_rate'] = (risk_stats['executed'] / risk_stats['total_signals']) * 100
    
    return risk_stats

def print_summary(active_trades: Dict, pnl_data: Dict, risk_stats: Dict, log_trades: List[Dict]):
    """Print comprehensive trading summary."""
    
    print("\n" + "="*80)
    print("🚀 COMPREHENSIVE TRADING ANALYSIS REPORT")
    print("="*80)
    
    # Active Positions Summary
    print("\n📊 ACTIVE POSITIONS:")
    print("-" * 60)
    
    if not active_trades:
        print("   No active positions found.")
    else:
        total_invested = 0
        total_current_value = 0
        total_pnl = 0
        
        for symbol, pnl in pnl_data.items():
            status = "🟢" if pnl['pnl_dollar'] >= 0 else "🔴"
            
            print(f"\n{status} {symbol}")
            print(f"   Entry Price:    ${pnl['entry_price']:.4f}")
            print(f"   Current Price:  ${pnl['current_price']:.4f}")
            print(f"   Quantity:       {pnl['quantity']:.4f}")
            print(f"   Entry Value:    ${pnl['entry_value']:.2f}")
            print(f"   Current Value:  ${pnl['current_value']:.2f}")
            print(f"   P&L:            ${pnl['pnl_dollar']:.2f} ({pnl['pnl_percent']:.2f}%)")
            print(f"   Stop Loss:      ${pnl['stop_loss']:.4f}")
            print(f"   Take Profit:    ${pnl['take_profit']:.4f}")
            print(f"   Entry Time:     {pnl['entry_time']}")
            print(f"   OCO Order ID:   {pnl['oco_order_id']}")
            
            total_invested += pnl['entry_value']
            total_current_value += pnl['current_value']
            total_pnl += pnl['pnl_dollar']
        
        print(f"\n📈 PORTFOLIO SUMMARY:")
        print(f"   Total Invested:     ${total_invested:.2f}")
        print(f"   Current Value:      ${total_current_value:.2f}")
        print(f"   Total P&L:          ${total_pnl:.2f}")
        print(f"   Total P&L %:        {((total_current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0:.2f}%")
    
    # Risk Management Analysis
    print(f"\n🛡️  RISK MANAGEMENT ANALYSIS:")
    print("-" * 60)
    print(f"   Total Signals Generated:    {risk_stats['total_signals']}")
    print(f"   Successfully Executed:      {risk_stats['executed']}")
    print(f"   Rejected by Risk Manager:   {risk_stats['rejected_by_risk']}")
    print(f"   Execution Rate:             {risk_stats['execution_rate']:.1f}%")
    
    if risk_stats['executed_symbols']:
        print(f"\n✅ Successfully Executed Trades:")
        for symbol in set(risk_stats['executed_symbols']):
            count = risk_stats['executed_symbols'].count(symbol)
            print(f"   • {symbol} ({count} time{'s' if count > 1 else ''})")
    
    if risk_stats['rejected_symbols']:
        print(f"\n❌ Rejected by Risk Management:")
        for symbol in set(risk_stats['rejected_symbols']):
            count = risk_stats['rejected_symbols'].count(symbol)
            print(f"   • {symbol} ({count} time{'s' if count > 1 else ''})")
    
    # Trading History from Logs
    print(f"\n📜 TRADING HISTORY FROM LOGS:")
    print("-" * 60)
    
    executed_trades = [t for t in log_trades if t['status'] == 'executed']
    
    if not executed_trades:
        print("   No executed trades found in logs.")
    else:
        for i, trade in enumerate(executed_trades, 1):
            print(f"\n{i}. {trade['symbol']}")
            print(f"   Quantity:     {trade.get('quantity', 'N/A')}")
            print(f"   Entry Price:  ${trade.get('entry_price', 0):.4f}")
            print(f"   Total Value:  ${trade.get('total_value', 0):.2f}")
            print(f"   Source:       {trade.get('source', 'N/A')}")

def main():
    """Main analysis function."""
    print("🔍 Starting comprehensive trading analysis...")
    
    # Load active trades
    active_trades = load_active_trades()
    
    # Parse logs for trade history
    log_trades = parse_logs_for_trades()
    
    # Get current prices
    symbols = list(active_trades.keys()) if active_trades else []
    current_prices = get_current_prices(symbols) if symbols else {}
    
    # Calculate P&L
    pnl_data = calculate_pnl(active_trades, current_prices)
    
    # Analyze risk management
    risk_stats = analyze_risk_management(log_trades)
    
    # Print comprehensive summary
    print_summary(active_trades, pnl_data, risk_stats, log_trades)
    
    print(f"\n🏁 Analysis complete!")

if __name__ == "__main__":
    main()
