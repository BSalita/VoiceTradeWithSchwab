# Live Trading Tests - USE WITH EXTREME CAUTION

⚠️ **WARNING** ⚠️  
These tests connect to the real Schwab API in LIVE trading mode and use REAL MONEY.

## Prerequisites

1. Set environment variables for API credentials:
   ```bash
   export SCHWAB_API_KEY=your_api_key
   export SCHWAB_API_SECRET=your_api_secret
   ```

2. Set confirmation environment variable:
   ```bash
   export CONFIRM_LIVE_TESTING=YES_I_UNDERSTAND_THE_RISKS
   ```

3. Enable live testing:
   ```bash
   export ENABLE_LIVE_TESTS=1
   ```

## Running the Tests

The safest way to run these tests is to use the provided script with built-in safety checks:

```bash
python run_live_tests.py
```

## Safety Measures

These tests include multiple safety measures:

1. **Environment Variables**: Require explicit environment variables
2. **User Confirmation**: Multiple confirmation prompts
3. **Minimal Quantities**: Use minimum possible order sizes (1 share)
4. **Price Limits**: Place limit orders far from market price
5. **Immediate Cancellation**: Cancel orders immediately after placement
6. **Maximum Value Limit**: Cap maximum order value to $200
7. **Account Verification**: Only run on accounts with limited funds
8. **Market Hours Check**: Warn if running outside market hours

## Recommendations

- Only run these tests on a dedicated test account with minimal funds
- Run during market hours when cancellations can be processed quickly
- Monitor the tests while they are running
- Check your brokerage account after running to ensure all orders were canceled
- Start with paper tests first before attempting live tests

## Test Coverage

The live tests cover only essential functionality:
- API connectivity with real credentials
- Basic data retrieval
- Minimal order placement with immediate cancellation 