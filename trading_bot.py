#
# Automated Trading Scanner & Executor
#
# -------------------------------------------------------------------------------------
# CRITICAL SECURITY & RISK WARNING:
# 1. This script is designed to execute REAL TRADES and will handle REAL MONEY.
#    Use it at your own risk.
# 2. It requires a Binance API Key and Secret with "Enable Spot & Margin Trading"
#    permissions. DO NOT enable withdrawals for this key.
# 3. For maximum security, restrict your API key to your IP address on the Binance website.
# 4. NEVER share your API keys or hardcode them in this file. Use environment
#    variables as shown.
# 5. This version trades AUTOMATICALLY without confirmation. It will only trade if
#    your USDT balance is above the MIN_USDT_BALANCE threshold.
# -------------------------------------------------------------------------------------
#
# How to Run:
# 1. Make sure you have the 'watchlist.txt' file in the same directory.
# 2. Copy '.env.example' to '.env' and fill in your API keys:
#    - For testnet keys, get them from: https://testnet.binance.vision/
#    - For live trading keys, get them from: https://www.binance.com/
# 3. Install required libraries: uv sync
# 4. Run the script: uv run python trading_bot.py
#

import os
import time
import math
import logging
import pandas as pd
import pandas_ta as ta
import json
from binance.spot import Spot as Client
from binance.error import ClientError
from dotenv import load_dotenv
from strategies import EMACrossStrategy

# Load environment variables from .env file
load_dotenv()

# --- Environment Configuration ---
# Set to True to use the Binance Spot Testnet, False for the live market.
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() in ("true", "1", "yes")

# --- Trade Configuration ---
# Amount in USDT to spend on each trade.
TRADE_AMOUNT_USDT = float(os.getenv("TRADE_AMOUNT_USDT", "15.0"))
# Desired Risk-to-Reward ratio for Take-Profit calculation. (e.g., 1.5 means you aim to win 1.5x what you risk)
RISK_REWARD_RATIO = float(os.getenv("RISK_REWARD_RATIO", "1.5"))
# --- NEW: Balance Safety Check ---
# The bot will only place trades if your free USDT balance is above this amount.
MIN_USDT_BALANCE = float(os.getenv("MIN_USDT_BALANCE", "100.0"))

# --- API Configuration ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Active Trades Tracking ---
# Dictionary to track active OCO orders by symbol
active_trades = {}
ACTIVE_TRADES_FILE = 'active_trades.txt'


def save_active_trades():
    """Save active trades dictionary to file."""
    try:
        with open(ACTIVE_TRADES_FILE, 'w') as f:
            json.dump(active_trades, f, indent=2)
        logging.debug(f"Active trades saved to {ACTIVE_TRADES_FILE}")
    except Exception as e:
        logging.error(f"Error saving active trades: {e}")


def load_active_trades():
    """Load active trades dictionary from file."""
    global active_trades
    try:
        if os.path.exists(ACTIVE_TRADES_FILE):
            with open(ACTIVE_TRADES_FILE, 'r') as f:
                loaded_trades = json.load(f)
                active_trades.update(loaded_trades)
            logging.info(
                f"Loaded {len(active_trades)} active trades from {ACTIVE_TRADES_FILE}")
            if active_trades:
                symbols = list(active_trades.keys())
                logging.info(f"Active symbols: {', '.join(symbols)}")
        else:
            logging.info(
                f"No existing {ACTIVE_TRADES_FILE} found, starting fresh")
    except Exception as e:
        logging.error(f"Error loading active trades: {e}")
        logging.info("Starting with empty active trades")


def clear_active_trades_file():
    """Clear the active trades file when all trades are completed."""
    try:
        if os.path.exists(ACTIVE_TRADES_FILE):
            os.remove(ACTIVE_TRADES_FILE)
            logging.info(
                f"Cleared {ACTIVE_TRADES_FILE} - no active trades remaining")
    except Exception as e:
        logging.error(f"Error clearing active trades file: {e}")


# Load active trades on module import
load_active_trades()

# Initialize trading strategy
trading_strategy = EMACrossStrategy()

# ======================================================================================
# SECTION 1: DATA FETCHING AND ANALYSIS
# ======================================================================================


def get_binance_data(client, symbol, interval='15m', limit=100):
    """Fetches historical Kline data from Binance."""
    try:
        klines = client.klines(symbol=symbol, interval=interval, limit=limit)
        columns = [
            'Open_Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_Time',
            'Quote_Asset_Volume', 'Number_of_Trades', 'Taker_Buy_Base_Asset_Volume',
            'Taker_Buy_Quote_Asset_Volume', 'Ignore'
        ]
        df = pd.DataFrame(klines, columns=columns)
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])
        return df
    except ClientError as e:
        # Testnet often doesn't have data for all pairs, this is a common error.
        if USE_TESTNET and e.error_code == -1121:
            logging.warning(
                f"[{symbol}] Invalid symbol on Testnet or no data available. Skipping.")
        else:
            logging.error(f"[{symbol}] Error fetching k-line data: {e}")
        return None


def analyze_data(df, swing_period=50):
    """Calculates indicators and price action data."""
    if df is None or len(df) < swing_period:
        return None

    df.ta.ema(length=9, append=True, col_names=('EMA_9',))
    df.ta.ema(length=21, append=True, col_names=('EMA_21',))
    df.ta.ema(length=50, append=True, col_names=('EMA_50',))
    df.ta.rsi(length=14, append=True, col_names=('RSI_14',))

    latest = df.iloc[-1]
    recent_swing_df = df.tail(swing_period)

    analysis = {
        '9_EMA': latest['EMA_9'],
        '21_EMA': latest['EMA_21'],
        '50_EMA': latest['EMA_50'],
        'RSI_14': latest['RSI_14'],
        'Last_Swing_High': recent_swing_df['High'].max(),
        'Last_Swing_Low': recent_swing_df['Low'].min()
    }
    return analysis

# ======================================================================================
# SECTION 2: DECISION MAKING LOGIC
# ======================================================================================

# The check_buy_signal function has been moved to strategies/ema_cross_strategy.py
# and is now accessed through the trading_strategy object initialized above.

# ======================================================================================
# SECTION 3: ACCOUNT & TRADE EXECUTION
# ======================================================================================


def get_usdt_balance(client):
    """Fetches the free USDT balance from the account."""
    try:
        account_info = client.account()
        for balance in account_info['balances']:
            if balance['asset'] == 'USDT':
                return float(balance['free'])
        return 0.0
    except ClientError as e:
        logging.error(f"Error fetching USDT balance: {e}")
        return 0.0
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while fetching balance: {e}")
        return 0.0


def get_symbol_balance(client, symbol):
    """Fetches the balance for a specific symbol (base asset)."""
    try:
        # Extract base asset from symbol (e.g., BTC from BTCUSDT)
        base_asset = symbol.replace('USDT', '').replace(
            'BUSD', '').replace('BNB', '')

        account_info = client.account()
        for balance in account_info['balances']:
            if balance['asset'] == base_asset:
                return float(balance['free'])
        return 0.0
    except ClientError as e:
        logging.error(f"Error fetching {symbol} balance: {e}")
        return 0.0
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while fetching {symbol} balance: {e}")
        return 0.0


def get_executed_quantity_from_order(buy_order):
    """Extract the actual executed quantity from a market buy order."""
    try:
        if 'fills' in buy_order and buy_order['fills']:
            # Sum up all fill quantities for the order
            total_executed = 0.0
            for fill in buy_order['fills']:
                total_executed += float(fill['qty'])
            return total_executed
        elif 'executedQty' in buy_order:
            return float(buy_order['executedQty'])
        else:
            logging.warning(
                "Could not determine executed quantity from order response")
            return None
    except Exception as e:
        logging.error(f"Error extracting executed quantity: {e}")
        return None


def wait_for_balance_update(client, symbol, expected_quantity, max_attempts=10, delay=3):
    """Wait for the symbol balance to be updated after a buy order."""
    base_asset = symbol.replace('USDT', '').replace(
        'BUSD', '').replace('BNB', '')

    for attempt in range(max_attempts):
        current_balance = get_symbol_balance(client, symbol)

        # Check if we have at least the expected quantity (with more conservative tolerance for fees/rounding)
        # Use 95% tolerance to account for trading fees and rounding
        if current_balance >= (expected_quantity * 0.95):
            logging.info(
                f"[{symbol}] Balance verified: {current_balance:.6f} {base_asset} (expected: {expected_quantity:.6f})")
            return True, current_balance

        if attempt < max_attempts - 1:  # Don't sleep on the last attempt
            logging.info(f"[{symbol}] Balance not updated yet (attempt {attempt + 1}/{max_attempts}). "
                         f"Current: {current_balance:.6f}, Expected: {expected_quantity:.6f}. Waiting {delay}s...")
            time.sleep(delay)

    logging.warning(f"[{symbol}] Balance not updated after {max_attempts} attempts. "
                    f"Current: {current_balance:.6f}, Expected: {expected_quantity:.6f}")
    return False, current_balance


def check_active_trades_status(client):
    """Check status of active OCO orders and remove completed ones."""
    global active_trades
    completed_trades = []

    for symbol, order_list_id in active_trades.items():
        try:
            # Check OCO order status
            oco_status = client.get_oco_order(orderListId=order_list_id)
            order_list_status = oco_status['listOrderStatus']

            if order_list_status in ['ALL_DONE', 'REJECT']:
                # OCO order is completed (either profit taken or stop loss hit)
                logging.info(
                    f"[{symbol}] OCO order completed with status: {order_list_status}")
                completed_trades.append(symbol)
            elif order_list_status == 'EXECUTING':
                # Still active, keep monitoring
                logging.debug(
                    f"[{symbol}] OCO order still active (ID: {order_list_id})")

        except ClientError as e:
            if e.error_code == -2013:  # Order does not exist
                logging.info(
                    f"[{symbol}] OCO order no longer exists, marking as completed")
                completed_trades.append(symbol)
            else:
                logging.error(f"[{symbol}] Error checking OCO status: {e}")
        except Exception as e:
            logging.error(
                f"[{symbol}] Unexpected error checking OCO status: {e}")

    # Remove completed trades from active tracking
    if completed_trades:
        for symbol in completed_trades:
            del active_trades[symbol]
            logging.info(f"[{symbol}] Removed from active trades tracking")

        # Save updated active trades to file
        if active_trades:
            save_active_trades()
        else:
            clear_active_trades_file()


def validate_trade_amount(client, symbol, trade_amount_usdt, current_price):
    """Validate if the trade amount meets minimum notional requirements."""
    try:
        filters = get_symbol_filters(client, symbol)
        if not filters:
            return False, "Could not get symbol filters"

        min_notional = get_min_notional(filters)
        quantity = trade_amount_usdt / current_price
        trade_value = quantity * current_price

        if trade_value < min_notional:
            return False, f"Trade value ${trade_value:.2f} below minimum notional ${min_notional:.2f}"

        return True, f"Trade value ${trade_value:.2f} meets minimum notional ${min_notional:.2f}"
    except Exception as e:
        return False, f"Error validating trade amount: {e}"


def is_symbol_actively_trading(symbol):
    """Check if a symbol currently has an active OCO order."""
    return symbol in active_trades


def get_symbol_filters(client, symbol):
    """Fetches exchange information to get order filters like tickSize and stepSize."""
    try:
        exchange_info = client.exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                return s['filters']
    except ClientError as e:
        logging.error(f"[{symbol}] Error fetching exchange info: {e}")
    return None


def get_min_notional(filters):
    """Extract minimum notional value from symbol filters."""
    for f in filters:
        if f['filterType'] == 'NOTIONAL':
            return float(f['minNotional'])
        elif f['filterType'] == 'MIN_NOTIONAL':
            return float(f['minNotional'])
    return 10.0  # Default fallback for most Binance symbols


def format_value_safe(value, filters, filter_type, key, round_down=False):
    """Generic function to format price or quantity based on symbol filters.

    Args:
        value: The value to format
        filters: Exchange filters
        filter_type: Type of filter (e.g., 'LOT_SIZE', 'PRICE_FILTER')
        key: Key to extract from filter (e.g., 'stepSize', 'tickSize')
        round_down: If True, always round down instead of using standard rounding
    """
    size = None
    for f in filters:
        if f['filterType'] == filter_type:
            size = float(f[key])
            break

    if size is not None and size > 0:
        if round_down:
            # Always round down for quantities to ensure we never exceed balance
            import math
            precision = int(round(-math.log(size, 10), 0))
            factor = 10 ** precision
            rounded_value = math.floor(value * factor) / factor
            return f"{rounded_value:.{precision}f}"
        else:
            # Standard rounding for prices
            precision = int(round(-math.log(size, 10), 0))
            return f"{value:.{precision}f}"
    return str(value)


def format_value(value, filters, filter_type, key):
    """Generic function to format price or quantity based on symbol filters."""
    size = None
    for f in filters:
        if f['filterType'] == filter_type:
            size = float(f[key])
            break
    if size is not None and size > 0:
        precision = int(round(-math.log(size, 10), 0))
        return f"{value:.{precision}f}"
    return str(value)


def execute_oco_trade(client, symbol, quantity, entry_price, stop_loss, take_profit):
    """Places a market buy order and then an OCO sell order."""
    global active_trades

    try:
        filters = get_symbol_filters(client, symbol)
        if not filters:
            logging.error(f"[{symbol}] Could not get symbol filters")
            return

        # Get minimum notional value requirement
        min_notional = get_min_notional(filters)
        trade_value = quantity * entry_price

        # Check if trade value meets minimum notional requirement
        if trade_value < min_notional:
            # Adjust quantity to meet minimum notional with 5% buffer
            required_quantity = (min_notional * 1.05) / entry_price
            logging.warning(
                f"[{symbol}] Trade value ${trade_value:.2f} below minimum notional ${min_notional:.2f}")
            logging.info(
                f"[{symbol}] Adjusting quantity from {quantity:.6f} to {required_quantity:.6f}")
            quantity = required_quantity
            trade_value = quantity * entry_price

        # Format all values according to the symbol's specific rules
        formatted_quantity = format_value(
            quantity, filters, 'LOT_SIZE', 'stepSize')
        formatted_profit_price = format_value(
            take_profit, filters, 'PRICE_FILTER', 'tickSize')
        formatted_stop_price = format_value(
            stop_loss, filters, 'PRICE_FILTER', 'tickSize')
        stop_limit_price = format_value(
            stop_loss * 0.999, filters, 'PRICE_FILTER', 'tickSize')  # 0.1% below trigger

        # Final validation - ensure the formatted values still meet notional requirements
        final_trade_value = float(formatted_quantity) * entry_price
        if final_trade_value < min_notional:
            logging.error(
                f"[{symbol}] Final trade value ${final_trade_value:.2f} still below minimum notional ${min_notional:.2f} after formatting")
            return

        logging.info(f"[{symbol}] Trade details:")
        logging.info(f"  - Quantity: {formatted_quantity}")
        logging.info(f"  - Entry Price: ${entry_price:.4f}")
        logging.info(f"  - Trade Value: ${final_trade_value:.2f}")
        logging.info(f"  - Stop Loss: ${formatted_stop_price}")
        logging.info(f"  - Take Profit: ${formatted_profit_price}")
        logging.info(f"  - Min Notional Required: ${min_notional:.2f}")

        logging.info(
            f"[{symbol}] Placing MARKET BUY order for {formatted_quantity} units.")
        buy_order = client.new_order(
            symbol=symbol, side='BUY', type='MARKET', quantity=formatted_quantity)
        logging.info(
            f"[{symbol}] MARKET BUY successful. Order ID: {buy_order['orderId']}")

        # Get the actual executed quantity from the buy order
        executed_quantity = get_executed_quantity_from_order(buy_order)
        if executed_quantity:
            logging.info(
                f"[{symbol}] Actual executed quantity: {executed_quantity:.8f}")
            expected_balance = executed_quantity
        else:
            logging.warning(
                f"[{symbol}] Using requested quantity as fallback: {formatted_quantity}")
            expected_balance = float(formatted_quantity)

        # Wait for balance to be updated before placing OCO order
        logging.info(f"[{symbol}] Verifying balance update...")
        balance_updated, actual_balance = wait_for_balance_update(
            client, symbol, expected_balance)

        if not balance_updated:
            logging.error(
                f"[{symbol}] Balance verification failed. Cannot place OCO order.")
            logging.error(
                f"[{symbol}] You may need to manually place a sell order for the purchased {symbol}")
            return

        # Use conservative quantity for OCO order - account for potential fees and rounding
        # Use 99.5% of actual balance to ensure we don't exceed available balance
        conservative_quantity = actual_balance * 0.995

        # Re-format the conservative quantity using safe rounding (always round down)
        oco_quantity_formatted = format_value_safe(
            conservative_quantity, filters, 'LOT_SIZE', 'stepSize', round_down=True)

        logging.info(f"[{symbol}] Balance check:")
        logging.info(f"  - Actual balance: {actual_balance:.8f}")
        logging.info(f"  - Original quantity: {formatted_quantity}")
        logging.info(f"  - Conservative quantity: {conservative_quantity:.8f}")
        logging.info(f"  - Final OCO quantity: {oco_quantity_formatted}")

        # Final validation before placing order
        final_oco_qty = float(oco_quantity_formatted)
        if final_oco_qty > actual_balance:
            logging.error(
                f"[{symbol}] Final OCO quantity ({final_oco_qty:.8f}) still exceeds balance ({actual_balance:.8f})")
            logging.error(
                f"[{symbol}] This should not happen with round-down formatting. Aborting OCO order.")
            return

        logging.info(
            f"[{symbol}] Placing OCO SELL order for {oco_quantity_formatted} units...")
        oco_order = client.new_oco_order(
            symbol=symbol,
            side='SELL',
            quantity=oco_quantity_formatted,
            price=formatted_profit_price,
            stopPrice=formatted_stop_price,
            stopLimitPrice=stop_limit_price,
            stopLimitTimeInForce='GTC'
        )

        # Track the active OCO order
        order_list_id = oco_order['orderListId']
        active_trades[symbol] = order_list_id

        logging.info(
            f"[{symbol}] OCO SELL order placed successfully. Order List ID: {order_list_id}")
        logging.info(
            f"[{symbol}] Added to active trades tracking. Total active trades: {len(active_trades)}")

        # Save updated active trades to file
        save_active_trades()

    except ClientError as error:
        error_msg = str(error)
        if "NOTIONAL" in error_msg:
            logging.error(
                f"[{symbol}] NOTIONAL ERROR: Trade value too small. Current trade value: ${trade_value:.2f}, Required minimum: ${min_notional:.2f}")
            logging.error(
                f"[{symbol}] Consider increasing TRADE_AMOUNT_USDT in your .env file to at least ${min_notional * 1.1:.2f}")
        else:
            logging.error(f"[{symbol}] TRADE EXECUTION FAILED: {error}")
    except Exception as e:
        logging.error(
            f"[{symbol}] An unexpected error occurred during execution: {e}")

# ======================================================================================
# SECTION 4: MAIN BOT LOOP
# ======================================================================================


def main():
    if not API_KEY or not API_SECRET:
        logging.error(
            "API Key/Secret not set. Please set environment variables.")
        return

    # --- Initialize Client based on Environment ---
    if USE_TESTNET:
        base_url = "https://testnet.binance.vision"
        logging.warning("<<<<< RUNNING IN TESTNET MODE >>>>>")
    else:
        base_url = "https://api.binance.com"
        logging.info("----- Running in LIVE mode -----")

    client = Client(API_KEY, API_SECRET, base_url=base_url)

    try:
        with open('watchlist.txt', 'r') as f:
            watchlist = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error("watchlist.txt not found. Please create it.")
        return

    logging.info(f"Starting bot... Monitoring {len(watchlist)} symbols.")

    while True:
        try:
            # Check status of active trades before starting new scan
            if active_trades:
                logging.info(
                    f"Checking status of {len(active_trades)} active trades...")
                check_active_trades_status(client)

            for symbol in watchlist:
                logging.info(f"--- Analyzing {symbol} ---")

                # Skip symbols that already have active OCO orders
                if is_symbol_actively_trading(symbol):
                    logging.info(
                        f"[{symbol}] Skipping - already has active OCO order (ID: {active_trades[symbol]})")
                    continue

                # --- BALANCE CHECK FIRST ---
                # Check balance before doing any analysis to save processing time
                logging.info(f"[{symbol}] Checking account balance...")
                usdt_balance = get_usdt_balance(client)

                if usdt_balance <= MIN_USDT_BALANCE:
                    logging.warning(
                        f"[{symbol}] USDT balance ({usdt_balance:.2f}) is below minimum ({MIN_USDT_BALANCE:.2f}). Skipping analysis.")
                    continue

                logging.info(
                    f"[{symbol}] Balance check passed: {usdt_balance:.2f} USDT available")

                df = get_binance_data(client, symbol)
                if df is None:
                    time.sleep(2)  # Wait a moment before next symbol on error
                    continue

                current_price = df['Close'].iloc[-1]
                analysis = analyze_data(df)

                if analysis and trading_strategy.check_buy_signal(symbol, analysis, current_price):
                    # A valid signal was found, prepare the trade plan
                    # Place SL slightly below the swing low
                    stop_loss = analysis['Last_Swing_Low'] * 0.998
                    risk = current_price - stop_loss
                    take_profit = current_price + (risk * RISK_REWARD_RATIO)
                    quantity_to_buy = TRADE_AMOUNT_USDT / current_price

                    # Validate trade amount meets minimum notional requirements
                    is_valid, validation_msg = validate_trade_amount(
                        client, symbol, TRADE_AMOUNT_USDT, current_price)

                    if not is_valid:
                        logging.warning(
                            f"[{symbol}] Trade validation failed: {validation_msg}")
                        logging.warning(
                            f"[{symbol}] Consider increasing TRADE_AMOUNT_USDT to at least ${get_min_notional(get_symbol_filters(client, symbol)) * 1.1:.2f}")
                        continue

                    logging.info(
                        f"[{symbol}] Trade validation passed: {validation_msg}")

                    # --- EXECUTE TRADE (Balance already verified) ---
                    logging.info(
                        f"USDT balance ({usdt_balance:.2f}) is above minimum ({MIN_USDT_BALANCE:.2f}). Executing trade.")
                    execute_oco_trade(
                        client, symbol, quantity_to_buy, current_price, stop_loss, take_profit)
                    # Wait after a trade to prevent rapid-fire trades on the same signal
                    logging.info(
                        "Trade executed. Pausing for next scan cycle.")
                    break  # Exit the for loop to start the 15min wait

                # Small delay to avoid hitting API rate limits too quickly
                time.sleep(5)

            # Log summary of scan cycle
            if active_trades:
                active_symbols = list(active_trades.keys())
                logging.info(
                    f"Scan cycle completed. Active trades: {len(active_trades)} ({', '.join(active_symbols)})")
            else:
                logging.info("Scan cycle completed. No active trades.")

            logging.info(
                f"Waiting 15 minutes before next scan...")
            time.sleep(900)  # 15 minutes
        except KeyboardInterrupt:
            print("\nExiting bot.")
            break


if __name__ == "__main__":
    main()
