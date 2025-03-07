"""
Unit tests for the MarketDataService.

These tests verify the functionality of the MarketDataService, which is responsible
for retrieving market data such as quotes, streaming prices, and market hours.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import datetime

from app.services.market_data_service import MarketDataService
from app.api.schwab_client import SchwabAPIClient


class TestMarketDataService:
    """
    Test suite for the MarketDataService functionality.
    
    These tests verify that the MarketDataService correctly:
    - Retrieves quotes for individual symbols and multiple symbols
    - Handles streaming price data
    - Manages callbacks for price updates
    - Provides market hours and status information
    """

    def setup_method(self):
        """
        Set up test environment before each test method runs.
        
        This method:
        1. Creates a mock API client
        2. Initializes a MarketDataService instance
        3. Configures the service to use the mock API client
        """
        # Create a mock API client
        self.api_client = MagicMock()
        
        # Create the market data service
        self.market_data_service = MarketDataService()
        self.market_data_service.api_client = self.api_client
    
    def test_initialization(self):
        """
        Test that the MarketDataService initializes with correct default values.
        
        Verifies:
        - The API client is initialized automatically if none is provided
        - The streaming_symbols set is empty
        """
        service = MarketDataService()
        assert service.api_client is not None
        assert service.streaming_symbols == set()

    def test_get_quote_success(self):
        """
        Test successful retrieval of a quote for a single symbol.
        
        This test:
        1. Sets up a mock quote response
        2. Calls the get_quote method
        3. Verifies the API client was called correctly
        4. Checks that the response contains the expected data
        """
        # Setup mock response
        mock_quote = {
            "symbol": "AAPL",
            "bid": 148.5,
            "ask": 148.7,
            "last": 148.6,
            "lastPrice": 148.6,
            "volume": 100000,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.api_client.get_quote.return_value = mock_quote
        
        # Call the service method
        result = self.market_data_service.get_quote("AAPL")
        
        # Verify the results
        self.api_client.get_quote.assert_called_once_with("AAPL")
        assert result["success"] == True
        assert result["symbol"] == "AAPL"
        assert result["quote"] == mock_quote

    def test_get_quote_error(self):
        """Test getting a quote with an error"""
        # Setup mock error
        self.api_client.get_quote.side_effect = Exception("API error")
        
        # Call the service method
        result = self.market_data_service.get_quote("AAPL")
        
        # Verify the results
        self.api_client.get_quote.assert_called_once_with("AAPL")
        assert result["success"] == False
        assert "error" in result
        assert "Failed to get quote for AAPL" in result["error"]

    def test_get_quotes_success(self):
        """Test getting multiple quotes successfully"""
        # Setup mock response
        mock_quotes = {
            "AAPL": {
                "symbol": "AAPL",
                "bid": 148.5,
                "ask": 148.7,
                "last": 148.6,
                "lastPrice": 148.6,
                "volume": 100000,
                "timestamp": datetime.datetime.now().isoformat()
            },
            "MSFT": {
                "symbol": "MSFT",
                "bid": 248.5,
                "ask": 248.7,
                "last": 248.6,
                "lastPrice": 248.6,
                "volume": 80000,
                "timestamp": datetime.datetime.now().isoformat()
            }
        }
        self.api_client.get_quotes.return_value = mock_quotes
        
        # Call the service method
        result = self.market_data_service.get_quotes(["AAPL", "MSFT"])
        
        # Verify the results
        self.api_client.get_quotes.assert_called_once_with(["AAPL", "MSFT"])
        assert result["success"] == True
        assert "quotes" in result
        assert result["quotes"] == mock_quotes

    def test_get_quotes_error(self):
        """Test getting multiple quotes with an error"""
        # Setup mock error
        self.api_client.get_quotes.side_effect = Exception("API error")
        
        # Call the service method
        result = self.market_data_service.get_quotes(["AAPL", "MSFT"])
        
        # Verify the results
        self.api_client.get_quotes.assert_called_once_with(["AAPL", "MSFT"])
        assert result["success"] == False
        assert "error" in result
        assert "Failed to get quotes" in result["error"]

    def test_start_price_stream_success(self):
        """Test starting a price stream successfully"""
        # Setup mock response
        self.api_client.start_price_stream.return_value = True
        
        # Call the service method
        result = self.market_data_service.start_price_stream(["AAPL", "MSFT"])
        
        # Verify the results
        self.api_client.start_price_stream.assert_called_once_with(["AAPL", "MSFT"])
        assert result["success"] == True
        assert "message" in result
        # Check if symbols are included in the response instead of in the message
        assert "symbols" in result
        assert "AAPL" in result["symbols"]
        assert "MSFT" in result["symbols"]
        assert self.market_data_service.streaming_symbols == {"AAPL", "MSFT"}

    def test_start_price_stream_error(self):
        """Test starting a price stream with an error"""
        # Setup mock error
        self.api_client.start_price_stream.return_value = False
        
        # Call the service method
        result = self.market_data_service.start_price_stream(["AAPL", "MSFT"])
        
        # Verify the results
        self.api_client.start_price_stream.assert_called_once_with(["AAPL", "MSFT"])
        assert result["success"] == False
        assert "error" in result
        assert "Failed to start price stream" in result["error"]
        assert self.market_data_service.streaming_symbols == set()

    def test_stop_price_stream_success(self):
        """Test stopping a price stream successfully"""
        # Setup initial state
        self.market_data_service.streaming_symbols = {"AAPL", "MSFT"}
        self.api_client.stop_price_stream.return_value = True
        
        # Call the service method
        result = self.market_data_service.stop_price_stream()
        
        # Verify the results
        self.api_client.stop_price_stream.assert_called_once()
        assert result["success"] == True
        assert "message" in result
        assert "Stopped price stream" in result["message"]
        assert self.market_data_service.streaming_symbols == set()

    def test_stop_price_stream_error(self):
        """Test stopping a price stream with an error"""
        # Setup initial state and mock error
        self.market_data_service.streaming_symbols = {"AAPL", "MSFT"}
        self.api_client.stop_price_stream.return_value = False
        
        # Call the service method
        result = self.market_data_service.stop_price_stream()
        
        # Verify the results
        self.api_client.stop_price_stream.assert_called_once()
        assert result["success"] == False
        assert "error" in result
        assert "Failed to stop price stream" in result["error"]
        # Streaming symbols should still be set even if there was an error
        assert self.market_data_service.streaming_symbols == {"AAPL", "MSFT"}

    def test_register_price_callback_success(self):
        """Test registering a price callback successfully"""
        # Setup mock callback
        mock_callback = MagicMock()
        
        # Call the service method
        result = self.market_data_service.register_price_callback("AAPL", mock_callback)
        
        # Verify the results
        self.api_client.register_price_callback.assert_called_once_with("AAPL", mock_callback)
        assert result["success"] == True
        assert "message" in result
        assert "AAPL" in result["message"]

    def test_register_price_callback_error(self):
        """Test registering a price callback with an error"""
        # Setup mock callback and error
        mock_callback = MagicMock()
        self.api_client.register_price_callback.side_effect = Exception("Registration error")
        
        # Call the service method
        result = self.market_data_service.register_price_callback("AAPL", mock_callback)
        
        # Verify the results
        self.api_client.register_price_callback.assert_called_once_with("AAPL", mock_callback)
        assert result["success"] == False
        assert "error" in result
        assert "Failed to register price callback" in result["error"]

    def test_get_market_hours(self):
        """Test getting market hours"""
        # Mock the API client response
        self.api_client.get_market_hours.return_value = {
            'status': 'OPEN',
            'hours': {
                'open': '09:30:00',
                'close': '16:00:00'
            }
        }
        
        result = self.market_data_service.get_market_hours()
        
        assert "status" in result
        assert "hours" in result
        assert result["status"] == "OPEN"

    def test_get_market_status(self):
        """Test getting market status"""
        # Mock the API client response
        self.api_client.get_market_status.return_value = "OPEN"
        
        result = self.market_data_service.get_market_status()
        
        assert isinstance(result, str)
        assert result == "OPEN"


def run_tests():
    """
    Run all market data service tests in sequence.
    
    This function:
    1. Creates a TestMarketDataService instance
    2. Sets up the test environment
    3. Runs each test method in sequence
    4. Reports success or failure
    
    Returns:
        bool: True if all tests pass, False if any test fails
    """
    test = TestMarketDataService()
    try:
        test.setup_method()
        
        # Run all the tests
        test.test_initialization()
        test.test_get_quote_success()
        test.test_get_quote_error()
        test.test_get_quotes_success()
        test.test_get_quotes_error()
        test.test_start_price_stream_success()
        test.test_start_price_stream_error()
        test.test_stop_price_stream_success()
        test.test_stop_price_stream_error()
        test.test_register_price_callback_success()
        test.test_register_price_callback_error()
        test.test_get_market_hours()
        test.test_get_market_status()
        
        print("✓ All market data service tests passed")
        return True
    except Exception as e:
        print(f"Error in market data service tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_tests() 