"""
Unit tests for the OTOLadderStrategy
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from unittest import TestCase

from app.api.schwab_client import SchwabAPIClient
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.strategies.oto_ladder_strategy import OTOLadderStrategy
from app.services.service_registry import ServiceRegistry


class TestOTOLadderStrategy(TestCase):
    """Test the OTOLadderStrategy"""

    def setup_method(self, method=None):
        """Set up test environment before each test"""
        # Create a mock API client
        self.api_client = SchwabAPIClient()
        
        # Create and register the trading service
        self.trading_service = TradingService()
        self.trading_service.api_client = self.api_client
        ServiceRegistry.register("trading", self.trading_service)
        
        # Create and register the market data service
        self.market_data_service = MarketDataService()
        self.market_data_service.api_client = self.api_client
        ServiceRegistry.register("market_data", self.market_data_service)
        
        # Create the strategy
        self.strategy = OTOLadderStrategy()
        # Set the api_client explicitly
        self.strategy.api_client = self.api_client
        
        # Clear any existing mock orders
        self.api_client.mock_orders = {}
        
        # Mock quote data for testing
        self.mock_quote_response = {
            'success': True,
            'symbol': 'SPY',
            'last_price': 450.0,
            'bid_price': 449.95,
            'ask_price': 450.05,
            'volume': 25000000,
            'timestamp': '2023-01-01T12:00:00Z'
        }
        
        # Set up a patch for get_quote to return the mock data
        get_quote_patcher = patch.object(
            self.api_client, 'get_quote', 
            return_value=self.mock_quote_response
        )
        self.mock_get_quote = get_quote_patcher.start()
        self.addCleanup(get_quote_patcher.stop)
    
    def teardown_method(self, method=None):
        """Clean up after each test"""
        ServiceRegistry.clear()
        # Remove any test OTO Ladder files that were created
        try:
            script_dir = os.path.join(os.getcwd(), 'oto_ladder')
            if os.path.exists(script_dir):
                for file in os.listdir(script_dir):
                    if file.endswith('.ts') and 'OTOLadderStrategy' in file:
                        os.remove(os.path.join(script_dir, file))
        except Exception as e:
            pass

    def test_initialization(self):
        """Test that the strategy initializes correctly"""
        assert self.strategy is not None
        assert self.strategy.api_client is not None
        assert self.strategy.strategy_name == "OTOLadderStrategy"
        # Verify OTO Ladder code was generated
        assert 'input symbol' in self.strategy.oto_ladder_code
        assert 'def SELL_PERCENTAGE = 5.0' in self.strategy.oto_ladder_code
        assert 'TIF = "EXTO"' in self.strategy.oto_ladder_code

    def test_generate_oto_ladder_code(self):
        """Test that the OTO Ladder code is properly generated"""
        code = self.strategy._generate_oto_ladder_code()
        assert code is not None
        assert isinstance(code, str)
        assert len(code) > 100
        
        # Check for key components
        assert '# Title: One-Triggers-Other Step Strategy with Extended Hours' in code
        assert 'input symbol' in code
        assert 'input startPrice' in code
        assert 'input step' in code
        assert 'input initialShares' in code
        assert 'def SELL_PERCENTAGE = 5.0' in code
        assert 'TIF = "EXTO"' in code

    def test_execute_basic_functionality(self):
        """Test basic execution functionality with default parameters"""
        # Mock the _save_oto_ladder_to_file method
        with patch.object(
            self.strategy, '_save_oto_ladder_to_file', 
            return_value='/path/to/mock_script.ts'
        ) as mock_save:
            
            result = self.strategy.execute(symbol='SPY')
            
            # Verify the result contains expected fields
            assert result['success'] is True
            assert result['strategy'] == 'OTOLadderStrategy'
            assert result['symbol'] == 'SPY'
            assert 'start_price' in result
            assert 'step' in result
            assert 'current_price' in result
            assert 'current_step_level' in result
            assert 'initial_shares' in result
            assert 'shares_to_sell' in result
            assert 'oto_ladder_file' in result
            assert 'oto_ladder_code' in result
            assert 'next_sell_price' in result
            
            # Verify the quote was requested
            self.mock_get_quote.assert_called_once_with('SPY')
            
            # Verify the file was saved
            mock_save.assert_called_once_with('SPY')

    def test_execute_with_custom_parameters(self):
        """Test execution with custom parameters"""
        # Mock the _save_oto_ladder_to_file method
        with patch.object(
            self.strategy, '_save_oto_ladder_to_file', 
            return_value='/path/to/mock_script.ts'
        ) as mock_save:
            
            result = self.strategy.execute(
                symbol='AAPL',
                start_price=200.0,
                step=10.0,
                initial_shares=500
            )
            
            # Verify the result contains expected fields with custom values
            assert result['success'] is True
            assert result['symbol'] == 'AAPL'
            assert result['start_price'] == 200.0
            assert result['step'] == 10.0
            assert result['initial_shares'] == 500
            assert result['shares_to_sell'] == 25  # 5% of 500
            
            # Verify the quote was requested for the correct symbol
            self.mock_get_quote.assert_called_once_with('AAPL')

    def test_get_current_price(self):
        """Test the _get_current_price method"""
        # Test with successful quote response
        price = self.strategy._get_current_price('SPY')
        assert price == 450.0
        self.mock_get_quote.assert_called_with('SPY')
        
        # Test with failed quote response
        self.mock_get_quote.return_value = {'success': False}
        price = self.strategy._get_current_price('SPY')
        assert price == 0.0
        
        # Test with exception handling
        self.mock_get_quote.side_effect = Exception("API error")
        price = self.strategy._get_current_price('SPY')
        assert price == 0.0

    @patch('os.makedirs')
    @patch('os.path.join')
    @patch('time.time', return_value=1234567890)
    @patch('builtins.open', new_callable=mock_open)
    def test_save_oto_ladder_to_file(self, mock_file, mock_time, mock_join, mock_makedirs):
        """Test the _save_oto_ladder_to_file method"""
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        filepath = self.strategy._save_oto_ladder_to_file('SPY')
        
        # Verify directory was created
        mock_makedirs.assert_called_once()
        
        # Verify file was opened and written
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(self.strategy.oto_ladder_code)
        
        # Verify timestamp was used in filename
        assert 'SPY_OTOLadderStrategy_1234567890.ts' in filepath

    def test_place_oto_order_chain(self):
        """Test the place_oto_order_chain method"""
        result = self.strategy.place_oto_order_chain(
            symbol='SPY',
            sell_quantity=10,
            sell_price=450.0,
            buy_price=440.0,
            take_profit_price=455.0
        )
        
        assert result['success'] is True
        assert 'message' in result
        assert 'details' in result
        
        # Check order details
        orders = result['details']
        assert orders['first_order']['type'] == 'SELL'
        assert orders['first_order']['quantity'] == 10
        assert orders['first_order']['price'] == 450.0
        assert orders['first_order']['tif'] == 'EXTO'
        
        assert orders['second_order']['type'] == 'BUY'
        assert orders['second_order']['quantity'] == 10
        assert orders['second_order']['price'] == 440.0
        
        assert orders['third_order']['type'] == 'SELL'
        assert orders['third_order']['quantity'] == 10
        assert orders['third_order']['price'] == 455.0

    def test_validate_config_valid(self):
        """Test config validation with valid configuration"""
        self.strategy.config = {
            'symbol': 'SPY',
            'start_price': 450.0,
            'step': 5.0,
            'initial_shares': 100
        }
        
        result = self.strategy.validate_config()
        assert result['valid'] is True

    def test_validate_config_missing_fields(self):
        """Test config validation with missing fields"""
        self.strategy.config = {
            'symbol': 'SPY',
            'start_price': 450.0
        }
        
        result = self.strategy.validate_config()
        assert result['valid'] is False
        assert 'missing' in result['error'].lower()

    def test_validate_config_invalid_values(self):
        """Test config validation with invalid values"""
        # Test with negative step
        self.strategy.config = {
            'symbol': 'SPY',
            'start_price': 450.0,
            'step': -5.0,
            'initial_shares': 100
        }
        
        result = self.strategy.validate_config()
        assert result['valid'] is False
        assert 'step' in result['error'].lower()
        
        # Test with zero shares
        self.strategy.config = {
            'symbol': 'SPY',
            'start_price': 450.0,
            'step': 5.0,
            'initial_shares': 0
        }
        
        result = self.strategy.validate_config()
        assert result['valid'] is False
        assert 'shares' in result['error'].lower()

    def test_validate_config_with_price_target(self):
        """Test config validation with price_target parameter"""
        # Test with valid price_target
        self.strategy.config = {
            'symbol': 'SPY',
            'start_price': 450.0,
            'step': 5.0,
            'initial_shares': 100,
            'price_target': 500.0
        }
        
        result = self.strategy.validate_config()
        assert result['valid'] is True
        
        # Test with negative price_target
        self.strategy.config = {
            'symbol': 'SPY',
            'start_price': 450.0,
            'step': 5.0,
            'initial_shares': 100,
            'price_target': -10.0
        }
        
        result = self.strategy.validate_config()
        assert result['valid'] is False
        assert 'price target' in result['error'].lower()
        
        # Test with price_target lower than start_price
        self.strategy.config = {
            'symbol': 'SPY',
            'start_price': 450.0,
            'step': 5.0,
            'initial_shares': 100,
            'price_target': 440.0
        }
        
        result = self.strategy.validate_config()
        assert result['valid'] is False
        assert 'price target should be greater than start price' in result['error'].lower()

    def test_execute_with_price_target_reached(self):
        """Test execution when price target is reached"""
        # Set a price target that's already reached
        self.mock_quote_response['last_price'] = 500.0
        
        # Mock the _save_oto_ladder_to_file method
        with patch.object(
            self.strategy, '_save_oto_ladder_to_file', 
            return_value='/path/to/mock_script.ts'
        ) as mock_save:
            
            result = self.strategy.execute(
                symbol='SPY',
                start_price=450.0,
                step=5.0,
                initial_shares=100,
                price_target=480.0  # Target below current price
            )
            
            # Verify the result indicates target reached
            assert result['success'] is True
            assert result['target_reached'] is True
            assert 'message' in result
            assert 'price target reached' in result['message'].lower()
            assert result['current_price'] == 500.0
            assert result['price_target'] == 480.0
            
            # Verify the quote was requested
            self.mock_get_quote.assert_called_once_with('SPY')
            
            # Verify the file was NOT saved since strategy terminated early
            mock_save.assert_not_called() 