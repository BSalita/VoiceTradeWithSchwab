#!/usr/bin/env python
"""
Performance Test Runner for Automated Trading System.

This script runs performance tests to measure system performance
under various load conditions and scenarios.
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from tests.performance.lib.reporting import PerformanceReporter
from tests.performance.lib.metrics import MetricsCollector
from tests.performance.scenarios import (
    get_all_test_scenarios,
    get_test_scenario
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("performance_tests")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run performance tests for the Automated Trading System")
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to test configuration file"
    )
    
    parser.add_argument(
        "--category",
        type=str,
        choices=["order_processing", "market_data", "strategy_execution", 
                 "voice_commands", "scalability", "all"],
        default="all",
        help="Test category to run (default: all)"
    )
    
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="Number of concurrent users to simulate (default: 10)"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds (default: 60)"
    )
    
    parser.add_argument(
        "--ramp-up",
        type=int,
        default=10,
        help="Ramp-up period in seconds (default: 10)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="tests/performance/reports",
        help="Directory to store test results (default: tests/performance/reports)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--compare-with",
        type=str,
        help="Path to previous test results for comparison"
    )
    
    return parser.parse_args()


def load_config(config_path):
    """Load test configuration from JSON file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {e}")
        sys.exit(1)


def prepare_output_directory(output_dir):
    """Prepare output directory for test results."""
    # Create timestamp-based subdirectory for this test run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(output_dir, timestamp)
    
    # Create directories if they don't exist
    os.makedirs(run_dir, exist_ok=True)
    
    return run_dir


def run_tests(config, output_dir):
    """Run performance tests based on configuration."""
    logger.info(f"Starting performance tests with configuration: {config}")
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    
    # Get test scenarios to run
    if config["category"] == "all":
        test_scenarios = get_all_test_scenarios()
    else:
        test_scenarios = [get_test_scenario(config["category"])]
    
    if not test_scenarios:
        logger.error(f"No test scenarios found for category: {config['category']}")
        return False
    
    # Run each test scenario
    results = {}
    
    for scenario_class in test_scenarios:
        scenario_name = scenario_class.__name__
        logger.info(f"Running test scenario: {scenario_name}")
        
        # Initialize scenario
        scenario = scenario_class(
            metrics=metrics,
            config=config
        )
        
        try:
            # Setup test
            logger.info(f"Setting up {scenario_name}")
            scenario.setup()
            
            # Execute test
            logger.info(f"Executing {scenario_name}")
            start_time = time.time()
            scenario.execute()
            execution_time = time.time() - start_time
            
            # Record basic results
            results[scenario_name] = {
                "success": True,
                "execution_time": execution_time,
                "metrics": metrics.get_metrics_for_scenario(scenario_name)
            }
            
            logger.info(f"Completed {scenario_name} in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error executing {scenario_name}: {e}", exc_info=True)
            results[scenario_name] = {
                "success": False,
                "error": str(e)
            }
        finally:
            # Cleanup
            try:
                logger.info(f"Cleaning up {scenario_name}")
                scenario.cleanup()
            except Exception as e:
                logger.error(f"Error during cleanup of {scenario_name}: {e}")
    
    # Generate report
    reporter = PerformanceReporter(output_dir)
    report_path = reporter.generate_report(results, config)
    
    # Compare with previous results if requested
    if "compare_with" in config and config["compare_with"]:
        comparison_report_path = reporter.generate_comparison_report(
            results, 
            config["compare_with"],
            config
        )
        logger.info(f"Comparison report generated at: {comparison_report_path}")
    
    logger.info(f"Performance test report generated at: {report_path}")
    return all(r.get("success", False) for r in results.values())


def main():
    """Main entry point for the performance test runner."""
    args = parse_arguments()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load configuration from file or use command line arguments
    if args.config:
        config = load_config(args.config)
    else:
        config = {
            "category": args.category,
            "users": args.users,
            "duration": args.duration,
            "ramp_up": args.ramp_up,
        }
        
        if args.compare_with:
            config["compare_with"] = args.compare_with
    
    # Prepare output directory
    output_dir = prepare_output_directory(args.output_dir)
    
    # Run tests
    success = run_tests(config, output_dir)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 