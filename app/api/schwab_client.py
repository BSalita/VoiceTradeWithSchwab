"""
Schwab API Client - Handles authentication and API requests to Schwab Trading API
"""

import time
import json
import logging
import threading
import requests
import websocket
from typing import Dict, Any, Optional, List, Union, Callable
from ..config import config
import os
import random
import datetime

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Exception raised for API errors"""
    pass

class SchwabAPIClient:
    """Client for interacting with the Schwab Trading API"""
    
    def __init__(self):
        """Initialize the Schwab API client"""
        # Get API credentials from environment variables
        self.api_key = os.environ.get("SCHWAB_API_KEY", "")
        self.api_secret = os.environ.get("SCHWAB_API_SECRET", "")
        self.account_id = os.environ.get("SCHWAB_ACCOUNT_ID", "")
        self.base_url = config.SCHWAB_API_BASE_URL
        self.auth_url = config.SCHWAB_AUTH_URL
        self.stream_url = config.SCHWAB_STREAM_URL
        
        # Authentication state
        self.token = None
        self.token_expiry = 0
        
        # WebSocket connection state
        self.ws = None
        self.ws_connected = False
        self.price_callbacks = {}  # Symbol -> callback function
        self.ws_thread = None
        self.keep_streaming = False
        
        # Trading simulation state
        self.trading_mode = os.environ.get("TRADING_MODE", "LIVE")
        self.mock_orders = {}
        self.mock_positions = []
        self.mock_order_id = 1000
        self.paper_orders = {}  # Paper trading orders for PAPER mode
        self.paper_positions = {}  # Paper trading positions by symbol
        self.paper_balance = 100000.0  # Default paper trading balance ($100,000)
        
        # Log the trading mode
        print(f"Trading mode: {self.trading_mode}")
        print(f"Mock orders available: {hasattr(self, 'mock_orders')}")
        
        # Only check credentials in LIVE mode
        if not all([self.api_key, self.api_secret, self.account_id]) and self.trading_mode == 'LIVE':
            print("Missing required API credentials for LIVE trading")
            if self.trading_mode != "MOCK":
                raise ValueError("API credentials not properly configured for LIVE trading. Check .env file.")
    
    def authenticate(self) -> bool:
        """
        Authenticate with the Schwab API and get an access token
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # For PAPER mode testing with mock functionality, skip actual authentication
        if self.trading_mode == "PAPER" and os.environ.get("USE_MOCK_FOR_PAPER", "0") == "1":
            logger.info("Using mock authentication for PAPER mode")
            self.token = "mock_token_for_paper_testing"
            self.token_expiry = time.time() + 3600  # 1 hour expiry
            return True
            
        try:
            # Check if current token is still valid
            if self.token and time.time() < self.token_expiry:
                return True
                
            # Request new token
            response = requests.post(
                self.auth_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.api_key,
                    'client_secret': self.api_secret
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                # Set expiry with 10-second buffer
                expires_in = data.get('expires_in', 1800)  # Default to 30 minutes
                self.token_expiry = time.time() + expires_in - 10
                logger.info("Successfully authenticated with Schwab API")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers for API requests
        
        Returns:
            Dict[str, str]: Headers with authentication token
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get the headers for API requests
        
        Returns:
            Dict[str, str]: Headers with authentication token
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the Schwab API
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            endpoint (str): API endpoint
            params (Optional[Dict]): Query parameters
            data (Optional[Dict]): Request body data
            
        Returns:
            Dict[str, Any]: Response data
        """
        # For PAPER mode testing with mock functionality, use the mock implementation
        if self.trading_mode == "PAPER" and os.environ.get("USE_MOCK_FOR_PAPER", "0") == "1":
            # Save original trading mode
            original_mode = self.trading_mode
            # Temporarily switch to MOCK mode
            self.trading_mode = "MOCK"
            
            try:
                # Find the appropriate mock method for this request
                if endpoint.startswith("accounts") and method == "GET":
                    return self._mock_get_account_info()
                elif endpoint.startswith("quotes") and method == "GET":
                    # Extract symbol from endpoint or params
                    if "/" in endpoint:
                        symbol = endpoint.split("/")[-1]
                    elif params and "symbol" in params:
                        symbol = params.get("symbol")
                    else:
                        symbol = "AAPL"  # Default symbol
                    
                    logger.info(f"Getting mock quote for {symbol} in PAPER mode")
                    return self._get_mock_quote(symbol)
                elif endpoint.startswith("orders") and method == "POST":
                    return self._mock_place_order(data)
                elif endpoint.startswith("orders") and method == "GET":
                    return self._mock_get_orders()
                elif endpoint.startswith("orders") and method == "DELETE":
                    order_id = endpoint.split("/")[-1]
                    return self._mock_cancel_order(order_id)
                else:
                    # Default empty response
                    return {}
            finally:
                # Restore original mode
                self.trading_mode = original_mode
            
        if not self.authenticate():
            raise Exception("Authentication failed")
            
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}")
            # Include error response if available
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"Error details: {error_data}")
                except:
                    logger.error(f"Error response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            raise
    
    # Account methods
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information
        
        Returns:
            Dict[str, Any]: Account information
        """
        return self._make_request('GET', f'accounts/{self.account_id}')
    
    def check_connection(self) -> bool:
        """
        Check if the connection to the API is working
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self.trading_mode == "MOCK":
            # Always return True for mock mode
            return True
            
        # For PAPER mode testing, allow using mock functionality
        if self.trading_mode == "PAPER" and os.environ.get("USE_MOCK_FOR_PAPER", "0") == "1":
            logger.info("Using mock functionality for PAPER mode tests")
            # Set a mock token to bypass authentication
            self.token = "mock_token_for_paper_testing"
            self.token_expiry = time.time() + 3600  # 1 hour expiry
            return True
            
        try:
            # Try to authenticate as a basic connectivity test
            return self.authenticate()
        except Exception as e:
            logger.error(f"Connection check failed: {str(e)}")
            return False
    
    def get_account_positions(self) -> List[Dict[str, Any]]:
        """
        Get current account positions
        
        Returns:
            List[Dict[str, Any]]: List of positions
        """
        if self.trading_mode == 'MOCK':
            # Return mock positions (empty for simplicity)
            return []
        elif self.trading_mode == 'PAPER':
            # Convert paper positions to API format
            positions = []
            for symbol, data in self.paper_positions.items():
                positions.append({
                    'symbol': symbol,
                    'quantity': data['quantity'],
                    'averagePrice': data['averagePrice'],
                    'currentValue': data['quantity'] * self._get_paper_current_price(symbol)
                })
            return positions
        else:
            # Live API call
            endpoint = f"{self.base_url}/accounts/{self.account_id}/positions"
            response = requests.get(
                endpoint,
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get positions failed: {response.status_code} - {response.text}")
                raise APIError(f"Failed to get positions: {response.text}")
    
    def get_account_balances(self) -> Dict[str, Any]:
        """
        Get account balances
        
        Returns:
            Dict[str, Any]: Account balances
        """
        response = self._make_request('GET', f'accounts/{self.account_id}/balances')
        return response.get('balances', {})
    
    # Market data methods
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get a quote for a symbol
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            Dict[str, Any]: Quote data
        """
        # For PAPER mode with mock functionality, use mock quote
        if self.trading_mode == "PAPER" and os.environ.get("USE_MOCK_FOR_PAPER", "0") == "1":
            logger.info(f"Getting mock quote for {symbol} in PAPER mode")
            return self._get_mock_quote(symbol)
            
        # For MOCK mode, use mock quote
        if self.trading_mode == "MOCK":
            return self._get_mock_quote(symbol)
            
        # For LIVE and regular PAPER mode, use API
        return self._make_request('GET', f'quotes/{symbol}')
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple symbols
        
        Args:
            symbols (List[str]): List of stock symbols
            
        Returns:
            Dict[str, Dict[str, Any]]: Quote data for each symbol
        """
        symbols_str = ','.join(symbols)
        response = self._make_request('GET', 'marketdata/quotes', params={'symbols': symbols_str})
        return response.get('quotes', {})
    
    # Order methods
    def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place an order
        
        Args:
            order_data (Dict[str, Any]): Order parameters
            
        Returns:
            Dict[str, Any]: Order result
        """
        # For PAPER mode with mock functionality, use mock order placement
        if self.trading_mode == "PAPER" and os.environ.get("USE_MOCK_FOR_PAPER", "0") == "1":
            logger.info(f"Placing mock order in PAPER mode: {order_data}")
            return self._mock_place_order(order_data)
            
        # For MOCK mode, use mock order placement
        if self.trading_mode == "MOCK":
            return self._mock_place_order(order_data)
            
        # For LIVE and regular PAPER mode, use API
        return self._make_request('POST', 'orders', data=order_data)
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order
        
        Args:
            order_id (str): Order ID to cancel
            
        Returns:
            Dict[str, Any]: Cancellation result
        """
        # For PAPER mode with mock functionality, use mock cancellation
        if self.trading_mode == "PAPER" and os.environ.get("USE_MOCK_FOR_PAPER", "0") == "1":
            logger.info(f"Cancelling mock order in PAPER mode: {order_id}")
            return self._mock_cancel_order(order_id)
            
        # For MOCK mode, use mock cancellation
        if self.trading_mode == "MOCK":
            return self._mock_cancel_order(order_id)
            
        # For LIVE and regular PAPER mode, use API
        return self._make_request('DELETE', f'orders/{order_id}')
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all orders, optionally filtered by status
        
        Args:
            status (Optional[str]): Filter by order status
            
        Returns:
            List[Dict[str, Any]]: List of orders
        """
        # For PAPER mode with mock functionality, use mock orders
        if self.trading_mode == "PAPER" and os.environ.get("USE_MOCK_FOR_PAPER", "0") == "1":
            logger.info(f"Getting mock orders in PAPER mode")
            return self._mock_get_orders()
            
        # For MOCK mode, use mock orders
        if self.trading_mode == "MOCK":
            return self._mock_get_orders()
            
        # For LIVE and regular PAPER mode, use API
        params = {}
        if status:
            params['status'] = status
        return self._make_request('GET', 'orders', params=params)
        
    # WebSocket streaming methods
    def start_price_stream(self, symbols: List[str]) -> bool:
        """
        Start streaming real-time price data for the specified symbols
        
        Args:
            symbols (List[str]): List of stock symbols to stream
            
        Returns:
            bool: True if stream started successfully, False otherwise
        """
        if not self.authenticate():
            logger.error("Authentication failed. Cannot start price stream.")
            return False
            
        if self.ws_connected:
            logger.warning("WebSocket already connected. Close it first.")
            return False
            
        try:
            # Create a new WebSocket connection
            ws_url = f"{self.stream_url}?token={self.token}"
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
                on_open=self._on_ws_open
            )
            
            # Set the symbols to subscribe to on open
            self.ws.symbols_to_subscribe = symbols
            
            # Start the WebSocket in a separate thread
            self.keep_streaming = True
            self.ws_thread = threading.Thread(target=self._run_websocket)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            logger.info(f"Started price stream for symbols: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting price stream: {str(e)}")
            return False
    
    def stop_price_stream(self) -> bool:
        """
        Stop streaming price data
        
        Returns:
            bool: True if stream stopped successfully, False otherwise
        """
        if not self.ws_connected:
            logger.warning("WebSocket not connected")
            return False
            
        try:
            self.keep_streaming = False
            self.ws.close()
            
            # Wait for the thread to finish
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=2.0)
                
            self.ws_connected = False
            logger.info("Stopped price stream")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping price stream: {str(e)}")
            return False
    
    def register_price_callback(self, symbol: str, callback: Callable[[str, float], None]) -> None:
        """
        Register a callback function for real-time price updates
        
        Args:
            symbol (str): Stock symbol
            callback (Callable): Function to call when price updates are received
                                The function should accept (symbol, price) parameters
        """
        self.price_callbacks[symbol.upper()] = callback
        logger.info(f"Registered price callback for {symbol}")
    
    def _run_websocket(self) -> None:
        """Run the WebSocket connection in a separate thread"""
        try:
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"WebSocket thread error: {str(e)}")
        finally:
            self.ws_connected = False
            logger.info("WebSocket connection closed")
            
    def _on_ws_open(self, ws) -> None:
        """Callback when WebSocket connection is opened"""
        logger.info("WebSocket connection opened")
        self.ws_connected = True
        
        # Subscribe to symbols
        if hasattr(ws, 'symbols_to_subscribe') and ws.symbols_to_subscribe:
            self._subscribe_to_symbols(ws.symbols_to_subscribe)
    
    def _on_ws_message(self, ws, message: str) -> None:
        """Callback when a message is received from the WebSocket"""
        try:
            data = json.loads(message)
            
            # Handle different types of messages
            msg_type = data.get('type')
            
            if msg_type == 'PRICE_UPDATE':
                symbol = data.get('symbol', '').upper()
                price = data.get('price')
                
                if symbol and price is not None and symbol in self.price_callbacks:
                    # Call the registered callback for this symbol
                    callback_fn = self.price_callbacks[symbol]
                    callback_fn(symbol, float(price))
                    
            elif msg_type == 'HEARTBEAT':
                # Just a keep-alive message, no action needed
                pass
                
            elif msg_type == 'ERROR':
                error_msg = data.get('message', 'Unknown WebSocket error')
                logger.error(f"WebSocket error: {error_msg}")
                
            else:
                logger.debug(f"Unhandled WebSocket message type: {msg_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Error decoding WebSocket message: {message}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
    
    def _on_ws_error(self, ws, error) -> None:
        """Callback when a WebSocket error occurs"""
        logger.error(f"WebSocket error: {str(error)}")
    
    def _on_ws_close(self, ws, close_status_code, close_msg) -> None:
        """Callback when WebSocket connection is closed"""
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.ws_connected = False
        
        # Reconnect if needed
        if self.keep_streaming:
            logger.info("Attempting to reconnect WebSocket...")
            time.sleep(2)  # Wait before reconnecting
            self._run_websocket()
    
    def _subscribe_to_symbols(self, symbols: List[str]) -> None:
        """
        Subscribe to price updates for the specified symbols
        
        Args:
            symbols (List[str]): List of stock symbols to subscribe to
        """
        if not self.ws_connected:
            logger.warning("WebSocket not connected. Cannot subscribe to symbols.")
            return
            
        try:
            subscription_msg = {
                'action': 'SUBSCRIBE',
                'symbols': [symbol.upper() for symbol in symbols]
            }
            
            self.ws.send(json.dumps(subscription_msg))
            logger.info(f"Subscribed to symbols: {symbols}")
            
        except Exception as e:
            logger.error(f"Error subscribing to symbols: {str(e)}")
    
    def _mock_place_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """Place a mock order."""
        # Generate a unique order ID
        order_id = str(self.mock_order_id)
        self.mock_order_id += 1
        
        # Get the order type - standardize on order_type
        order_type = order_params.get("order_type")
        if order_type is None:
            order_type = order_params.get("orderType", "MARKET")
        
        # Create a mock order
        mock_order = {
            "order_id": order_id,
            "symbol": order_params.get("symbol"),
            "quantity": order_params.get("quantity"),
            "side": order_params.get("side"),
            "order_type": order_type,  # Use order_type consistently
            "price": order_params.get("price"),
            "session": order_params.get("session", "REGULAR"),
            "duration": order_params.get("duration", "DAY"),
            "status": "SUBMITTED",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # Add strategy if provided
        if "strategy" in order_params:
            mock_order["strategy"] = order_params.get("strategy")
        
        # Store the mock order
        self.mock_orders[order_id] = mock_order
        print(f"DEBUG: Placed mock order: {mock_order}")
        print(f"DEBUG: Total mock orders: {len(self.mock_orders)}")
        
        # Return a response similar to what the API would return
        return {
            "success": True,
            "order_id": order_id,
            "order": {
                "order_id": order_id,
                "status": "SUBMITTED",
                "symbol": order_params.get("symbol"),
                "quantity": order_params.get("quantity"),
                "side": order_params.get("side"),
                "order_type": order_type  # Use order_type consistently
            }
        }
    
    def _mock_cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a mock order."""
        if order_id in self.mock_orders:
            self.mock_orders[order_id]['status'] = 'canceled'
            return {
                'success': True,
                'message': f'Order {order_id} cancelled successfully',
                'order_id': order_id
            }
        else:
            return {
                'success': False,
                'message': f'Order {order_id} not found',
                'order_id': order_id
            }
    
    def _get_mock_orders(self) -> List[Dict[str, Any]]:
        """Get mock orders."""
        # Get all orders
        orders = list(self.mock_orders.values())
        print(f"DEBUG: Getting mock orders. Total: {len(orders)}")
        
        return orders
    
    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:
        """Mock implementation of get_quote for PAPER mode"""
        # Generate somewhat realistic prices
        base_price = 150.0 if symbol == "AAPL" else 250.0
        if symbol == "MSFT":
            base_price = 250.0
        elif symbol == "GOOGL":
            base_price = 2000.0
        elif symbol == "AMZN":
            base_price = 100.0
            
        # Add some randomness
        variation = base_price * 0.001 * random.randint(-10, 10)
        price = base_price + variation
        
        # Create a realistic quote
        return {
            "symbol": symbol,
            "bid": price - 0.1,
            "ask": price + 0.1,
            "last": price,
            "lastPrice": price,
            "volume": random.randint(10000, 100000),
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def _mock_retrieve_order(self, order_id: str) -> Dict[str, Any]:
        """Get a mock order."""
        # Check if the order exists
        if order_id not in self.mock_orders:
            return {"success": False, "message": f"Order {order_id} not found"}
        
        mock_order = self.mock_orders[order_id]
        mock_order_dict = mock_order.copy()
        # For API compatibility, add orderType field if communicating with external systems
        if "order_type" in mock_order_dict and self._external_api_mode:
            mock_order_dict["orderType"] = mock_order_dict["order_type"]
        
        return {"success": True, "order": mock_order_dict}
    
    def _paper_place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place an order in PAPER mode."""
        symbol = order_data.get("symbol", "").upper()
        quantity = int(order_data.get("quantity", 0))
        side = order_data.get("side", "BUY")
        
        # Get order type from order_type field
        order_type = order_data.get("order_type")
        if order_type is None:
            order_type = order_data.get("orderType", "MARKET")
        price = order_data.get("price")
        
        # Generate a unique order ID
        order_id = f"PAPER-{os.urandom(4).hex()}"
        
        # Create the order object
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "quantity": quantity,
            "side": side,
            "order_type": order_type,  # Use order_type consistently
            "price": price,
            "session": order_data.get("session", "REGULAR"),
            "duration": order_data.get("duration", "DAY"),
            "status": "SUBMITTED",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }
        
        # For API compatibility, add orderType field if communicating with external systems
        if self._external_api_mode:
            order["orderType"] = order_type
        
        # Store the order
        self.mock_orders[order_id] = order
        
        logger.info(f"Created mock order: {order}")
        
        # Return success response
        return {
            "success": True,
            "order_id": order_id,
            "order": order
        }
    
    # Mock methods for PAPER mode testing
    def _mock_get_account_info(self) -> Dict[str, Any]:
        """Mock implementation of get_account_info for PAPER mode"""
        return {
            "account_id": self.account_id,
            "account_type": "PAPER",
            "balance": 100000.0,
            "buying_power": 100000.0,
            "cash": 100000.0,
            "currency": "USD",
            "status": "ACTIVE"
        }
    
    def _mock_get_orders(self) -> List[Dict[str, Any]]:
        """Mock implementation of get_orders for PAPER mode"""
        return list(self.mock_orders.values())

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get positions for the account
        
        Returns:
            List[Dict[str, Any]]: List of positions
        """
        # For mock mode, return mock positions
        if self.trading_mode == "MOCK":
            return self._mock_get_positions()
        
        # For PAPER mode testing with mock functionality
        if self.trading_mode == "PAPER" and os.environ.get("USE_MOCK_FOR_PAPER", "0") == "1":
            return self._mock_get_positions()
        
        endpoint = f'accounts/{self.account_id}/positions'
        return self._make_request('GET', endpoint)

    def _mock_get_positions(self) -> List[Dict[str, Any]]:
        """
        Get mock positions for testing
        
        Returns:
            List[Dict[str, Any]]: List of mock positions
        """
        # In mock mode, use the mock positions list
        mock_positions = []
        
        # Add some default mock positions if the list is empty
        if not mock_positions:
            mock_positions = [
                {
                    "symbol": "AAPL",
                    "quantity": 10,
                    "average_price": 150.0,
                    "current_price": 155.25,
                    "market_value": 1552.50,
                    "unrealized_pl": 52.50,
                    "unrealized_pl_percent": 3.5
                },
                {
                    "symbol": "MSFT",
                    "quantity": 5,
                    "average_price": 290.0,
                    "current_price": 305.75,
                    "market_value": 1528.75,
                    "unrealized_pl": 78.75,
                    "unrealized_pl_percent": 5.43
                },
                {
                    "symbol": "GOOG",
                    "quantity": 3,
                    "average_price": 2500.0,
                    "current_price": 2575.50,
                    "market_value": 7726.50,
                    "unrealized_pl": 226.50,
                    "unrealized_pl_percent": 3.02
                }
            ]
        
        return mock_positions 