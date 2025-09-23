"""
MarketWatcher - fetches top movers from Binance and updates watchlist.
"""

import logging
from typing import List, Optional, Dict, Tuple
from pathlib import Path
import numpy as np

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

    def calculate_risk_reward_ratio(self, symbol: str, current_price: float) -> Optional[float]:
        """Calculate Risk:Reward ratio for a symbol."""
        try:
            # Get klines for technical analysis
            klines = self.client.klines(symbol, "1h", limit=100)
            if not klines:
                return None
            
            closes = [float(k[4]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            
            # Calculate support and resistance levels
            support_level = self._find_support_level(lows, current_price)
            resistance_level = self._find_resistance_level(highs, current_price)
            
            if not support_level or not resistance_level:
                return None
            
            # Risk = distance from current price to support (stop loss)
            risk = abs(current_price - support_level)
            
            # Reward = distance from current price to resistance (take profit)
            reward = abs(resistance_level - current_price)
            
            if risk <= 0:
                return None
            
            return reward / risk
            
        except Exception as e:
            self.logger.error(f"Error calculating R:R for {symbol}: {e}")
            return None

    def calculate_relative_strength_vs_btc(self, symbol: str, days: int = 7) -> Optional[float]:
        """Calculate relative strength compared to BTC over specified days."""
        try:
            # Get data for both symbol and BTC
            limit = days * 24  # hourly data for specified days
            
            symbol_klines = self.client.klines(symbol, "1h", limit=limit)
            btc_klines = self.client.klines("BTCUSDT", "1h", limit=limit)
            
            if not symbol_klines or not btc_klines or len(symbol_klines) < limit or len(btc_klines) < limit:
                return None
            
            # Calculate percentage change over the period
            symbol_start = float(symbol_klines[0][4])  # Close price of first candle
            symbol_end = float(symbol_klines[-1][4])   # Close price of last candle
            symbol_change = (symbol_end - symbol_start) / symbol_start * 100
            
            btc_start = float(btc_klines[0][4])
            btc_end = float(btc_klines[-1][4])
            btc_change = (btc_end - btc_start) / btc_start * 100
            
            # Relative strength = symbol performance - BTC performance
            relative_strength = symbol_change - btc_change
            
            return relative_strength
            
        except Exception as e:
            self.logger.error(f"Error calculating relative strength for {symbol}: {e}")
            return None

    def calculate_trend_strength_adx(self, symbol: str) -> Optional[float]:
        """Calculate ADX (Average Directional Index) to measure trend strength."""
        try:
            klines = self.client.klines(symbol, "1h", limit=50)
            if not klines or len(klines) < 50:
                return None
            
            highs = np.array([float(k[2]) for k in klines])
            lows = np.array([float(k[3]) for k in klines])
            closes = np.array([float(k[4]) for k in klines])
            
            return self._calculate_adx(highs, lows, closes)
            
        except Exception as e:
            self.logger.error(f"Error calculating ADX for {symbol}: {e}")
            return None

    def calculate_volume_confirmation(self, symbol: str) -> Optional[float]:
        """Calculate volume confirmation ratio (recent volume vs average)."""
        try:
            klines = self.client.klines(symbol, "1h", limit=25)  # 25 hours of data
            if not klines or len(klines) < 25:
                return None
            
            volumes = [float(k[5]) for k in klines]
            
            # Recent volume (last 5 candles average)
            recent_volume = np.mean(volumes[-5:])
            
            # Average volume (previous 20 candles)
            avg_volume = np.mean(volumes[:-5])
            
            if avg_volume <= 0:
                return None
            
            # Volume ratio (how much higher recent volume is vs average)
            volume_ratio = recent_volume / avg_volume
            
            return volume_ratio
            
        except Exception as e:
            self.logger.error(f"Error calculating volume confirmation for {symbol}: {e}")
            return None

    def get_ranked_symbols(self, symbols: List[str]) -> List[Dict]:
        """Rank symbols based on 4 criteria and return sorted list."""
        ranked_symbols = []
        
        self.logger.info(f"Analyzing {len(symbols)} symbols with 4-criteria ranking...")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                self.logger.info(f"Analyzing {symbol} ({i}/{len(symbols)})...")
                
                # Get current price
                ticker = self.client.ticker_price(symbol)
                current_price = float(ticker['price'])
                
                # Calculate all 4 criteria
                rr_ratio = self.calculate_risk_reward_ratio(symbol, current_price)
                rel_strength = self.calculate_relative_strength_vs_btc(symbol)
                adx = self.calculate_trend_strength_adx(symbol)
                volume_conf = self.calculate_volume_confirmation(symbol)
                
                # Calculate composite score
                score = self._calculate_composite_score(rr_ratio, rel_strength, adx, volume_conf)
                
                symbol_data = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'risk_reward_ratio': rr_ratio,
                    'relative_strength_vs_btc': rel_strength,
                    'trend_strength_adx': adx,
                    'volume_confirmation': volume_conf,
                    'composite_score': score
                }
                
                ranked_symbols.append(symbol_data)
                
                # Fixed string formatting
                rr_str = f"{rr_ratio:.2f}" if rr_ratio is not None else "N/A"
                rel_str = f"{rel_strength:.2f}" if rel_strength is not None else "N/A"
                adx_str = f"{adx:.2f}" if adx is not None else "N/A"
                vol_str = f"{volume_conf:.2f}" if volume_conf is not None else "N/A"
                
                self.logger.info(f"  R:R={rr_str}, "
                               f"RelStr={rel_str}%, "
                               f"ADX={adx_str}, "
                               f"Vol={vol_str}x, "
                               f"Score={score:.2f}")
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze {symbol}: {e}")
                continue
        
        # Sort by composite score (descending - higher is better)
        ranked_symbols.sort(key=lambda x: x['composite_score'], reverse=True)
        
        self.logger.info("="*60)
        self.logger.info("🏆 TOP RANKED SYMBOLS BY 4-CRITERIA ANALYSIS")
        self.logger.info("="*60)
        
        for i, data in enumerate(ranked_symbols[:10], 1):  # Show top 10
            self.logger.info(f"{i:2d}. {data['symbol']:<12} - Score: {data['composite_score']:6.2f}")
            
            # Fixed string formatting for the detailed view
            rr_display = f"{data['risk_reward_ratio']:>6.2f}" if data['risk_reward_ratio'] is not None else "   N/A"
            rel_display = f"{data['relative_strength_vs_btc']:>6.2f}" if data['relative_strength_vs_btc'] is not None else "   N/A"
            adx_display = f"{data['trend_strength_adx']:>6.2f}" if data['trend_strength_adx'] is not None else "   N/A"
            vol_display = f"{data['volume_confirmation']:>6.2f}" if data['volume_confirmation'] is not None else "   N/A"
            
            self.logger.info(f"     R:R: {rr_display}, "
                           f"RelStr: {rel_display}%, "
                           f"ADX: {adx_display}, "
                           f"Vol: {vol_display}x")
        
        return ranked_symbols

    def _calculate_composite_score(self, rr_ratio: Optional[float], rel_strength: Optional[float], 
                                 adx: Optional[float], volume_conf: Optional[float]) -> float:
        """Calculate weighted composite score from 4 criteria."""
        score = 0.0
        
        # Weights for each criterion (can be adjusted)
        weights = {
            'rr_ratio': 0.4,        # 40% - Most important
            'rel_strength': 0.25,   # 25% 
            'adx': 0.2,            # 20%
            'volume_conf': 0.15     # 15%
        }
        
        # Risk:Reward Ratio (normalized to 0-100)
        if rr_ratio is not None and rr_ratio > 0:
            rr_score = min(rr_ratio * 20, 100)  # Scale R:R, cap at 100
            score += rr_score * weights['rr_ratio']
        
        # Relative Strength vs BTC (normalized to 0-100)
        if rel_strength is not None:
            # Positive relative strength gets higher score
            rel_score = max(0, min(rel_strength * 2 + 50, 100))  # Scale and shift
            score += rel_score * weights['rel_strength']
        
        # ADX Trend Strength (0-100 scale)
        if adx is not None and adx > 0:
            adx_score = min(adx * 2, 100)  # Scale ADX, cap at 100
            score += adx_score * weights['adx']
        
        # Volume Confirmation (normalized to 0-100)
        if volume_conf is not None and volume_conf > 0:
            # Volume ratio above 1.5x gets higher scores
            vol_score = min((volume_conf - 1) * 50, 100) if volume_conf > 1 else 0
            score += vol_score * weights['volume_conf']
        
        return score

    def _find_support_level(self, lows: List[float], current_price: float) -> Optional[float]:
        """Find nearest support level below current price."""
        # Simple implementation: find recent low that's below current price
        support_levels = [low for low in lows[-20:] if low < current_price * 0.98]  # 2% buffer
        return max(support_levels) if support_levels else None

    def _find_resistance_level(self, highs: List[float], current_price: float) -> Optional[float]:
        """Find nearest resistance level above current price."""
        # Simple implementation: find recent high that's above current price
        resistance_levels = [high for high in highs[-20:] if high > current_price * 1.02]  # 2% buffer
        return min(resistance_levels) if resistance_levels else None

    def _calculate_adx(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate ADX (Average Directional Index)."""
        try:
            # Calculate True Range (TR)
            tr1 = highs[1:] - lows[1:]
            tr2 = np.abs(highs[1:] - closes[:-1])
            tr3 = np.abs(lows[1:] - closes[:-1])
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            
            # Calculate Directional Movement (+DM, -DM)
            high_diff = np.diff(highs)
            low_diff = -np.diff(lows)
            
            plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
            minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
            
            # Calculate smoothed values
            atr = self._ema(tr, period)
            plus_di = 100 * self._ema(plus_dm, period) / atr
            minus_di = 100 * self._ema(minus_dm, period) / atr
            
            # Calculate ADX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
            adx = self._ema(dx, period)
            
            return float(adx[-1]) if len(adx) > 0 else None
            
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return None

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        alpha = 2.0 / (period + 1.0)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema

    def get_top_movers_with_ranking(self, limit: int = 20) -> List[str]:
        """Get top movers and apply 4-criteria ranking."""
        # First get top volume movers as candidates
        candidates = self.get_top_movers(limit * 2)  # Get more candidates for filtering
        
        if not candidates:
            return []
        
        # Apply 4-criteria ranking
        ranked_symbols = self.get_ranked_symbols(candidates)
        
        # Return top symbols by ranking
        return [data['symbol'] for data in ranked_symbols[:limit]]


def update_watchlist_with_ranking(limit: int = 20, config: Optional['TradingConfig'] = None) -> Optional[List[str]]:
    """Helper to update watchlist using 4-criteria ranking system."""
    try:
        if config is None:
            config = TradingConfig.from_env()
        
        watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet, quote="USDT")
        top_ranked = watcher.get_top_movers_with_ranking(limit=limit)
        
        if not top_ranked:
            return None
        
        watcher.write_watchlist(top_ranked, config.get_mode_specific_watchlist_file())
        return top_ranked
        
    except Exception as e:
        logging.getLogger(__name__).error(f"MarketWatcher ranking update failed: {e}")
        return None


def check_symbol_tradeable(symbol: str) -> bool:
    """Helper to check if a symbol is tradeable using current config."""
    try:
        config = TradingConfig.from_env()
        watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet)
        return watcher.is_symbol_tradeable(symbol)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to check if {symbol} is tradeable: {e}")
        return False


def update_watchlist_from_top_movers(limit: int = 20, config: Optional['TradingConfig'] = None) -> Optional[List[str]]:
    """Helper to load config, fetch top movers with ranking, and update watchlist file."""
    return update_watchlist_with_ranking(limit, config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    symbols = update_watchlist_from_top_movers(limit=20)
    if symbols:
        print("Top movers written to watchlist:")
        for s in symbols:
            print(s)
