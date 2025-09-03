"""
Risk Management Service - Single Responsibility: Manage trading risks.
"""

import logging
from typing import Optional

from ..core.interfaces import IRiskManager
from ..models import TradingSignal, RiskConfig, TradingConfig


class RiskManagementService(IRiskManager):
    """
    Service responsible for risk management calculations and validations.
    Implements various position sizing and risk control methods.
    """
    
    def __init__(self, trading_config: TradingConfig):
        """Initialize with trading configuration."""
        self.config = trading_config.risk_config
        self.trading_config = trading_config
        self.logger = logging.getLogger(__name__)
    
    def validate_trade(self, signal: TradingSignal, current_balance: float) -> bool:
        """
        Validate if a trade meets risk criteria.
        
        Args:
            signal: Trading signal to validate
            current_balance: Current account balance
            
        Returns:
            True if trade is acceptable, False otherwise
        """
        try:
            self.logger.info(f"🔍 RISK MANAGEMENT VALIDATION for {signal.symbol}")
            self.logger.info(f"   Signal Price: ${signal.price:.4f}")
            self.logger.info(f"   Current Balance: ${current_balance:.2f}")
            self.logger.info(f"   Stop Loss: ${signal.stop_loss:.4f}" if signal.stop_loss else "   Stop Loss: Not set")
            self.logger.info(f"   Take Profit: ${signal.take_profit:.4f}" if signal.take_profit else "   Take Profit: Not set")
            
            # Check 1: Minimum balance requirement
            self.logger.info(f"📊 CHECK 1: Minimum Balance")
            self.logger.info(f"   Required: ${self.trading_config.min_balance:.2f}")
            self.logger.info(f"   Current: ${current_balance:.2f}")
            if current_balance < self.trading_config.min_balance:
                self.logger.warning(f"❌ FAILED - Insufficient balance: ${current_balance:.2f} < ${self.trading_config.min_balance:.2f}")
                return False
            self.logger.info(f"✅ PASSED - Balance sufficient")
            
            # Calculate position size for further checks
            position_size = self.calculate_position_size(signal, current_balance)
            self.logger.info(f"💰 Calculated Position Size: {position_size:.6f} {signal.symbol}")

            # Reject trades with zero or negative calculated size (e.g., below $10 notional)
            if position_size <= 0:
                self.logger.warning("❌ FAILED - Calculated position size is 0; cannot place order below $10 notional or with invalid sizing")
                return False
            
            # Check 2: Maximum position size limit
            self.logger.info(f"📊 CHECK 2: Maximum Position Size")
            self.logger.info(f"   Maximum Allowed: {self.config.max_position_size:.2f}")
            self.logger.info(f"   Calculated Size: {position_size:.6f}")
            if position_size > self.config.max_position_size:
                self.logger.warning(f"❌ FAILED - Position size {position_size:.6f} exceeds maximum {self.config.max_position_size:.2f}")
                return False
            self.logger.info(f"✅ PASSED - Position size within limits")
            
            # Check 3: Trade value vs risk per trade percentage
            trade_value = position_size * signal.price
            max_trade_value = current_balance * (self.config.risk_per_trade_percentage / 100)
            self.logger.info(f"📊 CHECK 3: Risk Per Trade Limit")
            self.logger.info(f"   Risk Percentage: {self.config.risk_per_trade_percentage}%")
            self.logger.info(f"   Maximum Trade Value: ${max_trade_value:.2f}")
            self.logger.info(f"   Calculated Trade Value: ${trade_value:.2f}")
            if trade_value > max_trade_value:
                self.logger.warning(f"❌ FAILED - Trade value ${trade_value:.2f} exceeds maximum ${max_trade_value:.2f}")
                return False
            self.logger.info(f"✅ PASSED - Trade value within risk limits")
            
            # Check 4: Stop loss validation
            self.logger.info(f"📊 CHECK 4: Stop Loss Validation")
            if signal.stop_loss:
                self.logger.info(f"   Entry Price: ${signal.price:.4f}")
                self.logger.info(f"   Stop Loss: ${signal.stop_loss:.4f}")
                if signal.stop_loss >= signal.price:
                    self.logger.warning(f"❌ FAILED - Invalid stop loss: ${signal.stop_loss:.4f} >= ${signal.price:.4f}")
                    return False
                stop_loss_distance = signal.price - signal.stop_loss
                stop_loss_percentage = (stop_loss_distance / signal.price) * 100
                self.logger.info(f"   Stop Loss Distance: ${stop_loss_distance:.4f} ({stop_loss_percentage:.2f}%)")
                self.logger.info(f"✅ PASSED - Stop loss is valid")
            else:
                self.logger.info(f"⚠️  No stop loss set - will use default calculation")
            
            # Check 5: Take profit validation
            self.logger.info(f"📊 CHECK 5: Take Profit Validation")
            if signal.take_profit:
                self.logger.info(f"   Entry Price: ${signal.price:.4f}")
                self.logger.info(f"   Take Profit: ${signal.take_profit:.4f}")
                if signal.take_profit <= signal.price:
                    self.logger.warning(f"❌ FAILED - Invalid take profit: ${signal.take_profit:.4f} <= ${signal.price:.4f}")
                    return False
                take_profit_distance = signal.take_profit - signal.price
                take_profit_percentage = (take_profit_distance / signal.price) * 100
                self.logger.info(f"   Take Profit Distance: ${take_profit_distance:.4f} ({take_profit_percentage:.2f}%)")
                self.logger.info(f"✅ PASSED - Take profit is valid")
            else:
                self.logger.info(f"⚠️  No take profit set - will use default calculation")
            
            # Check 6: Risk-Reward Ratio (if both stop loss and take profit are set)
            if signal.stop_loss and signal.take_profit:
                risk_reward_ratio = self.calculate_risk_reward_ratio(signal)
                self.logger.info(f"📊 CHECK 6: Risk-Reward Ratio")
                self.logger.info(f"   Risk-Reward Ratio: {risk_reward_ratio:.2f}:1" if risk_reward_ratio else "   Could not calculate R:R ratio")
                if risk_reward_ratio and risk_reward_ratio < 1.0:
                    self.logger.warning(f"⚠️  WARNING - Poor risk-reward ratio: {risk_reward_ratio:.2f}:1")
                elif risk_reward_ratio:
                    self.logger.info(f"✅ Good risk-reward ratio: {risk_reward_ratio:.2f}:1")
            
            # All checks passed
            self.logger.info(f"🎉 ALL RISK CHECKS PASSED - Trade approved for {signal.symbol}")
            self.logger.info(f"   Final Position Size: {position_size:.6f} {signal.symbol}")
            self.logger.info(f"   Final Trade Value: ${trade_value:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error validating trade: {e}")
            return False
    
    def calculate_position_size(self, signal: TradingSignal, balance: float) -> float:
        """
        Calculate appropriate position size based on risk management rules.
        
        Args:
            signal: Trading signal
            balance: Current balance
            
        Returns:
            Position size in base currency units
        """
        try:
            self.logger.info(f"💰 POSITION SIZE CALCULATION for {signal.symbol}")
            self.logger.info(f"   Sizing Method: {self.config.position_sizing_method}")
            self.logger.info(f"   Account Balance: ${balance:.2f}")
            
            if self.config.position_sizing_method == "fixed":
                # Fixed allocation method (convert USDT to base quantity)
                percentage = float(self.config.fixed_allocation_percentage) / 100.0
                usdt_to_spend = balance * percentage
                # Enforce minimum notional of 10 USDT
                if usdt_to_spend < 10.0:
                    if balance >= 10.0:
                        self.logger.info("   Enforcing minimum notional: bumping spend to $10.00")
                        usdt_to_spend = 10.0
                    else:
                        self.logger.warning("   Balance below $10; cannot meet minimum notional. Skipping trade.")
                        return 0.0
                position_qty = usdt_to_spend / max(signal.price, 1e-12)
                self.logger.info(f"   Method: Fixed percentage ({percentage*100}%)")
                self.logger.info(f"   USDT to spend: ${usdt_to_spend:.6f}")
                self.logger.info(f"   Calculation: ${usdt_to_spend:.6f} ÷ ${signal.price:.6f} = {position_qty:.6f} (qty)")
                return position_qty
            
            elif self.config.position_sizing_method == "percent_risk":
                # Risk-based position sizing
                self.logger.info(f"   Method: Percent risk-based")
                self.logger.info(f"   Risk per trade: {self.config.risk_per_trade_percentage}%")
                
                if not signal.stop_loss:
                    # If no stop loss, use default 2%
                    fallback_size = balance * 0.02
                    self.logger.info(f"   No stop loss provided - using default 2%")
                    self.logger.info(f"   Fallback calculation: ${balance:.2f} × 0.02 = {fallback_size:.6f}")
                    return fallback_size
                
                risk_amount = balance * (self.config.risk_per_trade_percentage / 100)
                price_risk = signal.price - signal.stop_loss
                
                self.logger.info(f"   Entry Price: ${signal.price:.4f}")
                self.logger.info(f"   Stop Loss: ${signal.stop_loss:.4f}")
                self.logger.info(f"   Price Risk: ${price_risk:.4f}")
                self.logger.info(f"   Risk Amount: ${risk_amount:.2f}")
                
                if price_risk <= 0:
                    fallback_size = balance * 0.02
                    self.logger.warning(f"   Invalid price risk (≤0) - using fallback: {fallback_size:.6f}")
                    return fallback_size
                
                calculated_size = risk_amount / price_risk
                final_size = min(calculated_size, self.config.max_position_size)
                
                self.logger.info(f"   Calculated Size: {risk_amount:.2f} ÷ {price_risk:.4f} = {calculated_size:.6f}")
                self.logger.info(f"   Max Position Limit: {self.config.max_position_size:.6f}")
                self.logger.info(f"   Final Size: {final_size:.6f}")
                
                return final_size
            
            else:
                # Default to fixed percentage (2%) in base quantity
                usdt_to_spend = balance * 0.02
                # Enforce minimum notional of 10 USDT
                if usdt_to_spend < 10.0:
                    if balance >= 10.0:
                        self.logger.info("   Enforcing minimum notional: bumping spend to $10.00")
                        usdt_to_spend = 10.0
                    else:
                        self.logger.warning("   Balance below $10; cannot meet minimum notional. Skipping trade.")
                        return 0.0
                qty = usdt_to_spend / max(signal.price, 1e-12)
                self.logger.info(f"   Method: Default (2% fixed)")
                self.logger.info(f"   USDT to spend: ${usdt_to_spend:.6f}")
                self.logger.info(f"   Calculation: ${usdt_to_spend:.6f} ÷ ${signal.price:.6f} = {qty:.6f} (qty)")
                return qty
                
        except Exception as e:
            # Conservative fallback: 1% of balance converted to quantity
            usdt_to_spend = balance * 0.01
            # Enforce minimum notional of 10 USDT
            if usdt_to_spend < 10.0:
                if balance >= 10.0:
                    self.logger.info("   Enforcing minimum notional: bumping spend to $10.00")
                    usdt_to_spend = 10.0
                else:
                    self.logger.warning("   Balance below $10; cannot meet minimum notional. Skipping trade.")
                    return 0.0
            fallback_size = usdt_to_spend / max(signal.price, 1e-12)
            self.logger.error(f"❌ Error calculating position size: {e}")
            self.logger.info(f"   Using conservative fallback: {fallback_size:.6f} (qty)")
            return fallback_size
    
    def calculate_stop_loss(self, signal: TradingSignal) -> float:
        """
        Calculate stop loss price based on risk configuration.
        
        Args:
            signal: Trading signal
            
        Returns:
            Stop loss price
        """
        try:
            if signal.stop_loss:
                return signal.stop_loss
            
            # Default stop loss calculation
            stop_loss_distance = signal.price * (self.config.stop_loss_percentage / 100)
            return signal.price - stop_loss_distance
            
        except Exception as e:
            self.logger.error(f"Error calculating stop loss: {e}")
            return signal.price * 0.95  # 5% stop loss fallback
    
    def calculate_take_profit(self, signal: TradingSignal) -> float:
        """
        Calculate take profit price based on risk configuration.
        
        Args:
            signal: Trading signal
            
        Returns:
            Take profit price
        """
        try:
            if signal.take_profit:
                return signal.take_profit
            
            # Default take profit calculation
            take_profit_distance = signal.price * (self.config.take_profit_percentage / 100)
            return signal.price + take_profit_distance
            
        except Exception as e:
            self.logger.error(f"Error calculating take profit: {e}")
            return signal.price * 1.10  # 10% take profit fallback
    
    def check_daily_loss_limit(self, current_daily_loss: float) -> bool:
        """Check if daily loss limit has been reached."""
        return current_daily_loss < self.config.max_daily_loss
    
    def check_drawdown_limit(self, current_drawdown: float) -> bool:
        """Check if maximum drawdown limit has been reached."""
        return current_drawdown < self.config.max_drawdown
    
    def calculate_risk_reward_ratio(self, signal: TradingSignal) -> Optional[float]:
        """Calculate risk-to-reward ratio for a signal."""
        try:
            if not signal.stop_loss or not signal.take_profit:
                return None
            
            risk = signal.price - signal.stop_loss
            reward = signal.take_profit - signal.price
            
            if risk <= 0:
                return None
            
            return reward / risk
            
        except Exception as e:
            self.logger.error(f"Error calculating risk-reward ratio: {e}")
            return None
