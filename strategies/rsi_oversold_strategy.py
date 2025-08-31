"""
RSI Oversold Strategy

This module implements a simple RSI-based trading strategy that buys when RSI indicates oversold conditions.
This is an example of how to create alternative strategies using the base strategy framework.
"""

import logging
from typing import Dict, Any
from .base_strategy import BaseStrategy


class RSIOversoldStrategy(BaseStrategy):
    """
    RSI Oversold Strategy.

    This is a simple momentum reversal strategy that looks for oversold conditions:
    1. RSI must be below the oversold threshold (default: 30)
    2. Price must be above a longer-term moving average for trend confirmation
    3. Optional: Volume confirmation can be enabled
    """

    def __init__(self, oversold_threshold: float = 30, trend_ema_period: int = 50):
        """
        Initialize the RSI Oversold Strategy.

        Args:
            oversold_threshold (float): RSI level considered oversold (default: 30)
            trend_ema_period (int): EMA period for trend confirmation (default: 50)
        """
        super().__init__("RSI Oversold Strategy")
        self.oversold_threshold = oversold_threshold
        self.trend_ema_period = trend_ema_period
        self.required_indicators = ['RSI_14', f'{trend_ema_period}_EMA']
        self.use_volume_confirmation = False

    def check_buy_signal(self, symbol: str, analysis: Dict[str, Any], current_price: float) -> bool:
        """
        Check if RSI indicates an oversold buy opportunity.

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
                f"[{symbol}] Missing required indicators for RSI Oversold Strategy")
            return False

        # Strategy Rule 1: RSI must be oversold
        rsi_oversold = analysis['RSI_14'] < self.oversold_threshold

        # Strategy Rule 2: Price must be above long-term EMA (trend confirmation)
        trend_ema_key = f'{self.trend_ema_period}_EMA'
        price_above_trend = current_price > analysis[trend_ema_key]

        # Log analysis details
        logging.debug(f"[{symbol}] RSI Oversold Strategy Analysis:")
        logging.debug(
            f"  RSI: {analysis['RSI_14']:.2f} | Oversold (<{self.oversold_threshold}): {rsi_oversold}")
        logging.debug(
            f"  Price: ${current_price:.4f} | {self.trend_ema_period}-EMA: ${analysis[trend_ema_key]:.4f} | Above Trend: {price_above_trend}")

        # Both conditions must be met
        if rsi_oversold and price_above_trend:
            logging.info(
                f"[{symbol}] BUY SIGNAL FOUND! RSI oversold ({analysis['RSI_14']:.2f}) with trend confirmation.")
            return True

        # Log why signal was not triggered
        if not rsi_oversold:
            logging.debug(
                f"[{symbol}] No signal: RSI ({analysis['RSI_14']:.2f}) not oversold")
        elif not price_above_trend:
            logging.debug(
                f"[{symbol}] No signal: Price below {self.trend_ema_period}-EMA trend")

        return False

    def get_strategy_description(self) -> str:
        """
        Get a description of the RSI Oversold Strategy rules.

        Returns:
            str: A human-readable description of the strategy
        """
        return f"""
        {self.name} Rules:
        1. RSI Oversold: RSI must be below {self.oversold_threshold}
        2. Trend Confirmation: Price must be above the {self.trend_ema_period}-EMA
        
        This strategy looks for short-term oversold conditions in an uptrend,
        anticipating a bounce from oversold levels.
        """

    def configure_parameters(self, oversold_threshold: float = None,
                             trend_ema_period: int = None) -> None:
        """
        Configure strategy parameters.

        Args:
            oversold_threshold (float, optional): RSI level considered oversold
            trend_ema_period (int, optional): EMA period for trend confirmation
        """
        if oversold_threshold is not None:
            self.oversold_threshold = oversold_threshold

        if trend_ema_period is not None:
            self.trend_ema_period = trend_ema_period
            # Update required indicators when EMA period changes
            self.required_indicators = ['RSI_14', f'{trend_ema_period}_EMA']

        logging.info(f"RSI Oversold Strategy parameters updated: "
                     f"Oversold threshold: {self.oversold_threshold}, "
                     f"Trend EMA: {self.trend_ema_period}")

    def enable_volume_confirmation(self, enable: bool = True) -> None:
        """
        Enable or disable volume confirmation (placeholder for future implementation).

        Args:
            enable (bool): Whether to enable volume confirmation
        """
        self.use_volume_confirmation = enable
        if enable:
            logging.info(
                "Volume confirmation enabled for RSI Oversold Strategy")
        else:
            logging.info(
                "Volume confirmation disabled for RSI Oversold Strategy")
