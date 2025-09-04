"""
Base Strategy - Abstract base class for all trading strategies.
Following the Open-Closed Principle (OCP) of SOLID.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.interfaces import IStrategy
from ..models import MarketData, TradingSignal, TradeDirection, StrategyConfig


class BaseStrategy(IStrategy):
    """
    Abstract base class for trading strategies.
    Implements common functionality while allowing extension for specific strategies.
    """
    
    def __init__(self, name: str, config: Optional[StrategyConfig] = None):
        """
        Initialize base strategy.
        
        Args:
            name: Strategy name
            config: Strategy configuration
        """
        self.name = name
        self.config = config or StrategyConfig(
            name=name,
            parameters={},
            timeframe="4h",
            enabled=True,
            confidence_threshold=0.7
        )
        self.enabled = self.config.enabled
    
    @abstractmethod
    def analyze(self, market_data: MarketData) -> Optional[TradingSignal]:
        """
        Analyze market data and generate trading signals.
        Must be implemented by concrete strategies.
        """
        pass
    
    def get_name(self) -> str:
        """Get strategy name."""
        return self.name
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters."""
        return self.config.parameters
    
    def is_enabled(self) -> bool:
        """Check if strategy is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable the strategy."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the strategy."""
        self.enabled = False
    
    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters."""
        self.config.parameters.update(parameters)
    
    def validate_signal(self, signal: TradingSignal) -> bool:
        """
        Validate a generated signal meets basic criteria.
        Can be overridden by concrete strategies.
        """
        if not signal:
            return False
        
        # Check confidence threshold
        if signal.confidence < self.config.confidence_threshold:
            return False
        
        # Check required fields
        if not signal.symbol or not signal.price or signal.price <= 0:
            return False
        
        # Check stop loss and take profit validity
        if signal.direction == TradeDirection.BUY:
            if signal.stop_loss and signal.stop_loss >= signal.price:
                return False
            if signal.take_profit and signal.take_profit <= signal.price:
                return False
        
        return True
    
    def create_signal(self, market_data: MarketData, direction: TradeDirection, 
                     confidence: float, stop_loss: Optional[float] = None,
                     take_profit: Optional[float] = None, 
                     core_conditions_count: int = 0) -> TradingSignal:
        """
        Create a trading signal with common fields populated.
        """
        return TradingSignal(
            symbol=market_data.symbol,
            direction=direction,
            price=market_data.current_price,
            confidence=confidence,
            timestamp=datetime.now(),
            strategy_name=self.name,
            indicators=market_data.technical_analysis.indicators.copy(),
            core_conditions_count=core_conditions_count,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def get_required_indicators(self) -> list:
        """
        Get list of required indicators for this strategy.
        Should be overridden by concrete strategies.
        """
        return []
    
    def validate_market_data(self, market_data: MarketData) -> bool:
        """
        Validate that market data contains required indicators.
        """
        required_indicators = self.get_required_indicators()
        available_indicators = market_data.technical_analysis.indicators.keys()
        
        for indicator in required_indicators:
            if indicator not in available_indicators:
                return False
        
        return True
    
    def __str__(self) -> str:
        """String representation of the strategy."""
        return f"{self.name} (enabled={self.enabled})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"enabled={self.enabled}, timeframe='{self.config.timeframe}')")
