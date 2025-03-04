"""
Order processing performance test scenarios.

This module contains performance tests for the order processing
functionality of the Automated Trading System.
"""

import logging
import random
import time
from datetime import datetime, timedelta

from tests.performance.lib.base import PerformanceTest, LoadTest


class OrderProcessingTest(PerformanceTest):
    """Basic performance test for order processing operations."""
    
    def setup(self):
        """Set up the test environment."""
        self.logger.info("Setting up OrderProcessingTest")
        
        # Initialize services
        self.trading_service = self.get_service("trading")
        self.market_data_service = self.get_service("market_data")
        
        # Set up test data
        self.symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]
        self.order_ids = []
        
        # Test configuration
        self.test_iterations = self.config.get("iterations", 100)
        self.use_limit_orders = self.config.get("use_limit_orders", False)
        
        return True
    
    def execute(self):
        """Execute the test scenario."""
        self.logger.info(f"Executing OrderProcessingTest with {self.test_iterations} iterations")
        
        for i in range(self.test_iterations):
            # Select random symbol
            symbol = random.choice(self.symbols)
            
            # Random quantity between 1 and 100
            quantity = random.randint(1, 100)
            
            # Random side (buy or sell)
            side = "buy" if random.random() > 0.5 else "sell"
            
            try:
                # Get current quote for symbol
                with self.measure("get_quote"):
                    quote = self.market_data_service.get_quote(symbol)
                
                # Place order
                if self.use_limit_orders:
                    # Calculate limit price (slightly better than current price)
                    price = quote["last_price"]
                    if side == "buy":
                        # For buy, set price slightly lower
                        price = price * 0.99
                    else:
                        # For sell, set price slightly higher
                        price = price * 1.01
                    
                    with self.measure("place_limit_order"):
                        result = self.trading_service.place_limit_order(
                            symbol=symbol,
                            quantity=quantity,
                            side=side,
                            price=price
                        )
                else:
                    with self.measure("place_market_order"):
                        result = self.trading_service.place_market_order(
                            symbol=symbol,
                            quantity=quantity,
                            side=side
                        )
                
                # Store order ID for cleanup
                if result and "order_id" in result:
                    self.order_ids.append(result["order_id"])
                    
                    # Get order status
                    with self.measure("get_order_status"):
                        status = self.trading_service.get_order_status(result["order_id"])
                
            except Exception as e:
                self.logger.error(f"Error in iteration {i}: {str(e)}")
                continue
        
        return True
    
    def cleanup(self):
        """Clean up after the test."""
        self.logger.info("Cleaning up OrderProcessingTest")
        
        # Cancel any open orders
        for order_id in self.order_ids:
            try:
                self.trading_service.cancel_order(order_id)
            except Exception as e:
                self.logger.warning(f"Error canceling order {order_id}: {str(e)}")
        
        return True


class OrderProcessingLoadTest(LoadTest):
    """Load test for order processing with simulated users."""
    
    def setup(self):
        """Set up the test environment."""
        self.logger.info("Setting up OrderProcessingLoadTest")
        
        # Initialize services
        self.trading_service = self.get_service("trading")
        self.market_data_service = self.get_service("market_data")
        
        # Set up test data
        self.symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]
        self.order_lock = threading.Lock()
        self.order_ids = []
        
        return True
    
    def _user_task(self, user_id, results_queue, duration):
        """Task executed by each simulated user.
        
        Args:
            user_id: Unique identifier for the user.
            results_queue: Queue to store task results.
            duration: Duration in seconds for the task to run.
        """
        import threading
        
        # Per-user metrics
        operations = 0
        errors = 0
        
        # Use a different seed for each user for better randomization
        random.seed(user_id + int(time.time()))
        
        # Create user-specific logger
        logger = logging.getLogger(f"performance_tests.user_{user_id}")
        
        # Calculate end time
        end_time = time.time() + duration
        
        while time.time() < end_time:
            try:
                # Select random symbol
                symbol = random.choice(self.symbols)
                
                # Random quantity between 1 and 100
                quantity = random.randint(1, 100)
                
                # Random side (buy or sell)
                side = "buy" if random.random() > 0.5 else "sell"
                
                # Get current quote for symbol
                with self.measure(f"user_{user_id}.get_quote"):
                    quote = self.market_data_service.get_quote(symbol)
                
                # Place market order
                with self.measure(f"user_{user_id}.place_market_order"):
                    result = self.trading_service.place_market_order(
                        symbol=symbol,
                        quantity=quantity,
                        side=side
                    )
                
                # Store order ID for cleanup
                if result and "order_id" in result:
                    with self.order_lock:
                        self.order_ids.append(result["order_id"])
                
                operations += 1
                
            except Exception as e:
                logger.error(f"Error in user {user_id}: {str(e)}")
                errors += 1
            
            # Small delay between operations to avoid overwhelming the system
            time.sleep(random.uniform(0.1, 0.5))
        
        # Report results
        results_queue.put({
            "user_id": user_id,
            "operations": operations,
            "errors": errors
        })
    
    def cleanup(self):
        """Clean up after the test."""
        self.logger.info("Cleaning up OrderProcessingLoadTest")
        
        # Cancel any open orders
        for order_id in self.order_ids:
            try:
                self.trading_service.cancel_order(order_id)
            except Exception as e:
                self.logger.warning(f"Error canceling order {order_id}: {str(e)}")
        
        return True


class OrderMixTest(PerformanceTest):
    """Performance test with a mix of different order types and operations."""
    
    def setup(self):
        """Set up the test environment."""
        self.logger.info("Setting up OrderMixTest")
        
        # Initialize services
        self.trading_service = self.get_service("trading")
        self.market_data_service = self.get_service("market_data")
        self.account_service = self.get_service("account")
        
        # Test data
        self.symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]
        self.order_ids = []
        
        # Pre-test checks
        with self.measure("check_account"):
            self.account_info = self.account_service.get_account_info()
        
        self.buying_power = self.account_info.get("buying_power", 100000)
        
        return True
    
    def execute(self):
        """Execute the test scenario."""
        self.logger.info("Executing OrderMixTest")
        
        operations = [
            self._place_market_order,
            self._place_limit_order,
            self._get_open_orders,
            self._cancel_random_order,
            self._get_positions,
            self._get_historical_data
        ]
        
        weights = [0.3, 0.3, 0.1, 0.1, 0.1, 0.1]  # Probability distribution
        
        iterations = self.config.get("iterations", 100)
        
        for i in range(iterations):
            # Select operation based on weights
            operation = random.choices(operations, weights=weights, k=1)[0]
            
            try:
                operation()
            except Exception as e:
                self.logger.error(f"Error in iteration {i}: {str(e)}")
        
        return True
    
    def _place_market_order(self):
        """Place a market order."""
        symbol = random.choice(self.symbols)
        quantity = random.randint(1, 10)
        side = "buy" if random.random() > 0.5 else "sell"
        
        with self.measure("place_market_order"):
            result = self.trading_service.place_market_order(
                symbol=symbol,
                quantity=quantity,
                side=side
            )
        
        if result and "order_id" in result:
            self.order_ids.append(result["order_id"])
    
    def _place_limit_order(self):
        """Place a limit order."""
        symbol = random.choice(self.symbols)
        quantity = random.randint(1, 10)
        side = "buy" if random.random() > 0.5 else "sell"
        
        # Get current price
        with self.measure("get_quote"):
            quote = self.market_data_service.get_quote(symbol)
        
        price = quote["last_price"]
        
        # Adjust price for limit order
        if side == "buy":
            price = price * 0.97  # 3% below market
        else:
            price = price * 1.03  # 3% above market
        
        with self.measure("place_limit_order"):
            result = self.trading_service.place_limit_order(
                symbol=symbol,
                quantity=quantity,
                side=side,
                price=price
            )
        
        if result and "order_id" in result:
            self.order_ids.append(result["order_id"])
    
    def _get_open_orders(self):
        """Get open orders."""
        with self.measure("get_open_orders"):
            open_orders = self.trading_service.get_open_orders()
    
    def _cancel_random_order(self):
        """Cancel a random order if any exist."""
        if not self.order_ids:
            return
        
        order_id = random.choice(self.order_ids)
        
        with self.measure("cancel_order"):
            result = self.trading_service.cancel_order(order_id)
        
        if result and result.get("success", False):
            self.order_ids.remove(order_id)
    
    def _get_positions(self):
        """Get current positions."""
        with self.measure("get_positions"):
            positions = self.trading_service.get_positions()
    
    def _get_historical_data(self):
        """Get historical data for a symbol."""
        symbol = random.choice(self.symbols)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        with self.measure("get_historical_data"):
            data = self.market_data_service.get_historical_data(
                symbol=symbol,
                interval="1h",
                start_time=start_time,
                end_time=end_time
            )
    
    def cleanup(self):
        """Clean up after the test."""
        self.logger.info("Cleaning up OrderMixTest")
        
        # Cancel any open orders
        for order_id in self.order_ids:
            try:
                self.trading_service.cancel_order(order_id)
            except Exception as e:
                self.logger.warning(f"Error canceling order {order_id}: {str(e)}")
        
        return True 