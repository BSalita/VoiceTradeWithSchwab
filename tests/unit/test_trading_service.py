"""
Unit tests for the TradingService in mock mode
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.trading_service import TradingService
from app.api.schwab_client import SchwabAPIClient
from app.models.order import OrderType, OrderSide, OrderStatus, OrderDuration, TradingSession
from app.services.service_registry import ServiceRegistry


class TestTradingService:
    """Test the TradingService with mock mode"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create a mock API client
        self.api_client = SchwabAPIClient()
        
        # Create the trading service with the mock client
        self.trading_service = TradingService(api_client=self.api_client)
        
        # Register the service
        ServiceRegistry.register("trading", self.trading_service)

    def test_place_order(self):
        """Test placing an order through the trading service"""
        # Place an order
        order_result = self.trading_service.place_order(
            symbol="AAPL",
            quantity=5,
            side="BUY",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY",
            strategy="test_strategy"
        )
        
        # Verify the order result
        assert "order_id" in order_result
        assert order_result["status"] == "SUBMITTED"
        assert order_result["symbol"] == "AAPL"
        assert order_result["quantity"] == 5
        assert order_result["side"] == "BUY"
        
        # Verify the order was stored in the mock client
        order_id = order_result["order_id"]
        assert order_id in self.api_client.mock_orders
        
        # Verify strategy was recorded
        assert self.api_client.mock_orders[order_id].get("strategy") == "test_strategy"

    def test_cancel_order(self):
        """Test cancelling an order through the trading service"""
        # Place an order first
        order_result = self.trading_service.place_order(
            symbol="AAPL",
            quantity=5,
            side="BUY",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY"
        )
        
        order_id = order_result["order_id"]
        
        # Cancel the order
        cancel_result = self.trading_service.cancel_order(order_id)
        
        # Verify the cancel result
        assert cancel_result["success"] is True
        assert cancel_result["order_id"] == order_id
        
        # Verify the order status was updated
        assert self.api_client.mock_orders[order_id]["status"] == "CANCELLED"

    def test_get_orders(self):
        """Test getting orders through the trading service"""
        # Place a few orders
        symbols = ["AAPL", "MSFT", "GOOGL"]
        order_ids = []
        
        for symbol in symbols:
            order_result = self.trading_service.place_order(
                symbol=symbol,
                quantity=5,
                side="BUY",
                order_type="MARKET",
                price=None,
                session="REGULAR",
                duration="DAY"
            )
            order_ids.append(order_result["order_id"])
        
        # Get all orders
        orders = self.trading_service.get_orders()
        
        # Verify we got all orders
        assert len(orders) == len(symbols)
        
        # Mark one order as filled
        self.api_client.mock_orders[order_ids[0]]["status"] = "FILLED"
        
        # Get filled orders
        filled_orders = self.trading_service.get_orders(status="FILLED")
        
        # Verify we got only filled orders
        assert len(filled_orders) == 1
        assert filled_orders[0]["order_id"] == order_ids[0]

    def test_get_positions(self):
        """Test getting positions through the trading service"""
        # Place and fill an order
        order_result = self.trading_service.place_order(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="MARKET",
            price=150.0,
            session="REGULAR",
            duration="DAY"
        )
        
        order_id = order_result["order_id"]
        
        # Mark the order as filled
        self.api_client.mock_orders[order_id]["status"] = "FILLED"
        self.api_client.mock_orders[order_id]["filled_quantity"] = 10
        self.api_client.mock_orders[order_id]["filled_price"] = 150.0
        
        # Update paper positions
        self.api_client.paper_positions["AAPL"] = {
            "symbol": "AAPL",
            "quantity": 10,
            "costBasis": 1500.0,
            "currentValue": 1500.0
        }
        
        # Get positions
        positions = self.trading_service.get_positions()
        
        # Verify positions
        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["quantity"] == 10

    def test_get_balances(self):
        """Test getting balances through the trading service"""
        # Get balances
        balances = self.trading_service.get_balances()
        
        # Verify balances
        assert "cash" in balances
        assert "equity" in balances
        assert balances["cash"] >= 0

    @patch('app.services.trading_service.TradeHistory')
    def test_record_trade(self, mock_trade_history):
        """Test recording a trade in history"""
        # Setup mock
        mock_history_instance = MagicMock()
        mock_trade_history.return_value = mock_history_instance
        
        # Place and fill an order
        order_result = self.trading_service.place_order(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="MARKET",
            price=150.0,
            session="REGULAR",
            duration="DAY",
            strategy="test_strategy"
        )
        
        order_id = order_result["order_id"]
        
        # Mark the order as filled
        self.api_client.mock_orders[order_id]["status"] = "FILLED"
        self.api_client.mock_orders[order_id]["filled_quantity"] = 10
        self.api_client.mock_orders[order_id]["filled_price"] = 150.0
        
        # Record the trade
        self.trading_service.record_trade(
            order_id=order_id,
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="test_strategy"
        )
        
        # Verify trade was recorded
        mock_history_instance.add_trade.assert_called_once()
        call_args = mock_history_instance.add_trade.call_args[1]
        assert call_args["order_id"] == order_id
        assert call_args["symbol"] == "AAPL"
        assert call_args["quantity"] == 10
        assert call_args["price"] == 150.0
        assert call_args["side"] == "BUY"
        assert call_args["strategy"] == "test_strategy" 