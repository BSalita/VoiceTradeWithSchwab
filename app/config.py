"""
Configuration module for the trading application.
"""

import os
import logging
from typing import Any, Dict, Optional

class Config:
    """Configuration class for the application"""
    
    def __init__(self):
        """Initialize the configuration"""
        # Set up basic paths
        self.APP_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ROOT_DIR = os.path.dirname(self.APP_DIR)
        self.LOGS_DIR = os.path.join(self.ROOT_DIR, 'logs')
        self.DATA_DIR = os.path.join(self.ROOT_DIR, 'data')
        
        # Create required directories
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        os.makedirs(self.DATA_DIR, exist_ok=True)
        
        # Trading settings
        self.TRADING_MODE = self._get_trading_mode()
        self.COMMAND_HISTORY_SIZE = 100
        
        # Schwab API settings
        self.SCHWAB_API_BASE_URL = os.environ.get('SCHWAB_API_BASE_URL', 'https://api.schwab.com/v1/')
        self.SCHWAB_API_KEY = os.environ.get('SCHWAB_API_KEY', 'mock_api_key')
        self.SCHWAB_API_SECRET = os.environ.get('SCHWAB_API_SECRET', 'mock_api_secret')
        self.SCHWAB_AUTH_URL = os.environ.get('SCHWAB_AUTH_URL', 'https://auth.schwab.com/token')
        self.SCHWAB_STREAM_URL = os.environ.get('SCHWAB_STREAM_URL', 'wss://stream.schwab.com/v1')
        
        # Speech recognition settings
        self.WHISPER_MODEL_SIZE = os.environ.get('WHISPER_MODEL_SIZE', 'base')
        self.VOICE_RECOGNITION_TIMEOUT = int(os.environ.get('VOICE_RECOGNITION_TIMEOUT', '5'))
        self.SPEECH_RECOGNITION_ENGINE = os.environ.get('SPEECH_RECOGNITION_ENGINE', 'google')
        
        # Strategy settings
        self.STRATEGIES = {
            'BasicStrategy': 'app.strategies.basic_strategy.BasicStrategy',
            'LadderStrategy': 'app.strategies.ladder_strategy.LadderStrategy', 
            'OscillatingStrategy': 'app.strategies.oscillating_strategy.OscillatingStrategy',
            'HighLowStrategy': 'app.strategies.highlow_strategy.HighLowStrategy'
        }
        
        # Logging settings
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
        
        # API settings (load from environment or use defaults)
        self.API_TIMEOUT = int(os.environ.get('API_TIMEOUT', '30'))
    
    def _get_trading_mode(self) -> str:
        """
        Determine the trading mode with enhanced safety checks
        
        Returns:
            str: 'live', 'paper', or 'mock'
        """
        # Get mode from environment variable
        mode = os.environ.get('TRADING_MODE', '').lower()
        
        # Validate the mode
        valid_modes = ['live', 'paper', 'mock']
        
        # Check for environment variables indicating test environment
        is_test_env = any([
            os.environ.get('PYTEST_CURRENT_TEST', ''),  # Running under pytest
            os.environ.get('TEST_MODE', ''),            # Custom test flag
            'test' in mode                              # Mode contains 'test'
        ])
        
        # Force mock mode in test environments
        if is_test_env:
            logging.warning("Test environment detected, forcing MOCK trading mode")
            return 'mock'
        
        # Validate the mode with stricter checking
        if mode not in valid_modes:
            default_mode = 'mock'
            logging.warning(f"Invalid trading mode '{mode}'. Using {default_mode} mode.")
            return default_mode
            
        # Extra safety check for live mode
        if mode == 'live':
            # Look for explicit confirmation environment variable
            if not os.environ.get('CONFIRM_LIVE_TRADING', '').lower() == 'yes':
                logging.warning("Live trading requested but CONFIRM_LIVE_TRADING is not set to 'yes'. Falling back to paper mode.")
                return 'paper'
        
        return mode

    def get_api_keys(self) -> Dict[str, str]:
        """
        Get API keys from environment variables
        
        Returns:
            Dict[str, str]: Dictionary of API keys
        """
        return {
            'API_KEY': os.environ.get('API_KEY', ''),
            'API_SECRET': os.environ.get('API_SECRET', '')
        }

# Create a global config instance
config = Config() 