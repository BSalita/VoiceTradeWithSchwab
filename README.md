# Automated Trading System

> **IMPORTANT: AI-GENERATED PROJECT**  
> This entire project was 100% coded by Cursor and Claude-3.7-sonnet-thinking. It is a proof-of-concept demonstration of AI-generated software development and has not been tested in real-world trading environments. The performance, reliability, and accuracy of this system are unknown. The entire codebase was generated in just a few hours for the original commit.

A flexible trading application for automated stock trading using the Schwab API.

## Features

- **Multiple Interfaces**:
  - Command-line interface for text commands
  - Voice command interface for hands-free trading
  - RESTful web API for web applications
  
- **Trading Strategies**:
  - Basic order execution
  - Ladder trading strategy
  - Oscillating trading strategy
  - High-Low trading strategy

- **Trading Modes**:
  - Live trading with real orders
  - Paper trading with virtual money but real market data
  - Mock trading with simulated prices

- **Advanced Features**:
  - Extended hours trading
  - Trade history tracking and export
  - Multiple order types (market, limit)
  - Order duration options (day, GTC)

## Architecture

The application is built with a service-oriented architecture that separates core business logic from user interfaces:

- **Services Layer**: Core business logic independent of interfaces
- **Interface Layer**: Different user interfaces that use the services
- **API Layer**: Schwab API client for market data and order execution
- **Models Layer**: Shared data models used across the application

The code follows a standard Python package structure, allowing clean imports in both application code and tests.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/automated-trading.git
   cd automated-trading
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the example environment file and configure it:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file with your Schwab API credentials and preferences.

## Usage

### Command Line Interface

```
python main.py --text
```

This starts an interactive command session where you can type trading commands.

### Voice Command Interface

```
python main.py --voice
```

This starts a voice command interface that listens for spoken commands.

### Web API

```
python main.py --web --host 0.0.0.0 --port 5000
```

This starts a web server that provides a RESTful API for trading operations using Flask.

### FastAPI Web API (Recommended)

```
python main.py --web --use-fastapi --host 0.0.0.0 --port 5000
```

This starts a web server using FastAPI, which provides:
- Interactive API documentation at `/docs` (Swagger UI)
- Alternative documentation at `/redoc` (ReDoc)
- Better performance and type validation
- Async support for handling WebSocket connections

## API Endpoints

The web API provides the following endpoints:

### Trading Endpoints

- `GET /api/account` - Get account information
- `GET /api/orders` - List orders
- `POST /api/orders` - Place an order
- `DELETE /api/orders/:order_id` - Cancel an order

### Market Data Endpoints

- `GET /api/quotes/:symbol` - Get quote for a symbol
- `GET /api/quotes?symbols=AAPL,MSFT` - Get quotes for multiple symbols

### Strategy Endpoints

- `GET /api/strategies` - List active strategies
- `POST /api/strategies` - Start a strategy
- `GET /api/strategies/:strategy_key` - Get strategy status
- `DELETE /api/strategies/:strategy_key` - Stop a strategy

### History Endpoints

- `GET /api/history` - Get trade history
- `GET /api/history/export` - Export trade history to CSV

## Command Examples

### Basic Orders

```
buy 100 shares of AAPL
sell 50 shares of MSFT at $330.50
```

### Strategy Commands

```
ladder buy 100 shares of AAPL with 5 steps from $170 to $175
oscillating strategy for TSLA 10 shares with range 0.5%
highlow strategy for MSFT 5 shares
```

### Management Commands

```
status
show history
export history to trades.csv
cancel order ABC123
```

## Development

### Project Structure

```
automated-trading/
├── app/                       # Main application package
│   ├── api/                   # API client and utilities
│   ├── commands/              # Command processing
│   ├── config/                # Configuration handling
│   ├── interfaces/            # User interfaces
│   │   ├── cli/               # Command line interface
│   │   └── web/               # Web API interfaces
│   ├── models/                # Data models
│   ├── services/              # Business logic services
│   ├── strategies/            # Trading strategies
│   └── utils/                 # Utility functions
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── performance/           # Performance tests
├── .env.example               # Example environment variables
├── main.py                    # Main entry point
├── README.md                  # This file
└── requirements.txt           # Dependencies
```

The project follows a standard Python package structure, allowing for clean imports in both application code and tests:

```python
# Example imports
from app.services.trading_service import TradingService
from app.api.schwab_client import SchwabAPIClient
```

### Running Tests

The application includes a comprehensive test suite that covers all major components, with a focus on testing in mock mode to ensure functionality without requiring real API credentials.

To run all tests:
```
pytest
```

To run specific test categories:
```
pytest tests/unit/            # Run unit tests only
pytest tests/integration/     # Run integration tests only
```

To run tests with coverage report:
```
pytest --cov=app tests/
```

To run a specific test file:
```
pytest tests/unit/test_schwab_client.py
```

You can also use the provided test runner scripts:
```
python run_tests.py           # Run all tests
python run_mock_tests.py      # Run mock-specific tests
```

The test suite includes:
- Unit tests for all services and components
- Integration tests for API endpoints
- Mock mode testing for trading functionality
- Strategy execution tests
- Command processing tests

All tests can be run in mock mode without requiring real API credentials, making it easy to verify functionality in any environment.

## Testing

The application includes a comprehensive test suite to ensure reliability and functionality.

### Running Tests

#### Mock Tests

Mock tests run in a simulated environment without requiring real API credentials:

```bash
python run_mock_tests.py
```

These tests use mock API responses and are ideal for:
- Continuous integration/continuous deployment (CI/CD)
- Development and debugging
- Testing business logic without API dependencies

#### Live API Tests

Live tests connect to the real Schwab API and require valid credentials:

```bash
python run_live_tests.py
```

**IMPORTANT**: Live tests run in PAPER mode by default for safety. They will not place actual trades but will use real API connections.

To run live tests:
1. Set your environment variables with real API credentials:
   ```
   SCHWAB_API_KEY=your_api_key
   SCHWAB_API_SECRET=your_api_secret
   SCHWAB_ACCOUNT_ID=your_account_id
   ```
2. Set the trading mode to PAPER (default) or LIVE:
   ```
   TRADING_MODE=PAPER
   ```
   
> ⚠️ **WARNING**: To run in LIVE mode, you must explicitly set both `TRADING_MODE=LIVE` and `ALLOW_LIVE_TESTS=1`

### Test Organization

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests including API interactions
- `tests/conftest.py`: Shared test fixtures and utilities

### Adding New Tests

When adding new tests:
1. Use the mock mode for routine testing
2. Keep live tests in the integration directory
3. Add appropriate fixtures to conftest.py for reusable test components
4. Follow best practices in `docs/testing_strategy.md` and `docs/test_examples.md`

### Test Documentation

For more detailed information on testing:
- `docs/testing_strategy.md`: Overall testing approach, layers, and best practices
- `docs/test_examples.md`: Examples of tests for different components, especially voice commands
- `tests/live/README.md`: Guidelines for live tests
- `tests/paper/README.md`: Guidelines for paper tests

### Running Specific Test Categories

To run specific test categories:
```bash
# For mock tests:
python run_mock_tests.py --test_type unit

# For live tests:
python run_live_tests.py --test_file tests/integration/test_live_api.py
```

## License

This project is licensed under the MIT License.

## Disclaimer

**IMPORTANT NOTICE:**

This software was entirely generated by AI (Cursor and Claude-3.7-sonnet-thinking) as a proof-of-concept and is provided for educational and demonstration purposes only. 

- The system has not been tested in real-world trading environments
- Performance, reliability, and accuracy are unknown
- No guarantees are made about the financial outcomes of using this system
- The code has not been audited for security vulnerabilities or compliance with financial regulations
- Use of this system for actual trading is strongly discouraged without extensive human review and testing

By using this software, you acknowledge that:
1. It was created as a technology demonstration
2. No human expert has validated its trading strategies or implementation
3. You assume all risks associated with using AI-generated code for financial purposes

The authors and AI systems that generated this code are not responsible for any financial losses, technical issues, or other problems that may arise from using this software. 