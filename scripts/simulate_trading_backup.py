#!/usr/bin/eimport os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock
import json
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))Trading Bot Simulation and Backtesting Script

This script allows you to test your trading bot strategy against historical data
without making real trades. It simulates the bot's behavior and provides performance metrics.

Usage:
    python simulate_trading.py --symbol BTCUSDT --days 7 --interval 4h
    python simulate_trading.py --backtest --symbols BTCUSDT,ETHUSDT --days 30
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock
import json
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot modules
import trading_bot
from strategies.ema_cross_strategy import EMACrossStrategy


class TradingSimulator:
    """Simulates trading bot behavior with historical data"""
    
    def __init__(self, initial_balance=1000.0, trade_amount=15.0):
        """
        Initialize trading simulator
        
        Args:
            initial_balance (float): Starting USDT balance
            trade_amount (float): Amount in USDT per trade
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trade_amount = trade_amount
        self.positions = {}  # {symbol: {'quantity': float, 'entry_price': float, 'entry_time': datetime}}
        self.trade_history = []
        self.strategy = EMACrossStrategy()
        
        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        
    def simulate_market_data(self, symbol, days=7, interval='4h', use_real_data=True):
        """
        Fetch real historical market data from Binance for simulation
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            days (int): Number of days of historical data
            interval (str): Time interval ('1h', '4h', '1d')
            use_real_data (bool): If True, fetch real data from Binance; if False, generate simulated data
            
        Returns:
            pd.DataFrame: Historical OHLCV data
        """
        if use_real_data:
            return self._fetch_real_binance_data(symbol, days, interval)
        else:
            return self._generate_simulated_data(symbol, days, interval)
    
    def _fetch_real_binance_data(self, symbol, days=7, interval='4h'):
        """
        Fetch real historical data from Binance
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            days (int): Number of days of historical data
            interval (str): Time interval ('1h', '4h', '1d')
            
        Returns:
            pd.DataFrame: Real historical OHLCV data from Binance
        """
        print(f"📊 Fetching REAL market data from Binance for {symbol}")
        print(f"   Period: {days} days, Interval: {interval}")
        
        try:
            # Initialize Binance client (using environment variables or defaults)
            from binance.spot import Spot as Client
            from dotenv import load_dotenv
            
            load_dotenv()
            
            # For historical data, we don't need API credentials
            # Use public endpoints only
            api_key = os.getenv("BINANCE_API_KEY", "")
            api_secret = os.getenv("BINANCE_API_SECRET", "")
            use_testnet = os.getenv("USE_TESTNET", "True").lower() in ("true", "1", "yes")
            
            if use_testnet:
                base_url = "https://testnet.binance.vision"
                print(f"   Using TESTNET for data (limited historical data available)")
            else:
                base_url = "https://api.binance.com"
                print(f"   Using LIVE Binance API for historical data")
            
            # Create client (can work without credentials for public data)
            if api_key and api_secret:
                client = Client(api_key, api_secret, base_url=base_url)
            else:
                client = Client(base_url=base_url)
            
            # Calculate the limit (number of candles needed)
            if interval == '1h':
                limit = min(days * 24, 1000)  # Binance limit is 1000
            elif interval == '4h':
                limit = min(days * 6, 1000)
            elif interval == '1d':
                limit = min(days, 1000)
            elif interval == '15m':
                limit = min(days * 96, 1000)  # 96 15-min candles per day
            else:
                limit = min(days * 6, 1000)  # Default to 4h
            
            print(f"   Requesting {limit} candles of {interval} data...")
            
            # Fetch historical klines
            klines = client.klines(symbol=symbol, interval=interval, limit=limit)
            
            if not klines:
                print(f"   ⚠️ No data received for {symbol}")
                return self._generate_simulated_data(symbol, days, interval)
            
            # Convert to DataFrame
            columns = [
                'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time',
                'Quote_Asset_Volume', 'Number_of_Trades', 'Taker_Buy_Base_Asset_Volume',
                'Taker_Buy_Quote_Asset_Volume', 'Ignore'
            ]
            
            df = pd.DataFrame(klines, columns=columns)
            
            # Convert data types
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col])
            
            # Convert timestamps
            df['Timestamp'] = pd.to_datetime(df['Open_Time'], unit='ms')
            
            # Keep only necessary columns and rename to match expected format
            df = df[['Open', 'High', 'Low', 'Close', 'Volume', 'Timestamp']].copy()
            
            # Sort by timestamp (oldest first for proper backtesting)
            df = df.sort_values('Timestamp').reset_index(drop=True)
            
            print(f"   ✅ Successfully fetched {len(df)} real candles")
            print(f"   📅 Date range: {df['Timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M')} to {df['Timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M')}")
            print(f"   💰 Price range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")
            print(f"   📊 Latest price: ${df['Close'].iloc[-1]:.2f}")
            
            return df
            
        except Exception as e:
            print(f"   ❌ Error fetching real data: {e}")
            print(f"   🔄 Falling back to simulated data...")
            return self._generate_simulated_data(symbol, days, interval)
    
    def _generate_simulated_data(self, symbol, days=7, interval='4h'):
        """
        Generate simulated market data (fallback method)
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            days (int): Number of days of historical data
            interval (str): Time interval ('1h', '4h', '1d')
            
        Returns:
            pd.DataFrame: Simulated OHLCV data
        """
        print(f"📊 Generating simulated market data for {symbol}")
        print(f"   Period: {days} days, Interval: {interval}")
        
        # Generate realistic-looking price data
        if interval == '4h':
            periods = days * 6  # 6 four-hour periods per day
        elif interval == '1h':
            periods = days * 24
        elif interval == '1d':
            periods = days
        else:
            periods = days * 6  # Default to 4h
        
        # Starting price based on symbol
        if symbol == 'BTCUSDT':
            base_price = 45000 + np.random.uniform(-5000, 5000)
        elif symbol == 'ETHUSDT':
            base_price = 3000 + np.random.uniform(-500, 500)
        else:
            base_price = 100 + np.random.uniform(-20, 20)
        
        # Generate price series with realistic volatility
        price_changes = np.random.normal(0, 0.02, periods)  # 2% volatility
        prices = [base_price]
        
        for change in price_changes:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 0.01))  # Prevent negative prices
        
        # Create OHLCV data
        data = []
        for i in range(periods):
            open_price = prices[i]
            close_price = prices[i + 1]
            
            # High and low based on open/close with some random variation
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            volume = np.random.uniform(50, 200)
            
            data.append({
                'Open': open_price,
                'High': high_price,
                'Low': low_price,
                'Close': close_price,
                'Volume': volume,
                'Timestamp': datetime.now() - timedelta(hours=(periods - i) * 4)
            })
        
        df = pd.DataFrame(data)
        print(f"   Generated {len(df)} candles")
        print(f"   Price range: ${df['Low'].min():.2f} - ${df['High'].max():.2f}")
        return df
    
    def analyze_candle(self, df, index):
        """
        Analyze a single candle using the trading bot's logic
        
        Args:
            df (pd.DataFrame): Complete historical data
            index (int): Current candle index to analyze
            
        Returns:
            dict: Analysis results or None if insufficient data
        """
        # Ensure we have enough historical data for analysis
        if index < 55:  # Need at least 55 candles for 55-EMA
            return None
        
        # Get subset of data up to current candle
        historical_df = df.iloc[:index+1].copy()
        
        # Use the bot's analysis function
        analysis = trading_bot.analyze_data(historical_df)
        return analysis
    
    def check_buy_signal(self, symbol, analysis, current_price):
        """
        Check for buy signal using the strategy
        
        Args:
            symbol (str): Trading symbol
            analysis (dict): Technical analysis results
            current_price (float): Current price
            
        Returns:
            bool: True if buy signal detected
        """
        if not analysis:
            return False
        
        # Use mock client for strategy (no real API calls)
        mock_client = Mock()
        
        # Disable filters for simulation (focus on core strategy)
        with_patches = [
            ('trading_bot.ENABLE_DAILY_TREND_FILTER', False),
            ('trading_bot.ENABLE_ATR_FILTER', False),
            ('trading_bot.ENABLE_VOLUME_FILTER', False)
        ]
        
        # Temporarily patch settings
        original_values = {}
        for setting, value in with_patches:
            module_name, attr_name = setting.rsplit('.', 1)
            module = sys.modules[module_name]
            original_values[setting] = getattr(module, attr_name)
            setattr(module, attr_name, value)
        
        try:
            return self.strategy.check_buy_signal(symbol, analysis, current_price, mock_client)
        finally:
            # Restore original values
            for setting, original_value in original_values.items():
                module_name, attr_name = setting.rsplit('.', 1)
                module = sys.modules[module_name]
                setattr(module, attr_name, original_value)
    
    def execute_buy(self, symbol, price, timestamp):
        """
        Simulate buying a position
        
        Args:
            symbol (str): Trading symbol
            price (float): Entry price
            timestamp (datetime): Entry time
        """
        if self.balance < self.trade_amount:
            print(f"   ❌ Insufficient balance: ${self.balance:.2f} < ${self.trade_amount:.2f}")
            return False
        
        quantity = self.trade_amount / price
        self.positions[symbol] = {
            'quantity': quantity,
            'entry_price': price,
            'entry_time': timestamp,
            'stop_loss': price * 0.95,  # 5% stop loss
            'take_profit': price * 1.1  # 10% take profit
        }
        
        self.balance -= self.trade_amount
        self.total_trades += 1
        
        print(f"   🟢 BUY {symbol}: {quantity:.6f} @ ${price:.2f} (${self.trade_amount:.2f})")
        print(f"      Stop Loss: ${self.positions[symbol]['stop_loss']:.2f}")
        print(f"      Take Profit: ${self.positions[symbol]['take_profit']:.2f}")
        print(f"      Remaining Balance: ${self.balance:.2f}")
        
        return True
    
    def check_exit_conditions(self, symbol, current_price, timestamp):
        """
        Check if position should be closed (stop loss or take profit)
        
        Args:
            symbol (str): Trading symbol
            current_price (float): Current price
            timestamp (datetime): Current time
        """
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        # Check stop loss
        if current_price <= position['stop_loss']:
            pnl = (current_price - entry_price) * quantity
            self.balance += current_price * quantity
            self.total_pnl += pnl
            self.losing_trades += 1
            
            print(f"   🔴 STOP LOSS {symbol}: {quantity:.6f} @ ${current_price:.2f}")
            print(f"      PnL: ${pnl:.2f} ({((current_price / entry_price - 1) * 100):+.2f}%)")
            print(f"      Balance: ${self.balance:.2f}")
            
            self.trade_history.append({
                'symbol': symbol,
                'type': 'SELL',
                'reason': 'STOP_LOSS',
                'quantity': quantity,
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl': pnl,
                'timestamp': timestamp
            })
            
            del self.positions[symbol]
            
        # Check take profit
        elif current_price >= position['take_profit']:
            pnl = (current_price - entry_price) * quantity
            self.balance += current_price * quantity
            self.total_pnl += pnl
            self.winning_trades += 1
            
            print(f"   🟢 TAKE PROFIT {symbol}: {quantity:.6f} @ ${current_price:.2f}")
            print(f"      PnL: ${pnl:.2f} ({((current_price / entry_price - 1) * 100):+.2f}%)")
            print(f"      Balance: ${self.balance:.2f}")
            
            self.trade_history.append({
                'symbol': symbol,
                'type': 'SELL',
                'reason': 'TAKE_PROFIT',
                'quantity': quantity,
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl': pnl,
                'timestamp': timestamp
            })
            
            del self.positions[symbol]
    
    def run_simulation(self, symbol, days=7, interval='4h', use_real_data=True):
        """
        Run complete trading simulation
        
        Args:
            symbol (str): Trading symbol
            days (int): Number of days to simulate
            interval (str): Time interval
            use_real_data (bool): If True, use real Binance data; if False, use simulated data
        """
        print(f"\n🚀 STARTING TRADING SIMULATION")
        print(f"════════════════════════════════════════════")
        print(f"Symbol: {symbol}")
        print(f"Period: {days} days ({interval} intervals)")
        print(f"Initial Balance: ${self.initial_balance:.2f}")
        print(f"Trade Amount: ${self.trade_amount:.2f}")
        print(f"Strategy: {self.strategy.name}")
        print(f"Data Source: {'🌍 REAL Binance Data' if use_real_data else '🎲 Simulated Data'}")
        
        # Generate or fetch market data
        df = self.simulate_market_data(symbol, days, interval, use_real_data)
        
        if df is None or len(df) == 0:
            print("❌ No market data available. Simulation aborted.")
            return
        
        print(f"\n📈 RUNNING SIMULATION...")
        print(f"────────────────────────────────────────────")
        
        # Simulate each candle
        for i in range(len(df)):
            current_candle = df.iloc[i]
            current_price = current_candle['Close']
            timestamp = current_candle['Timestamp']
            
            # Check exit conditions for existing positions
            self.check_exit_conditions(symbol, current_price, timestamp)
            
            # Only look for new entries if not already in position
            if symbol not in self.positions and i % 20 == 0:  # Check every 20th candle to avoid spam
                analysis = self.analyze_candle(df, i)
                
                if analysis:
                    if self.check_buy_signal(symbol, analysis, current_price):
                        print(f"\n🎯 BUY SIGNAL DETECTED at {timestamp.strftime('%Y-%m-%d %H:%M')}")
                        self.execute_buy(symbol, current_price, timestamp)
        
        # Close any remaining positions at final price
        if self.positions:
            final_price = df.iloc[-1]['Close']
            final_timestamp = df.iloc[-1]['Timestamp']
            print(f"\n🔚 CLOSING REMAINING POSITIONS at final price ${final_price:.2f}")
            
            for symbol in list(self.positions.keys()):
                position = self.positions[symbol]
                quantity = position['quantity']
                entry_price = position['entry_price']
                pnl = (final_price - entry_price) * quantity
                
                self.balance += final_price * quantity
                self.total_pnl += pnl
                
                if pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1
                
                self.trade_history.append({
                    'symbol': symbol,
                    'type': 'SELL',
                    'reason': 'FINAL_CLOSE',
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'exit_price': final_price,
                    'pnl': pnl,
                    'timestamp': final_timestamp
                })
                
                print(f"   📍 FINAL CLOSE {symbol}: {quantity:.6f} @ ${final_price:.2f} (PnL: ${pnl:.2f})")
        
        self.print_results()
    
    def print_results(self):
        """Print simulation results and performance metrics"""
        print(f"\n📊 SIMULATION RESULTS")
        print(f"════════════════════════════════════════════")
        
        final_balance = self.balance
        total_return = final_balance - self.initial_balance
        return_pct = (total_return / self.initial_balance) * 100
        
        print(f"Initial Balance:     ${self.initial_balance:.2f}")
        print(f"Final Balance:       ${final_balance:.2f}")
        print(f"Total Return:        ${total_return:+.2f} ({return_pct:+.2f}%)")
        print(f"Total PnL:           ${self.total_pnl:+.2f}")
        
        print(f"\n📈 TRADING STATISTICS")
        print(f"────────────────────────────────────────────")
        print(f"Total Trades:        {self.total_trades}")
        print(f"Winning Trades:      {self.winning_trades}")
        print(f"Losing Trades:       {self.losing_trades}")
        
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
            print(f"Win Rate:            {win_rate:.1f}%")
            
            if self.trade_history:
                avg_win = np.mean([t['pnl'] for t in self.trade_history if t['pnl'] > 0]) if self.winning_trades > 0 else 0
                avg_loss = np.mean([t['pnl'] for t in self.trade_history if t['pnl'] < 0]) if self.losing_trades > 0 else 0
                
                print(f"Average Win:         ${avg_win:.2f}")
                print(f"Average Loss:        ${avg_loss:.2f}")
                
                if avg_loss != 0:
                    profit_factor = abs(avg_win * self.winning_trades / (avg_loss * self.losing_trades))
                    print(f"Profit Factor:       {profit_factor:.2f}")
        
        # Performance rating
        if return_pct > 10:
            rating = "🔥 EXCELLENT"
        elif return_pct > 5:
            rating = "🎯 GOOD" 
        elif return_pct > 0:
            rating = "✅ PROFITABLE"
        elif return_pct > -5:
            rating = "⚠️ BREAK-EVEN"
        else:
            rating = "❌ POOR"
        
        print(f"\n🏆 PERFORMANCE RATING: {rating}")
        
        if self.trade_history:
            print(f"\n📋 TRADE HISTORY:")
            print(f"────────────────────────────────────────────")
            for i, trade in enumerate(self.trade_history[-5:], 1):  # Show last 5 trades
                timestamp = trade['timestamp'].strftime('%m/%d %H:%M')
                print(f"{i}. {trade['symbol']} {trade['reason']}: ${trade['pnl']:+.2f} @ ${trade['exit_price']:.2f} ({timestamp})")


def main():
    """Main function to run simulation"""
    parser = argparse.ArgumentParser(description='Trading Bot Simulator with Real Binance Data')
    parser.add_argument('--symbol', default='BTCUSDT', help='Trading symbol (default: BTCUSDT)')
    parser.add_argument('--days', type=int, default=7, help='Number of days to simulate (default: 7)')
    parser.add_argument('--interval', default='4h', help='Time interval: 15m, 1h, 4h, 1d (default: 4h)')
    parser.add_argument('--balance', type=float, default=1000.0, help='Initial balance (default: 1000)')
    parser.add_argument('--trade-amount', type=float, default=15.0, help='Trade amount per position (default: 15)')
    parser.add_argument('--symbols', help='Multiple symbols separated by comma for comparison')
    parser.add_argument('--simulated', action='store_true', help='Use simulated data instead of real Binance data')
    parser.add_argument('--testnet', action='store_true', help='Use Binance testnet (limited historical data)')
    
    args = parser.parse_args()
    
    # Set environment variable for testnet if specified
    if args.testnet:
        os.environ['USE_TESTNET'] = 'True'
        print("🧪 Using Binance TESTNET (limited historical data available)")
    else:
        os.environ['USE_TESTNET'] = 'False'
        print("🌍 Using Binance LIVE API for historical data")
    
    use_real_data = not args.simulated
    
    if use_real_data:
        print("📈 REAL DATA MODE: Fetching actual market data from Binance")
        print("💡 This provides accurate backtesting results based on real price movements")
    else:
        print("🎲 SIMULATION MODE: Using randomly generated market data")
        print("⚠️  Results may not reflect real market conditions")
    
    if args.symbols:
        # Multi-symbol simulation
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"\n🔄 RUNNING MULTI-SYMBOL SIMULATION")
        print(f"Symbols: {', '.join(symbols)}")
        
        results = {}
        for symbol in symbols:
            print(f"\n{'='*60}")
            simulator = TradingSimulator(args.balance, args.trade_amount)
            simulator.run_simulation(symbol, args.days, args.interval, use_real_data)
            
            # Store results for comparison
            final_balance = simulator.balance
            total_return = final_balance - args.balance
            return_pct = (total_return / args.balance) * 100
            
            results[symbol] = {
                'final_balance': final_balance,
                'total_return': total_return,
                'return_pct': return_pct,
                'total_trades': simulator.total_trades,
                'win_rate': (simulator.winning_trades / simulator.total_trades * 100) if simulator.total_trades > 0 else 0
            }
        
        # Print comparison summary
        if len(results) > 1:
            print(f"\n🏆 MULTI-SYMBOL COMPARISON SUMMARY")
            print(f"═════════════════════════════════════════════════════════════")
            print(f"{'Symbol':<10} {'Return':<12} {'Trades':<8} {'Win Rate':<10} {'Final Balance':<15}")
            print(f"─────────────────────────────────────────────────────────────")
            
            # Sort by return percentage
            sorted_results = sorted(results.items(), key=lambda x: x[1]['return_pct'], reverse=True)
            
            for symbol, data in sorted_results:
                print(f"{symbol:<10} {data['return_pct']:+7.2f}%    {data['total_trades']:<8} {data['win_rate']:6.1f}%    ${data['final_balance']:<14.2f}")
            
            best_symbol = sorted_results[0][0]
            best_return = sorted_results[0][1]['return_pct']
            print(f"\n🥇 Best Performer: {best_symbol} ({best_return:+.2f}%)")
            
    else:
        # Single symbol simulation
        simulator = TradingSimulator(args.balance, args.trade_amount)
        simulator.run_simulation(args.symbol, args.days, args.interval, use_real_data)


if __name__ == "__main__":
    main()
