"""
Market Data Service - Service for retrieving market data
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from ..api.schwab_client import SchwabAPIClient

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Service for retrieving and streaming market data independent of the user interface
    """
    
    def __init__(self, api_client=None):
        """
        Initialize the market data service
        
        Args:
            api_client: Optional API client instance. If None, will create a new instance.
        """
        from ..api.schwab_client import SchwabAPIClient
        
        self.api_client = api_client if api_client else SchwabAPIClient()
        self.streaming_symbols = set()
        logger.info("Market data service initialized")
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get a quote for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote with success/error information
        """
        if not self.api_client:
            raise ValueError("API client not set")
        
        try:
            quote = self.api_client.get_quote(symbol)
            
            return {
                'success': True,
                'symbol': symbol,
                'quote': quote
            }
            
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get quote for {symbol}: {str(e)}"
            }
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get quotes for multiple symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Quotes with success/error information
        """
        if not self.api_client:
            raise ValueError("API client not set")
        
        try:
            quotes = self.api_client.get_quotes(symbols)
            
            return {
                'success': True,
                'quotes': quotes
            }
            
        except Exception as e:
            logger.error(f"Error getting quotes: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get quotes: {str(e)}"
            }
    
    def start_price_stream(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Start streaming price updates for symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Stream status with success/error information
        """
        if not self.api_client:
            raise ValueError("API client not set")
        
        try:
            # Start the price stream
            success = self.api_client.start_price_stream(symbols)
            
            if success:
                # Add to tracked symbols
                for symbol in symbols:
                    self.streaming_symbols.add(symbol)
                    
                logger.info(f"Started price stream for {len(symbols)} symbols")
                return {
                    'success': True,
                    'symbols': symbols,
                    'message': f"Started price stream for {len(symbols)} symbols"
                }
            else:
                logger.error("Failed to start price stream")
                return {
                    'success': False,
                    'error': "Failed to start price stream"
                }
            
        except Exception as e:
            logger.error(f"Error starting price stream: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to start price stream: {str(e)}"
            }
    
    def stop_price_stream(self) -> Dict[str, Any]:
        """
        Stop all price streams
        
        Returns:
            Stream status with success/error information
        """
        if not self.api_client:
            raise ValueError("API client not set")
        
        try:
            success = self.api_client.stop_price_stream()
            
            if success:
                count = len(self.streaming_symbols)
                self.streaming_symbols.clear()
                
                logger.info(f"Stopped price stream for {count} symbols")
                return {
                    'success': True,
                    'message': f"Stopped price stream for {count} symbols"
                }
            else:
                logger.error("Failed to stop price stream")
                return {
                    'success': False,
                    'error': "Failed to stop price stream"
                }
            
        except Exception as e:
            logger.error(f"Error stopping price stream: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to stop price stream: {str(e)}"
            }
    
    def register_price_callback(self, symbol: str, callback: Callable[[str, float], None]) -> Dict[str, Any]:
        """
        Register a callback for price updates
        
        Args:
            symbol: Stock symbol
            callback: Function to call on price updates
            
        Returns:
            Registration status with success/error information
        """
        if not self.api_client:
            raise ValueError("API client not set")
        
        try:
            self.api_client.register_price_callback(symbol, callback)
            
            logger.info(f"Registered price callback for {symbol}")
            return {
                'success': True,
                'symbol': symbol,
                'message': f"Registered price callback for {symbol}"
            }
            
        except Exception as e:
            logger.error(f"Error registering price callback: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to register price callback: {str(e)}"
            }
    
    def get_market_hours(self) -> Dict[str, Any]:
        """Get market hours."""
        if not self.api_client:
            raise ValueError("API client not set")
        
        # Get market hours
        hours = self.api_client.get_market_hours()
        
        return hours
    
    def get_market_status(self) -> str:
        """Get market status (OPEN, CLOSED, PRE_MARKET, AFTER_HOURS)."""
        if not self.api_client:
            raise ValueError("API client not set")
        
        # Get market status
        status = self.api_client.get_market_status()
        
        return status 