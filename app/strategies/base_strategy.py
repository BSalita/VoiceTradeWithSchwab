"""
Base Strategy - Abstract base class for all trading strategies
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..api.schwab_client import SchwabAPIClient
from ..models.order import OrderDuration, TradingSession

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    """
    
    def __init__(self):
        """Initialize the strategy"""
        self.api_client = SchwabAPIClient()
        self.strategy_name = self.__class__.__name__
        self.is_running = False
        self.config = {}
        logger.info(f"Initialized {self.strategy_name}")
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the trading strategy
        
        Args:
            **kwargs: Strategy-specific parameters
            
        Returns:
            Dict[str, Any]: Result of strategy execution
        """
        pass
    
    def start(self, **kwargs) -> bool:
        """
        Start the strategy
        
        Args:
            **kwargs: Strategy-specific parameters
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        logger.info(f"Starting {self.strategy_name}")
        self.is_running = True
        return True
    
    def stop(self) -> bool:
        """
        Stop the strategy
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        logger.info(f"Stopping {self.strategy_name}")
        self.is_running = False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the strategy
        
        Returns:
            Dict[str, Any]: Strategy status information
        """
        return {
            'name': self.strategy_name,
            'running': self.is_running
        }
    
    def place_order(self, symbol: str, quantity: int, order_type: str, 
                   side: str, price: Optional[float] = None,
                   session: str = "REGULAR", duration: str = "DAY",
                   strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        Place an order using the API client
        
        Args:
            symbol (str): Stock symbol
            quantity (int): Number of shares
            order_type (str): Type of order (MARKET, LIMIT, etc.)
            side (str): BUY or SELL
            price (Optional[float]): Price for limit orders
            session (str): Trading session (REGULAR, EXTENDED, ALL)
            duration (str): Order duration (DAY, GTC, GTD, FOK, IOC)
            strategy (Optional[str]): Strategy name for tracking
            
        Returns:
            Dict[str, Any]: Order response
        """
        logger.info(f"{self.strategy_name} placing {side} order for {quantity} shares of {symbol}")
        
        # Convert enums if needed
        if isinstance(session, TradingSession):
            session = session.value
        
        if isinstance(duration, OrderDuration):
            duration = duration.value
        
        order_data = {
            'symbol': symbol,
            'quantity': quantity,
            'side': side.upper(),
            'order_type': order_type,
            'session': session,
            'duration': duration
        }
        
        # Add strategy name if provided (for tracking)
        if strategy:
            order_data['strategy'] = strategy
        else:
            order_data['strategy'] = self.strategy_name
        
        if price and order_type.upper() != 'MARKET':
            order_data['price'] = price
            
        return self.api_client.place_order(order_data)

    def configure(self, **kwargs) -> Dict[str, Any]:
        """
        Configure the strategy with the provided parameters
        
        Args:
            **kwargs: Configuration parameters specific to the strategy
            
        Returns:
            Dict[str, Any]: Configuration result
        """
        logger.info(f"Configuring {self.strategy_name} strategy with: {kwargs}")
        
        # Store configuration
        self.config.update(kwargs)
        
        return {
            "success": True,
            "message": f"{self.strategy_name} configured successfully",
            "config": self.config
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the strategy configuration
        
        Returns:
            Dict[str, Any]: Validation result
        """
        # Base implementation just checks if config exists
        if not self.config:
            return {
                "success": False,
                "error": "Strategy not configured"
            }
            
        return {
            "success": True,
            "message": "Configuration is valid"
        } 