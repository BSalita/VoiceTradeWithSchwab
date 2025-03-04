"""
Unit tests for the BasicStrategy in mock mode
"""

import pytest
from unittest.mock import patch, MagicMock

from app.api.schwab_client import SchwabAPIClient
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.strategies.basic_strategy import BasicStrategy
from app.services.service_registry import ServiceRegistry


class TestBasicStrategy:
    """Test the BasicStrategy with mock mode"""

    def setup_method(self):
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
        self.strategy = BasicStrategy()
        # Set the api_client explicitly
        self.strategy.api_client = self.api_client
        
        # Clear any existing mock orders
        self.api_client.mock_orders = {}
    
    def teardown_method(self):
        """Clean up after each test"""
        ServiceRegistry.clear()

    def test_initialization(self):
        """Test that the strategy initializes correctly"""
        assert self.strategy is not None
        assert self.strategy.api_client is not None
        assert self.strategy.strategy_name == "BasicStrategy"

    def test_execute_buy_market_order(self):
        """Test executing a basic buy market order"""
        # Execute the strategy with a market buy
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="MARKET"
        )
        
        # Verify the result
        assert result["success"] is True
        assert "order" in result
        assert result["symbol"] == "AAPL"
        assert result["quantity"] == 10
        assert result["side"] == "BUY"
        assert result["type"] == "MARKET"
        assert result["strategy"] == "BasicStrategy"
        
        # Verify an order was placed
        orders = self.trading_service.get_orders()
        assert len(orders) == 1
        assert orders[0]["symbol"] == "AAPL"
        assert orders[0]["quantity"] == 10
        assert orders[0]["side"] == "BUY"
        assert orders[0]["order_type"] == "MARKET"

    def test_execute_sell_market_order(self):
        """Test executing a basic sell market order"""
        # Clear any existing mock orders
        self.api_client.mock_orders = {}
        
        # Execute the strategy with a market sell
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="SELL",
            order_type="MARKET"
        )
        
        # Verify the result
        assert result["success"] is True
        assert "order" in result
        assert result["symbol"] == "AAPL"
        assert result["quantity"] == 10
        assert result["side"] == "SELL"
        assert result["type"] == "MARKET"
        
        # Verify an order was placed
        orders = self.trading_service.get_orders()
        assert len(orders) == 1
        assert orders[0]["symbol"] == "AAPL"
        assert orders[0]["quantity"] == 10
        assert orders[0]["side"] == "SELL"
        assert orders[0]["order_type"] == "MARKET"

    def test_execute_limit_order(self):
        """Test executing a basic limit order"""
        # Clear any existing mock orders
        self.api_client.mock_orders = {}
        
        # Execute the strategy with a limit buy
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="LIMIT",
            price=150.0
        )
        
        # Verify the result
        assert result["success"] is True
        assert "order" in result
        assert result["symbol"] == "AAPL"
        assert result["quantity"] == 10
        assert result["side"] == "BUY"
        assert result["type"] == "LIMIT"
        assert result["price"] == 150.0
        
        # Verify an order was placed
        orders = self.trading_service.get_orders()
        assert len(orders) == 1
        assert orders[0]["symbol"] == "AAPL"
        assert orders[0]["quantity"] == 10
        assert orders[0]["side"] == "BUY"
        assert orders[0]["order_type"] == "LIMIT"
        assert orders[0]["price"] == 150.0

    def test_execute_with_invalid_side(self):
        """Test executing with an invalid side"""
        # Try to execute with an invalid side
        with pytest.raises(ValueError, match="Side must be either 'BUY' or 'SELL'"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=10,
                side="INVALID",
                order_type="MARKET"
            )

    def test_execute_with_invalid_order_type(self):
        """Test executing with an invalid order type"""
        # Try to execute with an invalid order type
        with pytest.raises(ValueError, match="Unsupported order type"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=10,
                side="BUY",
                order_type="INVALID"
            )

    def test_execute_limit_order_without_price(self):
        """Test executing a limit order without a price"""
        # Try to execute a limit order without a price
        with pytest.raises(ValueError, match="Price is required for non-market orders"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=10,
                side="BUY",
                order_type="LIMIT",
                price=None
            )

    def test_execute_with_zero_quantity(self):
        """Test executing with zero quantity"""
        # Try to execute with zero quantity
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=0,
                side="BUY",
                order_type="MARKET"
            )

    def test_execute_with_negative_quantity(self):
        """Test executing with negative quantity"""
        # Try to execute with negative quantity
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=-10,
                side="BUY",
                order_type="MARKET"
            )

    def test_execute_with_empty_symbol(self):
        """Test executing with empty symbol"""
        # Try to execute with empty symbol
        with pytest.raises(ValueError, match="Symbol is required"):
            self.strategy.execute(
                symbol="",
                quantity=10,
                side="BUY",
                order_type="MARKET"
            )

    @patch('app.api.schwab_client.SchwabAPIClient.place_order')
    def test_execute_handles_api_error(self, mock_place_order):
        """Test that the strategy handles API errors gracefully"""
        # Mock the API to raise an exception
        mock_place_order.side_effect = Exception("API error")
        
        # Execute the strategy
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="MARKET"
        )
        
        # Verify the result
        assert result["success"] is False
        assert "error" in result
        assert "API error" in result["error"]
        assert result["symbol"] == "AAPL"
        assert result["quantity"] == 10
        assert result["side"] == "BUY"
        assert result["type"] == "MARKET"

    @patch('app.api.schwab_client.SchwabAPIClient.get_quote')
    def test_execute_with_quote_data(self, mock_get_quote):
        """Test executing with market data"""
        # Mock the quote
        mock_get_quote.return_value = {
            "symbol": "AAPL",
            "lastPrice": 152.37,
            "bid": 152.35,
            "ask": 152.40,
            "volume": 25000000
        }
        
        # Execute the strategy
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="MARKET"
        )
        
        # Verify the quote data was included
        assert result["success"] is True
        assert result["market_price"] == 152.37


if __name__ == "__main__":
    # Run the tests
    test = TestBasicStrategy()
    
    try:
        test.setup_method()
        
        print("Running test_initialization...")
        test.test_initialization()
        print("✅ test_initialization passed")
        
        print("Running test_execute_buy_market_order...")
        test.test_execute_buy_market_order()
        print("✅ test_execute_buy_market_order passed")
        
        print("Running test_execute_sell_market_order...")
        test.test_execute_sell_market_order()
        print("✅ test_execute_sell_market_order passed")
        
        print("Running test_execute_limit_order...")
        test.test_execute_limit_order()
        print("✅ test_execute_limit_order passed")
        
        print("All basic strategy tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test.teardown_method() 