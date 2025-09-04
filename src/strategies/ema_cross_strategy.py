"""
Refactored EMA Cross Strategy following SOLID principles.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .base_strategy import BaseStrategy
from ..models import MarketData, TradingSignal, TradeDirection, StrategyConfig


class EMACrossStrategy(BaseStrategy):
    """
    EMA Cross Strategy with advanced quality filters.
    
    This strategy follows SOLID principles:
    - Single Responsibility: Only handles EMA crossover signal generation
    - Open-Closed: Extends BaseStrategy without modifying it
    - Liskov Substitution: Can replace any IStrategy implementation
    - Interface Segregation: Implements only IStrategy interface
    - Dependency Inversion: Depends on abstractions (MarketData) not concretions
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        """Initialize EMA Cross Strategy."""
        default_config = StrategyConfig(
            name="EMA Cross Strategy - 4H",
            parameters={
                'rsi_lower_bound': 45,
                'rsi_upper_bound': 75,
                'ema_support_tolerance': 0.03,
                'core_conditions_required': 1,  # Need 1 of 4 core conditions
                'enable_daily_trend_filter': True,
                'enable_atr_filter': True,
                'enable_volume_filter': True,
                'min_volume_ratio': 1.2
            },
            timeframe="4h",
            enabled=True,
            confidence_threshold=0.7
        )
        
        super().__init__(
            name=config.name if config else default_config.name,
            config=config or default_config
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze(self, market_data: MarketData) -> Optional[TradingSignal]:
        """
        Analyze market data and generate trading signals.
        
        Args:
            market_data: Market data with technical indicators
            
        Returns:
            TradingSignal if conditions are met, None otherwise
        """
        if not self.is_enabled():
            return None
        
        if not self.validate_market_data(market_data):
            self.logger.warning(f"[{market_data.symbol}] Missing required indicators")
            return None
        
        # Check quality filters first
        if not self._check_quality_filters(market_data):
            return None
        
        # Check core strategy conditions
        core_signals = self._check_core_conditions(market_data)
        if not core_signals['passed']:
            self._log_failed_conditions(market_data.symbol, core_signals['details'])
            return None
        
        # Check confirmation signals
        confirmations = self._check_confirmation_signals(market_data)
        
        # Calculate confidence based on signals strength
        confidence = self._calculate_confidence(core_signals['count'], confirmations)
        
        if confidence < self.config.confidence_threshold:
            self.logger.info(
                f"[{market_data.symbol}] ⚠️ PARTIAL SIGNAL: "
                f"Core conditions met ({core_signals['count']}/4 rules) but lacking confirmations"
            )
            return None
        
        # Calculate stop loss and take profit
        stop_loss = self._calculate_stop_loss(market_data)
        take_profit = self._calculate_take_profit(market_data)
        
        signal = self.create_signal(
            market_data=market_data,
            direction=TradeDirection.BUY,
            confidence=confidence,
            stop_loss=stop_loss,
            take_profit=take_profit,
            core_conditions_count=core_signals['count']
        )
        
        self.logger.info(
            f"[{market_data.symbol}] 🎯 HIGH-QUALITY BUY SIGNAL DETECTED! "
            f"Core: {core_signals['count']}/4, Confidence: {confidence:.1%}"
        )
        
        return signal
    
    def get_required_indicators(self) -> list:
        """Get list of required indicators."""
        return [
            '12_EMA', '26_EMA', '55_EMA', 'RSI_21',
            'MACD', 'MACD_Signal', 'MACD_Histogram',
            'BB_Upper', 'BB_Middle', 'BB_Lower',
            'ATR', 'ATR_Percentile', 'Volatility_State',
            'Current_Volume', 'Avg_Volume_20', 'Volume_Ratio'
        ]
    
    def _check_quality_filters(self, market_data: MarketData) -> bool:
        """Check quality filters that must pass first."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        
        # Daily trend filter (simplified - would need daily data in real implementation)
        if params.get('enable_daily_trend_filter', True):
            # For now, just check if price is above 55-EMA as proxy
            if market_data.current_price <= indicators.get('55_EMA', 0):
                self.logger.info(f"[{market_data.symbol}] ❌ DAILY TREND FILTER: Failed")
                return False
        
        # ATR volatility filter
        if params.get('enable_atr_filter', True):
            volatility_state = indicators.get('Volatility_State', 'NORMAL')
            if volatility_state in ['LOW', 'HIGH']:
                self.logger.info(f"[{market_data.symbol}] ❌ ATR FILTER: Failed - {volatility_state} volatility")
                return False
        
        # Volume filter
        if params.get('enable_volume_filter', True):
            volume_ratio = indicators.get('Volume_Ratio', 0)
            min_ratio = params.get('min_volume_ratio', 1.2)
            if volume_ratio < min_ratio:
                self.logger.info(f"[{market_data.symbol}] ❌ VOLUME FILTER: Failed - {volume_ratio:.2f}x < {min_ratio}x")
                return False
        
        return True
    
    def _check_core_conditions(self, market_data: MarketData) -> Dict[str, Any]:
        """Check core strategy conditions."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        current_price = market_data.current_price
        
        # Core condition checks
        conditions = []
        
        # 1. Price above 55-EMA (long-term trend)
        price_above_55ema = current_price > indicators.get('55_EMA', 0)
        conditions.append(('Price above 55-EMA', price_above_55ema))
        
        # 2. EMA uptrend (12-EMA > 26-EMA)
        emas_in_uptrend = indicators.get('12_EMA', 0) > indicators.get('26_EMA', 0)
        conditions.append(('EMA uptrend (12>26)', emas_in_uptrend))
        
        # 3. Healthy RSI range
        rsi = indicators.get('RSI_21', 50)
        rsi_lower = params.get('rsi_lower_bound', 45)
        rsi_upper = params.get('rsi_upper_bound', 75)
        rsi_healthy = rsi_lower < rsi < rsi_upper
        conditions.append(('RSI healthy range', rsi_healthy))
        
        # 4. Price near 26-EMA support
        ema_26 = indicators.get('26_EMA', current_price)
        tolerance = params.get('ema_support_tolerance', 0.03)
        distance_pct = abs(current_price - ema_26) / ema_26 if ema_26 > 0 else 1.0
        price_near_support = distance_pct < tolerance
        conditions.append(('Price near 26-EMA support', price_near_support))
        
        # Count passed conditions
        passed_count = sum(1 for _, passed in conditions if passed)
        required_count = params.get('core_conditions_required', 1)
        
        return {
            'passed': passed_count >= required_count,
            'count': passed_count,
            'details': conditions,
            'required': required_count
        }
    
    def _check_confirmation_signals(self, market_data: MarketData) -> Dict[str, bool]:
        """Check confirmation signals for signal quality."""
        indicators = market_data.technical_analysis.indicators
        
        # MACD bullish
        macd = indicators.get('MACD', 0)
        macd_signal = indicators.get('MACD_Signal', 0)
        macd_hist = indicators.get('MACD_Histogram', 0)
        macd_bullish = macd > macd_signal and macd_hist > 0
        
        # Bollinger Bands favorable entry
        bb_upper = indicators.get('BB_Upper', 0)
        bb_lower = indicators.get('BB_Lower', 0)
        current_price = market_data.current_price
        
        bb_favorable = True
        if bb_upper > bb_lower > 0:
            bb_range = bb_upper - bb_lower
            price_position = (current_price - bb_lower) / bb_range
            bb_favorable = price_position < 0.6  # Lower 60% of BB range
        
        return {
            'macd_bullish': macd_bullish,
            'bb_favorable': bb_favorable
        }
    
    def _calculate_confidence(self, core_count: int, confirmations: Dict[str, bool]) -> float:
        """Calculate signal confidence based on conditions met."""
        base_confidence = 0.5
        
        # Add confidence for core conditions
        core_bonus = (core_count / 4) * 0.3
        
        # Add confidence for confirmations
        confirmation_count = sum(1 for passed in confirmations.values() if passed)
        confirmation_bonus = (confirmation_count / len(confirmations)) * 0.2
        
        return min(base_confidence + core_bonus + confirmation_bonus, 1.0)
    
    def _calculate_stop_loss(self, market_data: MarketData) -> float:
        """Calculate stop loss price."""
        current_price = market_data.current_price
        atr = market_data.technical_analysis.indicators.get('ATR', current_price * 0.02)
        
        # Use 1.5x ATR below current price or 5% whichever is smaller
        atr_stop = current_price - (1.5 * atr)
        percentage_stop = current_price * 0.95
        
        return max(atr_stop, percentage_stop)
    
    def _calculate_take_profit(self, market_data: MarketData) -> float:
        """Calculate take profit price."""
        current_price = market_data.current_price
        atr = market_data.technical_analysis.indicators.get('ATR', current_price * 0.02)
        
        # Use 2x ATR above current price for 2:1 risk-reward
        return current_price + (2 * atr)
    
    def _log_failed_conditions(self, symbol: str, conditions: list) -> None:
        """Log detailed analysis when core conditions fail."""
        passed_count = sum(1 for _, passed in conditions if passed)
        required = self.config.parameters.get('core_conditions_required', 1)
        
        self.logger.info(f"[{symbol}] ❌ SIGNAL REJECTED: Core conditions not met")
        self.logger.info(f"  📊 CORE CONDITIONS ANALYSIS ({passed_count}/4 passed, need {required}+):")
        
        for condition_name, passed in conditions:
            status = "✅" if passed else "❌"
            self.logger.info(f"  • {condition_name}: {status}")
    
    def get_strategy_description(self) -> str:
        """Get a description of the strategy."""
        params = self.config.parameters
        required = params.get('core_conditions_required', 1)
        
        return f"""
        {self.name} Rules (4-Hour Timeframe with Quality Filters):
        
        QUALITY FILTERS (Must Pass First):
        1. Daily Trend Filter: Price above daily 50-EMA
        2. ATR Volatility Filter: Normal market volatility
        3. Volume Filter: Volume {params.get('min_volume_ratio', 1.2)}x+ above average
        
        CORE STRATEGY (Need {required} of 4 Rules):
        4. Long-term Trend: Price above 55-EMA
        5. Bullish Momentum: 12-EMA above 26-EMA
        6. Healthy RSI: Between {params.get('rsi_lower_bound', 45)}-{params.get('rsi_upper_bound', 75)}
        7. Good Entry: Within {params.get('ema_support_tolerance', 0.03)*100}% of 26-EMA
        
        CONFIRMATION SIGNALS (Improve Quality):
        8. MACD Confirmation: MACD above signal with positive histogram
        9. Bollinger Bands: Price in lower 60% of BB range
        """
