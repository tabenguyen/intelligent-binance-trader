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
    EMA Cross Strategy with RSI, MACD confirmation and Advanced Quality Filters for 4-hour timeframe.

    This strategy implements the following rules optimized for 4-hour charts:
    
    QUALITY FILTERS (Must pass first):
    1. Multi-Timeframe Trend: Price must be above daily 50-EMA (prevents counter-trend trades)
    2. ATR Volatility Filter: Market volatility must be in normal range (0.7x - 2.0x average)
    3. Volume Confirmation: Current volume must be 20%+ above 20-period average
    
    CORE STRATEGY CONDITIONS:
    4. Trend Confirmation: Price must be above the 55-EMA (long-term trend)
    5. Bullish Momentum: The fast 12-EMA must be above the medium 26-EMA
    6. MACD Confirmation: MACD line above signal line and histogram positive
    7. Healthy Momentum: RSI must be above 45 (bullish) but below 75 (not overbought)
    8. Good Entry: Price must be relatively close to the 26-EMA to avoid buying at the top
    9. Bollinger Bands: Price should be in lower half of BB for better entry
    """

    def __init__(self):
        """Initialize the EMA Cross Strategy for 4-hour timeframe."""
        super().__init__("EMA Cross Strategy - 4H")
        self.required_indicators = ['55_EMA', '12_EMA', '26_EMA', 'RSI_21']
        self.rsi_lower_bound = 45  # More lenient for 4-hour timeframe
        self.rsi_upper_bound = 75  # Higher threshold for 4-hour
        self.ema_support_tolerance = 0.03  # 3% tolerance from 26-EMA (wider for 4H)

    def check_buy_signal(self, symbol: str, analysis: Dict[str, Any], current_price: float, client=None) -> bool:
        """
        Check if the current market data constitutes a BUY signal based on 4-hour EMA cross strategy
        with advanced quality filters.

        Args:
            symbol (str): The trading symbol (e.g., 'BTCUSDT')
            analysis (Dict[str, Any]): Dictionary containing technical analysis data
            current_price (float): The current price of the symbol
            client: Binance client for multi-timeframe analysis

        Returns:
            bool: True if a buy signal is detected, False otherwise
        """
        # Import configuration from main module
        from trading_bot import (ENABLE_DAILY_TREND_FILTER, ENABLE_ATR_FILTER, 
                                ENABLE_VOLUME_FILTER, MIN_VOLUME_RATIO)
        
        # Validate required data is present
        if not self.validate_analysis_data(analysis, self.required_indicators):
            logging.warning(
                f"[{symbol}] Missing required indicators for 4H EMA Cross Strategy")
            return False

        # ═══════════════════════════════════════════════════════════════════
        # QUALITY FILTER 1: Multi-Timeframe Trend Confirmation
        # ═══════════════════════════════════════════════════════════════════
        daily_trend_bullish = True  # Default to True if filter disabled
        if ENABLE_DAILY_TREND_FILTER and client:
            from trading_bot import get_daily_trend_filter
            daily_trend_bullish = get_daily_trend_filter(client, symbol)
            if not daily_trend_bullish:
                logging.info(f"[{symbol}] ❌ DAILY TREND FILTER: Failed - Price below daily 50-EMA")
                return False
            else:
                logging.info(f"[{symbol}] ✅ DAILY TREND FILTER: Passed - Bullish daily trend confirmed")

        # ═══════════════════════════════════════════════════════════════════
        # QUALITY FILTER 2: ATR Volatility Filter
        # ═══════════════════════════════════════════════════════════════════
        atr_suitable = True  # Default to True if filter disabled
        if ENABLE_ATR_FILTER:
            volatility_state = analysis.get('Volatility_State', 'UNKNOWN')
            atr_percentile = analysis.get('ATR_Percentile', 1.0)
            
            if volatility_state == 'LOW':
                logging.info(f"[{symbol}] ❌ ATR FILTER: Failed - Market too choppy (ATR: {atr_percentile:.2f}x)")
                return False
            elif volatility_state == 'HIGH':
                logging.info(f"[{symbol}] ❌ ATR FILTER: Failed - Market too volatile (ATR: {atr_percentile:.2f}x)")
                return False
            else:
                logging.info(f"[{symbol}] ✅ ATR FILTER: Passed - Normal volatility (ATR: {atr_percentile:.2f}x)")
                atr_suitable = True

        # ═══════════════════════════════════════════════════════════════════
        # QUALITY FILTER 3: Volume Confirmation
        # ═══════════════════════════════════════════════════════════════════
        volume_confirmed = True  # Default to True if filter disabled
        if ENABLE_VOLUME_FILTER:
            volume_ratio = analysis.get('Volume_Ratio', 1.0)
            current_volume = analysis.get('Current_Volume', 0)
            avg_volume = analysis.get('Avg_Volume_20', 1)
            
            if volume_ratio < MIN_VOLUME_RATIO:
                logging.info(f"[{symbol}] ❌ VOLUME FILTER: Failed - Insufficient volume")
                logging.info(f"  Current: {current_volume:,.0f} | Avg: {avg_volume:,.0f} | Ratio: {volume_ratio:.2f}x (need {MIN_VOLUME_RATIO}x)")
                return False
            else:
                logging.info(f"[{symbol}] ✅ VOLUME FILTER: Passed - Strong volume confirmation")
                logging.info(f"  Current: {current_volume:,.0f} | Avg: {avg_volume:,.0f} | Ratio: {volume_ratio:.2f}x")
                volume_confirmed = True

        # ═══════════════════════════════════════════════════════════════════
        # CORE STRATEGY CONDITIONS (Original 4H Strategy)
        # ═══════════════════════════════════════════════════════════════════

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

        # Log detailed analysis for debugging
        self._log_signal_analysis(symbol, current_price, analysis, {
            'daily_trend_bullish': daily_trend_bullish,
            'atr_suitable': atr_suitable,
            'volume_confirmed': volume_confirmed,
            'price_above_55ema': price_above_55ema,
            'emas_in_uptrend': emas_in_uptrend,
            'macd_bullish': macd_bullish,
            'rsi_is_healthy': rsi_is_healthy,
            'price_near_support': price_near_support,
            'bb_favorable': bb_favorable
        })

        # All quality filters must pass first
        quality_filters_passed = daily_trend_bullish and atr_suitable and volume_confirmed
        
        # All core strategy conditions must be met
        core_conditions = (price_above_55ema and emas_in_uptrend and 
                          rsi_is_healthy and price_near_support)
        
        # Additional confirmations (MACD and BB) improve signal quality
        confirmation_signals = macd_bullish and bb_favorable
        
        if quality_filters_passed and core_conditions and confirmation_signals:
            logging.info(f"[{symbol}] 🎯 HIGH-QUALITY BUY SIGNAL DETECTED!")
            logging.info(f"[{symbol}] ✅ All quality filters passed")
            logging.info(f"[{symbol}] ✅ All core conditions met") 
            logging.info(f"[{symbol}] ✅ All confirmation signals positive")
            return True
        elif quality_filters_passed and core_conditions:
            logging.info(f"[{symbol}] ⚠️  PARTIAL SIGNAL: Core conditions met but lacking confirmations")
            logging.info(f"[{symbol}] MACD bullish: {macd_bullish}, BB favorable: {bb_favorable}")
        elif not quality_filters_passed:
            logging.info(f"[{symbol}] ❌ SIGNAL REJECTED: Quality filters failed")
            # Log which quality filters failed
            if not daily_trend_bullish:
                logging.info(f"  • Daily trend filter: FAILED (price below daily 50-EMA)")
            if not atr_suitable:
                logging.info(f"  • ATR filter: FAILED (volatility: {analysis.get('Volatility_State', 'UNKNOWN')})")
            if not volume_confirmed:
                logging.info(f"  • Volume filter: FAILED (ratio: {analysis.get('Volume_Ratio', 0):.2f}x, need {MIN_VOLUME_RATIO}x)")
        else:
            logging.info(f"[{symbol}] ❌ SIGNAL REJECTED: Core conditions not met")
            # Log detailed results of each core condition
            logging.info(f"  📊 CORE CONDITIONS ANALYSIS:")
            logging.info(f"  • Price above 55-EMA: {'✅' if price_above_55ema else '❌'} (Price: ${current_price:.2f} vs 55-EMA: ${analysis['55_EMA']:.2f})")
            logging.info(f"  • EMA uptrend (12>26): {'✅' if emas_in_uptrend else '❌'} (12-EMA: ${analysis['12_EMA']:.2f} vs 26-EMA: ${analysis['26_EMA']:.2f})")
            logging.info(f"  • RSI healthy range: {'✅' if rsi_is_healthy else '❌'} (RSI: {analysis['RSI_21']:.1f}, need {self.rsi_lower_bound}-{self.rsi_upper_bound})")
            
            # Calculate distance from 26-EMA for price near support check
            ema_distance_pct = abs(current_price - analysis['26_EMA']) / analysis['26_EMA'] * 100
            logging.info(f"  • Price near 26-EMA support: {'✅' if price_near_support else '❌'} ({ema_distance_pct:.1f}% from 26-EMA, need <{self.ema_support_tolerance*100}%)")
            
            # Also show confirmation signals status
            logging.info(f"  📋 CONFIRMATION SIGNALS:")
            if analysis.get('MACD') and analysis.get('MACD_Signal'):
                logging.info(f"  • MACD bullish: {'✅' if macd_bullish else '❌'} (MACD: {analysis['MACD']:.4f} vs Signal: {analysis['MACD_Signal']:.4f})")
            else:
                logging.info(f"  • MACD bullish: ✅ (not available, defaulted to True)")
                
            if analysis.get('BB_Upper') and analysis.get('BB_Lower'):
                bb_range = analysis['BB_Upper'] - analysis['BB_Lower']
                price_position_in_bb = (current_price - analysis['BB_Lower']) / bb_range * 100
                logging.info(f"  • BB favorable entry: {'✅' if bb_favorable else '❌'} (Price at {price_position_in_bb:.1f}% of BB range, need <60%)")
            else:
                logging.info(f"  • BB favorable entry: ✅ (not available, defaulted to True)")

        return False

    def get_strategy_description(self) -> str:
        """
        Get a description of the 4H EMA Cross Strategy with Quality Filters.

        Returns:
            str: A human-readable description of the strategy
        """
        return f"""
        {self.name} Rules (4-Hour Timeframe with Quality Filters):
        
        QUALITY FILTERS (Must Pass First):
        1. Daily Trend Filter: Price above daily 50-EMA
        2. ATR Volatility Filter: Normal market volatility (0.7x - 2.0x)
        3. Volume Filter: Volume 20%+ above 20-period average
        
        CORE STRATEGY:
        4. Long-term Trend: Price above 55-EMA
        5. Bullish Momentum: 12-EMA above 26-EMA
        6. MACD Confirmation: MACD above signal with positive histogram
        7. Healthy RSI: Between {self.rsi_lower_bound} and {self.rsi_upper_bound}
        8. Good Entry: Within {self.ema_support_tolerance*100}% of 26-EMA
        9. Bollinger Bands: Price in lower 60% of BB range
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
        logging.debug(f"[{symbol}] 4H EMA Cross Strategy Analysis with Quality Filters:")
        logging.debug(f"  Current Price: ${current_price:.4f}")
        
        # Quality Filters
        logging.debug(f"  ═══ QUALITY FILTERS ═══")
        logging.debug(f"  Daily Trend: {conditions.get('daily_trend_bullish', 'N/A')}")
        logging.debug(f"  ATR Suitable: {conditions.get('atr_suitable', 'N/A')} (State: {analysis.get('Volatility_State', 'N/A')})")
        logging.debug(f"  Volume Confirmed: {conditions.get('volume_confirmed', 'N/A')} (Ratio: {analysis.get('Volume_Ratio', 0):.2f}x)")
        
        # Core Strategy
        logging.debug(f"  ═══ CORE STRATEGY ═══")
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
        
        logging.debug(f"  ═══ CONDITIONS ═══")
        for condition, result in conditions.items():
            logging.debug(f"    {condition}: {result}")
        
        # Calculate overall result
        quality_filters = [
            conditions.get('daily_trend_bullish', True),
            conditions.get('atr_suitable', True), 
            conditions.get('volume_confirmed', True)
        ]
        core_conditions = [
            conditions.get('price_above_55ema', False),
            conditions.get('emas_in_uptrend', False),
            conditions.get('rsi_is_healthy', False),
            conditions.get('price_near_support', False)
        ]
        confirmations = [
            conditions.get('macd_bullish', True),
            conditions.get('bb_favorable', True)
        ]
        
        logging.debug(f"  Quality Filters: {all(quality_filters)} | Core: {all(core_conditions)} | Confirmations: {all(confirmations)}")
        logging.debug(f"  Final Signal: {all(quality_filters) and all(core_conditions) and all(confirmations)}")

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
