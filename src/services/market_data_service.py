"""
Market Data Service - Single Responsibility: Fetch and provide market data.
"""

import logging
from typing import List, Optional
from datetime import datetime
from binance.spot import Spot
from binance.error import ClientError

from ..core.interfaces import IMarketDataProvider
from ..models import MarketData, CandlestickData, TechnicalAnalysis


class BinanceMarketDataService(IMarketDataProvider):
    """
    Binance implementation of market data provider.
    Responsible only for fetching market data from Binance API.
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """Initialize Binance client."""
        if testnet:
            self.client = Spot(
                api_key=api_key,
                api_secret=api_secret,
                base_url="https://testnet.binance.vision"
            )
        else:
            self.client = Spot(
                api_key=api_key,
                api_secret=api_secret
            )
        self.logger = logging.getLogger(__name__)
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        try:
            ticker = self.client.ticker_price(symbol)
            return float(ticker['price'])
        except ClientError as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[List]:
        """Get candlestick data from Binance."""
        try:
            klines = self.client.klines(symbol, interval, limit=limit)
            return klines
        except ClientError as e:
            self.logger.error(f"Error fetching klines for {symbol}: {e}")
            raise
    
    def get_market_data(self, symbol: str, interval: str, limit: int) -> MarketData:
        """Get comprehensive market data for a symbol."""
        try:
            # Get current price
            current_price = self.get_current_price(symbol)
            
            # Get candlestick data
            klines = self.get_klines(symbol, interval, limit)
            
            # Convert to CandlestickData objects
            candlesticks = []
            for kline in klines:
                candlestick = CandlestickData(
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                    symbol=symbol
                )
                candlesticks.append(candlestick)
            
            # Get 24h stats
            stats = self.client.ticker_24hr(symbol)
            volume_24h = float(stats['volume'])
            price_change_24h = float(stats['priceChangePercent'])
            
            # Create empty technical analysis (will be populated by TechnicalAnalysisService)
            technical_analysis = TechnicalAnalysis(
                symbol=symbol,
                timestamp=datetime.now(),
                indicators={}
            )
            
            return MarketData(
                symbol=symbol,
                current_price=current_price,
                timestamp=datetime.now(),
                candlesticks=candlesticks,
                technical_analysis=technical_analysis,
                volume_24h=volume_24h,
                price_change_24h=price_change_24h
            )
            
        except ClientError as e:
            self.logger.error(f"Error fetching market data for {symbol}: {e}")
            raise
    
    def get_account_balance(self, asset: str = "USDT") -> float:
        """Get account balance for a specific asset."""
        try:
            account = self.client.account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except ClientError as e:
            self.logger.error(f"Error fetching balance: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol information including filters."""
        try:
            exchange_info = self.client.exchange_info()
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    return symbol_info
            raise ValueError(f"Symbol {symbol} not found")
        except ClientError as e:
            self.logger.error(f"Error fetching symbol info for {symbol}: {e}")
            raise
