"""
Trading Service - Core business logic for trading operations
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from ..api.schwab_client import SchwabAPIClient
from ..models.order import Order, OrderType, OrderSide, TradingSession, OrderDuration
from ..models.trade_history import TradeHistory

logger = logging.getLogger(__name__)

class TradingService:
    """
    Service for executing trades and managing order operations
    independent of the user interface
    """
    
    def __init__(self, api_client=None):
        """
        Initialize the trading service
        
        Args:
            api_client: Optional API client instance. If None, will create a new instance.
        """
        self.api_client = api_client if api_client else SchwabAPIClient()
        self.trade_history = TradeHistory()
        logger.info("Trading service initialized")
    
    def place_order(self, symbol: str, quantity: int, side: str, order_type: str,
                   price: Optional[float] = None, session: str = "REGULAR",
                   duration: str = "DAY", strategy: Optional[str] = None) -> Dict[str, Any]:
        """Place an order."""
        if not self.api_client:
            raise ValueError("API client not set")
        
        # Create order parameters
        order_params = {
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "order_type": order_type,
            "price": price,
            "session": session,
            "duration": duration
        }
        
        # Add strategy if provided
        if strategy:
            order_params["strategy"] = strategy
        
        # Place the order
        result = self.api_client.place_order(order_params)
        
        return result
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        if not self.api_client:
            raise ValueError("API client not set")
        
        # Cancel the order
        result = self.api_client.cancel_order(order_id)
        
        return result
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all orders, optionally filtered by status."""
        if not self.api_client:
            raise ValueError("API client not set")
        
        # Get orders
        orders = self.api_client.get_orders()
        
        # Filter by status if provided
        if status and orders:
            # Make status comparison case-insensitive
            status_lower = status.lower()
            orders = [order for order in orders if order.get("status", "").lower() == status_lower]
        
        return orders
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions."""
        if not self.api_client:
            raise ValueError("API client not set")
        
        # Get positions
        positions = self.api_client.get_positions()
        
        return positions
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get a quote for a symbol."""
        if not self.api_client:
            raise ValueError("API client not set")
        
        # Get quote
        quote = self.api_client.get_quote(symbol)
        
        return quote
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.api_client:
            raise ValueError("API client not set")
        
        # Get account information
        try:
            account = self.api_client.get_account_info()
            return account
        except Exception as e:
            logger.error(f"Error getting account information: {str(e)}")
            # Return a basic account structure for mock mode
            return {
                "account_id": self.api_client.account_id or "mock_account",
                "status": "ACTIVE",
                "account_type": "INDIVIDUAL",
                "created_at": datetime.now().isoformat(),
                "currency": "USD",
                "buying_power": 100000.00,
                "cash": 100000.00,
                "equity": 100000.00
            }
    
    def get_trade_history(self, symbol: Optional[str] = None, 
                          limit: int = 10, 
                          strategy: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get trade history with optional filters
        
        Args:
            symbol: Optional symbol filter
            limit: Maximum number of trades to return
            strategy: Optional strategy name filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Trade history with success/error information
        """
        try:
            trades = self.trade_history.get_trades(
                symbol=symbol,
                limit=limit,
                strategy=strategy,
                start_time=start_time,
                end_time=end_time
            )
            
            return {
                'success': True,
                'trades': trades,
                'count': len(trades),
                'filters': {
                    'symbol': symbol,
                    'limit': limit,
                    'strategy': strategy
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting trade history: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to retrieve trade history: {str(e)}"
            }
    
    def export_trade_history(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Export trade history to CSV file
        
        Args:
            filename: Optional filename to export to
            
        Returns:
            Export result with success/error information
        """
        try:
            output_file = self.trade_history.export_to_csv(filename)
            
            return {
                'success': True,
                'filename': output_file,
                'message': f"Trade history exported to {output_file}"
            }
            
        except Exception as e:
            logger.error(f"Error exporting trade history: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to export trade history: {str(e)}"
            }
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information
        
        Returns:
            Account information with success/error information
        """
        try:
            account_info = self.api_client.get_account_info()
            positions = self.api_client.get_account_positions()
            balances = self.api_client.get_account_balances()
            
            return {
                'success': True,
                'account': account_info,
                'positions': positions,
                'balances': balances
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to retrieve account information: {str(e)}"
            }
    
    def get_mode(self) -> str:
        """
        Get the current trading mode
        
        Returns:
            str: The current trading mode (LIVE, PAPER, MOCK)
        """
        return self.api_client.trading_mode if self.api_client else "UNKNOWN" 