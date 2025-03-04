"""
Command service for processing user commands.
"""

import re
from typing import Dict, Any, List, Optional

from app.services.service_registry import ServiceRegistry


class CommandService:
    """Service for processing user commands."""
    
    def __init__(self):
        """Initialize the command service."""
        self.commands = {
            "buy": self._handle_buy,
            "sell": self._handle_sell,
            "cancel": self._handle_cancel,
            "status": self._handle_status,
            "strategy": self._handle_strategy,
            "execute": self._handle_execute,
            "help": self._handle_help
        }
    
    def process_command(self, command_text: str) -> Dict[str, Any]:
        """Process a command string and return the result."""
        # Split the command into parts
        parts = command_text.strip().split()
        if not parts:
            return {"success": False, "message": "Empty command"}
        
        # Get the command name
        command_name = parts[0].lower()
        
        # Check if the command exists
        if command_name not in self.commands:
            return {"success": False, "message": f"Unknown command: {command_name}"}
        
        # Execute the command
        try:
            return self.commands[command_name](parts[1:])
        except Exception as e:
            return {"success": False, "message": f"Error executing command: {str(e)}"}
    
    def _handle_buy(self, args: List[str]) -> Dict[str, Any]:
        """Handle the buy command."""
        # Check arguments
        if len(args) < 2:
            return {"success": False, "message": "Usage: buy <quantity> <symbol>"}
        
        # Parse arguments
        try:
            quantity = int(args[0])
            symbol = args[1].upper()
        except ValueError:
            return {"success": False, "message": "Quantity must be a number"}
        
        # Get the trading service
        trading_service = ServiceRegistry.get("trading")
        if not trading_service:
            return {"success": False, "message": "Trading service not available"}
        
        # Place the order
        result = trading_service.place_order(
            symbol=symbol,
            quantity=quantity,
            side="BUY",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY"
        )
        
        # Return the result
        return {
            "success": True,
            "message": f"Placed BUY order for {quantity} {symbol}",
            "order": result
        }
    
    def _handle_sell(self, args: List[str]) -> Dict[str, Any]:
        """Handle the sell command."""
        # Check arguments
        if len(args) < 2:
            return {"success": False, "message": "Usage: sell <quantity> <symbol>"}
        
        # Parse arguments
        try:
            quantity = int(args[0])
            symbol = args[1].upper()
        except ValueError:
            return {"success": False, "message": "Quantity must be a number"}
        
        # Get the trading service
        trading_service = ServiceRegistry.get("trading")
        if not trading_service:
            return {"success": False, "message": "Trading service not available"}
        
        # Place the order
        result = trading_service.place_order(
            symbol=symbol,
            quantity=quantity,
            side="SELL",
            order_type="MARKET",
            price=None,
            session="REGULAR",
            duration="DAY"
        )
        
        # Return the result
        return {
            "success": True,
            "message": f"Placed SELL order for {quantity} {symbol}",
            "order": result
        }
    
    def _handle_cancel(self, args: List[str]) -> Dict[str, Any]:
        """Handle the cancel command."""
        # Check arguments
        if len(args) < 1:
            return {"success": False, "message": "Usage: cancel <order_id>"}
        
        # Parse arguments
        order_id = args[0]
        
        # Get the trading service
        trading_service = ServiceRegistry.get("trading")
        if not trading_service:
            return {"success": False, "message": "Trading service not available"}
        
        # Cancel the order
        result = trading_service.cancel_order(order_id)
        
        # Return the result
        return {
            "success": True,
            "message": f"Cancelled order {order_id}",
            "result": result
        }
    
    def _handle_status(self, args: List[str]) -> Dict[str, Any]:
        """Handle the status command."""
        # Get the trading service
        trading_service = ServiceRegistry.get("trading")
        if not trading_service:
            return {"success": False, "message": "Trading service not available"}
        
        # Get orders
        status = args[0] if args else None
        orders = trading_service.get_orders(status=status)
        
        # Return the result
        return {
            "success": True,
            "message": f"Found {len(orders)} orders",
            "orders": orders
        }
    
    def _handle_strategy(self, args: List[str]) -> Dict[str, Any]:
        """Handle the strategy command."""
        # Check arguments
        if len(args) < 2:
            return {"success": False, "message": "Usage: strategy <type> <symbol> [parameters...]"}
        
        # Parse arguments
        strategy_type = args[0].lower()
        symbol = args[1].upper()
        
        # Get the strategy service
        strategy_service = ServiceRegistry.get("strategy")
        if not strategy_service:
            return {"success": False, "message": "Strategy service not available"}
        
        # Create parameters based on strategy type
        parameters = {"symbol": symbol}
        
        if strategy_type == "highlow":
            # Check arguments for highlow strategy
            if len(args) < 5:
                return {"success": False, "message": "Usage: strategy highlow <symbol> <quantity> <low_threshold> <high_threshold>"}
            
            try:
                parameters["quantity"] = int(args[2])
                parameters["low_threshold"] = float(args[3])
                parameters["high_threshold"] = float(args[4])
            except ValueError:
                return {"success": False, "message": "Invalid parameters for highlow strategy"}
        
        # Create the strategy
        strategy_name = f"{strategy_type}_{symbol}"
        result = strategy_service.create_strategy(
            name=strategy_name,
            strategy_type=strategy_type,
            parameters=parameters
        )
        
        # Return the result
        return {
            "success": True,
            "message": f"Created {strategy_type} strategy for {symbol}",
            "strategy": strategy_name
        }
    
    def _handle_execute(self, args: List[str]) -> Dict[str, Any]:
        """Handle the execute command."""
        # Check arguments
        if len(args) < 1:
            return {"success": False, "message": "Usage: execute <strategy_name>"}
        
        # Parse arguments
        strategy_name = args[0]
        
        # Get the strategy service
        strategy_service = ServiceRegistry.get("strategy")
        if not strategy_service:
            return {"success": False, "message": "Strategy service not available"}
        
        # Execute the strategy
        result = strategy_service.execute_strategy(strategy_name)
        
        # Return the result
        return {
            "success": True,
            "message": f"Executed strategy {strategy_name}",
            "result": result
        }
    
    def _handle_help(self, args: List[str]) -> Dict[str, Any]:
        """Handle the help command."""
        # Define help text for each command
        help_text = {
            "buy": "buy <quantity> <symbol> - Place a buy order",
            "sell": "sell <quantity> <symbol> - Place a sell order",
            "cancel": "cancel <order_id> - Cancel an order",
            "status": "status [filter] - Show order status",
            "strategy": "strategy <type> <symbol> [parameters...] - Create a trading strategy",
            "execute": "execute <strategy_name> - Execute a trading strategy",
            "help": "help - Show this help message"
        }
        
        # Return the help text
        return {
            "success": True,
            "message": "Available commands:",
            "commands": help_text
        } 