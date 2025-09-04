"""
MarketWatcher - fetches top movers from Binance and updates watchlist.
"""

import logging
from typing import List, Optional
from pathlib import Path

from binance.spot import Spot
from binance.error import ClientError

from .models import TradingConfig


class MarketWatcher:
	"""Fetch top 24h movers and update watchlist file."""

	def __init__(self, api_key: str, api_secret: str, testnet: bool = True, quote: str = "USDT"):
		if testnet:
			self.client = Spot(api_key=api_key, api_secret=api_secret, base_url="https://testnet.binance.vision")
		else:
			self.client = Spot(api_key=api_key, api_secret=api_secret)
		self.logger = logging.getLogger(__name__)
		self.quote = quote.upper()

	def get_active_symbols(self) -> set:
		"""Get list of actively trading symbols (not closed/suspended)."""
		try:
			exchange_info = self.client.exchange_info()
			active_symbols = set()
			
			for symbol_info in exchange_info.get("symbols", []):
				symbol = symbol_info.get("symbol", "")
				status = symbol_info.get("status", "")
				
				# Only include symbols that are actively trading
				if status == "TRADING":
					active_symbols.add(symbol)
				else:
					self.logger.debug(f"Skipping {symbol} - status: {status}")
			
			self.logger.info(f"Found {len(active_symbols)} actively trading symbols")
			return active_symbols
		except ClientError as e:
			self.logger.error(f"Failed to fetch exchange info: {e}")
			return set()

	def get_top_movers(self, limit: int = 20) -> List[str]:
		"""Return top symbols by 24h percentage change for the given quote (default USDT)."""
		try:
			tickers = self.client.ticker_24hr()
		except ClientError as e:
			self.logger.error(f"Failed to fetch 24h tickers: {e}")
			return []

		# Get actively trading symbols first
		active_symbols = self.get_active_symbols()
		if not active_symbols:
			self.logger.warning("No active symbols found, proceeding without filtering")

		# Filter to quote pairs and exclude leveraged/stable tokens
		symbols = []
		exclude_bases = {"USDT", "BUSD", "USDC", "TUSD", "FDUSD", "DAI", "USD"}
		exclude_suffixes = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")

		for t in tickers:
			sym = t.get("symbol", "")
			if not sym.endswith(self.quote):
				continue
			if sym.endswith(exclude_suffixes):
				continue
			base = sym[: -len(self.quote)]
			if base in exclude_bases:
				continue
			
			# Skip symbols that are not actively trading
			if active_symbols and sym not in active_symbols:
				self.logger.debug(f"Skipping {sym} - market closed or suspended")
				continue
			
			# Keep only actively trading pairs
			symbols.append(
				{
					"symbol": sym,
					"change": float(t.get("priceChangePercent", 0.0)),
					"volume": float(t.get("quoteVolume", 0.0)),
				}
			)

		# Sort by percentage change descending, then by quote volume to break ties
		symbols.sort(key=lambda x: (x["change"], x["volume"]), reverse=True)
		top = [s["symbol"] for s in symbols[:limit]]
		self.logger.info(f"Selected {len(top)} top movers from {len(symbols)} active trading pairs")
		return top

	def is_symbol_tradeable(self, symbol: str) -> bool:
		"""Check if a specific symbol is currently tradeable."""
		try:
			exchange_info = self.client.exchange_info()
			
			for symbol_info in exchange_info.get("symbols", []):
				if symbol_info.get("symbol") == symbol:
					status = symbol_info.get("status", "")
					is_trading = status == "TRADING"
					
					if not is_trading:
						self.logger.warning(f"Symbol {symbol} is not tradeable - status: {status}")
					
					return is_trading
			
			self.logger.warning(f"Symbol {symbol} not found in exchange info")
			return False
		except ClientError as e:
			self.logger.error(f"Failed to check symbol {symbol} status: {e}")
			return False

	def write_watchlist(self, symbols: List[str], filepath: str) -> None:
		"""Write symbols to watchlist file, one per line, overwrite existing."""
		path = Path(filepath)
		path.parent.mkdir(parents=True, exist_ok=True)
		text = "\n".join(symbols)
		path.write_text(text)
		self.logger.info(f"Updated watchlist with {len(symbols)} symbols at {filepath}")


def check_symbol_tradeable(symbol: str) -> bool:
	"""Helper to check if a symbol is tradeable using current config."""
	try:
		config = TradingConfig.from_env()
		watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet)
		return watcher.is_symbol_tradeable(symbol)
	except Exception as e:
		logging.getLogger(__name__).error(f"Failed to check if {symbol} is tradeable: {e}")
		return False


def update_watchlist_from_top_movers(limit: int = 20) -> Optional[List[str]]:
	"""Helper to load config, fetch top movers, and update watchlist file."""
	try:
		config = TradingConfig.from_env()
		# Force USDT quote pairs as requested
		watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet, quote="USDT")
		top = watcher.get_top_movers(limit=limit)
		if not top:
			return None
		watcher.write_watchlist(top, config.watchlist_file)
		return top
	except Exception as e:
		logging.getLogger(__name__).error(f"MarketWatcher update failed: {e}")
		return None


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	symbols = update_watchlist_from_top_movers(limit=20)
	if symbols:
		print("Top movers written to watchlist:")
		for s in symbols:
			print(s)
