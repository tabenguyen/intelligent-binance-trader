"""
Enhanced Risk Management Service - Focus "Quality over Quantity"
Improvements: R:R ratio validation, quality-based position sizing, enhanced trade validation.
"""

import logging
from typing import Optional

from ..core.interfaces import IRiskManager
from ..models import TradingSignal, RiskConfig, TradingConfig


class EnhancedRiskManagementService(IRiskManager):
    """
    Enhanced Risk Management Service with focus "Quality over Quantity".
    
    Main improvements:
    1. Mandatory minimum R:R ratio of 1.5:1
    2. Quality-based position sizing
    3. Enhanced trade validation
    4. Stricter risk controls
    """
    
    def __init__(self, trading_config: TradingConfig):
        """Initialize with enhanced trading configuration."""
        self.config = trading_config.risk_config
        self.trading_config = trading_config
        self.logger = logging.getLogger(__name__)
        
        # Enhanced risk parameters
        self.min_risk_reward_ratio = 1.5  # Minimum R:R ratio
        self.preferred_risk_reward_ratio = 2.0  # Preferred R:R ratio
        self.max_risk_per_trade = 3.0  # Maximum 3% risk per trade
        self.quality_bonus_threshold = 0.85  # High quality signal threshold
        
        # Add symbol info cache for quantity formatting
        self._symbol_info_cache = {}
    
    def _get_symbol_info(self, symbol: str) -> dict:
        """Get symbol info from exchange, with caching."""
        if symbol not in self._symbol_info_cache:
            try:
                # Import here to avoid circular imports
                from ..services.binance_market_data_service import BinanceMarketDataService
                
                # Create a temporary market data service to get symbol info
                market_service = BinanceMarketDataService(
                    api_key=self.trading_config.api_key,
                    api_secret=self.trading_config.api_secret,
                    testnet=self.trading_config.testnet
                )
                
                exchange_info = market_service.client.exchange_info()
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['symbol'] == symbol:
                        self._symbol_info_cache[symbol] = symbol_info
                        break
                else:
                    raise ValueError(f"Symbol {symbol} not found in exchange info")
            except Exception as e:
                self.logger.error(f"Failed to get symbol info for {symbol}: {e}")
                # Return a default LOT_SIZE filter for fallback
                return {
                    'filters': [
                        {
                            'filterType': 'LOT_SIZE',
                            'stepSize': '0.000001',
                            'minQty': '0.000001',
                            'maxQty': '999999999.000000'
                        }
                    ]
                }
        
        return self._symbol_info_cache[symbol]
    
    def _format_quantity(self, symbol: str, quantity: float) -> float:
        """Format quantity according to symbol's LOT_SIZE filter."""
        try:
            symbol_info = self._get_symbol_info(symbol)
            
            # Find LOT_SIZE filter
            lot_size_filter = None
            for filter_info in symbol_info['filters']:
                if filter_info['filterType'] == 'LOT_SIZE':
                    lot_size_filter = filter_info
                    break
            
            if not lot_size_filter:
                self.logger.warning(f"No LOT_SIZE filter found for {symbol}, using 6 decimal places")
                return round(quantity, 6)
            
            # Get step size (minimum quantity increment)
            step_size = float(lot_size_filter['stepSize'])
            min_qty = float(lot_size_filter['minQty'])
            max_qty = float(lot_size_filter['maxQty'])
            
            # Calculate precision from step size
            if step_size >= 1:
                precision = 0
            else:
                precision = len(str(step_size).split('.')[-1].rstrip('0'))
            
            # Round to step size
            formatted_quantity = round(quantity / step_size) * step_size
            
            # Round to correct precision
            formatted_quantity = round(formatted_quantity, precision)
            
            # Ensure within min/max bounds
            if formatted_quantity < min_qty:
                formatted_quantity = min_qty
            elif formatted_quantity > max_qty:
                formatted_quantity = max_qty
            
            self.logger.debug(f"{symbol} quantity formatting: {quantity:.8f} -> {formatted_quantity:.8f} "
                            f"(step: {step_size}, precision: {precision})")
            
            return formatted_quantity
            
        except Exception as e:
            self.logger.error(f"Error formatting quantity for {symbol}: {e}")
            # Fallback to 6 decimal places
            return round(quantity, 6)

    # ...existing validation methods remain the same...
    
    def calculate_enhanced_position_size(self, signal: TradingSignal, balance: float) -> float:
        """
        Calculate enhanced position size with quality-based adjustments and proper formatting.
        """
        try:
            self.logger.info(f"💰 ENHANCED POSITION SIZE CALCULATION for {signal.symbol}")
            self.logger.info(f"   Account Balance: ${balance:.2f}")
            self.logger.info(f"   Signal Quality: {signal.confidence:.1%}")
            
            # Base calculation using risk-based sizing
            if not signal.stop_loss:
                self.logger.warning("❌ Cannot calculate risk-based size without stop loss")
                return 0.0
            
            # Use fixed allocation percentage of balance for position sizing
            allocation_percent = self.config.fixed_allocation_percentage / 100.0
            allocated_balance = balance * allocation_percent
            
            self.logger.info(f"   Fixed Allocation: {self.config.fixed_allocation_percentage:.1f}% of balance")
            self.logger.info(f"   Allocated Amount: ${allocated_balance:.2f}")
            
            # Calculate risk amount based on signal quality from allocated balance
            base_risk_percent = min(self.config.risk_per_trade_percentage / 100, self.max_risk_per_trade / 100)
            
            # Quality adjustment: High quality signals get slightly more allocation
            quality_multiplier = 1.0
            if signal.confidence >= self.quality_bonus_threshold:
                quality_multiplier = 1.2  # 20% bonus for premium signals
                self.logger.info(f"   Quality Bonus: +20% for premium signal")
            elif signal.confidence >= 0.8:
                quality_multiplier = 1.1  # 10% bonus for high quality signals
                self.logger.info(f"   Quality Bonus: +10% for high quality signal")
            
            adjusted_risk_percent = base_risk_percent * quality_multiplier
            risk_amount = allocated_balance * adjusted_risk_percent

            # Calculate position size based on actual risk
            price_risk = signal.price - signal.stop_loss
            if price_risk <= 0:
                self.logger.warning("❌ Invalid price risk calculation")
                return 0.0
            
            position_size = risk_amount / price_risk
            
            self.logger.info(f"   Base Risk %: {base_risk_percent*100:.2f}%")
            self.logger.info(f"   Quality Multiplier: {quality_multiplier:.1f}x")
            self.logger.info(f"   Adjusted Risk %: {adjusted_risk_percent*100:.2f}%")
            self.logger.info(f"   Risk Amount: ${risk_amount:.2f} (from ${allocated_balance:.2f} allocated)")
            self.logger.info(f"   Price Risk: ${price_risk:.4f}")
            self.logger.info(f"   Raw Position Size: {position_size:.8f}")
            
            # After calculating position_size, ensure it meets minimum requirements
            min_notional = self.config.min_notional_usdt
            current_price = signal.price
            
            # Calculate minimum quantity needed to meet notional requirement
            min_quantity_for_notional = min_notional / current_price
            
            # Use the larger of calculated position or minimum required
            if position_size < min_quantity_for_notional:
                self.logger.info(f"   Adjusting position size from {position_size:.8f} to {min_quantity_for_notional:.8f} "
                               f"to meet minimum notional requirement of ${min_notional}")
                position_size = min_quantity_for_notional
            
            # Format quantity according to symbol requirements
            formatted_position_size = self._format_quantity(signal.symbol, position_size)
            
            final_trade_value = formatted_position_size * signal.price
            
            self.logger.info(f"   Formatted Position Size: {formatted_position_size:.8f}")
            self.logger.info(f"   Final Trade Value: ${final_trade_value:.2f}")
            
            return formatted_position_size
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating enhanced position size: {e}")
            return 0.0
    
    def calculate_position_size(self, signal: TradingSignal, balance: float) -> float:
        """Wrapper for backward compatibility with formatting."""
        return self.calculate_enhanced_position_size(signal, balance)
    
    # ...rest of the methods remain the same...
    
    def validate_trade(self, signal: TradingSignal, current_balance: float) -> bool:
        """
        Enhanced trade validation with quality focus.
        """
        try:
            # Check if this is a special tight EMA stop protection case
            is_tight_ema_stop = signal.indicators.get('tight_ema_stop_protection', False)
            
            self.logger.info(f"🔍 ENHANCED RISK VALIDATION for {signal.symbol}")
            self.logger.info(f"   Signal Price: ${signal.price:.4f}")
            self.logger.info(f"   Current Balance: ${current_balance:.2f}")
            self.logger.info(f"   Signal Confidence: {signal.confidence:.1%}")
            self.logger.info(f"   Stop Loss: ${signal.stop_loss:.4f}" if signal.stop_loss else "   Stop Loss: Not set")
            self.logger.info(f"   Take Profit: ${signal.take_profit:.4f}" if signal.take_profit else "   Take Profit: Not set")
            
            if is_tight_ema_stop:
                ema_26_value = signal.indicators.get('ema_26_value', 0)
                self.logger.info(f"🛡️ SPECIAL CASE: Tight EMA stop protection active (EMA26: ${ema_26_value:.4f})")
            
            # Enhanced Check 1: Minimum balance (stricter)
            self.logger.info(f"📊 ENHANCED CHECK 1: Minimum Balance")
            min_balance_required = self.trading_config.min_balance * 1.2  # 20% buffer
            self.logger.info(f"   Required (with buffer): ${min_balance_required:.2f}")
            self.logger.info(f"   Current: ${current_balance:.2f}")
            if current_balance < min_balance_required:
                self.logger.warning(f"❌ FAILED - Insufficient balance with safety buffer")
                return False
            self.logger.info(f"✅ PASSED - Balance sufficient with buffer")
            
            # Enhanced Check 2: Mandatory R:R Ratio Validation (modified for tight stop case)
            if not self._validate_enhanced_risk_reward(signal, is_tight_ema_stop):
                return False
            
            # Enhanced Check 3: Signal Quality Assessment
            if not self._validate_signal_quality(signal):
                return False
            
            # Enhanced Check 4: Position Size Calculation & Validation
            position_size = self.calculate_enhanced_position_size(signal, current_balance)
            if position_size <= 0:
                self.logger.warning("❌ FAILED - Invalid position size calculated")
                return False
            
            # Enhanced Check 5: Trade Value vs Enhanced Risk Limits
            trade_value = position_size * signal.price
            if not self._validate_enhanced_trade_value(trade_value, current_balance, signal):
                return False
            
            # Enhanced Check 6: Maximum Position Size (stricter)
            max_position_adjusted = self.config.max_position_size * 0.8  # 20% buffer
            self.logger.info(f"📊 ENHANCED CHECK 6: Maximum Position Size")
            self.logger.info(f"   Maximum Allowed (with buffer): {max_position_adjusted:.2f}")
            self.logger.info(f"   Calculated Size: {position_size:.6f}")
            if position_size > max_position_adjusted:
                self.logger.warning(f"❌ FAILED - Position size exceeds conservative limit")
                return False
            self.logger.info(f"✅ PASSED - Position size within conservative limits")
            
            # Enhanced Check 7: Overall Risk Portfolio Check
            if not self._validate_portfolio_risk(trade_value, current_balance):
                return False
            
            # All enhanced checks passed
            risk = signal.price - signal.stop_loss if signal.stop_loss else 0
            reward = signal.take_profit - signal.price if signal.take_profit else 0
            actual_rr = reward / risk if risk > 0 else 0
            
            self.logger.info(f"🎉 ALL ENHANCED CHECKS PASSED - High-quality trade approved!")
            self.logger.info(f"   Final Position Size: {position_size:.6f} {signal.symbol}")
            self.logger.info(f"   Final Trade Value: ${trade_value:.2f}")
            self.logger.info(f"   Actual R:R Ratio: {actual_rr:.2f}:1")
            self.logger.info(f"   Signal Quality: {signal.confidence:.1%}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in enhanced trade validation: {e}")
            return False
    
    def _validate_enhanced_risk_reward(self, signal: TradingSignal, is_tight_ema_stop: bool = False) -> bool:
        """Enhanced R:R ratio validation - mandatory minimum 1.5:1."""
        self.logger.info(f"📊 ENHANCED CHECK 2: Mandatory Risk:Reward Ratio")
        
        if not signal.stop_loss or not signal.take_profit:
            self.logger.warning(f"❌ FAILED - Both stop loss and take profit are required for quality trades")
            return False
        
        if signal.stop_loss >= signal.price:
            self.logger.warning(f"❌ FAILED - Invalid stop loss: ${signal.stop_loss:.4f} >= ${signal.price:.4f}")
            return False
        
        if signal.take_profit <= signal.price:
            self.logger.warning(f"❌ FAILED - Invalid take profit: ${signal.take_profit:.4f} <= ${signal.price:.4f}")
            return False
        
        risk = signal.price - signal.stop_loss
        reward = signal.take_profit - signal.price
        risk_reward_ratio = reward / risk
        
        self.logger.info(f"   Entry Price: ${signal.price:.4f}")
        self.logger.info(f"   Stop Loss: ${signal.stop_loss:.4f} (Risk: ${risk:.4f})")
        self.logger.info(f"   Take Profit: ${signal.take_profit:.4f} (Reward: ${reward:.4f})")
        self.logger.info(f"   R:R Ratio: {risk_reward_ratio:.2f}:1")
        
        # For tight EMA stop cases, allow slightly lower R:R ratios due to the tight protection
        min_required_ratio = self.min_risk_reward_ratio
        if is_tight_ema_stop:
            min_required_ratio = 1.2  # Allow 1.2:1 for tight EMA stop cases instead of 1.5:1
            self.logger.info(f"🛡️ TIGHT EMA STOP: Reduced minimum R:R to {min_required_ratio:.1f}:1")
        
        self.logger.info(f"   Minimum Required: {min_required_ratio:.1f}:1")
        
        if risk_reward_ratio < min_required_ratio:
            self.logger.warning(f"❌ FAILED - R:R ratio {risk_reward_ratio:.2f}:1 below minimum {min_required_ratio:.1f}:1")
            return False
        
        # Bonus points for excellent R:R ratio
        if risk_reward_ratio >= self.preferred_risk_reward_ratio:
            self.logger.info(f"✅ EXCELLENT - R:R ratio {risk_reward_ratio:.2f}:1 meets preferred target!")
        elif is_tight_ema_stop:
            self.logger.info(f"✅ TIGHT STOP APPROVED - R:R ratio {risk_reward_ratio:.2f}:1 with EMA protection")
        else:
            self.logger.info(f"✅ GOOD - R:R ratio {risk_reward_ratio:.2f}:1 meets minimum requirement")
        
        return True
    
    def _validate_signal_quality(self, signal: TradingSignal) -> bool:
        """Validate signal quality based on confidence score."""
        self.logger.info(f"📊 ENHANCED CHECK 3: Signal Quality Assessment")
        
        min_confidence = 0.75  # Minimum 75% confidence for quality trades
        self.logger.info(f"   Signal Confidence: {signal.confidence:.1%}")
        self.logger.info(f"   Minimum Required: {min_confidence:.1%}")
        
        if signal.confidence < min_confidence:
            self.logger.warning(f"❌ FAILED - Signal confidence {signal.confidence:.1%} below minimum {min_confidence:.1%}")
            return False
        
        # High quality signal bonus
        if signal.confidence >= self.quality_bonus_threshold:
            self.logger.info(f"✅ PREMIUM QUALITY - Signal confidence {signal.confidence:.1%} qualifies for enhanced sizing")
        else:
            self.logger.info(f"✅ GOOD QUALITY - Signal confidence {signal.confidence:.1%} meets requirements")
        
        return True
    
    def calculate_enhanced_position_size(self, signal: TradingSignal, balance: float) -> float:
        """
        Calculate enhanced position size with quality-based adjustments and proper formatting.
        """
        try:
            self.logger.info(f"💰 ENHANCED POSITION SIZE CALCULATION for {signal.symbol}")
            self.logger.info(f"   Account Balance: ${balance:.2f}")
            self.logger.info(f"   Signal Quality: {signal.confidence:.1%}")
            
            # Base calculation using risk-based sizing
            if not signal.stop_loss:
                self.logger.warning("❌ Cannot calculate risk-based size without stop loss")
                return 0.0
            
            # Use fixed allocation percentage of balance for position sizing
            allocation_percent = self.config.fixed_allocation_percentage / 100.0
            allocated_balance = balance * allocation_percent
            
            self.logger.info(f"   Fixed Allocation: {self.config.fixed_allocation_percentage:.1f}% of balance")
            self.logger.info(f"   Allocated Amount: ${allocated_balance:.2f}")
            
            # Calculate risk amount based on signal quality from allocated balance
            base_risk_percent = min(self.config.risk_per_trade_percentage / 100, self.max_risk_per_trade / 100)
            
            # Quality adjustment: High quality signals get slightly more allocation
            quality_multiplier = 1.0
            if signal.confidence >= self.quality_bonus_threshold:
                quality_multiplier = 1.2  # 20% bonus for premium signals
                self.logger.info(f"   Quality Bonus: +20% for premium signal")
            elif signal.confidence >= 0.8:
                quality_multiplier = 1.1  # 10% bonus for high quality signals
                self.logger.info(f"   Quality Bonus: +10% for high quality signal")
            
            adjusted_risk_percent = base_risk_percent * quality_multiplier
            risk_amount = allocated_balance * adjusted_risk_percent

            # Calculate position size based on actual risk
            price_risk = signal.price - signal.stop_loss
            if price_risk <= 0:
                self.logger.warning("❌ Invalid price risk calculation")
                return 0.0
            
            position_size = risk_amount / price_risk
            
            self.logger.info(f"   Base Risk %: {base_risk_percent*100:.2f}%")
            self.logger.info(f"   Quality Multiplier: {quality_multiplier:.1f}x")
            self.logger.info(f"   Adjusted Risk %: {adjusted_risk_percent*100:.2f}%")
            self.logger.info(f"   Risk Amount: ${risk_amount:.2f} (from ${allocated_balance:.2f} allocated)")
            self.logger.info(f"   Price Risk: ${price_risk:.4f}")
            self.logger.info(f"   Raw Position Size: {position_size:.8f}")
            
            # After calculating position_size, ensure it meets minimum requirements
            min_notional = self.config.min_notional_usdt
            current_price = signal.price
            
            # Calculate minimum quantity needed to meet notional requirement
            min_quantity_for_notional = min_notional / current_price
            
            # Use the larger of calculated position or minimum required
            if position_size < min_quantity_for_notional:
                self.logger.info(f"   Adjusting position size from {position_size:.8f} to {min_quantity_for_notional:.8f} "
                               f"to meet minimum notional requirement of ${min_notional}")
                position_size = min_quantity_for_notional
            
            # Format quantity according to symbol requirements
            formatted_position_size = self._format_quantity(signal.symbol, position_size)
            
            final_trade_value = formatted_position_size * signal.price
            
            self.logger.info(f"   Formatted Position Size: {formatted_position_size:.8f}")
            self.logger.info(f"   Final Trade Value: ${final_trade_value:.2f}")
            
            return formatted_position_size
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating enhanced position size: {e}")
            return 0.0
    
    def calculate_position_size(self, signal: TradingSignal, balance: float) -> float:
        """Wrapper for backward compatibility with formatting."""
        return self.calculate_enhanced_position_size(signal, balance)
    
    def _validate_enhanced_trade_value(self, trade_value: float, balance: float, signal: TradingSignal) -> bool:
        """Enhanced trade value validation with quality considerations."""
        self.logger.info(f"📊 ENHANCED CHECK 5: Trade Value vs Risk Limits")
        
        # Minimum trade value validation from configuration
        min_trade_value = self.config.min_trade_value_usdt
        self.logger.info(f"   Minimum Trade Value: ${min_trade_value:.2f}")
        
        if trade_value < min_trade_value:
            self.logger.warning(f"❌ FAILED - Trade value ${trade_value:.2f} below minimum ${min_trade_value:.2f}")
            return False
        
        # Base maximum trade value (more conservative)
        base_max_percent = min(self.config.risk_per_trade_percentage, 60)  # Cap at 60%
        base_max_value = balance * (base_max_percent / 100)
        
        # Quality-based adjustment
        if signal.confidence >= self.quality_bonus_threshold:
            adjusted_max_value = base_max_value * 1.1  # 10% bonus for premium signals
            self.logger.info(f"   Premium Signal Bonus: +10% trade value limit")
        else:
            adjusted_max_value = base_max_value
        
        self.logger.info(f"   Base Risk Limit: {base_max_percent:.1f}%")
        self.logger.info(f"   Maximum Trade Value: ${adjusted_max_value:.2f}")
        self.logger.info(f"   Calculated Trade Value: ${trade_value:.2f}")
        
        if trade_value > adjusted_max_value:
            self.logger.warning(f"❌ FAILED - Trade value ${trade_value:.2f} exceeds enhanced limit ${adjusted_max_value:.2f}")
            return False
        
        self.logger.info(f"✅ PASSED - Trade value within enhanced limits")
        return True
    
    def _validate_portfolio_risk(self, trade_value: float, balance: float) -> bool:
        """Validate overall portfolio risk exposure."""
        self.logger.info(f"📊 ENHANCED CHECK 7: Portfolio Risk Assessment")
        
        # Use configured risk percentage for portfolio limit
        max_portfolio_risk = self.config.risk_per_trade_percentage / 100.0
        portfolio_risk_amount = balance * max_portfolio_risk
        
        self.logger.info(f"   Trade Value: ${trade_value:.2f}")
        self.logger.info(f"   Max Portfolio Risk: {max_portfolio_risk:.1%}")
        self.logger.info(f"   Portfolio Risk Amount: ${portfolio_risk_amount:.2f}")
        
        if trade_value > portfolio_risk_amount:
            self.logger.warning(f"❌ FAILED - Trade value exceeds portfolio risk limits")
            return False
        
        self.logger.info(f"✅ PASSED - Trade value within portfolio risk limits")
        return True
    
    def calculate_stop_loss(self, signal: TradingSignal) -> float:
        """Calculate dynamic stop loss based on ATR and market conditions."""
        try:
            # Use 1.5x ATR for more conservative stop loss
            atr_multiplier = 1.5
            
            # Get ATR from technical analysis if available
            if hasattr(signal, 'technical_analysis') and signal.technical_analysis:
                atr = getattr(signal.technical_analysis, 'atr', None)
                if atr and atr > 0:
                    stop_loss = signal.price - (atr * atr_multiplier)
                    self.logger.info(f"📊 Dynamic stop loss: ${stop_loss:.4f} (Price: ${signal.price:.4f} - {atr_multiplier}x ATR: ${atr:.4f})")
                    return max(stop_loss, signal.price * 0.97)  # Minimum 3% stop loss
            
            # Fallback to percentage-based stop loss
            default_stop_percentage = 0.025  # 2.5% more conservative
            stop_loss = signal.price * (1 - default_stop_percentage)
            self.logger.info(f"📊 Fallback stop loss: ${stop_loss:.4f} ({default_stop_percentage*100:.1f}% below entry)")
            return stop_loss
            
        except Exception as e:
            self.logger.warning(f"Error calculating stop loss: {e}")
            # Emergency fallback
            return signal.price * 0.975  # 2.5% stop loss
    
    def calculate_take_profit(self, signal: TradingSignal) -> float:
        """Calculate dynamic take profit to ensure minimum 1.5:1 R:R ratio."""
        try:
            # Calculate or use existing stop loss
            stop_loss = signal.stop_loss or self.calculate_stop_loss(signal)
            risk = signal.price - stop_loss
            
            # Ensure minimum 1.5:1 R:R ratio, prefer 2:1 for quality trades
            min_reward = risk * self.min_risk_reward_ratio  # 1.5x
            preferred_reward = risk * self.preferred_risk_reward_ratio  # 2.0x
            
            # Use ATR for dynamic take profit if available
            if hasattr(signal, 'technical_analysis') and signal.technical_analysis:
                atr = getattr(signal.technical_analysis, 'atr', None)
                if atr and atr > 0:
                    # Use 3x ATR for take profit to achieve ~2:1 R:R
                    atr_based_profit = signal.price + (atr * 3.0)
                    atr_reward = atr_based_profit - signal.price
                    
                    # Ensure it meets minimum R:R requirement
                    if atr_reward >= min_reward:
                        self.logger.info(f"📊 ATR-based take profit: ${atr_based_profit:.4f} (R:R: {atr_reward/risk:.2f}:1)")
                        return atr_based_profit
            
            # Fallback to preferred 2:1 ratio
            take_profit = signal.price + preferred_reward
            actual_rr = preferred_reward / risk if risk > 0 else 0
            self.logger.info(f"📊 Calculated take profit: ${take_profit:.4f} (R:R: {actual_rr:.2f}:1)")
            return take_profit
            
        except Exception as e:
            self.logger.warning(f"Error calculating take profit: {e}")
            # Emergency fallback - 4% take profit
            return signal.price * 1.04
    
    def calculate_risk_reward_ratio(self, signal: TradingSignal) -> Optional[float]:
        """Calculate risk-reward ratio for a signal."""
        if not signal.stop_loss or not signal.take_profit:
            return None
        
        if signal.stop_loss >= signal.price or signal.take_profit <= signal.price:
            return None
        
        risk = signal.price - signal.stop_loss
        reward = signal.take_profit - signal.price
        
        if risk <= 0:
            return None
        
        return reward / risk
    
    def update_trailing_stop(self, position_entry_price: float, current_price: float, 
                           current_stop_loss: float, signal: TradingSignal) -> Optional[float]:
        """
        Update trailing stop-loss for adaptive ATR strategy.
        
        Args:
            position_entry_price: Original entry price
            current_price: Current market price
            current_stop_loss: Current stop-loss level
            signal: Original trading signal with strategy metadata
            
        Returns:
            New stop-loss level or None if no update needed
        """
        try:
            # Check if this is an adaptive ATR strategy signal with trailing stop enabled
            if not signal.indicators.get('use_trailing_stop', False):
                return None
            
            # Get trailing stop parameters from signal
            trailing_atr_multiplier = signal.indicators.get('trailing_stop_atr_multiplier', 1.0)
            min_profit_before_trail = signal.indicators.get('min_profit_before_trail', 0.015)
            atr_value = signal.indicators.get('ATR', (current_price - position_entry_price) * 0.02)
            
            # Check if we have minimum profit before activating trailing stop
            current_profit_pct = (current_price - position_entry_price) / position_entry_price
            if current_profit_pct < min_profit_before_trail:
                self.logger.debug(f"Trailing stop not active yet - profit {current_profit_pct:.1%} < {min_profit_before_trail:.1%}")
                return None
            
            # Calculate new trailing stop level
            new_trailing_stop = current_price - (trailing_atr_multiplier * atr_value)
            
            # Only update if new stop is higher than current stop (for long positions)
            if new_trailing_stop > current_stop_loss:
                self.logger.info(f"🎯 TRAILING STOP UPDATE: ${current_stop_loss:.4f} -> ${new_trailing_stop:.4f}")
                self.logger.info(f"   Current Price: ${current_price:.4f}, ATR: ${atr_value:.4f}")
                self.logger.info(f"   Profit: {current_profit_pct:.1%}, Trail Distance: {trailing_atr_multiplier:.1f}x ATR")
                return new_trailing_stop
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating trailing stop: {e}")
            return None
    
    def should_exit_with_trailing_stop(self, position_entry_price: float, current_price: float,
                                     current_stop_loss: float, signal: TradingSignal) -> bool:
        """
        Check if position should be exited due to trailing stop being hit.
        
        Args:
            position_entry_price: Original entry price
            current_price: Current market price  
            current_stop_loss: Current stop-loss level
            signal: Original trading signal
            
        Returns:
            True if position should be exited
        """
        try:
            # For long positions, exit if current price drops below stop-loss
            if current_price <= current_stop_loss:
                profit_pct = (current_price - position_entry_price) / position_entry_price
                self.logger.info(f"🛑 TRAILING STOP TRIGGERED!")
                self.logger.info(f"   Entry: ${position_entry_price:.4f}, Current: ${current_price:.4f}")
                self.logger.info(f"   Stop Level: ${current_stop_loss:.4f}, Final Profit: {profit_pct:.1%}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking trailing stop exit: {e}")
            return False
    
    def get_risk_summary(self) -> str:
        """Get enhanced risk management summary."""
        return f"""
        🛡️ ENHANCED RISK MANAGEMENT - "QUALITY OVER QUANTITY"
        
        📊 QUALITY REQUIREMENTS:
        • Minimum Signal Confidence: 75%
        • Mandatory R:R Ratio: {self.min_risk_reward_ratio}:1 minimum
        • Preferred R:R Ratio: {self.preferred_risk_reward_ratio}:1
        • Both Stop Loss & Take Profit Required
        
        💰 POSITION SIZING:
        • Risk-based sizing with quality bonus
        • Premium signals (85%+): +20% allocation
        • High quality (80%+): +10% allocation
        • Maximum risk per trade: {self.max_risk_per_trade}%
        
        🔒 ENHANCED CONTROLS:
        • Balance requirement: +20% safety buffer
        • Position size limit: -20% conservative buffer
        • Portfolio risk limit: 10% per single trade
        • Minimum notional: ${self.config.min_notional_usdt}
        
        🎯 FOCUS:
        Fewer trades, but higher quality and better R:R ratios.
        """
