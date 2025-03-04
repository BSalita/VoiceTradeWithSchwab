#!/usr/bin/env python3
"""
Tests for interacting with the Schwab API using real credentials.
CAUTION: These tests use real API credentials and may retrieve real account data.
They are designed NOT to place actual trades but still use live connections.
"""

import os
import pytest
import unittest
from datetime import datetime
import logging
import requests
import traceback

# Remove path manipulation
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.api.schwab_client import SchwabAPIClient
from app.services.service_registry import ServiceRegistry
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LiveAPITestBase(unittest.TestCase):
    """Base class for live API tests."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment once before all tests."""
        # Check if we should run live tests
        cls.should_skip = False
        cls.skip_reason = None
        
        # Check for credentials
        api_key = os.environ.get("SCHWAB_API_KEY")
        api_secret = os.environ.get("SCHWAB_API_SECRET")
        account_id = os.environ.get("SCHWAB_ACCOUNT_ID")
        
        if not all([api_key, api_secret, account_id]):
            cls.should_skip = True
            cls.skip_reason = "Missing API credentials in environment variables"
            logger.warning(cls.skip_reason)
            return
            
        # Check if credentials are mock values
        if api_key == "mock_api_key" or api_secret == "mock_api_secret":
            cls.should_skip = True
            cls.skip_reason = "Using mock credentials, not real API keys"
            logger.warning(cls.skip_reason)
            return
        
        # Get trading mode from environment or default to PAPER
        trading_mode = os.environ.get("TRADING_MODE", "PAPER")
        
        # Force PAPER mode for safety unless explicitly overridden
        if trading_mode == "LIVE" and not os.environ.get("ALLOW_LIVE_TESTS"):
            logger.warning("⚠️ Forcing PAPER mode for safety. Set ALLOW_LIVE_TESTS=1 to use LIVE mode.")
            trading_mode = "PAPER"
        
        if trading_mode == "MOCK":
            cls.should_skip = True
            cls.skip_reason = "Tests require non-mock mode (PAPER or LIVE)"
            logger.warning(cls.skip_reason)
            return
        
        # Set up the API client and services
        os.environ["TRADING_MODE"] = trading_mode
        cls.trading_mode = trading_mode
        
        logger.info(f"\nRunning tests in {cls.trading_mode} mode")
        logger.info(f"Test time: {datetime.now().isoformat()}")
        
        try:
            cls.api_client = SchwabAPIClient()
            
            # Set up services
            cls.trading_service = TradingService()
            cls.trading_service.api_client = cls.api_client
            ServiceRegistry.register("trading", cls.trading_service)
            
            cls.market_data_service = MarketDataService()
            cls.market_data_service.api_client = cls.api_client
            ServiceRegistry.register("market_data", cls.market_data_service)
            
        except Exception as e:
            cls.should_skip = True
            cls.skip_reason = f"Error setting up API client: {str(e)}"
            logger.error(cls.skip_reason)
            logger.error(traceback.format_exc())
    
    def setUp(self):
        """Set up before each test."""
        if self.should_skip:
            self.skipTest(self.skip_reason)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if not cls.should_skip:
            ServiceRegistry.clear()
            logger.info("Test cleanup completed")


class TestLiveConnection(LiveAPITestBase):
    """Test basic API connectivity with real credentials."""
    
    def test_api_connection(self):
        """Test that we can connect to the API."""
        # This just tests that the API client was initialized without errors
        self.assertIsNotNone(self.api_client)
        self.assertEqual(self.api_client.trading_mode, self.trading_mode)
        logger.info(f"API client initialized successfully in {self.trading_mode} mode")


class TestMarketData(LiveAPITestBase):
    """Test retrieving market data with real credentials."""
    
    def test_get_quote(self):
        """Test retrieving a quote for a symbol."""
        symbol = "AAPL"
        
        try:
            # Try to get a quote
            quote = self.market_data_service.get_quote(symbol)
            
            # Verify the quote has expected fields
            self.assertIsNotNone(quote, "Quote should not be None")
            
            # Only verify symbol equality if we actually got a quote
            if quote:
                self.assertEqual(quote.get("symbol"), symbol)
                
                # Check for common quote fields
                expected_fields = ["bid", "ask", "last"]
                for field in expected_fields:
                    self.assertIn(field, quote, f"Quote should contain {field}")
                
                # Log the retrieved price
                logger.info(f"\nCurrent price for {symbol}: ${quote.get('last', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            # Don't fail the test on connection issues during development
            if "Connection" in str(e) or "Authentication" in str(e):
                self.skipTest(f"API connection issue: {str(e)}")
            else:
                raise


class TestAccountInfo(LiveAPITestBase):
    """Test retrieving account information with real credentials."""
    
    def test_get_account_info(self):
        """Test retrieving account information."""
        try:
            # Note: This assumes the API client has a get_account_info method
            account_info = self.api_client.get_account_info()
            self.assertIsNotNone(account_info)
            
            # Don't print sensitive information
            logger.info("\nSuccessfully retrieved account information")
            
        except NotImplementedError:
            self.skipTest("get_account_info not implemented")
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            # Don't fail the test on connection issues during development
            if "Connection" in str(e) or "Authentication" in str(e):
                self.skipTest(f"API connection issue: {str(e)}")
            else:
                raise


class TestOrdersReadOnly(LiveAPITestBase):
    """Test order-related API calls in read-only mode."""
    
    def test_get_orders(self):
        """Test retrieving orders (without placing any)."""
        try:
            orders = self.trading_service.get_orders()
            
            # We're just testing that the call works
            self.assertIsNotNone(orders)
            logger.info(f"\nRetrieved {len(orders)} orders")
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            # Don't fail the test on connection issues during development
            if "Connection" in str(e) or "Authentication" in str(e):
                self.skipTest(f"API connection issue: {str(e)}")
            else:
                raise


if __name__ == "__main__":
    # Run the tests with proper setup/teardown
    unittest.main() 