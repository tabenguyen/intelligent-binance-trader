#!/usr/bin/env python3
"""
Simple Enhanced Strategy Test - Debug version
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import load_config
from src.services.market_data_service import BinanceMarketDataService
from src.services.technical_analysis_service import TechnicalAnalysisService
from src.strategies.ema_cross_strategy import EMACrossStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_simple_strategy():
    """Test the original strategy to compare."""
    logger = logging.getLogger(__name__)
    
    print("🔍" + "=" * 80)
    print("🔍 TESTING ORIGINAL STRATEGY FOR COMPARISON")
    print("🔍" + "=" * 80)
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize services
        market_service = BinanceMarketDataService(
            api_key=config.api_key,
            api_secret=config.api_secret,
            testnet=config.testnet
        )
        
        tech_service = TechnicalAnalysisService()
        original_strategy = EMACrossStrategy()
        
        # Test one symbol
        symbol = "BTCUSDT"
        
        print(f"📊 Testing {symbol} with original strategy...")
        
        # Get market data
        market_data = market_service.get_market_data(symbol, config.timeframe, 100)
        if not market_data:
            print(f"❌ Could not get market data for {symbol}")
            return
        
        # Add technical analysis
        klines = market_service.get_klines(symbol, config.timeframe, 100)
        tech_analysis = tech_service.calculate_indicators(symbol, klines)
        market_data.technical_analysis = tech_analysis
        
        print(f"✅ Technical Analysis Available:")
        indicators = tech_analysis.indicators
        for key, value in indicators.items():
            print(f"   • {key}: {value}")
        
        print()
        print(f"📈 Current Price: ${market_data.current_price:.4f}")
        
        # Test original strategy
        signal = original_strategy.analyze(market_data)
        
        if signal:
            print(f"✅ Original Strategy Generated Signal:")
            print(f"   Strategy: {signal.strategy_name}")
            print(f"   Price: ${signal.price:.4f}")
            print(f"   Confidence: {signal.confidence:.1%}")
            print(f"   Core Conditions: {signal.core_conditions_count}/4")
            if signal.stop_loss:
                print(f"   Stop Loss: ${signal.stop_loss:.4f}")
            if signal.take_profit:
                print(f"   Take Profit: ${signal.take_profit:.4f}")
        else:
            print(f"➖ Original Strategy: No signal generated")
        
    except Exception as e:
        logger.error(f"Error in simple strategy test: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_simple_strategy()
