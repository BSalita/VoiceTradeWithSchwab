import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
SCHWAB_API_KEY = os.getenv('SCHWAB_API_KEY')
SCHWAB_API_SECRET = os.getenv('SCHWAB_API_SECRET')
SCHWAB_ACCOUNT_ID = os.getenv('SCHWAB_ACCOUNT_ID')
SCHWAB_API_BASE_URL = os.getenv('SCHWAB_API_BASE_URL', 'https://api.schwab.com/v1/')
SCHWAB_AUTH_URL = os.getenv('SCHWAB_AUTH_URL', 'https://api.schwab.com/oauth2/token')
SCHWAB_STREAM_URL = os.getenv('SCHWAB_STREAM_URL', 'wss://api.schwab.com/v1/markets/stream')

# Trading Settings
ENABLE_EXTENDED_HOURS = os.getenv('ENABLE_EXTENDED_HOURS', 'true').lower() == 'true'
DEFAULT_ORDER_TYPE = os.getenv('DEFAULT_ORDER_TYPE', 'MARKET')
MAX_ORDER_AMOUNT = float(os.getenv('MAX_ORDER_AMOUNT', '5000'))

# Trading Mode (LIVE, PAPER, MOCK)
TRADING_MODE = os.getenv('TRADING_MODE', 'MOCK').upper()
if TRADING_MODE not in ['LIVE', 'PAPER', 'MOCK']:
    print(f"Warning: Invalid TRADING_MODE '{TRADING_MODE}'. Defaulting to 'MOCK'")
    TRADING_MODE = 'MOCK'

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
ENABLE_TRADE_LOGGING = os.getenv('ENABLE_TRADE_LOGGING', 'true').lower() == 'true'

# Voice Recognition Settings
VOICE_RECOGNITION_TIMEOUT = int(os.getenv('VOICE_RECOGNITION_TIMEOUT', '5'))
ENABLE_VOICE_COMMANDS = os.getenv('ENABLE_VOICE_COMMANDS', 'true').lower() == 'true'
SPEECH_RECOGNITION_ENGINE = os.getenv('SPEECH_RECOGNITION_ENGINE', 'google').lower()  # 'google' or 'whisper'
WHISPER_MODEL_SIZE = os.getenv('WHISPER_MODEL_SIZE', 'base')  # 'tiny', 'base', 'small', 'medium', 'large'

# Application Paths
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(APP_ROOT, 'logs')

# Create logs directory if it doesn't exist
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Market Hours (Eastern Time)
REGULAR_MARKET_OPEN = '09:30'
REGULAR_MARKET_CLOSE = '16:00'
EXTENDED_HOURS_OPEN = '04:00'
EXTENDED_HOURS_CLOSE = '20:00'

# Trading Strategies Configuration
STRATEGIES = {
    'basic': 'BasicStrategy',
    'ladder': 'LadderStrategy',
    'oscillating': 'OscillatingStrategy',  # New continuous trading strategy
    'highlow': 'HighLowStrategy'
}

# Command Processing
COMMAND_HISTORY_SIZE = int(os.getenv('COMMAND_HISTORY_SIZE', '50')) 