"""
Unit tests for the CLI command handler in mock mode
"""

import pytest
from unittest.mock import patch, MagicMock

from app.interfaces.cli.command_handler import CommandHandler
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.services.strategy_service import StrategyService
from app.api.schwab_client import SchwabAPIClient
from app.services.service_registry import ServiceRegistry


class TestCLICommandHandler:
    """Test the CLI command handler with mock mode"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create a mock API client
        self.api_client = SchwabAPIClient()
        
        # Create and register services
        self.trading_service = TradingService(api_client=self.api_client)
        ServiceRegistry.register("trading", self.trading_service)
        
        self.market_data_service = MarketDataService(api_client=self.api_client)
        ServiceRegistry.register("market_data", self.market_data_service)
        
        self.strategy_service = StrategyService()
        ServiceRegistry.register("strategy", self.strategy_service)
        
        # Create the command handler
        self.command_handler = CommandHandler()

    def test_process_buy_command(self):
        """Test processing a buy command"""
        # Process a buy command
        result = self.command_handler.process_command("buy AAPL 10")
        
        # Verify the result
        assert "Order placed" in result
        assert "AAPL" in result
        assert "BUY" in result
        
        # Verify an order was placed
        orders = self.trading_service.get_orders()
        assert len(orders) == 1
        assert orders[0]["symbol"] == "AAPL"
        assert orders[0]["side"] == "BUY"
        assert orders[0]["quantity"] == 10

    def test_process_sell_command(self):
        """Test processing a sell command"""
        # Process a sell command
        result = self.command_handler.process_command("sell AAPL 10")
        
        # Verify the result
        assert "Order placed" in result
        assert "AAPL" in result
        assert "SELL" in result
        
        # Verify an order was placed
        orders = self.trading_service.get_orders()
        assert len(orders) == 1
        assert orders[0]["symbol"] == "AAPL"
        assert orders[0]["side"] == "SELL"
        assert orders[0]["quantity"] == 10

    def test_process_quote_command(self):
        """Test processing a quote command"""
        # Process a quote command
        result = self.command_handler.process_command("quote AAPL")
        
        # Verify the result
        assert "Quote for AAPL" in result
        assert "Bid:" in result
        assert "Ask:" in result
        assert "Last:" in result

    def test_process_positions_command(self):
        """Test processing a positions command"""
        # Place and fill an order to create a position
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
        
        # Process a positions command
        result = self.command_handler.process_command("positions")
        
        # Verify the result
        assert "Current positions" in result
        assert "AAPL" in result
        assert "10" in result

    def test_process_balances_command(self):
        """Test processing a balances command"""
        # Process a balances command
        result = self.command_handler.process_command("balances")
        
        # Verify the result
        assert "Account balances" in result
        assert "Cash:" in result
        assert "Equity:" in result

    def test_process_orders_command(self):
        """Test processing an orders command"""
        # Place a few orders
        self.trading_service.place_order(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY"
        )
        
        self.trading_service.place_order(
            symbol="MSFT",
            quantity=5,
            side="BUY",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY"
        )
        
        # Process an orders command
        result = self.command_handler.process_command("orders")
        
        # Verify the result
        assert "Current orders" in result
        assert "AAPL" in result
        assert "MSFT" in result
        assert "BUY" in result
        assert "SUBMITTED" in result

    def test_process_cancel_command(self):
        """Test processing a cancel command"""
        # Place an order
        order_result = self.trading_service.place_order(
            symbol="AAPL",
            quantity=10,
            side="BUY",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY"
        )
        
        order_id = order_result["order_id"]
        
        # Process a cancel command
        result = self.command_handler.process_command(f"cancel {order_id}")
        
        # Verify the result
        assert "Order cancelled" in result
        assert order_id in result
        
        # Verify the order was cancelled
        assert self.api_client.mock_orders[order_id]["status"] == "CANCELLED"

    def test_process_strategy_command(self):
        """Test processing a strategy command"""
        # Process a strategy command to create a highlow strategy
        result = self.command_handler.process_command("strategy highlow AAPL 10 150.0 140.0")
        
        # Verify the result
        assert "Strategy created" in result
        assert "highlow" in result
        assert "AAPL" in result
        
        # Verify the strategy was created
        strategies = self.strategy_service.list_strategies()
        assert len(strategies) == 1
        assert "highlow_AAPL" in strategies

    def test_process_execute_strategy_command(self):
        """Test processing an execute strategy command"""
        # Create a strategy
        self.command_handler.process_command("strategy highlow AAPL 10 150.0 140.0")
        
        # Mock the strategy's execute method
        with patch('app.strategies.highlow_strategy.HighLowStrategy.execute') as mock_execute:
            # Process an execute strategy command
            result = self.command_handler.process_command("execute highlow_AAPL")
            
            # Verify the result
            assert "Strategy executed" in result
            assert "highlow_AAPL" in result
            
            # Verify the strategy was executed
            mock_execute.assert_called_once()

    def test_process_list_strategies_command(self):
        """Test processing a list strategies command"""
        # Create a few strategies
        self.command_handler.process_command("strategy highlow AAPL 10 150.0 140.0")
        self.command_handler.process_command("strategy oscillating MSFT 5 200.0 190.0 1.0")
        
        # Process a list strategies command
        result = self.command_handler.process_command("strategies")
        
        # Verify the result
        assert "Registered strategies" in result
        assert "highlow_AAPL" in result
        assert "oscillating_MSFT" in result

    def test_process_remove_strategy_command(self):
        """Test processing a remove strategy command"""
        # Create a strategy
        self.command_handler.process_command("strategy highlow AAPL 10 150.0 140.0")
        
        # Process a remove strategy command
        result = self.command_handler.process_command("remove highlow_AAPL")
        
        # Verify the result
        assert "Strategy removed" in result
        assert "highlow_AAPL" in result
        
        # Verify the strategy was removed
        strategies = self.strategy_service.list_strategies()
        assert len(strategies) == 0

    def test_process_help_command(self):
        """Test processing a help command"""
        # Process a help command
        result = self.command_handler.process_command("help")
        
        # Verify the result contains help information
        assert "Available commands" in result
        assert "buy" in result
        assert "sell" in result
        assert "quote" in result
        assert "positions" in result
        assert "balances" in result
        assert "orders" in result
        assert "cancel" in result
        assert "strategy" in result
        assert "execute" in result
        assert "strategies" in result
        assert "remove" in result
        assert "help" in result
        assert "exit" in result

    def test_process_invalid_command(self):
        """Test processing an invalid command"""
        # Process an invalid command
        result = self.command_handler.process_command("invalid_command")
        
        # Verify the result
        assert "Unknown command" in result
        assert "help" in result 