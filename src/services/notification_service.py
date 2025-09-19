"""
Notification Service - Single Responsibility: Handle notifications.
"""

import logging
import requests
from datetime import datetime
from typing import Optional, List

from ..core.interfaces import INotificationService
from ..models import Trade, TradingSignal


class TelegramNotificationService(INotificationService):
    """
    Telegram-based notification service.
    Sends notifications to Telegram bot/channel.
    """
    
    def __init__(self, bot_token: str, chat_id: str, fallback_service: Optional[INotificationService] = None):
        """
        Initialize Telegram notification service.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Chat ID to send messages to
            fallback_service: Optional fallback notification service if Telegram fails
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)
        self.fallback = fallback_service or LoggingNotificationService()
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Test connection on initialization
        if bot_token and chat_id:
            self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test Telegram connection."""
        try:
            test_message = "🤖 Trading Bot Telegram Service Initialized"
            return self._send_message(test_message, silent=True)
        except Exception as e:
            self.logger.warning(f"Telegram connection test failed: {e}")
            return False
    
    def _send_message(self, message: str, silent: bool = False) -> bool:
        """
        Send message to Telegram.
        
        Args:
            message: Message to send
            silent: If True, don't log failures
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            if not silent:
                self.logger.debug(f"Telegram message sent successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            if not silent:
                self.logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            if not silent:
                self.logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_trade_notification(self, trade: Trade) -> None:
        """Send notification for a completed trade."""
        try:
            pnl_emoji = "📈" if trade.is_profitable else "📉"
            status_emoji = self._get_status_emoji(trade.status)
            
            # Format message with HTML markup for Telegram
            message = (
                f"{status_emoji} <b>Trade Completed: {trade.symbol}</b>\n"
                f"📊 Direction: <code>{trade.direction.value}</code>\n"
                f"🔢 Quantity: <code>{trade.quantity:.6f}</code>\n"
                f"📈 Entry: <code>${trade.entry_price:.4f}</code>\n"
                f"📉 Exit: <code>${trade.exit_price:.4f}</code>\n"
                f"{pnl_emoji} <b>P&L: ${trade.pnl:.2f}</b>\n"
                f"⏱ Duration: <code>{self._calculate_duration(trade)}</code>"
            )
            
            success = self._send_message(message)
            
            # Fallback to logging if Telegram fails
            if not success:
                self.fallback.send_trade_notification(trade)
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram trade notification: {e}")
            self.fallback.send_trade_notification(trade)
    
    def send_signal_notification(self, signal: TradingSignal) -> None:
        """Send notification for a trading signal."""
        try:
            direction_emoji = "🟢" if signal.direction.value == "BUY" else "🔴"
            
            # Format message with HTML markup for Telegram
            message = (
                f"{direction_emoji} <b>Trading Signal: {signal.symbol}</b>\n"
                f"🎯 Strategy: <code>{signal.strategy_name}</code>\n"
                f"📊 Direction: <code>{signal.direction.value}</code>\n"
                f"💰 Price: <code>${signal.price:.4f}</code>\n"
                f"🎲 Confidence: <code>{signal.confidence:.1%}</code>\n"
            )
            
            # Add stop loss and take profit if available
            if signal.stop_loss:
                message += f"🛑 Stop Loss: <code>${signal.stop_loss:.4f}</code>\n"
            if signal.take_profit:
                message += f"🎯 Take Profit: <code>${signal.take_profit:.4f}</code>\n"
                
            # Add core conditions if available
            if hasattr(signal, 'core_conditions_count'):
                message += f"✅ Core Conditions: <code>{signal.core_conditions_count}/4</code>"
            
            success = self._send_message(message)
            
            # Fallback to logging if Telegram fails
            if not success:
                self.fallback.send_signal_notification(signal)
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram signal notification: {e}")
            self.fallback.send_signal_notification(signal)
    
    def send_error_notification(self, error: str) -> None:
        """Send error notification."""
        try:
            message = f"🚨 <b>Trading Bot Error</b>\n<code>{error}</code>"
            success = self._send_message(message)
            
            # Always also log errors
            if not success:
                self.fallback.send_error_notification(error)
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram error notification: {e}")
            self.fallback.send_error_notification(error)
    
    def send_system_notification(self, message: str, level: str = "INFO") -> None:
        """Send system notification."""
        try:
            emoji = self._get_level_emoji(level)
            formatted_message = f"{emoji} <b>System</b>: {message}"
            
            success = self._send_message(formatted_message)
            
            # Fallback to logging if Telegram fails
            if not success and hasattr(self.fallback, 'send_system_notification'):
                self.fallback.send_system_notification(message, level)
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram system notification: {e}")
            if hasattr(self.fallback, 'send_system_notification'):
                self.fallback.send_system_notification(message, level)
    
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


class CompositeNotificationService(INotificationService):
    """
    Composite notification service that sends notifications to multiple services.
    Allows parallel use of logging and Telegram notifications.
    """
    
    def __init__(self, services: List[INotificationService]):
        """
        Initialize composite notification service.
        
        Args:
            services: List of notification services to use
        """
        self.services = services
        self.logger = logging.getLogger(__name__)
    
    def send_trade_notification(self, trade: Trade) -> None:
        """Send trade notification to all services."""
        for service in self.services:
            try:
                service.send_trade_notification(trade)
            except Exception as e:
                self.logger.error(f"Error in notification service {service.__class__.__name__}: {e}")
    
    def send_signal_notification(self, signal: TradingSignal) -> None:
        """Send signal notification to all services."""
        for service in self.services:
            try:
                service.send_signal_notification(signal)
            except Exception as e:
                self.logger.error(f"Error in notification service {service.__class__.__name__}: {e}")
    
    def send_error_notification(self, error: str) -> None:
        """Send error notification to all services."""
        for service in self.services:
            try:
                service.send_error_notification(error)
            except Exception as e:
                self.logger.error(f"Error in notification service {service.__class__.__name__}: {e}")
    
    def send_system_notification(self, message: str, level: str = "INFO") -> None:
        """Send system notification to all services that support it."""
        for service in self.services:
            try:
                if hasattr(service, 'send_system_notification'):
                    service.send_system_notification(message, level)
            except Exception as e:
                self.logger.error(f"Error in notification service {service.__class__.__name__}: {e}")


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
