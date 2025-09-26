"""
Adaptive ATR Strategy - "Flexibility over Rigidity"
A flexible trading strategy that adapts to market volatility using ATR percentiles (5%-95% range).
Features: Dynamic ATR-based stop-loss, flexible trailing stop take-profit, adaptive position sizing.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from .base_strategy import BaseStrategy
from ..models import MarketData, TradingSignal, TradeDirection, StrategyConfig


class AdaptiveATRStrategy(BaseStrategy):
    """
    Adaptive ATR Strategy with flexible volatility-based approach.
    
    Key Features:
    1. Wide ATR range acceptance (5%-95% percentile)
    2. Dynamic ATR-based stop-loss (adaptive to volatility)
    3. Flexible trailing stop take-profit (let winners run)
    4. Adaptive position sizing based on volatility
    5. Market condition awareness (trending vs consolidating)
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        """Initialize Adaptive ATR Strategy."""
        default_config = StrategyConfig(
            name="Adaptive ATR Strategy - 4H",
            parameters={
                # ATR Flexibility - Accept wide range
                'atr_min_percentile': 5.0,    # Accept from 5th percentile
                'atr_max_percentile': 95.0,   # Accept up to 95th percentile
                'enable_atr_adaptation': True, # Enable ATR-based adaptations
                
                # Dynamic Stop-Loss (ATR-based instead of fixed %)
                'use_dynamic_stop_loss': True,
                'low_volatility_stop_multiplier': 1.0,   # 1.0x ATR for low vol (5-30%)
                'medium_volatility_stop_multiplier': 1.5, # 1.5x ATR for medium vol (30-70%)
                'high_volatility_stop_multiplier': 2.0,   # 2.0x ATR for high vol (70-95%)
                
                # Flexible Take-Profit (Trailing Stop based)
                'use_trailing_stop': True,
                'initial_tp_atr_multiplier': 2.0,        # Initial TP: 2x ATR
                'trailing_stop_atr_multiplier': 1.0,     # Trailing: 1x ATR from peak
                'min_profit_before_trail': 0.015,        # Minimum 1.5% profit before trailing
                
                # Market Condition Adaptation
                'enable_market_condition_filter': True,
                'trending_adx_threshold': 25.0,          # ADX > 25 = trending
                'consolidating_bb_threshold': 0.02,      # BB width < 2% = consolidating
                
                # Entry Conditions (more flexible)
                'rsi_oversold_threshold': 35,            # More flexible RSI
                'rsi_overbought_threshold': 75,          # More flexible RSI
                'ema_cross_confirmation': True,          # Still need EMA cross
                'volume_confirmation_ratio': 1.2,        # Lower volume requirement
                'core_conditions_required': 3,           # Need 3/4 core conditions
                
                # Risk Management
                'max_risk_per_trade_pct': 2.0,          # Max 2% risk per trade
                'position_size_volatility_adjustment': True, # Reduce size in high vol
                
                # Quality Filters (lighter than improved strategy)
                'min_daily_volume_usdt': 1000000,       # Min $1M daily volume
                'price_above_ma_periods': 50,           # Price above 50-period MA
            },
            timeframe="4h",
            enabled=True,
            confidence_threshold=0.65  # Lower threshold for more opportunities
        )
        
        super().__init__(
            name=config.name if config else default_config.name,
            config=config or default_config
        )
        self.logger = logging.getLogger(__name__)
    
    def get_required_indicators(self) -> list:
        """Get list of required indicators for this strategy."""
        return [
            '12_EMA', '26_EMA', '50_MA',       # Moving averages
            'RSI_14',                          # RSI (14-period standard)
            'ADX',                             # Trend strength
            'ATR', 'ATR_Percentile',           # Volatility
            'BB_Upper', 'BB_Lower', 'BB_Width', # Bollinger Bands
            'Volume_Ratio'                     # Volume
        ]
    
    def analyze(self, market_data: MarketData) -> Optional[TradingSignal]:
        """
        Analyze market data with adaptive ATR-based approach.
        """
        try:
            if not self.is_enabled():
                return None
            
            # Check if we have technical analysis
            if not market_data.technical_analysis or not market_data.technical_analysis.indicators:
                self.logger.warning(f"[{market_data.symbol}] No technical analysis available")
                return None
            
            indicators = market_data.technical_analysis.indicators
            
            # Check for critical indicators
            critical_indicators = ['12_EMA', '26_EMA', 'RSI_14', 'ATR', 'ATR_Percentile']
            missing_critical = [ind for ind in critical_indicators if ind not in indicators]
            
            if missing_critical:
                self.logger.warning(f"[{market_data.symbol}] Missing critical indicators: {missing_critical}")
                return None
            
            # STEP 1: ATR Flexibility Check (5%-95% range)
            if not self._check_atr_flexibility(market_data):
                return None
            
            # STEP 2: Market Condition Analysis
            market_condition = self._analyze_market_condition(market_data)
            
            # STEP 3: Adaptive Entry Conditions
            entry_signals = self._check_adaptive_entry_conditions(market_data, market_condition)
            if not entry_signals['passed']:
                self._log_failed_entry_conditions(market_data.symbol, entry_signals['details'])
                return None
            
            # STEP 4: Calculate Dynamic Stop-Loss and Take-Profit
            stop_loss, initial_take_profit = self._calculate_dynamic_risk_reward(market_data, market_condition)
            
            # STEP 5: Adaptive Position Sizing
            volatility_adjustment = self._calculate_volatility_adjustment(market_data)
            
            # STEP 6: Calculate confidence based on market conditions and signals
            confidence = self._calculate_adaptive_confidence(entry_signals, market_condition, market_data)
            
            if confidence < self.config.confidence_threshold:
                self.logger.info(
                    f"[{market_data.symbol}] ⚠️ CONFIDENCE CHECK: "
                    f"Confidence {confidence:.1%} < {self.config.confidence_threshold:.1%}"
                )
                return None
            
            # Create adaptive signal
            signal = self.create_signal(
                market_data=market_data,
                direction=TradeDirection.BUY,
                confidence=confidence,
                stop_loss=stop_loss,
                take_profit=initial_take_profit,
                core_conditions_count=entry_signals['count']
            )
            
            # Add adaptive strategy metadata
            signal.indicators.update({
                'strategy_type': 'adaptive_atr',
                'market_condition': market_condition,
                'volatility_adjustment': volatility_adjustment,
                'atr_percentile': indicators.get('ATR_Percentile', 0),
                'use_trailing_stop': self.config.parameters.get('use_trailing_stop', True),
                'trailing_stop_atr_multiplier': self.config.parameters.get('trailing_stop_atr_multiplier', 1.0),
                'min_profit_before_trail': self.config.parameters.get('min_profit_before_trail', 0.015)
            })
            
            # Calculate R:R for logging
            risk = market_data.current_price - stop_loss
            reward = initial_take_profit - market_data.current_price
            actual_rr = reward / risk if risk > 0 else 0
            
            self.logger.info(
                f"[{market_data.symbol}] 🎯 ADAPTIVE ATR SIGNAL! "
                f"Market: {market_condition}, Confidence: {confidence:.1%}, "
                f"R:R: {actual_rr:.1f}:1, Vol Adj: {volatility_adjustment:.2f}"
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"[{market_data.symbol}] Error in analyze method: {e}")
            raise
    
    def _check_atr_flexibility(self, market_data: MarketData) -> bool:
        """Check ATR percentile within flexible range (5%-95%)."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        
        atr_percentile = indicators.get('ATR_Percentile', 50.0)
        min_percentile = params.get('atr_min_percentile', 5.0)
        max_percentile = params.get('atr_max_percentile', 95.0)
        
        if not (min_percentile <= atr_percentile <= max_percentile):
            self.logger.info(
                f"[{market_data.symbol}] ❌ ATR FLEXIBILITY: "
                f"ATR percentile {atr_percentile:.1f}% outside range ({min_percentile}-{max_percentile}%)"
            )
            return False
        
        self.logger.debug(
            f"[{market_data.symbol}] ✅ ATR FLEXIBILITY: "
            f"ATR percentile {atr_percentile:.1f}% within acceptable range"
        )
        return True
    
    def _analyze_market_condition(self, market_data: MarketData) -> str:
        """Analyze current market condition: trending, consolidating, or volatile."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        
        # Check trend strength using ADX
        adx = indicators.get('ADX', 20.0)
        trending_threshold = params.get('trending_adx_threshold', 25.0)
        
        # Check consolidation using Bollinger Bands width
        bb_width = indicators.get('BB_Width', 0.05)
        consolidating_threshold = params.get('consolidating_bb_threshold', 0.02)
        
        # Check volatility using ATR percentile
        atr_percentile = indicators.get('ATR_Percentile', 50.0)
        
        if adx >= trending_threshold:
            if atr_percentile >= 70:
                return "trending_high_vol"
            elif atr_percentile <= 30:
                return "trending_low_vol"
            else:
                return "trending_medium_vol"
        elif bb_width <= consolidating_threshold:
            return "consolidating"
        else:
            if atr_percentile >= 70:
                return "volatile"
            else:
                return "neutral"
    
    def _check_adaptive_entry_conditions(self, market_data: MarketData, market_condition: str) -> Dict[str, Any]:
        """Check adaptive entry conditions based on market condition."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        current_price = market_data.current_price
        
        conditions = []
        
        # 1. EMA Cross Confirmation (always required)
        ema_12 = indicators.get('12_EMA', 0)
        ema_26 = indicators.get('26_EMA', 0)
        ema_cross_bullish = ema_12 > ema_26 and current_price > ema_12
        conditions.append(('EMA Cross Bullish (12>26, Price>12)', ema_cross_bullish))
        
        # 2. Adaptive RSI based on market condition
        rsi = indicators.get('RSI_14', 50)
        if market_condition.startswith('trending'):
            # In trending markets, be more lenient with RSI
            rsi_favorable = 40 <= rsi <= 80
            rsi_desc = "RSI Trending Range (40-80)"
        elif market_condition == 'consolidating':
            # In consolidating markets, look for oversold bounces
            rsi_favorable = 30 <= rsi <= 60
            rsi_desc = "RSI Consolidation Range (30-60)"
        else:  # volatile or neutral
            # Standard RSI range
            rsi_favorable = 35 <= rsi <= 75
            rsi_desc = "RSI Standard Range (35-75)"
        
        conditions.append((rsi_desc, rsi_favorable))
        
        # 3. Price above moving average (adaptive period)
        ma_50 = indicators.get('50_MA', 0)
        price_above_ma = current_price > ma_50 if ma_50 > 0 else True
        conditions.append(('Price Above 50-MA', price_above_ma))
        
        # 4. Volume confirmation (lighter requirement)
        volume_ratio = indicators.get('Volume_Ratio', 1.0)
        min_volume_ratio = params.get('volume_confirmation_ratio', 1.2)
        volume_confirmed = volume_ratio >= min_volume_ratio
        conditions.append(('Volume Confirmation (≥1.2x)', volume_confirmed))
        
        # Count passed conditions - need all 4/4 for adaptive strategy
        passed_count = sum(1 for _, passed in conditions if passed)
        required_count = 4
        
        return {
            'passed': passed_count >= required_count,
            'count': passed_count,
            'details': conditions,
            'required': required_count
        }
    
    def _calculate_dynamic_risk_reward(self, market_data: MarketData, market_condition: str) -> Tuple[float, float]:
        """Calculate dynamic stop-loss and take-profit based on ATR and market condition."""
        current_price = market_data.current_price
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        
        atr = indicators.get('ATR', current_price * 0.02)  # Fallback to 2% of price
        atr_percentile = indicators.get('ATR_Percentile', 50.0)
        
        # Dynamic stop-loss multiplier based on volatility
        if atr_percentile <= 30:
            # Low volatility: tighter stop
            stop_multiplier = params.get('low_volatility_stop_multiplier', 1.0)
        elif atr_percentile <= 70:
            # Medium volatility: standard stop
            stop_multiplier = params.get('medium_volatility_stop_multiplier', 1.5)
        else:
            # High volatility: wider stop
            stop_multiplier = params.get('high_volatility_stop_multiplier', 2.0)
        
        # Adjust stop multiplier based on market condition
        if market_condition.startswith('trending'):
            stop_multiplier *= 0.8  # Tighter stops in trending markets
        elif market_condition == 'volatile':
            stop_multiplier *= 1.2  # Wider stops in volatile markets
        
        # Calculate stop-loss
        stop_loss = current_price - (stop_multiplier * atr)
        
        # Calculate initial take-profit (will be managed by trailing stop)
        tp_multiplier = params.get('initial_tp_atr_multiplier', 2.0)
        initial_take_profit = current_price + (tp_multiplier * atr)
        
        # Ensure minimum risk-reward ratio of 1.5:1
        risk = current_price - stop_loss
        min_reward = risk * 1.5
        min_take_profit = current_price + min_reward
        
        initial_take_profit = max(initial_take_profit, min_take_profit)
        
        self.logger.debug(
            f"[{market_data.symbol}] Dynamic R:R Calculation: "
            f"ATR={atr:.4f}, ATR%={atr_percentile:.1f}, "
            f"StopMult={stop_multiplier:.1f}, Market={market_condition}"
        )
        
        return stop_loss, initial_take_profit
    
    def _calculate_volatility_adjustment(self, market_data: MarketData) -> float:
        """Calculate position size adjustment based on volatility."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        
        if not params.get('position_size_volatility_adjustment', True):
            return 1.0  # No adjustment
        
        atr_percentile = indicators.get('ATR_Percentile', 50.0)
        
        # Reduce position size in high volatility environments
        if atr_percentile >= 80:
            return 0.7  # Reduce by 30%
        elif atr_percentile >= 60:
            return 0.85  # Reduce by 15%
        elif atr_percentile <= 20:
            return 1.15  # Increase by 15% in low volatility
        else:
            return 1.0  # No adjustment
    
    def _calculate_adaptive_confidence(self, entry_signals: Dict, market_condition: str, market_data: MarketData) -> float:
        """Calculate confidence based on entry signals and market condition."""
        base_confidence = 0.4
        
        # Entry signals bonus
        signal_ratio = entry_signals['count'] / entry_signals['required']
        signal_bonus = signal_ratio * 0.3
        
        # Market condition bonus
        condition_bonus = 0.0
        if market_condition.startswith('trending'):
            condition_bonus = 0.15  # Prefer trending markets
        elif market_condition == 'consolidating':
            condition_bonus = 0.10  # Decent for bounce plays
        elif market_condition == 'volatile':
            condition_bonus = 0.05  # Caution in volatile markets
        
        # ATR percentile bonus (reward middle range)
        indicators = market_data.technical_analysis.indicators
        atr_percentile = indicators.get('ATR_Percentile', 50.0)
        if 30 <= atr_percentile <= 70:
            atr_bonus = 0.1  # Sweet spot volatility
        else:
            atr_bonus = 0.05  # Still acceptable but not ideal
        
        # Volume confirmation bonus
        volume_ratio = indicators.get('Volume_Ratio', 1.0)
        volume_bonus = min((volume_ratio - 1.0) * 0.05, 0.1)  # Up to 10% bonus
        
        total_confidence = base_confidence + signal_bonus + condition_bonus + atr_bonus + volume_bonus
        return min(total_confidence, 1.0)
    
    def _log_failed_entry_conditions(self, symbol: str, conditions: list) -> None:
        """Log detailed analysis when entry conditions fail."""
        passed_count = sum(1 for _, passed in conditions if passed)
        required = 4
        
        self.logger.info(f"[{symbol}] ❌ ADAPTIVE ENTRY REJECTED: Entry conditions not met")
        self.logger.info(f"  📊 ADAPTIVE ENTRY ANALYSIS ({passed_count}/4 passed, need {required}+):")
        
        for condition_name, passed in conditions:
            status = "✅" if passed else "❌"
            self.logger.info(f"  • {condition_name}: {status}")
    
    def get_strategy_description(self) -> str:
        """Get adaptive strategy description."""
        params = self.config.parameters
        
        return f"""
        {self.name} - "FLEXIBILITY OVER RIGIDITY"
        
        🎯 ADAPTIVE FEATURES:
        1. Wide ATR Range: {params.get('atr_min_percentile', 5)}%-{params.get('atr_max_percentile', 95)}% acceptance
        2. Dynamic Stop-Loss: ATR-based instead of fixed percentages
        3. Trailing Take-Profit: Let winners run with trailing stops
        4. Market Condition Awareness: Adapt to trending/consolidating/volatile markets
        5. Volatility-Adjusted Position Sizing: Reduce risk in high volatility
        
        📊 DYNAMIC STOP-LOSS:
        • Low Volatility (5-30%): {params.get('low_volatility_stop_multiplier', 1.0)}x ATR
        • Medium Volatility (30-70%): {params.get('medium_volatility_stop_multiplier', 1.5)}x ATR  
        • High Volatility (70-95%): {params.get('high_volatility_stop_multiplier', 2.0)}x ATR
        
        🚀 FLEXIBLE TAKE-PROFIT:
        • Initial TP: {params.get('initial_tp_atr_multiplier', 2.0)}x ATR
        • Trailing Stop: {params.get('trailing_stop_atr_multiplier', 1.0)}x ATR from peak
        • Min Profit Before Trail: {params.get('min_profit_before_trail', 0.015)*100:.1f}%
        
        🌊 MARKET ADAPTATION:
        • Trending Markets: Tighter stops, lenient RSI (40-80)
        • Consolidating Markets: Oversold bounces, RSI (30-60)
        • Volatile Markets: Wider stops, standard RSI (35-75)
        
        💰 RISK MANAGEMENT:
        • Max Risk Per Trade: {params.get('max_risk_per_trade_pct', 2.0)}%
        • Position Size Adjustment: Based on volatility percentile
        • Minimum R:R Ratio: 1.5:1 (adaptive to market conditions)
        """

    def create_signal(self, market_data: MarketData, direction: TradeDirection, 
                     confidence: float, stop_loss: float, take_profit: float, 
                     core_conditions_count: int = 0, **kwargs) -> TradingSignal:
        """Create trading signal with adaptive strategy enhancements."""
        signal = TradingSignal(
            symbol=market_data.symbol,
            direction=direction,
            price=market_data.current_price,
            confidence=confidence,
            timestamp=market_data.timestamp,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy_name=self.name,
            core_conditions_count=core_conditions_count,
            indicators=market_data.technical_analysis.indicators.copy() if market_data.technical_analysis else {}
        )
        
        # Add strategy-specific metadata
        signal.indicators.update(kwargs)
        
        return signal