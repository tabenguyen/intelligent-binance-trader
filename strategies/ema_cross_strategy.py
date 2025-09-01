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
    EMA Cross Strategy with RSI and MACD confirmation for 4-hour timeframe.

    This strategy implements the following rules optimized for 4-hour charts:
    1. Trend Confirmation: Price must be above the 55-EMA (long-term trend)
    2. Bullish Momentum: The fast 12-EMA must be above the medium 26-EMA
    3. MACD Confirmation: MACD line above signal line and histogram positive
    4. Healthy Momentum: RSI must be above 45 (bullish) but below 75 (not overbought)
    5. Good Entry: Price must be relatively close to the 26-EMA to avoid buying at the top
    6. Bollinger Bands: Price should be in lower half of BB for better entry
    """

    def __init__(self):
        """Initialize the EMA Cross Strategy for 4-hour timeframe."""
        super().__init__("EMA Cross Strategy - 4H")
        self.required_indicators = ['55_EMA', '12_EMA', '26_EMA', 'RSI_21']
        self.rsi_lower_bound = 45  # More lenient for 4-hour timeframe
        self.rsi_upper_bound = 75  # Higher threshold for 4-hour
        self.ema_support_tolerance = 0.03  # 3% tolerance from 26-EMA (wider for 4H)

    def check_buy_signal(self, symbol: str, analysis: Dict[str, Any], current_price: float) -> bool:
        """
        Check if the current market data constitutes a BUY signal based on 4-hour EMA cross strategy.

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
                f"[{symbol}] Missing required indicators for 4H EMA Cross Strategy")
            return False

        # Strategy Rule 1: Long-term Trend Confirmation - Price must be above 55-EMA
        price_above_55ema = current_price > analysis['55_EMA']

        # Strategy Rule 2: Bullish Momentum - 12-EMA must be above 26-EMA
        emas_in_uptrend = analysis['12_EMA'] > analysis['26_EMA']

        # Strategy Rule 3: MACD Confirmation (if available)
        macd_bullish = True  # Default to True if MACD not available
        if analysis.get('MACD') and analysis.get('MACD_Signal') and analysis.get('MACD_Histogram'):
            macd_bullish = (analysis['MACD'] > analysis['MACD_Signal'] and 
                           analysis['MACD_Histogram'] > 0)

        # Strategy Rule 4: Healthy Momentum - RSI between 45 and 75 (4H optimized)
        rsi_is_healthy = self.rsi_lower_bound < analysis['RSI_21'] < self.rsi_upper_bound

        # Strategy Rule 5: Good Entry - Price within 3% of 26-EMA (support level)
        price_near_support = (
            abs(current_price - analysis['26_EMA']) / analysis['26_EMA']
        ) < self.ema_support_tolerance

        # Strategy Rule 6: Bollinger Bands confirmation (if available)
        bb_favorable = True  # Default to True if BB not available
        if (analysis.get('BB_Upper') and analysis.get('BB_Middle') and 
            analysis.get('BB_Lower')):
            # Price should be in lower half of Bollinger Bands for better entry
            bb_range = analysis['BB_Upper'] - analysis['BB_Lower']
            price_position_in_bb = (current_price - analysis['BB_Lower']) / bb_range
            bb_favorable = price_position_in_bb < 0.6  # Lower 60% of BB range

        # Strategy Rule 7: Volume confirmation - ensure we have decent volume
        # This will be implemented if volume data is added to analysis

        # Log detailed analysis for debugging
        self._log_signal_analysis(symbol, current_price, analysis, {
            'price_above_55ema': price_above_55ema,
            'emas_in_uptrend': emas_in_uptrend,
            'macd_bullish': macd_bullish,
            'rsi_is_healthy': rsi_is_healthy,
            'price_near_support': price_near_support,
            'bb_favorable': bb_favorable
        })

        # All major conditions must be met for a buy signal
        core_conditions = (price_above_55ema and emas_in_uptrend and 
                          rsi_is_healthy and price_near_support)
        
        # Additional confirmations (MACD and BB) improve signal quality
        confirmation_signals = macd_bullish and bb_favorable
        
        if core_conditions and confirmation_signals:
            logging.info(
                f"[{symbol}] BUY SIGNAL FOUND! All 4H EMA Cross Strategy conditions met.")
            return True
        elif core_conditions:
            logging.info(
                f"[{symbol}] Partial signal detected - core conditions met but lacking confirmations.")
            logging.info(
                f"[{symbol}] MACD bullish: {macd_bullish}, BB favorable: {bb_favorable}")

        return False

    def get_strategy_description(self) -> str:
        """
        Get a description of the 4H EMA Cross Strategy rules.

        Returns:
            str: A human-readable description of the strategy
        """
        return f"""
        {self.name} Rules (4-Hour Timeframe):
        1. Long-term Trend: Price must be above the 55-EMA
        2. Bullish Momentum: The 12-EMA must be above the 26-EMA
        3. MACD Confirmation: MACD above signal line with positive histogram
        4. Healthy Momentum: RSI must be between {self.rsi_lower_bound} and {self.rsi_upper_bound}
        5. Good Entry: Price must be within {self.ema_support_tolerance*100}% of the 26-EMA
        6. Bollinger Bands: Price in lower 60% of BB range for better entry
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
        logging.debug(f"[{symbol}] 4H EMA Cross Strategy Analysis:")
        logging.debug(f"  Current Price: ${current_price:.4f}")
        logging.debug(f"  12-EMA: ${analysis.get('12_EMA', 'N/A'):.4f}")
        logging.debug(f"  26-EMA: ${analysis.get('26_EMA', 'N/A'):.4f}")
        logging.debug(f"  55-EMA: ${analysis.get('55_EMA', 'N/A'):.4f}")
        logging.debug(f"  RSI-21: {analysis.get('RSI_21', 'N/A'):.2f}")
        
        if analysis.get('MACD'):
            logging.debug(f"  MACD: {analysis.get('MACD', 'N/A'):.4f}")
            logging.debug(f"  MACD Signal: {analysis.get('MACD_Signal', 'N/A'):.4f}")
            logging.debug(f"  MACD Histogram: {analysis.get('MACD_Histogram', 'N/A'):.4f}")
        
        if analysis.get('BB_Upper'):
            logging.debug(f"  BB Upper: ${analysis.get('BB_Upper', 'N/A'):.4f}")
            logging.debug(f"  BB Middle: ${analysis.get('BB_Middle', 'N/A'):.4f}")
            logging.debug(f"  BB Lower: ${analysis.get('BB_Lower', 'N/A'):.4f}")
        
        logging.debug(f"  Conditions:")
        for condition, result in conditions.items():
            logging.debug(f"    {condition}: {result}")
        
        logging.debug(f"  Signal Result: {all(conditions.values())}")

    def configure_parameters(self, rsi_lower: int = None, rsi_upper: int = None,
                             ema_tolerance: float = None) -> None:
        """
        Configure strategy parameters.

        Args:
            rsi_lower (int, optional): Lower bound for RSI
            rsi_upper (int, optional): Upper bound for RSI
            ema_tolerance (float, optional): Tolerance for distance from 26-EMA
        """
        if rsi_lower is not None:
            self.rsi_lower_bound = rsi_lower
        if rsi_upper is not None:
            self.rsi_upper_bound = rsi_upper
        if ema_tolerance is not None:
            self.ema_support_tolerance = ema_tolerance

        logging.info(
            f"4H EMA Cross Strategy parameters updated: RSI({self.rsi_lower_bound}-{self.rsi_upper_bound}), EMA tolerance: {self.ema_support_tolerance*100}%")
