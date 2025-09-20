"""
Simulated Trading Bot - Demo version with virtual balance and Twitter notifications.

This bot operates as a simulation without using real account balances.
All trades are virtual and notifications are sent to Twitter instead of Telegram.
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import List
from typing import Dict, List, Optional
from dataclasses import dataclass

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from .core.interfaces import INotificationService
from .models import Trade, TradingSignal, TradeDirection, TradeStatus, Position
from .services.notification_service import TelegramNotificationService, LoggingNotificationService
from .services.market_data_service import BinanceMarketDataService
from .services.technical_analysis_service import TechnicalAnalysisService
from .services.position_management_service import PositionManagementService
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
    signal_message_id: Optional[str] = None  # Store original signal message ID for Telegram


class SimulatedTradingBot:
    """
    Simulated trading bot that:
    - Uses virtual balance instead of real account
    - Posts trading signals to Telegram signal group
    - Sends completion notifications when trades finish
    - Never executes real trades
    """
    
    def __init__(self, config):
        """Initialize the simulated trading bot."""
        self.config = config
        
        # Ensure simulation mode is enabled for proper file isolation
        self.config.simulation_mode = True
        
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
        
        # Initialize position manager with simulation-specific file
        self.position_manager = PositionManagementService(
            config.get_mode_specific_active_trades_file()
        )
        
        # Initialize risk management service (same as real trading bot)
        from .services.risk_management_service import RiskManagementService
        self.risk_manager = RiskManagementService(config)
        
        self.technical_analysis_service = TechnicalAnalysisService()
        
        # Initialize Twitter notification service
        self.notification_service = self._initialize_notification_service()
        
        # Initialize strategies
        self.strategy = EMACrossStrategy()
        
        # Load previous simulation state if it exists
        self.load_simulation_state()
        
        self.logger.info(f"🎯 Simulated Trading Bot initialized with ${self.balance:.2f} balance")
    
    def _initialize_notification_service(self) -> INotificationService:
        """Initialize the notification service with Telegram integration for simulation."""
        try:
            # For simulation mode, use Telegram notifications to signal group
            if (hasattr(self.config, 'telegram_bot_token') and self.config.telegram_bot_token and
                hasattr(self.config, 'telegram_signal_group_id') and self.config.telegram_signal_group_id):
                
                self.logger.info("✅ Initializing Telegram notification service for simulation")
                
                # Use signal group for simulation notifications
                chat_id = self.config.telegram_signal_group_id if self.config.simulation_use_signal_group else self.config.telegram_chat_id
                
                return TelegramNotificationService(
                    bot_token=self.config.telegram_bot_token,
                    chat_id=chat_id,
                    fallback_service=LoggingNotificationService()
                )
            else:
                self.logger.warning("⚠️ Telegram credentials not configured for simulation, using logging only")
                return LoggingNotificationService()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram service: {e}")
            return LoggingNotificationService()
    
    def scan_for_signals(self) -> List[TradingSignal]:
        """Scan watchlist for trading signals."""
        signals = []
        
        try:
            # First refresh watchlist to get latest top movers (same as real bot)
            self._refresh_watchlist()
            
            # Use same filtering logic as real trading bot
            symbols_to_scan = [symbol for symbol in self.config.symbols if symbol not in self.positions]
            
            for symbol in symbols_to_scan:
                try:
                    # Get market data and raw klines for technical analysis
                    market_data = self.market_data_service.get_market_data(
                        symbol, 
                        self.config.timeframe,
                        100  # Get 100 candles for analysis
                    )
                    
                    if not market_data:
                        continue
                    
                    # Get raw klines for technical analysis
                    klines = self.market_data_service.get_klines(
                        symbol,
                        self.config.timeframe,
                        100
                    )
                    
                    # Get technical analysis
                    technical_analysis = self.technical_analysis_service.calculate_indicators(
                        symbol, 
                        klines
                    )
                    market_data.technical_analysis = technical_analysis
                    
                    # Check strategy for signals
                    try:
                        signal = self.strategy.analyze(market_data)
                        if signal:
                            signals.append(signal)
                            self.logger.info(f"📡 Signal generated: {signal.symbol} {signal.direction.value} @ ${signal.price:.4f}")
                                
                    except Exception as e:
                        self.logger.error(f"Error in strategy for {symbol}: {e}")
                            
                except Exception as e:
                    self.logger.error(f"Error processing {symbol}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in signal scanning: {e}")
        
        return signals
    
    def simulate_trade_execution(self, signal: TradingSignal) -> bool:
        """Simulate trade execution with virtual balance."""
        try:
            # Use same position sizing logic as real trading bot
            position_size = self.risk_manager.calculate_position_size(signal, self.balance)
            
            # Check if position size is valid
            if position_size <= 0:
                self.logger.warning(f"Cannot execute trade for {signal.symbol}: Position size calculation returned 0")
                return False
            
            # Calculate trade amount (quantity * price)
            trade_amount = position_size * signal.price
            
            # Validate we have sufficient balance
            if trade_amount > self.balance:
                self.logger.warning(f"Insufficient balance for {signal.symbol}: Need ${trade_amount:.2f}, have ${self.balance:.2f}")
                return False
            
            # Use risk manager to calculate stop loss and take profit (same as real bot)
            stop_loss = self.risk_manager.calculate_stop_loss(signal)
            take_profit = self.risk_manager.calculate_take_profit(signal)
            
            # Create simulated position
            position = SimulatedPosition(
                symbol=signal.symbol,
                quantity=position_size,
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
                f"   Quantity: {position_size:.6f}\n"
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
                current_price = self.market_data_service.get_current_price(symbol)
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
                self.simulate_trade_execution(signal)
            
            # Log performance summary
            performance = self.get_performance_summary()
            self.logger.info(
                f"📈 SIMULATION PERFORMANCE:\n"
                f"   Balance: ${performance['current_balance']:.2f} (${performance['total_pnl']:+.2f})\n"
                f"   Trades: {performance['total_trades']} (Win Rate: {performance['win_rate']:.1f}%)\n"
                f"   Active Positions: {performance['active_positions']}"
            )
            
            # Save simulation state after each cycle
            self.save_simulation_state()
            
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
            
            # Save final state
            self.save_simulation_state()
    
    def save_simulation_state(self) -> None:
        """Save current simulation state to persistent storage."""
        try:
            import json
            from pathlib import Path
            
            # Prepare simulation state data
            state_data = {
                'balance': self.balance,
                'initial_balance': self.initial_balance,
                'positions': {},
                'completed_trades': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Convert positions to serializable format
            for symbol, position in self.positions.items():
                state_data['positions'][symbol] = {
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'entry_time': position.entry_time.isoformat(),
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit,
                    'signal_message_id': position.signal_message_id
                }
            
            # Convert completed trades to serializable format
            for trade in self.completed_trades:
                state_data['completed_trades'].append({
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'direction': trade.direction.value,
                    'quantity': trade.quantity,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                    'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                    'status': trade.status.value,
                    'pnl': trade.pnl,
                    'commission': trade.commission,
                    'strategy_name': trade.strategy_name,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit
                })
            
            # Save to file
            state_file = self.config.get_mode_specific_active_trades_file()
            Path(state_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
            self.logger.debug(f"💾 Simulation state saved to {state_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save simulation state: {e}")
    
    def load_simulation_state(self) -> None:
        """Load simulation state from persistent storage."""
        try:
            import json
            from pathlib import Path
            
            state_file = self.config.get_mode_specific_active_trades_file()
            
            if not Path(state_file).exists():
                self.logger.info("📂 No previous simulation state found, starting fresh")
                return
            
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            # Restore balance
            self.balance = state_data.get('balance', self.config.simulation_balance)
            self.initial_balance = state_data.get('initial_balance', self.config.simulation_balance)
            
            # Restore positions
            self.positions = {}
            for symbol, pos_data in state_data.get('positions', {}).items():
                position = SimulatedPosition(
                    symbol=pos_data['symbol'],
                    quantity=pos_data['quantity'],
                    entry_price=pos_data['entry_price'],
                    entry_time=datetime.fromisoformat(pos_data['entry_time']),
                    stop_loss=pos_data['stop_loss'],
                    take_profit=pos_data['take_profit'],
                    signal_message_id=pos_data.get('signal_message_id')
                )
                self.positions[symbol] = position
            
            # Restore completed trades
            self.completed_trades = []
            for trade_data in state_data.get('completed_trades', []):
                trade = Trade(
                    id=trade_data['id'],
                    symbol=trade_data['symbol'],
                    direction=TradeDirection(trade_data['direction']),
                    quantity=trade_data['quantity'],
                    entry_price=trade_data['entry_price'],
                    exit_price=trade_data.get('exit_price'),
                    entry_time=datetime.fromisoformat(trade_data['entry_time']) if trade_data['entry_time'] else None,
                    exit_time=datetime.fromisoformat(trade_data['exit_time']) if trade_data['exit_time'] else None,
                    status=TradeStatus(trade_data['status']),
                    pnl=trade_data.get('pnl'),
                    commission=trade_data.get('commission'),
                    strategy_name=trade_data.get('strategy_name'),
                    stop_loss=trade_data.get('stop_loss'),
                    take_profit=trade_data.get('take_profit')
                )
                self.completed_trades.append(trade)
            
            saved_at = state_data.get('timestamp', 'unknown')
            self.logger.info(f"📂 Simulation state loaded (saved at {saved_at})")
            self.logger.info(f"   Balance: ${self.balance:.2f}")
            self.logger.info(f"   Active Positions: {len(self.positions)}")
            self.logger.info(f"   Completed Trades: {len(self.completed_trades)}")
            
        except Exception as e:
            self.logger.error(f"Failed to load simulation state: {e}")
            self.logger.info("🔄 Starting with fresh simulation state")

    def _refresh_watchlist(self) -> None:
        """Refresh symbols from top USDT movers and update config.symbols and watchlist file."""
        try:
            # Lazy import to avoid tight coupling
            from .market_watcher import update_watchlist_from_top_movers
            self.logger.info("📝 Refreshing watchlist from top 24h USDT movers...")
            top = update_watchlist_from_top_movers(limit=self.config.watchlist_top_movers_limit, config=self.config)
            symbols = top if top else self._read_watchlist_file()
            if symbols:
                prev_count = len(self.config.symbols)
                self.config.symbols = symbols
                self.logger.info(f"✅ Watchlist updated: {prev_count} -> {len(symbols)} symbols")
                self.logger.info(f"📋 Current watchlist: {', '.join(symbols)}")
            else:
                self.logger.warning("⚠️  Watchlist refresh returned no symbols; keeping existing list")
        except Exception as e:
            self.logger.warning(f"⚠️  Could not refresh watchlist: {e}")

    def _read_watchlist_file(self) -> List[str]:
        """Read symbols from configured watchlist file."""
        try:
            # Try mode-specific watchlist first
            path = self.config.get_mode_specific_watchlist_file()
            try:
                with open(path, 'r') as f:
                    lines = [ln.strip() for ln in f.readlines()]
                symbols = [s for s in lines if s]
                if symbols:
                    return symbols
            except FileNotFoundError:
                pass
            
            # Fallback to generic watchlist
            path = self.config.watchlist_file
            with open(path, 'r') as f:
                lines = [ln.strip() for ln in f.readlines()]
            return [s for s in lines if s]
        except Exception:
            return []