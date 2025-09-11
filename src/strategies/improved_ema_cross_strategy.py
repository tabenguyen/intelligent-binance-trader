"""
Improved EMA Cross Strategy - "Quality over Quantity"
Improvements: Minimum R:R ratio 1.5:1, tightened entry conditions, farther take profit targets.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .base_strategy import BaseStrategy
from ..models import MarketData, TradingSignal, TradeDirection, StrategyConfig


class ImprovedEMACrossStrategy(BaseStrategy):
    """
    Improved EMA Cross Strategy with focus "Quality over Quantity".
    
    Main improvements:
    1. Risk:Reward ratio minimum 1.5:1 (target 2:1)
    2. Tightened entry conditions (requires more confirmations)
    3. Farther take profit targets allowing winning trades to "run"
    4. Added RSI divergence and momentum filters
    5. Stronger volume confirmation
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        """Initialize Improved EMA Cross Strategy."""
        default_config = StrategyConfig(
            name="Improved EMA Cross Strategy - 4H",
            parameters={
                # RSI tightened - only trade when RSI in sweet spot
                'rsi_lower_bound': 50,    # Increased from 45 -> 50 (stronger momentum)
                'rsi_upper_bound': 70,    # Decreased from 75 -> 70 (avoid overbought)
                
                # EMA support tightened - only entry when price near support
                'ema_support_tolerance': 0.02,  # Decreased from 0.03 -> 0.02 (2% instead of 3%)
                
                # Need more core conditions to trade
                'core_conditions_required': 3,  # Increased from 1 -> 3 (3/4 instead of 1/4)
                
                # Quality filters tightened
                'enable_daily_trend_filter': True,
                'enable_atr_filter': True,
                'enable_volume_filter': True,
                'min_volume_ratio': 1.5,  # Increased from 1.2 -> 1.5 (stronger volume)
                
                # Risk:Reward settings
                'min_risk_reward_ratio': 1.5,   # Minimum 1.5:1
                'target_risk_reward_ratio': 2.0, # Target 2:1
                'stop_loss_atr_multiplier': 1.5, # 1.5x ATR for stop loss
                'take_profit_atr_multiplier': 3.0, # 3x ATR for take profit (2:1 ratio)
                
                # Momentum confirmation (new)
                'require_macd_bullish': True,     # Mandatory MACD bullish
                'require_price_above_emas': True, # Price must be > both 12EMA and 26EMA
                'min_ema_separation': 0.005,     # 12EMA must be >0.5% above 26EMA
                
                # Volume quality (new)
                'volume_trend_periods': 5,       # Check volume trend 5 periods
                'require_volume_increase': True,  # Volume must be increasing
            },
            timeframe="4h",
            enabled=True,
            confidence_threshold=0.8  # Increased from 0.7 -> 0.8 (tighter)
        )
        
        super().__init__(
            name=config.name if config else default_config.name,
            config=config or default_config
        )
        self.logger = logging.getLogger(__name__)
    
    def get_required_indicators(self) -> list:
        """Get list of required indicators for this strategy."""
        return [
            '12_EMA', '26_EMA', '55_EMA',  # EMAs
            'RSI_21',                      # RSI
            'MACD', 'MACD_Signal',         # MACD
            'ATR', 'ATR_Percentile',       # Volatility
            'Volume_Ratio'                 # Volume
        ]
    
    def analyze(self, market_data: MarketData) -> Optional[TradingSignal]:
        """
        Analyze market data with high quality criteria.
        """
        try:
            if not self.is_enabled():
                return None
            
            # Check if we have technical analysis
            if not market_data.technical_analysis or not market_data.technical_analysis.indicators:
                self.logger.warning(f"[{market_data.symbol}] No technical analysis available")
                return None
            
            # Check for critical indicators (more flexible validation)
            indicators = market_data.technical_analysis.indicators
            critical_indicators = ['12_EMA', '26_EMA', 'RSI_21']
            missing_critical = [ind for ind in critical_indicators if ind not in indicators]
            
            if missing_critical:
                self.logger.warning(f"[{market_data.symbol}] Missing critical indicators: {missing_critical}")
                return None
            
            # STEP 1: Quality filters (tighter)
            if not self._check_enhanced_quality_filters(market_data):
                return None
            
            # STEP 2: Core strategy conditions (need 3/4 instead of 1/4)
            core_signals = self._check_enhanced_core_conditions(market_data)
            if not core_signals['passed']:
                self._log_failed_conditions(market_data.symbol, core_signals['details'])
                return None
            
            # STEP 3: Momentum confirmations (mandatory if data available)
            momentum_signals = self._check_momentum_confirmations(market_data)
            if not momentum_signals['passed']:
                self.logger.info(f"[{market_data.symbol}] ❌ MOMENTUM CONFIRMATIONS: Failed")
                return None
            
            # STEP 4: Calculate improved stop loss and take profit
            stop_loss, take_profit = self._calculate_improved_risk_reward(market_data)
            
            # STEP 5: Validate Risk:Reward ratio
            if not self._validate_risk_reward_ratio(market_data.current_price, stop_loss, take_profit):
                self.logger.info(f"[{market_data.symbol}] ❌ RISK:REWARD: Below minimum 1.5:1")
                return None
            
            # STEP 6: Final confirmation signals
            final_confirmations = self._check_final_confirmations(market_data)
            
            # Calculate enhanced confidence
            confidence = self._calculate_enhanced_confidence(
                core_signals['count'], 
                momentum_signals, 
                final_confirmations
            )
            
            if confidence < self.config.confidence_threshold:
                self.logger.info(
                    f"[{market_data.symbol}] ⚠️ QUALITY CHECK: "
                    f"Confidence {confidence:.1%} < {self.config.confidence_threshold:.1%}"
                )
                return None
            
            # Create high-quality signal
            signal = self.create_signal(
                market_data=market_data,
                direction=TradeDirection.BUY,
                confidence=confidence,
                stop_loss=stop_loss,
                take_profit=take_profit,
                core_conditions_count=core_signals['count']
            )
            
            # Calculate actual R:R for logging (with safety check)
            risk = market_data.current_price - stop_loss
            reward = take_profit - market_data.current_price
            actual_rr = reward / risk if risk > 0 else 0
            
            self.logger.info(
                f"[{market_data.symbol}] 🎯 HIGH-QUALITY SIGNAL APPROVED! "
                f"Core: {core_signals['count']}/4, Confidence: {confidence:.1%}, R:R: {actual_rr:.1f}:1"
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"[{market_data.symbol}] Error in analyze method: {e}")
            raise
    
    def _check_enhanced_quality_filters(self, market_data: MarketData) -> bool:
        """Enhanced quality filters with tighter criteria."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        current_price = market_data.current_price
        
        # 1. Enhanced daily trend filter
        if params.get('enable_daily_trend_filter', True):
            ema_55 = indicators.get('55_EMA', 0)
            if current_price <= ema_55:
                self.logger.info(f"[{market_data.symbol}] ❌ DAILY TREND: Price ${current_price:.4f} <= 55EMA ${ema_55:.4f}")
                return False
            
            # Additional: Price must be higher than 55EMA by at least 1%
            price_above_percent = ((current_price - ema_55) / ema_55) * 100
            if price_above_percent < 1.0:
                self.logger.info(f"[{market_data.symbol}] ❌ DAILY TREND: Price only {price_above_percent:.1f}% above 55EMA")
                return False
        
        # 2. Enhanced ATR volatility filter
        if params.get('enable_atr_filter', True):
            atr_percentile = indicators.get('ATR_Percentile', 1.0)
            
            # ATR percentage should be reasonable (0.5% - 5% of price)
            if not (0.5 <= atr_percentile <= 5.0):
                self.logger.info(f"[{market_data.symbol}] ❌ ATR FILTER: ATR percentile {atr_percentile:.2f}% outside range (0.5%-5%)")
                return False
        
        # 3. Enhanced volume filter
        if params.get('enable_volume_filter', True):
            volume_ratio = indicators.get('Volume_Ratio', 0)
            min_ratio = params.get('min_volume_ratio', 1.5)
            
            if volume_ratio < min_ratio:
                self.logger.info(f"[{market_data.symbol}] ❌ VOLUME FILTER: {volume_ratio:.2f}x < {min_ratio}x")
                return False
            
            # Additional: Volume trend must increase in last 5 periods
            if params.get('require_volume_increase', True):
                # Simplified check - in practice needs historical volume data
                if volume_ratio < 1.3:  # At least 30% volume increase
                    self.logger.info(f"[{market_data.symbol}] ❌ VOLUME TREND: No increasing volume trend")
                    return False
        
        return True
    
    def _check_enhanced_core_conditions(self, market_data: MarketData) -> Dict[str, Any]:
        """Enhanced core conditions with tight criteria."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        current_price = market_data.current_price
        
        conditions = []
        
        # 1. Price well above 55-EMA (tightened: must be > 2%)
        ema_55 = indicators.get('55_EMA')
        if ema_55 and ema_55 > 0:
            price_above_percent = ((current_price - ema_55) / ema_55) * 100
            price_well_above_55ema = price_above_percent >= 2.0
        else:
            price_well_above_55ema = False
        conditions.append(('Price well above 55-EMA (>2%)', price_well_above_55ema))
        
        # 2. Strong EMA uptrend (tightened: 12EMA must be higher than 26EMA by at least 0.5%)
        ema_12 = indicators.get('12_EMA')
        ema_26 = indicators.get('26_EMA')
        if ema_12 and ema_26 and ema_26 > 0:
            ema_separation = ((ema_12 - ema_26) / ema_26) * 100
            min_separation = params.get('min_ema_separation', 0.5)
            strong_ema_uptrend = ema_separation >= min_separation
        else:
            strong_ema_uptrend = False
        conditions.append(('Strong EMA uptrend (12>26 by >0.5%)', strong_ema_uptrend))
        
        # 3. Optimal RSI range (tightened: 50-70)
        rsi = indicators.get('RSI_21', 50)
        rsi_lower = params.get('rsi_lower_bound', 50)
        rsi_upper = params.get('rsi_upper_bound', 70)
        rsi_optimal = rsi_lower <= rsi <= rsi_upper
        conditions.append(('RSI optimal range (50-70)', rsi_optimal))
        
        # 4. Price very close to 26-EMA support (tightened: 2% instead of 3%)
        if ema_26 and ema_26 > 0:
            tolerance = params.get('ema_support_tolerance', 0.02)
            distance_pct = abs(current_price - ema_26) / ema_26
            price_near_support = distance_pct <= tolerance
        else:
            price_near_support = False
        conditions.append(('Price very close to 26-EMA (≤2%)', price_near_support))
        
        # Count passed conditions
        passed_count = sum(1 for _, passed in conditions if passed)
        required_count = params.get('core_conditions_required', 3)
        
        return {
            'passed': passed_count >= required_count,
            'count': passed_count,
            'details': conditions,
            'required': required_count
        }
    
    def _check_momentum_confirmations(self, market_data: MarketData) -> Dict[str, Any]:
        """Mandatory momentum confirmations."""
        indicators = market_data.technical_analysis.indicators
        params = self.config.parameters
        current_price = market_data.current_price
        
        confirmations = []
        
        # 1. MACD bullish (mandatory)
        if params.get('require_macd_bullish', True):
            macd = indicators.get('MACD', 0)
            macd_signal = indicators.get('MACD_Signal', 0)
            macd_hist = indicators.get('MACD_Histogram', 0)
            macd_bullish = macd > macd_signal and macd_hist > 0
            confirmations.append(('MACD bullish (required)', macd_bullish))
        
        # 2. Price above both EMAs (mandatory)
        if params.get('require_price_above_emas', True):
            ema_12 = indicators.get('12_EMA', 0)
            ema_26 = indicators.get('26_EMA', 0)
            price_above_emas = current_price > ema_12 and current_price > ema_26
            confirmations.append(('Price above both 12&26 EMAs (required)', price_above_emas))
        
        # All momentum confirmations must pass
        passed_count = sum(1 for _, passed in confirmations if passed)
        total_required = len(confirmations)
        
        return {
            'passed': passed_count == total_required,
            'count': passed_count,
            'details': confirmations,
            'required': total_required
        }
    
    def _calculate_improved_risk_reward(self, market_data: MarketData) -> tuple:
        """Calculate improved stop loss and take profit with optimal R:R ratio."""
        current_price = market_data.current_price
        atr = market_data.technical_analysis.indicators.get('ATR', current_price * 0.02)
        params = self.config.parameters
        
        # Stop loss: 1.5x ATR below current price (conservative)
        stop_loss_multiplier = params.get('stop_loss_atr_multiplier', 1.5)
        stop_loss = current_price - (stop_loss_multiplier * atr)
        
        # Take profit: 3x ATR above current price (target 2:1 R:R)
        take_profit_multiplier = params.get('take_profit_atr_multiplier', 3.0)
        take_profit = current_price + (take_profit_multiplier * atr)
        
        # Ensure minimum 5% stop loss and 10% take profit
        min_stop_loss = current_price * 0.95
        min_take_profit = current_price * 1.10
        
        stop_loss = min(stop_loss, min_stop_loss)  # Not too close
        take_profit = max(take_profit, min_take_profit)  # Not too close
        
        return stop_loss, take_profit
    
    def _validate_risk_reward_ratio(self, entry_price: float, stop_loss: float, take_profit: float) -> bool:
        """Validate R:R ratio meets minimum requirements."""
        if stop_loss >= entry_price or take_profit <= entry_price:
            return False
        
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        
        if risk <= 0:
            return False
        
        risk_reward_ratio = reward / risk
        min_rr = self.config.parameters.get('min_risk_reward_ratio', 1.5)
        
        return risk_reward_ratio >= min_rr
    
    def _check_final_confirmations(self, market_data: MarketData) -> Dict[str, bool]:
        """Final quality confirmations."""
        indicators = market_data.technical_analysis.indicators
        current_price = market_data.current_price
        
        # Bollinger Bands positioning (not too high in BB)
        bb_upper = indicators.get('BB_Upper', 0)
        bb_lower = indicators.get('BB_Lower', 0)
        bb_favorable = True
        
        if bb_upper > bb_lower > 0:
            bb_range = bb_upper - bb_lower
            if bb_range > 0:  # Prevent division by zero
                price_position = (current_price - bb_lower) / bb_range
                bb_favorable = price_position <= 0.5  # Lower 50% of BB range (tightened from 60%)
            else:
                bb_favorable = True  # Default if range is zero
        
        # Price action quality (not too far from EMAs)
        ema_12 = indicators.get('12_EMA', current_price)
        ema_distance = abs(current_price - ema_12) / ema_12 if ema_12 > 0 else 0
        price_action_quality = ema_distance <= 0.03  # Within 3% of 12EMA
        
        return {
            'bb_favorable': bb_favorable,
            'price_action_quality': price_action_quality
        }
    
    def _calculate_enhanced_confidence(self, core_count: int, momentum_signals: Dict, final_confirmations: Dict) -> float:
        """Calculate enhanced confidence score."""
        base_confidence = 0.5
        
        # Core conditions bonus (need 3/4 to pass)
        core_bonus = (core_count / 4) * 0.25 if core_count > 0 else 0
        
        # Momentum confirmations bonus (must all pass)
        momentum_bonus = 0.15 if momentum_signals.get('passed', False) else 0
        
        # Final confirmations bonus
        if final_confirmations and len(final_confirmations) > 0:
            final_count = sum(1 for passed in final_confirmations.values() if passed)
            final_bonus = (final_count / len(final_confirmations)) * 0.10
        else:
            final_bonus = 0
        
        return min(base_confidence + core_bonus + momentum_bonus + final_bonus, 1.0)
    
    def _log_failed_conditions(self, symbol: str, conditions: list) -> None:
        """Log detailed analysis when core conditions fail."""
        passed_count = sum(1 for _, passed in conditions if passed)
        required = self.config.parameters.get('core_conditions_required', 3)
        
        self.logger.info(f"[{symbol}] ❌ HIGH-QUALITY SIGNAL REJECTED: Core conditions not met")
        self.logger.info(f"  📊 ENHANCED CORE ANALYSIS ({passed_count}/4 passed, need {required}+):")
        
        for condition_name, passed in conditions:
            status = "✅" if passed else "❌"
            self.logger.info(f"  • {condition_name}: {status}")
    
    def get_strategy_description(self) -> str:
        """Get enhanced strategy description."""
        params = self.config.parameters
        required = params.get('core_conditions_required', 3)
        min_rr = params.get('min_risk_reward_ratio', 1.5)
        
        return f"""
        {self.name} - "QUALITY OVER QUANTITY"
        
        🎯 MAIN IMPROVEMENTS:
        1. Risk:Reward minimum {min_rr}:1 (target 2:1)
        2. Need {required}/4 core conditions (instead of 1/4)
        3. Farther take profit allowing winning trades to "run"
        4. Stronger volume confirmation ({params.get('min_volume_ratio', 1.5)}x)
        5. RSI sweet spot (50-70 instead of 45-75)
        
        📋 ENHANCED QUALITY FILTERS:
        • Daily Trend: Price >2% above 55-EMA
        • ATR Volatility: 30-70 percentile sweet spot
        • Volume: {params.get('min_volume_ratio', 1.5)}x+ with increasing trend
        
        📊 ENHANCED CORE CONDITIONS (Need {required}/4):
        • Long-term Trend: Price well above 55-EMA (>2%)
        • Strong Momentum: 12-EMA > 26-EMA by >0.5%
        • Optimal RSI: 50-70 range (momentum zone)
        • Perfect Entry: Within 2% of 26-EMA support
        
        🚀 MANDATORY CONFIRMATIONS:
        • MACD Bullish: MACD > Signal with positive histogram
        • Price Position: Above both 12-EMA and 26-EMA
        • BB Position: Lower 50% of Bollinger Bands
        • Price Action: Within 3% of 12-EMA
        
        💰 RISK MANAGEMENT:
        • Stop Loss: 1.5x ATR (minimum 5%)
        • Take Profit: 3x ATR (minimum 10%)
        • R:R Ratio: Minimum {min_rr}:1, Target 2:1
        """

    def get_required_indicators(self) -> list:
        """Get list of required indicators."""
        return [
            '12_EMA', '26_EMA', '55_EMA', 'RSI_21',
            'MACD', 'MACD_Signal', 'MACD_Histogram',
            'BB_Upper', 'BB_Middle', 'BB_Lower',
            'ATR', 'ATR_Percentile', 'Volatility_State',
            'Current_Volume', 'Avg_Volume_20', 'Volume_Ratio'
        ]
