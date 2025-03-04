# Automated Trading Testing Strategy

This document outlines the comprehensive testing strategy for the Automated Trading application, covering all aspects from unit tests to live trading validation.

## Testing Layers

The application uses a multi-layered testing approach:

1. **Mock Tests** - No real API connections
2. **Paper Tests** - Real API connections but simulated trades
3. **Live Tests** - Real API connections with actual trades

### Mock Tests

Mock tests are the foundation of our testing strategy. They use simulated API responses and do not require real credentials.

**Characteristics:**
- No real API connections
- No credentials required
- Fast execution
- Suitable for CI/CD pipelines
- Test business logic and code flow

**Command to run:**
```bash
python run_mock_tests.py
```

### Paper Tests

Paper tests connect to the real Schwab API but use paper trading mode (simulated trades without real money).

**Characteristics:**
- Real API connections
- Real credentials required
- No real money used
- Test API integration
- Test rate limiting and error handling
- More comprehensive than live tests

**Prerequisites:**
1. Set environment variables for API credentials:
   ```bash
   export SCHWAB_API_KEY=your_api_key
   export SCHWAB_API_SECRET=your_api_secret
   ```

**Command to run:**
```bash
python run_paper_tests.py
```

### Live Tests

Live tests connect to the real Schwab API in live mode and place actual orders with real money.

**Characteristics:**
- Real API connections
- Real credentials required
- Real money used
- Minimal test coverage focused on critical paths
- Multiple safety measures

**Prerequisites:**
1. Set environment variables for API credentials:
   ```bash
   export SCHWAB_API_KEY=your_api_key
   export SCHWAB_API_SECRET=your_api_secret
   ```

2. Set confirmation environment variable:
   ```bash
   export CONFIRM_LIVE_TESTING=YES_I_UNDERSTAND_THE_RISKS
   ```

**Command to run:**
```bash
python run_live_tests.py
```

## Package Structure

The application uses a standard Python package structure, which allows tests to import modules without path manipulation. All tests can directly import the required modules from the `app` package.

### Python Package Import Structure 

Our test files do not require any manual path manipulation. The project is structured as a proper Python package, and all modules can be imported directly:

```python
# Example imports in test files
from app.services.trading_service import TradingService
from app.api.schwab_client import SchwabAPIClient
```

### Running Tests

Tests can be run using the test runner scripts or using pytest directly:

```bash
# Run all tests
python run_tests.py

# Run tests with pytest
pytest tests/
```

## Test Coverage

| Component | Mock Tests | Paper Tests | Live Tests |
|-----------|------------|-------------|------------|
| SchwabAPIClient | ✅ | ✅ | ✅ |
| Trading Service | ✅ | ✅ | ✅ |
| Command Processing | ✅ | ❌ | ❌ |
| Strategies | ✅ | ✅ | ❌ |
| FastAPI Endpoints | ✅ | ❌ | ❌ |

### Coverage Details

#### Mock Tests Coverage
- **API Client**: Test all API methods with mock responses
- **Trading Service**: Test order placement, cancellation, and retrieval
- **Command Processing**: Test natural language command parsing and execution
- **Strategies**: Test BasicStrategy and LadderStrategy logic
- **FastAPI Endpoints**: Test health check and basic API functionality

#### Paper Tests Coverage
- **API Client**: Test real API connectivity, data retrieval
- **Trading Service**: Test order placement with real API (in paper mode)
- **Strategies**: Test strategy execution with real market data

#### Live Tests Coverage
- **API Client**: Minimal tests for connectivity and data retrieval
- **Trading Service**: Minimal tests for order placement (with immediate cancellation)

## Safety Measures for Live Tests

Live tests include multiple safety measures:

1. **Environment Variables**: Require explicit environment variables
2. **User Confirmation**: Multiple confirmation prompts
3. **Minimal Quantities**: Use minimum possible order sizes (1 share)
4. **Price Limits**: Place limit orders far from market price
5. **Immediate Cancellation**: Cancel orders immediately after placement
6. **Maximum Value Limit**: Cap maximum order value to $200
7. **Account Verification**: Only run on accounts with limited funds
8. **Market Hours Check**: Warn if running outside market hours

## Recommended Testing Workflow

1. **Development Stage**:
   - Run mock tests frequently during development
   - Fix any issues before proceeding

2. **Integration Stage**:
   - Run paper tests to verify API integration
   - Debug any API-related issues

3. **Production Validation**:
   - Run minimal live tests to validate critical functionality
   - Only run on dedicated test accounts with limited funds

## Common Testing Problems and Solutions

### Mock Testing Issues
- **Failed assertions**: Verify your mocked data matches expected formats
- **Missing mocks**: Ensure all external dependencies are properly mocked
- **Patching built-in functions**: When mocking built-in functions like `open`, always use the fully qualified name with the `builtins` module (`patch('builtins.open')` instead of `patch('open')`)

### Paper Testing Issues
- **API connectivity**: Verify credentials and network access
- **Rate limiting**: Add delays between API calls
- **Data format changes**: Update test expectations if API responses change

### Live Testing Issues
- **Orders actually executing**: Use limit prices far from market
- **Account access issues**: Verify account permissions
- **Market closed errors**: Only run during market hours

## Adding New Tests

When adding new functionality, follow this pattern:

1. First write mock tests covering the functionality
2. If the feature requires API interaction, add paper tests
3. Only add live tests for critical order-related functionality

## Best Practices for Test Writing

### Mocking Guidelines

1. **Mocking External Services**:
   ```python
   @patch('app.api.schwab_client.SchwabAPIClient.get_quote')
   def test_market_data(self, mock_get_quote):
       mock_get_quote.return_value = {'symbol': 'AAPL', 'price': 150.0}
       # Test code...
   ```

2. **Mocking Built-in Functions**:
   Always use the full module path when mocking built-in functions:
   ```python
   # CORRECT WAY
   @patch('builtins.open', create=True)
   def test_file_operations(self, mock_open):
       mock_open.return_value.__enter__.return_value = io.StringIO("mock file content")
       # Test code...
       
   # INCORRECT WAY - Will cause errors
   @patch('open', create=True)  # Don't do this!
   def test_file_operations(self, mock_open):
       # This will fail
   ```

3. **Mocking Time**:
   ```python
   @patch('time.time')
   def test_timeout_function(self, mock_time):
       mock_time.side_effect = [0, 10]  # First call returns 0, second call returns 10
       # Test code...
   ```

4. **Mocking Classes**:
   ```python
   @patch('app.services.SomeClass')
   def test_with_mock_class(self, MockClass):
       instance = MockClass.return_value
       instance.method.return_value = 'mocked result'
       # Test code...
   ```

### Assertions Best Practices

1. Use specific assertions for better error messages:
   ```python
   # Good
   self.assertEqual(result.status_code, 200)
   
   # Better
   self.assertEqual(result.status_code, 200, f"Expected 200 OK, got {result.status_code}")
   ```

2. Test both success and error cases:
   ```python
   def test_valid_input(self):
       # Test with valid input
       
   def test_invalid_input(self):
       # Test with invalid input
   ``` 