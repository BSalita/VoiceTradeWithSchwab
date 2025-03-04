#!/usr/bin/env python3
"""
Integration tests for FastAPI endpoints in mock mode.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient

# Remove path manipulation
# import os
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the FastAPI app
from app.main import app
from app.api.schwab_client import SchwabAPIClient
from app.services.service_registry import ServiceRegistry
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.services.strategy_service import StrategyService


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Set up the API client in mock mode
    api_client = SchwabAPIClient()
    api_client.trading_mode = "MOCK"
    
    # Set up the trading service with the mock API client
    trading_service = TradingService()
    trading_service.api_client = api_client
    ServiceRegistry.register("trading", trading_service)
    
    # Set up the strategy service
    strategy_service = StrategyService()
    ServiceRegistry.register("strategy", strategy_service)
    
    # Create a test client
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_place_order(client):
    """Test placing an order via the API."""
    order_data = {
        "symbol": "AAPL",
        "quantity": 10,
        "side": "BUY",
        "order_type": "MARKET",
        "session": "REGULAR",
        "duration": "DAY"
    }
    
    response = client.post("/orders", json=order_data)
    assert response.status_code == 200
    
    # Verify the response contains an order ID
    response_data = response.json()
    assert "order_id" in response_data or "orderId" in response_data


def test_get_orders(client):
    """Test getting orders via the API."""
    # First place an order
    order_data = {
        "symbol": "MSFT",
        "quantity": 5,
        "side": "BUY",
        "order_type": "MARKET",
        "session": "REGULAR",
        "duration": "DAY"
    }
    
    client.post("/orders", json=order_data)
    
    # Now get all orders
    response = client.get("/orders")
    assert response.status_code == 200
    
    # Verify we got at least one order
    orders = response.json()
    assert len(orders) >= 1


def test_cancel_order(client):
    """Test cancelling an order via the API."""
    # First place an order
    order_data = {
        "symbol": "GOOGL",
        "quantity": 3,
        "side": "BUY",
        "order_type": "MARKET",
        "session": "REGULAR",
        "duration": "DAY"
    }
    
    place_response = client.post("/orders", json=order_data)
    place_data = place_response.json()
    
    # Get the order ID
    order_id = place_data.get("order_id") or place_data.get("orderId")
    
    # Cancel the order
    cancel_response = client.delete(f"/orders/{order_id}")
    assert cancel_response.status_code == 200
    
    # Verify the order was cancelled
    cancel_data = cancel_response.json()
    assert cancel_data.get("success") is True or cancel_data.get("status") in ["CANCELLED", "CANCELED"]


def test_get_quote(client):
    """Test getting a quote via the API."""
    response = client.get("/quotes/AAPL")
    assert response.status_code == 200
    
    # Verify the quote data
    quote = response.json()
    assert quote["symbol"] == "AAPL"
    assert "bid" in quote
    assert "ask" in quote
    assert "last" in quote


def test_execute_strategy(client):
    """Test executing a strategy via the API."""
    # Create a strategy
    strategy_data = {
        "name": "test_strategy",
        "type": "highlow",
        "parameters": {
            "symbol": "AAPL",
            "quantity": 10,
            "high_threshold": 155.0,
            "low_threshold": 145.0
        }
    }
    
    # Register the strategy
    response = client.post("/strategies", json=strategy_data)
    assert response.status_code == 200
    
    # Execute the strategy
    execute_response = client.post(f"/strategies/{strategy_data['name']}/execute")
    assert execute_response.status_code == 200
    
    # Verify the strategy was executed
    execute_data = execute_response.json()
    assert execute_data.get("success") is True


if __name__ == "__main__":
    # Create a test client
    api_client = SchwabAPIClient()
    api_client.trading_mode = "MOCK"
    
    trading_service = TradingService()
    trading_service.api_client = api_client
    ServiceRegistry.register("trading", trading_service)
    
    # Set up the strategy service for manual testing
    strategy_service = StrategyService()
    ServiceRegistry.register("strategy", strategy_service)
    
    test_client = TestClient(app)
    
    try:
        print("Running test_health_check...")
        test_health_check(test_client)
        print("✓ test_health_check passed")
        
        print("Running test_place_order...")
        test_place_order(test_client)
        print("✓ test_place_order passed")
        
        print("Running test_get_orders...")
        test_get_orders(test_client)
        print("✓ test_get_orders passed")
        
        print("Running test_cancel_order...")
        test_cancel_order(test_client)
        print("✓ test_cancel_order passed")
        
        print("Running test_get_quote...")
        test_get_quote(test_client)
        print("✓ test_get_quote passed")
        
        print("Running test_execute_strategy...")
        test_execute_strategy(test_client)
        print("✓ test_execute_strategy passed")
        
        print("All FastAPI endpoint tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        ServiceRegistry.clear() 