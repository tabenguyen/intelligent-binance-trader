"""
Configuration models for the trading system.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class RiskConfig:
    """Risk management configuration."""
    max_position_size: float
    max_daily_loss: float
    max_drawdown: float
    stop_loss_percentage: float
    take_profit_percentage: float
    trailing_stop_percentage: Optional[float] = None
    position_sizing_method: str = "fixed"
    risk_per_trade_percentage: float = 2.0


@dataclass
class StrategyConfig:
    """Strategy-specific configuration."""
    name: str
    parameters: Dict[str, Any]
    timeframe: str
    enabled: bool = True
    confidence_threshold: float = 0.7


@dataclass
class TradingConfig:
    """Main trading configuration."""
    # Required fields first
    api_key: str
    api_secret: str
    symbols: List[str]
    risk_config: RiskConfig
    strategies: List[StrategyConfig]
    
    # Optional fields with defaults
    testnet: bool = True
    base_currency: str = "USDT"
    min_balance: float = 100.0
    trade_amount: float = 15.0
    scan_interval: int = 3600  # seconds
    timeframe: str = "4h"
    
    # Feature Flags
    enable_daily_trend_filter: bool = True
    enable_atr_filter: bool = True
    enable_volume_filter: bool = True
    enable_advanced_exits: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Paths
    watchlist_file: str = "config/watchlist.txt"
    active_trades_file: str = "data/active_trades.txt"
    
    @classmethod
    def from_env(cls) -> 'TradingConfig':
        """Create configuration from environment variables."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        risk_config = RiskConfig(
            max_position_size=float(os.getenv("MAX_POSITION_SIZE", "100.0")),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "50.0")),
            max_drawdown=float(os.getenv("MAX_DRAWDOWN", "20.0")),
            stop_loss_percentage=float(os.getenv("STOP_LOSS_PCT", "5.0")),
            take_profit_percentage=float(os.getenv("TAKE_PROFIT_PCT", "10.0")),
            risk_per_trade_percentage=float(os.getenv("RISK_PER_TRADE_PCT", "2.0"))
        )
        
        return cls(
            api_key=os.getenv("BINANCE_API_KEY", ""),
            api_secret=os.getenv("BINANCE_API_SECRET", ""),
            testnet=os.getenv("USE_TESTNET", "true").lower() == "true",
            symbols=os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT").split(","),
            min_balance=float(os.getenv("MIN_BALANCE", "100.0")),
            trade_amount=float(os.getenv("TRADE_AMOUNT", "15.0")),
            timeframe=os.getenv("TIMEFRAME", "4h"),
            risk_config=risk_config,
            strategies=[],  # Will be populated separately
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
