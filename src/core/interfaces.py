"""
Core interfaces for the trading system.
Following the Interface Segregation Principle (ISP) - each interface should be focused on a specific responsibility.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import (
    TradingSignal, 
    MarketData, 
    TechnicalAnalysis,
    Position, 
    Trade, 
    OrderResult,
    TradingConfig
)


class IStrategy(ABC):
    """Interface for trading strategies."""
    
    @abstractmethod
    def analyze(self, market_data: MarketData) -> Optional[TradingSignal]:
        """Analyze market data and generate trading signals."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        pass


class IMarketDataProvider(ABC):
    """Interface for market data providers."""
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        pass
    
    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int) -> List[List]:
        """Get candlestick data."""
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str, interval: str, limit: int) -> MarketData:
        """Get comprehensive market data."""
        pass


class ITechnicalAnalyzer(ABC):
    """Interface for technical analysis."""
    
    @abstractmethod
    def calculate_indicators(self, symbol: str, data: List[List]) -> TechnicalAnalysis:
        """Calculate technical indicators."""
        pass
    
    @abstractmethod
    def add_indicator(self, name: str, calculator: callable) -> None:
        """Add a custom indicator calculator."""
        pass


class ITradeExecutor(ABC):
    """Interface for trade execution."""
    
    @abstractmethod
    def execute_market_buy(self, symbol: str, quantity: float) -> OrderResult:
        """Execute a market buy order."""
        pass
    
    @abstractmethod
    def execute_market_sell(self, symbol: str, quantity: float) -> OrderResult:
        """Execute a market sell order."""
        pass
    
    @abstractmethod
    def execute_oco_order(self, symbol: str, quantity: float, 
                         stop_price: float, limit_price: float) -> OrderResult:
        """Execute an OCO (One-Cancels-Other) order."""
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an existing order."""
        pass
    
    @abstractmethod
    def get_oco_order_status(self, symbol: str, order_list_id: str) -> Optional[str]:
        """Get OCO order status from the exchange."""
        pass
    
    @abstractmethod
    def get_oco_order_details(self, symbol: str, order_list_id: str) -> Optional[dict]:
        """Get detailed OCO order information including individual order statuses."""
        pass


class IRiskManager(ABC):
    """Interface for risk management."""
    
    @abstractmethod
    def validate_trade(self, signal: TradingSignal, current_balance: float) -> bool:
        """Validate if a trade meets risk criteria."""
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: TradingSignal, balance: float) -> float:
        """Calculate appropriate position size."""
        pass
    
    @abstractmethod
    def calculate_stop_loss(self, signal: TradingSignal) -> float:
        """Calculate stop loss price."""
        pass
    
    @abstractmethod
    def calculate_take_profit(self, signal: TradingSignal) -> float:
        """Calculate take profit price."""
        pass


class IPositionManager(ABC):
    """Interface for position management."""
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get all active positions."""
        pass
    
    @abstractmethod
    def add_position(self, position: Position) -> None:
        """Add a new position."""
        pass
    
    @abstractmethod
    def update_position(self, symbol: str, current_price: float) -> None:
        """Update position with current price."""
        pass
    
    @abstractmethod
    def close_position(self, symbol: str, exit_price: float) -> Trade:
        """Close a position and return the completed trade."""
        pass


class INotificationService(ABC):
    """Interface for notifications."""
    
    @abstractmethod
    def send_trade_notification(self, trade: Trade) -> None:
        """Send notification for a completed trade."""
        pass
    
    @abstractmethod
    def send_signal_notification(self, signal: TradingSignal) -> None:
        """Send notification for a trading signal."""
        pass
    
    @abstractmethod
    def send_error_notification(self, error: str) -> None:
        """Send error notification."""
        pass
    
    def send_system_notification(self, message: str, level: str = "INFO") -> None:
        """Send system notification. Optional method with default implementation."""
        pass
