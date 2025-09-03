"""
Refactored strategy implementations following SOLID principles.
"""

from .base_strategy import BaseStrategy
from .ema_cross_strategy import EMACrossStrategy

__all__ = [
    'BaseStrategy',
    'EMACrossStrategy'
]
