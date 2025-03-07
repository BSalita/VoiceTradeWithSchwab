"""
Unit tests for the BacktestingService class.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.services.backtesting_service import BacktestingService
from app.models.backtest_result import BacktestResult
from app.models.order import TradingSession

class TestBacktestingService:
    """Test suite for the BacktestingService class"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create a mock API client
        self.api_client = MagicMock()
        
        # Create backtesting service
        self.backtesting_service = BacktestingService()
        self.backtesting_service.api_client = self.api_client
        
        # Create a mock market data service
        self.mock_market_data_service = MagicMock()
        self.backtesting_service.market_data_service = self.mock_market_data_service
        
        # Create a proper mock for app.strategies
        self.strategies_patcher = patch('app.services.backtesting_service.strategies_create_strategy')
        self.mock_create_strategy = self.strategies_patcher.start()
        
        # Create a proper mock for a common strategy to handle tests
        self.mock_strategy = MagicMock()
        self.mock_strategy.execute.return_value = {
            "success": True,
            "orders": [
                {
                    "side": "BUY",
                    "quantity": 10,
                    "order_type": "MARKET"
                }
            ]
        }
        self.mock_create_strategy.return_value = self.mock_strategy
        
        # Sample historical data for testing
        self.historical_data = [
            {
                "timestamp": "2023-01-01T00:00:00Z",
                "open": 150.0,
                "high": 155.0,
                "low": 149.0,
                "close": 153.0,
                "volume": 10000000
            },
            {
                "timestamp": "2023-01-02T00:00:00Z",
                "open": 153.0,
                "high": 158.0,
                "low": 152.0,
                "close": 157.0,
                "volume": 12000000
            },
            {
                "timestamp": "2023-01-03T00:00:00Z",
                "open": 157.0,
                "high": 160.0,
                "low": 155.0,
                "close": 159.0,
                "volume": 11000000
            },
            {
                "timestamp": "2023-01-04T00:00:00Z",
                "open": 159.0,
                "high": 162.0,
                "low": 158.0,
                "close": 160.0,
                "volume": 10500000
            },
            {
                "timestamp": "2023-01-05T00:00:00Z",
                "open": 160.0,
                "high": 165.0,
                "low": 159.0,
                "close": 164.0,
                "volume": 13000000
            }
        ]
        
        # Set up mock to return historical data
        self.mock_market_data_service.get_historical_data.return_value = self.historical_data
        
    def teardown_method(self):
        """Clean up after each test"""
        self.strategies_patcher.stop()

    def test_initialization(self):
        """Test that the BacktestingService initializes correctly"""
        assert self.backtesting_service is not None
        assert hasattr(self.backtesting_service, 'api_client')
        assert hasattr(self.backtesting_service, 'market_data_service')
        assert hasattr(self.backtesting_service, 'backtest_history')
        
    def test_get_historical_data(self):
        """Test that the BacktestingService gets historical data correctly"""
        # Set up mock to return historical data
        self.mock_market_data_service.get_historical_data.return_value = self.historical_data
        
        # Call the method
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 5)
        result = self.backtesting_service._get_historical_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            trading_session=TradingSession.REGULAR
        )
        
        # Verify that market_data_service.get_historical_data was called correctly
        self.mock_market_data_service.get_historical_data.assert_called_once()
        
        # Verify result
        assert len(result) == 5
        assert result[0]["timestamp"] == "2023-01-01T00:00:00Z"
        assert result[4]["timestamp"] == "2023-01-05T00:00:00Z"
        
    @patch('app.strategies.get_strategy')
    @patch('app.services.backtesting_service.strategies_create_strategy')
    def test_run_backtest(self, mock_create_strategy, mock_get_strategy):
        """Test running a backtest"""
        # Create a mock strategy
        mock_strategy = MagicMock()
        mock_strategy.execute.return_value = {
            "success": True,
            "orders": [
                {
                    "side": "BUY",
                    "quantity": 10,
                    "order_type": "MARKET"
                }
            ]
        }
        mock_create_strategy.return_value = mock_strategy
        
        # Set up mock to return historical data
        self.mock_market_data_service.get_historical_data.return_value = self.historical_data
        
        # Call the method
        result = self.backtesting_service.run_backtest(
            strategy_name="ladder",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-05",
            initial_capital=10000.0,
            trading_session=TradingSession.REGULAR
        )
        
        # Verify that create_strategy and get_historical_data were called correctly
        mock_create_strategy.assert_called_once_with("ladder")
        self.mock_market_data_service.get_historical_data.assert_called_once()
        
        # Verify result
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == "ladder"
        assert result.symbol == "AAPL"
        assert result.initial_capital == 10000.0
        assert result.success is True
        
    def test_run_backtest_no_data(self):
        """Test running a backtest with no historical data"""
        # Set up mock to return empty historical data
        self.mock_market_data_service.get_historical_data.return_value = []
        
        # Call the method
        result = self.backtesting_service.run_backtest(
            strategy_name="ladder",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-05",
            initial_capital=10000.0,
            trading_session=TradingSession.REGULAR
        )
        
        # Verify result
        assert isinstance(result, BacktestResult)
        assert result.success is False
        assert result.error == "No historical data available"
        
    @patch('app.services.backtesting_service.strategies_create_strategy')
    def test_run_backtest_strategy_not_found(self, mock_create_strategy):
        """Test running a backtest with a strategy that doesn't exist"""
        # Set up mock to return None for strategy
        mock_create_strategy.return_value = None
        
        # Call the method
        result = self.backtesting_service.run_backtest(
            strategy_name="nonexistent_strategy",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-05",
            initial_capital=10000.0,
            trading_session=TradingSession.REGULAR
        )
        
        # Verify result
        assert isinstance(result, BacktestResult)
        assert result.success is False
        assert "Strategy nonexistent_strategy not found" in result.error
        
    def test_backtest_history(self):
        """Test that backtest history is properly tracked"""
        # Create a mock strategy
        with patch('app.services.backtesting_service.strategies_create_strategy') as mock_create_strategy:
            mock_strategy = MagicMock()
            mock_strategy.execute.return_value = {
                "success": True,
                "orders": []
            }
            mock_create_strategy.return_value = mock_strategy
            
            # Run a couple of backtests
            self.backtesting_service.run_backtest(
                strategy_name="ladder",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-05",
                initial_capital=10000.0,
                trading_session=TradingSession.REGULAR
            )
            
            self.backtesting_service.run_backtest(
                strategy_name="oscillating",
                symbol="MSFT",
                start_date="2023-01-01",
                end_date="2023-01-05",
                initial_capital=10000.0,
                trading_session=TradingSession.REGULAR
            )
            
            # Verify history
            history = self.backtesting_service.get_backtest_history()
            assert len(history) == 2
            
            # Check that each backtest has the correct strategy and symbol
            assert any(b["strategy_name"] == "ladder" and b["symbol"] == "AAPL" for b in history.values())
            assert any(b["strategy_name"] == "oscillating" and b["symbol"] == "MSFT" for b in history.values())
            
    @patch('app.services.backtesting_service.strategies_create_strategy')
    def test_compare_strategies(self, mock_create_strategy):
        """Test comparing multiple strategies"""
        # Create mock strategies
        mock_ladder_strategy = MagicMock()
        mock_ladder_strategy.execute.return_value = {
            "success": True,
            "orders": [
                {
                    "side": "BUY",
                    "quantity": 10,
                    "order_type": "MARKET"
                }
            ]
        }
        
        mock_oscillating_strategy = MagicMock()
        mock_oscillating_strategy.execute.return_value = {
            "success": True,
            "orders": [
                {
                    "side": "BUY",
                    "quantity": 5,
                    "order_type": "MARKET"
                },
                {
                    "side": "SELL",
                    "quantity": 5,
                    "order_type": "MARKET"
                }
            ]
        }
        
        # Set up mock to return the appropriate strategy based on the name
        def side_effect(strategy_name):
            if strategy_name == "ladder":
                return mock_ladder_strategy
            elif strategy_name == "oscillating":
                return mock_oscillating_strategy
            return None
        
        mock_create_strategy.side_effect = side_effect
        
        # Call the method
        result = self.backtesting_service.compare_strategies(
            strategies=["ladder", "oscillating"],
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-05",
            initial_capital=10000.0,
            trading_session=TradingSession.REGULAR
        )
        
        # Verify that create_strategy was called with each strategy name
        assert mock_create_strategy.call_count == 2
        
        # Verify result structure
        assert "results" in result
        assert "metrics_comparison" in result
        assert "metric_rankings" in result
        assert "overall_ranking" in result
        assert "best_strategy" in result
        
        # Verify results for each strategy
        assert "ladder" in result["results"]
        assert "oscillating" in result["results"]
        
    def test_clear_history(self):
        """Test clearing the backtest history"""
        # Create a mock strategy
        with patch('app.strategies.create_strategy') as mock_create_strategy:
            mock_strategy = MagicMock()
            mock_strategy.execute.return_value = {
                "success": True,
                "orders": []
            }
            mock_create_strategy.return_value = mock_strategy
            
            # Run a backtest
            self.backtesting_service.run_backtest(
                strategy_name="ladder",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-05",
                initial_capital=10000.0,
                trading_session=TradingSession.REGULAR
            )
            
            # Verify history has one entry
            history = self.backtesting_service.get_backtest_history()
            assert len(history) == 1
            
            # Clear history
            self.backtesting_service.clear_backtest_history()
            
            # Verify history is empty
            history = self.backtesting_service.get_backtest_history()
            assert len(history) == 0 