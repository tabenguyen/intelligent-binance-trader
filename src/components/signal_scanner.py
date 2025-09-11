"""
Signal Scanner Component - Component #1
Task: Analyze 4H charts and find new BUY signals
Frequency: Every 4 hours (07:05, 11:05, 15:05, etc.)
Logic: Market analysis + Place new buy orders when USDT is available
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from ..models import TradingConfig, TradingSignal, Position
from ..core.interfaces import IStrategy
from ..services import (
    BinanceMarketDataService, BinanceTradeExecutor,
    TechnicalAnalysisService, RiskManagementService,
    PositionManagementService, LoggingNotificationService
)
from ..strategies.improved_ema_cross_strategy import ImprovedEMACrossStrategy
from ..market_watcher import MarketWatcher
from ..utils.config import load_strategy_configs


class SignalScanner:
    """
    Component #1: Signal Scanner
    Responsible for analyzing market and generating new trading signals
    """
    
    def __init__(self, config: TradingConfig):
        """Initialize Signal Scanner with trading configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.market_data_provider = BinanceMarketDataService(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        self.trade_executor = BinanceTradeExecutor(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        self.technical_analyzer = TechnicalAnalysisService()
        self.risk_manager = RiskManagementService(config)
        
        # Initialize position manager with correct data file path
        data_file = getattr(config, 'active_trades_file', 'data/active_trades.json')
        self.position_manager = PositionManagementService(data_file)
        self.notification_service = LoggingNotificationService()
        
        # Initialize market watcher
        self.market_watcher = MarketWatcher(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        # Load strategies
        strategy_configs = load_strategy_configs()
        self.strategies: List[IStrategy] = [
            ImprovedEMACrossStrategy(strategy_configs[0])  # Use first strategy config
        ]
        
        self.logger.info(f"✅ Signal Scanner initialized with {len(self.strategies)} strategies")
    
    def scan_for_signals(self, triggered_by_order: bool = False) -> List[TradingSignal]:
        """
        Main scanning function - analyzes market for new opportunities.
        
        Args:
            triggered_by_order: True if scan was triggered by order completion
            
        Returns:
            List of valid trading signals
        """
        try:
            trigger_type = "ORDER COMPLETION" if triggered_by_order else "SCHEDULED"
            self.logger.info("=" * 80)
            self.logger.info(f"🔍 SIGNAL SCANNER - TRIGGERED BY {trigger_type}")
            self.logger.info("=" * 80)
            
            # Step 1: Check available USDT balance
            usdt_balance = self._get_available_usdt_balance()
            if usdt_balance < self.config.trade_amount:
                self.logger.info(f"💰 Insufficient USDT balance: ${usdt_balance:.2f} < ${self.config.trade_amount}")
                self.logger.info("⏸️ Scanner paused - waiting for order completion to free up USDT")
                return []
            
            self.logger.info(f"💰 Available USDT: ${usdt_balance:.2f} - Proceeding with scan")
            
            # Step 2: Refresh watchlist (only if not triggered by order)
            if not triggered_by_order:
                self._refresh_watchlist()
            
            # Step 3: Load watchlist symbols
            symbols = self._load_watchlist_symbols()
            if not symbols:
                self.logger.warning("📋 No symbols in watchlist")
                return []
            
            # Step 4: Scan for opportunities
            signals = self._scan_symbols_for_signals(symbols, triggered_by_order)
            
            # Step 5: Execute valid signals
            executed_signals = self._execute_signals(signals)
            
            self.logger.info("=" * 80)
            self.logger.info(f"🏁 SIGNAL SCANNER COMPLETE - {len(executed_signals)} signals executed")
            self.logger.info("=" * 80)
            
            return executed_signals
            
        except Exception as e:
            self.logger.error(f"❌ Signal Scanner error: {e}")
            self.notification_service.send_error_notification(str(e))
            return []
    
    def _get_available_usdt_balance(self) -> float:
        """Get available USDT balance for trading."""
        try:
            account_info = self.trade_executor.get_account_info()
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'USDT':
                    free_balance = float(balance['free'])
                    self.logger.info(f"💰 USDT Balance - Free: ${free_balance:.2f}")
                    return free_balance
            
            self.logger.warning("💰 USDT balance not found in account info")
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Error getting USDT balance: {e}")
            return 0.0
    
    def _refresh_watchlist(self) -> None:
        """Refresh watchlist with top movers."""
        try:
            self.logger.info("🔹 REFRESHING WATCHLIST")
            self.logger.info("-" * 40)
            self.logger.info("📝 Refreshing watchlist from top 24h USDT movers...")
            
            old_count = len(self._load_watchlist_symbols())
            
            # Get top movers and write to watchlist
            top_movers = self.market_watcher.get_top_movers(limit=20)
            if top_movers:
                watchlist_file = self.config.get_watchlist_file()
                self.market_watcher.write_watchlist(top_movers, watchlist_file)
                new_count = len(top_movers)
                self.logger.info(f"✅ Watchlist updated: {old_count} -> {new_count} symbols")
            else:
                self.logger.warning("⚠️ No top movers found")
            
        except Exception as e:
            self.logger.error(f"❌ Error refreshing watchlist: {e}")
    
    def _load_watchlist_symbols(self) -> List[str]:
        """Load symbols from watchlist file."""
        try:
            watchlist_file = self.config.get_watchlist_file()
            if not Path(watchlist_file).exists():
                self.logger.warning(f"📋 Watchlist file not found: {watchlist_file}")
                return []
            
            with open(watchlist_file, 'r') as f:
                symbols = [line.strip() for line in f if line.strip()]
            
            self.logger.info(f"📋 Loaded {len(symbols)} symbols from watchlist")
            return symbols
            
        except Exception as e:
            self.logger.error(f"❌ Error loading watchlist: {e}")
            return []
    
    def _scan_symbols_for_signals(self, symbols: List[str], triggered_by_order: bool) -> List[TradingSignal]:
        """Scan symbols for trading signals."""
        signals = []
        scan_type = "TRIGGERED" if triggered_by_order else "SCHEDULED"
        
        self.logger.info(f"🔹 {scan_type} SIGNAL SCAN")
        self.logger.info("-" * 40)
        self.logger.info(f"🔍 Scanning {len(symbols)} symbols for opportunities")
        
        # Log symbols for transparency
        symbols_str = ", ".join(symbols[:10])  # Show first 10
        if len(symbols) > 10:
            symbols_str += f", ... (+{len(symbols) - 10} more)"
        self.logger.info(f"📋 Symbols: {symbols_str}")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                self.logger.info(f"📈 [{i}/{len(symbols)}] Analyzing {symbol}...")
                
                # Get market data
                market_data = self.market_data_provider.get_market_data(
                    symbol=symbol,
                    interval=self.config.timeframe,
                    limit=200
                )
                
                if not market_data or len(market_data.candles) < 100:
                    self.logger.warning(f"❌ {symbol}: Insufficient market data")
                    continue
                
                # Check for signals using all strategies
                for strategy in self.strategies:
                    signal = strategy.analyze(market_data)
                    if signal and signal.action == 'BUY':
                        signals.append(signal)
                        self.logger.info(f"✅ {symbol}: BUY signal generated by {strategy.__class__.__name__}")
                        break  # One signal per symbol
                
            except Exception as e:
                self.logger.error(f"❌ Error analyzing {symbol}: {e}")
                continue
        
        self.logger.info(f"🎯 Signal scan complete: {len(signals)} BUY signals found")
        return signals
    
    def _execute_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Execute valid trading signals."""
        if not signals:
            self.logger.info("📋 No signals to execute")
            return []
        
        self.logger.info("🔹 EXECUTING SIGNALS")
        self.logger.info("-" * 40)
        
        executed_signals = []
        available_usdt = self._get_available_usdt_balance()
        
        for signal in signals:
            try:
                # Check if we still have enough USDT
                if available_usdt < self.config.trade_amount:
                    self.logger.info(f"💰 Insufficient USDT for {signal.symbol}: ${available_usdt:.2f} < ${self.config.trade_amount}")
                    break
                
                # Execute the signal
                result = self.trade_executor.execute_trade(signal)
                if result and result.success:
                    executed_signals.append(signal)
                    available_usdt -= self.config.trade_amount
                    self.logger.info(f"✅ {signal.symbol}: Signal executed successfully")
                    
                    # Log the new position
                    self.position_manager.add_position(Position(
                        symbol=signal.symbol,
                        entry_price=signal.entry_price,
                        quantity=result.quantity,
                        stop_loss=signal.stop_loss,
                        take_profit=signal.take_profit,
                        timestamp=datetime.now()
                    ))
                else:
                    self.logger.error(f"❌ {signal.symbol}: Failed to execute signal")
                
            except Exception as e:
                self.logger.error(f"❌ Error executing signal for {signal.symbol}: {e}")
        
        self.logger.info(f"🏆 Execution complete: {len(executed_signals)}/{len(signals)} signals executed")
        return executed_signals


def main():
    """Standalone entry point for Signal Scanner."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Now import from src
    from src.utils import load_config, setup_logging
    
    try:
        # Load configuration
        config = load_config()
        
        # Setup logging
        log_file = config.log_file or config.get_mode_specific_log_file()
        setup_logging(level=config.log_level, log_file=log_file)
        
        # Create and run scanner
        scanner = SignalScanner(config)
        
        # Check if triggered by order completion
        triggered_by_order = '--triggered-by-order' in sys.argv
        
        scanner.scan_for_signals(triggered_by_order=triggered_by_order)
        
    except Exception as e:
        print(f"Failed to run Signal Scanner: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
