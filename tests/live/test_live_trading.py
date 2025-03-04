"""
Live Trading Tests - USE WITH EXTREME CAUTION

These tests connect to the real Schwab API in LIVE trading mode.
They will use real money and place actual orders in the market.

PREREQUISITES:
1. Set ENABLE_LIVE_TESTS=1 in your environment
2. Provide valid API credentials in your environment
3. Set CONFIRM_LIVE_TESTING=YES_I_UNDERSTAND_THE_RISKS in your environment
4. Ideally run during market hours to avoid overnight risk

WARNING: These tests should only be run:
- On a dedicated test account with minimal funds
- By users who fully understand the financial implications
- In controlled environments with proper risk management
"""

import unittest
import os
import logging
import time
import getpass
from datetime import datetime
from app.api.schwab_client import SchwabAPIClient
from app.services.trading_service import TradingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test constants
TEST_SYMBOL = "AAPL"  # Liquid, high-volume stock
TEST_QUANTITY = 1  # Absolute minimum quantity
MAX_ORDER_VALUE = 200.00  # Maximum USD value allowed for test orders

class LiveTradingTest(unittest.TestCase):
    """Test suite for live trading - USE WITH EXTREME CAUTION"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment once before all tests"""
        # Multiple safety checks before allowing live tests
        if not os.environ.get("ENABLE_LIVE_TESTS"):
            raise unittest.SkipTest("Live trading tests not enabled. Set ENABLE_LIVE_TESTS=1 to run.")
            
        if os.environ.get("CONFIRM_LIVE_TESTING") != "YES_I_UNDERSTAND_THE_RISKS":
            raise unittest.SkipTest("Live trading confirmation not set properly. This is a safety feature.")
            
        # Additional user confirmation
        print("\n")
        print("=" * 80)
        print("WARNING: You are about to run LIVE trading tests with REAL MONEY.")
        print("These tests will place actual orders in the market.")
        print("=" * 80)
        
        confirmation = input("\nType 'I CONFIRM' to proceed with live tests: ")
        if confirmation != "I CONFIRM":
            raise unittest.SkipTest("User did not confirm live testing.")
            
        # Load API credentials from environment
        cls.api_key = os.environ.get("SCHWAB_API_KEY")
        cls.api_secret = os.environ.get("SCHWAB_API_SECRET")
        
        if not cls.api_key or not cls.api_secret:
            raise unittest.SkipTest("API credentials not found in environment variables")
            
        # Set trading mode to LIVE for the API client
        os.environ["TRADING_MODE"] = "LIVE"
        
        # Create API client (will use environment variables)
        cls.client = SchwabAPIClient()
        
        # Create trading service
        cls.trading_service = TradingService(cls.client)
        
        # Test connectivity before proceeding
        if not cls.client.check_connection():
            raise unittest.SkipTest("Could not connect to Schwab API. Check credentials and network.")
            
        # Verify we're in a safe environment
        account_info = cls.client.get_account_info()
        if account_info.get("account_value", 1000000) > 10000:
            raise unittest.SkipTest("Account value exceeds $10,000. Use a smaller test account for safety.")
            
        logger.info(f"Live trading test suite initialized with symbol {TEST_SYMBOL}")
        logger.warning("LIVE TRADING TESTS ACTIVE - REAL MONEY WILL BE USED")
        
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
        """Test placing and immediately canceling a limit order"""
        # Get current price
        quote = self.client.get_quote(TEST_SYMBOL)
        current_price = quote.get("ask", 100.0)
        
        # Ensure we don't exceed max order value
        if current_price * TEST_QUANTITY > MAX_ORDER_VALUE:
            self.skipTest(f"Current price {current_price} * {TEST_QUANTITY} exceeds max test order value of ${MAX_ORDER_VALUE}")
        
        # Place limit order way below market price (unlikely to be filled)
        limit_price = current_price * 0.7  # 30% below market
        
        # Final confirmation before placing a live order
        print(f"\nAbout to place LIVE limit order: {TEST_QUANTITY} shares of {TEST_SYMBOL} at ${limit_price:.2f}")
        confirmation = input("Type 'PLACE ORDER' to proceed: ")
        if confirmation != "PLACE ORDER":
            self.skipTest("User did not confirm order placement")
        
        order = self.trading_service.place_order(
            symbol=TEST_SYMBOL,
            quantity=TEST_QUANTITY,
            order_type="LIMIT",
            side="BUY",
            price=limit_price
        )
        
        self.assertIsNotNone(order)
        self.assertIsNotNone(order.get("order_id"))
        order_id = order.get("order_id")
        
        logger.info(f"Placed live limit order: {order}")
        
        # Brief delay to let the order process
        time.sleep(1)
        
        # IMMEDIATELY cancel the order to minimize risk
        result = self.client.cancel_order(order_id)
        self.assertTrue(result.get("success", False))
        
        logger.info(f"Cancelled order {order_id}")
        
        # Verify the order was actually cancelled
        time.sleep(2)
        orders = self.client.get_orders()
        matching_orders = [o for o in orders if o.get("order_id") == order_id]
        if matching_orders:
            self.assertEqual(matching_orders[0].get("status"), "CANCELLED")

    def test_minimal_market_data(self):
        """Test retrieving market data feeds"""
        # Test retrieving basic market data without placing orders
        try:
            # Test depends on what market data APIs are available
            market_data = self.client.get_market_data(TEST_SYMBOL)
            self.assertIsNotNone(market_data)
            logger.info(f"Retrieved market data for {TEST_SYMBOL}")
        except NotImplementedError:
            self.skipTest("Market data API not implemented")

if __name__ == "__main__":
    unittest.main() 