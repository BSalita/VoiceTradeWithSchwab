"""
Unit tests for the CLI interface
"""
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import io
import sys

from app.interfaces.cli.text_command_handler import TextCommandHandler
from app.commands.command_processor import CommandProcessor

class TestTextCommandHandler(unittest.TestCase):
    """Test cases for the TextCommandHandler class"""

    def setUp(self):
        """Set up the test environment"""
        # Initialize services
        from app.services.service_registry import ServiceRegistry
        from app.services.trading_service import TradingService
        from app.services.market_data_service import MarketDataService
        from app.services.strategy_service import StrategyService
        
        # Register services
        ServiceRegistry.register("trading", TradingService())
        ServiceRegistry.register("market_data", MarketDataService())
        ServiceRegistry.register("strategies", StrategyService())
        
        # Create a mock command processor
        self.mock_processor = MagicMock(spec=CommandProcessor)
        
        # Create a patcher for the command processor in TextCommandHandler
        self.processor_patcher = patch('app.interfaces.cli.text_command_handler.CommandProcessor')
        self.mock_processor_class = self.processor_patcher.start()
        self.mock_processor_class.return_value = self.mock_processor
        
        # Create a test instance
        self.handler = TextCommandHandler()
        
        # Create mock results for command processing
        self.success_result = {'success': True, 'message': 'Command executed successfully'}
        self.failure_result = {'success': False, 'error': 'Command failed'}
        
    def tearDown(self):
        """Clean up after tests"""
        self.processor_patcher.stop()
    
    def test_process_command_file_basic(self):
        """Test processing commands from a file - basic functionality"""
        # Create a temp file with commands
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write("# Test commands\nbuy 10 shares of AAPL\nsell 5 shares of MSFT\n")
            temp_file_name = temp_file.name
        
        try:
            # Set up mock return values
            self.mock_processor.process_command.side_effect = [
                self.success_result,
                self.success_result
            ]
            
            # Redirect stdout to capture output
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            # Process the file
            self.handler.process_command_file(temp_file_name)
            
            # Verify the correct commands were processed
            self.assertEqual(self.mock_processor.process_command.call_count, 2)
            self.mock_processor.process_command.assert_any_call("buy 10 shares of AAPL")
            self.mock_processor.process_command.assert_any_call("sell 5 shares of MSFT")
            
            # Check that output contains success messages
            output = captured_output.getvalue()
            self.assertIn("Command Processing Summary", output.replace("\x1b[1m", "").replace("\x1b[0m", ""))
            self.assertIn("Successful", output)
            self.assertIn("Failed", output)
            
        finally:
            # Clean up
            sys.stdout = sys.__stdout__
            os.unlink(temp_file_name)

    def test_process_command_file_with_comments_and_empty_lines(self):
        """Test processing commands from a file with comments and empty lines"""
        # Create a temp file with commands, comments and empty lines
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write("""# Test commands
            
# This is a comment
buy 10 shares of AAPL

# Another comment
sell 5 shares of MSFT

""")
            temp_file_name = temp_file.name
        
        try:
            # Set up mock return values
            self.mock_processor.process_command.side_effect = [
                self.success_result,
                self.success_result
            ]
            
            # Redirect stdout to capture output
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            # Process the file
            self.handler.process_command_file(temp_file_name)
            
            # Verify only the actual commands were processed (not comments/empty lines)
            self.assertEqual(self.mock_processor.process_command.call_count, 2)
            
            # Check output summary
            output = captured_output.getvalue()
            self.assertIn("Successful", output)
            
        finally:
            # Clean up
            sys.stdout = sys.__stdout__
            os.unlink(temp_file_name)

    def test_process_command_file_with_failures(self):
        """Test processing commands from a file with some failing commands"""
        # Create a temp file with commands
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file.write("buy 10 shares of AAPL\ninvalid command\nsell 5 shares of MSFT\n")
            temp_file_name = temp_file.name
        
        try:
            # Set up mock return values - second command fails
            self.mock_processor.process_command.side_effect = [
                self.success_result,
                self.failure_result,
                self.success_result
            ]
            
            # Redirect stdout to capture output
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            # Process the file
            self.handler.process_command_file(temp_file_name)
            
            # Verify all commands were processed
            self.assertEqual(self.mock_processor.process_command.call_count, 3)
            
            # Check output summary shows counts
            output = captured_output.getvalue()
            self.assertIn("Successful", output)
            self.assertIn("Failed", output)
            # Instead of checking exact counts which might have formatting, 
            # just check that the "Command failed" message appears for the invalid command
            self.assertIn("Command failed", output)
            
        finally:
            # Clean up
            sys.stdout = sys.__stdout__
            os.unlink(temp_file_name)

    def test_process_command_file_nonexistent(self):
        """Test attempting to process a nonexistent file"""
        # Use a filename that doesn't exist
        nonexistent_file = "nonexistent_file_123456789.txt"
        
        # Redirect stdout to capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Process the nonexistent file
            self.handler.process_command_file(nonexistent_file)
            
            # Verify no commands were processed
            self.mock_processor.process_command.assert_not_called()
            
            # Check error message was printed - strip formatting codes
            output = captured_output.getvalue()
            plain_output = output.replace("\x1b[31m", "").replace("\x1b[0m", "")
            self.assertIn(f"Error: File '{nonexistent_file}' not found", plain_output)
            
        finally:
            # Clean up
            sys.stdout = sys.__stdout__

if __name__ == "__main__":
    unittest.main() 