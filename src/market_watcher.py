"""
MarketWatcher - fetches top movers from Binance and updates watchlist.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from pathlib import Path
import numpy as np

from binance.spot import Spot
from binance.error import ClientError

from .models import TradingConfig


class MarketWatcher:
    """Fetch top 24h movers and update watchlist file using simplified 2-criteria analysis.
    
    SIMPLIFIED APPROACH:
    - Uses 2-criteria system: Relative Strength vs BTC (50%) + Trend Strength ADX (50%)
    - Provides initial quality screening (75%+ composite score)
    - RiskManagement performs all risk-reward and volume validation at execution time
    - Quality thresholds: 85%+ premium, 75%+ minimum (aligned with RiskManagement standards)
    - Focus on market strength and trend quality only - execution validation handled by RiskManagement
    """

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

    def write_watchlist(self, symbols_data: List[Dict], filepath: str) -> None:
        """Write symbols data to watchlist file in JSON format with simplified 2-criteria conditions, overwrite existing."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Format watchlist with detailed conditions
        watchlist = {
            "timestamp": datetime.now().isoformat(),
            "total_symbols": len(symbols_data),
            "quote_asset": self.quote,
            "symbols": []
        }
        
        for data in symbols_data:
            symbol_info = {
                "symbol": data['symbol'],
                "current_price": data['current_price'],
                "composite_score": data['composite_score'],
                "conditions": {
                    "relative_strength_vs_btc": {
                        "value": data['relative_strength_vs_btc'],
                        "status": self._get_relative_strength_status(data['relative_strength_vs_btc']),
                        "description": "Performance relative to BTC over 7 days (%)"
                    },
                    "trend_strength_adx": {
                        "value": data['trend_strength_adx'],
                        "status": self._get_adx_status(data['trend_strength_adx']),
                        "description": "Average Directional Index - trend strength (0-100)"
                    }
                }
            }
            watchlist["symbols"].append(symbol_info)
        
        # Write JSON to file
        with open(path, 'w') as f:
            json.dump(watchlist, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Updated JSON watchlist with {len(symbols_data)} symbols (2-criteria analysis) at {filepath}")



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
            
            btc_start = float(btc_klines[0][4])
            btc_end = float(btc_klines[-1][4])
            
            if symbol_start <= 0 or btc_start <= 0:
                return None
                
            symbol_change = (symbol_end - symbol_start) / symbol_start * 100
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



    def get_ranked_symbols(self, symbols: List[str]) -> List[Dict]:
        """Rank symbols based on simplified 2-criteria system and return sorted list."""
        ranked_symbols = []
        
        self.logger.info(f"Analyzing {len(symbols)} symbols with 2-criteria ranking...")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                self.logger.info(f"Analyzing {symbol} ({i}/{len(symbols)})...")
                
                # Get current price
                ticker = self.client.ticker_price(symbol)
                current_price = float(ticker['price'])
                
                # Calculate simplified 2 criteria only
                rel_strength = self.calculate_relative_strength_vs_btc(symbol)
                adx = self.calculate_trend_strength_adx(symbol)
                
                # Calculate composite score with simplified criteria
                score = self._calculate_composite_score(rel_strength, adx)
                
                symbol_data = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'relative_strength_vs_btc': rel_strength,
                    'trend_strength_adx': adx,
                    'composite_score': score
                }
                
                ranked_symbols.append(symbol_data)
                
                # Fixed string formatting for simplified criteria
                rel_str = f"{rel_strength:.2f}" if rel_strength is not None else "N/A"
                adx_str = f"{adx:.2f}" if adx is not None else "N/A"
                
                self.logger.info(f"  RelStr={rel_str}%, "
                               f"ADX={adx_str}, "
                               f"Score={score:.2f}")
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze {symbol}: {e}")
                continue
        
        # Sort by composite score (descending - higher is better)
        ranked_symbols.sort(key=lambda x: x['composite_score'], reverse=True)
        
        self.logger.info("="*60)
        self.logger.info("🏆 TOP RANKED SYMBOLS BY 2-CRITERIA ANALYSIS")
        self.logger.info("="*60)
        
        # Show statistics
        if ranked_symbols:
            scores = [data['composite_score'] for data in ranked_symbols]
            avg_score = sum(scores) / len(scores)
            
            self.logger.info(f"📊 Analysis Summary (aligned with RiskManagement standards):")
            self.logger.info(f"   Total analyzed: {len(ranked_symbols)}")
            self.logger.info(f"   Average score: {avg_score:.2f}")
            self.logger.info(f"   Premium quality (≥85): {len([s for s in scores if s >= 85])}")
            self.logger.info(f"   Minimum quality (≥75): {len([s for s in scores if s >= 75])}")
            self.logger.info("-"*60)
        
        for i, data in enumerate(ranked_symbols[:10], 1):  # Show top 10
            # Aligned with RiskManagement: 85%+ premium, 75%+ minimum
            quality_indicator = "🌟" if data['composite_score'] >= 85 else "⭐" if data['composite_score'] >= 75 else "💫"
            self.logger.info(f"{i:2d}. {quality_indicator} {data['symbol']:<12} - Score: {data['composite_score']:6.2f}")
            
            # Fixed string formatting for the simplified detailed view
            rel_display = f"{data['relative_strength_vs_btc']:>6.2f}" if data['relative_strength_vs_btc'] is not None else "   N/A"
            adx_display = f"{data['trend_strength_adx']:>6.2f}" if data['trend_strength_adx'] is not None else "   N/A"
            
            self.logger.info(f"     RelStr: {rel_display}%, "
                           f"ADX: {adx_display}")
        
        return ranked_symbols

    def _calculate_composite_score(self, rel_strength: Optional[float], adx: Optional[float]) -> float:
        """Calculate weighted composite score using simplified 2-criteria system.
        
        SIMPLIFIED APPROACH:
        - Focuses on market strength and trend quality only
        - 50/50 weighting between relative strength vs BTC and trend strength (ADX)
        - Minimum score 75.0 still matches RiskManagement 75% confidence requirement
        - RiskManagement service handles all risk-reward and volume validation at execution time
        """
        score = 0.0
        
        # Simplified weights for 2-criteria system
        weights = {
            'rel_strength': 0.50,   # 50% - Market strength relative to BTC
            'adx': 0.50            # 50% - Trend strength indicator
        }
        
        # Relative Strength vs BTC (normalized to 0-100)
        if rel_strength is not None:
            # Positive relative strength gets higher score
            rel_score = max(0, min(rel_strength * 2 + 50, 100))  # Scale and shift
            score += rel_score * weights['rel_strength']
        
        # ADX Trend Strength (0-100 scale)
        if adx is not None and adx > 0:
            adx_score = min(adx * 2, 100)  # Scale ADX, cap at 100
            score += adx_score * weights['adx']
        
        return score



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
            # Prevent division by zero warnings
            atr_safe = np.where(atr > 1e-10, atr, 1e-10)
            plus_di = 100 * self._ema(plus_dm, period) / atr_safe
            minus_di = 100 * self._ema(minus_dm, period) / atr_safe
            
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



    def _get_relative_strength_status(self, rel_strength: Optional[float]) -> str:
        """Get relative strength vs BTC status description."""
        if rel_strength is None:
            return "Unknown"
        elif rel_strength >= 10.0:
            return "Very Strong"
        elif rel_strength >= 5.0:
            return "Strong"
        elif rel_strength >= 0.0:
            return "Positive"
        elif rel_strength >= -5.0:
            return "Weak"
        else:
            return "Very Weak"

    def _get_adx_status(self, adx: Optional[float]) -> str:
        """Get ADX trend strength status description."""
        if adx is None:
            return "Unknown"
        elif adx >= 50:
            return "Very Strong Trend"
        elif adx >= 25:
            return "Strong Trend"
        elif adx >= 15:
            return "Weak Trend"
        else:
            return "No Trend"



    def get_top_movers_with_ranking(self, limit: int = 20, min_score: float = 75.0) -> List[Dict]:
        """Get top movers and apply simplified 2-criteria ranking, filtering by quality."""
        # First get top volume movers as candidates
        candidates = self.get_top_movers(limit * 3)  # Get more candidates for better filtering
        
        if not candidates:
            return []
        
        # Apply simplified 2-criteria ranking
        ranked_symbols = self.get_ranked_symbols(candidates)
        
        # Filter by minimum score - only return good opportunities
        good_opportunities = [
            symbol_data for symbol_data in ranked_symbols 
            if symbol_data['composite_score'] >= min_score
        ]
        
        self.logger.info(f"Found {len(good_opportunities)} good opportunities out of {len(ranked_symbols)} analyzed symbols")
        self.logger.info(f"Quality filter: minimum score {min_score}")
        
        # Return good opportunities, respecting limit as maximum but not minimum
        return good_opportunities[:limit] if len(good_opportunities) > limit else good_opportunities


def update_watchlist_with_ranking(limit: int = 20, min_score: float = 75.0, config: Optional['TradingConfig'] = None) -> Optional[List[Dict]]:
    """Helper to update watchlist using simplified 2-criteria ranking system with quality filtering."""
    try:
        if config is None:
            config = TradingConfig.from_env()
        
        watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet, quote="USDT")
        top_ranked = watcher.get_top_movers_with_ranking(limit=limit, min_score=min_score)
        
        if not top_ranked:
            logging.getLogger(__name__).info(f"No coins found meeting minimum quality score of {min_score}")
            return None
        
        watcher.write_watchlist(top_ranked, config.get_mode_specific_watchlist_file())
        
        # Log summary of selected opportunities
        avg_score = sum(coin['composite_score'] for coin in top_ranked) / len(top_ranked)
        logging.getLogger(__name__).info(f"Selected {len(top_ranked)} quality opportunities (avg score: {avg_score:.2f})")
        
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


def update_watchlist_from_top_movers(limit: int = 20, min_score: float = 75.0, config: Optional['TradingConfig'] = None) -> Optional[List[Dict]]:
    """
    Helper to load config, fetch top movers with ranking, and update watchlist file.
    
    Args:
        limit: Maximum number of coins to include (not a hard requirement)
        min_score: Minimum composite score required (default 75.0 to align with RiskManagement 75% confidence)
        config: Optional trading configuration
        
    Returns:
        List of selected coin data with analysis, or None if none meet criteria
    """
    return update_watchlist_with_ranking(limit, min_score, config)


def get_quality_opportunities(min_score: float = 60.0, max_candidates: int = 100, config: Optional['TradingConfig'] = None) -> Optional[List[Dict]]:
    """
    Get all coins that meet quality criteria without hard limits.
    
    Args:
        min_score: Minimum composite score required (default 60.0 for higher quality)
        max_candidates: Maximum candidates to analyze (to prevent excessive API calls)
        config: Optional trading configuration
        
    Returns:
        List of all coins meeting quality criteria, sorted by score
    """
    try:
        if config is None:
            config = TradingConfig.from_env()
        
        watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet, quote="USDT")
        
        # Get a larger pool of candidates
        candidates = watcher.get_top_movers(max_candidates)
        if not candidates:
            return None
        
        # Apply simplified 2-criteria ranking to all candidates
        ranked_symbols = watcher.get_ranked_symbols(candidates)
        
        # Filter by quality - no hard limit, only quality threshold
        quality_opportunities = [
            symbol_data for symbol_data in ranked_symbols 
            if symbol_data['composite_score'] >= min_score
        ]
        
        logger = logging.getLogger(__name__)
        if quality_opportunities:
            avg_score = sum(coin['composite_score'] for coin in quality_opportunities) / len(quality_opportunities)
            logger.info(f"Found {len(quality_opportunities)} quality opportunities (min score: {min_score}, avg: {avg_score:.2f})")
            
            # Log top opportunities
            for i, coin in enumerate(quality_opportunities[:5], 1):
                logger.info(f"  {i}. {coin['symbol']} - Score: {coin['composite_score']:.2f}")
        else:
            logger.info(f"No opportunities found meeting minimum quality score of {min_score}")
        
        return quality_opportunities
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Quality opportunities search failed: {e}")
        return None


def update_watchlist_with_quality_filter(min_score: float = 75.0, config: Optional['TradingConfig'] = None) -> Optional[List[Dict]]:
    """
    Update watchlist with all coins meeting quality criteria (no hard limit).
    
    Args:
        min_score: Minimum composite score required for inclusion
        config: Optional trading configuration
        
    Returns:
        List of selected quality coins or None if none found
    """
    try:
        quality_opportunities = get_quality_opportunities(min_score=min_score, config=config)
        
        if not quality_opportunities:
            return None
        
        if config is None:
            config = TradingConfig.from_env()
            
        watcher = MarketWatcher(config.api_key, config.api_secret, config.testnet, quote="USDT")
        watcher.write_watchlist(quality_opportunities, config.get_mode_specific_watchlist_file())
        
        logger = logging.getLogger(__name__)
        logger.info(f"Updated watchlist with {len(quality_opportunities)} quality opportunities")
        
        return quality_opportunities
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Quality watchlist update failed: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Default to quality-based selection using simplified 2-criteria system
    # Aligned with RiskManagement 75% confidence requirement
    symbols = update_watchlist_from_top_movers(limit=50, min_score=75.0)
    
    if symbols:
        print(f"Top {len(symbols)} quality opportunities written to watchlist:")
        for i, s in enumerate(symbols[:10], 1):  # Show top 10
            if isinstance(s, dict):
                print(f"{i:2d}. {s['symbol']:<12} - Score: {s['composite_score']:6.2f}")
            else:
                print(f"{i:2d}. {s}")
        
        if len(symbols) > 10:
            print(f"... and {len(symbols) - 10} more quality opportunities")
    else:
        print("No quality opportunities found meeting the criteria")
