#!/usr/bin/env python
"""
LIVE Trading Test Runner - USE WITH EXTREME CAUTION

This script runs tests against the real Schwab API in LIVE trading mode.
Real money will be used to place actual orders in the market.

Note on package structure:
    The project follows a standard Python package structure, allowing tests to directly import modules
    from the app package without path manipulation. All test files can import modules as:
    
    from app.services.trading_service import TradingService
    
    NO sys.path manipulation is required in test files.

PREREQUISITES:
1. Valid API credentials
2. Understanding of the risks involved
3. Preferably a dedicated test account with minimal funds

Usage:
    python run_live_tests.py

WARNING: This script should only be run:
- On a dedicated test account with minimal funds
- By users who fully understand the financial implications
- In controlled environments with proper risk management
"""

import os
import sys
import unittest
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LiveTestRunner")

def print_header():
    """
    Print a warning header for the live test runner.
    
    Displays a prominent warning about running live tests with real money.
    This function takes no arguments and returns no values.
    """
    print("\n" + "="*80)
    print("  ⚠️  WARNING: AUTOMATED TRADING LIVE TEST RUNNER  ⚠️")
    print("="*80)
    print(" ")
    print("  ⚠️  THIS WILL USE REAL MONEY TO PLACE ACTUAL ORDERS  ⚠️")
    print(" ")
    print("  Tests will execute against the LIVE Schwab API")
    print("  Real funds will be used to place real orders")
    print("  Only proceed if you understand the risks")
    print("="*80)
    print(" ")

def safety_checks():
    """
    Run multiple safety checks before proceeding with live tests.
    
    Performs the following checks:
    1. Verifies API credentials are available
    2. Confirms the presence of the required confirmation environment variable
    3. Checks if we're in market hours (with warning and confirmation if not)
    4. Requires explicit user confirmation to proceed
    
    Returns:
        bool: True if all safety checks pass and user confirms, False otherwise
    """
    # Check for API credentials
    if not os.environ.get("SCHWAB_API_KEY") or not os.environ.get("SCHWAB_API_SECRET"):
        print("\n⚠️  API credentials not found in environment")
        print("Please set SCHWAB_API_KEY and SCHWAB_API_SECRET environment variables")
        return False
    
    # Check for confirmation environment variable
    if os.environ.get("CONFIRM_LIVE_TESTING") != "YES_I_UNDERSTAND_THE_RISKS":
        print("\n⚠️  Live testing confirmation not set properly")
        print("Please set the following environment variable:")
        print("  export CONFIRM_LIVE_TESTING=YES_I_UNDERSTAND_THE_RISKS")
        return False
        
    # Check if we're in market hours (optional)
    current_hour = datetime.now().hour
    current_weekday = datetime.now().weekday()
    if current_weekday >= 5 or current_hour < 9 or current_hour > 16:
        print("\n⚠️  WARNING: It appears the market may be closed")
        print("Running live tests outside market hours may cause unexpected behavior")
        proceed = input("Continue anyway? (yes/no): ")
        if proceed.lower() != "yes":
            return False
    
    # Final user confirmation
    print("\n" + "="*80)
    print("  FINAL CONFIRMATION REQUIRED")
    print("="*80)
    print("\nYou are about to run tests that will:")
    print("  - Connect to the LIVE Schwab API")
    print("  - Place REAL orders with REAL money")
    print("  - Execute actual trades in the market")
    print("\nThese tests should only be used:")
    print("  - On a dedicated test account with minimal funds")
    print("  - By users who fully understand the risks")
    print("  - In controlled environments with proper monitoring")
    print("\nThe tests are designed to minimize risk by:")
    print("  - Using minimal quantities (1 share)")
    print("  - Placing limit orders far from market price")
    print("  - Immediately canceling orders after placement")
    print("  - Setting maximum order value limits")
    print("\nHowever, REAL MONEY will still be at risk.")
    
    confirmation = input("\nType 'I ACCEPT ALL RISKS' to proceed: ")
    return confirmation == "I ACCEPT ALL RISKS"

def run_tests():
    """
    Run all live trading tests.
    
    This function:
    1. Sets up the environment for live trading tests
    2. Discovers and runs tests in the tests/live directory
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    
    # Set environment variable to enable live tests
    os.environ["ENABLE_LIVE_TESTS"] = "1"
    
    # Discover and run live tests
    test_loader = unittest.TestLoader()
    start_dir = 'tests/live'
    test_suite = test_loader.discover(start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return True if all tests passed
    return result.wasSuccessful()

if __name__ == "__main__":
    print_header()
    
    # Run safety checks
    if not safety_checks():
        print("\n⚠️  Safety checks failed. Aborting live tests.")
        sys.exit(1)
    
    # Last warning
    print("\n⚠️  PROCEEDING WITH LIVE TESTS IN 5 SECONDS...")
    print("⚠️  Press Ctrl+C now to abort")
    
    # Countdown
    for i in range(5, 0, -1):
        print(f"⚠️  {i}...")
        time.sleep(1)
    
    # Run the tests
    success = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 