"""
Core interfaces for the trading system.
Following the Interface Segregation Principle (ISP) of SOLID.
"""

from .interfaces import (
    IStrategy,
    IMarketDataProvider, 
    ITradeExecutor,
    IRiskManager,
    IPositionManager,
    INotificationService,
    ITechnicalAnalyzer
)

__all__ = [
    'IStrategy',
    'IMarketDataProvider',
    'ITradeExecutor', 
    'IRiskManager',
    'IPositionManager',
    'INotificationService',
    'ITechnicalAnalyzer'
]
