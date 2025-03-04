#!/usr/bin/env python3
"""Tests for mock trading functionality."""

import os
import unittest
from unittest import mock
import json
import logging
import random

# Remove path manipulation
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.schwab_client import SchwabAPIClient
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.services.strategy_service import StrategyService
from app.services.service_registry import ServiceRegistry
from app.strategies.highlow_strategy import HighLowStrategy
from app.models.order import Order


def mock_get_quote(self, symbol):
    """
    Mock implementation of get_quote for testing.
    
    Args:
        self: The class instance (SchwabAPIClient)
        symbol (str): The stock symbol to get a quote for
        
    Returns:
        dict: A mock quote response with realistic fields including:
              symbol, bid, ask, last, volume, and timestamp
    """
    # Generate a random price around $150
    base_price = 150.0
    variation = random.uniform(-5.0, 5.0)
    price = base_price + variation
    
    # Create a mock quote response
    return {
        "symbol": symbol,
        "bid": price - 0.1,
        "ask": price + 0.1,
        "last": price,
        "volume": random.randint(1000, 100000),
        "timestamp": "2025-03-03T22:00:00.000Z"
    }


class TestMockTrading(unittest.TestCase):
    """
    Test suite for mock trading functionality.
    
    These tests verify that the mock trading mode correctly simulates
    real trading operations without requiring actual API connections,
    focusing on order placement, cancellation, and retrieval.
    """
    
    def setup_method(self):
        """
        Set up test environment before each test method runs.
        
        This method:
        1. Sets the trading mode to MOCK
        2. Initializes a mock API client
        3. Sets up trading and market data services
        4. Registers services with the ServiceRegistry
        """
        # Set the trading mode to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Create a mock API client
        self.api_client = SchwabAPIClient()
        
        # Create and register services
        self.trading_service = TradingService()
        self.trading_service.api_client = self.api_client
        ServiceRegistry.register("trading", self.trading_service)
        
        self.market_data_service = MarketDataService()
        self.market_data_service.api_client = self.api_client
        ServiceRegistry.register("market_data", self.market_data_service)
        
        self.strategy_service = StrategyService()
        ServiceRegistry.register("strategy", self.strategy_service)
        
        # Apply the mock get_quote patch
        self.get_quote_patcher = mock.patch.object(SchwabAPIClient, 'get_quote', mock_get_quote)
        self.get_quote_patcher.start()
    
    def teardown_method(self):
        """
        Clean up after each test method completes.
        
        This method:
        1. Stops any active mock patches
        2. Clears the ServiceRegistry to prevent test contamination
        3. Ensures the test environment is reset for the next test
        """
        # Stop the mock get_quote patch
        self.get_quote_patcher.stop()
        
        # Clear the service registry
        ServiceRegistry.clear()
    
    def test_place_order(self):
        """Test placing an order in mock mode."""
        # Place an order
        result = self.trading_service.place_order(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY",
            strategy="test_strategy"
        )
        
        # Verify the order was created
        assert "order_id" in result or "orderId" in result
        order_id = result.get("order_id") or result.get("orderId")
        
        # Verify the order is in the mock_orders dictionary
        assert order_id in self.api_client.mock_orders
        
        # Verify the order details
        mock_order = self.api_client.mock_orders[order_id]
        assert mock_order["symbol"] == "AAPL"
        assert mock_order["quantity"] == 10
        assert mock_order["side"] == "BUY"
        assert mock_order.get("strategy") == "test_strategy"
    
    def test_cancel_order(self):
        """Test cancelling an order in mock mode."""
        # Place an order using the trading service
        result = self.trading_service.place_order(
            symbol="MSFT",
            quantity=5,
            side="BUY",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY"
        )
        
        order_id = result.get("order_id") or result.get("orderId")
        
        # Cancel the order
        cancel_result = self.trading_service.cancel_order(order_id)
        print(f"DEBUG: Cancel result: {cancel_result}")
        
        # Verify the cancellation was successful
        assert cancel_result.get("success") is True or cancel_result.get("status") in ["CANCELLED", "CANCELED"]
        
        # Verify the order status was updated to cancelled
        updated_order = self.api_client.mock_orders[order_id]
        print(f"DEBUG: Updated order: {updated_order}")
        assert updated_order["status"] in ["CANCELLED", "CANCELED", "canceled"]
    
    def test_get_orders(self):
        """Test getting orders in mock mode."""
        # Place a few orders
        symbols = ["AAPL", "MSFT", "GOOGL"]
        order_ids = []
        
        for symbol in symbols:
            result = self.trading_service.place_order(
                symbol=symbol,
                quantity=5,
                side="BUY",
                order_type="MARKET",
                price=None,
                session="REGULAR",
                duration="DAY"
            )
            order_id = result.get("order_id") or result.get("orderId")
            order_ids.append(order_id)
        
        # Get all orders
        orders = self.trading_service.get_orders()
        
        # Verify we got all orders
        assert len(orders) >= len(symbols)
        
        # Mark one order as filled
        self.api_client.mock_orders[order_ids[0]]["status"] = "FILLED"
        
        # Get filled orders
        filled_orders = self.trading_service.get_orders(status="FILLED")
        
        # Verify we got only filled orders
        assert len(filled_orders) >= 1
        
        # Find our filled order
        found = False
        for order in filled_orders:
            order_id = order.get("order_id") or order.get("orderId")
            if order_id == order_ids[0]:
                found = True
                break
        
        assert found, "Could not find our filled order"
    
    def test_get_quote(self):
        """Test getting a quote in mock mode."""
        # Get a quote
        quote_result = self.market_data_service.get_quote("AAPL")
        print(f"DEBUG: Quote result: {quote_result}")
        
        # Verify the quote contains expected fields
        assert "success" in quote_result
        assert quote_result["success"] is True
        assert "symbol" in quote_result
        assert quote_result["symbol"] == "AAPL"
        
        # Check for the nested quote data
        assert "quote" in quote_result
        quote_data = quote_result["quote"]
        assert "symbol" in quote_data
        assert quote_data["symbol"] == "AAPL"
        assert "bid" in quote_data
        assert "ask" in quote_data
        assert "last" in quote_data
    
    def test_highlow_strategy(self):
        """Test the HighLowStrategy in mock mode."""
        # Create a HighLowStrategy
        strategy = HighLowStrategy(
            symbol="AAPL",
            quantity=10,
            high_threshold=155.0,  # Set high to trigger sell
            low_threshold=145.0    # Set low to trigger buy
        )
        
        # Register the strategy
        self.strategy_service.register_strategy("test_highlow", strategy)
        
        # Mock a low price to trigger buy
        with mock.patch.object(SchwabAPIClient, 'get_quote', lambda self, symbol: {
            "symbol": symbol,
            "bid": 144.0,
            "ask": 144.2,
            "last": 144.1
        }):
            # Execute the strategy
            self.strategy_service.execute_strategy("test_highlow")
            
            # Verify an order was placed
            orders = self.trading_service.get_orders()
            
            # Find a BUY order for AAPL
            buy_order = None
            for order in orders:
                if (order.get("symbol") == "AAPL" and 
                    order.get("side") == "BUY" and 
                    order.get("strategy") == "highlow"):
                    buy_order = order
                    break
            
            assert buy_order is not None, "No BUY order was placed"
        
        # Mock a high price to trigger sell
        with mock.patch.object(SchwabAPIClient, 'get_quote', lambda self, symbol: {
            "symbol": symbol,
            "bid": 156.0,
            "ask": 156.2,
            "last": 156.1
        }):
            # Execute the strategy again
            self.strategy_service.execute_strategy("test_highlow")
            
            # Verify another order was placed
            orders = self.trading_service.get_orders()
            
            # Find a SELL order for AAPL
            sell_order = None
            for order in orders:
                if (order.get("symbol") == "AAPL" and 
                    order.get("side") == "SELL" and 
                    order.get("strategy") == "highlow"):
                    sell_order = order
                    break
            
            assert sell_order is not None, "No SELL order was placed"


if __name__ == "__main__":
    """
    Main test runner for mock trading tests.
    
    When this file is executed directly, this block runs a series of tests
    in sequence, with detailed output for each test. This provides a lightweight
    alternative to using unittest's test runner, and allows for custom sequencing
    and reporting of test execution.
    """
    # Run the tests
    test = TestMockTrading()
    
    try:
        test.setup_method()
        
        print("\n===== Running Mock Trading Tests =====\n")
        
        print("Running test_place_order...")
        test.test_place_order()
        print("✓ test_place_order passed")
        
        print("\nRunning test_cancel_order...")
        test.test_cancel_order()
        print("✓ test_cancel_order passed")
        
        print("\nRunning test_get_orders...")
        test.test_get_orders()
        print("✓ test_get_orders passed")
        
        print("\nRunning test_get_quote...")
        test.test_get_quote()
        print("✓ test_get_quote passed")
        
        print("\nRunning test_highlow_strategy...")
        test.test_highlow_strategy()
        print("✓ test_highlow_strategy passed")
        
        print("\n===== All tests passed! =====")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test.teardown_method() 