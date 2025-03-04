# Command File Feature

The Automated Trading System supports executing commands from a file, allowing you to automate sequences of trading operations.

## Usage

To execute commands from a file, use the `--file` or `-f` option:

```bash
python main.py --file sample_commands.txt
```

You can also use the mock mode with command files for testing:

```bash
python main.py --file sample_commands.txt --mock
```

## File Format

The command file is a simple text file with one command per line. Comments and empty lines are supported:

- Lines starting with `#` are treated as comments and ignored
- Empty lines are ignored
- Each non-empty, non-comment line is processed as a command
- Lines ending with `\` are treated as continuation lines and joined with the next line

## Supported Commands

The command file supports all commands available in the interactive mode:

### Trading Commands
- `buy <quantity> shares of <symbol>` - Place a market buy order
- `buy <quantity> shares of <symbol> at $<price>` - Place a limit buy order
- `sell <quantity> shares of <symbol>` - Place a market sell order
- `sell <quantity> shares of <symbol> at $<price>` - Place a limit sell order
- `cancel order <order_id>` - Cancel an existing order

### Market Data Commands
- `what is the price of <symbol>` - Get a quote for a symbol
- `get quote for <symbol>` - Get a quote for a symbol
- `show price of <symbol>` - Get a quote for a symbol

### Strategy Commands
- `create ladder strategy for <symbol> from $<start_price> to $<end_price> with <steps> steps for <quantity> shares` - Create a ladder strategy
- `strategies` - List active strategies
- `stop strategy <strategy_id>` - Stop an active strategy

### Status Commands
- `status` - Show account status including positions and orders
- `history` - Show trading history
- `export history to <filename>` - Export trading history to a file

## Example Command File

```
# Sample Trading Commands
# This file contains example commands for the Automated Trading System

# Get quotes for stocks
what is the price of AAPL
what is the price of MSFT

# Place market orders
buy 10 shares of AAPL
sell 5 shares of MSFT

# Place limit orders
buy 10 shares of AAPL at $150.00
sell 5 shares of MSFT at $350.00

# Create and use strategies
create ladder strategy for AAPL from $145.00 to $150.00 with 5 steps for 100 shares

# Check status
status
strategies

# View history
history
```

## Command Processing

When processing a command file:

1. Each command is executed sequentially
2. Results are displayed after each command
3. A summary is shown at the end with counts of successful, failed, and skipped commands
4. Processing continues even if some commands fail

## Use Cases

Command files are useful for:

- Automating routine trading operations
- Setting up initial positions
- Implementing simple trading strategies
- Testing the trading system
- Documenting trading procedures
- Running overnight or scheduled trading operations

## Security Considerations

Be careful with command files containing actual trades:

- Always review command files before execution
- Consider using mock mode for testing
- Avoid storing sensitive information in command files
- Use comments to document the purpose of each command 
- Store command files securely to prevent unauthorized access 