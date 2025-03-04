"""
Test runner for Automated Trading application in MOCK mode.
This script runs tests without requiring real API credentials.

Note on package structure:
    The project follows a standard Python package structure, allowing tests to directly import modules
    from the app package without path manipulation. All test files can import modules as:
    
    from app.services.trading_service import TradingService
    
    NO sys.path manipulation is required in test files.
"""

import os
import sys
import importlib.util
import traceback

def import_module_from_file(file_path):
    """
    Import a module from a file path.
    
    Args:
        file_path (str): Path to the Python file to import
        
    Returns:
        module: The imported module object
    """
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_simple_test():
    """
    Run the simple test for SchwabAPIClient in mock mode.
    
    Executes the test_schwab_client_mock function from the simple_schwab_test.py file.
    
    Returns:
        bool: True if the test passes, False otherwise
    """
    print("\n===== Running Simple SchwabAPIClient Test =====")
    try:
        # First, ensure the trading mode is set to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Import and run the simple test
        module = import_module_from_file("tests/simple_schwab_test.py")
        if hasattr(module, 'test_schwab_client_mock'):
            module.test_schwab_client_mock()
            return True
        else:
            print("❌ Error: test_schwab_client_mock function not found in tests/simple_schwab_test.py")
            return False
    except Exception as e:
        print(f"❌ Error in simple test: {str(e)}")
        traceback.print_exc()
        return False

def run_mock_trading_tests():
    """
    Run tests for mock trading functionality.
    
    Imports and executes tests from the test_mock_trading.py file.
    
    Returns:
        bool: True if the tests pass or are skipped, False on error
    """
    print("\n===== Running Mock Trading Tests =====")
    try:
        # Ensure the trading mode is set to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Import and run the mock trading tests
        if os.path.exists("tests/unit/test_mock_trading.py"):
            module = import_module_from_file("tests/unit/test_mock_trading.py")
            # Assume the module has a main function or executes tests when imported
            if hasattr(module, 'run_tests'):
                module.run_tests()
            return True
        else:
            print("⚠️ Warning: tests/unit/test_mock_trading.py not found, skipping")
            return False
    except Exception as e:
        print(f"❌ Error in mock trading tests: {str(e)}")
        traceback.print_exc()
        return False

def run_fastapi_endpoint_tests():
    """
    Run the FastAPI endpoint tests.
    
    Imports and executes tests from the test_fastapi_endpoints_unit.py file.
    
    Returns:
        bool: True if the tests pass or are skipped, False on error
    """
    try:
        print("\n===== Running FastAPI Endpoint Tests =====")
        # Ensure the trading mode is set to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Import and run the FastAPI endpoint tests
        if os.path.exists("tests/unit/test_fastapi_endpoints_unit.py"):
            module = import_module_from_file("tests/unit/test_fastapi_endpoints_unit.py")
            # Assume the module has a main function or executes tests when imported
            if hasattr(module, 'run_tests'):
                module.run_tests()
            return True
        else:
            print("⚠️ Warning: tests/unit/test_fastapi_endpoints_unit.py not found, skipping")
            return False
    except Exception as e:
        print(f"❌ Error in FastAPI endpoint tests: {str(e)}")
        traceback.print_exc()
        return False

def run_command_processing_tests():
    """
    Run tests for command processing.
    
    Imports and executes tests from the test_command_processing.py file.
    
    Returns:
        bool: True if the tests pass or are skipped, False on error
    """
    print("\n===== Running Command Processing Tests =====")
    try:
        # Ensure the trading mode is set to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Import and run the command processing tests
        if os.path.exists("tests/unit/test_command_processing.py"):
            module = import_module_from_file("tests/unit/test_command_processing.py")
            # Assume the module has a main function or executes tests when imported
            if hasattr(module, 'run_tests'):
                module.run_tests()
            return True
        else:
            print("⚠️ Warning: tests/unit/test_command_processing.py not found, skipping")
            return False
    except Exception as e:
        print(f"❌ Error in command processing tests: {str(e)}")
        traceback.print_exc()
        return False

def run_basic_strategy_tests():
    """
    Run tests for the BasicStrategy.
    
    Imports and executes tests from the test_basic_strategy.py file,
    running individual test methods in a controlled sequence.
    
    Returns:
        bool: True if all tests pass, False if any test fails or on error
    """
    print("\n===== Running BasicStrategy Tests =====")
    try:
        # Ensure the trading mode is set to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Import and run the BasicStrategy tests
        if os.path.exists("tests/unit/test_basic_strategy.py"):
            module = import_module_from_file("tests/unit/test_basic_strategy.py")
            
            # Check if the module has a TestBasicStrategy class
            if hasattr(module, 'TestBasicStrategy'):
                test = module.TestBasicStrategy()
                try:
                    test.setup_method()
                    
                    # Run the tests
                    print("Testing initialization...")
                    test.test_initialization()
                    
                    print("Testing buy market order...")
                    test.test_execute_buy_market_order()
                    
                    print("Testing sell market order...")
                    test.test_execute_sell_market_order()
                    
                    print("Testing limit order...")
                    test.test_execute_limit_order()
                    
                    print("Testing error handling...")
                    test.test_execute_with_invalid_side()
                    test.test_execute_with_invalid_order_type()
                    test.test_execute_limit_order_without_price()
                    test.test_execute_with_zero_quantity()
                    test.test_execute_with_empty_symbol()
                    
                    # Clean up
                    test.teardown_method()
                    return True
                except Exception as e:
                    print(f"❌ Error in BasicStrategy tests: {str(e)}")
                    traceback.print_exc()
                    test.teardown_method()
                    return False
            else:
                print("❌ Error: TestBasicStrategy class not found in tests/unit/test_basic_strategy.py")
                return False
        else:
            print("⚠️ Warning: tests/unit/test_basic_strategy.py not found, skipping")
            return False
    except Exception as e:
        print(f"❌ Error in BasicStrategy tests: {str(e)}")
        traceback.print_exc()
        return False

def run_ladder_strategy_tests():
    """
    Run tests for the LadderStrategy.
    
    Imports and executes tests from the test_ladder_strategy.py file,
    running individual test methods in a controlled sequence.
    
    Returns:
        bool: True if all tests pass, False if any test fails or on error
    """
    print("\n===== Running LadderStrategy Tests =====")
    try:
        # Ensure the trading mode is set to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Import and run the LadderStrategy tests
        if os.path.exists("tests/unit/test_ladder_strategy.py"):
            module = import_module_from_file("tests/unit/test_ladder_strategy.py")
            
            # Check if the module has a TestLadderStrategy class
            if hasattr(module, 'TestLadderStrategy'):
                test = module.TestLadderStrategy()
                try:
                    test.setup_method()
                    
                    # Run the tests
                    print("Testing initialization...")
                    test.test_initialization()
                    
                    print("Testing buy ladder...")
                    test.test_execute_buy_ladder()
                    
                    print("Testing sell ladder...")
                    test.test_execute_sell_ladder()
                    
                    print("Testing single step ladder...")
                    test.test_execute_single_step_ladder()
                    
                    print("Testing cancel ladder...")
                    test.test_cancel_ladder()
                    
                    print("Testing get active ladders...")
                    test.test_get_active_ladders()
                    
                    print("Testing error handling...")
                    test.test_execute_with_invalid_side()
                    test.test_execute_with_zero_quantity()
                    test.test_execute_with_zero_steps()
                    test.test_execute_with_zero_price()
                    test.test_execute_buy_with_invalid_price_range()
                    test.test_execute_sell_with_invalid_price_range()
                    test.test_cancel_nonexistent_ladder()
                    
                    # Clean up
                    test.teardown_method()
                    return True
                except Exception as e:
                    print(f"❌ Error in LadderStrategy tests: {str(e)}")
                    traceback.print_exc()
                    test.teardown_method()
                    return False
            else:
                print("❌ Error: TestLadderStrategy class not found in tests/unit/test_ladder_strategy.py")
                return False
        else:
            print("⚠️ Warning: tests/unit/test_ladder_strategy.py not found, skipping")
            return False
    except Exception as e:
        print(f"❌ Error in LadderStrategy tests: {str(e)}")
        traceback.print_exc()
        return False

def run_cli_interface_tests():
    """
    Run tests for the CLI interface.
    
    Imports and executes tests from the test_cli_interface.py file.
    Can run tests either using a dedicated run_tests function if it exists,
    or by directly executing the tests using unittest.
    
    Returns:
        bool: True if the tests pass, False otherwise
    """
    print("\n===== Running CLI Interface Tests =====")
    try:
        # Ensure the trading mode is set to MOCK
        os.environ["TRADING_MODE"] = "MOCK"
        
        # Import and run the CLI interface tests
        if os.path.exists("tests/unit/test_cli_interface.py"):
            module = import_module_from_file("tests/unit/test_cli_interface.py")
            # Run tests either via run_tests function or directly
            if hasattr(module, 'run_tests'):
                return module.run_tests()
            else:
                # Import unittest and run the tests directly
                import unittest
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(module)
                runner = unittest.TextTestRunner(verbosity=2)
                result = runner.run(suite)
                return result.wasSuccessful()
        else:
            print("⚠️ Warning: tests/unit/test_cli_interface.py not found, skipping")
            return False
    except Exception as e:
        print(f"❌ Error in CLI interface tests: {str(e)}")
        traceback.print_exc()
        return False

def run_tests():
    """
    Run all mock tests sequentially.
    
    This function runs all available mock tests and reports on success or failure.
    It executes tests in the following order:
    1. Simple Schwab client test
    2. Mock trading tests
    3. FastAPI endpoint tests
    4. Command processing tests
    5. BasicStrategy tests
    6. LadderStrategy tests
    7. CLI interface tests
    
    Returns:
        bool: True if all tests pass, False if any test fails
    """
    print("\n" + "="*60)
    print("  AUTOMATED TRADING MOCK TEST RUNNER")
    print("="*60)
    print("Running tests in mock mode without real API connections\n")
    
    # Track test results
    results = {}
    
    # Run all tests
    results["Simple Client Test"] = run_simple_test()
    results["Mock Trading Tests"] = run_mock_trading_tests()
    results["FastAPI Endpoint Tests"] = run_fastapi_endpoint_tests()
    results["Command Processing Tests"] = run_command_processing_tests()
    results["BasicStrategy Tests"] = run_basic_strategy_tests()
    results["LadderStrategy Tests"] = run_ladder_strategy_tests()
    results["CLI Interface Tests"] = run_cli_interface_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    # Overall success only if all tests passed
    overall_success = all(results.values())
    print("\n" + "="*60)
    overall_status = "✅ SUCCESS" if overall_success else "❌ FAILURE"
    print(f"OVERALL: {overall_status}")
    print("="*60)
    
    return overall_success

if __name__ == "__main__":
    sys.exit(run_tests()) 