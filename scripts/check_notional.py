#!/usr/bin/env python3
"""
Quick script to check minimum notional requirements for trading pairs
"""

import sys
sys.path.append('..')

from binance.spot import Spot as Client
from binance.error import ClientError
from src.utils.env_loader import get_env, get_env_bool

USE_TESTNET = get_env_bool("USE_TESTNET", True)
API_KEY = get_env("BINANCE_API_KEY")
API_SECRET = get_env("BINANCE_API_SECRET")

def get_symbol_info(client, symbol):
    """Get detailed symbol information including filters."""
    try:
        exchange_info = client.exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                return s
        return None
    except ClientError as e:
        print(f"Error fetching exchange info: {e}")
        return None

def main():
    if not API_KEY or not API_SECRET:
        print("Please set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file")
        return

    # Initialize client
    if USE_TESTNET:
        base_url = "https://testnet.binance.vision"
        print("Using TESTNET")
    else:
        base_url = "https://api.binance.com"
        print("Using LIVE API")

    client = Client(API_KEY, API_SECRET, base_url=base_url)
    
    # Check BTCUSDT requirements
    symbol = "BTCUSDT"
    print(f"\nChecking requirements for {symbol}:")
    
    symbol_info = get_symbol_info(client, symbol)
    if not symbol_info:
        print(f"Could not get information for {symbol}")
        return
    
    print(f"Status: {symbol_info['status']}")
    print(f"Base Asset: {symbol_info['baseAsset']}")
    print(f"Quote Asset: {symbol_info['quoteAsset']}")
    
    print("\nFilters:")
    for filter_info in symbol_info['filters']:
        filter_type = filter_info['filterType']
        print(f"  {filter_type}:")
        
        if filter_type == 'PRICE_FILTER':
            print(f"    Min Price: {filter_info['minPrice']}")
            print(f"    Max Price: {filter_info['maxPrice']}")
            print(f"    Tick Size: {filter_info['tickSize']}")
        
        elif filter_type == 'LOT_SIZE':
            print(f"    Min Qty: {filter_info['minQty']}")
            print(f"    Max Qty: {filter_info['maxQty']}")
            print(f"    Step Size: {filter_info['stepSize']}")
        
        elif filter_type in ['NOTIONAL', 'MIN_NOTIONAL']:
            print(f"    Min Notional: {filter_info['minNotional']}")
            if 'applyToMarket' in filter_info:
                print(f"    Apply to Market: {filter_info['applyToMarket']}")
            if 'avgPriceMins' in filter_info:
                print(f"    Avg Price Mins: {filter_info['avgPriceMins']}")
        
        elif filter_type == 'MARKET_LOT_SIZE':
            print(f"    Min Qty (Market): {filter_info['minQty']}")
            print(f"    Max Qty (Market): {filter_info['maxQty']}")
            print(f"    Step Size (Market): {filter_info['stepSize']}")
    
    # Get current price to calculate example trade
    try:
        ticker = client.ticker_price(symbol=symbol)
        current_price = float(ticker['price'])
        print(f"\nCurrent Price: ${current_price:.2f}")
        
        # Calculate example trades
        trade_amounts = [10.0, 15.0, 20.0, 25.0]
        print(f"\nExample trade calculations:")
        for amount in trade_amounts:
            quantity = amount / current_price
            trade_value = quantity * current_price
            print(f"  ${amount:.2f} USDT = {quantity:.6f} BTC (Value: ${trade_value:.2f})")
            
    except ClientError as e:
        print(f"Error getting current price: {e}")

if __name__ == "__main__":
    main()
