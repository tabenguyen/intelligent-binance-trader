"""
Notification Service - Single Responsibility: Handle notifications.
"""

import logging
import requests
from datetime import datetime
from typing import Optional, List, Dict, Union, Any

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
                # Get more detailed error information
                error_detail = ""
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_json = e.response.json()
                        error_detail = f" - {error_json.get('description', 'Unknown error')}"
                    except:
                        error_detail = f" - Response: {e.response.text[:200]}"
                
                self.logger.error(f"Failed to send Telegram message: {e}{error_detail}")
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
            
            # Calculate trade value (quantity × entry price)
            trade_value = trade.quantity * trade.entry_price
            
            # Calculate percentage changes for stop loss and take profit
            entry_price = trade.entry_price
            exit_price = trade.exit_price or 0
            
            # Calculate percentage change from entry to exit
            price_change_pct = ((exit_price - entry_price) / entry_price) * 100 if exit_price > 0 else 0
            
            # Format timestamps
            entry_time_str = trade.entry_time.strftime("%Y-%m-%d %H:%M:%S UTC") if trade.entry_time else "N/A"
            exit_time_str = trade.exit_time.strftime("%Y-%m-%d %H:%M:%S UTC") if trade.exit_time else "N/A"
            
            # Format message with HTML markup for Telegram
            message = (
                f"{status_emoji} <b>Trade Completed: {trade.symbol}</b>\n"
                f"🔢 Quantity: <code>{trade.quantity:.6f}</code>\n"
                f"💰 Trade Value: <code>${trade_value:.2f}</code>\n"
                f"📈 Entry: <code>${trade.entry_price:.4f}</code>\n"
                f"📉 Exit: <code>${exit_price:.4f}</code> <code>({price_change_pct:+.2f}%)</code>\n"
            )
            
            # Add stop loss and take profit information if available
            if trade.stop_loss:
                sl_pct = trade.stop_loss_percentage or 0
                message += f"🛑 Stop Loss: <code>${trade.stop_loss:.4f}</code> <code>({sl_pct:+.2f}%)</code>\n"
            
            if trade.take_profit:
                tp_pct = trade.take_profit_percentage or 0
                message += f"🎯 Take Profit: <code>${trade.take_profit:.4f}</code> <code>({tp_pct:+.2f}%)</code>\n"
            
            # Add P&L and timing information
            message += (
                f"{pnl_emoji} <b>P&L: ${trade.pnl:.2f}</b>\n"
                f"⏱ Duration: <code>{self._calculate_duration(trade)}</code>\n"
                f"📅 Entry Time: <code>{entry_time_str}</code>\n"
                f"🏁 Exit Time: <code>{exit_time_str}</code>"
            )
            
            # Add strategy information if available
            if trade.strategy_name:
                message += f"\n🎯 Strategy: <code>{trade.strategy_name}</code>"
            
            success = self._send_message(message)
            
            # Fallback to logging if Telegram fails
            if not success:
                self.fallback.send_trade_notification(trade)
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram trade notification: {e}")
            self.fallback.send_trade_notification(trade)
    
    def send_signal_notification(self, signal: TradingSignal, trade_value: Optional[float] = None, position_size: Optional[float] = None) -> None:
        """Send notification for a trading signal."""
        try:
            direction_emoji = "🟢" if signal.direction.value == "BUY" else "🔴"
            
            # Format message with HTML markup for Telegram - Enhanced format
            message = (
                f"{direction_emoji} <b>Trading Signal: {signal.symbol}</b>\n"
                f"🎯 Strategy: <code>{signal.strategy_name}</code>\n"
                f"📊 Direction: <code>{signal.direction.value}</code>\n"
                f"💰 Price: <code>${signal.price:.4f}</code>\n"
                f"🎲 Confidence: <code>{signal.confidence:.1%}</code>\n"
            )
            
            # Add trade value if available
            if trade_value is not None:
                message += f"💵 Trade Value: <code>${trade_value:.2f}</code>\n"
            elif position_size is not None:
                # Calculate trade value from position size and price
                calculated_trade_value = position_size * signal.price
                message += f"💵 Trade Value: <code>${calculated_trade_value:.2f}</code>\n"
            
            # Add stop loss and take profit with rates/percentages
            if signal.stop_loss:
                sl_rate = ((signal.price - signal.stop_loss) / signal.price) * 100
                message += f"🛑 Stop Loss: <code>${signal.stop_loss:.4f}</code> <code>({sl_rate:.2f}%)</code>\n"
            if signal.take_profit:
                tp_rate = ((signal.take_profit - signal.price) / signal.price) * 100
                message += f"🎯 Take Profit: <code>${signal.take_profit:.4f}</code> <code>({tp_rate:.2f}%)</code>\n"
                
            # Add core conditions if available
            if hasattr(signal, 'core_conditions_count'):
                message += f"✅ Core Conditions: <code>{signal.core_conditions_count}/4</code>"
            
            success = self._send_message(message)
            
            # Fallback to logging if Telegram fails
            if not success:
                self.fallback.send_signal_notification(signal, trade_value, position_size)
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram signal notification: {e}")
            self.fallback.send_signal_notification(signal, trade_value, position_size)
    
    def send_error_notification(self, error: Union[str, dict, Exception, Any]) -> None:
        """Send error notification."""
        try:
            # Ensure error is a string - handle cases where dict or other types might be passed
            if isinstance(error, dict):
                error_str = str(error)
            elif isinstance(error, Exception):
                error_str = str(error)
            else:
                error_str = str(error) if error is not None else "Unknown error"
                
            message = f"🚨 <b>Trading Bot Error</b>\n<code>{error_str}</code>"
            success = self._send_message(message)
            
            # Always also log errors
            if not success:
                self.fallback.send_error_notification(error_str)
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram error notification: {e}")
            # Ensure we pass a string to the fallback
            error_str = str(error) if error is not None else "Unknown error"
            self.fallback.send_error_notification(error_str)
    
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
    
    def send_signal_notification(self, signal: TradingSignal, trade_value: Optional[float] = None, position_size: Optional[float] = None) -> None:
        """Send signal notification to all services."""
        for service in self.services:
            try:
                service.send_signal_notification(signal, trade_value, position_size)
            except Exception as e:
                self.logger.error(f"Error in notification service {service.__class__.__name__}: {e}")
    
    def send_error_notification(self, error: str) -> None:
        """Send error notification to all services."""
        # Ensure error is a string - handle cases where dict or other types might be passed
        if isinstance(error, dict):
            error_str = str(error)
        elif isinstance(error, Exception):
            error_str = str(error)
        else:
            error_str = str(error) if error is not None else "Unknown error"
            
        for service in self.services:
            try:
                service.send_error_notification(error_str)
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
            
            # Calculate trade value and percentage changes
            trade_value = trade.quantity * trade.entry_price
            exit_price = trade.exit_price or 0
            price_change_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100 if exit_price > 0 else 0
            
            # Format timestamps
            entry_time_str = trade.entry_time.strftime("%Y-%m-%d %H:%M:%S UTC") if trade.entry_time else "N/A"
            exit_time_str = trade.exit_time.strftime("%Y-%m-%d %H:%M:%S UTC") if trade.exit_time else "N/A"
            
            message = (
                f"{status_emoji} Trade Completed: {trade.symbol}\n"
                f"Quantity: {trade.quantity:.6f}\n"
                f"Trade Value: ${trade_value:.2f}\n"
                f"Entry: ${trade.entry_price:.4f}\n"
                f"Exit: ${exit_price:.4f} ({price_change_pct:+.2f}%)\n"
            )
            
            # Add stop loss and take profit information if available
            if trade.stop_loss:
                sl_pct = trade.stop_loss_percentage or 0
                message += f"Stop Loss: ${trade.stop_loss:.4f} ({sl_pct:+.2f}%)\n"
            
            if trade.take_profit:
                tp_pct = trade.take_profit_percentage or 0
                message += f"Take Profit: ${trade.take_profit:.4f} ({tp_pct:+.2f}%)\n"
            
            # Add P&L and timing information
            message += (
                f"{pnl_emoji} P&L: ${trade.pnl:.2f}\n"
                f"Duration: {self._calculate_duration(trade)}\n"
                f"Entry Time: {entry_time_str}\n"
                f"Exit Time: {exit_time_str}"
            )
            
            # Add strategy information if available
            if trade.strategy_name:
                message += f"\nStrategy: {trade.strategy_name}"
            
            if trade.is_profitable:
                self.logger.info(f"🎉 PROFITABLE TRADE: {message}")
            else:
                self.logger.warning(f"💸 LOSING TRADE: {message}")
                
        except Exception as e:
            self.logger.error(f"Error sending trade notification: {e}")
    
    def send_signal_notification(self, signal: TradingSignal, trade_value: Optional[float] = None, position_size: Optional[float] = None) -> None:
        """Send notification for a trading signal."""
        try:
            direction_emoji = "🟢" if signal.direction.value == "BUY" else "🔴"
            
            message = (
                f"{direction_emoji} Trading Signal: {signal.symbol}\n"
                f"Strategy: {signal.strategy_name}\n"
                f"Direction: {signal.direction.value}\n"
                f"Price: ${signal.price:.4f}\n"
                f"Confidence: {signal.confidence:.1%}\n"
            )
            
            # Add trade value if available
            if trade_value is not None:
                message += f"Trade Value: ${trade_value:.2f}\n"
            elif position_size is not None:
                # Calculate trade value from position size and price
                calculated_trade_value = position_size * signal.price
                message += f"Trade Value: ${calculated_trade_value:.2f}\n"
            
            # Add stop loss and take profit with rates/percentages
            if signal.stop_loss:
                sl_rate = ((signal.price - signal.stop_loss) / signal.price) * 100
                message += f"Stop Loss: ${signal.stop_loss:.4f} ({sl_rate:.2f}%)\n"
            if signal.take_profit:
                tp_rate = ((signal.take_profit - signal.price) / signal.price) * 100
                message += f"Take Profit: ${signal.take_profit:.4f} ({tp_rate:.2f}%)"
            
            self.logger.info(f"📡 SIGNAL GENERATED: {message}")
            
        except Exception as e:
            self.logger.error(f"Error sending signal notification: {e}")
    
    def send_error_notification(self, error: str) -> None:
        """Send error notification."""
        try:
            # Ensure error is a string - handle cases where dict or other types might be passed
            if isinstance(error, dict):
                error_str = str(error)
            elif isinstance(error, Exception):
                error_str = str(error)
            else:
                error_str = str(error) if error is not None else "Unknown error"
                
            self.logger.error(f"🚨 TRADING ERROR: {error_str}")
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


class TwitterNotificationService(INotificationService):
    """
    Twitter-based notification service.
    Posts trading signals as tweets and replies with trade completion.
    """
    
    def __init__(self, bearer_token: str, api_key: str, api_secret: str, 
                 access_token: str, access_token_secret: str, 
                 fallback_service: Optional[INotificationService] = None):
        """
        Initialize Twitter notification service.
        
        Args:
            bearer_token: Twitter API Bearer Token
            api_key: Twitter API Key
            api_secret: Twitter API Secret
            access_token: Twitter Access Token
            access_token_secret: Twitter Access Token Secret
            fallback_service: Optional fallback notification service if Twitter fails
        """
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.logger = logging.getLogger(__name__)
        self.fallback = fallback_service or LoggingNotificationService()
        
        # Store signal tweet IDs for later replies
        self.signal_tweets: Dict[str, str] = {}  # symbol -> tweet_id mapping
        
        # Test connection on initialization
        if all([bearer_token, api_key, api_secret, access_token, access_token_secret]):
            self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test Twitter API connection."""
        try:
            # Simple test to verify credentials work
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get('https://api.twitter.com/2/users/me', headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('data', {}).get('username', 'Unknown')
                self.logger.info(f"✅ Twitter API connected as @{username}")
                return True
            else:
                self.logger.warning(f"Twitter API test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Twitter connection test failed: {e}")
            return False
    
    def _post_tweet(self, message: str, reply_to_tweet_id: Optional[str] = None) -> Optional[str]:
        """
        Post a tweet to Twitter.
        
        Args:
            message: Tweet content
            reply_to_tweet_id: Optional tweet ID to reply to
            
        Returns:
            Tweet ID if successful, None otherwise
        """
        try:
            # Twitter API v2 endpoint for posting tweets
            url = 'https://api.twitter.com/2/tweets'
            
            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'text': message
            }
            
            # Add reply information if replying to another tweet
            if reply_to_tweet_id:
                payload['reply'] = {
                    'in_reply_to_tweet_id': reply_to_tweet_id
                }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 201:
                tweet_data = response.json()
                tweet_id = tweet_data.get('data', {}).get('id')
                
                if reply_to_tweet_id:
                    self.logger.info(f"✅ Twitter reply posted successfully (ID: {tweet_id})")
                else:
                    self.logger.info(f"✅ Twitter signal posted successfully (ID: {tweet_id})")
                
                return tweet_id
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                self.logger.error(f"Failed to post tweet: {response.status_code} - {error_data}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error posting tweet: {e}")
            return None
    
    def send_signal_notification(self, signal: TradingSignal, trade_value: Optional[float] = None, position_size: Optional[float] = None) -> None:
        """Send notification for a trading signal as a Twitter post."""
        try:
            direction_emoji = "🟢" if signal.direction.value == "BUY" else "🔴"
            
            # Format message for Twitter (280 character limit)
            message = (
                f"{direction_emoji} TRADING SIGNAL: #{signal.symbol}\n"
                f"📊 {signal.direction.value} @ ${signal.price:.4f}\n"
                f"🎯 Strategy: {signal.strategy_name}\n"
                f"🎲 Confidence: {signal.confidence:.1%}\n"
            )
            
            # Add trade value if available (keep concise for Twitter)
            if trade_value is not None:
                message += f"💵 Value: ${trade_value:.0f}\n"
            elif position_size is not None:
                # Calculate trade value from position size and price
                calculated_trade_value = position_size * signal.price
                message += f"💵 Value: ${calculated_trade_value:.0f}\n"
            
            # Add stop loss and take profit with rates if available
            if signal.stop_loss:
                sl_rate = ((signal.price - signal.stop_loss) / signal.price) * 100
                message += f"🛑 SL: ${signal.stop_loss:.4f} ({sl_rate:.1f}%)\n"
            if signal.take_profit:
                tp_rate = ((signal.take_profit - signal.price) / signal.price) * 100
                message += f"🎯 TP: ${signal.take_profit:.4f} ({tp_rate:.1f}%)\n"
            
            # Add hashtags
            message += f"\n#TradingBot #Crypto #{signal.symbol.replace('USDT', '')} #TechnicalAnalysis"
            
            # Post the signal tweet
            tweet_id = self._post_tweet(message)
            
            if tweet_id:
                # Store the tweet ID for later reply when trade completes
                # Ensure symbol is a string (defensive programming)
                symbol_key = str(signal.symbol) if signal.symbol else "UNKNOWN"
                self.signal_tweets[symbol_key] = tweet_id
                self.logger.info(f"📡 Signal tweet posted for {symbol_key}: {tweet_id}")
            else:
                # Fallback to logging if Twitter fails
                self.fallback.send_signal_notification(signal, trade_value, position_size)
                
        except Exception as e:
            self.logger.error(f"Error sending Twitter signal notification: {e}")
            self.fallback.send_signal_notification(signal, trade_value, position_size)
    
    def send_trade_notification(self, trade: Trade) -> None:
        """Send notification for a completed trade as a Twitter reply."""
        try:
            pnl_emoji = "📈" if trade.is_profitable else "📉"
            status_emoji = "✅" if trade.is_profitable else "❌"
            
            # Calculate trade value and percentage change
            trade_value = trade.quantity * trade.entry_price
            exit_price = trade.exit_price or 0
            price_change_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100 if exit_price > 0 else 0
            
            # Format message for Twitter reply
            message = (
                f"{status_emoji} TRADE COMPLETED: #{trade.symbol}\n"
                f"💰 Value: ${trade_value:.0f}\n"
                f"📈 Entry: ${trade.entry_price:.4f}\n"
                f"📉 Exit: ${exit_price:.4f} ({price_change_pct:+.1f}%)\n"
                f"{pnl_emoji} P&L: ${trade.pnl:.2f}\n"
                f"⏱ Duration: {self._calculate_duration(trade)}"
            )
            
            # Try to reply to the original signal tweet
            symbol_key = str(trade.symbol) if trade.symbol else "UNKNOWN"
            original_tweet_id = self.signal_tweets.get(symbol_key)
            
            if original_tweet_id:
                reply_tweet_id = self._post_tweet(message, reply_to_tweet_id=original_tweet_id)
                if reply_tweet_id:
                    self.logger.info(f"📱 Trade completion reply posted for {symbol_key}")
                    # Clean up the stored tweet ID
                    if symbol_key in self.signal_tweets:
                        del self.signal_tweets[symbol_key]
                else:
                    # Fallback to logging if reply fails
                    self.fallback.send_trade_notification(trade)
            else:
                # No original signal tweet found, just post as regular tweet
                tweet_id = self._post_tweet(message)
                if not tweet_id:
                    self.fallback.send_trade_notification(trade)
                
        except Exception as e:
            self.logger.error(f"Error sending Twitter trade notification: {e}")
            self.fallback.send_trade_notification(trade)
    
    def send_error_notification(self, error: str) -> None:
        """Send error notification."""
        try:
            # Ensure error is a string - handle cases where dict or other types might be passed
            if isinstance(error, dict):
                error_str = str(error)
            elif isinstance(error, Exception):
                error_str = str(error)
            else:
                error_str = str(error) if error is not None else "Unknown error"
                
            message = f"🚨 TRADING BOT ERROR\n{error_str[:200]}..."  # Truncate for Twitter
            tweet_id = self._post_tweet(message)
            
            # Always also log errors
            if not tweet_id:
                self.fallback.send_error_notification(error_str)
                
        except Exception as e:
            self.logger.error(f"Error sending Twitter error notification: {e}")
            # Ensure we pass a string to the fallback
            error_str = str(error) if error is not None else "Unknown error"
            self.fallback.send_error_notification(error_str)
    
    def send_system_notification(self, message: str, level: str = "INFO") -> None:
        """Send system notification."""
        try:
            # Only post important system notifications to Twitter
            if level in ["ERROR", "WARNING"]:
                emoji = "🚨" if level == "ERROR" else "⚠️"
                tweet_message = f"{emoji} SYSTEM: {message[:200]}..."  # Truncate for Twitter
                
                tweet_id = self._post_tweet(tweet_message)
                
                # Fallback to logging if Twitter fails
                if not tweet_id and hasattr(self.fallback, 'send_system_notification'):
                    self.fallback.send_system_notification(message, level)
            else:
                # For INFO and DEBUG, just use fallback
                if hasattr(self.fallback, 'send_system_notification'):
                    self.fallback.send_system_notification(message, level)
                
        except Exception as e:
            self.logger.error(f"Error sending Twitter system notification: {e}")
            if hasattr(self.fallback, 'send_system_notification'):
                self.fallback.send_system_notification(message, level)
    
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
    
    def send_signal_notification(self, signal: TradingSignal, trade_value: Optional[float] = None, position_size: Optional[float] = None) -> None:
        """Send signal notification via email."""
        # TODO: Implement email sending
        self.logger.info("Email notification not implemented, falling back to logging")
        self.fallback.send_signal_notification(signal, trade_value, position_size)
    
    def send_error_notification(self, error: str) -> None:
        """Send error notification via email."""
        # TODO: Implement email sending
        self.logger.info("Email notification not implemented, falling back to logging")
        self.fallback.send_error_notification(error)
