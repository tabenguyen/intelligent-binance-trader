"""
Simple test runner for trading bot testing without external dependencies

This file can be run directly without pytest to test core functionality.
For full testing, install dependencies with: uv sync --group test
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import json
import tempfile

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot modules
import trading_bot
from strategies.ema_cross_strategy import EMACrossStrategy


class TestTradingBotBasic(unittest.TestCase):
    """Basic tests that don't require external libraries"""
    
    def setUp(self):
        """Setup test environment"""
        self.mock_client = Mock()
        
        # Sample analysis data
        self.sample_analysis = {
            '12_EMA': 47200.0,
            '26_EMA': 46800.0,
            '55_EMA': 46500.0,
            'RSI_21': 62.5,
            'MACD': 150.0,
            'MACD_Signal': 120.0,
            'MACD_Histogram': 30.0,
            'BB_Upper': 48000.0,
            'BB_Middle': 47000.0,
            'BB_Lower': 46000.0,
            'Volume_Ratio': 1.25,
            'Volatility_State': 'NORMAL',
            'ATR_Percentile': 1.2
        }

    def test_format_value_basic(self):
        """Test basic value formatting"""
        filters = [
            {'filterType': 'PRICE_FILTER', 'tickSize': '0.01'},
            {'filterType': 'LOT_SIZE', 'stepSize': '0.00001'}
        ]
        
        # Test price formatting
        formatted_price = trading_bot.format_value(47123.456, filters, 'PRICE_FILTER', 'tickSize')
        self.assertEqual(formatted_price, "47123.46")
        
        # Test quantity formatting  
        formatted_qty = trading_bot.format_value(0.123456789, filters, 'LOT_SIZE', 'stepSize')
        self.assertEqual(formatted_qty, "0.12346")

    def test_get_min_notional(self):
        """Test minimum notional extraction"""
        filters = [
            {'filterType': 'PRICE_FILTER', 'tickSize': '0.01'},
            {'filterType': 'NOTIONAL', 'minNotional': '15.00'}
        ]
        
        min_notional = trading_bot.get_min_notional(filters)
        self.assertEqual(min_notional, 15.0)

    def test_is_symbol_actively_trading(self):
        """Test active trading check"""
        # Clear and set test data
        trading_bot.active_trades = {'BTCUSDT': 12345}
        
        # Test active symbol
        self.assertTrue(trading_bot.is_symbol_actively_trading('BTCUSDT'))
        
        # Test inactive symbol
        self.assertFalse(trading_bot.is_symbol_actively_trading('ETHUSDT'))

    def test_strategy_initialization(self):
        """Test strategy initialization"""
        strategy = EMACrossStrategy()
        
        self.assertIsNotNone(strategy.name)
        self.assertIn('EMA', strategy.name)
        self.assertTrue(hasattr(strategy, 'check_buy_signal'))
        self.assertTrue(hasattr(strategy, 'get_strategy_description'))

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', False)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_strategy_buy_signal_basic(self):
        """Test basic buy signal logic"""
        strategy = EMACrossStrategy()
        current_price = 46900.0  # Near 26_EMA (46800)
        
        # This should pass basic conditions
        result = strategy.check_buy_signal(
            "BTCUSDT", self.sample_analysis, current_price, self.mock_client
        )
        
        # Should return a boolean
        self.assertIsInstance(result, bool)

    def test_save_load_active_trades(self):
        """Test save/load active trades functionality"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Set test data
            trading_bot.active_trades = {'BTCUSDT': 12345, 'ETHUSDT': 67890}
            
            # Test save
            with patch('trading_bot.ACTIVE_TRADES_FILE', temp_file_path):
                trading_bot.save_active_trades()
            
            # Verify file exists and has content
            self.assertTrue(os.path.exists(temp_file_path))
            
            with open(temp_file_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data, {'BTCUSDT': 12345, 'ETHUSDT': 67890})
            
            # Test load
            trading_bot.active_trades.clear()
            with patch('trading_bot.ACTIVE_TRADES_FILE', temp_file_path):
                trading_bot.load_active_trades()
            
            self.assertEqual(trading_bot.active_trades, {'BTCUSDT': 12345, 'ETHUSDT': 67890})
            
        finally:
            # Cleanup
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_get_usdt_balance_mock(self):
        """Test USDT balance retrieval with mock"""
        # Setup mock response
        self.mock_client.account.return_value = {
            'balances': [
                {'asset': 'BTC', 'free': '0.5', 'locked': '0.0'},
                {'asset': 'USDT', 'free': '1000.0', 'locked': '50.0'},
                {'asset': 'ETH', 'free': '2.0', 'locked': '0.0'}
            ]
        }
        
        # Call function
        balance = trading_bot.get_usdt_balance(self.mock_client)
        
        # Should return the free USDT balance
        self.assertEqual(balance, 1000.0)

    def test_validate_trade_amount_calculation(self):
        """Test trade amount validation calculation"""
        # Mock exchange info
        filters = [
            {'filterType': 'NOTIONAL', 'minNotional': '10.00'}
        ]
        
        self.mock_client.exchange_info.return_value = {
            'symbols': [{'symbol': 'BTCUSDT', 'filters': filters}]
        }
        
        # Test valid amount (15 USDT at 47000 price = ~0.000319 BTC, value = ~15 USDT > 10 min)
        is_valid, msg = trading_bot.validate_trade_amount(self.mock_client, "BTCUSDT", 15.0, 47000.0)
        self.assertTrue(is_valid)
        self.assertIn("meets minimum notional", msg)
        
        # Test invalid amount (5 USDT at 47000 price = value < 10 min notional)
        is_valid, msg = trading_bot.validate_trade_amount(self.mock_client, "BTCUSDT", 5.0, 47000.0)
        self.assertFalse(is_valid)
        self.assertIn("below minimum notional", msg)


class TestStrategyConditions(unittest.TestCase):
    """Test strategy condition logic"""
    
    def setUp(self):
        """Setup for strategy tests"""
        self.strategy = EMACrossStrategy()
        self.mock_client = Mock()

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', False)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_buy_signal_conditions(self):
        """Test individual buy signal conditions"""
        
        # Test case 1: All conditions met
        analysis_good = {
            '12_EMA': 47200.0,    # Above 26_EMA ✓
            '26_EMA': 46800.0,
            '55_EMA': 46500.0,    # Price will be above this ✓
            'RSI_21': 62.5,       # Between 45-75 ✓
            'MACD': 150.0,        # Above signal ✓
            'MACD_Signal': 120.0,
            'MACD_Histogram': 30.0,  # Positive ✓
            'BB_Upper': 48000.0,
            'BB_Middle': 47000.0,
            'BB_Lower': 46000.0,
        }
        
        current_price_good = 46900.0  # Above 55_EMA and near 26_EMA ✓
        
        result = self.strategy.check_buy_signal("BTCUSDT", analysis_good, current_price_good, self.mock_client)
        self.assertTrue(result)
        
        # Test case 2: Price below 55_EMA
        current_price_bad = 46000.0  # Below 55_EMA
        result = self.strategy.check_buy_signal("BTCUSDT", analysis_good, current_price_bad, self.mock_client)
        self.assertFalse(result)
        
        # Test case 3: RSI too high
        analysis_rsi_high = analysis_good.copy()
        analysis_rsi_high['RSI_21'] = 80.0  # Above 75
        result = self.strategy.check_buy_signal("BTCUSDT", analysis_rsi_high, current_price_good, self.mock_client)
        self.assertFalse(result)
        
        # Test case 4: RSI too low
        analysis_rsi_low = analysis_good.copy()
        analysis_rsi_low['RSI_21'] = 35.0  # Below 45
        result = self.strategy.check_buy_signal("BTCUSDT", analysis_rsi_low, current_price_good, self.mock_client)
        self.assertFalse(result)
        
        # Test case 5: 12_EMA below 26_EMA (bearish momentum)
        analysis_bearish = analysis_good.copy()
        analysis_bearish['12_EMA'] = 46000.0  # Below 26_EMA
        result = self.strategy.check_buy_signal("BTCUSDT", analysis_bearish, current_price_good, self.mock_client)
        self.assertFalse(result)


def run_tests():
    """Run all tests and display results"""
    print("=" * 60)
    print("🧪 TRADING BOT TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTradingBotBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyConditions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print(f"\n✅ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ SOME TESTS FAILED!")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
