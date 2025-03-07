#!/usr/bin/env python3
"""
Automated Trading System - Main Entry Point
"""

import os
import sys
import logging
import argparse
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.logging import RichHandler

# Import app modules
import app
from app.interfaces.cli import TextCommandHandler, VoiceCommandHandler
from app.interfaces.web import create_app, create_fastapi_app
from app.services import ServiceRegistry
from app.config import config

# Set up logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("main")
console = Console()

def setup_command_line():
    """Set up command line arguments"""
    parser = argparse.ArgumentParser(
        description="Automated Trading System using Schwab API"
    )
    
    # Interface options
    interface_group = parser.add_argument_group('Interface Options')
    interface_group.add_argument(
        "--voice", "-v",
        action="store_true",
        help="Start with voice command interface"
    )
    
    interface_group.add_argument(
        "--text", "-t",
        action="store_true",
        help="Start with text command interface (default)"
    )
    
    interface_group.add_argument(
        "--web", "-w",
        action="store_true",
        help="Start web API server"
    )
    
    # Command file option
    interface_group.add_argument(
        "--file", "-f",
        type=str,
        metavar="FILENAME",
        help="Read and execute commands from a file"
    )
    
    # Web server options
    web_group = parser.add_argument_group('Web Server Options')
    web_group.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for web server (default: 127.0.0.1)"
    )
    
    web_group.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Port for web server (default: 5000)"
    )
    
    web_group.add_argument(
        "--debug",
        action="store_true",
        help="Run web server in debug mode"
    )
    
    web_group.add_argument(
        "--use-fastapi",
        action="store_true",
        help="Use FastAPI instead of Flask for the web API"
    )
    
    # Voice recognition options
    voice_group = parser.add_argument_group('Voice Recognition Options')
    voice_group.add_argument(
        "--whisper",
        action="store_true",
        help="Use Whisper for local speech recognition (default: Google)"
    )
    
    voice_group.add_argument(
        "--model", "-m",
        choices=["tiny", "base", "small", "medium", "large"],
        default=config.WHISPER_MODEL_SIZE,
        help="Select Whisper model size (default: base)"
    )
    
    # Add a positional argument for direct command execution
    parser.add_argument(
        "command",
        nargs="*",
        help="Command to execute directly (if no other interface option is specified)"
    )
    
    return parser.parse_args()

def display_welcome():
    """Display welcome message"""
    console.print()
    welcome_text = Text("Automated Trading System", style="bold blue")
    welcome_panel = Panel(
        welcome_text, 
        title="Welcome",
        subtitle=f"v{app.__version__}"
    )
    console.print(welcome_panel)
    console.print()
    
    console.print("[bold]Features:[/bold]")
    console.print("✓ Execute trades with Schwab API")
    console.print("✓ Text and voice command interfaces")
    console.print("✓ Web API interface")
    console.print("✓ Advanced trading strategies")
    console.print("✓ Extended hours trading")
    console.print()
    
    # Display API credential status
    api_key = config.SCHWAB_API_KEY
    if api_key:
        console.print("[green]✓ API credentials found[/green]")
    else:
        console.print("[yellow]! API credentials missing. Paper/mock trading will be used.[/yellow]")
    
    # Display trading mode
    trading_mode = config.TRADING_MODE
    if trading_mode == 'LIVE':
        console.print(f"[bold red]! LIVE TRADING ENABLED - REAL ORDERS WILL BE PLACED[/bold red]")
    else:
        console.print(f"[green]✓ Trading mode: {trading_mode}[/green]")
    
    console.print()

def start_flask_server(host, port, debug):
    """Start the Flask web API server"""
    console.print(f"[bold]Starting Flask web API server on {host}:{port}...[/bold]")
    
    # Create and run the Flask app
    app = create_app()
    app.run(host=host, port=port, debug=debug)

def start_fastapi_server(host, port, debug):
    """Start the FastAPI web API server"""
    console.print(f"[bold]Starting FastAPI web API server on {host}:{port}...[/bold]")
    
    # Import here to avoid circular imports
    import uvicorn
    
    # Create the FastAPI app
    fastapi_app = create_fastapi_app()
    
    # Run with uvicorn
    uvicorn.run(
        "app.interfaces.web.fastapi_app:create_fastapi_app",
        host=host,
        port=port,
        reload=debug,
        factory=True,
        log_level="info"
    )

def main():
    """Main entry point"""
    try:
        # Parse command line arguments
        args = setup_command_line()
        
        # Initialize services
        ServiceRegistry.initialize_services()
        
        # Handle speech recognition options
        if args.whisper:
            os.environ['SPEECH_RECOGNITION_ENGINE'] = 'whisper'
            if args.model:
                os.environ['WHISPER_MODEL_SIZE'] = args.model
                
        # Display welcome
        display_welcome()
        
        # Determine interface mode
        use_voice = args.voice
        use_text = args.text
        use_web = args.web
        command_file = args.file
        direct_command = args.command
        
        # Handle direct command execution (highest priority)
        if direct_command:
            command_string = " ".join(direct_command)
            console.print(f"[bold]Executing command: {command_string}[/bold]")
            
            # Use the TextCommandHandler like the file method does
            text_handler = TextCommandHandler()
            
            # Process the command directly - this will handle natural language the same way
            # that processing a file would
            text_handler.process_command(command_string)
            
            return 0
        
        # Default to text if no interface specified
        if not (use_voice or use_text or use_web) and not command_file:
            use_text = True
        
        # Show speech recognition info if voice is enabled
        if use_voice:
            speech_engine = os.environ.get('SPEECH_RECOGNITION_ENGINE', config.SPEECH_RECOGNITION_ENGINE)
            if speech_engine == 'whisper':
                whisper_model = os.environ.get('WHISPER_MODEL_SIZE', config.WHISPER_MODEL_SIZE)
                console.print(f"[bold blue]Using Whisper ({whisper_model}) for offline speech recognition[/bold blue]")
            else:
                console.print("[bold blue]Using Google for online speech recognition[/bold blue]")
        
        # Start the appropriate interface(s)
        if use_web:
            # Start web server
            if args.use_fastapi:
                start_fastapi_server(args.host, args.port, args.debug)
            else:
                start_flask_server(args.host, args.port, args.debug)
            
        elif use_voice and config.ENABLE_VOICE_COMMANDS:
            console.print("[bold]Starting voice command interface...[/bold]")
            voice_handler = VoiceCommandHandler()
            
            # Define callback to display results
            def voice_result_callback(result):
                success = result.get('success', False)
                if success:
                    console.print("[green]Command successful[/green]")
                else:
                    error = result.get('error', 'Unknown error')
                    console.print(f"[red]Command failed: {error}[/red]")
            
            # Start listening for voice commands
            voice_handler.start_listening(callback=voice_result_callback)
            
            console.print("[bold]Voice interface started. Press Ctrl+C to exit.[/bold]")
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                voice_handler.stop_listening()
                console.print("\n[bold]Voice interface stopped[/bold]")
                
        elif command_file:
            console.print(f"[bold]Processing commands from file: {command_file}[/bold]")
            text_handler = TextCommandHandler()
            text_handler.process_command_file(command_file)
            
        elif use_text:
            console.print("[bold]Starting text command interface...[/bold]")
            text_handler = TextCommandHandler()
            text_handler.start_interactive_session()
        
    except Exception as e:
        logger.exception("Unexpected error in main application")
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 