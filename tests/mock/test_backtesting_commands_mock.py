"""
Mock tests for backtesting commands
"""

import pytest
from unittest.mock import patch, MagicMock
import datetime
from app.commands.command_processor import CommandProcessor
from app.models.backtest_result import BacktestResult
from app.models.order import TradingSession

class TestBacktestingCommandsMock:
    """Test backtesting commands in mock mode"""

    def setup_method(self):
        """Set up the test environment"""
        # Create a mock command processor
        self.command_processor = CommandProcessor()
        
        # Create a mock backtesting service with the run_backtest method properly mocked
        self.mock_backtesting_service = MagicMock()
        
        # Set up the command processor to use our mock services
        self.command_processor.backtesting_service = self.mock_backtesting_service
        
        # Create a patch for backtesting service get method in ServiceRegistry
        self.registry_get_patcher = patch('app.services.service_registry.ServiceRegistry.get')
        self.mock_registry_get = self.registry_get_patcher.start()
        
        # Make ServiceRegistry.get return our mock backtesting service when asked for 'backtesting'
        def service_registry_side_effect(service_name):
            if service_name == 'backtesting':
                return self.mock_backtesting_service
            return None
            
        self.mock_registry_get.side_effect = service_registry_side_effect
        
        # Patch the _get_backtesting_service method to return our mock
        self.get_backtesting_service_patcher = patch.object(
            self.command_processor, '_get_backtesting_service', return_value=self.mock_backtesting_service
        )
        self.mock_get_backtesting_service = self.get_backtesting_service_patcher.start()
        
        # Set up mock validate_symbol to always return True
        self.validate_symbol_patcher = patch.object(
            self.command_processor, '_validate_symbol', return_value=True
        )
        self.mock_validate_symbol = self.validate_symbol_patcher.start()
        
    def teardown_method(self):
        """Clean up after each test"""
        self.validate_symbol_patcher.stop()
        self.registry_get_patcher.stop()
        self.get_backtesting_service_patcher.stop()
        
    def test_backtest_command_parse(self):
        """Test parsing of backtest command"""
        # Test simple backtest command
        command_text = "backtest ladder on AAPL from 2023-01-01 to 2023-06-30"
        command_type, command_data = self.command_processor._parse_command(command_text)
        
        assert command_type == "backtest"
        assert command_data["strategy_name"] == "ladder"
        assert command_data["symbol"] == "AAPL"
        assert command_data["start_date"] == "2023-01-01"
        assert command_data["end_date"] == "2023-06-30"
        assert command_data["initial_capital"] == 10000.0  # Default
        
        # Test backtest command with capital
        command_text = "backtest oscillating on SPY from 2023-01-01 to 2023-12-31 with initial capital $50000"
        command_type, command_data = self.command_processor._parse_command(command_text)
        
        assert command_type == "backtest"
        assert command_data["strategy_name"] == "oscillating"
        assert command_data["symbol"] == "SPY"
        assert command_data["start_date"] == "2023-01-01"
        assert command_data["end_date"] == "2023-12-31"
        assert command_data["initial_capital"] == 50000.0
        
    def test_compare_strategies_command_parse(self):
        """Test parsing of compare strategies command"""
        # Test simple compare command
        command_text = "compare strategies ladder,oscillating on AAPL from 2023-01-01 to 2023-12-31"
        command_type, command_data = self.command_processor._parse_command(command_text)
        
        assert command_type == "compare_strategies"
        assert command_data["strategies"] == ["ladder", "oscillating"]
        assert command_data["symbol"] == "AAPL"
        assert command_data["start_date"] == "2023-01-01"
        assert command_data["end_date"] == "2023-12-31"
        assert command_data["initial_capital"] == 10000.0  # Default
        
        # Test compare command with capital
        command_text = "compare strategies ladder,oto_ladder on MSFT from 2023-01-01 to 2023-12-31 with initial capital $25000"
        command_type, command_data = self.command_processor._parse_command(command_text)
        
        assert command_type == "compare_strategies"
        assert command_data["strategies"] == ["ladder", "oto_ladder"]
        assert command_data["symbol"] == "MSFT"
        assert command_data["start_date"] == "2023-01-01"
        assert command_data["end_date"] == "2023-12-31"
        assert command_data["initial_capital"] == 25000.0
        
    def test_backtest_execution(self):
        """Test execution of backtest command"""
        # Create a mock backtest result
        mock_result = BacktestResult(
            backtest_id="test_backtest",
            success=True,
            strategy_name="ladder",
            symbol="AAPL",
            start_date=datetime.datetime(2023, 1, 1),
            end_date=datetime.datetime(2023, 6, 30),
            initial_capital=10000.0,
            final_capital=12000.0,
            total_return=20.0,
            max_drawdown=5.0,
            sharpe_ratio=1.5,
            metrics={
                "win_rate": 60.0,
                "average_win": 500.0,
                "average_loss": -300.0,
                "profit_factor": 2.0,
                "expectancy": 150.0,
                "total_trades": 10,
                "winning_trades": 6,
                "losing_trades": 4
            },
            trades=[
                {
                    "id": "test_trade_1",
                    "symbol": "AAPL",
                    "side": "BUY",
                    "quantity": 10,
                    "price": 150.0,
                    "value": 1500.0,
                    "timestamp": "2023-01-02T10:00:00Z"
                },
                {
                    "id": "test_trade_2",
                    "symbol": "AAPL",
                    "side": "SELL",
                    "quantity": 10,
                    "price": 160.0,
                    "value": 1600.0,
                    "timestamp": "2023-01-05T14:30:00Z"
                }
            ]
        )
        
        # Set up mock backtesting service to return the mock result
        self.mock_backtesting_service.run_backtest.return_value = mock_result
        
        # Execute the command
        command_text = "backtest ladder on AAPL from 2023-01-01 to 2023-06-30"
        result = self.command_processor.process_command(command_text)
        
        # Verify the command was processed successfully
        assert result["success"] is True
        assert "Backtest for ladder on AAPL completed successfully" in result["message"]
        
        # Verify backtesting_service.run_backtest was called with correct parameters
        self.mock_backtesting_service.run_backtest.assert_called_once_with(
            strategy_name="ladder",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-06-30",
            initial_capital=10000.0,
            trading_session=TradingSession.REGULAR
        )
        
    def test_compare_strategies_execution(self):
        """Test execution of compare strategies command"""
        # Create mock backtest results
        mock_ladder_result = BacktestResult(
            backtest_id="test_ladder",
            success=True,
            strategy_name="ladder",
            symbol="AAPL",
            start_date=datetime.datetime(2023, 1, 1),
            end_date=datetime.datetime(2023, 12, 31),
            initial_capital=10000.0,
            final_capital=12000.0,
            total_return=20.0,
            max_drawdown=5.0,
            sharpe_ratio=1.5,
            metrics={
                "win_rate": 60.0,
                "average_win": 500.0,
                "average_loss": -300.0,
                "profit_factor": 2.0,
                "total_trades": 10
            }
        )
        
        mock_oscillating_result = BacktestResult(
            backtest_id="test_oscillating",
            success=True,
            strategy_name="oscillating",
            symbol="AAPL",
            start_date=datetime.datetime(2023, 1, 1),
            end_date=datetime.datetime(2023, 12, 31),
            initial_capital=10000.0,
            final_capital=11500.0,
            total_return=15.0,
            max_drawdown=4.0,
            sharpe_ratio=1.8,
            metrics={
                "win_rate": 70.0,
                "average_win": 300.0,
                "average_loss": -200.0,
                "profit_factor": 2.5,
                "total_trades": 20
            }
        )
        
        # Set up mock compare_strategies to return results
        self.mock_backtesting_service.compare_strategies.return_value = {
            "results": {
                "ladder": mock_ladder_result,
                "oscillating": mock_oscillating_result
            },
            "metrics_comparison": {
                "ladder": {
                    "total_return": 20.0,
                    "max_drawdown": 5.0,
                    "sharpe_ratio": 1.5,
                    "win_rate": 60.0,
                    "profit_factor": 2.0,
                    "total_trades": 10
                },
                "oscillating": {
                    "total_return": 15.0,
                    "max_drawdown": 4.0,
                    "sharpe_ratio": 1.8,
                    "win_rate": 70.0,
                    "profit_factor": 2.5,
                    "total_trades": 20
                }
            },
            "metric_rankings": {
                "total_return": {"ladder": 1, "oscillating": 2},
                "max_drawdown": {"oscillating": 1, "ladder": 2},
                "sharpe_ratio": {"oscillating": 1, "ladder": 2},
                "win_rate": {"oscillating": 1, "ladder": 2},
                "profit_factor": {"oscillating": 1, "ladder": 2}
            },
            "overall_ranking": ["oscillating", "ladder"],
            "best_strategy": "oscillating"
        }
        
        # Execute the command
        command_text = "compare strategies ladder,oscillating on AAPL from 2023-01-01 to 2023-12-31"
        result = self.command_processor.process_command(command_text)
        
        # Verify the command was processed successfully
        assert result["success"] is True
        assert "Strategy comparison for AAPL completed successfully" in result["message"]
        
        # Verify backtesting_service.compare_strategies was called with correct parameters
        self.mock_backtesting_service.compare_strategies.assert_called_once_with(
            strategies=["ladder", "oscillating"],
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=10000.0,
            trading_session=TradingSession.REGULAR
        )
        
    def test_backtest_error_handling(self):
        """Test error handling in backtest command"""
        # Test with invalid symbol
        self.mock_validate_symbol.return_value = False
        
        # Set up the backtesting service to return an error for an invalid symbol
        self.mock_backtesting_service.run_backtest.return_value = BacktestResult(
            backtest_id="error_test",
            success=False,
            strategy_name="ladder",
            symbol="INVALID_SYMBOL",
            start_date=datetime.datetime(2023, 1, 1),
            end_date=datetime.datetime(2023, 6, 30),
            initial_capital=10000.0,
            final_capital=10000.0,
            total_return=0.0,
            error="Invalid symbol: INVALID_SYMBOL"
        )

        # Execute the command
        command_text = "backtest ladder on INVALID_SYMBOL from 2023-01-01 to 2023-06-30"
        
        # Patch the _parse_command method to extract the proper symbol
        with patch.object(self.command_processor, '_parse_command') as mock_parse:
            mock_parse.return_value = ("backtest", {
                "strategy_name": "ladder", 
                "symbol": "INVALID_SYMBOL",
                "start_date": "2023-01-01",
                "end_date": "2023-06-30",
                "initial_capital": 10000.0
            })
            
            result = self.command_processor.process_command(command_text)
        
        # Verify the error response
        assert result["success"] is False
        assert "Invalid symbol" in result["error"] 