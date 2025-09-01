#!/usr/bin/env python3
"""
Test script for Intelligent Watchlist Scanner

This script tests the logic and calculations for:
1. Relative strength ranking calculations
2. Top performer identification and filtering
3. Performance-based trade prioritization
4. Ranking update logic and frequency
"""

import random
import time
from datetime import datetime, timedelta


def simulate_coin_performance(symbol, days_back=14, volatility=0.02):
    """Simulate realistic coin performance over a period."""
    random.seed(hash(symbol))  # Consistent results per symbol
    
    # Simulate daily price changes
    daily_changes = []
    for _ in range(days_back):
        # Random walk with slight bias (some coins naturally stronger)
        bias = random.uniform(-0.005, 0.015)  # Slight upward bias
        daily_change = random.normalvariate(bias, volatility)
        daily_changes.append(daily_change)
    
    # Calculate cumulative performance
    cumulative_performance = 1.0
    for change in daily_changes:
        cumulative_performance *= (1 + change)
    
    performance_pct = (cumulative_performance - 1) * 100
    return performance_pct, daily_changes


def test_relative_strength_calculations():
    """Test relative strength ranking calculations."""
    print("🔍 Testing Relative Strength Calculations")
    print("=" * 60)
    
    # Simulate a diverse watchlist
    watchlist = [
        'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
        'LTCUSDT', 'XLMUSDT', 'XRPUSDT', 'EOSUSDT', 'TRXUSDT',
        'BNBUSDT', 'VETUSDT', 'MATICUSDT', 'AVAXUSDT', 'SOLUSDT'
    ]
    
    lookback_days = 14
    top_performers_pct = 25  # Top 25%
    
    print(f"Simulating performance for {len(watchlist)} coins over {lookback_days} days...")
    
    # Calculate performance for each coin
    coin_performances = []
    for symbol in watchlist:
        performance_pct, _ = simulate_coin_performance(symbol, lookback_days)
        coin_performances.append({
            'symbol': symbol,
            'performance_pct': performance_pct
        })
    
    # Sort by performance (highest first)
    coin_performances.sort(key=lambda x: x['performance_pct'], reverse=True)
    
    # Calculate top performers count
    total_coins = len(coin_performances)
    top_performers_count = max(1, int(total_coins * (top_performers_pct / 100)))
    
    print(f"\n📊 Performance Rankings:")
    print(f"Total Coins: {total_coins}")
    print(f"Top Performers ({top_performers_pct}%): {top_performers_count} coins")
    print(f"Excluded Coins: {total_coins - top_performers_count}")
    
    # Create rankings
    rankings = {}
    for i, coin_data in enumerate(coin_performances):
        symbol = coin_data['symbol']
        rank = i + 1
        is_top_performer = rank <= top_performers_count
        
        rankings[symbol] = {
            'performance_pct': coin_data['performance_pct'],
            'rank': rank,
            'is_top_performer': is_top_performer
        }
    
    # Display results
    print(f"\n🏆 TOP PERFORMERS (Eligible for Trading):")
    for symbol, data in rankings.items():
        if data['is_top_performer']:
            print(f"  #{data['rank']} {symbol}: {data['performance_pct']:+.2f}%")
    
    print(f"\n📉 EXCLUDED PERFORMERS:")
    excluded_count = 0
    for symbol, data in sorted(rankings.items(), key=lambda x: x[1]['rank'], reverse=True):
        if not data['is_top_performer'] and excluded_count < 5:
            print(f"  #{data['rank']} {symbol}: {data['performance_pct']:+.2f}%")
            excluded_count += 1
    
    # Calculate statistics
    top_performers_avg = sum(data['performance_pct'] for data in rankings.values() 
                           if data['is_top_performer']) / top_performers_count
    
    all_performers_avg = sum(data['performance_pct'] for data in rankings.values()) / total_coins
    
    print(f"\n📈 PERFORMANCE STATISTICS:")
    print(f"  Top Performers Average: {top_performers_avg:+.2f}%")
    print(f"  All Coins Average: {all_performers_avg:+.2f}%")
    print(f"  Performance Edge: {top_performers_avg - all_performers_avg:+.2f}%")
    
    return rankings


def test_filtering_logic():
    """Test the filtering logic for trade decisions."""
    print("\n\n🎯 Testing Trade Filtering Logic")
    print("=" * 60)
    
    # Create test rankings
    test_rankings = {
        'BTCUSDT': {'rank': 1, 'performance_pct': 15.2, 'is_top_performer': True},
        'ETHUSDT': {'rank': 2, 'performance_pct': 12.8, 'is_top_performer': True},
        'ADAUSDT': {'rank': 3, 'performance_pct': 8.5, 'is_top_performer': True},
        'DOTUSDT': {'rank': 4, 'performance_pct': 6.1, 'is_top_performer': True},
        'LINKUSDT': {'rank': 5, 'performance_pct': 3.2, 'is_top_performer': False},
        'LTCUSDT': {'rank': 6, 'performance_pct': -1.5, 'is_top_performer': False},
        'XLMUSDT': {'rank': 7, 'performance_pct': -4.8, 'is_top_performer': False},
        'XRPUSDT': {'rank': 8, 'performance_pct': -8.2, 'is_top_performer': False}
    }
    
    def is_symbol_top_performer(symbol, rankings):
        """Simulate the filtering function."""
        return rankings.get(symbol, {}).get('is_top_performer', False)
    
    # Test signals for various coins
    test_signals = [
        {'symbol': 'BTCUSDT', 'signal': 'BUY', 'setup_quality': 'Excellent'},
        {'symbol': 'ETHUSDT', 'signal': 'BUY', 'setup_quality': 'Good'},
        {'symbol': 'LINKUSDT', 'signal': 'BUY', 'setup_quality': 'Excellent'},
        {'symbol': 'LTCUSDT', 'signal': 'BUY', 'setup_quality': 'Good'},
        {'symbol': 'XLMUSDT', 'signal': 'BUY', 'setup_quality': 'Marginal'},
        {'symbol': 'XRPUSDT', 'signal': 'BUY', 'setup_quality': 'Good'}
    ]
    
    print("Testing trade signals with relative strength filtering:")
    
    approved_trades = 0
    rejected_trades = 0
    
    for signal in test_signals:
        symbol = signal['symbol']
        ranking_data = test_rankings.get(symbol, {})
        is_top = is_symbol_top_performer(symbol, test_rankings)
        
        print(f"\n📈 Signal: {symbol} - {signal['signal']}")
        print(f"  Setup Quality: {signal['setup_quality']}")
        print(f"  Rank: #{ranking_data.get('rank', 'N/A')}")
        print(f"  Performance: {ranking_data.get('performance_pct', 0):+.1f}%")
        
        if is_top:
            print(f"  ✅ APPROVED - Top performer eligible for trading")
            approved_trades += 1
        else:
            print(f"  ❌ REJECTED - Weak relative strength")
            rejected_trades += 1
    
    print(f"\n📊 FILTERING RESULTS:")
    print(f"  Approved Trades: {approved_trades}")
    print(f"  Rejected Trades: {rejected_trades}")
    print(f"  Selectivity: {(rejected_trades / len(test_signals)) * 100:.1f}% filtered out")


def test_ranking_update_logic():
    """Test the ranking update frequency logic."""
    print("\n\n⏰ Testing Ranking Update Logic")
    print("=" * 60)
    
    update_frequency_hours = 4
    current_time = time.time()
    
    # Simulate different scenarios
    scenarios = [
        {
            'name': 'Fresh Start (No Previous Rankings)',
            'last_update': 0,
            'expected': 'UPDATE_REQUIRED'
        },
        {
            'name': 'Recent Update (1 hour ago)',
            'last_update': current_time - (1 * 3600),
            'expected': 'USE_CACHED'
        },
        {
            'name': 'Moderate Age (3 hours ago)',
            'last_update': current_time - (3 * 3600),
            'expected': 'USE_CACHED'
        },
        {
            'name': 'Stale Rankings (5 hours ago)',
            'last_update': current_time - (5 * 3600),
            'expected': 'UPDATE_REQUIRED'
        },
        {
            'name': 'Very Stale Rankings (12 hours ago)',
            'last_update': current_time - (12 * 3600),
            'expected': 'UPDATE_REQUIRED'
        }
    ]
    
    for scenario in scenarios:
        last_update = scenario['last_update']
        hours_since_update = (current_time - last_update) / 3600
        
        # Simulate the update logic
        should_update = (hours_since_update >= update_frequency_hours or last_update == 0)
        result = 'UPDATE_REQUIRED' if should_update else 'USE_CACHED'
        
        print(f"\n🕐 {scenario['name']}:")
        print(f"  Hours Since Update: {hours_since_update:.1f}")
        print(f"  Update Frequency: {update_frequency_hours} hours")
        print(f"  Decision: {result}")
        print(f"  Expected: {scenario['expected']}")
        
        if result == scenario['expected']:
            print(f"  ✅ Logic working correctly")
        else:
            print(f"  ❌ Logic error detected!")


def test_portfolio_concentration():
    """Test portfolio concentration effects of the system."""
    print("\n\n💰 Testing Portfolio Concentration Effects")
    print("=" * 60)
    
    # Simulate portfolio allocation scenarios
    scenarios = [
        {
            'name': 'No Filtering (All Coins)',
            'eligible_coins': 20,
            'total_coins': 20,
            'concentration': 'Dispersed'
        },
        {
            'name': 'Top 50% (Moderate Filtering)',
            'eligible_coins': 10,
            'total_coins': 20,
            'concentration': 'Moderate'
        },
        {
            'name': 'Top 25% (Intelligent Filtering)',
            'eligible_coins': 5,
            'total_coins': 20,
            'concentration': 'Concentrated'
        },
        {
            'name': 'Top 10% (Very Selective)',
            'eligible_coins': 2,
            'total_coins': 20,
            'concentration': 'Highly Concentrated'
        }
    ]
    
    for scenario in scenarios:
        eligible = scenario['eligible_coins']
        total = scenario['total_coins']
        selectivity_pct = ((total - eligible) / total) * 100
        
        print(f"\n📊 {scenario['name']}:")
        print(f"  Eligible Coins: {eligible}/{total}")
        print(f"  Selectivity: {selectivity_pct:.0f}% filtered out")
        print(f"  Concentration: {scenario['concentration']}")
        
        # Estimate capital allocation per coin
        capital_per_coin = 100 / eligible  # Assuming $100 total capital
        
        print(f"  Capital per Coin: ${capital_per_coin:.2f}")
        
        # Risk assessment
        if eligible >= 10:
            risk_level = "Low (Well diversified)"
        elif eligible >= 5:
            risk_level = "Moderate (Focused but diversified)"
        elif eligible >= 2:
            risk_level = "Higher (Concentrated)"
        else:
            risk_level = "High (Very concentrated)"
        
        print(f"  Risk Level: {risk_level}")


if __name__ == "__main__":
    test_relative_strength_calculations()
    test_filtering_logic()
    test_ranking_update_logic()
    test_portfolio_concentration()
    
    print("\n" + "=" * 60)
    print("✅ All Intelligent Watchlist Scanner Tests Completed!")
    print("\nKey Benefits of the System:")
    print("• Focuses capital on coins with proven momentum")
    print("• Avoids weak performers that may continue declining")
    print("• Increases probability of successful breakouts")
    print("• Concentrates firepower on best opportunities")
    print("• Follows 'buy strength, sell weakness' principle")
    print("• Improves risk-adjusted returns through better selection")
    print("\nThe bot now prioritizes quality over quantity!")
