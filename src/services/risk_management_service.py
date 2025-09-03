"""
Risk Management Service - Single Responsibility: Manage trading risks.
"""

import logging
from typing import Optional

from ..core.interfaces import IRiskManager
from ..models import TradingSignal, RiskConfig


class RiskManagementService(IRiskManager):
    """
    Service responsible for risk management calculations and validations.
    Implements various position sizing and risk control methods.
    """
    
    def __init__(self, risk_config: RiskConfig):
        """Initialize with risk configuration."""
        self.config = risk_config
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
            # Check minimum balance
            if current_balance < 100.0:  # Minimum required balance
                self.logger.warning(f"Insufficient balance: {current_balance}")
                return False
            
            # Calculate position size
            position_size = self.calculate_position_size(signal, current_balance)
            
            # Check if position size exceeds maximum
            if position_size > self.config.max_position_size:
                self.logger.warning(f"Position size {position_size} exceeds maximum {self.config.max_position_size}")
                return False
            
            # Check if trade amount is within limits
            trade_value = position_size * signal.price
            max_trade_value = current_balance * (self.config.risk_per_trade_percentage / 100)
            
            if trade_value > max_trade_value:
                self.logger.warning(f"Trade value {trade_value} exceeds maximum {max_trade_value}")
                return False
            
            # Validate stop loss and take profit
            if signal.stop_loss and signal.stop_loss >= signal.price:
                self.logger.warning(f"Invalid stop loss: {signal.stop_loss} >= {signal.price}")
                return False
            
            if signal.take_profit and signal.take_profit <= signal.price:
                self.logger.warning(f"Invalid take profit: {signal.take_profit} <= {signal.price}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
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
            if self.config.position_sizing_method == "fixed":
                # Fixed dollar amount
                return balance * 0.02  # 2% of balance
            
            elif self.config.position_sizing_method == "percent_risk":
                # Risk-based position sizing
                if not signal.stop_loss:
                    # If no stop loss, use default 2%
                    return balance * 0.02
                
                risk_amount = balance * (self.config.risk_per_trade_percentage / 100)
                price_risk = signal.price - signal.stop_loss
                
                if price_risk <= 0:
                    return balance * 0.02  # Fallback
                
                position_size = risk_amount / price_risk
                return min(position_size, self.config.max_position_size)
            
            else:
                # Default to fixed percentage
                return balance * 0.02
                
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return balance * 0.01  # Conservative fallback
    
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
