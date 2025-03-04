# Paper Trading Tests

This directory contains tests that connect to the real Schwab API but use paper trading mode (simulated trades without real money).

## Prerequisites

1. Set environment variables for API credentials:
   ```bash
   export SCHWAB_API_KEY=your_api_key
   export SCHWAB_API_SECRET=your_api_secret
   ```

2. Enable paper testing:
   ```bash
   export ENABLE_PAPER_TESTS=1
   ```

## Running the Tests

The easiest way to run these tests is to use the provided script:

```bash
python run_paper_tests.py
```

Alternatively, you can run them directly with pytest:

```bash
pytest tests/paper -v
```

## Test Coverage

The paper tests cover:

- API connectivity with real credentials
- Data retrieval (quotes, account info)
- Order placement in paper trading mode
- Strategy execution with real market data

## Safety Measures

These tests:
- Connect to the real API but use paper trading mode
- Do not use real money
- Place simulated orders only 