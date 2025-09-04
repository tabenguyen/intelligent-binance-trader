"""
Configuration management for the trading bot.
"""

import os
from pathlib import Path
from typing import List

from ..models import TradingConfig, RiskConfig, StrategyConfig
from .env_loader import get_env_int, get_env_float, get_env_bool


def load_config() -> TradingConfig:
    """Load configuration from environment and files."""
    # Load from environment
    config = TradingConfig.from_env()
    
    # Load watchlist
    watchlist_path = Path(config.watchlist_file)
    if watchlist_path.exists():
        config.symbols = load_watchlist(watchlist_path)
    
    # Add strategy configurations
    config.strategies = load_strategy_configs()
    
    return config


def load_watchlist(file_path: Path) -> List[str]:
    """Load symbols from watchlist file."""
    symbols = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('uv run'):
                    symbols.append(line)
        return symbols
    except Exception:
        # Return default symbols if file doesn't exist
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def load_strategy_configs() -> List[StrategyConfig]:
    """Load strategy configurations."""
    return [
        StrategyConfig(
            name="EMA Cross Strategy - 4H",
            parameters={
                'rsi_lower_bound': get_env_int('RSI_LOWER', 45),
                'rsi_upper_bound': get_env_int('RSI_UPPER', 75),
                'ema_support_tolerance': get_env_float('EMA_TOLERANCE', 0.03),
                'core_conditions_required': get_env_int('CORE_CONDITIONS_REQ', 1),
                'enable_daily_trend_filter': get_env_bool('ENABLE_DAILY_TREND', True),
                'enable_atr_filter': get_env_bool('ENABLE_ATR', True),
                'enable_volume_filter': get_env_bool('ENABLE_VOLUME', True),
                'min_volume_ratio': get_env_float('MIN_VOLUME_RATIO', 1.2)
            },
            timeframe="4h",
            enabled=True,
            confidence_threshold=get_env_float('CONFIDENCE_THRESHOLD', 0.7)
        )
    ]


def save_config(config: TradingConfig, file_path: str) -> None:
    """Save configuration to file."""
    # This would implement config serialization
    # For now, just log the configuration
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Configuration would be saved to {file_path}")


def validate_config(config: TradingConfig) -> bool:
    """Validate configuration."""
    if not config.api_key or not config.api_secret:
        return False
    
    if not config.symbols:
        return False
    
    if config.trade_amount <= 0:
        return False
    
    return True
