"""
Unit tests for the StrategyService in mock mode
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.strategy_service import StrategyService
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.api.schwab_client import SchwabAPIClient
from app.strategies.highlow_strategy import HighLowStrategy
from app.strategies.oscillating_strategy import OscillatingStrategy
from app.services.service_registry import ServiceRegistry


class TestStrategyService:
    """Test the StrategyService with mock mode"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create a mock API client
        self.api_client = SchwabAPIClient()
        
        # Create and register the trading service
        self.trading_service = TradingService(api_client=self.api_client)
        ServiceRegistry.register("trading", self.trading_service)
        
        # Create and register the market data service
        self.market_data_service = MarketDataService(api_client=self.api_client)
        ServiceRegistry.register("market_data", self.market_data_service)
        
        # Create the strategy service
        self.strategy_service = StrategyService()
        ServiceRegistry.register("strategy", self.strategy_service)

    def test_register_strategy(self):
        """Test registering a strategy"""
        # Create a strategy
        strategy = HighLowStrategy(
            symbol="AAPL",
            quantity=10,
            high_threshold=150.0,
            low_threshold=140.0
        )
        
        # Register the strategy
        self.strategy_service.register_strategy("test_highlow", strategy)
        
        # Verify the strategy was registered
        assert "test_highlow" in self.strategy_service.strategies
        assert self.strategy_service.strategies["test_highlow"] == strategy

    def test_get_strategy(self):
        """Test getting a registered strategy"""
        # Create and register a strategy
        strategy = HighLowStrategy(
            symbol="AAPL",
            quantity=10,
            high_threshold=150.0,
            low_threshold=140.0
        )
        
        self.strategy_service.register_strategy("test_highlow", strategy)
        
        # Get the strategy
        retrieved_strategy = self.strategy_service.get_strategy("test_highlow")
        
        # Verify the strategy
        assert retrieved_strategy == strategy

    def test_list_strategies(self):
        """Test listing all registered strategies"""
        # Create and register multiple strategies
        highlow_strategy = HighLowStrategy(
            symbol="AAPL",
            quantity=10,
            high_threshold=150.0,
            low_threshold=140.0
        )
        
        oscillating_strategy = OscillatingStrategy(
            symbol="MSFT",
            quantity=5,
            upper_limit=200.0,
            lower_limit=190.0,
            step_size=1.0
        )
        
        self.strategy_service.register_strategy("test_highlow", highlow_strategy)
        self.strategy_service.register_strategy("test_oscillating", oscillating_strategy)
        
        # List strategies
        strategies = self.strategy_service.list_strategies()
        
        # Verify the strategies
        assert len(strategies) == 2
        assert "test_highlow" in strategies
        assert "test_oscillating" in strategies

    def test_remove_strategy(self):
        """Test removing a registered strategy"""
        # Create and register a strategy
        strategy = HighLowStrategy(
            symbol="AAPL",
            quantity=10,
            high_threshold=150.0,
            low_threshold=140.0
        )
        
        self.strategy_service.register_strategy("test_highlow", strategy)
        
        # Remove the strategy
        self.strategy_service.remove_strategy("test_highlow")
        
        # Verify the strategy was removed
        assert "test_highlow" not in self.strategy_service.strategies

    @patch('app.strategies.highlow_strategy.HighLowStrategy.execute')
    def test_execute_strategy(self, mock_execute):
        """Test executing a strategy"""
        # Create and register a strategy
        strategy = HighLowStrategy(
            symbol="AAPL",
            quantity=10,
            high_threshold=150.0,
            low_threshold=140.0
        )
        
        self.strategy_service.register_strategy("test_highlow", strategy)
        
        # Execute the strategy
        self.strategy_service.execute_strategy("test_highlow")
        
        # Verify the strategy's execute method was called
        mock_execute.assert_called_once()

    @patch('app.strategies.highlow_strategy.HighLowStrategy.execute')
    def test_execute_all_strategies(self, mock_execute):
        """Test executing all registered strategies"""
        # Create and register multiple strategies
        highlow_strategy = HighLowStrategy(
            symbol="AAPL",
            quantity=10,
            high_threshold=150.0,
            low_threshold=140.0
        )
        
        oscillating_strategy = OscillatingStrategy(
            symbol="MSFT",
            quantity=5,
            upper_limit=200.0,
            lower_limit=190.0,
            step_size=1.0
        )
        
        self.strategy_service.register_strategy("test_highlow", highlow_strategy)
        self.strategy_service.register_strategy("test_oscillating", oscillating_strategy)
        
        # Mock the oscillating strategy's execute method
        with patch('app.strategies.oscillating_strategy.OscillatingStrategy.execute') as mock_oscillating_execute:
            # Execute all strategies
            self.strategy_service.execute_all_strategies()
            
            # Verify both strategies' execute methods were called
            mock_execute.assert_called_once()
            mock_oscillating_execute.assert_called_once()

    def test_highlow_strategy_integration(self):
        """Test the HighLowStrategy integration with mock mode"""
        # Create a HighLowStrategy
        strategy = HighLowStrategy(
            symbol="AAPL",
            quantity=10,
            high_threshold=150.0,
            low_threshold=140.0
        )
        
        # Register the strategy
        self.strategy_service.register_strategy("test_highlow", strategy)
        
        # Mock the quote to trigger a buy signal
        with patch.object(self.market_data_service, 'get_quote', return_value={
            "symbol": "AAPL",
            "bid": 139.0,
            "ask": 139.5,
            "last": 139.0
        }):
            # Execute the strategy
            self.strategy_service.execute_strategy("test_highlow")
            
            # Verify an order was placed
            orders = self.trading_service.get_orders()
            assert len(orders) == 1
            assert orders[0]["symbol"] == "AAPL"
            assert orders[0]["side"] == "BUY"
            assert orders[0]["quantity"] == 10
            
            # Mock the quote to trigger a sell signal
            with patch.object(self.market_data_service, 'get_quote', return_value={
                "symbol": "AAPL",
                "bid": 151.0,
                "ask": 151.5,
                "last": 151.0
            }):
                # Execute the strategy again
                self.strategy_service.execute_strategy("test_highlow")
                
                # Verify another order was placed
                orders = self.trading_service.get_orders()
                assert len(orders) == 2
                assert orders[1]["symbol"] == "AAPL"
                assert orders[1]["side"] == "SELL"
                assert orders[1]["quantity"] == 10

    def test_oscillating_strategy_integration(self):
        """Test the OscillatingStrategy integration with mock mode"""
        # Create an OscillatingStrategy
        strategy = OscillatingStrategy()
        
        # Configure with proper parameters matching the implementation
        strategy_params = {
            "symbol": "MSFT",
            "quantity": 5,
            "price_range": 0.02,  # 2% price range
            "is_percentage": True,
            "min_trade_interval": 60,
            "max_positions": 3
        }
        
        # Register the strategy
        self.strategy_service.register_strategy("test_oscillating", strategy)
        
        # Mock the quote to be within the oscillating range
        with patch.object(self.market_data_service, 'get_quote', return_value={
            "symbol": "MSFT",
            "bid": 195.0,
            "ask": 195.5,
            "last": 195.0,
            "lastPrice": 195.0
        }):
            # Execute the strategy with correct parameters
            self.strategy_service.execute_strategy("test_oscillating", **strategy_params)
            
            # Verify orders were placed
            orders = self.trading_service.get_orders()
            assert len(orders) > 0
            
            # Verify the strategy name was recorded
            for order in orders:
                if order.get("symbol") == "MSFT":
                    assert order.get("strategy") == "oscillating" 