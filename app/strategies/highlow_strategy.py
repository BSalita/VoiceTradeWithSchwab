"""
High-Low trading strategy.
"""

from typing import Dict, Any, Optional

from app.services.service_registry import ServiceRegistry


class HighLowStrategy:
    """
    High-Low trading strategy.
    
    This strategy buys when the price drops below a low threshold
    and sells when the price rises above a high threshold.
    """
    
    def __init__(self, symbol: str, quantity: int, low_threshold: float, high_threshold: float):
        """Initialize the strategy."""
        self.symbol = symbol
        self.quantity = quantity
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.last_action = None
    
    def execute(self) -> Dict[str, Any]:
        """Execute the strategy."""
        # Get the trading service
        trading_service = ServiceRegistry.get("trading")
        if not trading_service:
            return {"success": False, "message": "Trading service not available"}
        
        # Get the current price
        quote = trading_service.get_quote(self.symbol)
        
        # Handle different quote structures
        # If the quote is a nested structure with 'quote' key (from MarketDataService)
        if isinstance(quote, dict) and 'quote' in quote:
            quote_data = quote['quote']
        else:
            # Direct quote from TradingService or mock
            quote_data = quote
            
        current_price = quote_data.get("last")
        
        # Check if we should buy or sell
        if current_price <= self.low_threshold and self.last_action != "BUY":
            # Buy
            result = trading_service.place_order(
                symbol=self.symbol,
                quantity=self.quantity,
                side="BUY",
                order_type="MARKET",
                price=None,
                session="REGULAR",
                duration="DAY",
                strategy="highlow"
            )
            self.last_action = "BUY"
            return {"success": True, "action": "BUY", "price": current_price, "result": result}
        
        elif current_price >= self.high_threshold and self.last_action != "SELL":
            # Sell
            result = trading_service.place_order(
                symbol=self.symbol,
                quantity=self.quantity,
                side="SELL",
                order_type="MARKET",
                price=None,
                session="REGULAR",
                duration="DAY",
                strategy="highlow"
            )
            self.last_action = "SELL"
            return {"success": True, "action": "SELL", "price": current_price, "result": result}
        
        # No action
        return {"success": True, "action": "NONE", "price": current_price} 