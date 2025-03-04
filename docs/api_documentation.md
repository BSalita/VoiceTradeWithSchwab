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