"""
Position Management Service - Single Responsibility: Manage active positions.
"""

import json
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from ..core.interfaces import IPositionManager
from ..models import Position, Trade, TradeStatus, TradeDirection


class PositionManagementService(IPositionManager):
    """
    Service responsible for managing active trading positions.
    Handles position tracking, updates, and persistence.
    """
    
    def __init__(self, data_file: str = "data/active_trades.json"):
        """Initialize position manager with data file."""
        self.data_file = Path(data_file)
        self.positions: Dict[str, Position] = {}
        self.logger = logging.getLogger(__name__)
        self._load_positions()
    
    def get_positions(self) -> List[Position]:
        """Get all active positions."""
        return list(self.positions.values())
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol."""
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if there's an active position for a symbol."""
        return symbol in self.positions
    
    def add_position(self, position: Position) -> None:
        """Add a new position."""
        try:
            self.positions[position.symbol] = position
            self._save_positions()
            self.logger.info(f"Added position: {position.symbol} @ {position.entry_price}")
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
    
    def update_position(self, symbol: str, current_price: float) -> None:
        """Update position with current price."""
        try:
            if symbol in self.positions:
                self.positions[symbol].current_price = current_price
                self._save_positions()
        except Exception as e:
            self.logger.error(f"Error updating position {symbol}: {e}")
    
    def update_position_data(self, symbol: str, position: Position) -> None:
        """Update complete position data."""
        try:
            self.positions[symbol] = position  # Store regardless of whether it exists
            self._save_positions()
            self.logger.debug(f"Updated position data for {symbol}")
        except Exception as e:
            self.logger.error(f"Error updating position data for {symbol}: {e}")
    
    def update_position_oco_id(self, symbol: str, oco_order_id: str) -> None:
        """Update OCO order ID for a position."""
        try:
            if symbol in self.positions:
                self.positions[symbol].oco_order_id = oco_order_id
                self._save_positions()
                self.logger.info(f"Updated OCO order ID for {symbol}: {oco_order_id}")
            else:
                self.logger.warning(f"Position {symbol} not found for OCO ID update")
        except Exception as e:
            self.logger.error(f"Error updating OCO ID for {symbol}: {e}")
    
    def close_position(self, symbol: str, exit_price: float) -> Trade:
        """Close a position and return the completed trade."""
        try:
            if symbol not in self.positions:
                raise ValueError(f"No active position for {symbol}")
            
            position = self.positions[symbol]
            
            # Calculate P&L
            pnl = (exit_price - position.entry_price) * position.quantity
            
            # Create trade record
            trade = Trade(
                id=f"{symbol}_{int(datetime.now().timestamp())}",
                symbol=symbol,
                direction=TradeDirection.BUY,  # Assuming long positions for now
                quantity=position.quantity,
                entry_price=position.entry_price,
                exit_price=exit_price,
                entry_time=position.entry_time,
                exit_time=datetime.now(),
                status=TradeStatus.FILLED,
                pnl=pnl
            )
            
            # Remove from active positions
            del self.positions[symbol]
            self._save_positions()
            
            self.logger.info(f"Closed position: {symbol} @ {exit_price}, P&L: {pnl:.2f}")
            return trade
            
        except Exception as e:
            self.logger.error(f"Error closing position {symbol}: {e}")
            raise
    
    def update_stop_loss(self, symbol: str, new_stop_loss: float) -> None:
        """Update stop loss for a position."""
        try:
            if symbol in self.positions:
                self.positions[symbol].stop_loss = new_stop_loss
                self._save_positions()
                self.logger.info(f"Updated stop loss for {symbol}: {new_stop_loss}")
        except Exception as e:
            self.logger.error(f"Error updating stop loss for {symbol}: {e}")
    
    def update_trailing_stop(self, symbol: str, current_price: float) -> None:
        """Update trailing stop for a position."""
        try:
            if symbol not in self.positions:
                return
            
            position = self.positions[symbol]
            if not position.trailing_stop:
                return
            
            # Calculate new trailing stop
            trailing_distance = position.entry_price * (position.trailing_stop / 100)
            new_stop = current_price - trailing_distance
            
            # Only update if it's higher than current stop loss
            if not position.stop_loss or new_stop > position.stop_loss:
                position.stop_loss = new_stop
                self._save_positions()
                self.logger.info(f"Updated trailing stop for {symbol}: {new_stop}")
                
        except Exception as e:
            self.logger.error(f"Error updating trailing stop for {symbol}: {e}")
    
    def get_total_exposure(self) -> float:
        """Calculate total exposure across all positions."""
        total = 0.0
        for position in self.positions.values():
            total += position.current_price * position.quantity
        return total
    
    def get_total_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L across all positions."""
        total = 0.0
        for position in self.positions.values():
            total += position.unrealized_pnl
        return total
    
    def _load_positions(self) -> None:
        """Load positions from file."""
        try:
            if not self.data_file.exists():
                self.logger.info("No existing positions file found, starting fresh")
                return
            
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            for symbol, position_data in data.items():
                position = Position(
                    symbol=position_data['symbol'],
                    quantity=position_data['quantity'],
                    entry_price=position_data['entry_price'],
                    current_price=position_data['current_price'],
                    entry_time=datetime.fromisoformat(position_data['entry_time']),
                    stop_loss=position_data.get('stop_loss'),
                    take_profit=position_data.get('take_profit'),
                    trailing_stop=position_data.get('trailing_stop'),
                    oco_order_id=position_data.get('oco_order_id')
                )
                self.positions[symbol] = position
            
            self.logger.info(f"Loaded {len(self.positions)} active positions")
            
        except Exception as e:
            self.logger.error(f"Error loading positions: {e}")
            self.positions = {}
    
    def _save_positions(self) -> None:
        """Save positions to file."""
        try:
            # Create directory if it doesn't exist
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for symbol, position in self.positions.items():
                data[symbol] = {
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': position.current_price,
                    'entry_time': position.entry_time.isoformat(),
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit,
                    'trailing_stop': position.trailing_stop,
                    'oco_order_id': position.oco_order_id
                }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving positions: {e}")
