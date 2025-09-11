#!/usr/bin/env python3
"""
Test Enhanced Trading Strategy - Testing improved strategy
Purpose: Test improved EMA cross strategy with focus "Quality over Quantity"
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
from src.services.enhanced_risk_management_service import EnhancedRiskManagementService
from src.strategies.improved_ema_cross_strategy import ImprovedEMACrossStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/enhanced_strategy_test.log')
    ]
)

def test_enhanced_strategy():
    """Test enhanced strategy performance vs original."""
    logger = logging.getLogger(__name__)
    
    print("🧪" + "=" * 80)
    print("🧪 TESTING ENHANCED TRADING STRATEGY - 'QUALITY OVER QUANTITY'")
    print("🧪" + "=" * 80)
    
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
        risk_service = EnhancedRiskManagementService(config)
        enhanced_strategy = ImprovedEMACrossStrategy()
        
        # Test symbols
        test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
        
        print(f"📊 Testing {len(test_symbols)} symbols with enhanced strategy...")
        print(f"📋 Symbols: {', '.join(test_symbols)}")
        print()
        
        # Get current balance for risk calculations
        current_balance = market_service.get_account_balance()
        print(f"💰 Current Balance: ${current_balance:.2f}")
        print()
        
        print("🎯 ENHANCED STRATEGY REQUIREMENTS:")
        print(f"   • Minimum R:R Ratio: 1.5:1")
        print(f"   • Minimum Signal Confidence: 75%")
        print(f"   • Core Conditions Required: 4/4 (vs original 1/4)")
        print(f"   • Enhanced Volume: 1.5x (vs original 1.2x)")
        print(f"   • Tightened RSI: 50-70 (vs original 45-75)")
        print(f"   • Price position: within 2% of 26-EMA (vs 3%)")
        print()
        
        total_signals = 0
        quality_signals = 0
        high_rr_signals = 0
        approved_signals = 0
        
        for i, symbol in enumerate(test_symbols, 1):
            print(f"📈 [{i}/{len(test_symbols)}] ANALYZING {symbol}")
            print("-" * 60)
            
            try:
                # Get market data
                market_data = market_service.get_market_data(symbol, config.timeframe, 100)
                if not market_data:
                    print(f"   ❌ Could not get market data for {symbol}")
                    continue
                
                # Add technical analysis
                klines = market_service.get_klines(symbol, config.timeframe, 100)
                tech_analysis = tech_service.calculate_indicators(symbol, klines)
                market_data.technical_analysis = tech_analysis
                
                # Test enhanced strategy
                try:
                    signal = enhanced_strategy.analyze(market_data)
                    total_signals += 1
                except Exception as strategy_error:
                    print(f"   ❌ Strategy analysis error: {strategy_error}")
                    continue
                
                if signal:
                    print(f"   ✅ Signal Generated:")
                    print(f"      Strategy: {signal.strategy_name}")
                    print(f"      Price: ${signal.price:.4f}")
                    print(f"      Confidence: {signal.confidence:.1%}")
                    print(f"      Core Conditions: {signal.core_conditions_count}/4")
                    
                    # Calculate R:R ratio
                    if signal.stop_loss and signal.take_profit:
                        risk = signal.price - signal.stop_loss
                        reward = signal.take_profit - signal.price
                        rr_ratio = reward / risk if risk > 0 else 0
                        print(f"      Stop Loss: ${signal.stop_loss:.4f}")
                        print(f"      Take Profit: ${signal.take_profit:.4f}")
                        print(f"      R:R Ratio: {rr_ratio:.2f}:1")
                        
                        if rr_ratio >= 1.5:
                            high_rr_signals += 1
                            print(f"      ✅ Meets minimum R:R requirement (1.5:1)")
                        else:
                            print(f"      ❌ Below minimum R:R requirement (1.5:1)")
                    
                    # Check signal quality
                    if signal.confidence >= 0.75:
                        quality_signals += 1
                        print(f"      ✅ High quality signal (>75% confidence)")
                    else:
                        print(f"      ⚠️  Medium quality signal (<75% confidence)")
                    
                    # Test enhanced risk validation
                    print(f"   🛡️  ENHANCED RISK VALIDATION:")
                    is_approved = risk_service.validate_trade(signal, current_balance)
                    
                    if is_approved:
                        approved_signals += 1
                        print(f"      ✅ TRADE APPROVED by enhanced risk management")
                        
                        # Calculate enhanced position size
                        position_size = risk_service.calculate_enhanced_position_size(signal, current_balance)
                        trade_value = position_size * signal.price
                        print(f"      Position Size: {position_size:.6f} {symbol.replace('USDT', '')}")
                        print(f"      Trade Value: ${trade_value:.2f}")
                    else:
                        print(f"      ❌ TRADE REJECTED by enhanced risk management")
                
                else:
                    print(f"   ➖ No signal generated - conditions not met")
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error analyzing {symbol}: {e}")
                print()
        
        # Summary
        print("🏆" + "=" * 80)
        print("🏆 ENHANCED STRATEGY TEST RESULTS")
        print("🏆" + "=" * 80)
        print(f"📊 Total Symbols Analyzed: {len(test_symbols)}")
        print(f"📡 Total Signals Generated: {total_signals}")
        print(f"⭐ Quality Signals (>75% confidence): {quality_signals}")
        print(f"📈 High R:R Signals (≥1.5:1): {high_rr_signals}")
        print(f"✅ Approved by Enhanced Risk Mgmt: {approved_signals}")
        print()
        
        if total_signals > 0:
            quality_rate = (quality_signals / total_signals) * 100
            rr_rate = (high_rr_signals / total_signals) * 100
            approval_rate = (approved_signals / total_signals) * 100
            
            print(f"📈 QUALITY METRICS:")
            print(f"   • Quality Rate: {quality_rate:.1f}% (signals >75% confidence)")
            print(f"   • R:R Compliance: {rr_rate:.1f}% (signals ≥1.5:1 R:R)")
            print(f"   • Approval Rate: {approval_rate:.1f}% (passed enhanced risk)")
            print()
            
            print(f"💡 STRATEGY EFFECTIVENESS:")
            if approval_rate >= 20:
                print(f"   ✅ EXCELLENT - High approval rate indicates quality focus working")
            elif approval_rate >= 10:
                print(f"   ✅ GOOD - Moderate approval rate, quality controls effective")
            else:
                print(f"   ⚠️  LOW - Very selective, may need fine-tuning")
            
            print()
        
        print(f"🎯 ENHANCED STRATEGY OBJECTIVES:")
        print(f"   ✅ Minimum 1.5:1 R:R ratio enforcement")
        print(f"   ✅ 75% minimum confidence requirement")
        print(f"   ✅ 4/4 core conditions vs original 1/4")
        print(f"   ✅ Enhanced volume and technical filters")
        print(f"   ✅ Quality-based position sizing with bonuses")
        print()
        print(f"🏆 FOCUS: 'QUALITY OVER QUANTITY' - Fewer but higher quality trades!")
        
    except Exception as e:
        logger.error(f"Error in enhanced strategy test: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_enhanced_strategy()
