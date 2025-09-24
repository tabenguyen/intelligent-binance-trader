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
    # Used when position_sizing_method == "fixed" (percent of balance to allocate)
    fixed_allocation_percentage: float = 2.0
    # Minimum notional value in USDT for trade execution
    min_notional_usdt: float = 15.0
    # Minimum trade value in USDT
    min_trade_value_usdt: float = 20.0


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
    position_only_mode: bool = False  # If True, only update existing positions (for cronjob)
    
    # Trading Execution
    order_type: str = "market"  # "market" or "limit"
    limit_order_offset_percentage: float = 0.1  # For limit orders, offset from current price
    max_limit_order_retries: int = 5
    limit_order_retry_delay: int = 30  # seconds
    enable_oco_orders: bool = True  # One-Cancels-Other orders for stop loss and take profit
    
     # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Paths
    watchlist_file: str = "config/watchlist.json"
    active_trades_file: str = "data/active_trades.json"
    
    # Watchlist Management
    watchlist_top_movers_limit: int = 20  # Number of top movers to include in watchlist
    
    # Telegram Notifications
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_signal_group_id: Optional[str] = None
    enable_telegram_notifications: bool = False
    
    # Simulation Mode Configuration
    simulation_mode: bool = False
    simulation_balance: float = 10000.0  # Default $10k simulation balance
    simulation_use_signal_group: bool = True  # Use signal group for simulation notifications
    simulation_fixed_trade_value: float = 100.0  # Fixed trade value for simulation mode
    
    def get_mode_specific_watchlist_file(self) -> str:
        """Get watchlist file path based on trading mode."""
        if self.simulation_mode:
            return "config/watchlist_simulation.json"
        elif self.testnet:
            return "config/watchlist_testnet.json"
        else:
            return "config/watchlist_live.json"
    
    def get_mode_specific_active_trades_file(self) -> str:
        """Get active trades file path based on trading mode."""
        if self.simulation_mode:
            return "data/active_trades_simulation.json"
        elif self.testnet:
            return "data/active_trades_testnet.json"
        else:
            return "data/active_trades_live.json"
    
    def get_mode_specific_log_file(self) -> str:
        """Get log file path based on trading mode."""
        if self.simulation_mode:
            return "logs/output_simulation.log"
        elif self.testnet:
            return "logs/output_testnet.log"
        else:
            return "logs/output_live.log"
    
    @classmethod
    def from_env(cls) -> 'TradingConfig':
        """Create configuration from environment variables."""
        import os
        from ..utils.env_loader import load_environment, get_env, get_env_float, get_env_bool, get_env_int
        
        # Ensure environment variables are loaded
        load_environment()
        
        risk_config = RiskConfig(
            max_position_size=get_env_float("MAX_POSITION_SIZE", 1000.0),
            max_daily_loss=get_env_float("MAX_DAILY_LOSS", 50.0),
            max_drawdown=get_env_float("MAX_DRAWDOWN", 20.0),
            stop_loss_percentage=get_env_float("STOP_LOSS_PCT", 5.0),
            take_profit_percentage=get_env_float("TAKE_PROFIT_PCT", 10.0),
            risk_per_trade_percentage=get_env_float("RISK_PER_TRADE_PCT", 2.0),
            fixed_allocation_percentage=get_env_float("FIXED_ALLOCATION_PCT", 2.0),
            min_notional_usdt=get_env_float("MIN_NOTIONAL_USDT", 15.0),
            min_trade_value_usdt=get_env_float("MIN_TRADE_VALUE_USDT", 20.0)
        )
        
        return cls(
            api_key=get_env("BINANCE_API_KEY", ""),
            api_secret=get_env("BINANCE_API_SECRET", ""),
            testnet=get_env_bool("USE_TESTNET", True),
            symbols=get_env("SYMBOLS", "BTCUSDT,ETHUSDT").split(","),
            min_balance=get_env_float("MIN_USDT_BALANCE", 100.0),
            trade_amount=get_env_float("TRADE_AMOUNT", 15.0),
            timeframe=get_env("TIMEFRAME", "4h"),
            risk_config=risk_config,
            strategies=[],  # Will be populated separately
            log_level=get_env("LOG_LEVEL", "INFO"),
            
            # Trading execution options
            order_type=get_env("ORDER_TYPE", "market").lower(),
            limit_order_offset_percentage=get_env_float("LIMIT_ORDER_OFFSET_PCT", 0.1),
            max_limit_order_retries=get_env_int("MAX_LIMIT_ORDER_RETRIES", 5),
            limit_order_retry_delay=get_env_int("LIMIT_ORDER_RETRY_DELAY", 30),
            enable_oco_orders=get_env_bool("ENABLE_OCO_ORDERS", True),
            
            # Feature flags
            position_only_mode=get_env_bool("POSITION_ONLY_MODE", False),
            
            # Watchlist Management
            watchlist_top_movers_limit=get_env_int("WATCHLIST_TOP_MOVERS_LIMIT", 20),
            
            # Telegram Notifications
            telegram_bot_token=get_env("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=get_env("TELEGRAM_CHAT_ID"),
            telegram_signal_group_id=get_env("TELEGRAM_SIGNAL_GROUP_ID"),
            enable_telegram_notifications=get_env_bool("ENABLE_TELEGRAM_NOTIFICATIONS", False),
            
            # Simulation Mode Configuration  
            simulation_mode=get_env_bool("SIMULATION_MODE", False),
            simulation_balance=get_env_float("SIMULATION_BALANCE", 10000.0),
            simulation_use_signal_group=get_env_bool("SIMULATION_USE_SIGNAL_GROUP", True)
        )
