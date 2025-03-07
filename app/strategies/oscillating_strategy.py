"""
Oscillating Strategy - A strategy that buys and sells repeatedly based on price thresholds
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime, timedelta

from ..models.order import TradingSession, OrderDuration
from .base_strategy import BaseStrategy
from ..services.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

@dataclass
class OscillatingStrategyConfig:
    """Configuration for the Oscillating Strategy"""
    
    # Required parameters
    symbol: str
    quantity: int
    initial_price: Optional[float] = None
    
    # Price movement parameters
    price_range: float = 0.01  # Default 1% range
    is_percentage: bool = True  # True = percentage, False = fixed dollar amount
    
    # Normal distribution parameters
    use_normal_dist: bool = False
    std_dev: float = 1.0
    
    # Trading settings
    min_trade_interval: int = 60  # Seconds between trades
    max_positions: int = 3  # Maximum number of open positions
    
    # Session and duration settings
    session: str = TradingSession.REGULAR.value
    duration: str = OrderDuration.DAY.value
    
    # Advanced settings (optional)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class OscillatingStrategy(BaseStrategy):
    """
    A strategy that buys and sells repeatedly based on price thresholds
    
    This strategy monitors price movements and executes trades when prices cross
    certain thresholds. It's designed to take advantage of stocks that oscillate
    within a price range.
    
    Key features:
    - Sets buy and sell thresholds based on a percentage or fixed amount from current price
    - Can use normal distribution to randomize thresholds
    - Limits the number of open positions
    - Controls trade frequency with a minimum trade interval
    - Uses FIFO (first in, first out) for selling positions
    """
    
    def __init__(self, symbol=None, quantity=None, upper_limit=None, lower_limit=None, step_size=None, **kwargs):
        """Initialize the oscillating strategy"""
        super().__init__()
        self.config = {
            "symbol": symbol, 
            "quantity": quantity,
            "upper_limit": upper_limit,
            "lower_limit": lower_limit,
            "step_size": step_size
        }
        # Add any additional kwargs to config
        self.config.update(kwargs)
        
        self.lock = threading.Lock()
        self.active_positions = []
        self.last_trade_time = None
        self.buy_threshold = None
        self.sell_threshold = None
        self.strategy_start_time = None
        
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the oscillating strategy configuration
        
        Returns:
            Dict[str, Any]: Validation result with success/error information
        """
        # Call parent validation first
        result = super().validate_config()
        if not result.get("success", False):
            return result
            
        # Check required parameters
        if not self.config.get("symbol"):
            return {
                "success": False,
                "error": "Symbol is required"
            }
            
        if not self.config.get("quantity"):
            return {
                "success": False,
                "error": "Quantity is required"
            }
            
        # Validate specific parameters
        try:
            quantity = int(self.config.get("quantity", 0))
            if quantity <= 0:
                return {
                    "success": False,
                    "error": "Quantity must be a positive integer"
                }
        except (ValueError, TypeError):
            return {
                "success": False,
                "error": "Quantity must be a valid number"
            }
            
        # Validate price_range if specified
        if "price_range" in self.config:
            try:
                price_range = float(self.config.get("price_range", 0.01))
                if price_range <= 0:
                    return {
                        "success": False,
                        "error": "Price range must be positive"
                    }
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "error": "Price range must be a valid number"
                }
                
        return {
            "success": True,
            "message": "Configuration is valid"
        }
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the oscillating strategy
        
        Args:
            **kwargs: Strategy parameters matching OscillatingStrategyConfig fields
                symbol (str): Stock symbol to trade
                quantity (int): Number of shares per trade
                initial_price (float, optional): Starting price for calculations
                price_range (float, optional): Price movement range
                is_percentage (bool, optional): Whether price_range is percentage or fixed
                min_trade_interval (int, optional): Minimum seconds between trades
                max_positions (int, optional): Maximum number of concurrent positions
                
        Returns:
            Dict[str, Any]: Execution result with success flag and details
        """
        try:
            # Configure the strategy with provided parameters
            self.configure(**kwargs)
            
            # Validate parameters to make sure we have what we need
            validation = self.validate_config()
            if not validation.get("success", False):
                return validation
            
            # Get required parameters
            symbol = self.config.get("symbol")
            quantity = int(self.config.get("quantity", 0))
            initial_price = self.config.get("initial_price")
            
            logger.info(f"Executing oscillating strategy for {symbol} with {quantity} shares")
            
            # Get current price if not provided
            if not initial_price:
                quote = self.api_client.get_quote(symbol)
                initial_price = float(quote.get('lastPrice', 0))
                logger.info(f"Using current price of {initial_price} for {symbol}")
                # Store the initial price in config
                self.config["initial_price"] = initial_price
            
            # Calculate initial thresholds
            self._calculate_thresholds(initial_price)
            
            # Start the strategy
            success = self.start()
            
            # For testing - place an initial buy order right away
            if 'test' in kwargs and kwargs['test'] is True:
                # This is just for testing to avoid needing price stream
                logger.info("Test mode: executing immediate buy for testing")
                self._execute_buy(initial_price)
            
            return {
                "success": success,
                "message": f"Oscillating strategy started for {symbol}",
                "initialPrice": initial_price,
                "buyThreshold": self.buy_threshold,
                "sellThreshold": self.sell_threshold
            }
            
        except ValueError as e:
            logger.error(f"Value error executing oscillating strategy: {str(e)}")
            return {
                "success": False,
                "message": f"Configuration error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error executing oscillating strategy: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def start(self) -> bool:
        """
        Start the oscillating strategy
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Strategy is already running")
            return True
            
        try:
            # Start price streaming
            logger.info(f"Starting price stream for {self.config.get('symbol')}")
            self.api_client.start_price_stream([self.config.get('symbol')])
            self.api_client.register_price_callback(self.config.get('symbol'), self._on_price_update)
            
            self.is_running = True
            self.strategy_start_time = time.time()
            logger.info(f"Oscillating strategy started for {self.config.get('symbol')}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting oscillating strategy: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """
        Stop the oscillating strategy
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            with self.lock:
                if not self.is_running:
                    logger.warning("Oscillating strategy is not running")
                    return True
                
                # Stop price streaming
                logger.info(f"Stopping price stream for {self.config.get('symbol')}")
                self.api_client.stop_price_stream()
                
                # Update state
                self.is_running = False
                logger.info(f"Oscillating strategy stopped for {self.config.get('symbol')}")
                return True
                
        except Exception as e:
            logger.error(f"Error stopping oscillating strategy: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the strategy
        
        Returns:
            Dict[str, Any]: Status information
        """
        with self.lock:
            if not self.is_running or not self.config:
                return {
                    "running": False,
                    "message": "Strategy not running"
                }
                
            # Calculate runtime
            runtime = time.time() - self.strategy_start_time
            
            # Base status from parent class
            base_status = super().get_status()
            
            return {
                **base_status,
                "symbol": self.config.get("symbol"),
                "initialPrice": self.config.get("initial_price"),
                "currentPositions": len(self.active_positions),
                "maxPositions": self.config.get("max_positions", 3),
                "buyThreshold": self.buy_threshold,
                "sellThreshold": self.sell_threshold,
                "runningTime": runtime,
                "session": self.config.get("session", "REGULAR"),
                "duration": self.config.get("duration", "DAY")
            }
    
    def _calculate_thresholds(self, current_price: float) -> None:
        """
        Calculate buy and sell thresholds based on current price
        
        Args:
            current_price (float): Current price to base thresholds on
        """
        if self.config.get("is_percentage", False):
            # Calculate thresholds as percentage of current price
            range_amount = current_price * self.config.get("price_range", 0.01)
        else:
            # Use fixed dollar amount
            range_amount = self.config.get("price_range", 0.5)
        
        if self.config.get("use_normal_dist", False):
            # Use normal distribution to randomize thresholds
            range_factor = np.random.normal(0, self.config.get("std_dev", 0.5))
            adjusted_range = range_amount * (0.5 + 0.5 * range_factor)
            
            # Ensure range doesn't go negative
            adjusted_range = max(adjusted_range, range_amount * 0.1)
        else:
            adjusted_range = range_amount
        
        self.buy_threshold = current_price - adjusted_range
        self.sell_threshold = current_price + adjusted_range
        
        logger.debug(f"Thresholds calculated - Buy: {self.buy_threshold}, Sell: {self.sell_threshold}")
    
    def _on_price_update(self, symbol: str, price: float) -> None:
        """
        Handle price updates from the streaming API
        
        Args:
            symbol (str): Stock symbol
            price (float): Current price
        """
        try:
            if not self.is_running:
                return
                
            with self.lock:
                # Make sure this is for our configured symbol
                if symbol.upper() != self.config.get('symbol', '').upper():
                    return
                    
                logger.debug(f"Price update for {symbol}: {price}")
                
                # Check trade interval requirement
                if self.last_trade_time:
                    elapsed = time.time() - self.last_trade_time
                    min_interval = self.config.get('min_trade_interval', 60)
                    if elapsed < min_interval:
                        # Not enough time passed since last trade
                        return
                
                # Check thresholds for action
                if price <= self.buy_threshold:
                    # If we have not reached max positions allowed, buy
                    max_positions = self.config.get('max_positions', 3)
                    if len(self.active_positions) < max_positions:
                        self._execute_buy(price)
                    else:
                        logger.debug(f"Buy signal at {price} ignored - max positions ({max_positions}) reached")
                        
                elif price >= self.sell_threshold:
                    # If we have positions to sell, sell one
                    if self.active_positions:
                        self._execute_sell(price)
                    else:
                        logger.debug(f"Sell signal at {price} ignored - no positions to sell")
                        
        except Exception as e:
            logger.error(f"Error processing price update: {str(e)}")
    
    def _execute_buy(self, price: float) -> None:
        """
        Execute a buy order
        
        Args:
            price (float): Current price to execute at
        """
        with self.lock:
            # Get trading service
            trading_service = ServiceRegistry.get("trading")
            if not trading_service:
                logger.error("Trading service not available")
                return
                
            # Get order parameters
            session = self.config.get("session", "REGULAR")
            duration = self.config.get("duration", "DAY")
            
            # Place the order
            result = trading_service.place_order(
                symbol=self.config.get("symbol"),
                quantity=self.config.get("quantity", 1),
                side="BUY",
                order_type="MARKET",
                price=None,  # Market order
                session=session,
                duration=duration,
                strategy="oscillating"
            )
            
            # Store the position
            position = {
                'price': price,
                'quantity': self.config.get("quantity", 1),
                'time': time.time(),
                'order_id': result.get('order_id')
            }
            
            self.active_positions.append(position)
            self.last_trade_time = time.time()
            
            # Update thresholds for next trade
            self._calculate_thresholds(price)
            
            logger.info(f"BUY executed for {self.config.get('symbol')} at {price} - {self.config.get('quantity', 1)} shares")
    
    def _execute_sell(self, price: float) -> None:
        """
        Execute a sell order
        
        Args:
            price (float): Current price to execute at
        """
        with self.lock:
            # Make sure we have a position to sell
            if not self.active_positions:
                logger.warning("No active positions to sell")
                return
                
            # Get the oldest position (FIFO)
            position = self.active_positions.pop(0)
            
            # Get trading service
            trading_service = ServiceRegistry.get("trading")
            if not trading_service:
                logger.error("Trading service not available")
                # Put the position back
                self.active_positions.insert(0, position)
                return
                
            # Get order parameters
            session = self.config.get("session", "REGULAR")
            duration = self.config.get("duration", "DAY")
            
            # Place the sell order
            result = trading_service.place_order(
                symbol=self.config.get("symbol"),
                quantity=position.get("quantity", 1),
                side="SELL",
                order_type="MARKET",
                price=None,  # Market order
                session=session,
                duration=duration,
                strategy="oscillating"
            )
            
            # Update state
            self.last_trade_time = time.time()
            
            # Update thresholds for next trade
            self._calculate_thresholds(price)
            
            logger.info(f"SELL executed for {self.config.get('symbol')} at {price} - {position.get('quantity', 1)} shares") 