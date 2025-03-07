# User Guide: Automated Trading System

This comprehensive guide covers both end-user operation and developer instructions for the Automated Trading System.

## Table of Contents

- [For End Users](#for-end-users)
  - [Getting Started](#getting-started)
  - [System Requirements](#system-requirements)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Basic Usage](#basic-usage)
  - [Voice Commands](#voice-commands)
  - [Text Commands](#text-commands)
  - [Trading Strategies](#trading-strategies)
  - [Market Data](#market-data)
  - [Account Management](#account-management)
  - [Backtesting](#backtesting)
  - [Troubleshooting](#troubleshooting)
  - [FAQ](#faq)
- [For Developers](#for-developers)
  - [Development Environment Setup](#development-environment-setup)
  - [Project Structure](#project-structure)
  - [API Integration](#api-integration)
  - [Component Overview](#component-overview)
  - [Adding New Features](#adding-new-features)
  - [Testing](#testing)
  - [Deployment](#deployment)
  - [Contributing Guidelines](#contributing-guidelines)

## For End Users

### Getting Started

The Automated Trading System provides a voice-operated and text-based interface for executing trades and implementing trading strategies through the Schwab brokerage platform.

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: Version 3.8 or higher
- **Hardware**:
  - CPU: Intel Core i5 or equivalent (recommended)
  - RAM: 8GB minimum, 16GB recommended
  - Disk Space: 1GB available
  - Microphone: Required for voice commands
  - Speakers/Headphones: Required for voice feedback

### Installation

#### Option 1: Install from PyPI

```bash
pip install auto-trading-system
```

#### Option 2: Install from Source

```bash
git clone https://github.com/your-organization/voicetradewithschwab.git
cd voicetradewithschwab
pip install -e .
```

### Configuration

Before using the system, you need to configure your API credentials:

1. Create a `.env` file in the project root directory
2. Add your Schwab API credentials:

```
SCHWAB_API_KEY=your_api_key
SCHWAB_API_SECRET=your_api_secret
SCHWAB_ACCOUNT_ID=your_account_id
TRADING_MODE=paper  # Use "paper" for paper trading or "live" for live trading
```

3. Additional optional settings:

```
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
USE_MOCK_DATA=false  # Set to true to use mock data for testing
SPEECH_ENGINE=google  # google or whisper
```

### Basic Usage

To start the application:

```bash
voicetrade start
```

This will launch the interactive interface where you can issue voice or text commands.

#### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--mode` | Trading mode: "paper" or "live" |
| `--log-level` | Logging level (default: INFO) |
| `--config` | Path to custom config file |
| `--voice` | Enable voice interface (default: enabled) |
| `--no-voice` | Disable voice interface |

Example:

```bash
voicetrade start --mode paper --log-level DEBUG
```

### Voice Commands

The system supports natural language voice commands for trading, market data, and account management.

To activate voice command mode:

1. Start the application
2. Say "Hey Trader" or press the microphone button
3. Speak your command clearly
4. The system will confirm your command and execute it

#### Basic Voice Command Patterns

| Command Type | Example |
|--------------|---------|
| Buy Order | "Buy 100 shares of Apple" |
| Sell Order | "Sell 50 shares of Microsoft" |
| Limit Order | "Buy 75 shares of Google at 150 dollars" |
| Quote | "Get quote for Tesla" |
| Account | "What's my account balance?" |
| Position | "Show my positions" |
| Strategy | "Start ladder strategy for Amazon" |

#### Voice Command Examples

- "Buy 100 shares of Apple"
- "Sell 50 shares of Microsoft at 350 dollars"
- "Get the current price of Tesla"
- "What's my buying power?"
- "Show my open orders"
- "Cancel my order for Google"
- "Start a ladder strategy for Amazon with 5 steps"
- "Stop all running strategies"

### Text Commands

Text commands follow the same patterns as voice commands but are entered via keyboard:

#### Command Syntax

Text commands use a simple syntax:

```
command [parameters]
```

#### Text Command Examples

```
buy 100 AAPL
sell 50 MSFT at 350
quote TSLA
account balance
show positions
cancel order ORD123456
start ladder AMZN steps=5 total=100 start=150 end=160
stop strategy STRAT123456
```

### Trading Strategies

The system supports several built-in trading strategies:

#### Ladder Strategy

Places a series of orders at regular price intervals:

```
start ladder SYMBOL steps=N total=QUANTITY start=PRICE1 end=PRICE2
```

Example:
```
start ladder AAPL steps=5 total=100 start=150 end=155
```

This creates a buy ladder with 5 orders between $150 and $155, totaling 100 shares.

You can also use the simpler voice command syntax:
```
ladder buy 100 shares of AAPL with 5 steps from $150 to $155
```

When executed, the ladder strategy places all orders immediately and returns information about each order placed, making it easy to track and manage them.

#### TWAP Strategy

Time-Weighted Average Price strategy breaks a large order into smaller chunks executed at regular time intervals:

```
start twap SYMBOL side=BUY/SELL quantity=N intervals=N duration=MINUTES
```

Example:
```
start twap MSFT side=buy quantity=1000 intervals=10 duration=60
```

This buys 1000 shares of Microsoft in 10 equal parts over 60 minutes.

#### OTO Ladder Strategy

The OTO Ladder (One-Triggers-Other) Step Strategy creates a step-based approach for scaling in and out of positions using thinkorswim's script feature:

```
start oto_ladder symbol=SYMBOL start_price=PRICE step=STEP_SIZE initial_shares=QUANTITY price_target=PRICE_TARGET
```

Example:
```
start oto_ladder symbol=SPY start_price=450 step=5 initial_shares=100 price_target=500
```

This generates an OTO Ladder strategy that:
1. Sells 5% of the position (5 shares in this example) when price reaches each step above $450
2. For each sell, creates a buy-back order 2x the step size lower ($10 lower in this example)
3. For each buy-back, creates a take-profit order at the next step higher
4. Uses EXTO (Extended Hours) time-in-force for all orders

Voice command example:
```
Generate OTO Ladder strategy for SPY starting at $450 with $5 steps and 100 initial shares
```

When executed, the strategy:
1. Calculates the appropriate price levels based on current market conditions
2. Generates OTO Ladder code for thinkorswim
3. Saves the OTO Ladder file to the `oto_ladder` directory with a timestamp
4. Returns a result with the file path and strategy parameters

To use the generated OTO Ladder code:
1. Copy the code from the result or open the saved `.ts` file
2. In thinkorswim, go to Studies > Edit Studies > Create
3. Paste the code and save with a name like "OTO Ladder Strategy"
4. Apply the study to your chart
5. Follow the alerts to place OTO orders when price reaches new step levels

This strategy works best for trending markets where you want to gradually scale out of a position while automatically setting up for potential dip-buying opportunities.

#### Custom Strategies

For custom strategies, refer to the strategy documentation or use:

```
start strategy STRATEGY_NAME PARAM1=VALUE1 PARAM2=VALUE2 ...
```

### Market Data

Access market data with the following commands:

#### Quotes

```
quote SYMBOL
```

Example:
```
quote AAPL
```

#### Multiple Quotes

```
quotes SYMBOL1 SYMBOL2 SYMBOL3
```

Example:
```
quotes AAPL MSFT GOOG
```

#### Historical Data

```
history SYMBOL [period=1d/1w/1m/1y] [interval=1m/5m/15m/1h/1d]
```

Example:
```
history AAPL period=1w interval=15m
```

### Account Management

Manage your account with these commands:

#### Account Balance

```
account balance
```

#### Positions

```
show positions
```

#### Orders

```
show orders [open/filled/canceled/all]
```

Example:
```
show orders open
```

#### Cancel Order

```
cancel order ORDER_ID
```

Example:
```
cancel order ORD123456
```

### Backtesting

The system provides comprehensive backtesting capabilities to evaluate and compare trading strategies using historical data.

#### Running a Backtest

To backtest a strategy, use the following command format:

```
backtest STRATEGY_NAME on SYMBOL from START_DATE to END_DATE [with initial capital $AMOUNT]
```

Example:
```
backtest ladder on AAPL from 2023-01-01 to 2023-06-30
```

This will run a backtest of the ladder strategy on AAPL from January 1, 2023 to June 30, 2023 with the default initial capital of $10,000.

You can specify a different initial capital:
```
backtest oto_ladder on SPY from 2023-01-01 to 2023-12-31 with initial capital $50000
```

#### Comparing Strategies

To compare multiple strategies, use the following command format:

```
compare strategies STRATEGY1,STRATEGY2,... on SYMBOL from START_DATE to END_DATE [with initial capital $AMOUNT]
```

Example:
```
compare strategies ladder,oto_ladder,oscillating on MSFT from 2023-01-01 to 2023-12-31
```

This will run backtests for the ladder, oto_ladder, and oscillating strategies on MSFT for the year 2023, and compare their performance metrics.

#### Backtest Results

Backtest results include the following metrics:

| Metric | Description |
|--------|-------------|
| Total Return | Percentage return over the backtest period |
| Max Drawdown | Maximum percentage decline from a peak |
| Sharpe Ratio | Risk-adjusted return (higher is better) |
| Win Rate | Percentage of profitable trades |
| Profit Factor | Ratio of gross profits to gross losses |
| Average Win | Average profit per winning trade |
| Average Loss | Average loss per losing trade |
| Total Trades | Total number of trades executed |

#### Strategy Comparison

When comparing strategies, the system ranks them based on multiple metrics and provides an overall ranking. The best strategy is determined by its combined performance across all metrics.

#### API Endpoints

For programmatic access, the following API endpoints are available:

- `POST /api/backtest`: Run a backtest
- `POST /api/backtest/compare`: Compare multiple strategies
- `GET /api/backtest/history`: Get backtest history
- `GET /api/backtest/{backtest_id}`: Get a specific backtest result
- `DELETE /api/backtest/history`: Clear backtest history

### Troubleshooting

#### Order Placement Issues

If your order fails to execute, check the following:

1. **Invalid Symbol Format**: 
   - Symbols must contain only uppercase letters
   - Symbols containing "INVALID" are automatically rejected for testing/safety purposes
   - Example of valid symbol: "AAPL"
   - Example of invalid symbol: "INVALID_MSFT" or "aapl"

2. **Price Format**:
   - For limit orders, a valid price must be specified
   - Example: "buy 10 shares of AAPL at $150.50"

3. **Quantity Issues**:
   - Quantity must be a positive integer
   - Example of invalid quantity: "buy -5 shares of AAPL"

#### Strategy Issues

If you encounter issues with strategies:

1. **Strategy Command Format**:
   - Check that you're using the correct syntax for the strategy
   - Example: "start ladder AAPL steps=5 total=100 start=150 end=155"

2. **Viewing Active Strategies**:
   - Use the "strategies" command to view all active strategies
   - Note that some strategies might not have detailed configuration information available

#### Voice Recognition Issues

If the system fails to recognize your voice commands:

1. Check that your microphone is properly connected and functioning
2. Speak clearly and at a normal pace
3. Reduce background noise
4. Try using more concise commands
5. If using Whisper, ensure you have installed the required dependencies

#### API Connection Issues

If you encounter API connection errors:

1. Verify your internet connection
2. Check that your API credentials are correct in the `.env` file
3. Ensure the Schwab API service is operational
4. Check if you've exceeded API rate limits
5. Verify your account is authorized for API trading

#### Common Error Messages

| Error | Possible Cause | Solution |
|-------|---------------|----------|
| "Authentication failed" | Invalid API credentials | Check your API key and secret |
| "Insufficient funds" | Not enough buying power | Deposit funds or reduce order size |
| "Invalid symbol" | Incorrect stock symbol | Verify the symbol is correct |
| "Rate limit exceeded" | Too many API requests | Wait before making more requests |
| "Market closed" | Trading outside market hours | Wait for market hours or use extended hours |

### FAQ

**Q: Is paper trading available?**
A: Yes, set `TRADING_MODE=paper` in your `.env` file to use paper trading.

**Q: Can I trade options?**
A: Currently, the system supports equity trading only. Options trading is planned for a future release.

**Q: How secure is my account information?**
A: The system stores API credentials locally and uses secure connections. Never share your `.env` file or API credentials.

**Q: Does the system work with brokers other than Schwab?**
A: Currently, only Schwab is supported. Integration with other brokers is planned.

**Q: Can I customize voice commands?**
A: Yes, advanced users can modify the command parsing logic in the `app/interfaces/cli/command_processor.py` file.

## Available Strategies

The system includes several built-in trading strategies that can be used out of the box. Here's an overview of the available strategies and their parameters:

### Ladder Strategy

Creates a series of orders at incrementally spaced price levels.

**Parameters:**
- `symbol` - Stock symbol
- `steps` - Number of price levels
- `start_price` - Starting price level
- `end_price` - Ending price level
- `total_quantity` - Total number of shares to trade
- `side` - Buy or sell (default: buy)
- `distribution` - How to distribute shares among levels (equal or weighted)

**Example:**
```
start ladder strategy for AAPL with steps=5 start_price=150 end_price=155 total_quantity=100
```

### OTO Ladder Strategy

Creates a series of one-triggers-other (OTO) orders at incrementally spaced price levels.

**Parameters:**
- `symbol` - Stock symbol
- `start_price` - Starting price level
- `step` - Price increment between levels
- `initial_shares` - Number of shares per level
- `price_target` - Optional price level at which the strategy will terminate (if current price reaches or exceeds this value)

**Example:**
```
start oto_ladder strategy for MSFT with start_price=250 step=5 initial_shares=10 price_target=280
```

### HighLow Strategy

A simple breakout strategy that buys when price falls below a threshold and sells when it rises above another threshold.

**Parameters:**
- `symbol` - Stock symbol
- `quantity` - Number of shares per trade
- `low_threshold` - Price below which to buy
- `high_threshold` - Price above which to sell

**Example:**
```
start highlow strategy for AAPL with quantity=10 low_threshold=140 high_threshold=150
```

### Oscillating Strategy

Trades based on price oscillations within a range around the current price.

**Parameters:**
- `symbol` - Stock symbol
- `quantity` - Number of shares per trade
- `price_range` - Price movement range (percentage or fixed amount)
- `is_percentage` - Whether price_range is a percentage (true) or fixed amount (false)
- `min_trade_interval` - Minimum seconds between trades (default: 60)
- `max_positions` - Maximum number of concurrent positions (default: 3)

**Example:**
```
start oscillating strategy for TSLA with quantity=5 price_range=0.02 is_percentage=true
```

### TWAP Strategy

Time-Weighted Average Price strategy that executes trades at regular intervals.

**Parameters:**
- `symbol` - Stock symbol
- `total_quantity` - Total number of shares to trade
- `intervals` - Number of execution intervals
- `duration` - Total strategy duration in minutes

**Example:**
```
start twap strategy for GOOG with total_quantity=100 intervals=5 duration=60
```

For more detailed examples, please check the command reference in the next section.

## For Developers

### Development Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/your-organization/voicetradewithschwab.git
cd voicetradewithschwab
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. Set up pre-commit hooks:
```bash
pre-commit install
```

5. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Project Structure

The codebase is organized as follows:

```
voicetradewithschwab/
├── app/                      # Application source code
│   ├── api/                  # API client implementations
│   ├── config/               # Configuration handlers
│   ├── core/                 # Core business logic
│   ├── interfaces/           # User interfaces (CLI, API)
│   ├── models/               # Data models
│   ├── services/             # Service layer
│   └── strategies/           # Trading strategy implementations
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── mock/                 # Mock tests
│   ├── paper/                # Paper trading tests
│   └── live/                 # Live trading tests (use with caution)
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── .env.example              # Example environment variables
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── setup.py                  # Package setup script
└── README.md                 # Project overview
```

### API Integration

#### Schwab API Client

The system integrates with the Schwab API via the `SchwabAPIClient` class in `app/api/schwab_client.py`. To extend or modify API integration:

1. Familiarize yourself with the Schwab API documentation
2. Use the client methods as documented in `docs/api_documentation.md`
3. For new endpoints, add methods to the client class following the established pattern

Example:

```python
def get_options_chain(self, symbol):
    """Get options chain for a symbol."""
    endpoint = f"/v1/markets/options/{symbol}"
    response = self._send_request("GET", endpoint)
    return self._process_response(response)
```

### Component Overview

#### Command Processing

Commands are processed by the `CommandProcessor` class in `app/interfaces/cli/command_processor.py`:

1. Command text is parsed to identify command type and parameters
2. Command is validated for required parameters and format
3. Command is routed to the appropriate service
4. Service executes the command and returns a result
5. Result is formatted for presentation to the user

#### Voice Recognition

Voice commands are handled by the `VoiceCommandHandler` class in `app/interfaces/cli/voice_command_handler.py`:

1. Audio is captured from the microphone
2. Speech is recognized using Google or Whisper engine
3. Recognized text is sent to the command processor
4. Results are spoken back to the user

#### Service Layer

The service layer (`app/services/`) abstracts business logic:

- `TradingService`: Handles order placement and management
- `MarketDataService`: Provides market data access
- `StrategyService`: Manages trading strategies
- `AccountService`: Handles account information

#### Strategy Framework

Strategies are implemented in `app/strategies/`:

1. Base `Strategy` class defines the interface
2. Concrete strategy classes implement specific algorithms
3. `StrategyService` manages strategy lifecycle
4. Strategy parameters are validated before execution

### Adding New Features

#### Adding a New Command

To add a new command:

1. Update the `CommandProcessor.identify_command_type` method to recognize the new command
2. Add a validation method for the command
3. Implement the command execution logic in the appropriate service
4. Add tests for the new command

Example:

```python
def identify_command_type(self, command_parts):
    """Identify command type from command parts."""
    if not command_parts:
        return None
    
    command = command_parts[0].lower()
    
    # Existing command mappings...
    
    # New command
    if command in ["alert", "notify"]:
        return "price_alert"
    
    return None

def validate_price_alert_command(self, command_parts):
    """Validate price alert command."""
    if len(command_parts) < 4:
        return {
            "valid": False,
            "error": "Incomplete command. Format: alert SYMBOL [above/below] PRICE"
        }
    
    # Validation logic...
    
    return {"valid": True}
```

#### Adding a New Strategy

To implement a new strategy:

1. Create a new class in `app/strategies/` that inherits from `Strategy`
2. Implement required methods: `validate_parameters` and `execute`
3. Register the strategy in `app/strategies/__init__.py`
4. Add tests in `tests/unit/strategies/`
5. Document the strategy in `docs/strategy_implementation.md`

Example skeleton:

```python
class MyNewStrategy(Strategy):
    """My new trading strategy."""
    
    def validate_parameters(self):
        """Validate strategy parameters."""
        # Parameter validation logic
        return True
    
    def execute(self):
        """Execute the strategy logic."""
        # Strategy implementation
        return True
```

### Testing

The system uses pytest for testing and follows a proper Python package structure:

#### Project Structure

The project is organized as a standard Python package, which allows for clean imports:

```python
from app.services.trading_service import TradingService
from app.api.schwab_client import SchwabAPIClient
```

This structure eliminates the need for path manipulation in test files or application code.

#### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --mock

# Run with coverage
python run_tests.py --unit --coverage
```

#### Test Types

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Mock Tests**: Test with mock API responses
- **Paper Tests**: Test with paper trading account
- **Live Tests**: Test with live trading account (use with caution)

#### Writing Tests

Follow these guidelines when writing tests:

1. Use descriptive test names
2. Test one concept per test function
3. Use fixtures for common setup
4. Mock external dependencies
5. Include both positive and negative test cases
6. Use proper import paths (no sys.path manipulation)
7. Write comprehensive docstrings for test methods

Example test file:

```python
"""
Unit tests for the TradingService class.

These tests verify that the TradingService correctly handles
order placement, cancellation, and retrieval operations.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.trading_service import TradingService
from app.api.schwab_client import SchwabAPIClient

class TestTradingService:
    """Test suite for the TradingService functionality."""
    
    def setup_method(self):
        """
        Set up test environment before each test method runs.
        
        This method:
        1. Creates a mock API client
        2. Initializes a TradingService instance
        """
        self.api_client = MagicMock(spec=SchwabAPIClient)
        self.trading_service = TradingService()
        self.trading_service.api_client = self.api_client
    
    def test_place_market_order(self):
        """
        Test placing a market order successfully.
        
        Verifies that:
        1. The order is processed correctly
        2. The API client is called with the right parameters
        3. The response contains the expected data
        """
        # Test implementation
        
    def teardown_method(self):
        """
        Clean up after each test method completes.
        """
        pass

For more detailed examples and best practices, see the [Test Examples](test_examples.md) and [Testing Strategy](testing_strategy.md) documentation.

### Deployment

The system can be deployed in various environments:

#### Local Deployment

For personal use on a local machine:

1. Install the package
2. Configure the `.env` file
3. Run the application

#### Server Deployment

For multi-user or API access:

1. Set up a server with Python 3.8+
2. Install the package and dependencies
3. Configure environment variables
4. Set up a service manager (systemd, supervisor)
5. Configure a web server if using the web interface (nginx, apache)

Example systemd service file:

```ini
[Unit]
Description=Automated Trading System
After=network.target

[Service]
User=trading
WorkingDirectory=/opt/voicetradewithschwab
ExecStart=/opt/voicetradewithschwab/venv/bin/python -m app.main
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

#### Docker Deployment

For containerized deployment:

1. Build the Docker image:
```bash
docker build -t voicetradewithschwab .
```

2. Run the container:
```bash
docker run -d --name trading-system \
  -p 8000:8000 \
  --env-file .env \
  voicetradewithschwab
```

### Contributing Guidelines

#### Code Style

Follow these style guidelines:

1. Use PEP 8 for Python code style
2. Sort imports with isort
3. Format code with black
4. Use descriptive variable and function names
5. Write docstrings for all functions, classes, and modules

#### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

#### Code Review Criteria

Pull requests are evaluated based on:

1. Code quality and style
2. Test coverage
3. Documentation
4. Performance impact
5. Security considerations

#### Security Practices

When contributing, follow these security practices:

1. Never commit API credentials or secrets
2. Validate all user inputs
3. Use secure dependencies
4. Follow the principle of least privilege
5. Document security implications of changes 