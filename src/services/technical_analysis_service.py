"""
Technical Analysis Service - Single Responsibility: Calculate technical indicators.
"""

import logging
import pandas as pd
import pandas_ta as ta
from typing import List, Dict, Any, Callable
from datetime import datetime

from ..core.interfaces import ITechnicalAnalyzer
from ..models import TechnicalAnalysis


class TechnicalAnalysisService(ITechnicalAnalyzer):
    """
    Service responsible for calculating technical indicators.
    Uses pandas_ta for efficient calculation.
    """
    
    def __init__(self):
        """Initialize the technical analysis service."""
        self.logger = logging.getLogger(__name__)
        self.custom_indicators: Dict[str, Callable] = {}
    
    def calculate_indicators(self, symbol: str, data: List[List]) -> TechnicalAnalysis:
        """
        Calculate technical indicators from kline data.
        
        Args:
            symbol: Trading symbol
            data: Kline data from Binance API
            
        Returns:
            TechnicalAnalysis object with calculated indicators
        """
        try:
            # Convert to DataFrame
            df = self._klines_to_dataframe(data)
            
            # Calculate all indicators
            indicators = {}
            
            # EMAs
            indicators['12_EMA'] = ta.ema(df['close'], length=12).iloc[-1]
            indicators['26_EMA'] = ta.ema(df['close'], length=26).iloc[-1]
            indicators['55_EMA'] = ta.ema(df['close'], length=55).iloc[-1]
            
            # RSI
            indicators['RSI_21'] = ta.rsi(df['close'], length=21).iloc[-1]
            
            # MACD
            macd_data = ta.macd(df['close'])
            if macd_data is not None and len(macd_data.columns) >= 3:
                indicators['MACD'] = macd_data.iloc[-1, 0]  # MACD line
                indicators['MACD_Signal'] = macd_data.iloc[-1, 1]  # Signal line
                indicators['MACD_Histogram'] = macd_data.iloc[-1, 2]  # Histogram
            
            # Bollinger Bands
            bb_data = ta.bbands(df['close'], length=20)
            if bb_data is not None and len(bb_data.columns) >= 3:
                indicators['BB_Upper'] = bb_data.iloc[-1, 0]  # Upper band
                indicators['BB_Middle'] = bb_data.iloc[-1, 1]  # Middle band
                indicators['BB_Lower'] = bb_data.iloc[-1, 2]  # Lower band
            
            # ATR for volatility
            atr = ta.atr(df['high'], df['low'], df['close'], length=14)
            if atr is not None:
                indicators['ATR'] = atr.iloc[-1]
                # Calculate ATR percentile for volatility state
                atr_mean = atr.rolling(50).mean().iloc[-1]
                indicators['ATR_Percentile'] = indicators['ATR'] / atr_mean if atr_mean > 0 else 1.0
                
                # Determine volatility state
                if indicators['ATR_Percentile'] < 0.7:
                    indicators['Volatility_State'] = 'LOW'
                elif indicators['ATR_Percentile'] > 2.0:
                    indicators['Volatility_State'] = 'HIGH'
                else:
                    indicators['Volatility_State'] = 'NORMAL'
            
            # Volume analysis
            if len(df) >= 20:
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].rolling(20).mean().iloc[-1]
                indicators['Current_Volume'] = current_volume
                indicators['Avg_Volume_20'] = avg_volume
                indicators['Volume_Ratio'] = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Calculate custom indicators
            for name, calculator in self.custom_indicators.items():
                try:
                    indicators[name] = calculator(df)
                except Exception as e:
                    self.logger.warning(f"Error calculating custom indicator {name}: {e}")
            
            return TechnicalAnalysis(
                symbol=symbol,
                timestamp=datetime.now(),
                indicators=indicators
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol}: {e}")
            raise
    
    def add_indicator(self, name: str, calculator: Callable) -> None:
        """Add a custom indicator calculator."""
        self.custom_indicators[name] = calculator
        self.logger.info(f"Added custom indicator: {name}")
    
    def _klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """Convert klines data to pandas DataFrame."""
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Convert to appropriate types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def get_daily_trend_filter(self, symbol: str, data: List[List]) -> bool:
        """
        Check if price is above daily 50-EMA for trend confirmation.
        This is a specialized method for multi-timeframe analysis.
        """
        try:
            df = self._klines_to_dataframe(data)
            if len(df) < 50:
                return True  # Default to True if not enough data
                
            ema_50 = ta.ema(df['close'], length=50).iloc[-1]
            current_price = df['close'].iloc[-1]
            
            return current_price > ema_50
            
        except Exception as e:
            self.logger.warning(f"Error calculating daily trend filter for {symbol}: {e}")
            return True  # Default to True on error
