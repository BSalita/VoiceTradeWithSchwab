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
    
    def __init__(self):
        """Initialize the oscillating strategy"""
        super().__init__()
        self.config = None
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
                initial_price (float, optional): Starting price for calculating thresholds
                price_range (float, optional): Range percentage (0.01 = 1%) or fixed amount
                is_percentage (bool, optional): True to use percentage, False for fixed amount
                use_normal_dist (bool, optional): True to use normal distribution randomization
                std_dev (float, optional): Standard deviation for normal distribution
                min_trade_interval (int, optional): Seconds between trades
                max_positions (int, optional): Maximum number of open positions
                session (str, optional): Trading session (REGULAR, EXTENDED)
                duration (str, optional): Order duration (DAY, GTC)
                
        Returns:
            Dict[str, Any]: Result of strategy execution with success/error information
        """
        try:
            # Update configuration with kwargs
            if kwargs:
                self.configure(**kwargs)
                
            # Validate configuration
            validation = self.validate_config()
            if not validation.get("success", False):
                return validation
            
            # Use configuration for execution parameters
            symbol = self.config.get("symbol")
            quantity = int(self.config.get("quantity", 0))
            initial_price = self.config.get("initial_price")
            
            # Log strategy parameters
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
            bool: True if started successfully
        """
        try:
            with self.lock:
                if self.is_running:
                    logger.warning("Oscillating strategy is already running")
                    return True
                
                # Set strategy state
                self.is_running = True
                self.strategy_start_time = datetime.now()
                
                # Start price streaming
                logger.info(f"Starting price stream for {self.config.symbol}")
                self.api_client.start_price_stream([self.config.symbol])
                self.api_client.register_price_callback(self.config.symbol, self._on_price_update)
                
                logger.info(f"Oscillating strategy started for {self.config.symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error starting oscillating strategy: {str(e)}")
            self.is_running = False
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
                logger.info(f"Stopping price stream for {self.config.symbol}")
                self.api_client.stop_price_stream()
                
                # Update state
                self.is_running = False
                logger.info(f"Oscillating strategy stopped for {self.config.symbol}")
                return True
                
        except Exception as e:
            logger.error(f"Error stopping oscillating strategy: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the oscillating strategy
        
        Returns:
            Dict[str, Any]: Strategy status
        """
        with self.lock:
            base_status = super().get_status()
            
            if not self.is_running or not self.config:
                return base_status
            
            # Add strategy-specific status
            runtime = None
            if self.strategy_start_time:
                runtime = str(datetime.now() - self.strategy_start_time)
            
            return {
                **base_status,
                "symbol": self.config.symbol,
                "initialPrice": self.config.initial_price,
                "currentPositions": len(self.active_positions),
                "maxPositions": self.config.max_positions,
                "buyThreshold": self.buy_threshold,
                "sellThreshold": self.sell_threshold,
                "lastTradeTime": self.last_trade_time,
                "runningTime": runtime,
                "session": self.config.session,
                "duration": self.config.duration
            }
    
    def _calculate_thresholds(self, current_price: float) -> None:
        """
        Calculate buy and sell thresholds based on current price
        
        Args:
            current_price (float): Current price to base thresholds on
        """
        if self.config.is_percentage:
            # Calculate thresholds as percentage of current price
            range_amount = current_price * self.config.price_range
        else:
            # Use fixed dollar amount
            range_amount = self.config.price_range
        
        if self.config.use_normal_dist:
            # Use normal distribution to randomize thresholds
            range_factor = np.random.normal(0, self.config.std_dev)
            adjusted_range = range_amount * (0.5 + 0.5 * range_factor)
            
            # Ensure range doesn't go negative
            adjusted_range = max(adjusted_range, range_amount * 0.1)
        else:
            adjusted_range = range_amount
        
        self.buy_threshold = current_price - adjusted_range
        self.sell_threshold = current_price + adjusted_range
        
        logger.debug(f"Thresholds calculated - Buy: {self.buy_threshold}, Sell: {self.sell_threshold}")
    
    def _on_price_update(self, price_data: Dict[str, Any]) -> None:
        """
        Handle price updates from the streaming API
        
        Args:
            price_data (Dict[str, Any]): Price update data
        """
        try:
            if not self.is_running:
                return
                
            with self.lock:
                # Extract price and validate
                current_price = float(price_data.get('price', 0))
                if current_price <= 0:
                    logger.warning(f"Invalid price received for {self.config.get('symbol')}: {price_data}")
                    return
                
                logger.debug(f"Price update for {self.config.get('symbol')}: {current_price}")
                
                # Check if we can trade (based on time interval)
                current_time = datetime.now()
                min_interval = self.config.get('min_trade_interval', 60)
                
                if self.last_trade_time:
                    time_since_last_trade = (current_time - self.last_trade_time).total_seconds()
                    if time_since_last_trade < min_interval:
                        remaining = min_interval - time_since_last_trade
                        logger.debug(f"Trade cooldown: {remaining:.1f}s remaining until next trade")
                        return
                
                # Check position count
                max_positions = self.config.get('max_positions', 3)
                current_positions = len(self.active_positions)
                
                # Check for buy opportunity
                if current_price <= self.buy_threshold and current_positions < max_positions:
                    logger.info(f"Buy signal triggered: Price {current_price} <= threshold {self.buy_threshold}")
                    logger.info(f"Current positions: {current_positions}, Max: {max_positions}")
                    self._execute_buy(current_price)
                    return
                
                # Check for sell opportunity if we have positions
                if current_price >= self.sell_threshold and self.active_positions:
                    logger.info(f"Sell signal triggered: Price {current_price} >= threshold {self.sell_threshold}")
                    logger.info(f"Active positions: {len(self.active_positions)}")
                    self._execute_sell(current_price)
                    return
                
                # Log threshold distances for monitoring
                if current_positions < max_positions:
                    buy_distance = ((current_price / self.buy_threshold) - 1) * 100
                    logger.debug(f"Distance to buy: {buy_distance:.2f}% (Current: {current_price}, Threshold: {self.buy_threshold})")
                
                if self.active_positions:
                    sell_distance = ((self.sell_threshold / current_price) - 1) * 100
                    logger.debug(f"Distance to sell: {sell_distance:.2f}% (Current: {current_price}, Threshold: {self.sell_threshold})")
                
        except ValueError as e:
            logger.error(f"Value error in price update: {str(e)}")
        except TypeError as e:
            logger.error(f"Type error in price update: {str(e)}")
        except KeyError as e:
            logger.error(f"Missing key in price data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing price update: {str(e)}")
    
    def _execute_buy(self, price: float) -> None:
        """
        Execute a buy order
        
        Args:
            price (float): Current price
        """
        try:
            # Get session and duration (convert strings to enum values if needed)
            session = self.config.session
            if isinstance(session, str):
                session = TradingSession(session).value
                
            duration = self.config.duration
            if isinstance(duration, str):
                duration = OrderDuration(duration).value
                
            order_result = self.place_order(
                symbol=self.config.symbol,
                quantity=self.config.quantity,
                order_type="MARKET",
                side="BUY",
                session=session,
                duration=duration,
                strategy="oscillating"  # Add strategy name for history tracking
            )
            
            # Record the trade
            position = {
                'orderId': order_result.get('orderId', 'unknown'),
                'buyPrice': price,
                'quantity': self.config.quantity,
                'buyTime': datetime.now()
            }
            
            self.active_positions.append(position)
            self.last_trade_time = datetime.now()
            
            # Recalculate thresholds for next trade
            self._calculate_thresholds(price)
            
            logger.info(f"BUY executed for {self.config.symbol} at {price} - {self.config.quantity} shares")
            
        except ValueError as e:
            logger.error(f"Value error executing buy: {str(e)}")
        except AttributeError as e:
            logger.error(f"Attribute error executing buy: {str(e)}")
        except ConnectionError as e:
            logger.error(f"Connection error executing buy: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error executing buy: {str(e)}")
    
    def _execute_sell(self, price: float) -> None:
        """
        Execute a sell order (FIFO - oldest position first)
        
        Args:
            price (float): Current price
        """
        try:
            if not self.active_positions:
                return
                
            # Get oldest position (FIFO)
            position = self.active_positions.pop(0)
            
            # Get session and duration (convert strings to enum values if needed)
            session = self.config.session
            if isinstance(session, str):
                session = TradingSession(session).value
                
            duration = self.config.duration
            if isinstance(duration, str):
                duration = OrderDuration(duration).value
            
            order_result = self.place_order(
                symbol=self.config.symbol,
                quantity=position['quantity'],
                order_type="MARKET",
                side="SELL",
                session=session,
                duration=duration,
                strategy="oscillating"  # Add strategy name for history tracking
            )
            
            # Calculate profit/loss
            buy_price = position['buyPrice']
            profit = (price - buy_price) * position['quantity']
            profit_percent = ((price / buy_price) - 1) * 100
            
            self.last_trade_time = datetime.now()
            
            # Recalculate thresholds for next trade
            self._calculate_thresholds(price)
            
            logger.info(f"SELL executed for {self.config.symbol} at {price} - {position['quantity']} shares")
            logger.info(f"P/L: ${profit:.2f} ({profit_percent:.2f}%)")
            
        except ValueError as e:
            logger.error(f"Value error executing sell: {str(e)}")
        except KeyError as e:
            logger.error(f"Missing key in position data: {str(e)}")
        except AttributeError as e:
            logger.error(f"Attribute error executing sell: {str(e)}")
        except ConnectionError as e:
            logger.error(f"Connection error executing sell: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error executing sell: {str(e)}") 