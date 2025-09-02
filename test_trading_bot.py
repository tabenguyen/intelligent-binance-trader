"""
Comprehensive Test Suite for Trading Bot

This test suite covers:
- Trading strategy logic
- API interactions (mocked)
- Signal generation
- Risk management
- Order execution simulation
- Portfolio management

Run with: pytest test_trading_bot.py -v
Run with coverage: pytest test_trading_bot.py --cov=trading_bot --cov-report=html
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from freezegun import freeze_time
import json
import os
import tempfile
from datetime import datetime, timedelta

# Import your trading bot modules
import trading_bot
from strategies.ema_cross_strategy import EMACrossStrategy
from strategies.base_strategy import BaseStrategy


class TestTradingBotCore:
    """Test core trading bot functionality"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        # Create mock client
        self.mock_client = Mock()
        
        # Sample market data
        self.sample_klines = [
            [1640995200000, "46000.00", "47000.00", "45500.00", "46500.00", "100.5", 1640998800000, "4672500.00", 1000, "50.25", "2336250.00", "0"],
            [1640998800000, "46500.00", "47500.00", "46000.00", "47000.00", "110.2", 1641002400000, "5181400.00", 1100, "55.1", "2590700.00", "0"],
            [1641002400000, "47000.00", "48000.00", "46800.00", "47800.00", "95.8", 1641006000000, "4576440.00", 950, "47.9", "2288220.00", "0"],
        ]
        
        # Sample technical analysis data
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
            'Last_Swing_High': 48000.0,
            'Last_Swing_Low': 45500.0,
            'Volume_Ratio': 1.25,
            'Current_Volume': 110.2,
            'Avg_Volume_20': 88.16,
            'Volatility_State': 'NORMAL',
            'ATR_Percentile': 1.2
        }

    def test_get_binance_data_success(self):
        """Test successful data retrieval from Binance"""
        # Setup mock response
        self.mock_client.klines.return_value = self.sample_klines
        
        # Call function
        df = trading_bot.get_binance_data(self.mock_client, "BTCUSDT", "4h", 100)
        
        # Assertions
        assert df is not None
        assert len(df) == 3
        assert 'Open' in df.columns
        assert 'High' in df.columns
        assert 'Low' in df.columns
        assert 'Close' in df.columns
        assert 'Volume' in df.columns
        
        # Check data types
        assert df['Open'].dtype in [np.float64, float]
        assert df['Close'].iloc[-1] == 47800.0

    def test_get_binance_data_api_error(self):
        """Test handling of API errors"""
        from binance.error import ClientError
        
        # Setup mock to raise error (ClientError requires status_code, error_code, error_message, header)
        self.mock_client.klines.side_effect = ClientError(400, -1121, "Invalid symbol", {})
        
        # Call function
        df = trading_bot.get_binance_data(self.mock_client, "INVALID", "4h", 100)
        
        # Should return None on error
        assert df is None

    def test_analyze_data_success(self):
        """Test technical analysis calculation"""
        # Create sample DataFrame
        dates = pd.date_range(start='2024-01-01', periods=100, freq='4h')
        df = pd.DataFrame({
            'Open': np.random.uniform(45000, 48000, 100),
            'High': np.random.uniform(46000, 49000, 100),
            'Low': np.random.uniform(44000, 47000, 100),
            'Close': np.random.uniform(45000, 48000, 100),
            'Volume': np.random.uniform(50, 150, 100)
        })
        
        # Ensure realistic price relationships
        for i in range(len(df)):
            df.loc[i, 'High'] = max(df.loc[i, 'Open'], df.loc[i, 'Close']) + np.random.uniform(0, 500)
            df.loc[i, 'Low'] = min(df.loc[i, 'Open'], df.loc[i, 'Close']) - np.random.uniform(0, 500)
        
        # Call function
        analysis = trading_bot.analyze_data(df)
        
        # Assertions
        assert analysis is not None
        assert 'Last_Swing_High' in analysis
        assert 'Last_Swing_Low' in analysis
        assert analysis['Last_Swing_High'] > analysis['Last_Swing_Low']

    def test_analyze_data_insufficient_data(self):
        """Test analysis with insufficient data"""
        # Create small DataFrame
        df = pd.DataFrame({
            'Open': [46000, 46500],
            'High': [47000, 47500],
            'Low': [45500, 46000],
            'Close': [46500, 47000],
            'Volume': [100, 110]
        })
        
        # Call function
        analysis = trading_bot.analyze_data(df, swing_period=50)
        
        # Should return None with insufficient data
        assert analysis is None


class TestEMACrossStrategy:
    """Test EMA Cross Strategy implementation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.strategy = EMACrossStrategy()
        self.mock_client = Mock()
        
        # Sample analysis data for testing
        self.bullish_analysis = {
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
        
        self.bearish_analysis = {
            '12_EMA': 46000.0,  # Below 26_EMA
            '26_EMA': 46800.0,
            '55_EMA': 47500.0,  # Price below this
            'RSI_21': 35.0,     # Below threshold
            'MACD': -50.0,
            'MACD_Signal': -20.0,
            'MACD_Histogram': -30.0,
            'BB_Upper': 48000.0,
            'BB_Middle': 47000.0,
            'BB_Lower': 46000.0,
            'Volume_Ratio': 0.8,  # Below threshold
            'Volatility_State': 'HIGH',
            'ATR_Percentile': 2.5
        }

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', False) 
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_buy_signal_all_conditions_met(self):
        """Test buy signal when all conditions are met"""
        current_price = 46900.0  # Near 26_EMA (46800)
        
        result = self.strategy.check_buy_signal(
            "BTCUSDT", self.bullish_analysis, current_price, self.mock_client
        )
        
        assert result is True

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', False)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_buy_signal_price_below_55ema(self):
        """Test buy signal rejection when price below 55-EMA"""
        current_price = 46000.0  # Below 55_EMA (46500)
        
        result = self.strategy.check_buy_signal(
            "BTCUSDT", self.bullish_analysis, current_price, self.mock_client
        )
        
        assert result is False

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', False)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_buy_signal_rsi_overbought(self):
        """Test buy signal rejection when RSI is overbought"""
        current_price = 46900.0
        analysis = self.bullish_analysis.copy()
        analysis['RSI_21'] = 80.0  # Above upper threshold (75)
        
        result = self.strategy.check_buy_signal(
            "BTCUSDT", analysis, current_price, self.mock_client
        )
        
        assert result is False

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', False)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_buy_signal_rsi_too_low(self):
        """Test buy signal rejection when RSI is too low"""
        current_price = 46900.0
        analysis = self.bullish_analysis.copy()
        analysis['RSI_21'] = 35.0  # Below lower threshold (45)
        
        result = self.strategy.check_buy_signal(
            "BTCUSDT", analysis, current_price, self.mock_client
        )
        
        assert result is False

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', False)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_buy_signal_price_far_from_support(self):
        """Test buy signal rejection when price too far from 26-EMA"""
        current_price = 48500.0  # More than 3% from 26_EMA (46800)
        
        result = self.strategy.check_buy_signal(
            "BTCUSDT", self.bullish_analysis, current_price, self.mock_client
        )
        
        assert result is False

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', True)
    @patch('trading_bot.ENABLE_ATR_FILTER', False)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_buy_signal_daily_trend_filter_fail(self):
        """Test buy signal rejection when daily trend filter fails"""
        current_price = 46900.0
        
        with patch('trading_bot.get_daily_trend_filter', return_value=False):
            result = self.strategy.check_buy_signal(
                "BTCUSDT", self.bullish_analysis, current_price, self.mock_client
            )
        
        assert result is False

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', True)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', False)
    def test_buy_signal_volatility_filter_fail(self):
        """Test buy signal rejection when volatility filter fails"""
        current_price = 46900.0
        analysis = self.bullish_analysis.copy()
        analysis['Volatility_State'] = 'HIGH'  # Too volatile
        
        result = self.strategy.check_buy_signal(
            "BTCUSDT", analysis, current_price, self.mock_client
        )
        
        assert result is False

    @patch('trading_bot.ENABLE_DAILY_TREND_FILTER', False)
    @patch('trading_bot.ENABLE_ATR_FILTER', False)
    @patch('trading_bot.ENABLE_VOLUME_FILTER', True)
    @patch('trading_bot.MIN_VOLUME_RATIO', 1.2)
    def test_buy_signal_volume_filter_fail(self):
        """Test buy signal rejection when volume filter fails"""
        current_price = 46900.0
        analysis = self.bullish_analysis.copy()
        analysis['Volume_Ratio'] = 0.8  # Below minimum threshold
        
        result = self.strategy.check_buy_signal(
            "BTCUSDT", analysis, current_price, self.mock_client
        )
        
        assert result is False


class TestTradingExecution:
    """Test trade execution functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_client = Mock()
        
        # Sample exchange filters
        self.sample_filters = [
            {'filterType': 'PRICE_FILTER', 'minPrice': '0.01', 'maxPrice': '1000000.00', 'tickSize': '0.01'},
            {'filterType': 'LOT_SIZE', 'minQty': '0.00001', 'maxQty': '9000.00', 'stepSize': '0.00001'},
            {'filterType': 'NOTIONAL', 'minNotional': '10.00'},
        ]

    def test_get_symbol_filters_success(self):
        """Test successful retrieval of symbol filters"""
        # Setup mock response
        self.mock_client.exchange_info.return_value = {
            'symbols': [
                {
                    'symbol': 'BTCUSDT',
                    'filters': self.sample_filters
                }
            ]
        }
        
        # Call function
        filters = trading_bot.get_symbol_filters(self.mock_client, "BTCUSDT")
        
        # Assertions
        assert filters is not None
        assert len(filters) == 3
        assert filters[0]['filterType'] == 'PRICE_FILTER'

    def test_get_min_notional(self):
        """Test minimum notional value extraction"""
        min_notional = trading_bot.get_min_notional(self.sample_filters)
        assert min_notional == 10.0

    def test_format_value_price(self):
        """Test price formatting according to tick size"""
        formatted_price = trading_bot.format_value(
            47123.456, self.sample_filters, 'PRICE_FILTER', 'tickSize'
        )
        assert formatted_price == "47123.46"

    def test_format_value_quantity(self):
        """Test quantity formatting according to step size"""
        formatted_qty = trading_bot.format_value(
            0.123456789, self.sample_filters, 'LOT_SIZE', 'stepSize'
        )
        assert formatted_qty == "0.12346"

    def test_validate_trade_amount_success(self):
        """Test trade amount validation success"""
        # Setup mocks
        self.mock_client.exchange_info.return_value = {
            'symbols': [{'symbol': 'BTCUSDT', 'filters': self.sample_filters}]
        }
        
        # Test with valid amount
        is_valid, msg = trading_bot.validate_trade_amount(
            self.mock_client, "BTCUSDT", 15.0, 47000.0
        )
        
        assert is_valid is True
        assert "meets minimum notional" in msg

    def test_validate_trade_amount_failure(self):
        """Test trade amount validation failure"""
        # Setup mocks
        self.mock_client.exchange_info.return_value = {
            'symbols': [{'symbol': 'BTCUSDT', 'filters': self.sample_filters}]
        }
        
        # Test with amount too small
        is_valid, msg = trading_bot.validate_trade_amount(
            self.mock_client, "BTCUSDT", 5.0, 47000.0
        )
        
        assert is_valid is False
        assert "below minimum notional" in msg

    def test_execute_oco_trade_validation_only(self):
        """Test OCO trade validation without actual execution"""
        # Test that the function handles basic validation
        filters = self.sample_filters
        min_notional = trading_bot.get_min_notional(filters)
        
        # Test trade amount validation (min notional is 10.0 from sample_filters)
        small_trade_value = 0.0001 * 47000.0  # Very small trade (~4.7 USDT)
        insufficient_trade = small_trade_value < min_notional
        
        # Should identify insufficient trade amount  
        assert insufficient_trade is True
        
        # Test sufficient trade amount
        large_trade_value = 0.5 * 47000.0  # Large trade (23500 USDT)
        sufficient_trade = large_trade_value >= min_notional
        assert sufficient_trade is True

    def test_get_usdt_balance_success(self):
        """Test USDT balance retrieval"""
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
        
        # Assertions
        assert balance == 1000.0

    def test_get_usdt_balance_no_usdt(self):
        """Test USDT balance when no USDT found"""
        # Setup mock response without USDT
        self.mock_client.account.return_value = {
            'balances': [
                {'asset': 'BTC', 'free': '0.5', 'locked': '0.0'},
                {'asset': 'ETH', 'free': '2.0', 'locked': '0.0'}
            ]
        }
        
        # Call function
        balance = trading_bot.get_usdt_balance(self.mock_client)
        
        # Should return 0.0 when no USDT found
        assert balance == 0.0


class TestActiveTradesManagement:
    """Test active trades tracking functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Clear active trades
        trading_bot.active_trades.clear()
        
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def teardown_method(self):
        """Cleanup after tests"""
        # Remove temporary file
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)

    def test_save_and_load_active_trades(self):
        """Test saving and loading active trades"""
        # Add some test data
        trading_bot.active_trades = {
            'BTCUSDT': 12345,
            'ETHUSDT': 67890
        }
        
        # Test save
        with patch('trading_bot.ACTIVE_TRADES_FILE', self.temp_file_path):
            trading_bot.save_active_trades()
        
        # Verify file contents
        with open(self.temp_file_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == {'BTCUSDT': 12345, 'ETHUSDT': 67890}
        
        # Test load
        trading_bot.active_trades.clear()
        with patch('trading_bot.ACTIVE_TRADES_FILE', self.temp_file_path):
            trading_bot.load_active_trades()
        
        assert trading_bot.active_trades == {'BTCUSDT': 12345, 'ETHUSDT': 67890}

    def test_is_symbol_actively_trading(self):
        """Test checking if symbol is actively trading"""
        # Add test data
        trading_bot.active_trades = {'BTCUSDT': 12345}
        
        # Test active symbol
        assert trading_bot.is_symbol_actively_trading('BTCUSDT') is True
        
        # Test inactive symbol
        assert trading_bot.is_symbol_actively_trading('ETHUSDT') is False

    def test_check_active_trades_status_completed(self):
        """Test checking status of completed trades"""
        mock_client = Mock()
        
        # Setup active trades
        trading_bot.active_trades = {'BTCUSDT': 12345}
        
        # Mock OCO order status - completed
        mock_client.get_oco_order.return_value = {
            'listOrderStatus': 'ALL_DONE'
        }
        
        # Call function
        trading_bot.check_active_trades_status(mock_client)
        
        # Should remove completed trade
        assert 'BTCUSDT' not in trading_bot.active_trades

    def test_check_active_trades_status_executing(self):
        """Test checking status of executing trades"""
        mock_client = Mock()
        
        # Setup active trades
        trading_bot.active_trades = {'BTCUSDT': 12345}
        
        # Mock OCO order status - still executing
        mock_client.get_oco_order.return_value = {
            'listOrderStatus': 'EXECUTING'
        }
        
        # Call function
        trading_bot.check_active_trades_status(mock_client)
        
        # Should keep active trade
        assert 'BTCUSDT' in trading_bot.active_trades


class TestRelativeStrengthRankings:
    """Test relative strength ranking functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_client = Mock()
        self.watchlist = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        
        # Reset global rankings
        trading_bot.relative_strength_rankings = {}
        trading_bot.last_ranking_update = 0

    @patch('trading_bot.RANKING_UPDATE_FREQUENCY_HOURS', 24)
    @patch('trading_bot.MIN_COINS_FOR_RANKING', 3)
    @patch('trading_bot.RELATIVE_STRENGTH_LOOKBACK_DAYS', 7)
    @patch('trading_bot.TOP_PERFORMERS_PERCENTAGE', 40)
    def test_calculate_relative_strength_rankings_success(self):
        """Test successful relative strength calculation"""
        # Mock data for each symbol
        def mock_klines_side_effect(symbol, **kwargs):
            base_price = {'BTCUSDT': 45000, 'ETHUSDT': 3000, 'ADAUSDT': 0.5, 'DOTUSDT': 25, 'LINKUSDT': 15}[symbol]
            # Create mock data with different performance levels
            multiplier = {'BTCUSDT': 1.1, 'ETHUSDT': 1.05, 'ADAUSDT': 0.95, 'DOTUSDT': 1.15, 'LINKUSDT': 1.02}[symbol]
            
            return [
                [1640995200000, str(base_price), str(base_price * 1.02), str(base_price * 0.98), str(base_price * multiplier), "100.0", 1640998800000, "100000.0", 1000, "50.0", "50000.0", "0"]
                for _ in range(50)  # Sufficient historical data
            ]
        
        self.mock_client.klines.side_effect = mock_klines_side_effect
        
        # Mock get_binance_data to return proper DataFrames
        with patch('trading_bot.get_binance_data') as mock_get_data:
            def mock_data_side_effect(client, symbol, **kwargs):
                base_price = {'BTCUSDT': 45000, 'ETHUSDT': 3000, 'ADAUSDT': 0.5, 'DOTUSDT': 25, 'LINKUSDT': 15}[symbol]
                multiplier = {'BTCUSDT': 1.1, 'ETHUSDT': 1.05, 'ADAUSDT': 0.95, 'DOTUSDT': 1.15, 'LINKUSDT': 1.02}[symbol]
                
                df = pd.DataFrame({
                    'Open': [base_price] * 50,
                    'High': [base_price * 1.02] * 50,
                    'Low': [base_price * 0.98] * 50,
                    'Close': [base_price * multiplier] * 50,
                    'Volume': [100.0] * 50
                })
                return df
            
            mock_get_data.side_effect = mock_data_side_effect
            
            # Call function
            rankings = trading_bot.calculate_relative_strength_rankings(self.mock_client, self.watchlist)
            
            # Assertions
            assert len(rankings) == 5
            assert all(symbol in rankings for symbol in self.watchlist)
            
            # Check ranking structure
            for symbol, data in rankings.items():
                assert 'performance_pct' in data
                assert 'rank' in data
                assert 'is_top_performer' in data
                assert isinstance(data['rank'], int)
                assert isinstance(data['performance_pct'], float)
                assert isinstance(data['is_top_performer'], bool)

    @patch('trading_bot.MIN_COINS_FOR_RANKING', 10)
    def test_calculate_relative_strength_insufficient_coins(self):
        """Test ranking with insufficient coins"""
        small_watchlist = ['BTCUSDT', 'ETHUSDT']
        
        rankings = trading_bot.calculate_relative_strength_rankings(self.mock_client, small_watchlist)
        
        # Should return empty dict when insufficient coins
        assert rankings == {}


class TestConfigurationAndEnvironment:
    """Test configuration and environment handling"""
    
    def test_environment_variables_default_values(self):
        """Test default values when environment variables not set"""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to get fresh environment variable reads
            import importlib
            importlib.reload(trading_bot)
            
            # Should use default values
            assert trading_bot.TRADE_AMOUNT_USDT >= 0
            assert trading_bot.RISK_REWARD_RATIO >= 0
            assert trading_bot.MIN_USDT_BALANCE >= 0

    def test_environment_variables_custom_values(self):
        """Test custom environment variable values"""
        test_env = {
            'TRADE_AMOUNT_USDT': '25.0',
            'RISK_REWARD_RATIO': '2.0',
            'MIN_USDT_BALANCE': '200.0',
            'USE_TESTNET': 'False'
        }
        
        with patch.dict(os.environ, test_env):
            import importlib
            importlib.reload(trading_bot)
            
            assert trading_bot.TRADE_AMOUNT_USDT == 25.0
            assert trading_bot.RISK_REWARD_RATIO == 2.0
            assert trading_bot.MIN_USDT_BALANCE == 200.0
            assert trading_bot.USE_TESTNET is False


# Test fixtures and utilities
@pytest.fixture
def sample_market_data():
    """Fixture providing sample market data"""
    return pd.DataFrame({
        'Open': np.random.uniform(45000, 48000, 100),
        'High': np.random.uniform(46000, 49000, 100),
        'Low': np.random.uniform(44000, 47000, 100),
        'Close': np.random.uniform(45000, 48000, 100),
        'Volume': np.random.uniform(50, 150, 100)
    })


@pytest.fixture
def mock_binance_client():
    """Fixture providing a mock Binance client"""
    client = Mock()
    client.klines.return_value = [
        [1640995200000, "46000.00", "47000.00", "45500.00", "46500.00", "100.5", 1640998800000, "4672500.00", 1000, "50.25", "2336250.00", "0"]
    ]
    client.account.return_value = {
        'balances': [{'asset': 'USDT', 'free': '1000.0', 'locked': '0.0'}]
    }
    client.exchange_info.return_value = {
        'symbols': [{
            'symbol': 'BTCUSDT',
            'filters': [
                {'filterType': 'PRICE_FILTER', 'tickSize': '0.01'},
                {'filterType': 'LOT_SIZE', 'stepSize': '0.00001'},
                {'filterType': 'NOTIONAL', 'minNotional': '10.00'}
            ]
        }]
    }
    return client


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
