"""
Command Handler module - provides a unified interface for CLI command handling.
This module serves as a wrapper around the TextCommandHandler and VoiceCommandHandler.
"""

import logging
from typing import Dict, Any, Optional

# Import the specific handlers
from .text_command_handler import TextCommandHandler
from .voice_command_handler import VoiceCommandHandler

logger = logging.getLogger(__name__)

class CommandHandler:
    """
    Unified command handler that delegates to either text or voice handlers
    based on the type of input.
    """
    
    def __init__(self):
        """Initialize the command handler."""
        self.text_handler = TextCommandHandler()
        self.voice_handler = VoiceCommandHandler()
        logger.info("CommandHandler initialized with text and voice capabilities")
    
    def process_command(self, command: str, use_voice: bool = False) -> Dict[str, Any]:
        """
        Process a command string, delegating to the appropriate handler.
        
        Args:
            command (str): The command to process
            use_voice (bool): Whether to use voice processing (default: False)
            
        Returns:
            Dict[str, Any]: Command processing result
        """
        if use_voice:
            return self.voice_handler.process_command(command)
        else:
            return self.text_handler.process_command(command)
    
    def process_command_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process commands from a file.
        
        Args:
            file_path (str): Path to the command file
            
        Returns:
            Dict[str, Any]: Processing results
        """
        # Only text handler supports file processing
        return self.text_handler.process_command_file(file_path)
    
    def get_command_history(self, limit: Optional[int] = None) -> list:
        """
        Get command history from text handler.
        
        Args:
            limit (Optional[int]): Maximum number of history items to retrieve
            
        Returns:
            list: Command history items
        """
        return self.text_handler.get_command_history(limit) 