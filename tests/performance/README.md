# Performance Testing Framework

This directory contains the performance testing framework for the Automated Trading System. The purpose of these tests is to measure and benchmark the system's performance under various loads and scenarios.

## Overview

Performance testing helps identify:

- System bottlenecks
- Resource utilization patterns
- Response time degradation under load
- Maximum sustainable throughput
- Behavior under stress conditions

## Test Scenarios

The framework includes test scenarios for:

1. **Order Processing**: Measures order processing throughput and latency.
2. **Market Data Processing**: Tests the system's ability to handle high-frequency market data.
3. **Strategy Execution**: Benchmarks performance of various trading strategies.
4. **Voice Command Processing**: Measures voice recognition and command processing speed.
5. **System Scalability**: Tests behavior with increasing user load and concurrent strategies.

## Key Metrics

Performance tests track these key metrics:

- **Latency**: Time to process individual requests (ms).
- **Throughput**: Number of operations per second (ops/sec).
- **Error Rate**: Percentage of operations that fail under load.
- **Resource Utilization**: CPU, memory, network usage.
- **Scalability**: Performance change with increasing load.

## Running Performance Tests

### Prerequisites

- Python 3.8 or higher
- All project dependencies installed
- Recommended: Dedicated test environment to avoid interference

### Basic Usage

```bash
# Run all performance tests
python -m tests.performance.run_performance_tests

# Run specific performance test category
python -m tests.performance.run_performance_tests --category=order_processing

# Run tests with specific load parameters
python -m tests.performance.run_performance_tests --users=50 --duration=300
```

### Configuration

Performance tests can be configured through command-line arguments or a configuration file:

```bash
# Use configuration file
python -m tests.performance.run_performance_tests --config=tests/performance/configs/high_load.json

# Set specific parameters
python -m tests.performance.run_performance_tests --ramp-up=30 --test-duration=600 --concurrent-users=100
```

## Test Reports

After test execution, detailed reports are generated in the `tests/performance/reports` directory:

- HTML reports with charts and graphs
- CSV data for further analysis
- JSON format for integration with monitoring systems

Example report sections:
- Test summary and environment information
- Latency percentiles (p50, p90, p95, p99)
- Throughput over time
- Error rate analysis
- Resource utilization charts
- Comparison with baseline performance

## Continuous Performance Testing

The performance tests are integrated into the CI/CD pipeline to catch performance regressions early:

- Daily execution of critical performance tests
- Performance comparison with previous runs
- Alerts for significant performance degradation
- Weekly comprehensive performance test suite

## Directory Structure

```
tests/performance/
├── README.md                   # This documentation
├── run_performance_tests.py    # Main test runner
├── configs/                    # Test configurations
│   ├── default.json            # Default configuration
│   ├── high_load.json          # High load test configuration
│   └── stress_test.json        # Stress test configuration
├── scenarios/                  # Test scenarios
│   ├── order_processing.py     # Order processing tests
│   ├── market_data.py          # Market data tests
│   ├── strategy_execution.py   # Strategy execution tests
│   ├── voice_commands.py       # Voice command tests
│   └── scalability.py          # Scalability tests
├── lib/                        # Support libraries
│   ├── metrics.py              # Metrics collection
│   ├── load_generation.py      # Load generation utilities
│   └── reporting.py            # Report generation
└── reports/                    # Test result reports
    └── .gitignore              # Ignore generated reports
```

## Writing New Performance Tests

To create a new performance test:

1. Create a new Python file in the `scenarios` directory
2. Implement the test using the `PerformanceTest` base class
3. Define setup, execution, and cleanup methods
4. Register custom metrics if needed
5. Add the test to the test runner configuration

Example test structure:

```python
from tests.performance.lib.base import PerformanceTest

class OrderProcessingTest(PerformanceTest):
    """Performance test for order processing."""
    
    def setup(self):
        """Prepare test environment."""
        self.trading_service = self.get_service("trading")
        self.symbols = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]
        
    def execute(self):
        """Execute the test scenario."""
        for i in range(self.config.iterations):
            symbol = self.symbols[i % len(self.symbols)]
            with self.measure("order_placement"):
                self.trading_service.place_market_order(
                    symbol=symbol,
                    quantity=100,
                    side="buy" if i % 2 == 0 else "sell"
                )
                
    def cleanup(self):
        """Clean up after test."""
        for order in self.open_orders:
            self.trading_service.cancel_order(order["order_id"])
```

## Performance Baselines

Performance baselines are maintained to track system performance over time:

- **Order Processing**: < 100ms latency at 95th percentile, > 100 orders/sec
- **Market Data**: < 50ms processing time, > 1000 quotes/sec
- **Strategy Execution**: < 200ms strategy cycle time
- **Voice Commands**: < 1.5s from speech to command execution
- **System Scalability**: Linear scaling to 100 concurrent users

## Troubleshooting Performance Issues

Common performance issues and solutions:

1. **High Order Latency**
   - Check database connection pool settings
   - Verify network latency to broker API
   - Examine order validation logic

2. **Market Data Processing Bottlenecks**
   - Review data serialization/deserialization
   - Check subscription management
   - Consider optimizing storage of historical data

3. **Strategy Execution Delays**
   - Profile strategy execution code
   - Optimize market data access patterns
   - Consider caching frequently used data

4. **Voice Command Processing Issues**
   - Check audio processing pipeline
   - Optimize speech recognition settings
   - Review command parsing logic

## Additional Resources

- [Locust Documentation](https://docs.locust.io/) - The load testing tool used
- [Grafana Dashboards](https://grafana.com/) - For performance visualization
- [JMeter](https://jmeter.apache.org/) - Alternative load testing tool 