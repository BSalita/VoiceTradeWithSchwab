"""
Text Command Handler - Handles text-based commands for the trading system
"""

import logging
from typing import Dict, Any, Optional
from .command_processor import CommandProcessor
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter

logger = logging.getLogger(__name__)

class TextCommandHandler:
    """
    Handles text-based commands for the trading system
    """
    
    def __init__(self):
        """Initialize the text command handler"""
        self.command_processor = CommandProcessor()
        self.command_history = InMemoryHistory()
        
        # Create auto-completer with common commands
        self.command_completer = WordCompleter([
            'buy', 'sell', 'ladder strategy', 'cancel order', 'cancel ladder',
            'status', 'help',
            'buy AAPL 10 shares at market',
            'sell MSFT 5 shares at limit 350',
            'ladder strategy for TSLA 5 shares from 800 to 850 step 10'
        ], ignore_case=True)
        
        # Create the prompt session
        self.session = PromptSession(
            history=self.command_history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.command_completer
        )
        
        logger.info("Text command handler initialized")
    
    def start_interactive_session(self) -> None:
        """
        Start an interactive command session
        """
        print("\nWelcome to the Automated Trading System")
        print("Type 'help' for available commands or 'exit' to quit\n")
        
        while True:
            try:
                # Get user input
                command = self.session.prompt("Command> ")
                
                # Check for exit command
                if command.lower() in ['exit', 'quit']:
                    print("Exiting command session...")
                    break
                
                # Process the command
                if command.strip():
                    result = self.process_command(command)
                    self._display_result(result)
                
            except KeyboardInterrupt:
                print("\nSession interrupted. Type 'exit' to quit.")
            except EOFError:
                print("\nExiting command session...")
                break
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a text command
        
        Args:
            command (str): Command text
            
        Returns:
            Dict[str, Any]: Command result
        """
        logger.info(f"Processing text command: {command}")
        return self.command_processor.process_command(command)
    
    def _display_result(self, result: Dict[str, Any]) -> None:
        """
        Display the result of a command
        
        Args:
            result (Dict[str, Any]): Command result
        """
        success = result.get('success', False)
        
        if success:
            print("\n✅ Command executed successfully")
            
            # Display specific information based on command type
            if 'order' in result:
                order_id = result.get('order', {}).get('orderId', 'Unknown')
                symbol = result.get('symbol', '')
                quantity = result.get('quantity', 0)
                side = result.get('side', '')
                price = result.get('price', 'Market')
                
                print(f"Order: {side} {quantity} shares of {symbol}")
                print(f"Order ID: {order_id}")
                print(f"Price: {price if price else 'Market'}")
                
            elif 'ladder_id' in result:
                ladder_id = result.get('ladder_id', '')
                symbol = result.get('symbol', '')
                quantity = result.get('quantity', 0)
                side = result.get('side', '')
                steps = result.get('steps', 0)
                orders_placed = result.get('orders_placed', 0)
                
                print(f"Ladder: {side} {quantity} shares of {symbol} in {steps} steps")
                print(f"Ladder ID: {ladder_id}")
                print(f"Orders placed: {orders_placed}/{steps}")
                
            elif 'help_text' in result:
                print(result.get('help_text', ''))
                
            elif 'account' in result:
                print("Account Status:")
                
                # Show positions if available
                positions = result.get('positions', [])
                if positions:
                    print("\nCurrent Positions:")
                    for pos in positions:
                        symbol = pos.get('symbol', '')
                        quantity = pos.get('quantity', 0)
                        current_price = pos.get('marketValue', 0) / pos.get('quantity', 1) if pos.get('quantity', 0) > 0 else 0
                        print(f"  {symbol}: {quantity} shares @ ${current_price:.2f}")
                
                # Show balances if available
                balances = result.get('balances', {})
                if balances:
                    print("\nAccount Balances:")
                    cash = balances.get('cashBalance', 0)
                    buying_power = balances.get('buyingPower', 0)
                    print(f"  Cash: ${cash:.2f}")
                    print(f"  Buying Power: ${buying_power:.2f}")
                
                # Show active ladders if available
                active_ladders = result.get('active_ladders', {})
                if active_ladders:
                    print("\nActive Ladder Strategies:")
                    for ladder_id, ladder in active_ladders.items():
                        symbol = ladder.get('symbol', '')
                        side = ladder.get('side', '')
                        steps = len(ladder.get('orders', []))
                        print(f"  {ladder_id}: {side} {symbol} with {steps} steps")
        else:
            print("\n❌ Command failed")
            error = result.get('error', 'Unknown error')
            print(f"Error: {error}")
            
            # Show help if available
            if 'help' in result:
                print("\nAvailable Commands:")
                print(result.get('help', '')) 