"""
Basic Strategy - Simple buy/sell strategy for equities
"""

import logging
import time
from typing import Dict, Any, Optional
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class BasicStrategy(BaseStrategy):
    """
    Basic trading strategy for simple buy/sell operations
    """
    
    def __init__(self):
        """Initialize the basic strategy"""
        super().__init__()
    
    def execute(self, symbol: str, quantity: int, side: str, order_type: str = 'MARKET', 
               price: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute a basic buy or sell order
        
        Args:
            symbol (str): Stock symbol to trade
            quantity (int): Number of shares
            side (str): 'BUY' or 'SELL'
            order_type (str): Order type (MARKET, LIMIT, etc.)
            price (Optional[float]): Price for limit orders
            
        Returns:
            Dict[str, Any]: Order result
        """
        logger.info(f"Executing basic {side} strategy for {symbol}")
        
        # Validate inputs
        if not symbol:
            raise ValueError("Symbol is required")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if side.upper() not in ['BUY', 'SELL']:
            raise ValueError("Side must be either 'BUY' or 'SELL'")
        if order_type.upper() not in ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT']:
            raise ValueError("Unsupported order type")
        if order_type.upper() != 'MARKET' and price is None:
            raise ValueError("Price is required for non-market orders")
        
        # Get current market data
        quote = self.api_client.get_quote(symbol)
        current_price = quote.get('lastPrice')
        
        if not current_price:
            logger.warning(f"Could not get current price for {symbol}")
        else:
            logger.info(f"Current price for {symbol}: ${current_price}")
        
        # Place the order
        try:
            order_result = self.place_order(
                symbol=symbol,
                quantity=quantity,
                order_type=order_type.upper(),
                side=side.upper(),
                price=price
            )
            
            logger.info(f"Order placed successfully: {order_result.get('orderId', 'Unknown ID')}")
            return {
                'success': True,
                'order': order_result,
                'strategy': self.strategy_name,
                'symbol': symbol,
                'quantity': quantity,
                'side': side.upper(),
                'type': order_type.upper(),
                'price': price,
                'market_price': current_price,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Order execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'strategy': self.strategy_name,
                'symbol': symbol,
                'quantity': quantity,
                'side': side.upper(),
                'type': order_type.upper(),
                'price': price,
                'market_price': current_price,
                'timestamp': time.time()
            } 