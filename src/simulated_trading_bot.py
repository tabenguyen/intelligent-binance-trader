"""
Simulated Trading Bot - Demo version with virtual balance and Twitter notifications.

This bot operates as a simulation without using real account balances.
All trades are virtual and notifications are sent to Twitter instead of Telegram.
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from .core.interfaces import INotificationService
from .models import Trade, TradingSignal, TradeDirection, TradeStatus, Position
from .services.notification_service import TwitterNotificationService, LoggingNotificationService
from .services.market_data_service import BinanceMarketDataService
from .services.technical_analysis_service import TechnicalAnalysisService
from .strategies.ema_cross_strategy import EMACrossStrategy
from .utils.logging_config import setup_logging


@dataclass
@dataclass
class SimulatedPosition:
    """Represents a simulated trading position."""
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    signal_tweet_id: Optional[str] = None  # Store original signal tweet ID


class SimulatedTradingBot:
    """
    Simulated trading bot that:
    - Uses virtual balance instead of real account
    - Posts trading signals to Twitter
    - Replies to signal tweets when trades complete
    - Never executes real trades
    """
    
    def __init__(self, config):
        """Initialize the simulated trading bot."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Simulated balance and positions
        self.balance = config.simulation_balance
        self.initial_balance = config.simulation_balance
        self.positions: Dict[str, SimulatedPosition] = {}
        self.completed_trades: List[Trade] = []
        
        # Initialize services
        self.market_data_service = BinanceMarketDataService(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        self.technical_analysis_service = TechnicalAnalysisService()
        
        # Initialize Twitter notification service
        self.notification_service = self._initialize_notification_service()
        
        # Initialize strategies
        self.strategy = EMACrossStrategy()
        
        self.logger.info(f"🎯 Simulated Trading Bot initialized with ${self.balance:.2f} balance")
    
    def _initialize_notification_service(self) -> INotificationService:
        """Initialize the notification service with Twitter integration."""
        try:
            # Create Twitter service if credentials are available
            if all([
                hasattr(self.config, 'twitter_bearer_token') and self.config.twitter_bearer_token,
                hasattr(self.config, 'twitter_api_key') and self.config.twitter_api_key,
                hasattr(self.config, 'twitter_api_secret') and self.config.twitter_api_secret,
                hasattr(self.config, 'twitter_access_token') and self.config.twitter_access_token,
                hasattr(self.config, 'twitter_access_token_secret') and self.config.twitter_access_token_secret
            ]):
                self.logger.info("✅ Initializing Twitter notification service")
                return TwitterNotificationService(
                    bearer_token=self.config.twitter_bearer_token,
                    api_key=self.config.twitter_api_key,
                    api_secret=self.config.twitter_api_secret,
                    access_token=self.config.twitter_access_token,
                    access_token_secret=self.config.twitter_access_token_secret,
                    fallback_service=LoggingNotificationService()
                )
            else:
                self.logger.warning("⚠️ Twitter credentials not configured, using logging only")
                return LoggingNotificationService()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter service: {e}")
            return LoggingNotificationService()
    
    def scan_for_signals(self) -> List[TradingSignal]:
        """Scan watchlist for trading signals."""
        signals = []
        
        try:
            for symbol in self.config.symbols:
                # Skip if we already have a position
                if symbol in self.positions:
                    continue
                
                try:
                    # Get market data
                    market_data = self.market_data_provider.get_market_data(
                        symbol, 
                        self.config.timeframe
                    )
                    
                    if not market_data:
                        continue
                    
                    # Get technical analysis
                    technical_analysis = self.technical_analysis.analyze(market_data)
                    market_data.technical_analysis = technical_analysis
                    
                    # Check each strategy for signals
                    for strategy in self.strategies:
                        try:
                            signal = strategy.generate_signal(market_data)
                            if signal:
                                signals.append(signal)
                                self.logger.info(f"📡 Signal generated: {signal.symbol} {signal.direction.value} @ ${signal.price:.4f}")
                                
                        except Exception as e:
                            self.logger.error(f"Error in strategy {strategy.__class__.__name__} for {symbol}: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error processing {symbol}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in signal scanning: {e}")
        
        return signals
    
    def simulate_trade_execution(self, signal: TradingSignal) -> bool:
        """Simulate trade execution with virtual balance."""
        try:
            # Check if we have enough balance
            trade_amount = min(self.config.trade_amount, self.balance * 0.95)  # Use 95% of balance max
            
            if trade_amount < self.config.min_notional:
                self.logger.warning(f"Insufficient balance for {signal.symbol}: ${self.balance:.2f}")
                return False
            
            # Calculate position size
            quantity = trade_amount / signal.price
            
            # Calculate stop loss and take profit
            if signal.direction == TradeDirection.BUY:
                stop_loss = signal.stop_loss or signal.price * 0.95  # 5% stop loss
                take_profit = signal.take_profit or signal.price * 1.10  # 10% take profit
            else:
                stop_loss = signal.stop_loss or signal.price * 1.05  # 5% stop loss for short
                take_profit = signal.take_profit or signal.price * 0.90  # 10% take profit for short
            
            # Create simulated position
            position = SimulatedPosition(
                symbol=signal.symbol,
                quantity=quantity,
                entry_price=signal.price,
                entry_time=datetime.now(),
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Update simulated balance
            self.balance -= trade_amount
            self.positions[signal.symbol] = position
            
            # Send signal notification to Twitter
            self.notification_service.send_signal_notification(signal)
            
            self.logger.info(
                f"🎯 SIMULATED TRADE EXECUTED: {signal.symbol}\n"
                f"   Direction: {signal.direction.value}\n"
                f"   Quantity: {quantity:.6f}\n"
                f"   Entry Price: ${signal.price:.4f}\n"
                f"   Trade Amount: ${trade_amount:.2f}\n"
                f"   Stop Loss: ${stop_loss:.4f}\n"
                f"   Take Profit: ${take_profit:.4f}\n"
                f"   Remaining Balance: ${self.balance:.2f}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error simulating trade execution for {signal.symbol}: {e}")
            return False
    
    def update_simulated_positions(self) -> None:
        """Update simulated positions and check for exits."""
        if not self.positions:
            return
        
        symbols_to_close = []
        
        for symbol, position in self.positions.items():
            try:
                # Get current price
                current_price = self.market_data_provider.get_current_price(symbol)
                if not current_price:
                    continue
                
                # Calculate P&L
                pnl = (current_price - position.entry_price) * position.quantity
                pnl_percentage = ((current_price - position.entry_price) / position.entry_price) * 100
                
                self.logger.info(
                    f"📊 SIMULATED POSITION UPDATE: {symbol}\n"
                    f"   Entry: ${position.entry_price:.4f} → Current: ${current_price:.4f} ({pnl_percentage:+.2f}%)\n"
                    f"   P&L: ${pnl:+.2f} | Quantity: {position.quantity:.6f}\n"
                    f"   Stop Loss: ${position.stop_loss:.4f} | Take Profit: ${position.take_profit:.4f}"
                )
                
                # Check exit conditions
                should_close = False
                exit_reason = ""
                
                if current_price <= position.stop_loss:
                    should_close = True
                    exit_reason = "STOP_LOSS"
                elif current_price >= position.take_profit:
                    should_close = True
                    exit_reason = "TAKE_PROFIT"
                
                if should_close:
                    # Create trade record
                    trade = Trade(
                        id=f"{symbol}_{int(datetime.now().timestamp())}",
                        symbol=symbol,
                        direction=TradeDirection.BUY,  # Assuming long positions
                        quantity=position.quantity,
                        entry_price=position.entry_price,
                        exit_price=current_price,
                        entry_time=position.entry_time,
                        exit_time=datetime.now(),
                        status=TradeStatus.TAKE_PROFIT if exit_reason == "TAKE_PROFIT" else TradeStatus.STOP_LOSS,
                        pnl=pnl,
                        stop_loss=position.stop_loss,
                        take_profit=position.take_profit,
                        strategy_name="Simulated EMA Cross Strategy"
                    )
                    
                    # Update simulated balance
                    exit_value = current_price * position.quantity
                    self.balance += exit_value
                    
                    # Store completed trade
                    self.completed_trades.append(trade)
                    
                    # Send trade completion notification to Twitter
                    self.notification_service.send_trade_notification(trade)
                    
                    self.logger.info(
                        f"✅ SIMULATED TRADE CLOSED: {symbol} @ ${current_price:.4f} ({exit_reason})\n"
                        f"   P&L: ${pnl:+.2f}\n"
                        f"   Balance: ${self.balance:.2f}"
                    )
                    
                    symbols_to_close.append(symbol)
                    
            except Exception as e:
                self.logger.error(f"Error updating simulated position {symbol}: {e}")
        
        # Remove closed positions
        for symbol in symbols_to_close:
            del self.positions[symbol]
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary of the simulation."""
        total_trades = len(self.completed_trades)
        winning_trades = sum(1 for trade in self.completed_trades if trade.pnl > 0)
        losing_trades = total_trades - winning_trades
        
        total_pnl = sum(trade.pnl for trade in self.completed_trades if trade.pnl)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'active_positions': len(self.positions)
        }
    
    def run_simulation_cycle(self) -> None:
        """Run one simulation cycle."""
        try:
            self.logger.info("🔄 Starting simulation cycle...")
            
            # Update existing positions first
            self.update_simulated_positions()
            
            # Scan for new signals
            signals = self.scan_for_signals()
            
            # Execute new trades
            for signal in signals:
                if len(self.positions) < 3:  # Limit concurrent positions
                    self.simulate_trade_execution(signal)
                else:
                    self.logger.info(f"⚠️ Maximum positions reached, skipping {signal.symbol}")
            
            # Log performance summary
            performance = self.get_performance_summary()
            self.logger.info(
                f"📈 SIMULATION PERFORMANCE:\n"
                f"   Balance: ${performance['current_balance']:.2f} (${performance['total_pnl']:+.2f})\n"
                f"   Trades: {performance['total_trades']} (Win Rate: {performance['win_rate']:.1f}%)\n"
                f"   Active Positions: {performance['active_positions']}"
            )
            
        except Exception as e:
            self.logger.error(f"Error in simulation cycle: {e}")
    
    def run_continuous_simulation(self, scan_interval: int = 3600) -> None:
        """Run continuous simulation with periodic scanning."""
        self.logger.info(f"🚀 Starting continuous simulation (scan every {scan_interval}s)")
        
        try:
            while True:
                self.run_simulation_cycle()
                
                self.logger.info(f"⏳ Waiting {scan_interval} seconds until next scan...")
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Simulation stopped by user")
        except Exception as e:
            self.logger.error(f"Fatal error in simulation: {e}")
            raise
        finally:
            # Final performance report
            performance = self.get_performance_summary()
            self.logger.info(
                f"🏁 FINAL SIMULATION RESULTS:\n"
                f"   Initial Balance: ${performance['initial_balance']:.2f}\n"
                f"   Final Balance: ${performance['current_balance']:.2f}\n"
                f"   Total P&L: ${performance['total_pnl']:+.2f}\n"
                f"   Return: {((performance['current_balance'] - performance['initial_balance']) / performance['initial_balance'] * 100):+.2f}%\n"
                f"   Total Trades: {performance['total_trades']}\n"
                f"   Win Rate: {performance['win_rate']:.1f}%"
            )