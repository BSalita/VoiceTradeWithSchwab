# Error Handling Guide

This document provides a comprehensive guide to error handling in the Automated Trading System, covering all major components and providing guidance for troubleshooting common issues.

## Table of Contents

- [Error Handling Principles](#error-handling-principles)
- [Error Categories](#error-categories)
- [API Client Error Handling](#api-client-error-handling)
- [Service Layer Error Handling](#service-layer-error-handling)
- [Command Processing Error Handling](#command-processing-error-handling)
- [Web API Error Handling](#web-api-error-handling)
- [Strategy Error Handling](#strategy-error-handling)
- [Voice Command Error Handling](#voice-command-error-handling)
- [Logging and Monitoring](#logging-and-monitoring)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Error Handling Principles

The Automated Trading System follows these core principles for error handling:

1. **Fail safely**: In case of errors, the system should default to the most conservative action to protect the user's capital.
2. **Provide clear feedback**: Error messages should be clear and actionable.
3. **Centralized error handling**: Each layer of the application has standardized error handling.
4. **Comprehensive logging**: All errors are logged with context for troubleshooting.
5. **Recovery mechanisms**: Where possible, automatic recovery mechanisms are implemented.

## Error Categories

Errors in the system are categorized as follows:

### 1. API Errors

Errors related to communication with the Schwab API:
- Authentication failures
- Network connectivity issues
- Rate limiting
- Invalid API responses

### 2. Validation Errors

Errors related to input validation:
- Invalid command formats
- Invalid parameter values
- Missing required parameters

### 3. Business Logic Errors

Errors related to business rules:
- Insufficient funds
- Invalid trading hours
- Unsupported order types
- Strategy parameter constraints

### 4. System Errors

Errors related to the application itself:
- Configuration issues
- Dependency failures
- Resource limitations

## API Client Error Handling

The `SchwabAPIClient` class handles errors from the Schwab API:

### Exception Hierarchy

```python
# Base exception for all API errors
class SchwabAPIError(Exception):
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

# Specific error types
class SchwabAuthenticationError(SchwabAPIError):
    """Raised when API authentication fails"""
    pass

class SchwabRateLimitError(SchwabAPIError):
    """Raised when API rate limits are exceeded"""
    pass

class SchwabNetworkError(SchwabAPIError):
    """Raised when network connectivity issues occur"""
    pass

class SchwabResponseError(SchwabAPIError):
    """Raised when the API returns an error response"""
    pass
```

### Error Handling Strategy

1. **Request Retries**: Network errors are automatically retried with exponential backoff.
2. **Rate Limit Handling**: Rate limit errors trigger automatic throttling.
3. **Error Mapping**: HTTP errors are mapped to specific exception types.
4. **Logging**: All API errors are logged with context.

### Example Usage

```python
try:
    client = SchwabAPIClient()
    result = client.place_order(...)
except SchwabAuthenticationError:
    # Handle authentication issues
    log.error("Authentication failed. Please check credentials.")
except SchwabRateLimitError as e:
    # Handle rate limiting
    retry_after = e.details.get('retry_after', 60)
    log.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
    time.sleep(retry_after)
except SchwabNetworkError:
    # Handle network issues
    log.error("Network error. Please check your connection.")
except SchwabResponseError as e:
    # Handle API response errors
    log.error(f"API error: {e.message}, Code: {e.code}")
except SchwabAPIError as e:
    # Catch-all for other API errors
    log.error(f"Unexpected API error: {e.message}")
```

## Service Layer Error Handling

Services like `TradingService`, `MarketDataService`, and `StrategyService` implement consistent error handling:

### Error Propagation

Services may catch and handle specific errors but generally propagate them with additional context:

```python
def place_market_order(self, symbol, quantity, side):
    """Place a market order."""
    try:
        return self.api_client.place_order(
            symbol=symbol,
            quantity=quantity,
            side=side,
            order_type="market"
        )
    except SchwabAPIError as e:
        # Add context to the error
        message = f"Failed to place {side} order for {quantity} shares of {symbol}: {e.message}"
        logger.error(message)
        # Re-raise with additional context
        raise SchwabAPIError(message, code=e.code, details=e.details)
```

### Result Formatting

Services standardize error and success responses:

```python
# Success result
{
    "success": true,
    "data": {...},  # Operation-specific data
    "message": "Operation completed successfully"
}

# Error result
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {}  # Additional context
    }
}
```

## Command Processing Error Handling

The `CommandProcessor` class handles errors in natural language command processing:

### Command Validation

Commands are validated before execution:

```python
def validate_order_command(self, command_parts):
    """Validate order command parameters."""
    if len(command_parts) < 4:
        return {
            "valid": False,
            "error": "Incomplete command. Format: buy/sell [quantity] shares of [symbol]"
        }
    
    try:
        quantity = int(command_parts[1])
        if quantity <= 0:
            return {
                "valid": False,
                "error": "Quantity must be a positive number"
            }
    except ValueError:
        return {
            "valid": False,
            "error": f"Invalid quantity: {command_parts[1]}"
        }
    
    return {"valid": True}
```

### Error Responses

Command errors return human-friendly messages:

```python
def process_command(self, command_text):
    """Process a command string."""
    try:
        command_parts = self.parse_command(command_text)
        command_type = self.identify_command_type(command_parts)
        
        if command_type == "buy_order":
            validation = self.validate_order_command(command_parts)
            if not validation["valid"]:
                return {
                    "success": False,
                    "message": validation["error"]
                }
            
            # Process valid command...
            
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"An error occurred while processing your command: {str(e)}"
        }
```

## Web API Error Handling

### FastAPI Error Handling

FastAPI endpoints use exception handlers for consistent error responses:

```python
@app.exception_handler(SchwabAPIError)
async def api_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": exc.code or "API_ERROR",
                "message": exc.message,
                "details": exc.details
            }
        }
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": exc.errors()
            }
        }
    )

@app.exception_handler(Exception)
async def general_error_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred"
            }
        }
    )
```

### Input Validation

Pydantic models provide input validation for API requests:

```python
class OrderRequest(BaseModel):
    symbol: str
    quantity: int
    side: str
    order_type: str
    price: Optional[float] = None
    duration: str = "day"
    session: str = "regular"
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('quantity must be positive')
        return v
    
    @validator('side')
    def side_must_be_valid(cls, v):
        if v.lower() not in ('buy', 'sell'):
            raise ValueError('side must be "buy" or "sell"')
        return v.lower()
```

## Strategy Error Handling

Trading strategies implement error handling for different execution phases:

### Initialization Errors

Errors during strategy setup:

```python
def initialize_ladder_strategy(self, symbol, side, steps, start_price, end_price, quantity):
    """Initialize a ladder strategy."""
    try:
        # Validate parameters
        if steps <= 0:
            raise ValueError("Steps must be a positive number")
        
        if quantity <= 0:
            raise ValueError("Quantity must be a positive number")
        
        if start_price <= 0 or end_price <= 0:
            raise ValueError("Prices must be positive numbers")
        
        if side.lower() not in ("buy", "sell"):
            raise ValueError("Side must be 'buy' or 'sell'")
        
        if (side.lower() == "buy" and start_price > end_price) or \
           (side.lower() == "sell" and start_price < end_price):
            raise ValueError(f"Invalid price range for {side} ladder")
        
        # Continue with initialization...
        
    except Exception as e:
        logger.error(f"Error initializing ladder strategy: {str(e)}")
        raise
```

### Execution Errors

Errors during strategy execution:

```python
def execute_ladder_step(self, ladder_id, step_index):
    """Execute a single step of a ladder strategy."""
    try:
        ladder = self.active_ladders.get(ladder_id)
        if not ladder:
            raise ValueError(f"Ladder {ladder_id} not found")
        
        if step_index >= len(ladder["steps"]):
            raise IndexError(f"Step index {step_index} out of range")
        
        step = ladder["steps"][step_index]
        if step["status"] != "pending":
            logger.warning(f"Step {step_index} already executed")
            return
        
        # Execute the step...
        
    except Exception as e:
        logger.error(f"Error executing ladder step: {str(e)}")
        # Update step status to failed
        if ladder and step_index < len(ladder["steps"]):
            ladder["steps"][step_index]["status"] = "failed"
            ladder["steps"][step_index]["error"] = str(e)
        raise
```

## Voice Command Error Handling

The `VoiceCommandHandler` implements error handling for speech recognition:

### Recognition Errors

Handling errors during speech recognition:

```python
def listen_for_command(self):
    """Listen for a voice command."""
    with sr.Microphone() as source:
        try:
            self.speak("Listening...")
            audio = self.recognizer.listen(source, timeout=self.timeout)
            
            try:
                if self.speech_engine == "whisper" and WHISPER_AVAILABLE:
                    command = self._recognize_with_whisper(audio)
                else:
                    command = self.recognizer.recognize_google(audio)
                
                self.speak(f"I heard: {command}")
                return command
                
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't understand that.")
                return None
                
            except sr.RequestError as e:
                self.speak("Sorry, I couldn't connect to the recognition service.")
                logger.error(f"Recognition service error: {str(e)}")
                return None
                
        except sr.WaitTimeoutError:
            self.speak("No speech detected. Please try again.")
            return None
            
        except Exception as e:
            self.speak("An error occurred while listening.")
            logger.error(f"Error in speech recognition: {str(e)}", exc_info=True)
            return None
```

### Command Execution Errors

Handling errors during command execution:

```python
def process_voice_command(self, command):
    """Process a recognized voice command."""
    if not command:
        return False
    
    try:
        result = self.command_processor.process_command(command)
        
        if result["success"]:
            self.speak(result["message"])
            return True
        else:
            self.speak(f"Error: {result['message']}")
            return False
            
    except Exception as e:
        error_message = f"Error processing command: {str(e)}"
        logger.error(error_message, exc_info=True)
        self.speak("Sorry, I encountered a problem processing your command.")
        return False
```

## Logging and Monitoring

### Logging Strategy

The application uses a structured logging approach:

```python
# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("logs", f"{config.APP_NAME}.log")),
        logging.StreamHandler()
    ]
)

# Create a logger for a specific component
logger = logging.getLogger("trading_service")

# Log with context
logger.error(
    "Failed to place order",
    extra={
        "symbol": symbol,
        "quantity": quantity,
        "side": side,
        "user_id": user_id
    }
)
```

### Error Aggregation

Critical errors are collected for monitoring:

```python
class ErrorTracker:
    """Track application errors for monitoring and alerting."""
    
    def __init__(self):
        self.errors = []
        self.error_count = 0
        self.alert_threshold = 5
        self.alert_window = 60  # seconds
        
    def record_error(self, error_type, message, context=None):
        """Record an error occurrence."""
        now = time.time()
        self.errors.append({
            "timestamp": now,
            "type": error_type,
            "message": message,
            "context": context or {}
        })
        
        # Clean up old errors
        self.errors = [e for e in self.errors if now - e["timestamp"] < self.alert_window]
        
        # Check alert threshold
        if len(self.errors) >= self.alert_threshold:
            self.trigger_alert()
    
    def trigger_alert(self):
        """Trigger an alert for excessive errors."""
        logger.critical(f"Alert: {len(self.errors)} errors in the last {self.alert_window} seconds")
        # Additional alert mechanisms (email, SMS, etc.)
```

## Troubleshooting Common Issues

### API Connectivity Issues

**Symptoms:**
- "Failed to connect to API" errors
- Timeout errors
- Authentication failures

**Troubleshooting Steps:**
1. Check internet connectivity
2. Verify API credentials in `.env` file
3. Check if API endpoints are operational
4. Verify API rate limits haven't been exceeded
5. Check proxy settings if applicable

**Resolution:**
```python
# Verify API credentials
import os
from dotenv import load_dotenv
load_dotenv()

print("API Key present:", bool(os.environ.get("SCHWAB_API_KEY")))
print("API Secret present:", bool(os.environ.get("SCHWAB_API_SECRET")))

# Test connectivity
from app.api.schwab_client import SchwabAPIClient
client = SchwabAPIClient()
result = client.test_connectivity()
print("Connectivity test:", "Passed" if result["success"] else "Failed")
```

### Order Placement Failures

**Symptoms:**
- Orders fail to execute
- "Invalid parameter" errors
- "Insufficient funds" errors

**Troubleshooting Steps:**
1. Check account balance and buying power
2. Verify market hours for the requested security
3. Confirm order parameters are valid
4. Check for position or account limits

**Resolution:**
```python
# Check account status
from app.services import get_service
trading_service = get_service("trading")
account_info = trading_service.get_account_info()
print(f"Balance: ${account_info['balance']}")
print(f"Buying Power: ${account_info['buying_power']}")

# Verify market hours
market_data_service = get_service("market_data")
market_status = market_data_service.get_market_hours("AAPL")
print(f"Market Open: {market_status['is_open']}")
```

### Voice Recognition Issues

**Symptoms:**
- "Sorry, I didn't understand that" errors
- No response to speech
- Incorrect command recognition

**Troubleshooting Steps:**
1. Check microphone configuration
2. Verify internet connectivity for cloud-based recognition
3. Check for background noise
4. Test with simpler commands
5. Verify Whisper model is installed correctly if using it

**Resolution:**
```python
# Test microphone
import speech_recognition as sr
recognizer = sr.Recognizer()
with sr.Microphone() as source:
    print("Testing microphone...")
    audio = recognizer.listen(source, timeout=5)
    try:
        text = recognizer.recognize_google(audio)
        print(f"Recognized: {text}")
    except sr.UnknownValueError:
        print("Speech not recognized")
    except sr.RequestError:
        print("Recognition service unavailable")
```

### Strategy Execution Issues

**Symptoms:**
- Strategies fail to start
- Orders not placed as expected
- Unexpected strategy behavior

**Troubleshooting Steps:**
1. Check strategy initialization parameters
2. Verify market conditions match strategy requirements
3. Check for errors in strategy execution
4. Verify sufficient funds for the strategy

**Resolution:**
```python
# Check active strategies
from app.services import get_service
strategy_service = get_service("strategy")
active_strategies = strategy_service.get_active_strategies()
print(f"Active strategies: {len(active_strategies)}")
for strategy in active_strategies:
    print(f"ID: {strategy['id']}, Type: {strategy['type']}, Status: {strategy['status']}")
    if strategy['status'] == 'error':
        print(f"Error: {strategy.get('error_message')}")
```

### Configuration Issues

**Symptoms:**
- Application fails to start
- Missing component errors
- Unexpected default values

**Troubleshooting Steps:**
1. Check `.env` file for required variables
2. Verify configuration file syntax
3. Check for conflicting settings
4. Verify file permissions

**Resolution:**
```python
# Check configuration
from app.config import config
print("Trading Mode:", config.TRADING_MODE)
print("Log Level:", config.LOG_LEVEL)
print("Mock Data:", config.USE_MOCK_DATA)

# Verify environment variables
import os
required_vars = ["SCHWAB_API_KEY", "SCHWAB_API_SECRET", "TRADING_MODE"]
for var in required_vars:
    print(f"{var} set: {var in os.environ}")
``` 