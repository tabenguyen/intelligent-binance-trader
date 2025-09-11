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
from .models import TradingConfig, MarketData, TradingSignal, Position, OrderResult
from .market_watcher import check_symbol_tradeable
from .services import (
    BinanceMarketDataService, BinanceTradeExecutor,
    TechnicalAnalysisService, RiskManagementService,
    PositionManagementService, LoggingNotificationService
)
from .services.enhanced_risk_management_service import EnhancedRiskManagementService
from .strategies import EMACrossStrategy
from .strategies.improved_ema_cross_strategy import ImprovedEMACrossStrategy
from .utils.config import load_strategy_configs


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
        
        self.risk_manager: IRiskManager = EnhancedRiskManagementService(config)
        
        self.position_manager: IPositionManager = PositionManagementService(
            config.get_mode_specific_active_trades_file()
        )
        
        self.notification_service: INotificationService = LoggingNotificationService()
        
        # Initialize strategies
        self.strategies: List[IStrategy] = self._initialize_strategies()
        
        self.logger.info(f"Trading Bot initialized with {len(self.strategies)} strategies")
    
    def start(self) -> None:
        """Start the trading bot for a single execution cycle."""
        try:
            self.logger.info("=" * 80)
            self.logger.info("🚀 STARTING TRADING BOT")
            self.logger.info("=" * 80)
            
            # Validate configuration
            self._validate_configuration()
            
            # Execute single trading cycle (no loop for scheduled execution)
            self._execute_single_cycle()
            
        except KeyboardInterrupt:
            self.logger.info("=" * 80)
            self.logger.info("🛑 TRADING BOT STOPPED BY USER")
            self.logger.info("=" * 80)
        except Exception as e:
            self.logger.error("=" * 80)
            self.logger.error(f"❌ TRADING BOT ERROR: {e}")
            self.logger.error("=" * 80)
            self.notification_service.send_error_notification(str(e))
        finally:
            self.stop()
    
    def start_continuous(self) -> None:
        """Start the trading bot in continuous mode (legacy mode)."""
        try:
            self.logger.info("=" * 80)
            self.logger.info("🚀 STARTING TRADING BOT - CONTINUOUS MODE")
            self.logger.info("=" * 80)
            self.running = True
            
            # Validate configuration
            self._validate_configuration()
            
            # Start main trading loop
            self._main_loop()
            
        except KeyboardInterrupt:
            self.logger.info("=" * 80)
            self.logger.info("🛑 TRADING BOT STOPPED BY USER")
            self.logger.info("=" * 80)
        except Exception as e:
            self.logger.error("=" * 80)
            self.logger.error(f"❌ TRADING BOT ERROR: {e}")
            self.logger.error("=" * 80)
            self.notification_service.send_error_notification(str(e))
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the trading bot."""
        self.logger.info("=" * 80)
        self.logger.info("🛑 STOPPING TRADING BOT")
        self.logger.info("=" * 80)
        self.running = False
    
    def _execute_single_cycle(self) -> None:
        """Execute a single trading cycle for scheduled execution."""
        try:
            self.logger.info("=" * 60)
            self.logger.info("🔄 STARTING TRADING CYCLE #1")
            self.logger.info("=" * 60)
            start_time = time.time()
            
            self._trading_cycle()
            
            cycle_duration = time.time() - start_time
            self.logger.info("-" * 60)
            self.logger.info(f"⏱️  CYCLE #1 COMPLETED in {cycle_duration:.2f}s")
            self.logger.info("-" * 60)
            self.logger.info("🏁 Single execution completed - exiting for scheduler control")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error("!" * 60)
            self.logger.error(f"❌ ERROR IN TRADING CYCLE: {e}")
            self.logger.error("!" * 60)
            self.notification_service.send_error_notification(str(e))
            raise  # Re-raise to let scheduler handle the error
    
    def _main_loop(self) -> None:
        """Main trading loop."""
        cycle_count = 0
        while self.running:
            try:
                cycle_count += 1
                self.logger.info("=" * 60)
                self.logger.info(f"🔄 STARTING TRADING CYCLE #{cycle_count}")
                self.logger.info("=" * 60)
                start_time = time.time()
                
                self._trading_cycle()
                
                cycle_duration = time.time() - start_time
                self.logger.info("-" * 60)
                self.logger.info(f"⏱️  CYCLE #{cycle_count} COMPLETED in {cycle_duration:.2f}s")
                self.logger.info("-" * 60)
                
                # Calculate next scan time
                next_scan_time = time.strftime('%H:%M:%S', time.localtime(time.time() + self.config.scan_interval))
                self.logger.info(f"💤 WAITING {self.config.scan_interval}s until next scan (next: {next_scan_time})")
                self.logger.info("=" * 60)
                
                time.sleep(self.config.scan_interval)
                
            except Exception as e:
                self.logger.error("!" * 60)
                self.logger.error(f"❌ ERROR IN TRADING CYCLE: {e}")
                self.logger.error("!" * 60)
                self.notification_service.send_error_notification(str(e))
                self.logger.info("💤 Waiting 60s before retrying after error...")
                time.sleep(60)  # Wait before retrying
    
    def _trading_cycle(self) -> None:
        """Execute one trading cycle."""
        
        # STEP 1: Refresh watchlist
        self.logger.info("🔹 STEP 1: REFRESHING WATCHLIST")
        self.logger.info("-" * 40)
        self._refresh_watchlist()

        # STEP 2: Update existing positions
        self.logger.info("🔹 STEP 2: UPDATING EXISTING POSITIONS")
        self.logger.info("-" * 40)
        active_positions = self.position_manager.get_positions()
        if active_positions:
            self.logger.info(f"📊 Found {len(active_positions)} active positions to update")
            self._update_positions()
        else:
            self.logger.info("📊 No active positions to update")
        
        # STEP 3: Scan for new opportunities
        self.logger.info("🔹 STEP 3: SCANNING FOR NEW OPPORTUNITIES")
        self.logger.info("-" * 40)
        symbols_to_scan = [symbol for symbol in self.config.symbols 
                          if not self.position_manager.has_position(symbol)]
        
        if symbols_to_scan:
            self.logger.info(f"🔍 Scanning {len(symbols_to_scan)} symbols for opportunities")
            self.logger.info(f"📋 Symbols: {', '.join(symbols_to_scan)}")
            
            # Collect all signals first
            all_signals = []
            
            for i, symbol in enumerate(symbols_to_scan, 1):
                try:
                    self.logger.info(f"📈 [{i}/{len(symbols_to_scan)}] Analyzing {symbol}...")
                    
                    # Check if symbol is tradeable before analysis
                    if not check_symbol_tradeable(symbol):
                        self.logger.warning(f"⚠️  Skipping {symbol} - market is closed or suspended")
                        continue
                    
                    # Get market data
                    market_data = self._get_market_data(symbol)
                    if not market_data:
                        self.logger.warning(f"⚠️  Could not get market data for {symbol}")
                        continue
                    
                    # Run strategies
                    for strategy in self.strategies:
                        if not strategy.is_enabled():
                            continue
                        
                        signal = strategy.analyze(market_data)
                        if signal and strategy.validate_signal(signal):
                            all_signals.append(signal)
                            self.logger.info(f"📡 Valid signal collected for {symbol} by {strategy.__class__.__name__} "
                                           f"(Core: {signal.core_conditions_count}/4, Confidence: {signal.confidence:.1%})")
                        
                except Exception as e:
                    self.logger.error(f"Error analyzing {symbol}: {e}")
            
            # STEP 4: Process signals
            self.logger.info("🔹 STEP 4: PROCESSING SIGNALS")
            self.logger.info("-" * 40)
            
            # Sort signals by core conditions count (descending), then by confidence (descending)
            if all_signals:
                all_signals.sort(key=lambda s: (s.core_conditions_count, s.confidence), reverse=True)
                
                self.logger.info(f"📋 Found {len(all_signals)} valid signals, processing in priority order:")
                for i, signal in enumerate(all_signals, 1):
                    self.logger.info(f"  {i}. {signal.symbol} - Core: {signal.core_conditions_count}/4, "
                                   f"Confidence: {signal.confidence:.1%}")
                
                # Process all signals in priority order
                signals_executed = 0
                for i, signal in enumerate(all_signals, 1):
                    try:
                        # Check if we already have a position for this symbol
                        if self.position_manager.has_position(signal.symbol):
                            self.logger.info(f"⏭️  Skipping {signal.symbol} - already have position")
                            continue
                        
                        self.logger.info(f"🎯 Processing signal {i}/{len(all_signals)}: {signal.symbol} "
                                       f"(Core: {signal.core_conditions_count}/4)")
                        self._process_signal(signal)
                        signals_executed += 1
                        
                    except Exception as e:
                        self.logger.error(f"❌ Error processing signal for {signal.symbol}: {e}")
                        continue
                
                signals_found = len(all_signals)
            else:
                signals_found = 0
                signals_executed = 0
                self.logger.info("📋 No valid signals found")
            
            # Summary of scanning results
            self.logger.info("🔹 STEP 4 SUMMARY")
            self.logger.info("-" * 40)
            self.logger.info(f"� Scan completed: {signals_found} signals found, {signals_executed} executed")
            
        else:
            self.logger.info("💼 All symbols have active positions - no scanning needed")

    def _refresh_watchlist(self) -> None:
        """Refresh symbols from top USDT movers and update config.symbols and watchlist file."""
        try:
            # Lazy import to avoid tight coupling
            from .market_watcher import update_watchlist_from_top_movers
            self.logger.info("📝 Refreshing watchlist from top 24h USDT movers...")
            top = update_watchlist_from_top_movers(limit=20)
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
            self.logger.info("🎯" + "=" * 50)
            self.logger.info(f"🎯 PROCESSING SIGNAL FOR {signal.symbol}")
            self.logger.info("🎯" + "=" * 50)
            self.logger.info(f"   Strategy: {signal.strategy_name}")
            self.logger.info(f"   Confidence: {signal.confidence:.1%}")
            self.logger.info(f"   Signal Price: ${signal.price:.4f}")
            self.logger.info(f"   Core Conditions: {signal.core_conditions_count}/4")
            
            # Check if symbol is tradeable (market not closed/suspended)
            if not check_symbol_tradeable(signal.symbol):
                self.logger.warning(f"❌ Signal for {signal.symbol} rejected - market is closed or suspended")
                return
            
            self.logger.info("💰" + "-" * 30)
            self.logger.info("💰 RISK MANAGEMENT & POSITION SIZING")
            self.logger.info("💰" + "-" * 30)
            
            # Get current balance
            current_balance = self.market_data_provider.get_account_balance()
            self.logger.info(f"   Current Balance: ${current_balance:.2f}")
            
            # Validate trade with risk manager
            if not self.risk_manager.validate_trade(signal, current_balance):
                self.logger.warning(f"❌ Signal for {signal.symbol} rejected by risk manager")
                return
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(signal, current_balance)
            
            # Calculate stop loss and take profit if not set
            stop_loss = signal.stop_loss or self.risk_manager.calculate_stop_loss(signal)
            take_profit = signal.take_profit or self.risk_manager.calculate_take_profit(signal)
            
            # Refresh balance just before executing to ensure accuracy
            final_balance = self.market_data_provider.get_account_balance()
            if final_balance < current_balance * 0.9:  # Balance dropped significantly
                self.logger.warning(f"⚠️  Balance changed during processing: ${current_balance:.2f} -> ${final_balance:.2f}")
                # Re-validate with new balance
                if not self.risk_manager.validate_trade(signal, final_balance):
                    self.logger.warning(f"❌ Signal for {signal.symbol} no longer valid with current balance")
                    return
                # Recalculate position size with updated balance
                position_size = self.risk_manager.calculate_position_size(signal, final_balance)
                current_balance = final_balance
            
            self.logger.info("🔥" + "-" * 30)
            self.logger.info("� EXECUTING TRADE")
            self.logger.info("🔥" + "-" * 30)
            self.logger.info(f"   Symbol: {signal.symbol}")
            self.logger.info(f"   Order Type: {self.config.order_type.upper()}")
            self.logger.info(f"   Position Size: {position_size:.6f}")
            self.logger.info(f"   Stop Loss: ${stop_loss:.4f}")
            self.logger.info(f"   Take Profit: ${take_profit:.4f}")
            
            # Execute trade based on order type
            if self.config.order_type.lower() == "market":
                result = self._execute_market_order(signal, position_size)
            elif self.config.order_type.lower() == "limit":
                result = self._execute_limit_order(signal, position_size)
            else:
                self.logger.error(f"❌ Unknown order type: {self.config.order_type}")
                return
            
            if result and result.success:
                self.logger.info("🎉" + "=" * 40)
                self.logger.info("🎉 TRADE EXECUTED SUCCESSFULLY!")
                self.logger.info("🎉" + "=" * 40)
                self.logger.info(f"   Symbol: {signal.symbol}")
                self.logger.info(f"   Quantity: {result.filled_quantity:.6f}")
                self.logger.info(f"   Entry Price: ${result.filled_price:.4f}")
                self.logger.info(f"   Total Value: ${result.filled_quantity * result.filled_price:.2f}")
                
                # Create position
                position = Position(
                    symbol=signal.symbol,
                    quantity=result.filled_quantity,
                    entry_price=result.filled_price,
                    current_price=result.filled_price,
                    entry_time=datetime.now(),
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                # Add position to manager
                self.position_manager.add_position(position)
                
                # Send notifications
                self.notification_service.send_signal_notification(signal)
                
                # Place OCO order for stop loss and take profit if enabled
                if self.config.enable_oco_orders:
                    self.logger.info("🛡️" + "-" * 30)
                    self.logger.info("🛡️ PLACING PROTECTION ORDERS")
                    self.logger.info("🛡️" + "-" * 30)
                    self.logger.info(f"📋 Placing OCO order for {signal.symbol} position...")
                    oco_result = self._place_oco_order(position)
                    if oco_result and oco_result.success:
                        # Update position with OCO order ID
                        position.oco_order_id = oco_result.order_id
                        self.position_manager.update_position_data(position.symbol, position)
                        self.logger.info(f"✅ OCO order successfully placed for {signal.symbol} (Order ID: {oco_result.order_id})")
                    else:
                        # OCO order failed - position remains unprotected
                        error_msg = oco_result.error_message if oco_result else "Unknown error"
                        self.logger.error("!" * 60)
                        self.logger.error(f"❌ CRITICAL: OCO order failed for {signal.symbol} - Position is unprotected!")
                        self.logger.error(f"   Error: {error_msg}")
                        self.logger.error(f"   Position Value: ${position.quantity * position.entry_price:.2f}")
                        self.logger.error(f"   Manual Action Required: Please place stop-loss orders manually via Binance interface")
                        self.logger.error("!" * 60)
                    
            else:
                error_msg = result.error_message if result else "Unknown error"
                self.logger.error("❌" + "=" * 40)
                self.logger.error(f"❌ TRADE EXECUTION FAILED")
                self.logger.error("❌" + "=" * 40)
                self.logger.error(f"   Symbol: {signal.symbol}")
                self.logger.error(f"   Error: {error_msg}")
                
        except Exception as e:
            self.logger.error("!" * 60)
            self.logger.error(f"❌ ERROR PROCESSING SIGNAL FOR {signal.symbol}: {e}")
            self.logger.error("!" * 60)
            self.notification_service.send_error_notification(str(e))
    
    def _execute_market_order(self, signal: TradingSignal, position_size: float) -> OrderResult:
        """Execute a market order."""
        return self.trade_executor.execute_market_buy(signal.symbol, position_size)
    
    def _execute_limit_order(self, signal: TradingSignal, position_size: float) -> OrderResult:
        """Execute a limit order with retries."""
        # Offset used to compute limit price from the latest market price each attempt
        offset = self.config.limit_order_offset_percentage / 100
        self.logger.info("📋" + "-" * 30)
        self.logger.info("📋 LIMIT ORDER STRATEGY")
        self.logger.info("📋" + "-" * 30)
        self.logger.info(f"📋 Using {self.config.limit_order_offset_percentage}% offset below last price")
        self.logger.info(f"📋 Max retries: {self.config.max_limit_order_retries}")
        
        for attempt in range(1, self.config.max_limit_order_retries + 1):
            self.logger.info(f"🔄" + "-" * 25)
            self.logger.info(f"🔄 LIMIT ORDER ATTEMPT {attempt}/{self.config.max_limit_order_retries}")
            self.logger.info(f"🔄" + "-" * 25)
            
            # Refresh current price before each attempt
            try:
                current_price = self.market_data_provider.get_current_price(signal.symbol)
                if not current_price or current_price <= 0:
                    raise ValueError("invalid current price")
            except Exception:
                current_price = signal.price
                self.logger.warning(f"⚠️  Could not fetch current price; using signal price ${signal.price:.4f}")

            limit_price = current_price * (1 - offset)

            self.logger.info(f"� Last Price: ${current_price:.4f} -> Limit Price: ${limit_price:.4f}")
            
            result = self.trade_executor.execute_limit_buy(signal.symbol, position_size, limit_price)
            
            if result.success:
                # Check if order was filled immediately
                if result.filled_quantity > 0:
                    self.logger.info(f"✅ Limit order filled immediately!")
                    return result
                else:
                    # Order placed, wait and check status
                    self.logger.info(f"⏳ Limit order placed (ID: {result.order_id}), waiting {self.config.limit_order_retry_delay}s...")
                    time.sleep(self.config.limit_order_retry_delay)
                    
                    # Check if order was filled during wait period
                    try:
                        self.logger.info(f"🔍 Checking order status for {result.order_id}...")
                        order_details = self.trade_executor.get_order_details(signal.symbol, result.order_id)
                        if order_details:
                            order_status = order_details.get('status')
                            self.logger.info(f"📋 Order {result.order_id} status: {order_status}")
                            if order_status == 'FILLED':
                                self.logger.info(f"✅ Limit order was filled during wait period!")
                                filled_qty = float(order_details.get('executedQty', 0))
                                avg_price = float(order_details.get('cummulativeQuoteQty', 0)) / filled_qty if filled_qty > 0 else result.filled_price
                                
                                # Return successful result
                                return OrderResult(
                                    success=True,
                                    order_id=result.order_id,
                                    filled_quantity=filled_qty,
                                    filled_price=avg_price,
                                    commission=0.0,  # TODO: Extract from order details
                                    raw_response=order_details
                                )
                            elif order_status in ['PARTIALLY_FILLED']:
                                self.logger.info(f"⚠️  Limit order partially filled, continuing...")
                                # For partial fills, we could handle differently, but for now treat as not filled
                        else:
                            self.logger.warning(f"⚠️  Could not get order details for {result.order_id}")
                    except Exception as e:
                        self.logger.warning(f"Could not check order status: {e}")
                    
                    # Order not filled, cancel and retry or switch to market order
                    if attempt == self.config.max_limit_order_retries:
                        self.logger.warning("⚠️" + "-" * 30)
                        self.logger.warning("⚠️  SWITCHING TO MARKET ORDER")
                        self.logger.warning("⚠️" + "-" * 30)
                        self.logger.warning(f"⚠️  Limit order not filled after {attempt} attempts")
                        
                        # Check if order was filled before cancelling
                        order_status = self.trade_executor.get_order_status(signal.symbol, result.order_id)
                        if order_status == 'FILLED':
                            self.logger.info(f"✅ Order was filled before cancellation!")
                            # Get filled order details and return success
                            order_details = self.trade_executor.get_order_details(signal.symbol, result.order_id)
                            if order_details:
                                filled_qty = float(order_details.get('executedQty', 0))
                                avg_price = float(order_details.get('cummulativeQuoteQty', 0)) / filled_qty if filled_qty > 0 else result.filled_price
                                return OrderResult(
                                    success=True,
                                    order_id=result.order_id,
                                    filled_quantity=filled_qty,
                                    filled_price=avg_price,
                                    commission=0.0,
                                    raw_response=order_details
                                )
                        self.trade_executor.cancel_order(signal.symbol, result.order_id)
                        return self.trade_executor.execute_market_buy(signal.symbol, position_size)
                    else:
                        # Check if order was filled before cancelling
                        order_status = self.trade_executor.get_order_status(signal.symbol, result.order_id)
                        if order_status == 'FILLED':
                            self.logger.info(f"✅ Order was filled before cancellation!")
                            # Get filled order details and return success
                            order_details = self.trade_executor.get_order_details(signal.symbol, result.order_id)
                            if order_details:
                                filled_qty = float(order_details.get('executedQty', 0))
                                avg_price = float(order_details.get('cummulativeQuoteQty', 0)) / filled_qty if filled_qty > 0 else result.filled_price
                                return OrderResult(
                                    success=True,
                                    order_id=result.order_id,
                                    filled_quantity=filled_qty,
                                    filled_price=avg_price,
                                    commission=0.0,
                                    raw_response=order_details
                                )
                        # Cancel and retry
                        self.trade_executor.cancel_order(signal.symbol, result.order_id)
            else:
                self.logger.warning(f"⚠️  Limit order attempt {attempt} failed: {result.error_message}")
                
        # If all attempts failed, try market order as fallback
        self.logger.warning(f"⚠️  All limit order attempts failed, trying market order as fallback")
        return self.trade_executor.execute_market_buy(signal.symbol, position_size)
    
    def _place_oco_order(self, position: Position) -> Optional['OrderResult']:
        """Place OCO (One-Cancels-Other) order for stop loss and take profit."""
        try:
            self.logger.info(f"📋 Placing OCO order for {position.symbol}")
            self.logger.info(f"   Position Entry: ${position.entry_price:.6f}")
            self.logger.info(f"   Position Quantity: {position.quantity}")
            self.logger.info(f"   Stop Loss: ${position.stop_loss:.6f}")
            self.logger.info(f"   Take Profit: ${position.take_profit:.6f}")
            
            # Calculate some diagnostics
            try:
                current_price = self.market_data_provider.get_current_price(position.symbol)
                pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                stop_distance = abs(position.stop_loss - current_price) / current_price * 100
                profit_distance = abs(position.take_profit - current_price) / current_price * 100
                
                self.logger.info(f"📊 OCO Order Context:")
                self.logger.info(f"   Current Price: ${current_price:.6f}")
                self.logger.info(f"   Current P&L: {pnl_pct:.2f}%")
                self.logger.info(f"   Stop Loss Distance: {stop_distance:.2f}%")
                self.logger.info(f"   Take Profit Distance: {profit_distance:.2f}%")
                
                # Validate price relationships
                if position.stop_loss >= current_price:
                    self.logger.warning(f"⚠️  STOP LOSS ISSUE: Stop loss ${position.stop_loss:.6f} >= current price ${current_price:.6f}")
                if position.take_profit <= current_price:
                    self.logger.warning(f"⚠️  TAKE PROFIT ISSUE: Take profit ${position.take_profit:.6f} <= current price ${current_price:.6f}")
                    
            except Exception as context_error:
                self.logger.warning(f"⚠️  Could not gather OCO context: {context_error}")
            
            result = self.trade_executor.execute_oco_order(
                symbol=position.symbol,
                quantity=position.quantity,
                stop_price=position.stop_loss,
                limit_price=position.take_profit
            )
            
            if result.success:
                self.logger.info(f"✅ OCO order placed successfully (ID: {result.order_id})")
                self.logger.info(f"   Order protects {position.quantity} {position.symbol.replace('USDT', '')}")
                self.logger.info(f"   Stop Loss: ${position.stop_loss:.6f}")
                self.logger.info(f"   Take Profit: ${position.take_profit:.6f}")
                return result
            else:
                self.logger.error(f"❌ Failed to place OCO order: {result.error_message}")
                
                # Enhanced failure analysis
                base_asset = position.symbol.replace('USDT', '').replace('BUSD', '').replace('BTC', '').replace('ETH', '')
                self.logger.error(f"🔍 OCO FAILURE ANALYSIS for {position.symbol}:")
                self.logger.error(f"   Asset: {base_asset}")
                self.logger.error(f"   Required Quantity: {position.quantity}")
                self.logger.error(f"   Position Value: ${position.quantity * position.entry_price:.2f}")
                
                # Log recent trade info if available
                if hasattr(position, 'entry_time'):
                    from datetime import datetime
                    entry_time = datetime.fromisoformat(position.entry_time.replace('Z', '+00:00'))
                    time_since_entry = datetime.now() - entry_time.replace(tzinfo=None)
                    self.logger.error(f"   Time Since Entry: {time_since_entry}")
                    if time_since_entry.total_seconds() < 60:
                        self.logger.error(f"   💡 Recent trade - balance may need time to sync")
                
                self.logger.error(f"🛠️  IMMEDIATE ACTIONS:")
                self.logger.error(f"   1. Check if {base_asset} balance is available")
                self.logger.error(f"   2. Verify no conflicting orders exist")
                self.logger.error(f"   3. Consider running balance-aware OCO script")
                self.logger.error(f"   4. Position remains UNPROTECTED until OCO is placed!")
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error placing OCO order for {position.symbol}: {e}")
            self.logger.error(f"🚨 CRITICAL: Position {position.symbol} has NO EXIT PROTECTION!")
            self.logger.error(f"   Quantity: {position.quantity}")
            self.logger.error(f"   Entry Price: ${position.entry_price:.6f}")
            self.logger.error(f"   Expected Stop Loss: ${position.stop_loss:.6f}")
            self.logger.error(f"   Expected Take Profit: ${position.take_profit:.6f}")
            self.logger.error(f"🛠️  MANUAL INTERVENTION REQUIRED:")
            self.logger.error(f"   • Set manual stop loss/take profit orders")
            self.logger.error(f"   • Monitor position closely")
            self.logger.error(f"   • Run OCO retry scripts")
            return None
    
    def _update_positions(self) -> None:
        """Update all active positions."""
        positions = self.position_manager.get_positions()
        
        for i, position in enumerate(positions, 1):
            try:
                self.logger.info(f"📊" + "-" * 40)
                self.logger.info(f"📊 UPDATING POSITION [{i}/{len(positions)}]: {position.symbol}")
                self.logger.info(f"📊" + "-" * 40)
                
                # Get current price
                current_price = self.market_data_provider.get_current_price(position.symbol)
                
                # Calculate P&L info
                old_price = position.current_price
                pnl = (current_price - position.entry_price) * position.quantity
                pnl_percentage = ((current_price - position.entry_price) / position.entry_price) * 100
                
                self.logger.info(f"   Entry: ${position.entry_price:.4f} → Current: ${current_price:.4f} ({pnl_percentage:+.2f}%)")
                self.logger.info(f"   P&L: ${pnl:+.2f} | Quantity: {position.quantity:.6f}")
                self.logger.info(f"   Stop Loss: ${position.stop_loss:.4f} | Take Profit: ${position.take_profit:.4f}")
                if position.oco_order_id:
                    self.logger.info(f"   OCO Order ID: {position.oco_order_id}")
                
                # Update position
                self.position_manager.update_position(position.symbol, current_price)
                
                # Check exit conditions
                self._check_exit_conditions(position, current_price)
                
            except Exception as e:
                self.logger.error(f"❌ Error updating position {position.symbol}: {e}")
    
    def _check_exit_conditions(self, position: Position, current_price: float) -> None:
        """Check if position should be closed."""
        try:
            should_close = False
            exit_reason = ""
            
            # Check OCO order status (for positions with tracked OCO order IDs)
            if position.oco_order_id:
                try:
                    # Get detailed OCO information for better logging
                    oco_details = self.trade_executor.get_oco_order_details(position.symbol, position.oco_order_id)
                    
                    if oco_details:
                        order_status = oco_details['status']
                        filled_type = oco_details.get('filled_order_type')
                        filled_price = oco_details.get('filled_price')
                        
                        self.logger.info(f"🔍 OCO Order Status for {position.symbol}: {order_status}")
                        
                        # Handle all possible OCO completion statuses
                        if order_status in ["ALL_DONE", "FILLED", "PARTIALLY_FILLED"]:
                            if filled_type and filled_price:
                                self.logger.info(f"✅ OCO order completed via {filled_type} at ${filled_price:.4f}")
                            else:
                                self.logger.info(f"✅ OCO order completed for {position.symbol} (Status: {order_status})")
                            
                            self.logger.info(f"🗑️  Removing completed position from active trades")
                            
                            # Close position record (OCO already executed the exit)
                            trade = self.position_manager.close_position(position.symbol, current_price)
                            
                            self.notification_service.send_trade_notification(trade)
                            self.logger.info(f"✅ Position closed: {position.symbol} @ ${current_price:.4f} (OCO Completed)")
                            return
                            
                        elif order_status in ["CANCELED", "REJECT"]:
                            self.logger.warning(f"⚠️  OCO order {position.oco_order_id} for {position.symbol} was cancelled/rejected (Status: {order_status})")
                            self.logger.info(f"🗑️  Removing position {position.symbol} - no exit protection")
                            
                            # Close position record without executing trade (since OCO was cancelled externally)
                            trade = self.position_manager.close_position(position.symbol, current_price)
                            
                            self.logger.info(f"✅ Position removed: {position.symbol} @ ${current_price:.4f} (OCO {order_status})")
                            return
                            
                        elif order_status == "EXECUTING":
                            self.logger.info(f"⏳ OCO order for {position.symbol} is still active")
                            # Continue to fallback checks if needed
                        
                        else:
                            self.logger.warning(f"⚠️  Unknown OCO order status '{order_status}' for {position.symbol}")
                            # Continue to fallback checks
                    else:
                        # Fallback to simple status check
                        order_status = self.trade_executor.get_oco_order_status(position.symbol, position.oco_order_id)
                        self.logger.info(f"🔍 OCO Order Status for {position.symbol}: {order_status}")
                        
                        if order_status in ["ALL_DONE", "FILLED", "PARTIALLY_FILLED"]:
                            self.logger.info(f"✅ OCO order completed for {position.symbol} (Status: {order_status})")
                            self.logger.info(f"🗑️  Removing completed position from active trades")
                            
                            # Close position record (OCO already executed the exit)
                            trade = self.position_manager.close_position(position.symbol, current_price)
                            
                            self.notification_service.send_trade_notification(trade)
                            self.logger.info(f"✅ Position closed: {position.symbol} @ ${current_price:.4f} (OCO Completed)")
                            return
                            
                        elif order_status in ["CANCELED", "REJECT"]:
                            self.logger.warning(f"⚠️  OCO order {position.oco_order_id} for {position.symbol} was cancelled/rejected (Status: {order_status})")
                            self.logger.info(f"🗑️  Removing position {position.symbol} - no exit protection")
                            
                            # Close position record without executing trade (since OCO was cancelled externally)
                            trade = self.position_manager.close_position(position.symbol, current_price)
                            
                            self.logger.info(f"✅ Position removed: {position.symbol} @ ${current_price:.4f} (OCO {order_status})")
                            return
                        
                except Exception as e:
                    self.logger.warning(f"Could not check OCO order status for {position.symbol}: {e}")
            
            # For legacy positions without OCO order ID, check if any OCO orders exist
            elif not position.oco_order_id:
                try:
                    open_orders = self.trade_executor.get_open_orders(position.symbol)
                    oco_orders = [order for order in open_orders if order.get('type') == 'OCO']
                    
                    if oco_orders:
                        # Found existing OCO orders, update position with the first one
                        oco_order = oco_orders[0]
                        position.oco_order_id = str(oco_order.get('orderId', ''))
                        self.position_manager.update_position_data(position.symbol, position)
                        self.logger.info(f"✅ Found existing OCO order for {position.symbol} (ID: {position.oco_order_id})")
                    else:
                        self.logger.warning(f"⚠️  No OCO orders found for {position.symbol} - position has no exit protection")
                        # Validate we actually hold this asset before creating OCO
                        base_asset = position.symbol.replace('USDT', '')
                        try:
                            current_balance = self.market_data_provider.get_account_balance(base_asset)
                            
                            # Round the position quantity to Binance precision (same as OCO order will use)
                            rounded_quantity = self.trade_executor._round_quantity(position.symbol, position.quantity)
                            
                            # Use a small tolerance for floating-point precision issues (0.1% tolerance)
                            tolerance = max(0.001, rounded_quantity * 0.001)  # At least 0.001 or 0.1% of quantity
                            
                            if current_balance >= (rounded_quantity - tolerance):
                                self.logger.info(f"🔧 Attempting to create missing OCO order...")
                                self.logger.info(f"   Verified balance: {current_balance} {base_asset}")
                                self.logger.info(f"   Required quantity: {rounded_quantity} (original: {position.quantity})")
                                self.logger.info(f"   Tolerance applied: {tolerance}")
                                
                                # Automatically create missing OCO order
                                oco_result = self._place_oco_order(position)
                                if oco_result and oco_result.success:
                                    # Update position with new OCO order ID
                                    position.oco_order_id = oco_result.order_id
                                    self.position_manager.update_position_data(position.symbol, position)
                                    self.logger.info(f"✅ Successfully created OCO order for {position.symbol} (ID: {oco_result.order_id})")
                                else:
                                    error_msg = oco_result.error_message if oco_result else "Unknown error"
                                    self.logger.error(f"❌ Failed to create OCO order for {position.symbol}: {error_msg}")
                                    self.logger.info(f"💡 Position remains unprotected - consider manual intervention")
                            else:
                                deficit = (rounded_quantity - tolerance) - current_balance
                                self.logger.warning(f"⚠️  Insufficient balance to create OCO:")
                                self.logger.warning(f"   Available: {current_balance} {base_asset}")
                                self.logger.warning(f"   Required: {rounded_quantity} (rounded from {position.quantity})")
                                self.logger.warning(f"   Deficit: {deficit:.6f} {base_asset}")
                                self.logger.info(f"💡 Position may have been partially/fully sold outside the bot")
                                self.logger.info(f"💡 Consider removing this position record or adjusting quantity")
                                
                        except Exception as balance_error:
                            self.logger.warning(f"Could not verify balance for {base_asset}: {balance_error}")
                            self.logger.info(f"💡 Consider manually setting stop loss/take profit or closing position")
                        
                except Exception as e:
                    self.logger.warning(f"Could not check/create OCO orders for {position.symbol}: {e}")
                    self.logger.info(f"💡 Consider manually setting stop loss/take profit or closing position")
            
            # Fallback: Check manual stop loss and take profit (if no OCO or OCO check failed)
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
        """Initialize trading strategies with proper configuration."""
        strategies = []
        
        # Load strategy configurations from environment
        strategy_configs = load_strategy_configs()
        
        # Use ENHANCED EMA Cross Strategy - "Quality over Quantity"
        ema_config = next((config for config in strategy_configs if "EMA Cross" in config.name), None)
        if ema_config:
            # Use the enhanced strategy for better quality trades
            improved_ema_strategy = ImprovedEMACrossStrategy(ema_config)
            strategies.append(improved_ema_strategy)
            self.logger.info("✅ Loaded ENHANCED EMA Cross Strategy - Quality over Quantity focus")
        else:
            # Fallback to enhanced strategy with default config
            improved_ema_strategy = ImprovedEMACrossStrategy()
            strategies.append(improved_ema_strategy)
            self.logger.info("✅ Loaded ENHANCED EMA Cross Strategy with default config")
        
        # Add more strategies here as needed
        
        return strategies
    
    def _validate_configuration(self) -> None:
        """Validate trading configuration."""
        self.logger.info("🔍" + "-" * 30)
        self.logger.info("🔍 VALIDATING CONFIGURATION")
        self.logger.info("🔍" + "-" * 30)
        
        if not self.config.api_key or not self.config.api_secret:
            self.logger.error("❌ API keys are missing!")
            raise ValueError("API keys are required")
        
        if not self.config.symbols:
            self.logger.error("❌ No symbols configured!")
            raise ValueError("No symbols configured")
        
        if self.config.trade_amount <= 0:
            self.logger.error("❌ Invalid trade amount!")
            raise ValueError("Trade amount must be positive")
        
        self.logger.info("✅ Configuration validated successfully")
        self.logger.info(f"   🔑 API Keys: Configured")
        self.logger.info(f"   📊 Symbols: {len(self.config.symbols)} configured")
        self.logger.info(f"   💰 Trade Amount: ${self.config.trade_amount}")
        self.logger.info(f"   🏦 Testnet Mode: {'Enabled' if self.config.testnet else 'Disabled'}")
        self.logger.info(f"   🔄 Scan Interval: {self.config.scan_interval}s")
    
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
