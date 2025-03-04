"""
Unit tests for the SchwabAPIClient in mock mode
"""

import pytest
import os
from unittest.mock import patch

from app.api.schwab_client import SchwabAPIClient
from app.models.order import OrderType, OrderSide, OrderStatus, OrderDuration, TradingSession


class TestSchwabClientMockMode:
    """Test the SchwabAPIClient in mock mode"""

    def test_init_mock_mode(self):
        """Test initialization in mock mode"""
        client = SchwabAPIClient()
        assert client.trading_mode == "MOCK"
        assert hasattr(client, "mock_orders")
        assert isinstance(client.mock_orders, dict)

    def test_place_order_mock_mode(self):
        """Test placing an order in mock mode"""
        client = SchwabAPIClient()
        
        # Place a mock order
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "order_type": "MARKET",
            "side": "BUY",
            "session": "REGULAR",
            "duration": "DAY"
        }
        
        result = client.place_order(order_data)
        
        # Verify the result
        assert "order_id" in result
        assert result["status"] == "SUBMITTED"
        assert result["symbol"] == "AAPL"
        assert result["quantity"] == 10
        assert result["side"] == "BUY"
        
        # Verify the order was stored
        order_id = result["order_id"]
        assert order_id in client.mock_orders

    def test_cancel_order_mock_mode(self):
        """Test cancelling an order in mock mode"""
        client = SchwabAPIClient()
        
        # Place a mock order first
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "order_type": "MARKET",
            "side": "BUY",
            "session": "REGULAR",
            "duration": "DAY"
        }
        
        result = client.place_order(order_data)
        order_id = result["order_id"]
        
        # Cancel the order
        cancel_result = client.cancel_order(order_id)
        
        # Verify the result
        assert cancel_result["success"] is True
        assert cancel_result["order_id"] == order_id
        
        # Verify the order status was updated
        assert client.mock_orders[order_id]["status"] == "CANCELLED"

    def test_get_orders_mock_mode(self):
        """Test getting orders in mock mode"""
        client = SchwabAPIClient()
        
        # Place a few mock orders
        symbols = ["AAPL", "MSFT", "GOOGL"]
        order_ids = []
        
        for symbol in symbols:
            order_data = {
                "symbol": symbol,
                "quantity": 10,
                "order_type": "MARKET",
                "side": "BUY",
                "session": "REGULAR",
                "duration": "DAY"
            }
            
            result = client.place_order(order_data)
            order_ids.append(result["order_id"])
        
        # Get all orders
        orders = client.get_orders()
        
        # Verify we got all orders
        assert len(orders) == len(symbols)
        
        # Get orders with status filter
        client.mock_orders[order_ids[0]]["status"] = "FILLED"
        filled_orders = client.get_orders("FILLED")
        
        # Verify we got only filled orders
        assert len(filled_orders) == 1
        assert filled_orders[0]["order_id"] == order_ids[0]

    def test_get_quote_mock_mode(self):
        """Test getting a quote in mock mode"""
        client = SchwabAPIClient()
        
        # Get a quote
        quote = client.get_quote("AAPL")
        
        # Verify the quote has expected fields
        assert "symbol" in quote
        assert quote["symbol"] == "AAPL"
        assert "bid" in quote
        assert "ask" in quote
        assert "last" in quote

    def test_get_account_info_mock_mode(self):
        """Test getting account info in mock mode"""
        client = SchwabAPIClient()
        
        # Get account info
        account_info = client.get_account_info()
        
        # Verify the account info
        assert "account_id" in account_info
        assert account_info["account_id"] == "mock_account"

    def test_get_account_positions_mock_mode(self):
        """Test getting account positions in mock mode"""
        client = SchwabAPIClient()
        
        # Place an order that will be filled
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "order_type": "MARKET",
            "side": "BUY",
            "session": "REGULAR",
            "duration": "DAY"
        }
        
        result = client.place_order(order_data)
        order_id = result["order_id"]
        
        # Mark the order as filled
        client.mock_orders[order_id]["status"] = "FILLED"
        client.mock_orders[order_id]["filled_quantity"] = 10
        client.mock_orders[order_id]["filled_price"] = 150.0
        
        # Update paper positions
        client.paper_positions["AAPL"] = {
            "symbol": "AAPL",
            "quantity": 10,
            "costBasis": 1500.0,
            "currentValue": 1500.0
        }
        
        # Get positions
        positions = client.get_account_positions()
        
        # Verify positions
        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["quantity"] == 10

    def test_get_account_balances_mock_mode(self):
        """Test getting account balances in mock mode"""
        client = SchwabAPIClient()
        
        # Get balances
        balances = client.get_account_balances()
        
        # Verify balances
        assert "cash" in balances
        assert "equity" in balances
        assert balances["cash"] >= 0

    def test_paper_trading_buy_sell(self):
        """Test paper trading buy and sell flow"""
        client = SchwabAPIClient()
        client.trading_mode = "PAPER"  # Switch to paper mode
        
        # Set initial balance
        initial_balance = 10000.0
        client.paper_balance = initial_balance
        
        # Buy shares
        buy_order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "order_type": "MARKET",
            "side": "BUY",
            "price": 150.0,
            "session": "REGULAR",
            "duration": "DAY"
        }
        
        buy_result = client.place_order(buy_order_data)
        buy_order_id = buy_result["order_id"]
        
        # Verify balance decreased
        expected_cost = 10 * 150.0
        assert client.paper_balance == pytest.approx(initial_balance - expected_cost)
        
        # Verify position was created
        assert "AAPL" in client.paper_positions
        assert client.paper_positions["AAPL"]["quantity"] == 10
        
        # Sell shares
        sell_order_data = {
            "symbol": "AAPL",
            "quantity": 5,
            "order_type": "MARKET",
            "side": "SELL",
            "price": 160.0,
            "session": "REGULAR",
            "duration": "DAY"
        }
        
        sell_result = client.place_order(sell_order_data)
        
        # Verify position was updated
        assert client.paper_positions["AAPL"]["quantity"] == 5
        
        # Verify balance increased
        expected_proceeds = 5 * 160.0
        assert client.paper_balance == pytest.approx(initial_balance - expected_cost + expected_proceeds) 