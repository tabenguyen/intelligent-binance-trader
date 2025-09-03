"""
Main Trading Bot implementation following SOLID principles.
"""

import logging
import time
from typing import List, Optional
from datetime import datetime

from .core.interfaces import (
    IStrategy, IMarketDataProvider, ITradeExecutor, 
    IRiskManager, IPositionManager, INotificationService,
    ITechnicalAnalyzer
)
from .models import TradingConfig, MarketData, TradingSignal, Position
from .services import (
    BinanceMarketDataService, BinanceTradeExecutor,
    TechnicalAnalysisService, RiskManagementService,
    PositionManagementService, LoggingNotificationService
)
from .strategies import EMACrossStrategy


class TradingBot:
    """
    Main Trading Bot class following SOLID principles.
    
    Dependency Inversion Principle: Depends on abstractions (interfaces) not concretions.
    Single Responsibility Principle: Orchestrates trading operations.
    Open-Closed Principle: Can be extended with new strategies without modification.
    """
    
    def __init__(self, config: TradingConfig):
        """
        Initialize trading bot with dependency injection.
        
        Args:
            config: Trading configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # Initialize services (Dependency Injection)
        self.market_data_provider: IMarketDataProvider = BinanceMarketDataService(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        self.technical_analyzer: ITechnicalAnalyzer = TechnicalAnalysisService()
        
        self.trade_executor: ITradeExecutor = BinanceTradeExecutor(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        self.risk_manager: IRiskManager = RiskManagementService(config.risk_config)
        
        self.position_manager: IPositionManager = PositionManagementService(
            config.active_trades_file
        )
        
        self.notification_service: INotificationService = LoggingNotificationService()
        
        # Initialize strategies
        self.strategies: List[IStrategy] = self._initialize_strategies()
        
        self.logger.info(f"Trading Bot initialized with {len(self.strategies)} strategies")
    
    def start(self) -> None:
        """Start the trading bot."""
        try:
            self.logger.info("🚀 Starting Trading Bot...")
            self.running = True
            
            # Validate configuration
            self._validate_configuration()
            
            # Start main trading loop
            self._main_loop()
            
        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped by user")
        except Exception as e:
            self.logger.error(f"Trading bot error: {e}")
            self.notification_service.send_error_notification(str(e))
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the trading bot."""
        self.logger.info("🛑 Stopping Trading Bot...")
        self.running = False
    
    def _main_loop(self) -> None:
        """Main trading loop."""
        while self.running:
            try:
                self._trading_cycle()
                time.sleep(self.config.scan_interval)
            except Exception as e:
                self.logger.error(f"Error in trading cycle: {e}")
                self.notification_service.send_error_notification(str(e))
                time.sleep(60)  # Wait before retrying
    
    def _trading_cycle(self) -> None:
        """Execute one trading cycle."""
        # Update existing positions
        self._update_positions()
        
        # Scan for new opportunities
        for symbol in self.config.symbols:
            if not self.position_manager.has_position(symbol):
                self._analyze_symbol(symbol)
    
    def _analyze_symbol(self, symbol: str) -> None:
        """Analyze a symbol for trading opportunities."""
        try:
            # Get market data
            market_data = self._get_market_data(symbol)
            if not market_data:
                return
            
            # Run strategies
            for strategy in self.strategies:
                if not strategy.is_enabled():
                    continue
                
                signal = strategy.analyze(market_data)
                if signal and strategy.validate_signal(signal):
                    self._process_signal(signal)
                    break  # Only take first valid signal
                    
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
    
    def _get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get comprehensive market data for a symbol."""
        try:
            # Get raw market data
            market_data = self.market_data_provider.get_market_data(
                symbol=symbol,
                interval=self.config.timeframe,
                limit=100
            )
            
            # Add technical analysis
            klines = self.market_data_provider.get_klines(
                symbol=symbol,
                interval=self.config.timeframe,
                limit=100
            )
            
            technical_analysis = self.technical_analyzer.calculate_indicators(symbol, klines)
            market_data.technical_analysis = technical_analysis
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def _process_signal(self, signal: TradingSignal) -> None:
        """Process a trading signal."""
        try:
            # Get current balance
            current_balance = self.market_data_provider.get_account_balance()
            
            # Validate trade with risk manager
            if not self.risk_manager.validate_trade(signal, current_balance):
                self.logger.info(f"Signal for {signal.symbol} rejected by risk manager")
                return
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(signal, current_balance)
            
            # Execute trade
            result = self.trade_executor.execute_market_buy(signal.symbol, position_size)
            
            if result.success:
                # Create position
                position = Position(
                    symbol=signal.symbol,
                    quantity=result.filled_quantity,
                    entry_price=result.filled_price,
                    current_price=result.filled_price,
                    entry_time=datetime.now(),
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit
                )
                
                self.position_manager.add_position(position)
                self.notification_service.send_signal_notification(signal)
                
                self.logger.info(
                    f"✅ Executed trade: {signal.symbol} @ ${result.filled_price:.2f}"
                )
            else:
                self.logger.error(f"Failed to execute trade: {result.error_message}")
                
        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")
            self.notification_service.send_error_notification(str(e))
    
    def _update_positions(self) -> None:
        """Update all active positions."""
        positions = self.position_manager.get_positions()
        
        for position in positions:
            try:
                # Get current price
                current_price = self.market_data_provider.get_current_price(position.symbol)
                
                # Update position
                self.position_manager.update_position(position.symbol, current_price)
                
                # Check exit conditions
                self._check_exit_conditions(position, current_price)
                
            except Exception as e:
                self.logger.error(f"Error updating position {position.symbol}: {e}")
    
    def _check_exit_conditions(self, position: Position, current_price: float) -> None:
        """Check if position should be closed."""
        try:
            should_close = False
            exit_reason = ""
            
            # Check stop loss
            if position.stop_loss and current_price <= position.stop_loss:
                should_close = True
                exit_reason = "Stop Loss"
            
            # Check take profit
            elif position.take_profit and current_price >= position.take_profit:
                should_close = True
                exit_reason = "Take Profit"
            
            if should_close:
                # Execute sell order
                result = self.trade_executor.execute_market_sell(
                    position.symbol, position.quantity
                )
                
                if result.success:
                    # Close position
                    trade = self.position_manager.close_position(
                        position.symbol, result.filled_price
                    )
                    
                    self.notification_service.send_trade_notification(trade)
                    
                    self.logger.info(
                        f"✅ Closed position: {position.symbol} @ ${result.filled_price:.2f} "
                        f"({exit_reason}) P&L: ${trade.pnl:.2f}"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error checking exit conditions for {position.symbol}: {e}")
    
    def _initialize_strategies(self) -> List[IStrategy]:
        """Initialize trading strategies."""
        strategies = []
        
        # Add EMA Cross Strategy
        ema_strategy = EMACrossStrategy()
        strategies.append(ema_strategy)
        
        # Add more strategies here as needed
        
        return strategies
    
    def _validate_configuration(self) -> None:
        """Validate trading configuration."""
        if not self.config.api_key or not self.config.api_secret:
            raise ValueError("API keys are required")
        
        if not self.config.symbols:
            raise ValueError("No symbols configured")
        
        if self.config.trade_amount <= 0:
            raise ValueError("Trade amount must be positive")
        
        self.logger.info("Configuration validated successfully")
    
    def get_status(self) -> dict:
        """Get current bot status."""
        positions = self.position_manager.get_positions()
        
        return {
            'running': self.running,
            'active_positions': len(positions),
            'total_exposure': self.position_manager.get_total_exposure(),
            'unrealized_pnl': self.position_manager.get_total_unrealized_pnl(),
            'strategies_count': len(self.strategies),
            'symbols': self.config.symbols
        }
