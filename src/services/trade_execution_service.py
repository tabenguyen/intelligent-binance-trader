"""
Trade Execution Service - Single Responsibility: Execute trades on Binance.
"""

import logging
import math
from typing import Optional
from binance.spot import Spot as Client
from binance.error import ClientError

from ..core.interfaces import ITradeExecutor
from ..models import OrderResult


class BinanceTradeExecutor(ITradeExecutor):
    """
    Binance implementation of trade executor.
    Responsible only for executing trades through Binance API.
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """Initialize Binance client for trading."""
        if testnet:
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret,
                base_url="https://testnet.binance.vision"
            )
        else:
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret
            )
        self.logger = logging.getLogger(__name__)
    
    def execute_market_buy(self, symbol: str, quantity: float) -> OrderResult:
        """Execute a market buy order."""
        try:
            # Round quantity to appropriate precision
            quantity = self._round_quantity(symbol, quantity)
            
            response = self.client.new_order(
                symbol=symbol,
                side="BUY",
                type="MARKET",
                quantity=quantity
            )
            
            return self._parse_order_response(response, True)
            
        except ClientError as e:
            self.logger.error(f"Error executing market buy for {symbol}: {e}")
            return OrderResult(
                success=False,
                order_id=None,
                filled_quantity=0.0,
                filled_price=0.0,
                commission=0.0,
                error_message=str(e)
            )
    
    def execute_market_sell(self, symbol: str, quantity: float) -> OrderResult:
        """Execute a market sell order."""
        try:
            # Round quantity to appropriate precision
            quantity = self._round_quantity(symbol, quantity)
            
            response = self.client.new_order(
                symbol=symbol,
                side="SELL",
                type="MARKET",
                quantity=quantity
            )
            
            return self._parse_order_response(response, True)
            
        except ClientError as e:
            self.logger.error(f"Error executing market sell for {symbol}: {e}")
            return OrderResult(
                success=False,
                order_id=None,
                filled_quantity=0.0,
                filled_price=0.0,
                commission=0.0,
                error_message=str(e)
            )
    
    def execute_oco_order(self, symbol: str, quantity: float, 
                         stop_price: float, limit_price: float) -> OrderResult:
        """Execute an OCO (One-Cancels-Other) order."""
        try:
            # Round values to appropriate precision
            quantity = self._round_quantity(symbol, quantity)
            stop_price = self._round_price(symbol, stop_price)
            limit_price = self._round_price(symbol, limit_price)
            
            response = self.client.new_oco_order(
                symbol=symbol,
                side="SELL",
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price,
                stopLimitPrice=stop_price,
                stopLimitTimeInForce="GTC"
            )
            
            return self._parse_oco_response(response)
            
        except ClientError as e:
            self.logger.error(f"Error executing OCO order for {symbol}: {e}")
            return OrderResult(
                success=False,
                order_id=None,
                filled_quantity=0.0,
                filled_price=0.0,
                commission=0.0,
                error_message=str(e),
                raw_response=None
            )
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an existing order."""
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Successfully cancelled order {order_id} for {symbol}")
            return True
        except ClientError as e:
            self.logger.error(f"Error cancelling order {order_id} for {symbol}: {e}")
            return False
    
    def get_min_notional(self, symbol: str) -> float:
        """Get minimum notional value for a symbol."""
        try:
            exchange_info = self.client.exchange_info()
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    for filter_info in symbol_info['filters']:
                        if filter_info['filterType'] == 'NOTIONAL':
                            return float(filter_info['minNotional'])
            return 10.0  # Default fallback
        except Exception as e:
            self.logger.warning(f"Could not get min notional for {symbol}: {e}")
            return 10.0
    
    def _parse_order_response(self, response: dict, success: bool) -> OrderResult:
        """Parse standard order response."""
        if not success:
            return OrderResult(
                success=False,
                order_id=None,
                filled_quantity=0.0,
                filled_price=0.0,
                commission=0.0,
                raw_response=response
            )
        
        # Calculate average price and total commission
        fills = response.get('fills', [])
        total_qty = 0.0
        total_cost = 0.0
        total_commission = 0.0
        
        for fill in fills:
            qty = float(fill['qty'])
            price = float(fill['price'])
            commission = float(fill['commission'])
            
            total_qty += qty
            total_cost += qty * price
            total_commission += commission
        
        avg_price = total_cost / total_qty if total_qty > 0 else 0.0
        
        return OrderResult(
            success=True,
            order_id=str(response.get('orderId')),
            filled_quantity=total_qty,
            filled_price=avg_price,
            commission=total_commission,
            raw_response=response
        )
    
    def _parse_oco_response(self, response: dict) -> OrderResult:
        """Parse OCO order response."""
        return OrderResult(
            success=True,
            order_id=str(response.get('orderListId')),
            filled_quantity=0.0,  # OCO orders are pending initially
            filled_price=0.0,
            commission=0.0,
            raw_response=response
        )
    
    def _round_quantity(self, symbol: str, quantity: float) -> float:
        """Round quantity to appropriate precision for the symbol."""
        # This is a simplified version - in production you'd get this from exchange info
        return round(quantity, 6)
    
    def _round_price(self, symbol: str, price: float) -> float:
        """Round price to appropriate precision for the symbol."""
        # This is a simplified version - in production you'd get this from exchange info
        return round(price, 2)
