# Code Documentation Style Guide

This document outlines the standard documentation practices for the Automated Trading System codebase. Following these guidelines ensures consistency, readability, and maintainability across the project.

## Table of Contents

- [General Principles](#general-principles)
- [Python Docstring Format](#python-docstring-format)
- [Module Documentation](#module-documentation)
- [Class Documentation](#class-documentation)
- [Method and Function Documentation](#method-and-function-documentation)
- [Test Documentation](#test-documentation)
- [Variable and Attribute Documentation](#variable-and-attribute-documentation)
- [Code Comments](#code-comments)
- [Example Documentation](#example-documentation)
- [Documentation Validation](#documentation-validation)

## General Principles

1. **Clarity**: Documentation should be clear and understandable to developers not familiar with the code.
2. **Completeness**: All public modules, classes, methods, and functions must be documented.
3. **Relevance**: Focus on information that helps other developers understand and use the code.
4. **Consistency**: Maintain consistent formatting and style throughout the codebase.
5. **Updates**: Always update documentation when code changes.

## Python Docstring Format

We use Google-style docstrings for all Python code. This format is well-supported by tools like Sphinx and provides a good balance of readability and structure.

### Basic Format

```python
def function_name(param1, param2):
    """A brief description of the function.
    
    A more detailed description that explains what the function does,
    its purpose, and any high-level concepts.
    
    Args:
        param1 (type): Description of param1.
        param2 (type): Description of param2.
        
    Returns:
        type: Description of return value.
        
    Raises:
        ExceptionType: When and why this exception is raised.
        
    Examples:
        >>> function_name('foo', 123)
        'foo123'
    """
    # Function implementation
```

## Module Documentation

Each module (Python file) should begin with a docstring that explains the purpose and contents of the module.

```python
"""
Trading strategy implementations for the Automated Trading System.

This module contains various trading strategy implementations,
including ladder, TWAP, VWAP, and momentum strategies.
Each strategy inherits from the base Strategy class and implements
the required methods for strategy execution.
"""

# Imports
# ...
```

## Class Documentation

Class docstrings should describe the purpose of the class, its behavior, and important attributes.

```python
class StrategyService:
    """Service for managing trading strategies.
    
    The StrategyService handles the lifecycle of trading strategies,
    including creation, execution, monitoring, and termination.
    It serves as the central coordination point for all strategy-related
    operations in the system.
    
    Attributes:
        strategies (dict): Dictionary of active strategies.
        market_data_service (MarketDataService): Service for market data.
        trading_service (TradingService): Service for executing trades.
    """
    # Class implementation
```

## Method and Function Documentation

Methods and functions should have docstrings that describe:

1. What the function does
2. Parameters and their types
3. Return value and type
4. Exceptions that may be raised
5. Examples of usage (when helpful)

```python
def place_market_order(self, symbol, quantity, side):
    """Place a market order for the specified symbol.
    
    Places a market order to buy or sell the specified quantity
    of the given symbol at the current market price.
    
    Args:
        symbol (str): The stock symbol (e.g., 'AAPL').
        quantity (int): Number of shares to buy or sell.
        side (str): 'buy' or 'sell'.
        
    Returns:
        dict: Order information including:
            - order_id (str): Unique identifier for the order.
            - status (str): Current status of the order.
            - filled_quantity (int): Number of shares filled.
            - average_price (float): Average fill price.
            
    Raises:
        ValueError: If symbol, quantity, or side is invalid.
        APIError: If the API request fails.
        
    Examples:
        >>> trading_service.place_market_order('AAPL', 100, 'buy')
        {
            'order_id': '12345',
            'status': 'filled',
            'filled_quantity': 100,
            'average_price': 150.25
        }
    """
    # Method implementation
```

## Test Documentation

Test files require special documentation to clarify their purpose, scope, and covered functionality.

### Test Module Documentation

Each test module should have a top-level docstring that explains:
1. What component(s) it tests
2. The testing approach
3. Any special setup requirements

Example:

```python
"""
Unit tests for the TradingService class.

These tests verify that the TradingService correctly handles order placement,
cancellation, and retrieval, with a focus on mock trading functionality.
"""
```

### Test Class Documentation

Test classes should document what specific functionality they test:

```python
class TestTradingService:
    """
    Test suite for the TradingService functionality.
    
    These tests verify that the trading service correctly:
    - Places market and limit orders
    - Cancels existing orders
    - Retrieves order status
    - Handles error conditions
    """
```

### Test Method Documentation

Test methods should explain:
1. What specific functionality is being tested
2. The test's verification steps
3. Expected outcomes

```python
def test_place_market_order(self):
    """
    Test placing a market order successfully.
    
    Verifies that:
    1. The order is processed correctly
    2. The API client is called with the right parameters
    3. The response contains the expected data
    """
```

### Test Runner Function Documentation

Functions that run tests should document:
1. What tests they run and in what order
2. Environment setup and teardown
3. Return values and their meaning

```python
def run_tests():
    """
    Run all trading service tests in sequence.
    
    This function:
    1. Creates a TestTradingService instance
    2. Sets up the test environment
    3. Runs each test method in sequence
    4. Reports success or failure
    
    Returns:
        bool: True if all tests pass, False if any test fails
    """
```

### Setup and Teardown Method Documentation

Document the purpose of setup and teardown methods:

```python
def setup_method(self):
    """
    Set up test environment before each test method runs.
    
    This method:
    1. Creates mock dependencies
    2. Initializes service under test
    3. Configures test data
    """
```

## Variable and Attribute Documentation

For important module-level variables or class attributes, include type information and description:

```python
# Maximum number of concurrent strategies allowed
MAX_STRATEGIES = 10  # type: int

class Strategy:
    # ... 
    
    #: List of orders placed by this strategy
    orders = []  # type: List[Dict[str, Any]]
```

## Code Comments

Use comments to explain why certain code exists, not what it does (the code itself should be clear enough to understand what it does).

Good comment:
```python
# Retry the API call up to 3 times to handle intermittent network issues
for attempt in range(3):
    try:
        return api_client.execute_request(request)
    except NetworkError:
        if attempt == 2:  # Last attempt
            raise
        time.sleep(1)
```

Avoid unnecessary comments:
```python
# Increment counter  # Unnecessary - code is self-explanatory
counter += 1
```

## Example Documentation

### Module Example

```python
"""
Market data service implementation for the Automated Trading System.

This module provides services for retrieving and processing market data
from various sources, including real-time quotes, historical data,
and order book information.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from app.api.market_data_client import MarketDataClient
from app.models.market_data import Quote, Bar, OrderBook
from app.config import get_config

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for retrieving and processing market data.
    
    Provides methods for getting quotes, historical data, and subscribing
    to real-time updates for various market data types.
    """
    
    def __init__(self, client=None):
        """Initialize the market data service.
        
        Args:
            client (MarketDataClient, optional): Client for API requests.
                If None, a new client will be created.
        """
        self.client = client or MarketDataClient()
        self.config = get_config()
        self.subscriptions = {}
        
    # Rest of the class...
```

### Function Example

```python
def analyze_volume_profile(self, symbol: str, period: str = '1d', 
                           bars: int = 100) -> Dict[str, Any]:
    """Analyze trading volume profile for a symbol.
    
    Retrieves historical volume data and calculates volume distribution
    across different price levels and time periods.
    
    Args:
        symbol (str): The stock symbol to analyze.
        period (str, optional): Time period for each bar. 
            Options: '1m', '5m', '15m', '1h', '1d'.
            Defaults to '1d'.
        bars (int, optional): Number of bars to retrieve.
            Defaults to 100.
            
    Returns:
        Dict[str, Any]: Volume analysis including:
            - volume_by_price (Dict[float, int]): Volume at each price level.
            - time_distribution (List[Dict]): Volume distribution by time.
            - avg_volume (float): Average volume over the period.
            - volume_trend (List[float]): Trend in volume changes.
            
    Raises:
        ValueError: If the symbol or parameters are invalid.
        APIError: If the data request fails.
        
    Examples:
        >>> market_data.analyze_volume_profile('AAPL', period='1h', bars=24)
        {
            'volume_by_price': {150.0: 10000, 150.5: 15000, ...},
            'time_distribution': [...],
            'avg_volume': 12500,
            'volume_trend': [1.02, 0.98, 1.05, ...]
        }
    """
    # Implementation...
```

## Documentation Validation

We use several tools to validate our documentation:

1. **Pylint**: Configured to check for missing docstrings.
2. **pydocstyle**: Verifies docstring format compliance.
3. **Sphinx**: Used to generate HTML documentation from docstrings.

Run these validation tools regularly:

```bash
# Check docstring style
pydocstyle app/

# Generate documentation
cd docs && make html
```

Remember that good documentation is part of the definition of "done" for any code changes. Code reviews should always include a review of documentation changes. 