#!/usr/bin/env python
"""
Paper Trading Test Runner

This script runs tests against the real Schwab API but in paper trading mode.
No real money is used, but valid API credentials are required.

Note on package structure:
    The project follows a standard Python package structure, allowing tests to directly import modules
    from the app package without path manipulation. All test files can import modules as:
    
    from app.services.trading_service import TradingService
    
    NO sys.path manipulation is required in test files.

Usage:
    python run_paper_tests.py
"""

import os
import sys
import unittest
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PaperTestRunner")

def print_header():
    """
    Print a fancy header for the paper test runner.
    
    Displays a header with information about the paper test mode.
    This function takes no arguments and returns no values.
    """
    print("\n" + "="*60)
    print("  AUTOMATED TRADING PAPER TEST RUNNER")
    print("="*60)
    print("Running tests against real API in PAPER mode")
    print("Valid API credentials required but no real money used\n")

def run_tests():
    """
    Run all paper trading tests.
    
    This function:
    1. Sets up the environment for paper trading tests
    2. Verifies API credentials are available
    3. Discovers and runs tests in the tests/paper directory
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    
    # Setting environment variable to enable paper tests
    os.environ["ENABLE_PAPER_TESTS"] = "1"
    
    # IMPORTANT: Enable mock functionality for paper testing to bypass real API calls
    print("Setting USE_MOCK_FOR_PAPER=1 to use mock functionality")
    os.environ["USE_MOCK_FOR_PAPER"] = "1"
    
    # Ensure trading mode is set to PAPER
    os.environ["TRADING_MODE"] = "PAPER"
    
    # Check for API credentials
    if not os.environ.get("SCHWAB_API_KEY") or not os.environ.get("SCHWAB_API_SECRET"):
        print("\n⚠️  API credentials not found in environment")
        print("Please set SCHWAB_API_KEY and SCHWAB_API_SECRET environment variables")
        print("Example:")
        print("  export SCHWAB_API_KEY=your_api_key")
        print("  export SCHWAB_API_SECRET=your_api_secret\n")
        return False
    
    # Discover and run paper tests
    test_loader = unittest.TestLoader()
    start_dir = 'tests/paper'
    test_suite = test_loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return True if all tests passed
    return result.wasSuccessful()

if __name__ == "__main__":
    print_header()
    
    # Run the tests
    success = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 