"""
Ladder Strategy - Buys or sells at multiple price points in a ladder pattern
"""

import logging
import time
from typing import Dict, Any, List, Optional
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class LadderStrategy(BaseStrategy):
    """
    Ladder trading strategy that places orders at multiple price points
    """
    
    def __init__(self):
        """Initialize the ladder strategy"""
        super().__init__()
        self.active_ladders = {}  # Track active ladder strategies
    
    def execute(self, symbol: str, quantity: int, side: str, 
               price_start: float, price_end: float, steps: int,
               order_type: str = 'LIMIT') -> Dict[str, Any]:
        """
        Execute a ladder strategy by placing multiple orders at different price points
        
        Args:
            symbol (str): Stock symbol to trade
            quantity (int): Number of shares per step
            side (str): 'BUY' or 'SELL'
            price_start (float): Starting price
            price_end (float): Ending price
            steps (int): Number of steps in the ladder
            order_type (str): Order type (usually LIMIT)
            
        Returns:
            Dict[str, Any]: Results of the ladder strategy execution
        """
        logger.info(f"Executing ladder {side} strategy for {symbol}")
        
        # Validate inputs
        if not symbol:
            raise ValueError("Symbol is required")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if side.upper() not in ['BUY', 'SELL']:
            raise ValueError("Side must be either 'BUY' or 'SELL'")
        if steps <= 0:
            raise ValueError("Steps must be greater than 0")
        if price_start <= 0 or price_end <= 0:
            raise ValueError("Prices must be greater than 0")
        
        # For buy ladders, start should be lower than end
        # For sell ladders, start should be higher than end
        if side.upper() == 'BUY' and price_start >= price_end:
            raise ValueError("For buy ladders, start price must be lower than end price")
        if side.upper() == 'SELL' and price_start <= price_end:
            raise ValueError("For sell ladders, start price must be higher than end price")
        
        # Calculate price increments
        if steps == 1:
            prices = [price_start]
        else:
            price_increment = (price_end - price_start) / (steps - 1)
            prices = [price_start + (i * price_increment) for i in range(steps)]
        
        # Round prices to 2 decimal places
        prices = [round(price, 2) for price in prices]
        
        # Get current market data for reference
        quote = self.api_client.get_quote(symbol)
        current_price = quote.get('lastPrice')
        
        if not current_price:
            logger.warning(f"Could not get current price for {symbol}")
        else:
            logger.info(f"Current price for {symbol}: ${current_price}")
        
        # Place orders for each price point
        orders = []
        success_count = 0
        
        for price in prices:
            try:
                order_result = self.place_order(
                    symbol=symbol,
                    quantity=quantity,
                    order_type=order_type.upper(),
                    side=side.upper(),
                    price=price
                )
                
                logger.info(f"Ladder order placed at ${price}: {order_result.get('orderId', 'Unknown ID')}")
                orders.append({
                    'success': True,
                    'order': order_result,
                    'price': price
                })
                success_count += 1
                
                # Small delay between orders
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ladder order failed at ${price}: {str(e)}")
                orders.append({
                    'success': False,
                    'error': str(e),
                    'price': price
                })
        
        # Create a unique ID for this ladder
        ladder_id = f"{symbol}_{side}_{int(time.time())}"
        
        # Store the ladder details
        self.active_ladders[ladder_id] = {
            'symbol': symbol,
            'side': side.upper(),
            'quantity': quantity,
            'price_start': price_start,
            'price_end': price_end,
            'steps': steps,
            'orders': orders,
            'timestamp': time.time(),
            'active': True
        }
        
        # Return results
        return {
            'success': success_count > 0,
            'ladder_id': ladder_id,
            'orders_placed': success_count,
            'orders_failed': steps - success_count,
            'strategy': self.strategy_name,
            'symbol': symbol,
            'quantity': quantity,
            'side': side.upper(),
            'price_start': price_start,
            'price_end': price_end,
            'steps': steps,
            'price_points': prices,
            'orders': orders,
            'market_price': current_price,
            'timestamp': time.time()
        }
    
    def cancel_ladder(self, ladder_id: str) -> Dict[str, Any]:
        """
        Cancel all orders in a ladder
        
        Args:
            ladder_id (str): ID of the ladder to cancel
            
        Returns:
            Dict[str, Any]: Results of the cancellation
        """
        if ladder_id not in self.active_ladders:
            raise ValueError(f"Ladder ID {ladder_id} not found")
        
        ladder = self.active_ladders[ladder_id]
        logger.info(f"Cancelling ladder {ladder_id} for {ladder['symbol']}")
        
        cancelled = 0
        failed = 0
        
        for order in ladder['orders']:
            if order['success']:
                try:
                    order_id = order['order'].get('order_id')
                    if order_id:
                        self.api_client.cancel_order(order_id)
                        cancelled += 1
                        logger.info(f"Cancelled order {order_id}")
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to cancel order: {str(e)}")
        
        # Update ladder status
        self.active_ladders[ladder_id]['active'] = False
        
        return {
            'success': failed == 0,
            'ladder_id': ladder_id,
            'orders_cancelled': cancelled,
            'orders_failed': failed,
            'timestamp': time.time()
        }
    
    def get_active_ladders(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active ladders
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of active ladders
        """
        # Return only active ladders
        return {ladder_id: ladder for ladder_id, ladder in self.active_ladders.items() 
                if ladder.get('active', True)} 