"""
Strategies package - Trading strategies for automated trading
"""

import logging
import importlib
from typing import Dict, Any, Type, Optional
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

# Strategy registry
STRATEGY_REGISTRY: Dict[str, Type[BaseStrategy]] = {}

def register_strategy(strategy_name: str, strategy_class: Type[BaseStrategy]) -> None:
    """
    Register a strategy class
    
    Args:
        strategy_name: Name of the strategy
        strategy_class: Strategy class
    """
    STRATEGY_REGISTRY[strategy_name] = strategy_class
    logger.debug(f"Registered strategy: {strategy_name}")

def get_strategy(strategy_name: str) -> Optional[Type[BaseStrategy]]:
    """
    Get a strategy class by name
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        The strategy class or None if not found
    """
    return STRATEGY_REGISTRY.get(strategy_name)

def create_strategy(strategy_name: str, **kwargs) -> Optional[BaseStrategy]:
    """
    Create a strategy instance
    
    Args:
        strategy_name: Name of the strategy
        **kwargs: Strategy configuration parameters
        
    Returns:
        The strategy instance or None if not found
    """
    strategy_class = get_strategy(strategy_name)
    if strategy_class:
        strategy = strategy_class()
        # Initialize with configuration if provided
        if kwargs:
            strategy.configure(**kwargs)
        return strategy
    else:
        logger.error(f"Strategy not found: {strategy_name}")
        return None

# Register built-in strategies
def _register_builtin_strategies() -> None:
    """Register all built-in strategies"""
    from .basic_strategy import BasicStrategy
    from .ladder_strategy import LadderStrategy
    from .oscillating_strategy import OscillatingStrategy
    from .highlow_strategy import HighLowStrategy
    from .oto_ladder_strategy import OTOLadderStrategy
    
    register_strategy("basic", BasicStrategy)
    register_strategy("ladder", LadderStrategy)
    register_strategy("oscillating", OscillatingStrategy)
    register_strategy("highlow", HighLowStrategy)
    register_strategy("oto_ladder", OTOLadderStrategy)
    
    logger.info("Built-in strategies registered")

# Initialize the registry
_register_builtin_strategies() 