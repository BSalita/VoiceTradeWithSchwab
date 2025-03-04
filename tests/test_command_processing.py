#!/usr/bin/env python3
"""
Unit tests for command processing functionality.
"""
import pytest
import unittest.mock as mock
import os
import json

# Remove path manipulation
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.schwab_client import SchwabAPIClient
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.commands.command_processor import CommandProcessor
from app.services.service_registry import ServiceRegistry
from app.services.strategy_service import StrategyService


class TestCommandProcessing:
    """Test command processing in mock mode."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Set the trading mode to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Create a mock API client
        self.api_client = SchwabAPIClient()
        
        # Create and register services
        self.trading_service = TradingService()
        self.trading_service.api_client = self.api_client
        ServiceRegistry.register("trading", self.trading_service)
        
        self.strategy_service = StrategyService()
        ServiceRegistry.register("strategy", self.strategy_service)
        
        # Create command service
        self.command_service = CommandProcessor()
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clear the service registry
        ServiceRegistry.clear()
    
    def test_buy_command(self):
        """Test processing a buy command."""
        # Process a buy command
        result = self.command_service.process_command("buy 10 AAPL")
        
        # Verify the command was processed
        assert result.get("success") is True
        
        # Verify an order was placed
        orders = self.trading_service.get_orders()
        
        # Find a BUY order for AAPL
        buy_order = None
        for order in orders:
            if (order.get("symbol") == "AAPL" and 
                order.get("side") == "BUY" and
                order.get("quantity") == 10):
                buy_order = order
                break
        
        assert buy_order is not None, "No BUY order was placed"
    
    def test_sell_command(self):
        """Test processing a sell command."""
        # Process a sell command
        result = self.command_service.process_command("sell 5 MSFT")
        
        # Verify the command was processed
        assert result.get("success") is True
        
        # Verify an order was placed
        orders = self.trading_service.get_orders()
        
        # Find a SELL order for MSFT
        sell_order = None
        for order in orders:
            if (order.get("symbol") == "MSFT" and 
                order.get("side") == "SELL" and
                order.get("quantity") == 5):
                sell_order = order
                break
        
        assert sell_order is not None, "No SELL order was placed"
    
    def test_cancel_command(self):
        """Test processing a cancel command."""
        # Place an order first
        order_result = self.command_service.process_command("buy 3 shares of GOOGL")
        order_id = order_result.get('order_id')
        
        # Now cancel it
        result = self.command_service.process_command(f"cancel order {order_id}")
        
        # Print the result structure for debugging
        print(f"Cancel result: {result}")
        
        # Verify the result
        assert result.get('success') is True
        
        # The order_id might be in the result or in an order field
        if 'order' in result:
            order = result.get('order', {})
            assert order_id == order.get('order_id')
            # Check if the order status is canceled (case-insensitive)
            order_status = order.get('status', '').upper()
            assert order_status in ['CANCELLED', 'CANCELED']
        else:
            assert order_id == result.get('order_id')
            # Get the order from the trading service to check its status
            orders = self.trading_service.get_orders()
            for order in orders:
                if order.get('order_id') == order_id:
                    order_status = order.get('status', '').upper()
                    assert order_status in ['CANCELLED', 'CANCELED']
                    break
    
    def test_status_command(self):
        """Test processing a status command."""
        # First place an order
        self.command_service.process_command("buy 7 TSLA")
        
        # Process a status command
        status_result = self.command_service.process_command("status")
        
        # Verify the command was processed
        assert status_result.get("success") is True
        assert "orders" in status_result
        
        # Verify we got at least one order
        assert len(status_result["orders"]) >= 1
    
    def test_strategy_command(self):
        """Test processing a strategy command."""
        # Process a strategy command to create a highlow strategy
        strategy_result = self.command_service.process_command(
            "strategy highlow AAPL 10 145.0 155.0"
        )
        
        # Verify the command was processed
        assert strategy_result.get("success") is True
        
        # Verify the strategy was created
        strategies = self.strategy_service.get_strategies()
        assert "highlow_AAPL" in strategies
    
    def test_execute_strategy_command(self):
        """Test processing an execute strategy command."""
        # First create a strategy
        self.command_service.process_command(
            "strategy highlow AAPL 10 145.0 155.0"
        )
        
        # Process an execute command
        execute_result = self.command_service.process_command(
            "execute highlow_AAPL"
        )
        
        # Verify the command was processed
        assert execute_result.get("success") is True
    
    def test_help_command(self):
        """Test processing a help command."""
        # Process a help command
        help_result = self.command_service.process_command("help")
        
        # Verify the command was processed
        assert help_result.get("success") is True
        assert "commands" in help_result
        
        # Verify we got help for multiple commands
        assert len(help_result["commands"]) > 1


if __name__ == "__main__":
    # Run the tests
    test = TestCommandProcessing()
    
    try:
        test.setup_method()
        
        print("Running test_buy_command...")
        test.test_buy_command()
        print("✓ test_buy_command passed")
        
        print("Running test_sell_command...")
        test.test_sell_command()
        print("✓ test_sell_command passed")
        
        print("Running test_cancel_command...")
        test.test_cancel_command()
        print("✓ test_cancel_command passed")
        
        print("Running test_status_command...")
        test.test_status_command()
        print("✓ test_status_command passed")
        
        print("Running test_strategy_command...")
        test.test_strategy_command()
        print("✓ test_strategy_command passed")
        
        print("Running test_execute_strategy_command...")
        test.test_execute_strategy_command()
        print("✓ test_execute_strategy_command passed")
        
        print("Running test_help_command...")
        test.test_help_command()
        print("✓ test_help_command passed")
        
        print("All command processing tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        test.teardown_method() 