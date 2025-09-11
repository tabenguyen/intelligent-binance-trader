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
            
            # Validate minimum data requirements
            if df is None or len(df) < 26:
                self.logger.warning(f"Insufficient data for {symbol}: {len(df) if df is not None else 0} candles (need 26+)")
                return self._create_empty_analysis(symbol)
            
            # Calculate all indicators with error handling
            indicators = {}
            
            # EMAs with safe calculation
            indicators.update(self._safe_calculate_emas(df))
            
            # RSI with safe calculation
            indicators.update(self._safe_calculate_rsi(df))
            
            # MACD with safe calculation
            indicators.update(self._safe_calculate_macd(df))
            
            # Bollinger Bands with safe calculation
            indicators.update(self._safe_calculate_bollinger_bands(df))
            
            # ATR and volatility analysis
            indicators.update(self._safe_calculate_atr(df))
            
            # Volume analysis
            indicators.update(self._safe_calculate_volume(df))
            
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
            return self._create_empty_analysis(symbol)
    
    def _safe_calculate_emas(self, df: pd.DataFrame) -> Dict[str, float]:
        """Safely calculate EMA indicators."""
        indicators = {}
        try:
            # EMA 12
            ema_12 = ta.ema(df['close'], length=12)
            if ema_12 is not None and len(ema_12) > 0:
                indicators['12_EMA'] = float(ema_12.iloc[-1])
            
            # EMA 26
            ema_26 = ta.ema(df['close'], length=26)
            if ema_26 is not None and len(ema_26) > 0:
                indicators['26_EMA'] = float(ema_26.iloc[-1])
            
            # EMA 55 - This was missing!
            if len(df) >= 55:
                ema_55 = ta.ema(df['close'], length=55)
                if ema_55 is not None and len(ema_55) > 0:
                    indicators['55_EMA'] = float(ema_55.iloc[-1])
            else:
                # If insufficient data for 55-EMA, use 26-EMA as fallback
                if '26_EMA' in indicators:
                    indicators['55_EMA'] = indicators['26_EMA'] * 0.98  # Slightly lower estimate
                    
        except Exception as e:
            self.logger.warning(f"Error calculating EMAs: {e}")
        
        return indicators
    
    def _safe_calculate_rsi(self, df: pd.DataFrame) -> Dict[str, float]:
        """Safely calculate RSI indicator."""
        indicators = {}
        try:
            if len(df) >= 21:
                rsi = ta.rsi(df['close'], length=21)
                if rsi is not None and len(rsi) > 0:
                    indicators['RSI_21'] = float(rsi.iloc[-1])
        except Exception as e:
            self.logger.warning(f"Error calculating RSI: {e}")
        
        return indicators
    
    def _safe_calculate_macd(self, df: pd.DataFrame) -> Dict[str, float]:
        """Safely calculate MACD indicators."""
        indicators = {}
        try:
            if len(df) >= 34:  # Need enough data for MACD (26 + 9)
                macd_data = ta.macd(df['close'])
                if macd_data is not None and len(macd_data.columns) >= 3 and len(macd_data) > 0:
                    indicators['MACD'] = float(macd_data.iloc[-1, 0])  # MACD line
                    indicators['MACD_Signal'] = float(macd_data.iloc[-1, 1])  # Signal line
                    indicators['MACD_Histogram'] = float(macd_data.iloc[-1, 2])  # Histogram
        except Exception as e:
            self.logger.warning(f"Error calculating MACD: {e}")
        
        return indicators
    
    def _safe_calculate_bollinger_bands(self, df: pd.DataFrame) -> Dict[str, float]:
        """Safely calculate Bollinger Bands."""
        indicators = {}
        try:
            if len(df) >= 20:
                bb_data = ta.bbands(df['close'], length=20)
                if bb_data is not None and len(bb_data.columns) >= 3 and len(bb_data) > 0:
                    indicators['BB_Upper'] = float(bb_data.iloc[-1, 0])  # Upper band
                    indicators['BB_Middle'] = float(bb_data.iloc[-1, 1])  # Middle band
                    indicators['BB_Lower'] = float(bb_data.iloc[-1, 2])  # Lower band
        except Exception as e:
            self.logger.warning(f"Error calculating Bollinger Bands: {e}")
        
        return indicators
    
    def _safe_calculate_atr(self, df: pd.DataFrame) -> Dict[str, float]:
        """Safely calculate ATR and volatility indicators."""
        indicators = {}
        try:
            if len(df) >= 14:
                atr = ta.atr(df['high'], df['low'], df['close'], length=14)
                if atr is not None and len(atr) > 0:
                    atr_value = float(atr.iloc[-1])
                    indicators['ATR'] = atr_value
                    
                    # Calculate ATR percentile for volatility state (as percentage)
                    current_price = float(df['close'].iloc[-1])
                    atr_percentage = (atr_value / current_price) * 100 if current_price > 0 else 0
                    indicators['ATR_Percentile'] = atr_percentage
                        
                    # Determine volatility state based on ATR percentage
                    if atr_percentage < 0.5:  # Low volatility
                        indicators['Volatility_State'] = 'LOW'
                    elif atr_percentage > 2.0:  # High volatility
                        indicators['Volatility_State'] = 'HIGH'
                    else:
                        indicators['Volatility_State'] = 'NORMAL'
        except Exception as e:
            self.logger.warning(f"Error calculating ATR: {e}")
        
        return indicators
    
    def _safe_calculate_volume(self, df: pd.DataFrame) -> Dict[str, float]:
        """Safely calculate volume indicators."""
        indicators = {}
        try:
            if len(df) >= 20:
                current_volume = float(df['volume'].iloc[-1])
                avg_volume = float(df['volume'].rolling(20).mean().iloc[-1])
                
                indicators['Current_Volume'] = current_volume
                indicators['Avg_Volume_20'] = avg_volume
                indicators['Volume_Ratio'] = current_volume / avg_volume if avg_volume > 0 else 1.0
        except Exception as e:
            self.logger.warning(f"Error calculating volume indicators: {e}")
        
        return indicators
    
    def _create_empty_analysis(self, symbol: str) -> TechnicalAnalysis:
        """Create empty technical analysis for insufficient data."""
        return TechnicalAnalysis(
            symbol=symbol,
            timestamp=datetime.now(),
            indicators={}
        )
    
    def add_indicator(self, name: str, calculator: Callable) -> None:
        """Add a custom indicator calculator."""
        self.custom_indicators[name] = calculator
        self.logger.info(f"Added custom indicator: {name}")
    
    def _klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """Convert klines data to pandas DataFrame with error handling."""
        try:
            if not klines or len(klines) == 0:
                self.logger.warning("Empty klines data received")
                return None
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Validate we have the minimum required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_columns):
                self.logger.error(f"Missing required columns in klines data: {df.columns.tolist()}")
                return None
            
            # Convert to appropriate types with error handling
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
            
            for col in required_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Check for NaN values after conversion
                if df[col].isna().any():
                    self.logger.warning(f"Found NaN values in column {col} after conversion")
                    # Fill NaN values with forward fill, then backward fill
                    df[col] = df[col].ffill().bfill()
            
            # Remove any rows that still have NaN values
            initial_len = len(df)
            df = df.dropna(subset=required_columns)
            
            if len(df) < initial_len:
                self.logger.warning(f"Dropped {initial_len - len(df)} rows with NaN values")
            
            if len(df) == 0:
                self.logger.error("No valid data remaining after cleaning")
                return None
                
            return df
            
        except Exception as e:
            self.logger.error(f"Error converting klines to dataframe: {e}")
            return None
    
    def get_daily_trend_filter(self, symbol: str, data: List[List]) -> bool:
        """
        Check if price is above daily 50-EMA for trend confirmation.
        This is a specialized method for multi-timeframe analysis.
        """
        try:
            df = self._klines_to_dataframe(data)
            if df is None or len(df) < 50:
                self.logger.warning(f"Insufficient data for daily trend filter {symbol}: {len(df) if df is not None else 0} candles")
                return True  # Default to True if not enough data
                
            ema_50 = ta.ema(df['close'], length=50)
            if ema_50 is None or len(ema_50) == 0:
                self.logger.warning(f"Could not calculate EMA-50 for {symbol}")
                return True
                
            ema_50_value = float(ema_50.iloc[-1])
            current_price = float(df['close'].iloc[-1])
            
            is_above_ema = current_price > ema_50_value
            self.logger.info(f"Daily trend filter for {symbol}: Price ${current_price:.4f} {'above' if is_above_ema else 'below'} EMA-50 ${ema_50_value:.4f}")
            
            return is_above_ema
            
        except Exception as e:
            self.logger.warning(f"Error calculating daily trend filter for {symbol}: {e}")
            return True  # Default to True on error
