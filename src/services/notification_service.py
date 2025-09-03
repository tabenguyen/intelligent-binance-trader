"""
Notification Service - Single Responsibility: Handle notifications.
"""

import logging
from datetime import datetime

from ..core.interfaces import INotificationService
from ..models import Trade, TradingSignal


class LoggingNotificationService(INotificationService):
    """
    Simple notification service that logs messages.
    Can be extended to support email, SMS, webhook notifications, etc.
    """
    
    def __init__(self):
        """Initialize the notification service."""
        self.logger = logging.getLogger(__name__)
    
    def send_trade_notification(self, trade: Trade) -> None:
        """Send notification for a completed trade."""
        try:
            pnl_emoji = "📈" if trade.is_profitable else "📉"
            status_emoji = self._get_status_emoji(trade.status)
            
            message = (
                f"{status_emoji} Trade Completed: {trade.symbol}\n"
                f"Direction: {trade.direction.value}\n"
                f"Quantity: {trade.quantity:.6f}\n"
                f"Entry: ${trade.entry_price:.2f}\n"
                f"Exit: ${trade.exit_price:.2f}\n"
                f"{pnl_emoji} P&L: ${trade.pnl:.2f}\n"
                f"Duration: {self._calculate_duration(trade)}"
            )
            
            if trade.is_profitable:
                self.logger.info(f"🎉 PROFITABLE TRADE: {message}")
            else:
                self.logger.warning(f"💸 LOSING TRADE: {message}")
                
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {e}")
    
    def send_signal_notification(self, signal: TradingSignal) -> None:
        """Send notification for a trading signal."""
        try:
            direction_emoji = "🟢" if signal.direction.value == "BUY" else "🔴"
            
            message = (
                f"{direction_emoji} Trading Signal: {signal.symbol}\n"
                f"Strategy: {signal.strategy_name}\n"
                f"Direction: {signal.direction.value}\n"
                f"Price: ${signal.price:.2f}\n"
                f"Confidence: {signal.confidence:.1%}\n"
                f"Stop Loss: ${signal.stop_loss:.2f}" if signal.stop_loss else "Stop Loss: N/A" + "\n"
                f"Take Profit: ${signal.take_profit:.2f}" if signal.take_profit else "Take Profit: N/A"
            )
            
            self.logger.info(f"📡 SIGNAL GENERATED: {message}")
            
        except Exception as e:
            self.logger.error(f"Error sending signal notification: {e}")
    
    def send_error_notification(self, error: str) -> None:
        """Send error notification."""
        try:
            self.logger.error(f"🚨 TRADING ERROR: {error}")
        except Exception as e:
            self.logger.critical(f"Failed to send error notification: {e}")
    
    def send_system_notification(self, message: str, level: str = "INFO") -> None:
        """Send system notification."""
        try:
            emoji = self._get_level_emoji(level)
            formatted_message = f"{emoji} SYSTEM: {message}"
            
            if level == "ERROR":
                self.logger.error(formatted_message)
            elif level == "WARNING":
                self.logger.warning(formatted_message)
            else:
                self.logger.info(formatted_message)
                
        except Exception as e:
            self.logger.error(f"Error sending system notification: {e}")
    
    def _get_status_emoji(self, status) -> str:
        """Get emoji for trade status."""
        status_emojis = {
            "FILLED": "✅",
            "STOP_LOSS": "🛑", 
            "TAKE_PROFIT": "🎯",
            "CANCELLED": "❌",
            "PENDING": "⏳"
        }
        return status_emojis.get(status.value if hasattr(status, 'value') else str(status), "📋")
    
    def _get_level_emoji(self, level: str) -> str:
        """Get emoji for log level."""
        level_emojis = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "🚨",
            "DEBUG": "🔍"
        }
        return level_emojis.get(level.upper(), "📋")
    
    def _calculate_duration(self, trade: Trade) -> str:
        """Calculate trade duration."""
        try:
            if not trade.exit_time:
                return "N/A"
            
            duration = trade.exit_time - trade.entry_time
            hours = duration.total_seconds() / 3600
            
            if hours < 1:
                minutes = duration.total_seconds() / 60
                return f"{minutes:.0f}m"
            elif hours < 24:
                return f"{hours:.1f}h"
            else:
                days = hours / 24
                return f"{days:.1f}d"
                
        except Exception:
            return "N/A"


class EmailNotificationService(INotificationService):
    """
    Email-based notification service.
    Placeholder for future implementation.
    """
    
    def __init__(self, smtp_config: dict):
        """Initialize email notification service."""
        self.smtp_config = smtp_config
        self.logger = logging.getLogger(__name__)
        self.fallback = LoggingNotificationService()
    
    def send_trade_notification(self, trade: Trade) -> None:
        """Send trade notification via email."""
        # TODO: Implement email sending
        self.logger.info("Email notification not implemented, falling back to logging")
        self.fallback.send_trade_notification(trade)
    
    def send_signal_notification(self, signal: TradingSignal) -> None:
        """Send signal notification via email."""
        # TODO: Implement email sending
        self.logger.info("Email notification not implemented, falling back to logging")
        self.fallback.send_signal_notification(signal)
    
    def send_error_notification(self, error: str) -> None:
        """Send error notification via email."""
        # TODO: Implement email sending
        self.logger.info("Email notification not implemented, falling back to logging")
        self.fallback.send_error_notification(error)
