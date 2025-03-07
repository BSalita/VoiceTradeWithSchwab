# API Documentation

This document provides comprehensive documentation for both the Schwab API client integration and the application's REST API endpoints.

## Table of Contents

- [Schwab API Client](#schwab-api-client)
  - [Authentication](#authentication)
  - [Market Data Methods](#market-data-methods)
  - [Trading Methods](#trading-methods)
  - [Account Methods](#account-methods)
  - [Error Handling](#error-handling)
- [REST API Endpoints](#rest-api-endpoints)
  - [Authentication](#api-authentication)
  - [Health Check Endpoint](#health-check-endpoint)
  - [Trading Endpoints](#trading-endpoints)
  - [Market Data Endpoints](#market-data-endpoints)
  - [Strategy Endpoints](#strategy-endpoints)
  - [Account Endpoints](#account-endpoints)
  - [Error Responses](#error-responses)
- [WebSocket API](#websocket-api)
- [API Endpoints](#api-endpoints)
  - [Health](#health)
  - [Account](#account)
  - [Orders](#orders)
  - [Quotes](#quotes)
  - [Strategies](#strategies)
  - [History](#history)
  - [Backtesting](#backtesting)

## Schwab API Client

The `SchwabAPIClient` class provides a standardized interface for interacting with the Schwab API.

### Authentication

Authentication is handled automatically when the client is instantiated. API credentials are sourced from environment variables or passed directly to the constructor.

```python
from app.api.schwab_client import SchwabAPIClient

# Using environment variables (SCHWAB_API_KEY, SCHWAB_API_SECRET)
client = SchwabAPIClient()

# Directly providing credentials
client = SchwabAPIClient(api_key="your_key", api_secret="your_secret")
```

#### Required Environment Variables

- `SCHWAB_API_KEY`: Your Schwab API key
- `SCHWAB_API_SECRET`: Your Schwab API secret
- `SCHWAB_ACCOUNT_ID`: Your Schwab account ID (optional for some operations)

### Market Data Methods

#### Get Quote

Retrieves current market data for a specific symbol.

```python
quote = client.get_quote("AAPL")
```

**Parameters:**
- `symbol` (str): The stock symbol to query

**Returns:**
- Dictionary containing quote information:
  - `symbol`: Symbol requested
  - `bid_price`: Current bid price
  - `ask_price`: Current ask price
  - `last_price`: Last traded price
  - `volume`: Trading volume
  - `timestamp`: Quote timestamp
  - Additional fields may be available

**Error Handling:**
- Raises `SchwabAPIError` if the request fails
- Returns error information in the response for invalid symbols

#### Get Quotes (Multiple Symbols)

Retrieves quotes for multiple symbols in a single request.

```python
quotes = client.get_quotes(["AAPL", "MSFT", "GOOG"])
```

**Parameters:**
- `symbols` (list): List of stock symbols to query

**Returns:**
- Dictionary mapping symbols to their quote data

### Trading Methods

#### Place Order

Places a new order.

```python
order = client.place_order(
    symbol="AAPL",
    quantity=10,
    side="buy",
    order_type="market",
    price=None,  # Not used for market orders
    duration="day",
    session="regular"
)
```

**Parameters:**
- `symbol` (str): Stock symbol. Must be a valid symbol. The system will validate symbols and reject those containing "INVALID" in their name or that don't match the required format.
- `quantity` (int): Number of shares
- `side` (str): "buy" or "sell"
- `order_type` (str): "market" or "limit"
- `price` (float, optional): Limit price (required for limit orders)
- `duration` (str): "day" or "gtc" (good till canceled)
- `session` (str): "regular" or "extended"

**Returns:**
- Dictionary containing order information:
  - `order_id`: Unique order identifier
  - `status`: Current order status
  - `symbol`: Stock symbol
  - `quantity`: Order quantity
  - `side`: Buy or sell
  - `order_type`: Market or limit
  - `price`: Limit price (if applicable)
  - Additional fields may be available

#### Cancel Order

Cancels an existing order.

```python
result = client.cancel_order("order_123456")
```

**Parameters:**
- `order_id` (str): The order ID to cancel

**Returns:**
- Dictionary indicating success or failure

#### Get Orders

Retrieves a list of orders.

```python
orders = client.get_orders(status="open")
```

**Parameters:**
- `status` (str, optional): Filter by order status ("open", "filled", "canceled", "all")
- `from_date` (str, optional): Start date in "YYYY-MM-DD" format
- `to_date` (str, optional): End date in "YYYY-MM-DD" format

**Returns:**
- List of order dictionaries

### Account Methods

#### Get Account Information

Retrieves account details.

```python
account_info = client.get_account_info()
```

**Returns:**
- Dictionary containing account information:
  - `account_id`: Account identifier
  - `account_type`: Account type
  - `balance`: Cash balance
  - `buying_power`: Available buying power
  - Additional fields may be available

#### Get Positions

Retrieves current positions in the account.

```python
positions = client.get_positions()
```

**Returns:**
- List of position dictionaries, each containing:
  - `symbol`: Stock symbol
  - `quantity`: Number of shares
  - `average_price`: Average purchase price
  - `current_price`: Current market price
  - `market_value`: Current market value
  - Additional fields may be available

### Error Handling

The client uses a standardized error format:

```python
try:
    result = client.place_order(...)
except SchwabAPIError as e:
    print(f"API Error: {e.message}, Code: {e.code}")
```

Error codes and their meanings:

| Code | Description |
|------|-------------|
| 400  | Bad request, check parameters |
| 401  | Authentication error |
| 403  | Insufficient permissions |
| 404  | Resource not found |
| 429  | Rate limit exceeded |
| 500  | Server error |

## REST API Endpoints

The application provides a RESTful API for trading operations.

> **Note on Response Format**: All API responses include a `success` field with a boolean value (`true` or `false`). While the Python code uses Python boolean values (`True`/`False`), the actual JSON responses sent to clients will contain lowercase `true` or `false` as per JSON standard. All documentation examples use the JSON format that clients will receive.

### API Authentication

API endpoints require authentication using an API key passed in the header:

```
Authorization: Bearer YOUR_API_KEY
```

### Health Check Endpoint

#### GET /health

Checks the health status of the API.

**Response:**
```json
{
  "status": "ok"
}
```

### Trading Endpoints

#### GET /api/orders

Retrieves a list of orders.

**Parameters:**
- `status` (query, optional): Filter by order status ("open", "filled", "canceled", "all")

**Response:**
```json
{
  "success": true,
  "orders": [
    {
      "order_id": "order_123456",
      "symbol": "AAPL",
      "quantity": 10,
      "side": "buy",
      "order_type": "market",
      "status": "filled",
      "created_at": "2023-06-15T10:30:00Z",
      "filled_at": "2023-06-15T10:30:05Z",
      "filled_price": 150.25
    },
    ...
  ]
}
```

#### POST /api/orders

Places a new order.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "quantity": 10,
  "side": "buy",
  "order_type": "market",
  "price": null,
  "duration": "DAY",
  "session": "REGULAR",
  "strategy": null
}
```

**Response:**
```json
{
  "success": true,
  "order": {
    "order_id": "order_789012",
    "symbol": "AAPL",
    "quantity": 10,
    "side": "buy",
    "order_type": "market",
    "status": "pending",
    "created_at": "2023-06-15T14:45:00Z"
  }
}
```

#### DELETE /api/orders/{order_id}

Cancels a specific order.

**Parameters:**
- `order_id` (path): The order ID to cancel

**Response:**
```json
{
  "success": true,
  "message": "Order canceled successfully"
}
```

### Market Data Endpoints

#### GET /api/quotes/{symbol}

Gets a quote for a specific symbol.

**Parameters:**
- `symbol` (path): The stock symbol to query

**Response:**
```json
{
  "success": true,
  "quote": {
    "symbol": "AAPL",
    "bid_price": 150.10,
    "ask_price": 150.15,
    "last_price": 150.12,
    "volume": 12345678,
    "timestamp": "2023-06-15T14:30:00Z"
  }
}
```

### Strategy Endpoints

#### POST /api/strategies

Creates and starts a new trading strategy.

**Request Body:**
```json
{
  "name": "my_ladder_strategy",
  "type": "ladder",
  "parameters": {
    "symbol": "AAPL",
    "side": "buy",
    "total_quantity": 100,
    "steps": 5,
    "start_price": 145.00,
    "end_price": 150.00
  }
}
```

**Response:**
```json
{
  "success": true,
  "strategy": "my_ladder_strategy"
}
```

#### POST /api/strategies/{name}/execute

Executes a specific strategy by name.

**Parameters:**
- `name` (path): The strategy name to execute

**Response:**
```json
{
  "success": true,
  "result": {
    // Strategy execution details
  }
}
```

### Account Endpoints

#### GET /api/account

Retrieves account information.

**Response:**
```json
{
  "success": true,
  "account": {
    "account_id": "account_123456",
    "account_type": "margin",
    "balance": 10000.00,
    "buying_power": 20000.00,
    "created_at": "2022-01-01T00:00:00Z"
  }
}
```

#### GET /api/account/positions

Retrieves current positions.

**Response:**
```json
{
  "success": true,
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "average_price": 150.25,
      "current_price": 155.50,
      "market_value": 15550.00,
      "profit_loss": 525.00,
      "profit_loss_percent": 3.49
    },
    ...
  ]
}
```

### Error Responses

All endpoints use a standardized error response format:

```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Invalid parameter: quantity must be a positive integer"
  }
}
```

Common error codes:

| Code | Description |
|------|-------------|
| 400  | Bad request, check parameters |
| 401  | Authentication error |
| 403  | Insufficient permissions |
| 404  | Resource not found |
| 429  | Rate limit exceeded |
| 500  | Server error |

## WebSocket API

The application also provides a WebSocket API for real-time data.

### Connection

Connect to the WebSocket endpoint:

```
ws://your-api-domain/ws
```

Authentication is required via a query parameter:

```
ws://your-api-domain/ws?token=YOUR_API_TOKEN
```

### Quote Streaming

Subscribe to real-time quotes:

```json
{
  "action": "subscribe",
  "channel": "quotes",
  "symbols": ["AAPL", "MSFT", "GOOG"]
}
```

Quote updates are delivered as:

```json
{
  "channel": "quotes",
  "symbol": "AAPL",
  "data": {
    "bid_price": 150.10,
    "ask_price": 150.15,
    "last_price": 150.12,
    "volume": 12345678,
    "timestamp": "2023-06-15T14:30:00.123Z"
  }
}
```

### Order Updates

Subscribe to order status updates:

```json
{
  "action": "subscribe",
  "channel": "orders"
}
```

Order updates are delivered as:

```json
{
  "channel": "orders",
  "order_id": "order_123456",
  "data": {
    "status": "filled",
    "filled_at": "2023-06-15T14:30:05Z",
    "filled_price": 150.25,
    "filled_quantity": 10
  }
}
```

## API Endpoints

- [Health](#health)
- [Account](#account)
- [Orders](#orders)
- [Quotes](#quotes)
- [Strategies](#strategies)
- [History](#history)
- [Backtesting](#backtesting)

## Backtesting

### Run a Backtest

```
POST /api/backtest
```

Run a backtest for a trading strategy.

#### Request Body

```json
{
  "strategy_name": "ladder",
  "symbol": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2023-06-30",
  "initial_capital": 10000.0,
  "trading_session": "REGULAR",
  "strategy_params": {
    "steps": 5,
    "start_price": 150.0,
    "end_price": 160.0
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `strategy_name` | string | Name of the strategy to backtest |
| `symbol` | string | Stock symbol to backtest |
| `start_date` | string | Start date in YYYY-MM-DD format |
| `end_date` | string | End date in YYYY-MM-DD format |
| `initial_capital` | number | Initial capital for the backtest (default: 10000.0) |
| `trading_session` | string | Trading session: "REGULAR" or "EXTENDED" |
| `strategy_params` | object | Additional parameters for the strategy |

#### Response

```json
{
  "success": true,
  "message": "Backtest for ladder on AAPL completed successfully",
  "backtest_id": "ladder_AAPL_20230101_20230630_20230707123456",
  "summary": {
    "backtest_id": "ladder_AAPL_20230101_20230630_20230707123456",
    "strategy_name": "ladder",
    "symbol": "AAPL",
    "period": "2023-01-01 to 2023-06-30",
    "initial_capital": 10000.0,
    "final_capital": 12000.0,
    "total_return": "20.00%",
    "max_drawdown": "5.00%",
    "sharpe_ratio": "1.50",
    "win_rate": "60.00%",
    "total_trades": 10
  },
  "metrics": {
    "total_trades": 10,
    "winning_trades": 6,
    "losing_trades": 4,
    "win_rate": "60.00%",
    "average_win": "$500.00",
    "average_loss": "$300.00",
    "profit_factor": "2.00",
    "average_trade": "$150.00"
  },
  "trades": [
    {
      "id": "backtest_order_0",
      "symbol": "AAPL",
      "side": "BUY",
      "quantity": 10,
      "price": 150.0,
      "value": 1500.0,
      "timestamp": "2023-01-02T10:00:00Z"
    },
    {
      "id": "backtest_order_1",
      "symbol": "AAPL",
      "side": "SELL",
      "quantity": 10,
      "price": 160.0,
      "value": 1600.0,
      "timestamp": "2023-01-05T14:30:00Z"
    }
  ],
  "equity_curve": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "portfolio_value": 10000.0,
      "cash": 10000.0,
      "position_value": 0.0,
      "close_price": 150.0
    },
    {
      "timestamp": "2023-01-02T00:00:00Z",
      "portfolio_value": 10000.0,
      "cash": 8500.0,
      "position_value": 1500.0,
      "close_price": 150.0
    },
    {
      "timestamp": "2023-01-05T00:00:00Z",
      "portfolio_value": 10100.0,
      "cash": 10100.0,
      "position_value": 0.0,
      "close_price": 160.0
    }
  ]
}
```

### Compare Strategies

```
POST /api/backtest/compare
```

Compare multiple strategies over the same time period.

#### Request Body

```json
{
  "strategies": ["ladder", "oto_ladder", "oscillating"],
  "symbol": "MSFT",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 10000.0,
  "trading_session": "REGULAR",
  "strategy_params": {
    "ladder": {
      "steps": 5,
      "start_price": 250.0,
      "end_price": 260.0
    },
    "oto_ladder": {
      "start_price": 250.0,
      "step": 5.0,
      "initial_shares": 100,
      "price_target": 280.0
    },
    "oscillating": {
      "symbol": "MSFT",
      "quantity": 10,
      "price_range": 0.02,
      "is_percentage": true,
      "min_trade_interval": 60,
      "max_positions": 3
    },
    "highlow": {
      "symbol": "MSFT",
      "quantity": 10,
      "low_threshold": 140.0,
      "high_threshold": 150.0
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `strategies` | array | List of strategy names to compare |
| `symbol` | string | Stock symbol to backtest |
| `start_date` | string | Start date in YYYY-MM-DD format |
| `end_date` | string | End date in YYYY-MM-DD format |
| `initial_capital` | number | Initial capital for each backtest (default: 10000.0) |
| `trading_session` | string | Trading session: "REGULAR" or "EXTENDED" |
| `strategy_params` | object | Parameters for each strategy, keyed by strategy name |

#### Response

```json
{
  "success": true,
  "message": "Strategy comparison for MSFT completed successfully",
  "backtest_period": {
    "symbol": "MSFT",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 10000.0,
    "trading_session": "REGULAR"
  },
  "metrics_comparison": {
    "ladder": {
      "total_return": 20.0,
      "max_drawdown": 5.0,
      "sharpe_ratio": 1.5,
      "win_rate": 60.0,
      "profit_factor": 2.0,
      "total_trades": 10
    },
    "oto_ladder": {
      "total_return": 15.0,
      "max_drawdown": 4.0,
      "sharpe_ratio": 1.8,
      "win_rate": 70.0,
      "profit_factor": 2.5,
      "total_trades": 20
    },
    "oscillating": {
      "total_return": 18.0,
      "max_drawdown": 6.0,
      "sharpe_ratio": 1.2,
      "win_rate": 55.0,
      "profit_factor": 1.8,
      "total_trades": 30
    }
  },
  "metric_rankings": {
    "total_return": {
      "ladder": 1,
      "oscillating": 2,
      "oto_ladder": 3
    },
    "max_drawdown": {
      "oto_ladder": 1,
      "ladder": 2,
      "oscillating": 3
    },
    "sharpe_ratio": {
      "oto_ladder": 1,
      "ladder": 2,
      "oscillating": 3
    },
    "win_rate": {
      "oto_ladder": 1,
      "ladder": 2,
      "oscillating": 3
    },
    "profit_factor": {
      "oto_ladder": 1,
      "ladder": 2,
      "oscillating": 3
    }
  },
  "overall_ranking": ["oto_ladder", "ladder", "oscillating"],
  "best_strategy": "oto_ladder"
}
```

### Get Backtest History

```
GET /api/backtest/history
```

Get backtest history, optionally filtered by strategy and/or symbol.

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `strategy` | string | Filter by strategy name (optional) |
| `symbol` | string | Filter by symbol (optional) |

#### Response

```json
{
  "success": true,
  "message": "Retrieved 2 backtests",
  "backtests": [
    {
      "backtest_id": "ladder_AAPL_20230101_20230630_20230707123456",
      "strategy_name": "ladder",
      "symbol": "AAPL",
      "period": "2023-01-01 to 2023-06-30",
      "initial_capital": 10000.0,
      "final_capital": 12000.0,
      "total_return": "20.00%",
      "max_drawdown": "5.00%",
      "sharpe_ratio": "1.50",
      "win_rate": "60.00%",
      "total_trades": 10
    },
    {
      "backtest_id": "oto_ladder_MSFT_20230101_20231231_20230707123456",
      "strategy_name": "oto_ladder",
      "symbol": "MSFT",
      "period": "2023-01-01 to 2023-12-31",
      "initial_capital": 10000.0,
      "final_capital": 11500.0,
      "total_return": "15.00%",
      "max_drawdown": "4.00%",
      "sharpe_ratio": "1.80",
      "win_rate": "70.00%",
      "total_trades": 20
    }
  ],
  "count": 2
}
```

### Get Backtest Result

```
GET /api/backtest/{backtest_id}
```

Get a specific backtest result.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `backtest_id` | string | ID of the backtest |

#### Response

```json
{
  "success": true,
  "message": "Retrieved backtest ladder_AAPL_20230101_20230630_20230707123456",
  "backtest_id": "ladder_AAPL_20230101_20230630_20230707123456",
  "summary": {
    "backtest_id": "ladder_AAPL_20230101_20230630_20230707123456",
    "strategy_name": "ladder",
    "symbol": "AAPL",
    "period": "2023-01-01 to 2023-06-30",
    "initial_capital": 10000.0,
    "final_capital": 12000.0,
    "total_return": "20.00%",
    "max_drawdown": "5.00%",
    "sharpe_ratio": "1.50",
    "win_rate": "60.00%",
    "total_trades": 10
  },
  "metrics": {
    "total_trades": 10,
    "winning_trades": 6,
    "losing_trades": 4,
    "win_rate": "60.00%",
    "average_win": "$500.00",
    "average_loss": "$300.00",
    "profit_factor": "2.00",
    "average_trade": "$150.00"
  },
  "trades": [
    {
      "id": "backtest_order_0",
      "symbol": "AAPL",
      "side": "BUY",
      "quantity": 10,
      "price": 150.0,
      "value": 1500.0,
      "timestamp": "2023-01-02T10:00:00Z"
    },
    {
      "id": "backtest_order_1",
      "symbol": "AAPL",
      "side": "SELL",
      "quantity": 10,
      "price": 160.0,
      "value": 1600.0,
      "timestamp": "2023-01-05T14:30:00Z"
    }
  ],
  "equity_curve": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "portfolio_value": 10000.0,
      "cash": 10000.0,
      "position_value": 0.0,
      "close_price": 150.0
    },
    {
      "timestamp": "2023-01-02T00:00:00Z",
      "portfolio_value": 10000.0,
      "cash": 8500.0,
      "position_value": 1500.0,
      "close_price": 150.0
    },
    {
      "timestamp": "2023-01-05T00:00:00Z",
      "portfolio_value": 10100.0,
      "cash": 10100.0,
      "position_value": 0.0,
      "close_price": 160.0
    }
  ]
}
```

### Clear Backtest History

```
DELETE /api/backtest/history
```

Clear backtest history.

#### Response

```json
{
  "success": true,
  "message": "Backtest history cleared",
  "backtests": [],
  "count": 0
}
``` 