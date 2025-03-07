"""
Mock tests for the OTO Ladder strategy
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from unittest import TestCase

from app.strategies.oto_ladder_strategy import OTOLadderStrategy
from app.commands.command_processor import CommandProcessor


class TestOTOLadderStrategyMock(TestCase):
    """Test the OTO Ladder strategy in mock mode"""

    def setup_method(self, method=None):
        """Set up test environment before each test"""
        # Create a mock command processor
        self.command_processor = CommandProcessor()
        
        # Create a mock strategy
        self.strategy = OTOLadderStrategy()
        
        # Mock the _save_oto_ladder_to_file method to avoid file system operations
        self.mock_save_path = "/mock/path/to/oto_ladder_file.ts"
        self.save_file_patcher = patch.object(
            self.strategy, '_save_oto_ladder_to_file', 
            return_value=self.mock_save_path
        )
        self.mock_save_file = self.save_file_patcher.start()
        self.addCleanup(self.save_file_patcher.stop)
        
        # Mock the _get_current_price method to return a predictable value
        self.mock_price = 450.0
        self.get_price_patcher = patch.object(
            self.strategy, '_get_current_price', 
            return_value=self.mock_price
        )
        self.mock_get_price = self.get_price_patcher.start()
        self.addCleanup(self.get_price_patcher.stop)
        
        # Create a temporary directory for any files that might be created
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self, method=None):
        """Clean up after each test"""
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_oto_ladder_strategy_execution(self):
        """Test basic execution of the OTO Ladder strategy"""
        # Execute the strategy with default parameters
        result = self.strategy.execute(symbol="SPY")
        
        # Verify the result
        assert result['success'] is True
        assert result['symbol'] == "SPY"
        assert result['start_price'] == self.mock_price  # Should use current price when start_price is 0
        assert result['step'] == 5.0  # Default step
        assert result['initial_shares'] == 100  # Default shares
        assert result['shares_to_sell'] == 5  # 5% of 100
        assert result['oto_ladder_file'] == self.mock_save_path
        
        # Verify the mock methods were called
        self.mock_get_price.assert_called_once_with("SPY")
        self.mock_save_file.assert_called_once_with("SPY")

    def test_oto_ladder_strategy_with_custom_parameters(self):
        """Test execution of the OTO Ladder strategy with custom parameters"""
        # Execute the strategy with custom parameters
        result = self.strategy.execute(
            symbol="AAPL",
            start_price=200.0,
            step=10.0,
            initial_shares=500
        )
        
        # Verify the result
        assert result['success'] is True
        assert result['symbol'] == "AAPL"
        assert result['start_price'] == 200.0
        assert result['step'] == 10.0
        assert result['initial_shares'] == 500
        assert result['shares_to_sell'] == 25  # 5% of 500
        
        # Verify the mock methods were called
        self.mock_get_price.assert_called_once_with("AAPL")
        self.mock_save_file.assert_called_once_with("AAPL")

    def test_command_processor_oto_ladder_command(self):
        """Test the command processor's handling of OTO Ladder commands"""
        # Mock the strategy service's execute_strategy method
        with patch.object(self.command_processor, '_get_strategy_service') as mock_get_service:
            mock_strategy_service = MagicMock()
            mock_strategy_service.execute_strategy.return_value = {
                'success': True,
                'strategy': {
                    'symbol': 'SPY',
                    'start_price': 450.0,
                    'step': 5.0,
                    'initial_shares': 100,
                    'oto_ladder_file': '/path/to/oto_ladder.ts'
                }
            }
            mock_get_service.return_value = mock_strategy_service
            
            # Test with a natural language command
            result = self.command_processor.process_command(
                "generate oto ladder strategy for SPY starting at $450 with $5 steps and 100 shares"
            )
            
            # Verify the result
            assert result['success'] is True
            assert 'OTO Ladder strategy created for SPY' in result['message']
            
            # Verify the strategy service was called with the right parameters
            mock_strategy_service.execute_strategy.assert_called_once()
            call_args = mock_strategy_service.execute_strategy.call_args[0][0]
            assert call_args['strategy'] == 'oto_ladder'
            assert call_args['symbol'] == 'SPY'
            assert call_args['start_price'] == 450.0
            assert call_args['step'] == 5.0
            assert call_args['initial_shares'] == 100

    def test_command_processor_oto_ladder_command_variations(self):
        """Test the command processor's handling of different OTO Ladder command variations"""
        # Mock the strategy service's execute_strategy method
        with patch.object(self.command_processor, '_get_strategy_service') as mock_get_service:
            mock_strategy_service = MagicMock()
            mock_strategy_service.execute_strategy.return_value = {
                'success': True,
                'strategy': {
                    'symbol': 'AAPL',
                    'start_price': 200.0,
                    'step': 10.0,
                    'initial_shares': 500,
                    'oto_ladder_file': '/path/to/oto_ladder.ts'
                }
            }
            mock_get_service.return_value = mock_strategy_service
            
            # Test with different command variations
            variations = [
                "create oto ladder for AAPL starting at $200 with $10 steps and 500 initial shares",
                "start oto ladder strategy for AAPL $200 with $10 steps and 500 shares",
                "generate oto ladder for AAPL starting at 200 with 10 steps and 500 shares"
            ]
            
            for cmd in variations:
                result = self.command_processor.process_command(cmd)
                
                # Verify the result
                assert result['success'] is True
                assert 'OTO Ladder strategy created for AAPL' in result['message']
                
                # Verify the strategy service was called with the right parameters
                call_args = mock_strategy_service.execute_strategy.call_args[0][0]
                assert call_args['strategy'] == 'oto_ladder'
                assert call_args['symbol'] == 'AAPL'
                assert call_args['start_price'] == 200.0
                assert call_args['step'] == 10.0
                assert call_args['initial_shares'] == 500 