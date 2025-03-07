# Strategy Implementation Guide

This document provides comprehensive guidance for implementing, testing, and deploying trading strategies within the Automated Trading System.

## Table of Contents

- [Strategy Overview](#strategy-overview)
- [Strategy Architecture](#strategy-architecture)
- [Built-in Strategies](#built-in-strategies)
  - [Ladder Strategy](#ladder-strategy)
  - [TWAP Strategy](#twap-strategy)
  - [VWAP Strategy](#vwap-strategy)
  - [Momentum Strategy](#momentum-strategy)
  - [OTO Ladder Strategy](#oto-ladder-strategy)
- [Creating Custom Strategies](#creating-custom-strategies)
  - [Strategy Base Class](#strategy-base-class)
  - [Implementing a Strategy](#implementing-a-strategy)
  - [Strategy Initialization](#strategy-initialization)
  - [Strategy Execution](#strategy-execution)
  - [Strategy Termination](#strategy-termination)
- [Strategy Parameters](#strategy-parameters)
- [Strategy Lifecycle](#strategy-lifecycle)
- [Market Data Integration](#market-data-integration)
- [Order Management](#order-management)
- [Risk Management](#risk-management)
- [Backtesting](#backtesting)
- [Performance Measurement](#performance-measurement)
- [Deployment](#deployment)
- [Example Implementation](#example-implementation)

## Strategy Overview

Strategies in the Automated Trading System are modular components that implement trading logic to achieve specific investment objectives. Each strategy follows a standardized interface, allowing for consistent implementation, testing, and deployment.

## Strategy Architecture

Strategies are implemented using a component-based architecture:

```
app/
└── strategies/
    ├── __init__.py
    ├── base.py            # Base strategy class
    ├── ladder.py          # Ladder strategy implementation
    ├── twap.py            # TWAP strategy implementation
    ├── vwap.py            # VWAP strategy implementation
    ├── momentum.py        # Momentum strategy implementation
    └── custom/            # Directory for custom strategies
```

Each strategy inherits from the base `Strategy` class and implements required methods.

## Built-in Strategies

### Ladder Strategy

The ladder strategy places a series of orders at predefined price levels:

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | The stock symbol |
| `side` | string | "buy" or "sell" |
| `steps` | integer | Number of orders to place |
| `start_price` | float | Starting price level |
| `end_price` | float | Ending price level |
| `total_quantity` | integer | Total shares to trade |
| `distribution` | string | "equal" or "weighted" distribution method |

#### Behavior

For a buy ladder:
- Orders are placed from highest to lowest price
- Each price level is calculated based on an even distribution between start and end prices
- Quantity per level is either equal or weighted based on distribution parameter

For a sell ladder:
- Orders are placed from lowest to highest price
- Each price level is calculated based on an even distribution between start and end prices
- Quantity per level is either equal or weighted based on distribution parameter

#### Return Value

The ladder strategy execution returns information about all orders placed:

```python
{
    "success": true,
    "message": "Ladder strategy executed successfully",
    "strategy_id": "ladder_123456",
    "orders": [
        {
            "order_id": "order_1",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 20,
            "price": 175.00,
            "status": "open"
        },
        {
            "order_id": "order_2",
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 20,
            "price": 173.75,
            "status": "open"
        },
        # Additional orders...
    ]
}
```

When accessing the ladder strategy through commands, all orders are directly returned in the response for easier tracking and management.

### TWAP Strategy

The Time-Weighted Average Price (TWAP) strategy breaks a large order into smaller chunks executed at regular time intervals:

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | The stock symbol |
| `side` | string | "buy" or "sell" |
| `total_quantity` | integer | Total shares to trade |
| `start_time` | datetime | Strategy start time |
| `end_time` | datetime | Strategy end time |
| `intervals` | integer | Number of execution intervals |
| `order_type` | string | "market" or "limit" |
| `limit_offset` | float | Offset for limit price (if using limit orders) |

#### Behavior

- Strategy divides total quantity into equal-sized child orders
- Child orders are executed at regular intervals between start and end times
- For limit orders, the price is set at current market price +/- limit_offset (based on side)

### VWAP Strategy

The Volume-Weighted Average Price (VWAP) strategy executes trades in proportion to historical volume profiles:

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | The stock symbol |
| `side` | string | "buy" or "sell" |
| `total_quantity` | integer | Total shares to trade |
| `start_time` | datetime | Strategy start time |
| `end_time` | datetime | Strategy end time |
| `intervals` | integer | Number of execution intervals |
| `historical_days` | integer | Number of days for volume profile calculation |
| `order_type` | string | "market" or "limit" |
| `limit_offset` | float | Offset for limit price (if using limit orders) |

#### Behavior

- Strategy loads historical volume profile for the specified symbol
- Child order sizes are proportional to expected volume during each interval
- Execution times are determined based on historical volume distribution

### HighLow Strategy

The HighLow strategy is a simple breakout trading strategy that buys when the price falls below a low threshold and sells when the price rises above a high threshold.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | The stock symbol |
| `quantity` | integer | Number of shares per trade |
| `low_threshold` | float | Price below which to buy |
| `high_threshold` | float | Price above which to sell |

#### Behavior

- The strategy tracks the last action taken (BUY or SELL)
- When price falls below the low threshold and the last action was not BUY, it places a buy order
- When price rises above the high threshold and the last action was not SELL, it places a sell order
- Orders are placed as market orders for immediate execution
- The strategy maintains a simple state machine to avoid repeatedly placing the same type of order

#### Implementation Notes

- The strategy handles different quote formats from both MarketDataService and TradingService
- For quotes from MarketDataService, it extracts the actual quote data from the nested structure
- For direct quotes from TradingService, it uses the quote data as is
- The "last" price field is used to determine the current price for decision making

### Oscillating Strategy

The Oscillating strategy is designed for range-bound markets, placing buy and sell orders as price oscillates between thresholds calculated from the current price.

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | The stock symbol |
| `quantity` | integer | Number of shares per trade |
| `price_range` | float | Price movement range for thresholds |
| `is_percentage` | boolean | Whether price_range is a percentage (true) or fixed amount (false) |
| `min_trade_interval` | integer | Minimum seconds between trades |
| `max_positions` | integer | Maximum number of concurrent positions |
| `use_normal_dist` | boolean | Whether to use normal distribution for randomizing thresholds |
| `std_dev` | float | Standard deviation for normal distribution (if enabled) |
| `session` | string | Trading session: "REGULAR" or "EXTENDED" |
| `duration` | string | Order duration: "DAY", "GTC", etc. |

#### Behavior

- Strategy calculates buy and sell thresholds based on the current price and price_range
- Thresholds can be fixed dollar amounts or percentages of the current price
- Optional normal distribution can add randomness to threshold calculations
- Strategy streams real-time price updates for the configured symbol
- When price crosses below buy threshold and position count is below max_positions, a buy order is placed
- When price crosses above sell threshold and positions exist, the oldest position is sold (FIFO)
- A minimum time interval between trades can be enforced to prevent excessive trading
- The strategy tracks all active positions and their purchase prices

#### Implementation Notes

- The strategy configuration is stored as a dictionary for flexibility
- Parameters are accessed using the get() method with default values for safety
- Price streaming is handled asynchronously through callbacks
- The strategy includes test mode for easier integration testing without requiring price streaming
- All trading is done through the TradingService to ensure proper order tracking

### Momentum Strategy

The Momentum strategy takes positions based on short-term price movements:

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | The stock symbol |
| `quantity` | integer | Shares per trade |
| `lookback_period` | integer | Lookback period for momentum calculation (minutes) |
| `threshold` | float | Momentum threshold to trigger trades |
| `stop_loss` | float | Stop loss percentage |
| `take_profit` | float | Take profit percentage |
| `max_trades` | integer | Maximum number of trades to execute |

#### Behavior

- Strategy calculates momentum by comparing current price to price from lookback_period minutes ago
- When momentum exceeds threshold, a position is taken in the direction of momentum
- Positions are closed when stop_loss or take_profit conditions are met
- Strategy stops executing after max_trades are completed

### OTO Ladder Strategy

The OTO Ladder (One-Triggers-Other) Step Strategy is designed to automate a step-based approach to scaling in and out of positions, with support for thinkorswim platform integration.

#### Strategy Overview

This strategy implements a step-based trading approach that:

1. Sells 5% of initial shares when price rises to pre-defined step levels
2. For each sell, creates a buy-back order at a price 2x the step value lower
3. For each buy-back, creates a take-profit order at the next step higher
4. Uses Extended Hours (EXTO) time-in-force for all orders
5. Generates ready-to-use OTO Ladder code that can be loaded into thinkorswim

The strategy is ideal for scaling out of positions on the way up while automatically positioning for buying back on dips.

#### Implementation

The OTO Ladder Strategy is implemented in `app/strategies/oto_ladder_strategy.py`. It extends the `BaseStrategy` class and provides:

1. OTO Ladder code generation for thinkorswim platform
2. Price step calculation based on current market conditions
3. OTO (One-Triggers-Other) order chain creation
4. Extended hours trading support via EXTO time-in-force
5. File export of OTO Ladder code for easy loading into thinkorswim

#### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | 'SPY' | Trading symbol |
| `start_price` | float | current_price | Price level where the strategy begins (if 0, uses current price) |
| `step` | float | 5.0 | Price increment that triggers sells |
| `initial_shares` | int | 100 | Initial number of shares in the position |
| `price_target` | float | None | Optional price level at which the strategy will terminate. When the current price equals or exceeds this value, the strategy will stop execution and return a success message |

#### Usage Example

```python
from app.strategies import create_strategy

# Create and configure the strategy
strategy = create_strategy("oto_ladder", 
                           symbol="AAPL", 
                           start_price=200.0, 
                           step=10.0, 
                           initial_shares=500,
                           price_target=250.0)  # Strategy will terminate when AAPL reaches $250

# Execute the strategy
result = strategy.execute()

# Check if price target was reached
if result.get('target_reached'):
    print(f"Price target reached: {result['message']}")
else:
    # Get the OTO Ladder code
    oto_ladder_code = result['oto_ladder_code']

    # Get the path to the saved OTO Ladder file
    file_path = result['oto_ladder_file']
```

#### Thinkorswim Integration

The strategy generates OTO Ladder code that can be directly loaded into thinkorswim. This code creates:

1. Visual indicators for each step level
2. Arrow markers for entry and exit points
3. Alerts when new step levels are reached
4. Detailed instructions for creating OTO order chains
5. Debug information to track strategy execution

To use the OTO Ladder code in thinkorswim:
1. Copy the code from the strategy output or load the generated .ts file
2. In thinkorswim, go to Studies > Edit Studies > Create
3. Paste the code and click "Create"
4. Apply the custom study to your chart

#### OTO Order Chain Structure

The strategy creates an order chain with the following structure:
- **First Order**: Sell 5% of original shares at the current step level
- **Second Order**: Buy back the same number of shares at 2x step lower (activated after first order fills)
- **Third Order**: Sell the shares again at the next step higher (activated after second order fills)

All orders in the chain use EXTO time-in-force, ensuring they remain active during extended trading hours.

## Creating Custom Strategies

### Strategy Base Class

All strategies inherit from the base `Strategy` class:

```python
class Strategy:
    """Base class for all trading strategies."""
    
    def __init__(self, strategy_id, strategy_type, parameters):
        """Initialize the strategy with parameters."""
        self.strategy_id = strategy_id
        self.strategy_type = strategy_type
        self.parameters = parameters
        self.status = "initialized"
        self.orders = []
        self.start_time = None
        self.end_time = None
        self.trading_service = None
        self.market_data_service = None
        self.on_error_callback = None
        
    def initialize(self, trading_service, market_data_service, on_error_callback=None):
        """Initialize strategy with required services."""
        self.trading_service = trading_service
        self.market_data_service = market_data_service
        self.on_error_callback = on_error_callback
        self.validate_parameters()
        return True
        
    def validate_parameters(self):
        """Validate strategy parameters."""
        raise NotImplementedError("Subclasses must implement validate_parameters")
        
    def start(self):
        """Start strategy execution."""
        if self.status != "initialized":
            raise ValueError(f"Cannot start strategy in {self.status} state")
        self.status = "running"
        self.start_time = datetime.now()
        return self.execute()
        
    def execute(self):
        """Execute the strategy logic."""
        raise NotImplementedError("Subclasses must implement execute")
        
    def stop(self):
        """Stop strategy execution."""
        if self.status not in ["running", "paused"]:
            raise ValueError(f"Cannot stop strategy in {self.status} state")
        self.status = "stopped"
        self.end_time = datetime.now()
        return True
        
    def pause(self):
        """Pause strategy execution."""
        if self.status != "running":
            raise ValueError(f"Cannot pause strategy in {self.status} state")
        self.status = "paused"
        return True
        
    def resume(self):
        """Resume strategy execution."""
        if self.status != "paused":
            raise ValueError(f"Cannot resume strategy in {self.status} state")
        self.status = "running"
        return self.execute()
        
    def get_status(self):
        """Get strategy status and information."""
        return {
            "strategy_id": self.strategy_id,
            "strategy_type": self.strategy_type,
            "status": self.status,
            "parameters": self.parameters,
            "orders": self.orders,
            "start_time": self.start_time,
            "end_time": self.end_time
        }
        
    def handle_error(self, error_message, error_details=None):
        """Handle strategy error."""
        self.status = "error"
        error_info = {
            "message": error_message,
            "details": error_details,
            "timestamp": datetime.now()
        }
        if self.on_error_callback:
            self.on_error_callback(self.strategy_id, error_info)
        return error_info
```

### Implementing a Strategy

To create a custom strategy:

1. Create a new Python file in the `app/strategies/custom` directory
2. Implement a class that inherits from `Strategy`
3. Implement the required methods:
   - `validate_parameters`
   - `execute`
4. Optionally override other methods as needed

### Strategy Initialization

Strategy initialization consists of:

1. Parameter validation
2. Service dependency injection
3. State initialization

Example implementation:

```python
def validate_parameters(self):
    """Validate strategy parameters."""
    required_params = ["symbol", "quantity", "side"]
    for param in required_params:
        if param not in self.parameters:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Validate symbol
    symbol = self.parameters["symbol"]
    try:
        quote = self.market_data_service.get_quote(symbol)
        if not quote:
            raise ValueError(f"Invalid symbol: {symbol}")
    except Exception as e:
        raise ValueError(f"Error validating symbol: {str(e)}")
    
    # Validate quantity
    quantity = self.parameters["quantity"]
    if not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("Quantity must be a positive integer")
    
    # Validate side
    side = self.parameters["side"]
    if side not in ["buy", "sell"]:
        raise ValueError("Side must be 'buy' or 'sell'")
    
    return True
```

### Strategy Execution

Strategy execution is the core logic that implements the trading algorithm:

1. Analyze market data
2. Make trading decisions
3. Place orders
4. Monitor results
5. Adjust as needed

Example implementation:

```python
def execute(self):
    """Execute the strategy logic."""
    try:
        symbol = self.parameters["symbol"]
        quantity = self.parameters["quantity"]
        side = self.parameters["side"]
        
        # Get current market data
        quote = self.market_data_service.get_quote(symbol)
        current_price = quote["last_price"]
        
        # Make trading decision
        if self._should_execute(current_price):
            # Place order
            order_result = self.trading_service.place_market_order(
                symbol=symbol,
                quantity=quantity,
                side=side
            )
            
            # Record order
            self.orders.append({
                "order_id": order_result["order_id"],
                "symbol": symbol,
                "quantity": quantity,
                "side": side,
                "price": current_price,
                "timestamp": datetime.now()
            })
            
            return True
        else:
            # No execution needed
            return False
            
    except Exception as e:
        return self.handle_error(f"Execution error: {str(e)}")
        
def _should_execute(self, current_price):
    """Determine if strategy should execute based on current price."""
    # Custom decision logic here
    return True
```

### Strategy Termination

Strategy termination handles:

1. Canceling outstanding orders
2. Closing positions if needed
3. Releasing resources
4. Updating status

## Strategy Parameters

Each strategy has its own set of parameters that control its behavior. Parameters should be:

1. Well-documented
2. Validated during initialization
3. Accessible through the strategy interface

Common parameter types include:

- **Symbol parameters**: Stock symbols, asset identifiers
- **Quantity parameters**: Number of shares, position sizes
- **Price parameters**: Target prices, limit prices, reference prices
- **Time parameters**: Start times, end times, intervals
- **Threshold parameters**: Trigger levels, stop-loss points
- **Behavioral parameters**: Order types, execution styles

## Strategy Lifecycle

Strategies follow a defined lifecycle:

1. **Initialization**: Strategy is created with parameters
2. **Validation**: Parameters are validated
3. **Start**: Strategy begins execution
4. **Execution**: Strategy executes its core logic
5. **Monitoring**: Strategy monitors execution and market conditions
6. **Adjustment**: Strategy adjusts based on market conditions
7. **Termination**: Strategy completes execution

## Market Data Integration

Strategies access market data through the `market_data_service`:

```python
# Get current quote
quote = self.market_data_service.get_quote(symbol)

# Get historical data
historical_data = self.market_data_service.get_historical_data(
    symbol=symbol,
    interval="1min",
    start_time=datetime.now() - timedelta(days=1),
    end_time=datetime.now()
)

# Subscribe to real-time updates
self.market_data_service.subscribe_quotes(
    symbols=[symbol],
    callback=self._on_quote_update
)

def _on_quote_update(self, quote):
    """Handle real-time quote updates."""
    # Process quote update
    pass
```

## Order Management

Strategies place and manage orders through the `trading_service`:

```python
# Place market order
market_order = self.trading_service.place_market_order(
    symbol=symbol,
    quantity=quantity,
    side=side
)

# Place limit order
limit_order = self.trading_service.place_limit_order(
    symbol=symbol,
    quantity=quantity,
    side=side,
    price=limit_price
)

# Cancel order
cancel_result = self.trading_service.cancel_order(order_id)

# Get order status
order_status = self.trading_service.get_order_status(order_id)

# Get open orders
open_orders = self.trading_service.get_open_orders(symbol)
```

## Risk Management

Strategies should implement risk management controls:

1. **Position size limits**: Maximum position size
2. **Loss limits**: Maximum allowable loss
3. **Order frequency controls**: Rate limiting for order placement
4. **Exposure limits**: Maximum market exposure
5. **Correlation limits**: Exposure across correlated assets

Example implementation:

```python
def check_risk_limits(self):
    """Check if strategy is within risk limits."""
    # Check position size
    position = self.trading_service.get_position(self.parameters["symbol"])
    if position and position["quantity"] >= self.parameters["max_position"]:
        return False
    
    # Check drawdown
    if self._calculate_drawdown() >= self.parameters["max_drawdown"]:
        return False
    
    # Check order frequency
    recent_orders = [o for o in self.orders 
                     if (datetime.now() - o["timestamp"]).seconds < 60]
    if len(recent_orders) >= self.parameters["max_orders_per_minute"]:
        return False
    
    return True
```

## Backtesting

Strategies can be tested using historical data before live deployment:

```python
from app.backtesting import backtest_strategy

# Run backtest
results = backtest_strategy(
    strategy_type="custom_strategy",
    parameters={
        "symbol": "AAPL",
        "quantity": 100,
        "side": "buy",
        # Other parameters...
    },
    start_date="2023-01-01",
    end_date="2023-03-31",
    initial_capital=10000
)

# Analyze results
print(f"Total Return: {results['total_return']}%")
print(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']}")
print(f"Max Drawdown: {results['metrics']['max_drawdown']}%")
```

## Performance Measurement

Strategy performance is measured using key metrics:

1. **Total return**: Overall profit/loss
2. **Win rate**: Percentage of profitable trades
3. **Average win/loss**: Average profit/loss per trade
4. **Sharpe ratio**: Risk-adjusted return
5. **Maximum drawdown**: Largest decline from peak
6. **Volatility**: Standard deviation of returns

## Deployment

To deploy a custom strategy:

1. Register the strategy with the strategy service:

```python
from app.strategies.custom.my_strategy import MyStrategy
from app.services import get_service

# Get strategy service
strategy_service = get_service("strategy")

# Register custom strategy
strategy_service.register_strategy_class("my_strategy", MyStrategy)

# Start strategy instance
strategy_id = strategy_service.start_strategy(
    strategy_type="my_strategy",
    parameters={
        "symbol": "AAPL",
        "quantity": 100,
        "side": "buy",
        # Other parameters...
    }
)
```

2. Monitor strategy execution:

```python
# Get strategy status
status = strategy_service.get_strategy_status(strategy_id)
print(f"Strategy status: {status['status']}")

# Get strategy orders
orders = strategy_service.get_strategy_orders(strategy_id)
for order in orders:
    print(f"Order {order['order_id']}: {order['status']}")
```

3. Stop strategy when needed:

```python
# Stop strategy
strategy_service.stop_strategy(strategy_id)
```

## Example Implementation

Here's a complete example of a simple moving average crossover strategy:

```python
class MovingAverageCrossover(Strategy):
    """Moving average crossover strategy."""
    
    def validate_parameters(self):
        """Validate strategy parameters."""
        required_params = ["symbol", "quantity", "short_period", "long_period"]
        for param in required_params:
            if param not in self.parameters:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Validate symbol
        symbol = self.parameters["symbol"]
        try:
            quote = self.market_data_service.get_quote(symbol)
            if not quote:
                raise ValueError(f"Invalid symbol: {symbol}")
        except Exception as e:
            raise ValueError(f"Error validating symbol: {str(e)}")
        
        # Validate quantity
        quantity = self.parameters["quantity"]
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")
        
        # Validate periods
        short_period = self.parameters["short_period"]
        long_period = self.parameters["long_period"]
        if not isinstance(short_period, int) or short_period <= 0:
            raise ValueError("Short period must be a positive integer")
        if not isinstance(long_period, int) or long_period <= 0:
            raise ValueError("Long period must be a positive integer")
        if short_period >= long_period:
            raise ValueError("Short period must be less than long period")
        
        return True
    
    def execute(self):
        """Execute the strategy logic."""
        try:
            symbol = self.parameters["symbol"]
            quantity = self.parameters["quantity"]
            short_period = self.parameters["short_period"]
            long_period = self.parameters["long_period"]
            
            # Get historical data
            historical_data = self.market_data_service.get_historical_data(
                symbol=symbol,
                interval="1day",
                start_time=datetime.now() - timedelta(days=long_period*2),
                end_time=datetime.now()
            )
            
            # Calculate moving averages
            prices = [bar["close"] for bar in historical_data]
            short_ma = sum(prices[-short_period:]) / short_period
            long_ma = sum(prices[-long_period:]) / long_period
            
            # Check for crossover
            prev_prices = prices[:-1]
            prev_short_ma = sum(prev_prices[-short_period:]) / short_period
            prev_long_ma = sum(prev_prices[-long_period:]) / long_period
            
            # Detect crossover
            current_position = self._get_current_position(symbol)
            
            if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                # Bullish crossover
                if current_position <= 0:
                    # Place buy order
                    order_result = self.trading_service.place_market_order(
                        symbol=symbol,
                        quantity=quantity,
                        side="buy"
                    )
                    self.orders.append({
                        "order_id": order_result["order_id"],
                        "symbol": symbol,
                        "quantity": quantity,
                        "side": "buy",
                        "reason": "bullish_crossover",
                        "timestamp": datetime.now()
                    })
            elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                # Bearish crossover
                if current_position >= 0:
                    # Place sell order
                    order_result = self.trading_service.place_market_order(
                        symbol=symbol,
                        quantity=abs(current_position) if current_position > 0 else quantity,
                        side="sell"
                    )
                    self.orders.append({
                        "order_id": order_result["order_id"],
                        "symbol": symbol,
                        "quantity": abs(current_position) if current_position > 0 else quantity,
                        "side": "sell",
                        "reason": "bearish_crossover",
                        "timestamp": datetime.now()
                    })
            
            return True
            
        except Exception as e:
            return self.handle_error(f"Execution error: {str(e)}")
    
    def _get_current_position(self, symbol):
        """Get current position for symbol."""
        try:
            position = self.trading_service.get_position(symbol)
            if position:
                return position["quantity"]
            return 0
        except Exception:
            return 0
```

To use this strategy:

```python
from app.services import get_service

# Get strategy service
strategy_service = get_service("strategy")

# Start moving average crossover strategy
strategy_id = strategy_service.start_strategy(
    strategy_type="moving_average_crossover",
    parameters={
        "symbol": "AAPL",
        "quantity": 100,
        "short_period": 10,
        "long_period": 30
    }
)

# Monitor strategy status
status = strategy_service.get_strategy_status(strategy_id)
print(f"Strategy status: {status['status']}") 