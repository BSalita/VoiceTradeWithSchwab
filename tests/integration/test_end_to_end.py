"""
End-to-End Test Suite for Automated Trading System

This test suite verifies the complete workflow of the application from command input
to order execution, testing the integration of all major components:

1. Command processing (text and voice)
2. Service interactions
3. API client communication
4. Order execution and verification 
5. Strategy execution

These tests run in mock mode to avoid requiring real API credentials.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import json
import time
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EndToEndTests")

# Set environment to mock mode for testing
os.environ["TRADING_MODE"] = "MOCK"

# Import application components
from app.interfaces.cli.text_command_handler import TextCommandHandler
from app.interfaces.cli.voice_command_handler import VoiceCommandHandler
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.services.strategy_service import StrategyService
from app.api.schwab_client import SchwabAPIClient
from app.services.service_registry import ServiceRegistry


class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for the complete application workflow"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Initialize API client
        self.api_client = SchwabAPIClient()
        
        # Initialize and register services
        self.trading_service = TradingService(api_client=self.api_client)
        self.market_data_service = MarketDataService(api_client=self.api_client)
        self.strategy_service = StrategyService()
        
        ServiceRegistry.register("trading", self.trading_service)
        ServiceRegistry.register("market_data", self.market_data_service)
        ServiceRegistry.register("strategy", self.strategy_service)
        
        # Initialize command handlers
        self.text_handler = TextCommandHandler()
        
        # For voice handler, mock the speech recognition components
        with patch('speech_recognition.Recognizer'), \
             patch('pyttsx3.init'), \
             patch('app.interfaces.cli.voice_command_handler.WHISPER_AVAILABLE', True):
            self.voice_handler = VoiceCommandHandler()
            
        logger.info("Test environment initialized in mock mode")
        
    def tearDown(self):
        """Clean up after each test"""
        ServiceRegistry.clear()
        logger.info("Test environment cleaned up")
        
    def test_end_to_end_market_order_text(self):
        """Test the complete flow of placing a market order via text command"""
        # 1. Define test parameters
        symbol = "AAPL"
        quantity = 10
        command = f"buy {quantity} shares of {symbol}"
        
        # 2. Process the command using the text handler
        logger.info(f"Processing command: {command}")
        result = self.text_handler.handle_command(command)
        
        # 3. Verify the command was processed successfully
        self.assertTrue(result["success"], f"Command failed: {result.get('message', 'Unknown error')}")
        self.assertIn("order", result, "No order information in result")
        
        # 4. Verify the order details
        order = result["order"]
        self.assertEqual(order["symbol"], symbol)
        self.assertEqual(order["quantity"], quantity)
        self.assertEqual(order["side"], "buy")
        self.assertEqual(order["order_type"], "market")
        
        # 5. Verify the order was recorded
        # First check if orders are in the result, otherwise fall back to get_orders
        if "orders" in result and result["orders"]:
            orders = result["orders"]
            logger.info(f"Using orders from result: {orders}")
        else:
            # Fall back to get_orders if orders not in result
            orders = self.trading_service.get_orders()
            logger.info(f"Using orders from get_orders: {orders}")
        
        self.assertGreaterEqual(len(orders), 1, "No orders found")
        
        # Find our order
        matching_orders = [o for o in orders if o["symbol"] == symbol and o["quantity"] == quantity]
        self.assertGreaterEqual(len(matching_orders), 1, f"No matching orders found for {symbol} with quantity {quantity}")
        
        logger.info(f"Market order successfully placed and verified: {order['order_id']}")
        
    def test_end_to_end_limit_order_text(self):
        """Test the complete flow of placing a limit order via text command"""
        # 1. Define test parameters
        symbol = "MSFT"
        quantity = 5
        price = 250.00
        command = f"sell {quantity} shares of {symbol} at ${price}"
        
        # 2. Process the command using the text handler
        logger.info(f"Processing command: {command}")
        result = self.text_handler.handle_command(command)
        
        # 3. Verify the command was processed successfully
        self.assertTrue(result["success"], f"Command failed: {result.get('message', 'Unknown error')}")
        self.assertIn("order", result, "No order information in result")
        
        # 4. Verify the order details
        order = result["order"]
        self.assertEqual(order["symbol"], symbol)
        self.assertEqual(order["quantity"], quantity)
        self.assertEqual(order["side"], "sell")
        self.assertEqual(order["order_type"], "limit")
        self.assertEqual(order["price"], price)
        
        # 5. Verify the order was recorded
        # First check if orders are in the result, otherwise fall back to get_orders
        if "orders" in result and result["orders"]:
            orders = result["orders"]
            logger.info(f"Using orders from result: {orders}")
        else:
            # Fall back to get_orders if orders not in result
            orders = self.trading_service.get_orders()
            logger.info(f"Using orders from get_orders: {orders}")
        
        self.assertGreaterEqual(len(orders), 1, "No orders found")
        
        # Find our order
        matching_orders = [o for o in orders if o["symbol"] == symbol and o["quantity"] == quantity]
        self.assertGreaterEqual(len(matching_orders), 1, f"No matching orders found for {symbol} with quantity {quantity}")
        
        logger.info(f"Limit order successfully placed and verified: {order['order_id']}")
        
    def test_end_to_end_market_data_text(self):
        """Test the complete flow of retrieving market data via text command"""
        # 1. Define test parameters
        symbol = "GOOG"
        command = f"what is the price of {symbol}"
        
        # 2. Process the command using the text handler
        logger.info(f"Processing command: {command}")
        result = self.text_handler.handle_command(command)
        
        # 3. Verify the command was processed successfully
        self.assertTrue(result["success"], f"Command failed: {result.get('message', 'Unknown error')}")
        self.assertIn("quote", result, "No quote information in result")
        
        # 4. Verify the quote details
        quote = result["quote"]
        self.assertEqual(quote["symbol"], symbol)
        self.assertIn("bid_price", quote)
        self.assertIn("ask_price", quote)
        self.assertIn("last_price", quote)
        
        logger.info(f"Market data successfully retrieved for {symbol}")
        
    def test_end_to_end_voice_command_simulation(self):
        """Test the complete flow using simulated voice commands"""
        # Since we can't actually speak in an automated test, we'll simulate voice recognition
        
        # 1. Mock the speech recognition
        command = "buy 15 shares of TSLA"
        
        # 2. Mock the listen_for_command method to return our test command
        with patch.object(self.voice_handler, 'listen_for_command', return_value=command):
            # 3. Call the listen_once method, which should use our mocked command
            logger.info(f"Simulating voice command: {command}")
            result = self.voice_handler.process_voice_command(command)
            
            # 4. Verify the order was created
            # First check if orders are in the result, otherwise fall back to get_orders
            if result and isinstance(result, dict) and "orders" in result and result["orders"]:
                orders = result["orders"]
                logger.info(f"Using orders from result: {orders}")
            else:
                # Fall back to get_orders if orders not in result
                orders = self.trading_service.get_orders()
                logger.info(f"Using orders from get_orders: {orders}")
            
            # Find our order
            matching_orders = [o for o in orders if o["symbol"] == "TSLA" and o["quantity"] == 15]
            self.assertGreaterEqual(len(matching_orders), 1, "No matching orders found for TSLA with quantity 15")
            
            logger.info(f"Voice command successfully processed")
            
    def test_end_to_end_ladder_strategy(self):
        """Test the complete flow of setting up and executing a ladder strategy"""
        # 1. Set up test parameters
        symbol = "AMZN"
        quantity = 20
        steps = 4
        start_price = 3000.0
        end_price = 3100.0
        
        # 2. Execute the ladder strategy command
        command = f"ladder buy {quantity} shares of {symbol} with {steps} steps from ${start_price} to ${end_price}"
        logger.info(f"Processing command: {command}")
        result = self.text_handler.handle_command(command)
        
        # 3. Verify the strategy was created successfully
        self.assertTrue(result["success"])
        self.assertIn("strategy", result)
        
        strategy = result["strategy"]
        self.assertEqual(strategy["symbol"], symbol)
        self.assertEqual(strategy["side"], "buy")
        self.assertEqual(strategy["type"], "ladder")
        self.assertEqual(strategy["steps"], steps)
        
        # 4. Verify the orders were created for the strategy
        # Let's give the strategy a moment to create the orders
        time.sleep(0.1)
        
        # First check if orders are in the result, otherwise fall back to get_orders
        if "orders" in result and result["orders"]:
            orders = result["orders"]
            logger.info(f"Using orders from result: {orders}")
        else:
            # Fall back to get_orders if orders not in result
            orders = self.trading_service.get_orders()
            logger.info(f"Using orders from get_orders: {orders}")
        
        # Print the result for debugging
        logger.info(f"Result keys: {result.keys()}")
        if "orders" in result:
            logger.info(f"Orders in result: {len(result['orders'])}")
        
        # Filter for ladder orders
        # The orders in the result have a different structure now
        ladder_orders = []
        for o in orders:
            # Check if this is a direct order or an order info object
            if 'order' in o and o.get('success'):
                # This is an order info object
                order = o['order']
                if order.get('symbol') == symbol:
                    ladder_orders.append(order)
            elif o.get('symbol') == symbol and o.get('strategy') == 'LadderStrategy':
                # This is a direct order
                ladder_orders.append(o)
        
        # Verify we have the correct number of orders
        self.assertEqual(len(ladder_orders), steps, f"Expected {steps} ladder orders, found {len(ladder_orders)}")
        
        # Verify the price range
        if ladder_orders:
            # Extract prices from orders
            prices = []
            for order in ladder_orders:
                # Check if price is directly in the order or in a parent object
                if 'price' in order and order['price'] is not None:
                    prices.append(order['price'])
                elif 'order' in order and 'price' in order['order'] and order['order']['price'] is not None:
                    prices.append(order['order']['price'])
            
            prices.sort()
            
            if prices:
                self.assertAlmostEqual(prices[0], start_price, delta=0.01)
                self.assertAlmostEqual(prices[-1], end_price, delta=0.01)
        
    def test_end_to_end_cancel_order(self):
        """Test the complete flow of placing and canceling an order"""
        # 1. First place an order
        symbol = "NFLX"
        quantity = 8
        command = f"buy {quantity} shares of {symbol}"
        
        logger.info(f"Processing command: {command}")
        result = self.text_handler.handle_command(command)
        
        self.assertTrue(result["success"])
        order_id = result["order"]["order_id"]
        
        # 2. Now cancel the order
        cancel_command = f"cancel order {order_id}"
        
        logger.info(f"Processing command: {cancel_command}")
        cancel_result = self.text_handler.handle_command(cancel_command)
        
        # 3. Verify the cancellation
        self.assertTrue(cancel_result["success"], 
                      f"Cancel failed: {cancel_result.get('message', 'Unknown error')}")
        
        # 4. Check that the order status is updated
        # Use the canceled_orders from the cancel_result if available
        if "canceled_orders" in cancel_result:
            canceled_orders = cancel_result["canceled_orders"]
        else:
            # Fallback to the original method
            orders = self.trading_service.get_orders(status="canceled")
            canceled_orders = [o for o in orders if o["order_id"] == order_id]
        
        self.assertEqual(len(canceled_orders), 1)
        
        logger.info(f"Order successfully canceled")
        
    def test_end_to_end_multiple_commands_sequence(self):
        """Test a sequence of commands simulating a complete trading session"""
        commands = [
            "what is the price of AAPL",
            "buy 10 shares of AAPL",
            "what is the price of MSFT",
            "sell 5 shares of MSFT at $275.50",
            "status",
            "ladder buy 15 shares of GOOG with 3 steps from $2000 to $2050",
            "strategies",
            "cancel order"  # This will be updated with a real order ID
        ]
        
        logger.info("Starting command sequence simulation")
        
        # Process the first few commands
        for i in range(5):
            command = commands[i]
            logger.info(f"Processing command: {command}")
            result = self.text_handler.handle_command(command)
            self.assertTrue(result["success"], 
                          f"Command failed: {result.get('message', 'Unknown error')}")
            
            # If this is the buy order, save the order_id for later cancellation
            if i == 1:  # This is the buy AAPL command
                order_id = result["order"]["order_id"]
                # Update the cancel command with the real order id
                commands[7] = f"cancel order {order_id}"
                
        # Process the ladder strategy
        logger.info(f"Processing command: {commands[5]}")
        result = self.text_handler.handle_command(commands[5])
        self.assertTrue(result["success"])
        strategy_id = result["strategy"]["id"]
        
        # Check active strategies
        logger.info(f"Processing command: {commands[6]}")
        result = self.text_handler.handle_command(commands[6])
        self.assertTrue(result["success"])
        
        # Verify the strategy is in the list
        self.assertIn(strategy_id, str(result))
        
        # Cancel an order
        logger.info(f"Processing command: {commands[7]}")
        result = self.text_handler.handle_command(commands[7])
        self.assertTrue(result["success"])
        
        logger.info("Command sequence completed successfully")
        
    def test_end_to_end_error_handling(self):
        """Test error handling across the complete workflow"""
        # Test various error scenarios
        error_commands = [
            # Missing quantity
            "buy shares of AAPL",
            
            # Invalid symbol
            "buy 10 shares of INVALID_SYMBOL_123456",
            
            # Missing price for limit order
            "buy 10 shares of AAPL at",
            
            # Invalid quantity
            "buy -5 shares of AAPL",
            
            # Invalid command format
            "execute trade AAPL",
            
            # Non-existent order ID
            "cancel order NONEXISTENT_ID_12345"
        ]
        
        logger.info("Testing error handling scenarios")
        
        for command in error_commands:
            logger.info(f"Testing error command: {command}")
            result = self.text_handler.handle_command(command)
            
            # The command should be recognized, but fail with an error message
            self.assertFalse(result["success"], f"Error command unexpectedly succeeded: {command}")
            self.assertIn("message", result, "No error message provided")
            
            logger.info(f"Error properly handled: {result['message']}")
            
        logger.info("Error handling tests completed successfully")


if __name__ == "__main__":
    unittest.main() 