"""
Base Strategy Abstract Class

This module defines the abstract base class for all trading strategies.
Each strategy must implement the check_buy_signal method to determine
when to enter a trade based on market analysis.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    All trading strategies must inherit from this class and implement
    the check_buy_signal method according to their specific logic.
    """

    def __init__(self, name: str):
        """
        Initialize the strategy with a name.

        Args:
            name (str): The name of the strategy
        """
        self.name = name

    @abstractmethod
    def check_buy_signal(self, symbol: str, analysis: Dict[str, Any], current_price: float) -> bool:
        """
        Check if the current market data constitutes a BUY signal.

        This method must be implemented by each strategy to define their
        specific entry conditions.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT')
            analysis (Dict[str, Any]): Dictionary containing technical analysis data
                Expected keys may include:
                - '9_EMA': 9-period Exponential Moving Average
                - '21_EMA': 21-period Exponential Moving Average
                - '50_EMA': 50-period Exponential Moving Average
                - 'RSI_14': 14-period Relative Strength Index
                - 'Last_Swing_High': Recent swing high price
                - 'Last_Swing_Low': Recent swing low price
            current_price (float): The current price of the symbol

        Returns:
            bool: True if a buy signal is detected, False otherwise
        """
        pass

    @abstractmethod
    def get_strategy_description(self) -> str:
        """
        Get a description of the strategy rules.

        Returns:
            str: A human-readable description of the strategy
        """
        pass

    def validate_analysis_data(self, analysis: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate that the analysis dictionary contains all required keys.

        Args:
            analysis (Dict[str, Any]): The analysis data to validate
            required_keys (list): List of required keys

        Returns:
            bool: True if all required keys are present, False otherwise
        """
        return all(key in analysis for key in required_keys)
