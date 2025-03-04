"""
Unit tests for the LadderStrategy in mock mode
"""

import pytest
from unittest.mock import patch, MagicMock
import time

from app.api.schwab_client import SchwabAPIClient
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.strategies.ladder_strategy import LadderStrategy
from app.services.service_registry import ServiceRegistry


class TestLadderStrategy:
    """Test the LadderStrategy with mock mode"""

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
        self.strategy = LadderStrategy()
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
        assert self.strategy.strategy_name == "LadderStrategy"
        assert hasattr(self.strategy, "active_ladders")
        assert isinstance(self.strategy.active_ladders, dict)

    def test_execute_buy_ladder(self):
        """Test executing a buy ladder"""
        # Execute the strategy with a buy ladder
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            price_start=145.0,
            price_end=150.0,
            steps=3,
            order_type="LIMIT"
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["strategy"] == "LadderStrategy"
        assert result["symbol"] == "AAPL"
        assert result["quantity"] == 10
        assert result["side"] == "BUY"
        assert result["price_start"] == 145.0
        assert result["price_end"] == 150.0
        assert result["steps"] == 3
        
        # Verify the price points
        assert "price_points" in result
        assert len(result["price_points"]) == 3
        assert result["price_points"] == [145.0, 147.5, 150.0]
        
        # Verify the orders were placed
        assert "orders" in result
        assert len(result["orders"]) == 3
        
        # Verify the orders in the trading service
        orders = self.trading_service.get_orders()
        assert len(orders) == 3
        
        # Verify the prices of the orders
        prices = [order["price"] for order in orders]
        assert 145.0 in prices
        assert 147.5 in prices
        assert 150.0 in prices
        
        # Verify all orders are for the same symbol and quantity
        for order in orders:
            assert order["symbol"] == "AAPL"
            assert order["quantity"] == 10
            assert order["side"] == "BUY"
            assert order["order_type"] == "LIMIT"
        
        # Verify the ladder was tracked
        assert "ladder_id" in result
        assert result["ladder_id"] in self.strategy.active_ladders

    def test_execute_sell_ladder(self):
        """Test executing a sell ladder"""
        # Clear any existing mock orders
        self.api_client.mock_orders = {}
        
        # Execute the strategy with a sell ladder
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="SELL",
            price_start=155.0,
            price_end=150.0,  # For sell, start should be higher than end
            steps=3,
            order_type="LIMIT"
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["strategy"] == "LadderStrategy"
        assert result["symbol"] == "AAPL"
        assert result["quantity"] == 10
        assert result["side"] == "SELL"
        assert result["price_start"] == 155.0
        assert result["price_end"] == 150.0
        assert result["steps"] == 3
        
        # Verify the price points
        assert "price_points" in result
        assert len(result["price_points"]) == 3
        assert result["price_points"] == [155.0, 152.5, 150.0]
        
        # Verify the orders were placed
        assert "orders" in result
        assert len(result["orders"]) == 3
        
        # Verify the orders in the trading service
        orders = self.trading_service.get_orders()
        assert len(orders) == 3
        
        # Verify the prices of the orders
        prices = [order["price"] for order in orders]
        assert 155.0 in prices
        assert 152.5 in prices
        assert 150.0 in prices
        
        # Verify all orders are for the same symbol and quantity
        for order in orders:
            assert order["symbol"] == "AAPL"
            assert order["quantity"] == 10
            assert order["side"] == "SELL"
            assert order["order_type"] == "LIMIT"

    def test_execute_single_step_ladder(self):
        """Test executing a ladder with a single step"""
        # Clear any existing mock orders
        self.api_client.mock_orders = {}
        
        # Execute the strategy with a single step
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            price_start=145.0,
            price_end=150.0,  # For buy, end should be higher than start
            steps=1,
            order_type="LIMIT"
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["strategy"] == "LadderStrategy"
        assert result["steps"] == 1
        
        # Verify the price points
        assert "price_points" in result
        assert len(result["price_points"]) == 1
        assert result["price_points"] == [145.0]
        
        # Verify the orders were placed
        assert "orders" in result
        assert len(result["orders"]) == 1
        
        # Verify the orders in the trading service
        orders = self.trading_service.get_orders()
        assert len(orders) == 1
        assert orders[0]["price"] == 145.0

    def test_cancel_ladder(self):
        """Test cancelling a ladder"""
        # Clear any existing mock orders
        self.api_client.mock_orders = {}
        
        # First execute a ladder
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            price_start=145.0,
            price_end=150.0,
            steps=3,
            order_type="LIMIT"
        )
        
        ladder_id = result["ladder_id"]
        
        # Now cancel the ladder
        cancel_result = self.strategy.cancel_ladder(ladder_id)
        
        # Verify the cancel result
        assert cancel_result["success"] is True
        assert cancel_result["ladder_id"] == ladder_id
        assert cancel_result["orders_cancelled"] == 3
        assert cancel_result["orders_failed"] == 0
        
        # Verify the orders were cancelled (case-insensitive)
        orders = self.trading_service.get_orders()
        for order in orders:
            status = order["status"].upper()
            assert status in ["CANCELLED", "CANCELED"]
        
        # Verify the ladder is marked as inactive
        assert self.strategy.active_ladders[ladder_id]["active"] is False

    def test_get_active_ladders(self):
        """Test getting active ladders"""
        # Clear any existing mock orders
        self.api_client.mock_orders = {}
        
        # Clear any existing active ladders
        self.strategy.active_ladders = {}
        
        # Execute a few ladders
        ladder1 = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            price_start=145.0,
            price_end=150.0,
            steps=3,
            order_type="LIMIT"
        )
        
        ladder2 = self.strategy.execute(
            symbol="MSFT",
            quantity=5,
            side="SELL",
            price_start=250.0,
            price_end=245.0,
            steps=2,
            order_type="LIMIT"
        )
        
        # Get active ladders
        active_ladders = self.strategy.get_active_ladders()
        
        # Verify the active ladders
        assert len(active_ladders) == 2
        assert ladder1["ladder_id"] in active_ladders
        assert ladder2["ladder_id"] in active_ladders
        
        # Verify ladder details
        assert active_ladders[ladder1["ladder_id"]]["symbol"] == "AAPL"
        assert active_ladders[ladder1["ladder_id"]]["side"] == "BUY"
        assert active_ladders[ladder1["ladder_id"]]["steps"] == 3
        
        assert active_ladders[ladder2["ladder_id"]]["symbol"] == "MSFT"
        assert active_ladders[ladder2["ladder_id"]]["side"] == "SELL"
        assert active_ladders[ladder2["ladder_id"]]["steps"] == 2

    def test_execute_with_invalid_side(self):
        """Test executing with an invalid side"""
        # Try to execute with an invalid side
        with pytest.raises(ValueError, match="Side must be either 'BUY' or 'SELL'"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=10,
                side="INVALID",
                price_start=145.0,
                price_end=150.0,
                steps=3,
                order_type="LIMIT"
            )

    def test_execute_with_zero_quantity(self):
        """Test executing with zero quantity"""
        # Try to execute with zero quantity
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=0,
                side="BUY",
                price_start=145.0,
                price_end=150.0,
                steps=3,
                order_type="LIMIT"
            )

    def test_execute_with_zero_steps(self):
        """Test executing with zero steps"""
        # Try to execute with zero steps
        with pytest.raises(ValueError, match="Steps must be greater than 0"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=10,
                side="BUY",
                price_start=145.0,
                price_end=150.0,
                steps=0,
                order_type="LIMIT"
            )

    def test_execute_with_zero_price(self):
        """Test executing with zero price"""
        # Try to execute with zero price
        with pytest.raises(ValueError, match="Prices must be greater than 0"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=10,
                side="BUY",
                price_start=0,
                price_end=150.0,
                steps=3,
                order_type="LIMIT"
            )

    def test_execute_buy_with_invalid_price_range(self):
        """Test executing a buy ladder with invalid price range"""
        # For buy ladders, start should be lower than end
        with pytest.raises(ValueError, match="For buy ladders, start price must be lower than end price"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=10,
                side="BUY",
                price_start=150.0,  # Higher than end
                price_end=145.0,
                steps=3,
                order_type="LIMIT"
            )

    def test_execute_sell_with_invalid_price_range(self):
        """Test executing a sell ladder with invalid price range"""
        # For sell ladders, start should be higher than end
        with pytest.raises(ValueError, match="For sell ladders, start price must be higher than end price"):
            self.strategy.execute(
                symbol="AAPL",
                quantity=10,
                side="SELL",
                price_start=145.0,  # Lower than end
                price_end=150.0,
                steps=3,
                order_type="LIMIT"
            )

    def test_cancel_nonexistent_ladder(self):
        """Test cancelling a ladder that doesn't exist"""
        # Try to cancel a non-existent ladder
        with pytest.raises(ValueError, match="Ladder ID nonexistent_ladder not found"):
            self.strategy.cancel_ladder("nonexistent_ladder")

    @patch('app.api.schwab_client.SchwabAPIClient.place_order')
    def test_execute_with_partial_failure(self, mock_place_order):
        """Test executing a ladder with partial failure"""
        # Make every other order fail
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise Exception("API error")
            else:
                return {"orderId": f"order_{call_count}", "status": "SUBMITTED"}
        
        call_count = 0
        mock_place_order.side_effect = side_effect
        
        # Execute the strategy
        result = self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            price_start=145.0,
            price_end=150.0,
            steps=4,
            order_type="LIMIT"
        )
        
        # Verify the result
        assert result["success"] is True  # Still successful if at least one order succeeds
        assert result["orders_placed"] == 2
        assert result["orders_failed"] == 2
        
        # Verify the orders
        orders = result["orders"]
        assert len(orders) == 4
        
        # Verify the success/failure of each order
        success_count = sum(1 for order in orders if order["success"])
        failure_count = sum(1 for order in orders if not order["success"])
        assert success_count == 2
        assert failure_count == 2

    @patch('time.sleep')
    def test_execute_with_sleep(self, mock_sleep):
        """Test that the strategy adds a delay between orders"""
        # Execute the strategy
        self.strategy.execute(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            price_start=145.0,
            price_end=150.0,
            steps=3,
            order_type="LIMIT"
        )
        
        # Verify that sleep was called between orders
        assert mock_sleep.call_count == 3  # Called after each order


if __name__ == "__main__":
    # Run the tests
    test = TestLadderStrategy()
    
    try:
        test.setup_method()
        
        print("Running test_initialization...")
        test.test_initialization()
        print("✅ test_initialization passed")
        
        print("Running test_execute_buy_ladder...")
        test.test_execute_buy_ladder()
        print("✅ test_execute_buy_ladder passed")
        
        print("Running test_execute_sell_ladder...")
        test.test_execute_sell_ladder()
        print("✅ test_execute_sell_ladder passed")
        
        print("Running test_cancel_ladder...")
        test.test_cancel_ladder()
        print("✅ test_cancel_ladder passed")
        
        print("Running test_get_active_ladders...")
        test.test_get_active_ladders()
        print("✅ test_get_active_ladders passed")
        
        print("All ladder strategy tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test.teardown_method() 