#!/usr/bin/env python3
"""
test_simulation_bot.py - Comprehensive test suite for the simulation bot system.

Tests:
1. Configuration loading and validation
2. SimulatedTradingBot initialization and basic functionality
3. Twitter notification service (if credentials available)
4. Virtual balance management
5. Trade simulation logic
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.env_loader import load_environment
from src.models.config_models import TradingConfig
from src.models.trade_models import Trade
from src.services.notification_service import TwitterNotificationService
from src.simulated_trading_bot import SimulatedTradingBot, SimulatedPosition


class TestSimulationConfiguration(unittest.TestCase):
    """Test configuration loading and validation for simulation mode."""
    
    def setUp(self):
        """Set up test environment variables."""
        self.original_env = dict(os.environ)
        
        # Set required environment variables for testing
        os.environ.update({
            'SIMULATION_MODE': 'true',
            'SIMULATION_BALANCE': '10000.0',
            'BINANCE_API_KEY': 'test_api_key',
            'BINANCE_API_SECRET': 'test_api_secret',
            'USE_TESTNET': 'true',
            'SYMBOLS': 'BTCUSDT,ETHUSDT',
            'TRADE_AMOUNT': '100.0',
            'ENABLE_TWITTER_NOTIFICATIONS': 'false'
        })
    
    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_simulation_config_loading(self):
        """Test that simulation configuration loads correctly."""
        config = TradingConfig.from_env()
        
        self.assertTrue(config.simulation_mode)
        self.assertEqual(config.simulation_balance, 10000.0)
        self.assertEqual(config.trade_amount, 100.0)
        self.assertIn('BTCUSDT', config.symbols)
        self.assertIn('ETHUSDT', config.symbols)
    
    def test_twitter_config_optional(self):
        """Test that Twitter configuration is optional."""
        config = TradingConfig.from_env()
        
        # Should not raise error even without Twitter credentials
        self.assertFalse(config.enable_twitter_notifications)


class TestSimulatedTradingBot(unittest.TestCase):
    """Test the simulated trading bot functionality."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config = Mock()
        self.config.simulation_mode = True
        self.config.simulation_balance = 10000.0
        self.config.trade_amount = 100.0
        self.config.symbols = ['BTCUSDT', 'ETHUSDT']
        self.config.enable_twitter_notifications = False
        self.config.testnet = True
        self.config.api_key = 'test_key'
        self.config.api_secret = 'test_secret'
    
    @patch('src.simulated_trading_bot.MarketDataService')
    @patch('src.simulated_trading_bot.TechnicalAnalysisService')
    @patch('src.simulated_trading_bot.EMACrossStrategy')
    def test_bot_initialization(self, mock_strategy, mock_ta, mock_market):
        """Test that the bot initializes correctly."""
        bot = SimulatedTradingBot(self.config)
        
        self.assertEqual(bot.simulated_balance, 10000.0)
        self.assertEqual(len(bot.simulated_positions), 0)
        self.assertIsNotNone(bot.market_data_service)
        self.assertIsNotNone(bot.technical_analysis_service)
        self.assertIsNotNone(bot.strategy)
    
    @patch('src.simulated_trading_bot.MarketDataService')
    @patch('src.simulated_trading_bot.TechnicalAnalysisService')
    @patch('src.simulated_trading_bot.EMACrossStrategy')
    def test_virtual_balance_management(self, mock_strategy, mock_ta, mock_market):
        """Test virtual balance tracking."""
        bot = SimulatedTradingBot(self.config)
        
        # Initial balance
        self.assertEqual(bot.simulated_balance, 10000.0)
        
        # Simulate a profitable trade
        bot.simulated_balance += 50.0
        self.assertEqual(bot.simulated_balance, 10050.0)
        
        # Check performance calculation
        performance = bot.get_performance_summary()
        self.assertEqual(performance['current_balance'], 10050.0)
        self.assertEqual(performance['total_pnl'], 50.0)
    
    @patch('src.simulated_trading_bot.MarketDataService')
    @patch('src.simulated_trading_bot.TechnicalAnalysisService')
    @patch('src.simulated_trading_bot.EMACrossStrategy')
    def test_simulated_position_management(self, mock_strategy, mock_ta, mock_market):
        """Test simulated position tracking."""
        bot = SimulatedTradingBot(self.config)
        
        # Create a simulated position
        position = SimulatedPosition(
            symbol='BTCUSDT',
            side='BUY',
            quantity=0.001,
            entry_price=50000.0,
            entry_time='2024-01-01T12:00:00Z',
            stop_loss=48000.0,
            take_profit=52000.0
        )
        
        bot.simulated_positions['BTCUSDT'] = position
        self.assertEqual(len(bot.simulated_positions), 1)
        
        # Test position value calculation
        current_price = 51000.0
        pnl = (current_price - position.entry_price) * position.quantity
        self.assertAlmostEqual(pnl, 1.0, places=6)


class TestTwitterNotificationService(unittest.TestCase):
    """Test Twitter notification functionality."""
    
    def setUp(self):
        """Set up Twitter service with mock configuration."""
        self.config = Mock()
        self.config.twitter_bearer_token = 'test_bearer_token'
        self.config.twitter_api_key = 'test_api_key'
        self.config.twitter_api_secret = 'test_api_secret'
        self.config.twitter_access_token = 'test_access_token'
        self.config.twitter_access_token_secret = 'test_access_secret'
    
    @patch('src.services.notification_service.requests.post')
    def test_twitter_service_initialization(self, mock_post):
        """Test that Twitter service initializes correctly."""
        service = TwitterNotificationService(self.config)
        
        self.assertEqual(service.bearer_token, 'test_bearer_token')
        self.assertEqual(service.api_key, 'test_api_key')
    
    @patch('src.services.notification_service.requests.post')
    def test_signal_notification_format(self, mock_post):
        """Test trading signal notification formatting."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'data': {'id': '123456'}}
        mock_post.return_value = mock_response
        
        service = TwitterNotificationService(self.config)
        
        # Create test trade
        trade = Trade(
            symbol='BTCUSDT',
            side='BUY',
            quantity=0.001,
            price=50000.0,
            trade_amount=50.0,
            stop_loss=48000.0,
            take_profit=52000.0
        )
        
        # Test signal notification
        result = service.send_signal_notification(trade)
        
        # Should return tweet ID for later replies
        self.assertEqual(result, '123456')
        
        # Check that request was made with proper format
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Verify request structure
        self.assertIn('json', call_args.kwargs)
        tweet_data = call_args.kwargs['json']
        self.assertIn('text', tweet_data)
        
        # Verify tweet content includes key information
        tweet_text = tweet_data['text']
        self.assertIn('BTCUSDT', tweet_text)
        self.assertIn('BUY', tweet_text)
        self.assertIn('$50.00', tweet_text)


class TestTradeModels(unittest.TestCase):
    """Test enhanced trade models."""
    
    def test_trade_percentage_calculations(self):
        """Test stop loss and take profit percentage calculations."""
        trade = Trade(
            symbol='BTCUSDT',
            side='BUY',
            quantity=0.001,
            price=50000.0,
            trade_amount=50.0,
            stop_loss=48000.0,
            take_profit=52000.0
        )
        
        # Test percentage calculations
        self.assertAlmostEqual(trade.stop_loss_percentage, -4.0, places=1)
        self.assertAlmostEqual(trade.take_profit_percentage, 4.0, places=1)
    
    def test_trade_with_none_values(self):
        """Test trade model handles None values correctly."""
        trade = Trade(
            symbol='BTCUSDT',
            side='BUY',
            quantity=0.001,
            price=50000.0,
            trade_amount=50.0
        )
        
        # Should handle None stop_loss and take_profit gracefully
        self.assertIsNone(trade.stop_loss_percentage)
        self.assertIsNone(trade.take_profit_percentage)


def run_integration_test():
    """Run a simple integration test with the actual simulation bot."""
    print("\n" + "="*60)
    print("🧪 RUNNING INTEGRATION TEST")
    print("="*60)
    
    try:
        # Set up minimal environment for testing
        test_env = {
            'SIMULATION_MODE': 'true',
            'SIMULATION_BALANCE': '1000.0',
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret',
            'USE_TESTNET': 'true',
            'SYMBOLS': 'BTCUSDT',
            'TRADE_AMOUNT': '50.0',
            'ENABLE_TWITTER_NOTIFICATIONS': 'false'
        }
        
        # Temporarily set environment
        original_env = dict(os.environ)
        os.environ.update(test_env)
        
        try:
            from src.models.config_models import TradingConfig
            config = TradingConfig.from_env()
            
            print(f"✅ Configuration loaded successfully")
            print(f"   Simulation Balance: ${config.simulation_balance:.2f}")
            print(f"   Trading Symbols: {config.symbols}")
            print(f"   Simulation Mode: {config.simulation_mode}")
            
            # Test bot initialization (without actually running)
            print("✅ Integration test passed - configuration and imports work correctly")
            
        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(original_env)
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("🚀 Starting Simulation Bot Test Suite")
    print("="*60)
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSimulationConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestSimulatedTradingBot))
    suite.addTests(loader.loadTestsFromTestCase(TestTwitterNotificationService))
    suite.addTests(loader.loadTestsFromTestCase(TestTradeModels))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run integration test
    run_integration_test()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    if result.wasSuccessful():
        print("✅ All unit tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} test(s) had errors")
    
    print(f"🧪 Tests run: {result.testsRun}")
    print("="*60)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())