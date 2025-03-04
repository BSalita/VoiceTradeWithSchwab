"""
Integration tests for the FastAPI endpoints in mock mode
"""

import pytest
from fastapi.testclient import TestClient
import json

from app.interfaces.web import create_fastapi_app
from app.api.schwab_client import SchwabAPIClient
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.services.strategy_service import StrategyService
from app.services.service_registry import ServiceRegistry


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app"""
    # Create a mock API client
    api_client = SchwabAPIClient()
    
    # Create and register services
    trading_service = TradingService(api_client=api_client)
    ServiceRegistry.register("trading", trading_service)
    
    market_data_service = MarketDataService(api_client=api_client)
    ServiceRegistry.register("market_data", market_data_service)
    
    strategy_service = StrategyService()
    ServiceRegistry.register("strategy", strategy_service)
    
    # Create the FastAPI app
    app = create_fastapi_app()
    
    # Create a test client
    client = TestClient(app)
    
    return client, api_client


class TestFastAPIEndpoints:
    """Test the FastAPI endpoints with mock mode"""

    def test_health_check(self, test_client):
        """Test the health check endpoint"""
        client, _ = test_client
        
        # Make a request to the health check endpoint
        response = client.get("/health")
        
        # Verify the response
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_get_account_info(self, test_client):
        """Test the get account info endpoint"""
        client, _ = test_client
        
        # Make a request to the account info endpoint
        response = client.get("/api/account")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "account_id" in data
        assert data["account_id"] == "mock_account"

    def test_get_account_balances(self, test_client):
        """Test the get account balances endpoint"""
        client, _ = test_client
        
        # Make a request to the account balances endpoint
        response = client.get("/api/account/balances")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "cash" in data
        assert "equity" in data
        assert data["cash"] >= 0

    def test_get_account_positions(self, test_client):
        """Test the get account positions endpoint"""
        client, api_client = test_client
        
        # Place and fill an order to create a position
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "order_type": "MARKET",
            "side": "BUY",
            "session": "REGULAR",
            "duration": "DAY"
        }
        
        result = api_client.place_order(order_data)
        order_id = result["order_id"]
        
        # Mark the order as filled
        api_client.mock_orders[order_id]["status"] = "FILLED"
        api_client.mock_orders[order_id]["filled_quantity"] = 10
        api_client.mock_orders[order_id]["filled_price"] = 150.0
        
        # Update paper positions
        api_client.paper_positions["AAPL"] = {
            "symbol": "AAPL",
            "quantity": 10,
            "costBasis": 1500.0,
            "currentValue": 1500.0
        }
        
        # Make a request to the account positions endpoint
        response = client.get("/api/account/positions")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "AAPL"
        assert data[0]["quantity"] == 10

    def test_place_order(self, test_client):
        """Test the place order endpoint"""
        client, api_client = test_client
        
        # Prepare the order data
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "order_type": "MARKET",
            "side": "BUY",
            "price": None,
            "session": "REGULAR",
            "duration": "DAY",
            "strategy": "test_strategy"
        }
        
        # Make a request to the place order endpoint
        response = client.post("/api/orders", json=order_data)
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
        assert data["status"] == "SUBMITTED"
        assert data["symbol"] == "AAPL"
        assert data["quantity"] == 10
        assert data["side"] == "BUY"
        
        # Verify the order was stored
        order_id = data["order_id"]
        assert order_id in api_client.mock_orders
        
        # Verify strategy was recorded
        assert api_client.mock_orders[order_id].get("strategy") == "test_strategy"

    def test_get_orders(self, test_client):
        """Test the get orders endpoint"""
        client, api_client = test_client
        
        # Place a few orders
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
            
            result = api_client.place_order(order_data)
            order_ids.append(result["order_id"])
        
        # Make a request to the get orders endpoint
        response = client.get("/api/orders")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(symbols)
        
        # Mark one order as filled
        api_client.mock_orders[order_ids[0]]["status"] = "FILLED"
        
        # Make a request to get filled orders
        response = client.get("/api/orders?status=FILLED")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["order_id"] == order_ids[0]

    def test_cancel_order(self, test_client):
        """Test the cancel order endpoint"""
        client, api_client = test_client
        
        # Place an order
        order_data = {
            "symbol": "AAPL",
            "quantity": 10,
            "order_type": "MARKET",
            "side": "BUY",
            "session": "REGULAR",
            "duration": "DAY"
        }
        
        result = api_client.place_order(order_data)
        order_id = result["order_id"]
        
        # Make a request to the cancel order endpoint
        response = client.delete(f"/api/orders/{order_id}")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["order_id"] == order_id
        
        # Verify the order was cancelled
        assert api_client.mock_orders[order_id]["status"] == "CANCELLED"

    def test_get_quote(self, test_client):
        """Test the get quote endpoint"""
        client, _ = test_client
        
        # Make a request to the get quote endpoint
        response = client.get("/api/market/quote/AAPL")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "bid" in data
        assert "ask" in data
        assert "last" in data

    def test_create_strategy(self, test_client):
        """Test the create strategy endpoint"""
        client, _ = test_client
        
        # Prepare the strategy data
        strategy_data = {
            "type": "highlow",
            "symbol": "AAPL",
            "quantity": 10,
            "parameters": {
                "high_threshold": 150.0,
                "low_threshold": 140.0
            }
        }
        
        # Make a request to the create strategy endpoint
        response = client.post("/api/strategies", json=strategy_data)
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "highlow_AAPL"
        assert data["type"] == "highlow"
        assert data["symbol"] == "AAPL"
        
        # Make a request to the list strategies endpoint
        response = client.get("/api/strategies")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "highlow_AAPL"

    def test_execute_strategy(self, test_client):
        """Test the execute strategy endpoint"""
        client, _ = test_client
        
        # Create a strategy
        strategy_data = {
            "type": "highlow",
            "symbol": "AAPL",
            "quantity": 10,
            "parameters": {
                "high_threshold": 150.0,
                "low_threshold": 140.0
            }
        }
        
        client.post("/api/strategies", json=strategy_data)
        
        # Make a request to the execute strategy endpoint
        response = client.post("/api/strategies/highlow_AAPL/execute")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["strategy"] == "highlow_AAPL"

    def test_delete_strategy(self, test_client):
        """Test the delete strategy endpoint"""
        client, _ = test_client
        
        # Create a strategy
        strategy_data = {
            "type": "highlow",
            "symbol": "AAPL",
            "quantity": 10,
            "parameters": {
                "high_threshold": 150.0,
                "low_threshold": 140.0
            }
        }
        
        client.post("/api/strategies", json=strategy_data)
        
        # Make a request to the delete strategy endpoint
        response = client.delete("/api/strategies/highlow_AAPL")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["strategy"] == "highlow_AAPL"
        
        # Make a request to the list strategies endpoint
        response = client.get("/api/strategies")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_trade_history(self, test_client):
        """Test the get trade history endpoint"""
        client, _ = test_client
        
        # Make a request to the get trade history endpoint
        response = client.get("/api/history")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)  # Should return a list, even if empty 