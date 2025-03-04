"""
Paper Trading Tests

These tests connect to the real Schwab API but only in paper trading mode.
They validate the full API integration without using real money.

To run these tests:
1. Set ENABLE_PAPER_TESTS=1 in your environment
2. Provide valid API credentials in your environment
"""

import unittest
import os
import logging
import time
from datetime import datetime
from app.api.schwab_client import SchwabAPIClient
from app.services.trading_service import TradingService
from app.strategies.basic_strategy import BasicStrategy
from app.strategies.ladder_strategy import LadderStrategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test stock symbol to use (should be a liquid, low-priced stock)
TEST_SYMBOL = "AAPL"  
TEST_QUANTITY = 1  # Minimum possible to reduce paper risk

class PaperTradingTest(unittest.TestCase):
    """Test suite for paper trading"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests"""
        if not os.environ.get("ENABLE_PAPER_TESTS"):
            raise unittest.SkipTest("Paper trading tests are disabled (ENABLE_PAPER_TESTS not set)")
            
        # Load API credentials from environment
        cls.api_key = os.environ.get("SCHWAB_API_KEY")
        cls.api_secret = os.environ.get("SCHWAB_API_SECRET")
        
        if not cls.api_key or not cls.api_secret:
            raise unittest.SkipTest("API credentials not found in environment variables")
            
        # Set trading mode to PAPER for the API client
        os.environ["TRADING_MODE"] = "PAPER"
        
        # Create API client (will use environment variables)
        cls.client = SchwabAPIClient()
        
        # Create trading service
        cls.trading_service = TradingService(cls.client)
        
        # Test connectivity before proceeding
        if not cls.client.check_connection():
            raise unittest.SkipTest("Could not connect to Schwab API. Check credentials and network.")
            
        logger.info(f"Paper trading test suite initialized with symbol {TEST_SYMBOL}")
        
    def setUp(self):
        """Set up each individual test"""
        # Add small delay between tests to avoid API rate limits
        time.sleep(1)
        
    def test_get_account_info(self):
        """Test retrieving account information"""
        account_info = self.client.get_account_info()
        self.assertIsNotNone(account_info)
        logger.info(f"Retrieved account info: {account_info}")
        
    def test_get_quotes(self):
        """Test retrieving stock quotes"""
        quote = self.client.get_quote(TEST_SYMBOL)
        self.assertIsNotNone(quote)
        self.assertEqual(quote.get("symbol"), TEST_SYMBOL)
        self.assertIsNotNone(quote.get("ask"))
        self.assertIsNotNone(quote.get("bid"))
        logger.info(f"Retrieved quote for {TEST_SYMBOL}: {quote}")
        
    def test_place_and_cancel_limit_order(self):
        """Test placing and canceling a limit order"""
        # Get current price
        quote = self.client.get_quote(TEST_SYMBOL)
        current_price = quote.get("ask", 100.0)
        
        # Place limit order way below market price (unlikely to be filled)
        limit_price = current_price * 0.8  # 20% below market
        
        order_result = self.trading_service.place_order(
            symbol=TEST_SYMBOL,
            quantity=TEST_QUANTITY,
            order_type="LIMIT",
            side="BUY",
            price=limit_price
        )
        
        self.assertIsNotNone(order_result)
        self.assertTrue(order_result.get("success", False))
        self.assertIsNotNone(order_result.get("order_id"))
        order_id = order_result.get("order_id")
        
        logger.info(f"Placed limit order: {order_result}")
        
        # Brief delay to let the order process
        time.sleep(2)
        
        # Verify order status
        orders = self.client.get_orders()
        matching_orders = [o for o in orders if o.get("order_id") == order_id]
        self.assertEqual(len(matching_orders), 1)
        
        # Cancel the order
        result = self.client.cancel_order(order_id)
        self.assertTrue(result.get("success", False))
        
        logger.info(f"Cancelled order {order_id}")
    
    def test_basic_strategy(self):
        """Test the BasicStrategy in paper mode"""
        # Create a BasicStrategy instance
        strategy = BasicStrategy()
        
        # Execute a small limit order that won't fill immediately
        quote = self.client.get_quote(TEST_SYMBOL)
        current_price = quote.get("bid", 100.0)
        limit_price = current_price * 0.9  # 10% below market
        
        result = strategy.execute(
            symbol=TEST_SYMBOL,
            quantity=TEST_QUANTITY,
            side="BUY",
            order_type="LIMIT",
            price=limit_price
        )
        self.assertTrue(result.get("success", False))
        self.assertIsNotNone(result.get("order", {}).get("order_id"))
        
        # Clean up - cancel the order
        order_id = result.get("order", {}).get("order_id")
        if order_id:
            self.client.cancel_order(order_id)
    
    def test_ladder_strategy(self):
        """Test the LadderStrategy in paper mode"""
        # Create a LadderStrategy instance
        strategy = LadderStrategy()
        
        # Get current price
        quote = self.client.get_quote(TEST_SYMBOL)
        current_price = quote.get("bid", 100.0)
        
        # Create a small ladder way below market price
        price_start = current_price * 0.8  # 20% below market
        price_end = current_price * 0.9  # 10% below market
        steps = 3
        quantity = TEST_QUANTITY
        
        # Execute ladder strategy
        result = strategy.execute(
            symbol=TEST_SYMBOL,
            quantity=quantity,
            side="BUY",
            price_start=price_start,
            price_end=price_end,
            steps=steps
        )
        self.assertTrue(result.get("success", False))
        
        # Clean up - cancel any orders
        orders = self.client.get_orders()
        for order in orders:
            if order.get("symbol") == TEST_SYMBOL and order.get("strategy") == "LadderStrategy":
                self.client.cancel_order(order.get("order_id"))

if __name__ == "__main__":
    unittest.main() 