"""
Strategy Service - Service for managing trading strategies
"""

import logging
import time
from typing import Dict, List, Any, Optional, Type
from ..strategies import get_strategy, BaseStrategy
from ..config import config
import importlib

from app.strategies.highlow_strategy import HighLowStrategy
from app.services.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

class StrategyService:
    """
    Service for managing trading strategies independent of the user interface
    """
    
    def __init__(self):
        """Initialize the strategy service"""
        self.active_strategies = {}  # Strategy instances by key
        self.valid_strategy_types = config.STRATEGIES  # From config
        self.strategies = {}
        self.strategy_types = {
            "highlow": HighLowStrategy
        }
        logger.info("Strategy service initialized")
    
    def start_strategy(self, strategy_type: str, **kwargs) -> Dict[str, Any]:
        """
        Start a trading strategy
        
        Args:
            strategy_type: Type of strategy to start (e.g., 'ladder', 'oscillating')
            **kwargs: Strategy configuration parameters
            
        Returns:
            Strategy status with success/error information
        """
        try:
            # Check if the strategy type is valid
            if strategy_type not in self.valid_strategy_types:
                return {
                    'success': False,
                    'error': f"Invalid strategy type: {strategy_type}",
                    'valid_types': list(self.valid_strategy_types.keys())
                }
            
            # Generate a unique key for the strategy
            strategy_key = f"{strategy_type}_{kwargs.get('symbol')}_{int(time.time())}"
            
            # Create and execute the strategy
            strategy_class = get_strategy(strategy_type)
            strategy = strategy_class()
            result = strategy.execute(**kwargs)
            
            # Store the strategy if successful
            if result.get('success', False):
                self.active_strategies[strategy_key] = strategy
                logger.info(f"Started {strategy_type} strategy with key {strategy_key}")
                
                # Add the strategy key to the result
                result['strategy_key'] = strategy_key
                return result
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error starting {strategy_type} strategy: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to start {strategy_type} strategy: {str(e)}"
            }
    
    def stop_strategy(self, strategy_key: str) -> Dict[str, Any]:
        """
        Stop a running strategy
        
        Args:
            strategy_key: Key of the strategy to stop
            
        Returns:
            Strategy status with success/error information
        """
        try:
            # Check if the strategy exists
            strategy = self.active_strategies.get(strategy_key)
            if not strategy:
                return {
                    'success': False,
                    'error': f"Strategy not found: {strategy_key}"
                }
            
            # Stop the strategy
            result = strategy.stop()
            
            # Remove the strategy if successful
            if result.get('success', False):
                del self.active_strategies[strategy_key]
                logger.info(f"Stopped strategy {strategy_key}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error stopping strategy {strategy_key}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to stop strategy {strategy_key}: {str(e)}"
            }
    
    def stop_all_strategies(self) -> Dict[str, Any]:
        """
        Stop all running strategies
        
        Returns:
            Strategies status with success/error information
        """
        results = {
            'success': True,
            'stopped': 0,
            'failed': 0,
            'details': []
        }
        
        # Copy keys to avoid modifying dictionary during iteration
        strategy_keys = list(self.active_strategies.keys())
        
        for key in strategy_keys:
            result = self.stop_strategy(key)
            results['details'].append({
                'strategy_key': key,
                'success': result.get('success', False),
                'error': result.get('error')
            })
            
            if result.get('success', False):
                results['stopped'] += 1
            else:
                results['failed'] += 1
        
        # Set overall success to False if any failed
        if results['failed'] > 0:
            results['success'] = False
            results['error'] = f"Failed to stop {results['failed']} strategies"
            
        logger.info(f"Stopped {results['stopped']} strategies, {results['failed']} failed")
        return results
    
    def get_strategy_status(self, strategy_key: str) -> Dict[str, Any]:
        """
        Get status of a running strategy
        
        Args:
            strategy_key: Key of the strategy
            
        Returns:
            Strategy status with success/error information
        """
        try:
            # Check if the strategy exists
            strategy = self.active_strategies.get(strategy_key)
            if not strategy:
                return {
                    'success': False,
                    'error': f"Strategy not found: {strategy_key}"
                }
            
            # Get the strategy status
            status = strategy.get_status()
            
            return {
                'success': True,
                'strategy_key': strategy_key,
                'status': status
            }
            
        except Exception as e:
            logger.error(f"Error getting status for strategy {strategy_key}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to get status for strategy {strategy_key}: {str(e)}"
            }
    
    def get_all_strategies_status(self) -> Dict[str, Any]:
        """
        Get status of all running strategies
        
        Returns:
            All strategies status with success/error information
        """
        results = {
            'success': True,
            'strategies': [],
            'count': len(self.active_strategies)
        }
        
        for key, strategy in self.active_strategies.items():
            try:
                status = strategy.get_status()
                results['strategies'].append({
                    'strategy_key': key,
                    'strategy_type': strategy.strategy_name,
                    'status': status
                })
            except Exception as e:
                logger.error(f"Error getting status for strategy {key}: {str(e)}")
                results['strategies'].append({
                    'strategy_key': key,
                    'strategy_type': strategy.strategy_name,
                    'error': str(e)
                })
        
        return results
    
    def create_strategy(self, name: str, strategy_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new strategy."""
        # Check if strategy type exists
        if strategy_type not in self.strategy_types:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        # Create the strategy
        strategy_class = self.strategy_types[strategy_type]
        strategy = strategy_class(**parameters)
        
        # Register the strategy
        self.strategies[name] = strategy
        
        return {"success": True, "strategy": name}
    
    def execute_strategy(self, name: str) -> Dict[str, Any]:
        """Execute a strategy."""
        # Check if strategy exists
        if name not in self.strategies:
            raise ValueError(f"Unknown strategy: {name}")
        
        # Get the strategy
        strategy = self.strategies[name]
        
        # Execute the strategy
        result = strategy.execute()
        
        return result
    
    def get_strategies(self) -> Dict[str, Any]:
        """Get all registered strategies."""
        return self.strategies
    
    def register_strategy(self, name: str, strategy: Any) -> None:
        """Register a strategy."""
        self.strategies[name] = strategy 