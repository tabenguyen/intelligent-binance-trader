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

	def get_top_movers(self, limit: int = 20) -> List[str]:
		"""Return top symbols by 24h percentage change for the given quote (default USDT)."""
		try:
			tickers = self.client.ticker_24hr()
		except ClientError as e:
			self.logger.error(f"Failed to fetch 24h tickers: {e}")
			return []

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
		return top

	def write_watchlist(self, symbols: List[str], filepath: str) -> None:
		"""Write symbols to watchlist file, one per line, overwrite existing."""
		path = Path(filepath)
		path.parent.mkdir(parents=True, exist_ok=True)
		text = "\n".join(symbols)
		path.write_text(text)
		self.logger.info(f"Updated watchlist with {len(symbols)} symbols at {filepath}")


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
