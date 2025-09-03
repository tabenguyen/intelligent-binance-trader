"""
Market data models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd


@dataclass
class CandlestickData:
    """Represents a single candlestick data point."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str


@dataclass
class TechnicalAnalysis:
    """Container for technical analysis indicators."""
    symbol: str
    timestamp: datetime
    indicators: Dict[str, float]
    
    def get_indicator(self, name: str) -> Optional[float]:
        """Get a specific indicator value."""
        return self.indicators.get(name)
    
    def has_indicator(self, name: str) -> bool:
        """Check if an indicator exists."""
        return name in self.indicators


@dataclass
class MarketData:
    """Comprehensive market data for a symbol."""
    symbol: str
    current_price: float
    timestamp: datetime
    candlesticks: List[CandlestickData]
    technical_analysis: TechnicalAnalysis
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert candlesticks to pandas DataFrame."""
        data = []
        for candle in self.candlesticks:
            data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
        return pd.DataFrame(data)
    
    @property
    def latest_candle(self) -> Optional[CandlestickData]:
        """Get the most recent candlestick."""
        return self.candlesticks[-1] if self.candlesticks else None
