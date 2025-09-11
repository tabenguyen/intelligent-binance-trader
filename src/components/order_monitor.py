"""
Order Monitor Component - Component #2
Task: Continuously monitor status of placed orders (buy orders, OCO orders)
Frequency: Very high frequency, e.g., every minute (or using Binance WebSocket for real-time updates)
Logic: Continuously asks Binance: "Have my orders been matched?"
"""

import logging
import time
import json
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from pathlib import Path

from ..models import TradingConfig, Position
from ..services import BinanceTradeExecutor, PositionManagementService, LoggingNotificationService


class OrderMonitor:
    """
    Component #2: Order Monitor
    Responsible for monitoring order status and triggering signal scanner when orders complete
    """
    
    def __init__(self, config: TradingConfig):
        """Initialize Order Monitor with trading configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.trade_executor = BinanceTradeExecutor(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        # Initialize position manager with correct data file path
        data_file = getattr(config, 'active_trades_file', 'data/active_trades.json')
        self.position_manager = PositionManagementService(data_file)
        self.notification_service = LoggingNotificationService()
        
        # Tracking state
        self.monitored_orders: Set[str] = set()  # Order IDs being monitored
        self.last_usdt_balance: Optional[float] = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        self.logger.info("✅ Order Monitor initialized")
    
    def start_monitoring(self) -> None:
        """
        Start continuous order monitoring loop.
        This is the main function that runs continuously.
        """
        self.logger.info("=" * 80)
        self.logger.info("👁️ ORDER MONITOR - STARTING CONTINUOUS MONITORING")
        self.logger.info("=" * 80)
        monitor_interval = getattr(self.config, 'monitor_interval_seconds', 60)
        self.logger.info(f"🔄 Monitor frequency: Every {monitor_interval} seconds")
        
        while True:
            try:
                cycle_start = time.time()
                
                # Monitor orders and detect completions
                order_completed = self._monitor_orders()
                
                # If order completed, trigger signal scanner
                if order_completed:
                    self._trigger_signal_scanner()
                
                # Reset error counter on successful cycle
                self.consecutive_errors = 0
                
                # Calculate sleep time
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, monitor_interval - cycle_duration)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                self.logger.info("=" * 80)
                self.logger.info("🛑 ORDER MONITOR STOPPED BY USER")
                self.logger.info("=" * 80)
                break
                
            except Exception as e:
                self.consecutive_errors += 1
                self.logger.error(f"❌ Order Monitor error #{self.consecutive_errors}: {e}")
                
                if self.consecutive_errors >= self.max_consecutive_errors:
                    self.logger.error(f"💥 Too many consecutive errors ({self.consecutive_errors}), stopping monitor")
                    self.notification_service.send_error_notification(
                        f"Order Monitor stopped due to {self.consecutive_errors} consecutive errors"
                    )
                    break
                
                # Progressive backoff on errors
                error_sleep_time = min(300, 30 * self.consecutive_errors)  # Max 5 minutes
                self.logger.info(f"😴 Sleeping {error_sleep_time}s before retry...")
                time.sleep(error_sleep_time)
    
    def _monitor_orders(self) -> bool:
        """
        Monitor orders and detect completions.
        
        Returns:
            True if any order was completed (FILLED)
        """
        try:
            # Get current positions and orders
            positions = self.position_manager.get_positions()
            
            if not positions:
                # No active positions, check for USDT balance changes (buy orders filled)
                return self._check_usdt_balance_changes()
            
            # Monitor active positions for TP/SL completion
            return self._monitor_active_positions(positions)
            
        except Exception as e:
            self.logger.error(f"❌ Error in order monitoring: {e}")
            return False
    
    def _check_usdt_balance_changes(self) -> bool:
        """
        Check for USDT balance changes that indicate order completion.
        Used when no active positions exist.
        """
        try:
            current_balance = self._get_usdt_balance()
            
            if self.last_usdt_balance is None:
                self.last_usdt_balance = current_balance
                return False
            
            # Check for significant balance increase (TP/SL filled)
            balance_increase = current_balance - self.last_usdt_balance
            
            if balance_increase > (self.config.trade_amount * 0.1):  # 10% threshold
                self.logger.info(f"💰 USDT balance increased: ${self.last_usdt_balance:.2f} -> ${current_balance:.2f}")
                self.logger.info("🎯 ORDER COMPLETION DETECTED - TP/SL order filled")
                self.last_usdt_balance = current_balance
                return True
            
            # Update balance for next check
            self.last_usdt_balance = current_balance
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error checking USDT balance: {e}")
            return False
    
    def _monitor_active_positions(self, positions: List[Position]) -> bool:
        """
        Monitor active positions for OCO order completion.
        
        Args:
            positions: List of active positions
            
        Returns:
            True if any position was closed (TP/SL filled)
        """
        order_completed = False
        
        for position in positions:
            try:
                # Check if position's OCO orders are still active
                orders = self._get_open_orders_for_symbol(position.symbol)
                
                # If no open orders for this symbol, position was closed
                if not orders:
                    self.logger.info(f"🎯 POSITION CLOSED: {position.symbol}")
                    self.logger.info(f"   📊 Entry: ${position.entry_price:.6f}")
                    self.logger.info(f"   🎯 TP: ${position.take_profit:.6f}")
                    self.logger.info(f"   🛑 SL: ${position.stop_loss:.6f}")
                    
                    # Remove position from tracking
                    self.position_manager.remove_position(position.symbol)
                    order_completed = True
                
            except Exception as e:
                self.logger.error(f"❌ Error monitoring position {position.symbol}: {e}")
        
        if order_completed:
            self.logger.info("🔄 ORDER COMPLETION DETECTED - Position(s) closed")
        
        return order_completed
    
    def _get_usdt_balance(self) -> float:
        """Get current USDT balance."""
        try:
            # Use the client directly since BinanceTradeExecutor doesn't expose account info
            if hasattr(self.trade_executor, 'client'):
                account_info = self.trade_executor.client.account()
                for balance in account_info.get('balances', []):
                    if balance['asset'] == 'USDT':
                        free_balance = float(balance['free'])
                        return free_balance
            
            self.logger.warning("💰 USDT balance not found in account info")
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Error getting USDT balance: {e}")
            return 0.0
    
    def _get_open_orders_for_symbol(self, symbol: str) -> List[Dict]:
        """Get open orders for a specific symbol."""
        try:
            orders = self.trade_executor.get_open_orders(symbol)
            return orders or []
        except Exception as e:
            self.logger.error(f"❌ Error getting open orders for {symbol}: {e}")
            return []
    
    def _trigger_signal_scanner(self) -> None:
        """
        Trigger Signal Scanner to run immediately.
        The magic connection: When Order Monitor detects completion,
        it immediately triggers Signal Scanner to look for new opportunities.
        """
        try:
            self.logger.info("🚀" * 20)
            self.logger.info("🚀 TRIGGERING SIGNAL SCANNER - ORDER COMPLETION DETECTED")
            self.logger.info("🚀" * 20)
            
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent
            
            # Run Signal Scanner with triggered flag
            cmd = [
                "uv", "run", "python", "-m", "src.components.signal_scanner",
                "--triggered-by-order"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info("✅ Signal Scanner triggered successfully")
                self.logger.info("🔄 Returning to order monitoring...")
            else:
                self.logger.error(f"❌ Signal Scanner failed with code {result.returncode}")
                self.logger.error(f"stderr: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            self.logger.error("⏰ Signal Scanner timed out after 5 minutes")
        except Exception as e:
            self.logger.error(f"❌ Failed to trigger Signal Scanner: {e}")
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status for debugging."""
        try:
            positions = self.position_manager.get_positions()
            usdt_balance = self._get_usdt_balance()
            
            return {
                'active_positions': len(positions),
                'usdt_balance': usdt_balance,
                'last_usdt_balance': self.last_usdt_balance,
                'consecutive_errors': self.consecutive_errors,
                'positions': [
                    {
                        'symbol': p.symbol,
                        'entry_price': p.entry_price,
                        'take_profit': p.take_profit,
                        'stop_loss': p.stop_loss
                    }
                    for p in positions
                ]
            }
        except Exception as e:
            return {'error': str(e)}


def main():
    """Standalone entry point for Order Monitor."""
    import sys
    import os
    from pathlib import Path
    
    # Add project root to path 
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Now import from src
    from src.utils import load_config, setup_logging
    
    try:
        # Load configuration
        config = load_config()
        
        # Add monitor-specific configuration
        config.monitor_interval_seconds = getattr(config, 'monitor_interval_seconds', 60)  # Default 1 minute
        
        # Setup logging with monitor-specific log file
        log_file = "logs/order_monitor.log"
        setup_logging(level=config.log_level, log_file=log_file)
        
        # Create and start monitor
        monitor = OrderMonitor(config)
        monitor.start_monitoring()
        
    except Exception as e:
        print(f"Failed to start Order Monitor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()