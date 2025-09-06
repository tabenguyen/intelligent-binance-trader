"""
Trade Execution Service - Single Responsibility: Execute trades on Binance.
Respects Binance symbol filters (PRICE_FILTER, LOT_SIZE, NOTIONAL) when placing orders.
"""

import logging
import math
from typing import Optional, List
from binance.spot import Spot as Client
from binance.error import ClientError

from ..core.interfaces import ITradeExecutor
from ..models.trade_models import OrderResult


class TradeExecutionService(ITradeExecutor):
    """
    Trade execution service for Binance.
    Handles all trading operations including market/limit orders and OCO orders.
    """

    def __init__(self, client: Client):
        self.client = client
        self.logger = logging.getLogger(__name__)

    def get_order_status(self, symbol: str, order_id: str) -> Optional[str]:
        """Get order status from the exchange."""
        try:
            # Convert string order_id to int for API call
            order_id_int = int(order_id) if isinstance(order_id, str) else order_id
            order = self.client.get_order(symbol=symbol, orderId=order_id_int)
            return order.get('status')
        except ClientError as e:
            self.logger.warning(f"Could not get status for order {order_id} on {symbol}: {e}")
            return None
        except ValueError as e:
            self.logger.warning(f"Invalid order ID format {order_id}: {e}")
            return None

    def get_oco_order_status(self, symbol: str, order_list_id: str) -> Optional[str]:
        """Get OCO order status from the exchange."""
        try:
            # Convert string order_list_id to int for API call
            order_list_id_int = int(order_list_id) if isinstance(order_list_id, str) else order_list_id
            oco_order = self.client.get_oco_order(symbol=symbol, orderListId=order_list_id_int)
            return oco_order.get('listOrderStatus')
        except ClientError as e:
            self.logger.warning(f"Could not get status for OCO order {order_list_id} on {symbol}: {e}")
            return None
        except ValueError as e:
            self.logger.warning(f"Invalid OCO order ID format {order_list_id}: {e}")
            return None


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
        # Cache for symbol filters to reduce API calls
        self._filters_cache = {}
    
    def execute_market_buy(self, symbol: str, quantity: float) -> OrderResult:
        """Execute a market buy order."""
        try:
            self.logger.info(f"🛒 Executing MARKET BUY order for {symbol}")
            self.logger.info(f"   Quantity: {quantity:.6f}")
            
            # Round quantity to appropriate precision and validate
            quantity = self._round_quantity(symbol, quantity)
            if quantity <= 0:
                raise ClientError(400, -1013, "Quantity too small after LOT_SIZE adjustment", {})
            
            response = self.client.new_order(
                symbol=symbol,
                side="BUY",
                type="MARKET",
                quantity=quantity
            )
            
            result = self._parse_order_response(response, True)
            if result.success:
                self.logger.info(f"✅ Market buy executed: {result.filled_quantity:.6f} {symbol} @ ${result.filled_price:.4f}")
            
            return result
            
        except ClientError as e:
            self.logger.error(f"❌ Error executing market buy for {symbol}: {e}")
            return OrderResult(
                success=False,
                order_id=None,
                filled_quantity=0.0,
                filled_price=0.0,
                commission=0.0,
                error_message=str(e)
            )
    
    def execute_limit_buy(self, symbol: str, quantity: float, price: float) -> OrderResult:
        """Execute a limit buy order."""
        try:
            self.logger.info(f"🛒 Executing LIMIT BUY order for {symbol}")
            self.logger.info(f"   Quantity: {quantity:.6f}")
            self.logger.info(f"   Limit Price: ${price:.4f}")
            
            # Round values to appropriate precision using exchange filters
            quantity = self._round_quantity(symbol, quantity)
            price = self._round_price(symbol, price)

            # Validate notional and adjust down to allowed quantities if necessary
            min_notional = self._get_min_notional_from_filters(symbol)
            notional = quantity * price
            if notional < min_notional:
                # Keep safety by not auto-increasing quantity beyond requested risk
                msg = (
                    f"Notional {notional:.8f} < minNotional {min_notional:.8f}. "
                    f"Increase trade size or price."
                )
                raise ClientError(400, -1013, msg, {})
            
            response = self.client.new_order(
                symbol=symbol,
                side="BUY",
                type="LIMIT",
                timeInForce="GTC",  # Good Till Cancelled
                quantity=quantity,
                price=price
            )
            
            result = self._parse_order_response(response, True)
            if result.success:
                self.logger.info(f"✅ Limit buy order placed: {quantity:.6f} {symbol} @ ${price:.4f} (Order ID: {result.order_id})")
            
            return result
            
        except ClientError as e:
            self.logger.error(f"❌ Error executing limit buy for {symbol}: {e}")
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
            if quantity <= 0:
                raise ClientError(400, -1013, "Quantity too small after LOT_SIZE adjustment", {})
            
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
            # Log initial OCO order parameters
            self.logger.info(f"🔧 OCO Order Request for {symbol}:")
            self.logger.info(f"   Raw Quantity: {quantity}")
            self.logger.info(f"   Raw Stop Price: ${stop_price:.8f}")
            self.logger.info(f"   Raw Limit Price: ${limit_price:.8f}")
            
            # Round values to appropriate precision
            original_quantity = quantity
            quantity = self._round_quantity(symbol, quantity)
            if quantity <= 0:
                self.logger.error(f"❌ Quantity adjustment failed: {original_quantity} → {quantity} (below minimum)")
                raise ClientError(400, -1013, "Quantity too small after LOT_SIZE adjustment", {})
            
            original_stop = stop_price
            original_limit = limit_price
            stop_price = self._round_price(symbol, stop_price)
            limit_price = self._round_price(symbol, limit_price)
            
            # Log formatted values
            self.logger.info(f"🔧 OCO Order Formatted for {symbol}:")
            self.logger.info(f"   Quantity: {original_quantity} → {quantity}")
            self.logger.info(f"   Stop Price: ${original_stop:.8f} → ${stop_price:.8f}")
            self.logger.info(f"   Limit Price: ${original_limit:.8f} → ${limit_price:.8f}")
            
            # Check account balance before placing order
            try:
                # Apply the same rounding and tolerance logic as in trading bot
                rounded_quantity = self._round_quantity(symbol, quantity)
                tolerance = max(0.001, rounded_quantity * 0.001)  # 0.1% tolerance
                required_balance = rounded_quantity - tolerance
                
                account_info = self.client.account()
                base_asset = symbol.replace('USDT', '').replace('BUSD', '').replace('BTC', '').replace('ETH', '')
                available_balance = 0.0
                
                for balance in account_info['balances']:
                    if balance['asset'] == base_asset:
                        available_balance = float(balance['free'])
                        locked_balance = float(balance['locked'])
                        
                        self.logger.info(f"💰 {base_asset} Balance Check:")
                        self.logger.info(f"   Available: {available_balance}")
                        self.logger.info(f"   Locked: {locked_balance}")
                        self.logger.info(f"   Requested: {quantity} (original)")
                        self.logger.info(f"   Rounded: {rounded_quantity}")
                        self.logger.info(f"   Tolerance: {tolerance}")
                        self.logger.info(f"   Required: {required_balance}")
                        self.logger.info(f"   Sufficient: {'✅ Yes' if available_balance >= required_balance else '❌ No'}")
                        break
                
                if available_balance < required_balance:
                    deficit = required_balance - available_balance
                    self.logger.error(f"❌ Insufficient balance detected BEFORE API call:")
                    self.logger.error(f"   Available: {available_balance} {base_asset}")
                    self.logger.error(f"   Required: {required_balance} {base_asset} (rounded: {rounded_quantity}, tolerance: {tolerance})")
                    self.logger.error(f"   Shortfall: {deficit} {base_asset}")
                    raise ClientError(400, -2010, f"Insufficient {base_asset} balance", {})
                
                # Adjust quantity if very close to available balance to avoid precision issues
                if quantity > available_balance and available_balance >= required_balance:
                    original_quantity = quantity
                    quantity = available_balance
                    self.logger.warning(f"⚠️  Adjusting OCO quantity for precision:")
                    self.logger.warning(f"   Original: {original_quantity}")
                    self.logger.warning(f"   Adjusted: {quantity}")
                    self.logger.warning(f"   Reason: Available balance slightly less than requested")
                    
            except Exception as balance_check_error:
                self.logger.warning(f"⚠️  Could not pre-verify balance: {balance_check_error}")
            
            # Log final OCO order parameters before API call
            self.logger.info(f"🚀 Executing OCO order via API...")
            
            response = self.client.new_oco_order(
                symbol=symbol,
                side="SELL",
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price,
                stopLimitPrice=stop_price,
                stopLimitTimeInForce="GTC"
            )
            
            self.logger.info(f"✅ OCO order API response received successfully")
            return self._parse_oco_response(response)
            
        except ClientError as e:
            # Enhanced error logging with detailed diagnostics
            error_code = e.error_code if hasattr(e, 'error_code') else 'Unknown'
            error_msg = str(e)
            
            self.logger.error(f"❌ OCO Order FAILED for {symbol}")
            self.logger.error(f"   Error Code: {error_code}")
            self.logger.error(f"   Error Message: {error_msg}")
            
            # Specific error code analysis and retry logic
            if error_code == -2010:
                self.logger.error(f"🔍 INSUFFICIENT BALANCE ANALYSIS:")
                self.logger.error(f"   This indicates the account doesn't have enough {symbol.replace('USDT', '')} to sell")
                self.logger.error(f"   Possible causes:")
                self.logger.error(f"   • Asset balance not yet updated after recent buy order")
                self.logger.error(f"   • Asset already locked in other orders")
                self.logger.error(f"   • Rounding/precision issues with quantity")
                
                # Attempt automatic retry with fresh balance check
                self.logger.warning(f"🔄 Attempting automatic recovery for {symbol}...")
                try:
                    import time
                    time.sleep(2)  # Wait for balance to update
                    
                    # Get fresh account balance
                    account_info = self.client.account()
                    base_asset = symbol.replace('USDT', '').replace('BUSD', '').replace('BTC', '').replace('ETH', '')
                    fresh_balance = 0.0
                    
                    for balance in account_info['balances']:
                        if balance['asset'] == base_asset:
                            fresh_balance = float(balance['free'])
                            break
                    
                    if fresh_balance > 0:
                        # Adjust quantity to available balance with small buffer
                        buffer = max(0.001, fresh_balance * 0.001)  # 0.1% buffer
                        retry_quantity = fresh_balance - buffer
                        retry_quantity = self._round_quantity(symbol, retry_quantity)
                        
                        if retry_quantity > 0:
                            self.logger.warning(f"🔄 Retrying OCO with adjusted quantity:")
                            self.logger.warning(f"   Fresh Balance: {fresh_balance}")
                            self.logger.warning(f"   Retry Quantity: {retry_quantity}")
                            
                            # Retry the OCO order with adjusted quantity
                            response = self.client.new_oco_order(
                                symbol=symbol,
                                side="SELL",
                                quantity=retry_quantity,
                                price=limit_price,
                                stopPrice=stop_price,
                                stopLimitPrice=stop_price,
                                stopLimitTimeInForce="GTC"
                            )
                            
                            self.logger.info(f"✅ OCO order retry successful!")
                            return self._parse_oco_response(response)
                        else:
                            self.logger.error(f"❌ Retry quantity too small: {retry_quantity}")
                    else:
                        self.logger.error(f"❌ No balance available for retry: {fresh_balance}")
                        
                except Exception as retry_error:
                    self.logger.error(f"❌ OCO retry failed: {retry_error}")
                
                self.logger.error(f"   💡 SUGGESTED ACTIONS:")
                self.logger.error(f"   • Wait a few seconds and retry")
                self.logger.error(f"   • Check account balance manually")
                self.logger.error(f"   • Use balance-aware OCO placement script")
                
            elif error_code == -1013:
                self.logger.error(f"🔍 FILTER FAILURE ANALYSIS:")
                self.logger.error(f"   This indicates the order doesn't meet exchange requirements")
                self.logger.error(f"   Possible causes:")
                self.logger.error(f"   • Quantity doesn't meet LOT_SIZE filter")
                self.logger.error(f"   • Price doesn't meet PRICE_FILTER requirements")
                self.logger.error(f"   • Order value below NOTIONAL minimum")
                
            elif error_code == -1102:
                self.logger.error(f"🔍 PARAMETER ERROR ANALYSIS:")
                self.logger.error(f"   Missing or malformed request parameters")
                self.logger.error(f"   Check API parameter format and requirements")
                
            else:
                self.logger.error(f"🔍 GENERAL ERROR ANALYSIS:")
                self.logger.error(f"   Unexpected error code: {error_code}")
                self.logger.error(f"   Check Binance API documentation for details")
            
            # Log recovery suggestions
            self.logger.error(f"🛠️  RECOVERY OPTIONS:")
            self.logger.error(f"   1. Run: python scripts/balance_aware_oco.py")
            self.logger.error(f"   2. Run: python scripts/check_balances.py")
            self.logger.error(f"   3. Run: python scripts/check_open_orders.py")
            self.logger.error(f"   4. Check logs above for balance verification details")
            
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
            # Convert string order_id to int for API call
            order_id_int = int(order_id) if isinstance(order_id, str) else order_id
            
            # Check current order status first
            status = self.get_order_status(symbol, order_id)
            if status is None:
                self.logger.warning(f"Order {order_id} for {symbol} not found; skipping cancel")
                return False
            if status in {"FILLED", "CANCELED", "REJECTED", "EXPIRED"}:
                self.logger.info(f"Order {order_id} for {symbol} is {status}; no cancel needed")
                return False

            # Attempt cancellation only if still active
            self.client.cancel_order(symbol=symbol, orderId=order_id_int)
            self.logger.info(f"Successfully cancelled order {order_id} for {symbol}")
            return True
        except ClientError as e:
            self.logger.error(f"Error cancelling order {order_id} for {symbol}: {e}")
            return False
        except ValueError as e:
            self.logger.warning(f"Invalid order ID format {order_id}: {e}")
            return False

    def get_order_status(self, symbol: str, order_id: str) -> Optional[str]:
        """Get current status for an order (e.g., NEW, PARTIALLY_FILLED, FILLED, CANCELED)."""
        try:
            # Convert string order_id to int for API call
            order_id_int = int(order_id) if isinstance(order_id, str) else order_id
            order = self.client.get_order(symbol=symbol, orderId=order_id_int)
            return order.get('status')
        except ClientError as e:
            self.logger.warning(f"Could not get status for order {order_id} on {symbol}: {e}")
            return None
        except ValueError as e:
            self.logger.warning(f"Invalid order ID format {order_id}: {e}")
            return None

    def get_order_details(self, symbol: str, order_id: str) -> Optional[dict]:
        """Get full order details from the exchange."""
        try:
            # Convert string order_id to int for API call
            order_id_int = int(order_id) if isinstance(order_id, str) else order_id
            return self.client.get_order(symbol=symbol, orderId=order_id_int)
        except ClientError as e:
            self.logger.warning(f"Could not get order {order_id} on {symbol}: {e}")
            return None
        except ValueError as e:
            self.logger.warning(f"Invalid order ID format {order_id}: {e}")
            return None
    
    def get_open_orders(self, symbol: str) -> List[dict]:
        """Get all open orders for a symbol."""
        try:
            return self.client.get_open_orders(symbol=symbol)
        except ClientError as e:
            self.logger.warning(f"Could not get open orders for {symbol}: {e}")
            return []
    
    def get_min_notional(self, symbol: str) -> float:
        """Get minimum notional value for a symbol (backwards-compatible)."""
        return self._get_min_notional_from_filters(symbol)
    
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
        """Round quantity to valid LOT_SIZE step and enforce min/max quantity."""
        try:
            filters = self._get_symbol_filters(symbol)
            lot = filters.get('LOT_SIZE', {})
            step = float(lot.get('stepSize', '0')) if lot else 0.0
            min_qty = float(lot.get('minQty', '0')) if lot else 0.0
            max_qty = float(lot.get('maxQty', '0')) if lot else float('inf')

            if step and step > 0:
                # Floor to the nearest step to avoid exceeding intended risk
                quantity = math.floor(quantity / step) * step
            # Enforce bounds
            if quantity < min_qty:
                # Return 0 to signal invalid (caller will handle gracefully)
                self.logger.warning(
                    f"Quantity {quantity} below minQty {min_qty} for {symbol} (step {step})"
                )
                return 0.0
            if quantity > max_qty:
                quantity = max_qty
            # Avoid negative zero-like floating quirks
            return float(f"{quantity:.12f}")
        except Exception as e:
            self.logger.warning(f"Falling back to generic quantity rounding for {symbol}: {e}")
            return round(quantity, 6)
    
    def _round_price(self, symbol: str, price: float) -> float:
        """Round price to valid PRICE_FILTER tick size."""
        try:
            filters = self._get_symbol_filters(symbol)
            pf = filters.get('PRICE_FILTER', {})
            tick = float(pf.get('tickSize', '0')) if pf else 0.0
            if tick and tick > 0:
                price = math.floor(price / tick) * tick
            return float(f"{price:.12f}")
        except Exception as e:
            self.logger.warning(f"Falling back to generic price rounding for {symbol}: {e}")
            return round(price, 2)

    # -------- Internal helpers for symbol filters --------
    def _get_symbol_filters(self, symbol: str) -> dict:
        """Return a dict mapping filterType -> filter for the given symbol, cached."""
        try:
            if symbol in self._filters_cache:
                return self._filters_cache[symbol]
            info = self.client.exchange_info()
            for s in info.get('symbols', []):
                if s.get('symbol') == symbol:
                    by_type = {f['filterType']: f for f in s.get('filters', [])}
                    self._filters_cache[symbol] = by_type
                    return by_type
            raise ValueError(f"Symbol {symbol} not found in exchange_info")
        except Exception as e:
            self.logger.warning(f"Could not load filters for {symbol}: {e}")
            return {}

    def _get_min_notional_from_filters(self, symbol: str) -> float:
        """Extract minNotional from symbol filters, supporting NOTIONAL/MIN_NOTIONAL."""
        try:
            filters = self._get_symbol_filters(symbol)
            notional = filters.get('NOTIONAL') or filters.get('MIN_NOTIONAL')
            if notional and 'minNotional' in notional:
                return float(notional['minNotional'])
            # Safe fallback used by many USDT pairs
            return 5.0
        except Exception as e:
            self.logger.warning(f"Could not get min notional for {symbol}: {e}")
            return 5.0
