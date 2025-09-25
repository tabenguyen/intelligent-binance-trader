"""
Refactored strategy implementations following SOLID principles.
"""

from .base_strategy import BaseStrategy
from .ema_cross_strategy import EMACrossStrategy
from .adaptive_atr_strategy import AdaptiveATRStrategy

__all__ = [
    'BaseStrategy',
    'EMACrossStrategy',
    'AdaptiveATRStrategy'
]
