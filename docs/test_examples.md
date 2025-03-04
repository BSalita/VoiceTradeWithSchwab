# Test Examples

This document provides examples of tests for different components of the trading system, with a focus on best practices and common patterns.

## Table of Contents

- [Import Structure](#import-structure)
- [Voice Command Tests](#voice-command-tests)
- [Trading Service Tests](#trading-service-tests)
- [Command Processing Tests](#command-processing-tests)
- [API Client Tests](#api-client-tests)
- [FastAPI Endpoint Tests](#fastapi-endpoint-tests)

## Import Structure

The project is structured as a proper Python package, which allows direct imports of modules without path manipulation. All test files should use proper import paths:

```python
# Correct import structure
from app.services.trading_service import TradingService
from app.api.schwab_client import SchwabAPIClient
from app.interfaces.cli.command_processor import CommandProcessor
from app.models.order import Order

# Avoid using relative imports in test files
# Do NOT use: from ...app.services import trading_service

# Test files should NOT include sys.path manipulation
# Do NOT use: sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

When creating new test files, ensure they can find the application modules by importing them directly from the `app` package.

## Voice Command Tests

Voice command tests are particularly complex because they involve:
- Mocking external libraries (speech_recognition, pyttsx3, whisper)
- Working with audio data
- Testing multiple recognition engines
- Handling file operations

### Testing with Google Recognition

```python
def test_listen_for_command_google(self):
    """Test listening for commands using Google recognition"""
    # Set up the mock to return a specific command
    self.mock_recognizer.listen.return_value = self.mock_audio
    self.mock_recognizer.recognize_google.return_value = "buy 10 shares of Apple"
    self.handler.speech_engine = "google"
    
    # Call the method
    result = self.handler._recognize_speech()
    
    # Verify the result
    self.assertEqual(result, "buy 10 shares of Apple")
    self.mock_recognizer.listen.assert_called_once()
    self.mock_recognizer.recognize_google.assert_called_once_with(self.mock_audio)
```

### Testing with Whisper Model

When testing the Whisper model, you need to properly mock the `open` function by using `builtins.open`:

```python
@patch('whisper.load_model')
def test_listen_for_command_whisper(self, mock_load_model):
    """Test listening for commands using Whisper model"""
    # Set up the mock to return a specific command
    self.mock_recognizer.listen.return_value = self.mock_audio
    self.handler.speech_engine = "whisper"
    
    # Mock the whisper model to return a specific result
    self.handler.whisper_model = self.mock_whisper_model
    self.mock_whisper_model.transcribe.return_value = {"text": "sell 20 shares of Microsoft"}
    
    # Create a temporary environment for testing
    with patch('os.makedirs'), patch('os.path.join', return_value="temp/temp_speech.wav"), \
         patch('builtins.open', create=True), patch('os.remove'):
        # Call the method
        result = self.handler._recognize_speech()
        
        # Verify the result
        self.assertEqual(result, "sell 20 shares of Microsoft")
        self.mock_recognizer.listen.assert_called_once()
```

### Testing Error Handling

```python
def test_recognize_with_whisper_error(self):
    """Test error handling in Whisper model recognition"""
    # Set up the mock to raise an exception
    self.mock_recognizer.listen.return_value = self.mock_audio
    self.handler.speech_engine = "whisper"
    self.handler.whisper_model = self.mock_whisper_model
    self.mock_whisper_model.transcribe.side_effect = Exception("Transcription error")
    
    # Create a temporary environment for testing
    with patch('os.makedirs'), patch('os.path.join', return_value="temp/temp_speech.wav"), \
         patch('builtins.open', create=True):
        
        # Call the method and expect an exception
        result = self.handler._recognize_speech()
        
        # Verify that None is returned for the error case
        self.assertIsNone(result)
```

### Testing Listening Loop

```python
@patch('app.interfaces.cli.voice_command_handler.time.sleep')
def test_listen_loop(self, mock_sleep):
    """Test the listening loop"""
    # Set up mocks
    self.mock_recognizer.listen.return_value = self.mock_audio
    self.mock_recognizer.recognize_google.return_value = "buy 10 shares of Apple"
    
    # Create a callback that will set is_listening to False after being called
    def side_effect(result):
        self.handler.is_listening = False
        
    # Set up the handler to run the loop once then exit
    self.handler.is_listening = True
    self.handler.callback = MagicMock()
    self.handler.callback.side_effect = side_effect
    
    # Call the method
    self.handler._listen_loop()
    
    # Verify the interactions
    self.mock_recognizer.listen.assert_called_once()
    self.mock_recognizer.recognize_google.assert_called_once()
    self.mock_command_processor.process_command.assert_called_once()
    self.handler.callback.assert_called_once()
```

### Common Pitfalls in Voice Command Tests

1. **Not properly mocking the built-in `open` function**:
   - Incorrect: `@patch('open', create=True)`
   - Correct: `@patch('builtins.open', create=True)`

2. **Missing cleanup of temporary files**:
   - Always patch `os.remove` or use a context manager to clean up temporary files

3. **Not handling different recognition engines**:
   - Test both Google and Whisper recognition paths

4. **Missing error handling tests**:
   - Test `UnknownValueError`, `RequestError`, and other exceptions

## Trading Service Tests

### Testing Order Placement

```python
def test_place_market_order_success(self):
    """Test successful market order placement."""
    # Arrange
    service = TradingService(mock_api_client)
    mock_api_client.place_order.return_value = {"order_id": "12345"}
    
    # Act
    result = service.place_market_order(symbol="AAPL", quantity=10, side="buy")
    
    # Assert
    self.assertTrue(result["success"])
    self.assertEqual(result["order_id"], "12345")
    mock_api_client.place_order.assert_called_once()
```

## Command Processing Tests

### Testing Command Parsing

```python
def test_parse_buy_command(self):
    """Test parsing a buy command."""
    # Arrange
    processor = CommandProcessor()
    
    # Act
    command_parts = processor.parse_command("buy 10 shares of AAPL")
    command_type = processor.identify_command_type(command_parts)
    
    # Assert
    self.assertEqual(command_type, "buy_order")
    self.assertEqual(command_parts, ["buy", "10", "shares", "of", "AAPL"])
```

## API Client Tests

### Testing API Requests

```python
@patch('requests.post')
def test_place_order_success(self, mock_post):
    """Test successful order placement."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"order_id": "12345"}
    mock_post.return_value = mock_response
    
    client = SchwabAPIClient()
    
    # Act
    result = client.place_order(symbol="AAPL", quantity=10, side="buy")
    
    # Assert
    self.assertEqual(result["order_id"], "12345")
    mock_post.assert_called_once()
```

## FastAPI Endpoint Tests

### Testing API Endpoints

```python
def test_health_endpoint(self):
    """Test the health check endpoint."""
    # Arrange
    client = TestClient(app)
    
    # Act
    response = client.get("/api/health")
    
    # Assert
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()["status"], "ok")
```

### Testing Error Handling

```python
def test_place_order_validation_error(self):
    """Test validation error handling in place order endpoint."""
    # Arrange
    client = TestClient(app)
    
    # Act
    response = client.post(
        "/api/orders",
        json={"symbol": "AAPL", "quantity": -10, "side": "buy"}
    )
    
    # Assert
    self.assertEqual(response.status_code, 422)
    self.assertFalse(response.json()["success"])
    self.assertIn("error", response.json())
``` 