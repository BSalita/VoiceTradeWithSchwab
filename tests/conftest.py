"""
Shared test fixtures for the automated trading application
"""

import os
import pytest
from unittest.mock import MagicMock, patch
import tempfile
import sys
from pathlib import Path

from app.services import ServiceRegistry
from app.api.schwab_client import SchwabAPIClient
from app.models.order import Order, OrderType, OrderSide, OrderStatus, OrderDuration, TradingSession
from app.models.trade_history import TradeHistory
from app.commands.command_processor import CommandProcessor
from app.strategies.base_strategy import BaseStrategy

@pytest.fixture(scope="function", autouse=True)
def mock_environment():
    """Set up mock environment variables for testing"""
    os.environ["TRADING_MODE"] = "MOCK"
    os.environ["SCHWAB_API_KEY"] = "mock_api_key"
    os.environ["SCHWAB_API_SECRET"] = "mock_api_secret"
    os.environ["SCHWAB_ACCOUNT_ID"] = "mock_account_id"
    yield
    # Clean up
    if "TRADING_MODE" in os.environ:
        del os.environ["TRADING_MODE"]
    if "SCHWAB_API_KEY" in os.environ:
        del os.environ["SCHWAB_API_KEY"]
    if "SCHWAB_API_SECRET" in os.environ:
        del os.environ["SCHWAB_API_SECRET"]
    if "SCHWAB_ACCOUNT_ID" in os.environ:
        del os.environ["SCHWAB_ACCOUNT_ID"]


@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing"""
    with patch("app.api.schwab_client.SchwabAPIClient", autospec=True) as mock_client:
        # Set up mock methods
        mock_instance = mock_client.return_value
        
        # Mock place_order
        mock_instance.place_order.return_value = {
            "order_id": "mock_order_123",
            "status": "SUBMITTED",
            "symbol": "AAPL",
            "quantity": 10,
            "side": "BUY",
            "order_type": "MARKET"
        }
        
        # Mock get_quote
        mock_instance.get_quote.return_value = {
            "symbol": "AAPL",
            "bid": 150.0,
            "ask": 150.1,
            "last": 150.05,
            "volume": 1000000
        }
        
        # Mock get_account_info
        mock_instance.get_account_info.return_value = {
            "account_id": "mock_account_id",
            "account_type": "MARGIN",
            "status": "ACTIVE"
        }
        
        # Mock get_account_positions
        mock_instance.get_account_positions.return_value = [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "costBasis": 1500.0,
                "currentValue": 1600.0,
                "unrealizedPnL": 100.0
            }
        ]
        
        # Mock get_account_balances
        mock_instance.get_account_balances.return_value = {
            "cash": 10000.0,
            "marginBuyingPower": 20000.0,
            "equity": 30000.0
        }
        
        yield mock_instance


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
        yield temp_file.name
    # Clean up
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def trade_history():
    """Create a trade history instance for testing"""
    history = TradeHistory()
    # Add some test trades
    history.add_trade(
        symbol="AAPL",
        side="BUY",
        quantity=10,
        price=150.0,
        order_id="mock_order_123",
        strategy="basic"
    )
    history.add_trade(
        symbol="MSFT",
        side="SELL",
        quantity=5,
        price=250.0,
        order_id="mock_order_456",
        strategy="oscillating"
    )
    return history


@pytest.fixture
def command_processor():
    """Create a command processor for testing"""
    return CommandProcessor()


@pytest.fixture
def mock_services():
    """Set up mock services for testing"""
    # Reset the service registry
    ServiceRegistry._services = {}
    
    # Create mock services
    mock_trading = MagicMock()
    mock_market_data = MagicMock()
    mock_strategies = MagicMock()
    
    # Register mock services
    ServiceRegistry.register("trading", mock_trading)
    ServiceRegistry.register("market_data", mock_market_data)
    ServiceRegistry.register("strategies", mock_strategies)
    
    return {
        "trading": mock_trading,
        "market_data": mock_market_data,
        "strategies": mock_strategies
    }


@pytest.fixture
def sample_order():
    """Create a sample order for testing"""
    return Order(
        symbol="AAPL",
        quantity=10,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        status=OrderStatus.PENDING,
        duration=OrderDuration.DAY,
        session=TradingSession.REGULAR
    ) 