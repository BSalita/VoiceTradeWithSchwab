"""
Text Command Handler - Processes text commands for the trading system using services
"""

import logging
import sys
import cmd
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ...services import get_service, ServiceRegistry
from ...commands.command_processor import CommandProcessor
import os

logger = logging.getLogger(__name__)
console = Console()

class TextCommandHandler(cmd.Cmd):
    """
    Command-line interface for processing text commands
    """
    
    intro = "Automated Trading System CLI. Type 'help' for commands, 'exit' to quit."
    prompt = "Trading> "
    
    def __init__(self):
        """Initialize the text command handler"""
        super().__init__()
        self.command_processor = CommandProcessor()
        
        # Initialize services if not already done
        try:
            trading_service = get_service("trading")
            if trading_service is None:
                ServiceRegistry.initialize_services()
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            
        logger.info("Text command handler initialized")
    
    def start_interactive_session(self) -> None:
        """Start the interactive command session"""
        console.print("[bold]Starting interactive trading session...[/bold]")
        console.print("Type [bold]help[/bold] for available commands, [bold]exit[/bold] to quit.")
        console.print()
        
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            console.print("\n[bold]Session terminated by user[/bold]")
        except Exception as e:
            logger.exception("Error in interactive session")
            console.print(f"[red]Error: {str(e)}[/red]")
    
    def process_command_file(self, filename: str) -> None:
        """
        Process commands from a file
        
        Args:
            filename: Path to the file containing commands
        """
        try:
            # Check if file exists
            if not os.path.exists(filename):
                console.print(f"[red]Error: File '{filename}' not found[/red]")
                return
                
            # Check file size to avoid memory issues
            file_size = os.path.getsize(filename)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                console.print(f"[red]Error: File '{filename}' is too large (max 10MB)[/red]")
                return
                
            # Read commands from file
            console.print(f"[bold]Reading commands from {filename}...[/bold]")
            with open(filename, 'r') as file:
                commands = file.readlines()
                
            # Process each command
            total_commands = len(commands)
            successful_commands = 0
            failed_commands = 0
            skipped_commands = 0
            
            console.print(f"[bold]Found {total_commands} commands to process[/bold]")
            console.print()
            
            for i, command in enumerate(commands, 1):
                # Skip empty lines and comments
                command = command.strip()
                if not command or command.startswith('#'):
                    skipped_commands += 1
                    continue
                
                # Handle continuation lines (lines ending with \)
                while command.endswith('\\') and i < len(commands):
                    command = command[:-1].strip() + ' ' + commands[i].strip()
                    i += 1
                    
                # Display the command being processed
                console.print(f"[bold blue]Command {i}/{total_commands}:[/bold blue] {command}")
                
                try:
                    # Process the command
                    result = self.command_processor.process_command(command)
                    self._display_result(result)
                    
                    # Track success/failure
                    if result.get('success', False):
                        successful_commands += 1
                    else:
                        failed_commands += 1
                except ValueError as e:
                    # Handle parsing errors
                    console.print(f"[red]Error parsing command at line {i}: {str(e)}[/red]")
                    failed_commands += 1
                except Exception as e:
                    # Handle other errors
                    console.print(f"[red]Error executing command at line {i}: {str(e)}[/red]")
                    failed_commands += 1
                    
                console.print()
                
            # Display summary
            console.print("[bold]Command Processing Summary:[/bold]")
            console.print(f"Total lines: {total_commands}")
            console.print(f"[cyan]Skipped: {skipped_commands}[/cyan] (comments and empty lines)")
            console.print(f"[green]Successful: {successful_commands}[/green]")
            console.print(f"[red]Failed: {failed_commands}[/red]")
            
            # Provide a recommendation if there were failures
            if failed_commands > 0:
                console.print()
                console.print("[yellow]Tip: Check the command syntax for failed commands.[/yellow]")
                console.print("[yellow]Use 'help <command>' for syntax help.[/yellow]")
            
        except UnicodeDecodeError:
            logger.exception(f"Error reading file: {filename}")
            console.print(f"[red]Error: File '{filename}' is not a valid text file[/red]")
        except PermissionError:
            logger.exception(f"Permission error reading file: {filename}")
            console.print(f"[red]Error: You don't have permission to read '{filename}'[/red]")
        except Exception as e:
            logger.exception(f"Error processing command file: {filename}")
            console.print(f"[red]Error processing command file: {str(e)}[/red]")
    
    def handle_command(self, command: str) -> Dict[str, Any]:
        """
        Process a single command and return the result
        
        Args:
            command (str): Command to process
            
        Returns:
            Dict[str, Any]: Result of the command processing
        """
        logger.info(f"Processing command: {command}")
        
        # Strip whitespace and handle empty commands
        command = command.strip()
        if not command:
            return {"success": False, "message": "Empty command"}
            
        try:
            # Process via command processor
            result = self.command_processor.process_command(command)
            self._display_result(result)
            return result
        except Exception as e:
            logger.exception(f"Error processing command: {command}")
            error_result = {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e),
                "command": command
            }
            self._display_result(error_result)
            return error_result
    
    def default(self, line: str) -> bool:
        """Handle commands that don't match a specific method"""
        if line.lower() in ('exit', 'quit', 'bye'):
            return self.do_exit(line)
            
        # Process the command
        result = self.command_processor.process_command(line)
        self._display_result(result)
        return False  # Don't exit
    
    def emptyline(self) -> bool:
        """Do nothing on empty line"""
        return False  # Don't exit
    
    def do_exit(self, arg: str) -> bool:
        """Exit the CLI"""
        console.print("[bold]Exiting trading session...[/bold]")
        return True  # Signal to exit
        
    def help_exit(self) -> None:
        """Help for exit command"""
        console.print("Exit the trading session")
        
    def help_buy(self) -> None:
        """Help for buy command"""
        console.print("[bold]Buy Command:[/bold] Purchase shares of a stock")
        console.print("\n[italic]Format:[/italic]")
        console.print("  buy <quantity> shares of <symbol>")
        console.print("  buy <quantity> shares of <symbol> at $<price>")
        console.print("\n[italic]Examples:[/italic]")
        console.print("  buy 10 shares of AAPL            (Market order)")
        console.print("  buy 5 shares of MSFT at $300.50  (Limit order)")
        console.print("\n[italic]Notes:[/italic]")
        console.print("  - Market orders execute immediately at current market price")
        console.print("  - Limit orders execute only when the stock reaches your specified price")
        
    def help_sell(self) -> None:
        """Help for sell command"""
        console.print("[bold]Sell Command:[/bold] Sell shares of a stock")
        console.print("\n[italic]Format:[/italic]")
        console.print("  sell <quantity> shares of <symbol>")
        console.print("  sell <quantity> shares of <symbol> at $<price>")
        console.print("\n[italic]Examples:[/italic]")
        console.print("  sell 10 shares of AAPL            (Market order)")
        console.print("  sell 5 shares of MSFT at $300.50  (Limit order)")
        console.print("\n[italic]Notes:[/italic]")
        console.print("  - Market orders execute immediately at current market price")
        console.print("  - Limit orders execute only when the stock reaches your specified price")
        console.print("  - You must own the shares you are trying to sell")
        
    def help_quote(self) -> None:
        """Help for quote command"""
        console.print("[bold]Quote Command:[/bold] Get current price of a stock")
        console.print("\n[italic]Format:[/italic]")
        console.print("  what is the price of <symbol>")
        console.print("  what is the current price of <symbol>")
        console.print("\n[italic]Examples:[/italic]")
        console.print("  what is the price of AAPL")
        console.print("  what is the current price of MSFT")
        console.print("\n[italic]Notes:[/italic]")
        console.print("  - Returns real-time or slightly delayed quotes depending on your data feed")
        console.print("  - Shows bid, ask, and last price when available")
        
    def help_status(self) -> None:
        """Display help information for the status command"""
        console.print("[bold]STATUS[/bold] - Shows the current status of your trading account")
        console.print()
        console.print("[bold]Usage:[/bold] status")
        console.print()
        console.print("[bold]Description:[/bold]")
        console.print("  The status command displays information about your current account status including:")
        console.print("  - Connection status to broker")
        console.print("  - Account balances and buying power")
        console.print("  - Current positions")
        console.print("  - Open orders")
        console.print("  - Trading mode (LIVE/MOCK/PAPER)")
        console.print()
        console.print("[bold]Example:[/bold]")
        console.print("  Trading> status")
        
    def help_strategies(self) -> None:
        """Display help information for the strategies command"""
        console.print("[bold]STRATEGIES[/bold] - List or manage trading strategies")
        console.print()
        console.print("[bold]Usage:[/bold]")
        console.print("  strategies list                - Show available strategies")
        console.print("  strategies info <name>         - Show details about a specific strategy")
        console.print("  strategies start <name> <args> - Start a strategy with arguments")
        console.print("  strategies stop <name>         - Stop a running strategy")
        console.print("  strategies status              - Show status of all running strategies")
        console.print()
        console.print("[bold]Description:[/bold]")
        console.print("  The strategies command helps you manage automated trading strategies.")
        console.print("  Different strategies have different parameters and behaviors.")
        console.print("  Common strategy types include:")
        console.print("  - BasicStrategy: Simple buy/sell execution")
        console.print("  - LadderStrategy: Places orders at multiple price points")
        console.print("  - OscillatingStrategy: Trades based on price oscillations")
        console.print("  - HighLowStrategy: Trades based on daily high/low points")
        console.print()
        console.print("[bold]Examples:[/bold]")
        console.print("  Trading> strategies list")
        console.print("  Trading> strategies start LadderStrategy AAPL BUY 150 170 5 10")
        
    def help_history(self) -> None:
        """Display help information for the history command"""
        console.print("[bold]HISTORY[/bold] - View your trading history")
        console.print()
        console.print("[bold]Usage:[/bold]")
        console.print("  history                     - Show recent trades (last 30 days)")
        console.print("  history <symbol>            - Show trades for a specific symbol")
        console.print("  history days <n>            - Show trades from the last n days")
        console.print("  history <buy|sell>          - Filter by buy or sell trades")
        console.print()
        console.print("[bold]Description:[/bold]")
        console.print("  The history command displays your past trades with details including:")
        console.print("  - Date and time of execution")
        console.print("  - Symbol, quantity, and price")
        console.print("  - Order type and side")
        console.print("  - Strategy used (if applicable)")
        console.print("  - Total value of the trade")
        console.print("  - By default shows transactions from the last 30 days")
        console.print()
        console.print("[bold]Examples:[/bold]")
        console.print("  Trading> history")
        console.print("  Trading> history AAPL")
        console.print("  Trading> history days 7")
        console.print("  Trading> history buy")
        
    def help_export(self) -> None:
        """Help for export command"""
        console.print("[bold]Export Command:[/bold] Export trading history to a file")
        console.print("\n[italic]Format:[/italic]")
        console.print("  export history to <filename>")
        console.print("\n[italic]Examples:[/italic]")
        console.print("  export history to trades.csv")
        console.print("\n[italic]Notes:[/italic]")
        console.print("  - Exports in CSV format by default")
        console.print("  - File will be created in the current directory if path not specified")
        
    def help_cancel(self) -> None:
        """Help for cancel command"""
        console.print("[bold]Cancel Command:[/bold] Cancel open orders")
        console.print("\n[italic]Format:[/italic]")
        console.print("  cancel order <order_id>")
        console.print("  cancel all orders")
        console.print("  cancel all orders for <symbol>")
        console.print("\n[italic]Examples:[/italic]")
        console.print("  cancel order 12345")
        console.print("  cancel all orders")
        console.print("  cancel all orders for AAPL")
        console.print("\n[italic]Notes:[/italic]")
        console.print("  - Only open orders can be cancelled")
        console.print("  - Market orders may execute too quickly to be cancelled")
        
    def help_help(self) -> None:
        """Enhanced help command"""
        console.print("[bold]Available Commands:[/bold]")
        console.print()
        console.print("  [bold]Trading Commands:[/bold]")
        console.print("  - buy          Purchase shares of a stock")
        console.print("  - sell         Sell shares of a stock")
        console.print("  - quote        Get current price of a stock")
        console.print()
        console.print("  [bold]Account Commands:[/bold]")
        console.print("  - status       Check account status and positions")
        console.print("  - orders       View open orders")
        console.print("  - history      View trade history")
        console.print("  - export       Export trade history to file")
        console.print("  - cancel       Cancel open orders")
        console.print()
        console.print("  [bold]Strategy Commands:[/bold]")
        console.print("  - strategies   List active trading strategies")
        console.print()
        console.print("  [bold]System Commands:[/bold]")
        console.print("  - help         Show this help message")
        console.print("  - exit         Exit the application")
        console.print()
        console.print("[italic]For detailed help on a specific command, type:[/italic] help <command>")

    def _display_result(self, result: Dict[str, Any]) -> None:
        """
        Display the result of a command
        
        Args:
            result: Command result
        """
        console.print()
        
        success = result.get('success', False)
        
        if success:
            # Handle specific result types
            
            # Order result
            if 'order' in result:
                symbol = result.get('symbol', '')
                quantity = result.get('quantity', 0)
                side = result.get('side', '')
                price = result.get('price', 'market price')
                
                content = f"{side} order for {quantity} shares of {symbol} at {price}"
                panel = Panel(content, title="Order Placed", style="green")
                console.print(panel)
                
            # Quote result
            elif 'quote' in result:
                symbol = result.get('symbol', '')
                quote = result.get('quote', {})
                
                if quote:
                    table = Table(title=f"Quote for {symbol}")
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="green")
                    
                    for key, value in quote.items():
                        table.add_row(key, str(value))
                        
                    console.print(table)
                else:
                    console.print(f"[green]Quote retrieved for {symbol}[/green]")
            
            # Status result
            elif 'account' in result:
                account = result.get('account', {})
                positions = result.get('positions', [])
                balances = result.get('balances', {})
                
                # Display account info
                console.print("[bold]Account Information[/bold]")
                for key, value in account.items():
                    console.print(f"{key}: {value}")
                
                # Display positions in a table
                if positions:
                    table = Table(title="Positions")
                    table.add_column("Symbol", style="cyan")
                    table.add_column("Quantity", style="green")
                    table.add_column("Cost Basis", style="yellow")
                    table.add_column("Current Value", style="yellow")
                    table.add_column("P/L", style="green")
                    
                    for position in positions:
                        symbol = position.get('symbol', '')
                        quantity = position.get('quantity', 0)
                        cost_basis = position.get('costBasis', 0)
                        current_value = position.get('currentValue', 0)
                        pnl = position.get('unrealizedPnL', 0)
                        
                        table.add_row(
                            symbol,
                            str(quantity),
                            f"${cost_basis:.2f}",
                            f"${current_value:.2f}",
                            f"${pnl:.2f}"
                        )
                        
                    console.print(table)
                else:
                    console.print("[yellow]No open positions[/yellow]")
                    
                # Display balances
                console.print("[bold]Account Balances[/bold]")
                for key, value in balances.items():
                    console.print(f"{key}: ${value:.2f}")
                    
            # Trade history result
            elif 'trades' in result:
                trades = result.get('trades', [])
                count = result.get('count', 0)
                filters = result.get('filters', {})
                
                # Display filter information
                filter_info = []
                if filters.get('symbol'):
                    filter_info.append(f"Symbol: {filters['symbol']}")
                if filters.get('limit'):
                    filter_info.append(f"Limit: {filters['limit']}")
                if filters.get('strategy'):
                    filter_info.append(f"Strategy: {filters['strategy']}")
                    
                filter_str = ", ".join(filter_info) if filter_info else "No filters applied"
                
                if trades:
                    table = Table(title=f"Trade History ({count} trades, {filter_str})")
                    table.add_column("Date/Time", style="cyan")
                    table.add_column("Symbol", style="cyan")
                    table.add_column("Side", style="green")
                    table.add_column("Quantity", style="yellow")
                    table.add_column("Price", style="yellow")
                    table.add_column("Strategy", style="magenta")
                    
                    for trade in trades:
                        date_time = trade.get('dateTime', '')
                        symbol = trade.get('symbol', '')
                        side = trade.get('side', '')
                        quantity = trade.get('quantity', 0)
                        price = trade.get('price', 0)
                        strategy = trade.get('strategy', 'unknown')
                        
                        table.add_row(
                            date_time,
                            symbol,
                            side,
                            str(quantity),
                            f"${price:.2f}",
                            strategy
                        )
                        
                    console.print(table)
                else:
                    console.print("[yellow]No trades found[/yellow]")
                    
            # Export result
            elif 'filename' in result:
                filename = result.get('filename', '')
                message = result.get('message', '')
                
                panel = Panel(message, title="Export Complete", style="green")
                console.print(panel)
                
            # Strategy result
            elif 'strategy_key' in result or 'strategies' in result:
                if 'strategy_key' in result:
                    # Single strategy result
                    strategy_key = result.get('strategy_key', '')
                    status = result.get('status', {})
                    
                    table = Table(title=f"Strategy Status: {strategy_key}")
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="green")
                    
                    for key, value in status.items():
                        table.add_row(key, str(value))
                        
                    console.print(table)
                    
                else:
                    # Multiple strategies result
                    strategies = result.get('strategies', [])
                    count = result.get('count', 0)
                    
                    if strategies:
                        table = Table(title=f"Active Strategies ({count})")
                        table.add_column("Key", style="cyan")
                        table.add_column("Type", style="yellow")
                        table.add_column("Symbol", style="green")
                        table.add_column("Status", style="magenta")
                        
                        for strategy in strategies:
                            key = strategy.get('strategy_key', '')
                            type_name = strategy.get('strategy_type', '')
                            status = strategy.get('status', {})
                            symbol = status.get('symbol', '')
                            is_running = status.get('is_running', False)
                            status_text = "Running" if is_running else "Stopped"
                            
                            table.add_row(
                                key,
                                type_name,
                                symbol,
                                status_text
                            )
                            
                        console.print(table)
                    else:
                        console.print("[yellow]No active strategies[/yellow]")
                        
            # Help result
            elif 'help_text' in result:
                help_text = result.get('help_text', '')
                panel = Panel(help_text, title="Available Commands", style="cyan")
                console.print(panel)
                
            # Generic success
            else:
                message = result.get('message', 'Command executed successfully')
                console.print(f"[green]✓ {message}[/green]")
                
        else:
            # Error result
            error = result.get('error', 'Unknown error')
            console.print(f"[red]✗ Error: {error}[/red]")
            
            # Show help if available
            if 'help' in result:
                console.print("\n[bold]Available Commands:[/bold]")
                console.print(result.get('help', '')) 