#!/usr/bin/env python
"""
Test Runner for Automated Trading System

This script provides a unified interface for running all types of tests:
- Unit tests
- Integration tests
- Mock tests
- Paper tests
- Live tests (with appropriate safeguards)

Usage:
    python run_tests.py [--unit] [--integration] [--mock] [--paper] [--live] [--coverage]
    
Options:
    --unit          Run unit tests only
    --integration   Run integration tests only
    --mock          Run mock tests only
    --paper         Run paper trading tests
    --live          Run live trading tests (requires confirmation)
    --coverage      Generate test coverage report
    
By default (no options), all unit and integration tests will be run in mock mode.

Note on package structure:
    The project follows a standard Python package structure, allowing tests to directly import modules
    from the app package without path manipulation. All test files can import modules as:
    
    from app.services.trading_service import TradingService
    
    NO sys.path manipulation is required in test files.
"""

import os
import sys
import argparse
import subprocess
import unittest
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestRunner")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run automated trading tests')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--mock', action='store_true', help='Run mock tests only')
    parser.add_argument('--paper', action='store_true', help='Run paper trading tests')
    parser.add_argument('--live', action='store_true', help='Run live trading tests')
    parser.add_argument('--coverage', action='store_true', help='Generate test coverage report')
    return parser.parse_args()

def print_header(title):
    """Print a section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def run_unittest_suite(test_dir, pattern="test_*.py", verbosity=2):
    """
    Run a unittest discovery suite.
    
    Args:
        test_dir (str): Directory containing tests to run
        pattern (str): Pattern to match test files (default: "test_*.py")
        verbosity (int): Verbosity level for test output (default: 2)
        
    Returns:
        unittest.TestResult: Result of the test run
    """
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=pattern)
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)

def run_unit_tests(with_coverage=False):
    """
    Run unit tests.

    Args:
        with_coverage (bool): Whether to generate coverage reports (default: False)
    
    Returns:
        bool: True if tests were successful, False otherwise
    """
    print_header("RUNNING UNIT TESTS")
    os.environ["TRADING_MODE"] = "MOCK"
    
    # Check for PyAudio availability and warn if not present
    try:
        import pyaudio
        pyaudio_available = True
    except ImportError:
        pyaudio_available = False
        logger.warning("PyAudio not found - voice command tests will be skipped")
        logger.warning("To install PyAudio, see instructions in requirements-optional.txt")
    
    if with_coverage:
        cmd = [
            "pytest", 
            "tests/unit/", 
            "-v", 
            "--cov=app", 
            "--cov-report=term", 
            "--cov-report=html:coverage_reports/unit/"
        ]
        return subprocess.call(cmd) == 0
    else:
        result = run_unittest_suite("tests/unit/")
        # Consider skipped tests due to dependencies as a success
        if not result.wasSuccessful() and len(result.errors) == 0 and len(result.failures) == 0:
            logger.info("Tests were skipped but no failures occurred")
            return True
        return result.wasSuccessful()

def run_integration_tests(with_coverage=False):
    """
    Run integration tests.
    
    Args:
        with_coverage (bool): Whether to generate coverage reports (default: False)
    
    Returns:
        bool: True if tests were successful, False otherwise
    """
    print_header("RUNNING INTEGRATION TESTS")
    os.environ["TRADING_MODE"] = "MOCK"
    
    if with_coverage:
        cmd = [
            "pytest", 
            "tests/integration/", 
            "-v", 
            "--cov=app", 
            "--cov-report=term", 
            "--cov-report=html:coverage_reports/integration/"
        ]
        return subprocess.call(cmd) == 0
    else:
        return run_unittest_suite("tests/integration/").wasSuccessful()

def run_mock_tests():
    """
    Run mock tests using the dedicated runner.
    
    Returns:
        bool: True if tests were successful, False otherwise
    """
    print_header("RUNNING MOCK TESTS")
    
    try:
        # Use the existing mock test runner
        mock_runner = __import__("run_mock_tests")
        return mock_runner.run_tests() if hasattr(mock_runner, "run_tests") else False
    except (ImportError, AttributeError):
        logger.error("Failed to import run_mock_tests.py or missing run_tests function")
        return False

def run_paper_tests():
    """
    Run paper trading tests using the dedicated runner.
    
    Returns:
        bool: True if tests were successful, False otherwise
    """
    print_header("RUNNING PAPER TRADING TESTS")
    
    # Check for API credentials
    if not os.environ.get("SCHWAB_API_KEY") or not os.environ.get("SCHWAB_API_SECRET"):
        logger.error("API credentials not found in environment")
        logger.error("Please set SCHWAB_API_KEY and SCHWAB_API_SECRET environment variables")
        return False
    
    try:
        # Use the existing paper test runner
        paper_runner = __import__("run_paper_tests")
        return paper_runner.run_tests() if hasattr(paper_runner, "run_tests") else False
    except (ImportError, AttributeError):
        logger.error("Failed to import run_paper_tests.py or missing run_tests function")
        return False

def run_live_tests():
    """
    Run live trading tests with confirmation.
    
    Returns:
        bool: True if tests were successful, False otherwise
    """
    print_header("⚠️ RUNNING LIVE TRADING TESTS ⚠️")
    
    # Check for API credentials
    if not os.environ.get("SCHWAB_API_KEY") or not os.environ.get("SCHWAB_API_SECRET"):
        logger.error("API credentials not found in environment")
        logger.error("Please set SCHWAB_API_KEY and SCHWAB_API_SECRET environment variables")
        return False
    
    # Confirm with user
    print("\n⚠️ WARNING: This will use REAL MONEY to place ACTUAL ORDERS ⚠️")
    print("Only proceed if you understand the risks.")
    confirmation = input("\nType 'YES I UNDERSTAND THE RISKS' to continue: ")
    
    if confirmation != "YES I UNDERSTAND THE RISKS":
        print("Live tests aborted by user")
        return False
    
    try:
        # Use the existing live test runner
        live_runner = __import__("run_live_tests")
        return live_runner.run_tests() if hasattr(live_runner, "run_tests") else False
    except (ImportError, AttributeError):
        logger.error("Failed to import run_live_tests.py or missing run_tests function")
        return False

def main():
    """Main entry point."""
    args = parse_arguments()
    start_time = datetime.now()
    success = True
    
    # Create coverage report directory if needed
    if args.coverage:
        os.makedirs("coverage_reports", exist_ok=True)
        os.makedirs("coverage_reports/unit", exist_ok=True)
        os.makedirs("coverage_reports/integration", exist_ok=True)
    
    # Determine which tests to run based on arguments
    if not any([args.unit, args.integration, args.mock, args.paper, args.live]):
        # Default: run unit and integration tests
        success = run_unit_tests(args.coverage) and success
        success = run_integration_tests(args.coverage) and success
    else:
        # Run specific test types
        if args.unit:
            success = run_unit_tests(args.coverage) and success
        if args.integration:
            success = run_integration_tests(args.coverage) and success
        if args.mock:
            success = run_mock_tests() and success
        if args.paper:
            success = run_paper_tests() and success
        if args.live:
            success = run_live_tests() and success
    
    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {'SUCCESS' if success else 'FAILURE'}")
    print("="*60)
    print(f"Started at:  {start_time}")
    print(f"Finished at: {end_time}")
    print(f"Duration:    {duration}")
    print("="*60)
    
    if args.coverage:
        print("\nCoverage reports generated in coverage_reports/")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 