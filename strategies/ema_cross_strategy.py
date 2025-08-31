"""
EMA Cross Strategy

This module implements a trading strategy based on EMA crossovers with RSI confirmation.
The strategy looks for bullish momentum while ensuring the entry point is near support.
"""

import logging
from typing import Dict, Any
from .base_strategy import BaseStrategy


class EMACrossStrategy(BaseStrategy):
    """
    EMA Cross Strategy with RSI confirmation.

    This strategy implements the following rules:
    1. Trend Confirmation: Price must be above the 50-EMA
    2. Bullish Momentum: The fast 9-EMA must be above the medium 21-EMA
    3. Healthy Momentum: RSI must be above 50 (bullish) but below 70 (not overbought)
    4. Good Entry: Price must be relatively close to the 21-EMA to avoid buying at the top
    """

    def __init__(self):
        """Initialize the EMA Cross Strategy."""
        super().__init__("EMA Cross Strategy")
        self.required_indicators = ['50_EMA', '9_EMA', '21_EMA', 'RSI_14']
        self.rsi_lower_bound = 50
        self.rsi_upper_bound = 70
        self.ema_support_tolerance = 0.02  # 2% tolerance from 21-EMA

    def check_buy_signal(self, symbol: str, analysis: Dict[str, Any], current_price: float) -> bool:
        """
        Check if the current market data constitutes a BUY signal based on EMA cross strategy.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT')
            analysis (Dict[str, Any]): Dictionary containing technical analysis data
            current_price (float): The current price of the symbol

        Returns:
            bool: True if a buy signal is detected, False otherwise
        """
        # Validate required data is present
        if not self.validate_analysis_data(analysis, self.required_indicators):
            logging.warning(
                f"[{symbol}] Missing required indicators for EMA Cross Strategy")
            return False

        # Strategy Rule 1: Trend Confirmation - Price must be above 50-EMA
        price_above_50ema = current_price > analysis['50_EMA']

        # Strategy Rule 2: Bullish Momentum - 9-EMA must be above 21-EMA
        emas_in_uptrend = analysis['9_EMA'] > analysis['21_EMA']

        # Strategy Rule 3: Healthy Momentum - RSI between 50 and 70
        rsi_is_healthy = self.rsi_lower_bound < analysis['RSI_14'] < self.rsi_upper_bound

        # Strategy Rule 4: Good Entry - Price within 2% of 21-EMA (support level)
        price_near_support = (
            abs(current_price - analysis['21_EMA']) / analysis['21_EMA']
        ) < self.ema_support_tolerance

        # Log detailed analysis for debugging
        self._log_signal_analysis(symbol, current_price, analysis, {
            'price_above_50ema': price_above_50ema,
            'emas_in_uptrend': emas_in_uptrend,
            'rsi_is_healthy': rsi_is_healthy,
            'price_near_support': price_near_support
        })

        # All conditions must be met for a buy signal
        if price_above_50ema and emas_in_uptrend and rsi_is_healthy and price_near_support:
            logging.info(
                f"[{symbol}] BUY SIGNAL FOUND! All EMA Cross Strategy conditions met.")
            return True

        return False

    def get_strategy_description(self) -> str:
        """
        Get a description of the EMA Cross Strategy rules.

        Returns:
            str: A human-readable description of the strategy
        """
        return f"""
        {self.name} Rules:
        1. Trend Confirmation: Price must be above the 50-EMA
        2. Bullish Momentum: The 9-EMA must be above the 21-EMA
        3. Healthy Momentum: RSI must be between {self.rsi_lower_bound} and {self.rsi_upper_bound}
        4. Good Entry: Price must be within {self.ema_support_tolerance*100}% of the 21-EMA
        """

    def _log_signal_analysis(self, symbol: str, current_price: float,
                             analysis: Dict[str, Any], conditions: Dict[str, bool]) -> None:
        """
        Log detailed analysis of signal conditions for debugging.

        Args:
            symbol (str): The trading symbol
            current_price (float): Current price
            analysis (Dict[str, Any]): Technical analysis data
            conditions (Dict[str, bool]): Boolean results of each condition
        """
        logging.debug(f"[{symbol}] EMA Cross Strategy Analysis:")
        logging.debug(f"  Current Price: ${current_price:.4f}")
        logging.debug(
            f"  50-EMA: ${analysis['50_EMA']:.4f} | Above: {conditions['price_above_50ema']}")
        logging.debug(f"  21-EMA: ${analysis['21_EMA']:.4f}")
        logging.debug(
            f"  9-EMA: ${analysis['9_EMA']:.4f} | Above 21-EMA: {conditions['emas_in_uptrend']}")
        logging.debug(
            f"  RSI: {analysis['RSI_14']:.2f} | Healthy: {conditions['rsi_is_healthy']}")

        distance_from_21ema = abs(
            current_price - analysis['21_EMA']) / analysis['21_EMA']
        logging.debug(
            f"  Distance from 21-EMA: {distance_from_21ema*100:.2f}% | Near Support: {conditions['price_near_support']}")

    def configure_parameters(self, rsi_lower: int = None, rsi_upper: int = None,
                             ema_tolerance: float = None) -> None:
        """
        Configure strategy parameters.

        Args:
            rsi_lower (int, optional): Lower bound for RSI
            rsi_upper (int, optional): Upper bound for RSI
            ema_tolerance (float, optional): Tolerance for distance from 21-EMA
        """
        if rsi_lower is not None:
            self.rsi_lower_bound = rsi_lower
        if rsi_upper is not None:
            self.rsi_upper_bound = rsi_upper
        if ema_tolerance is not None:
            self.ema_support_tolerance = ema_tolerance

        logging.info(
            f"EMA Cross Strategy parameters updated: RSI({self.rsi_lower_bound}-{self.rsi_upper_bound}), EMA tolerance: {self.ema_support_tolerance*100}%")
