#!/usr/bin/env python3
"""
Automatic Account Balance Sync
Automatically syncs entire Binance account balance into active_trades file.
Fetches real balances and prices from Binance API.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path  
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    # Use proper config loading like the main bot
    from src.utils import load_config
    
    # Load config
    config = load_config()
    
    print("✅ Config loaded successfully")
    
except ImportError as e:
    print(f"⚠️  Could not load config: {e}")
    config = None

# Try to import Binance client
try:
    from binance.spot import Spot as Client
    from binance.error import ClientError
    api_available = True
    print("✅ Binance API loaded successfully")
except ImportError as e:
    print(f"⚠️  Could not load Binance API: {e}")
    api_available = False


def get_account_balances():
    """Get current account balances from Binance, filtered by USDT value > $1."""
    if not api_available or not config:
        return {}
        
    try:
        # Use config for API credentials and testnet setting
        if config.testnet:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret,
                base_url="https://testnet.binance.vision"
            )
        else:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
        
        account_info = client.account()
        
        balances = {}
        excluded_assets = {'USDT', 'BUSD', 'USDC', 'DAI', 'TUSD', 'PAX', 'USDS', 'BNB'}
        
        for balance in account_info['balances']:
            asset = balance['asset']
            free_balance = float(balance['free'])
            locked_balance = float(balance['locked'])
            total_balance = free_balance + locked_balance
            
            # Skip if balance is zero or asset is excluded
            if total_balance <= 0 or asset in excluded_assets:
                continue
            
            # Get USDT value for this asset
            try:
                symbol = f"{asset}USDT"
                ticker = client.ticker_price(symbol=symbol)
                price = float(ticker['price'])
                usdt_value = total_balance * price
                
                # Only include if USDT value > $1
                if usdt_value > 1.0:
                    balances[asset] = {
                        'free': free_balance,
                        'locked': locked_balance,
                        'total': total_balance,
                        'usdt_value': usdt_value,
                        'price': price
                    }
                    
            except Exception as e:
                # If we can't get price (no USDT pair), skip this asset
                print(f"   ⚠️ Skipping {asset}: No USDT pair or price error")
                continue
        
        return balances
        
    except ClientError as e:
        print(f"❌ Binance API Error: {e}")
        return {}
    except Exception as e:
        print(f"❌ Error getting balances: {e}")
        return {}


def get_trading_pairs(assets):
    """Get USDT trading pairs for assets."""
    if not api_available or not config:
        return {}
        
    try:
        # Use config for API credentials and testnet setting
        if config.testnet:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret,
                base_url="https://testnet.binance.vision"
            )
        else:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
        
        exchange_info = client.exchange_info()
        pairs = {}
        
        for symbol_info in exchange_info['symbols']:
            symbol = symbol_info['symbol']
            base_asset = symbol_info['baseAsset']
            quote_asset = symbol_info['quoteAsset']
            status = symbol_info['status']
            
            if (base_asset in assets and 
                quote_asset == 'USDT' and 
                status == 'TRADING'):
                pairs[base_asset] = symbol
        
        return pairs
        
    except Exception as e:
        print(f"❌ Error getting trading pairs: {e}")
        return {}


def get_current_price(symbol):
    """Get current price for a trading pair."""
    if not api_available or not config:
        return None
        
    try:
        # Use config for API credentials and testnet setting
        if config.testnet:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret,
                base_url="https://testnet.binance.vision"
            )
        else:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
        
        ticker = client.ticker_price(symbol=symbol)
        return float(ticker['price'])
        
    except ClientError as e:
        print(f"❌ Error getting price for {symbol}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error getting price for {symbol}: {e}")
        return None


def estimate_entry_price(symbol, quantity, current_price):
    """Estimate entry price from trade history or use current price."""
    if not api_available or not config:
        return current_price, datetime.now().isoformat()
        
    try:
        # Use config for API credentials and testnet setting
        if config.testnet:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret,
                base_url="https://testnet.binance.vision"
            )
        else:
            client = Client(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
        
        # Try to get recent trade history
        trades = client.my_trades(symbol=symbol, limit=50)
        
        if trades:
            # Look for recent buy trades that could match this position
            for trade in reversed(trades):  # Most recent first
                if trade['isBuyer']:
                    entry_price = float(trade['price'])
                    entry_time = datetime.fromtimestamp(trade['time'] / 1000).isoformat()
                    print(f"   📊 Found recent buy at ${entry_price:.6f}")
                    return entry_price, entry_time
        
        # Fallback to current price
        print(f"   📊 Using current price ${current_price:.6f}")
        return current_price, datetime.now().isoformat()
        
    except Exception as e:
        print(f"   ⚠️  Using current price due to error: {e}")
        return current_price, datetime.now().isoformat()


def create_trade_entry(symbol: str, quantity: float, entry_price: float) -> dict:
    """Create a new trade entry with calculated stop loss and take profit."""
    
    # Calculate stop loss and take profit (conservative 5% stop, 10% target)
    stop_loss = entry_price * 0.95
    take_profit = entry_price * 1.10
    
    return {
        "symbol": symbol,
        "quantity": quantity,
        "entry_price": entry_price,
        "current_price": entry_price,
        "entry_time": datetime.now().isoformat(),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "trailing_stop": None,
        "oco_order_id": None
    }


def sync_active_trades():
    """Automatically sync entire account balance to active trades file."""
    
    print("🔄 Auto-Syncing Account Balance to Active Trades")
    print("=" * 50)
    
    if not api_available:
        print("❌ Cannot sync without Binance API access")
        return
    
    trades_file = Path("data/active_trades_live.json")
    
    # Load current trades for comparison
    current_trades = {}
    if trades_file.exists():
        try:
            with open(trades_file, 'r') as f:
                content = f.read().strip()
                if content and not content.startswith('2025-'):
                    current_trades = json.loads(content)
        except Exception as e:
            print(f"⚠️  Error reading current trades: {e}")
    
    print(f"📄 Current active trades file has {len(current_trades)} positions")
    
    # Step 1: Get account balances
    print(f"\n� Fetching account balances...")
    balances = get_account_balances()
    
    if not balances:
        print("❌ Could not fetch account balances")
        return
    
    print(f"📊 Found {len(balances)} tradeable assets (>$1 USDT value):")
    for asset, balance_info in balances.items():
        print(f"   {asset}: {balance_info['total']:.6f} (${balance_info['usdt_value']:.2f})")
    
    # Step 2: Get trading pairs
    print(f"\n🔍 Finding USDT trading pairs...")
    pairs = get_trading_pairs(list(balances.keys()))
    
    print(f"📈 Available trading pairs:")
    for asset, symbol in pairs.items():
        print(f"   {asset} → {symbol}")
    
    # Step 3: Build new trades
    print(f"\n🔄 Building synchronized trades...")
    new_trades = {}
    
    for asset, balance_info in balances.items():
        if asset not in pairs:
            print(f"   ⚠️  Skipping {asset} - no USDT pair found")
            continue
        
        symbol = pairs[asset]
        quantity = balance_info['total']
        
        print(f"\n📊 Processing {symbol} ({asset}):")
        print(f"   Quantity: {quantity} (${balance_info['usdt_value']:.2f})")
        
        # Use price from balance info (already fetched)
        current_price = balance_info['price']
        if current_price == 0.0:
            print(f"   ❌ Could not get price for {symbol}")
            continue
        
        # Check if we already have this trade
        if symbol in current_trades:
            print(f"   ✅ Updating existing trade record")
            new_trades[symbol] = current_trades[symbol].copy()
            new_trades[symbol]['quantity'] = quantity  # Update quantity
            new_trades[symbol]['current_price'] = current_price  # Update current price
            # Preserve existing OCO order ID and other important fields
            # (entry_price, entry_time, stop_loss, take_profit, trailing_stop, oco_order_id are preserved)
        else:
            print(f"   🆕 Creating new trade record")
            
            # Estimate entry price from trade history
            entry_price, entry_time = estimate_entry_price(symbol, quantity, current_price)
            
            # Calculate stop loss and take profit
            stop_loss = entry_price * 0.95  # 5% stop loss
            take_profit = entry_price * 1.10  # 10% take profit
            
            new_trades[symbol] = {
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": entry_price,
                "current_price": current_price,
                "entry_time": entry_time,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "trailing_stop": None,
                "oco_order_id": None
            }
        
        profit_loss = (current_price - new_trades[symbol]['entry_price']) / new_trades[symbol]['entry_price'] * 100
        print(f"   💹 P&L: {profit_loss:+.2f}%")
    
    # Step 4: Show removed positions
    removed_positions = []
    for symbol in current_trades.keys():
        base_asset = symbol.replace('USDT', '')
        if base_asset not in balances:
            removed_positions.append(symbol)
    
    # Step 5: Show summary
    print(f"\n📊 SYNCHRONIZATION SUMMARY:")
    print(f"=" * 40)
    
    if removed_positions:
        print(f"🗑️  Removed from trades file (no longer held):")
        for symbol in removed_positions:
            base_asset = symbol.replace('USDT', '')
            print(f"   • {symbol} ({base_asset})")
    
    print(f"\n📈 Final active trades ({len(new_trades)} positions):")
    total_value = 0.0
    for symbol, trade in new_trades.items():
        asset = symbol.replace('USDT', '')
        value = trade['quantity'] * trade['current_price']
        total_value += value
        profit_loss = (trade['current_price'] - trade['entry_price']) / trade['entry_price'] * 100
        
        print(f"   {symbol}: {trade['quantity']:.2f} {asset}")
        print(f"      Entry: ${trade['entry_price']:.6f}, Current: ${trade['current_price']:.6f}")
        print(f"      Value: ${value:.2f}, P&L: {profit_loss:+.2f}%")
        print(f"      Stop: ${trade['stop_loss']:.6f}, Target: ${trade['take_profit']:.6f}")
        print()
    
    print(f"💰 Total Portfolio Value: ${total_value:.2f}")
    
    # Step 6: Confirm save
    confirm = input(f"💾 Save synchronized trades to {trades_file}? (y/N): ").strip().lower()
    
    if confirm == 'y':
        try:
            # Create backup
            if trades_file.exists():
                backup_file = trades_file.with_suffix('.json.backup')
                import shutil
                shutil.copy2(trades_file, backup_file)
                print(f"📄 Backup created: {backup_file}")
            
            # Save new trades
            trades_file.parent.mkdir(exist_ok=True)
            with open(trades_file, 'w') as f:
                json.dump(new_trades, f, indent=2)
            
            print(f"✅ Active trades synchronized successfully!")
            print(f"📁 File updated: {trades_file}")
            
            print(f"\n🚀 WHAT'S NEXT:")
            print(f"1. 🤖 Start trading bot: python main.py")
            print(f"2. 🛡️  Bot will place OCO orders for unprotected positions")
            print(f"3. 🔄 Enhanced retry logic will handle balance issues")
            print(f"4. 📊 Real-time price updates and monitoring")
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
    else:
        print(f"❌ Sync cancelled - no changes saved")


if __name__ == "__main__":
    try:
        sync_active_trades()
    except KeyboardInterrupt:
        print(f"\n❌ Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
