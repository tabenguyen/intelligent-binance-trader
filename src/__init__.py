"""
Trading Bot - A SOLID-principles based cryptocurrency trading system.

This package provides a modular, extensible trading bot architecture following
SOLID principles for maintainable and testable code.
"""

from .trading_bot import TradingBot
from .models import TradingConfig
from .utils import load_config, setup_logging

__version__ = "2.0.0"
__author__ = "Trading Bot Team"

__all__ = [
    'TradingBot',
    'TradingConfig', 
    'load_config',
    'setup_logging'
]
