"""
Voice Command Handler - Processes voice commands for the trading system
"""

import logging
import time
import threading
import os
import speech_recognition as sr
import pyttsx3
from typing import Dict, Any, Optional, Callable
from .command_processor import CommandProcessor
from ..config import config
from datetime import datetime

logger = logging.getLogger(__name__)

# Import Whisper conditionally to avoid errors if not installed
# but user wants to use Google's service
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not available. Install with 'pip install openai-whisper torch'")

class VoiceCommandHandler:
    """
    Handles voice-based commands for the trading system
    """
    
    def __init__(self):
        """Initialize the voice command handler"""
        self.command_processor = CommandProcessor()
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.is_listening = False
        self.listen_thread = None
        self.timeout = config.VOICE_RECOGNITION_TIMEOUT
        self.callback = None
        self.speech_engine = config.SPEECH_RECOGNITION_ENGINE
        self.whisper_model = None
        
        # Error recovery tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        self.last_error_time = None
        
        # Initialize Whisper model if needed
        if self.speech_engine == 'whisper':
            if not WHISPER_AVAILABLE:
                logger.error("Whisper selected but not installed. Falling back to Google")
                self.speech_engine = 'google'
            else:
                logger.info(f"Loading Whisper model ({config.WHISPER_MODEL_SIZE})...")
                self.whisper_model = whisper.load_model(config.WHISPER_MODEL_SIZE)
                logger.info("Whisper model loaded successfully")
        
        # Configure text-to-speech
        self.engine.setProperty('rate', 150)  # Speed of speech
        voices = self.engine.getProperty('voices')
        # Set to a female voice if available (usually index 1)
        if len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)
            
        logger.info(f"Voice command handler initialized with {self.speech_engine} speech recognition")
    
    def speak(self, text: str) -> None:
        """
        Speak a message using text-to-speech
        
        Args:
            text (str): Text to speak
        """
        logger.info(f"Speaking: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def start_listening(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        Start listening for voice commands
        
        Args:
            callback (Optional[Callable]): Function to call with results
        """
        if self.is_listening:
            logger.warning("Already listening for voice commands")
            return
            
        self.callback = callback
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        logger.info("Started listening for voice commands")
        self.speak(f"Voice commands activated using {self.speech_engine} recognition. What would you like to do?")
    
    def stop_listening(self) -> None:
        """
        Stop listening for voice commands
        """
        if not self.is_listening:
            logger.warning("Not currently listening for voice commands")
            return
            
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=1.0)
            self.listen_thread = None
        
        logger.info("Stopped listening for voice commands")
        self.speak("Voice commands deactivated")
    
    def listen_once(self) -> Dict[str, Any]:
        """
        Listen for a single voice command
        
        Returns:
            Dict[str, Any]: Result of command processing
        """
        self.speak("Listening for command")
        
        try:
            command = self._recognize_speech()
            if command:
                result = self.process_command(command)
                self._speak_result(result)
                return result
            else:
                self.speak("I didn't hear anything. Please try again.")
                return {
                    'success': False,
                    'error': 'No speech detected',
                    'message': 'No speech detected'
                }
        except Exception as e:
            logger.error(f"Error in listen_once: {str(e)}")
            self.speak("There was an error processing your command")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a voice command
        
        Args:
            command (str): Command text
            
        Returns:
            Dict[str, Any]: Command result
        """
        logger.info(f"Processing voice command: {command}")
        
        # Echo the recognized command
        self.speak(f"I heard: {command}")
        
        try:
            # Process the command
            result = self.command_processor.process_command(command)
            return result
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            error_message = f"Error: {str(e)}"
            self.speak(error_message)
            return {
                'success': False,
                'error': str(e),
                'message': error_message
            }
    
    def _listen_loop(self) -> None:
        """
        Background loop for continuous listening
        """
        while self.is_listening:
            try:
                command = self._recognize_speech()
                if command:
                    result = self.process_command(command)
                    self._speak_result(result)
                    
                    # Call the callback if provided
                    if self.callback:
                        try:
                            self.callback(result)
                        except Exception as e:
                            logger.error(f"Error in callback: {str(e)}")
                    
                    # Reset error counter on successful command
                    self.consecutive_errors = 0
                else:
                    # Increment error counter for null commands (not understood)
                    self.consecutive_errors += 1
                    self._handle_recognition_errors()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in listen loop: {str(e)}")
                self.consecutive_errors += 1
                self._handle_recognition_errors()
                time.sleep(1)  # Pause briefly after an error
    
    def _handle_recognition_errors(self) -> None:
        """
        Handle recognition errors with progressive feedback to the user
        """
        current_time = datetime.now() if datetime else None
        
        # Check if we need to reset error counter based on time
        if self.last_error_time and current_time:
            # If it's been more than 30 seconds since the last error, reset counter
            if (current_time - self.last_error_time).total_seconds() > 30:
                self.consecutive_errors = 1
        
        self.last_error_time = current_time
        
        # Provide progressive feedback based on error count
        if self.consecutive_errors == 1:
            # First error - simple acknowledgment
            self.speak("I didn't catch that. Please try again.")
        elif self.consecutive_errors == 2:
            # Second error - suggest speaking more clearly
            self.speak("Still having trouble understanding. Please speak clearly and a bit louder.")
        elif self.consecutive_errors >= self.max_consecutive_errors:
            # Multiple errors - provide more detailed help
            self.speak("I'm having trouble understanding your commands. Try these tips:")
            self.speak("Speak clearly and at a moderate pace.")
            self.speak("Reduce background noise if possible.")
            self.speak("Use simple command phrases like 'buy 10 shares of Apple' or 'what is the price of Microsoft'")
            # Reset counter to avoid repeating this message too often
            self.consecutive_errors = 0
    
    def _recognize_speech(self) -> Optional[str]:
        """
        Recognize speech from the microphone using the configured engine
        
        Returns:
            Optional[str]: Recognized speech text or None
        """
        with sr.Microphone() as source:
            logger.info(f"Listening for speech using {self.speech_engine}...")
            
            # Adjust for ambient noise
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception as e:
                logger.warning(f"Could not adjust for ambient noise: {e}")
            
            try:
                # Listen for speech
                audio = self.recognizer.listen(source, timeout=self.timeout)
                
                # Process with selected engine
                if self.speech_engine == 'whisper' and self.whisper_model:
                    # Use Whisper for local recognition
                    temp_dir = "temp"
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_file = os.path.join(temp_dir, "temp_speech.wav")
                    
                    # Save audio to temporary file
                    with open(temp_file, "wb") as f:
                        f.write(audio.get_wav_data())
                    
                    # Transcribe with Whisper
                    result = self.whisper_model.transcribe(temp_file)
                    text = result["text"].strip()
                    
                    # Clean up temporary file
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        logger.warning(f"Could not remove temp file: {str(e)}")
                    
                    logger.info(f"Recognized with Whisper: {text}")
                else:
                    # Use Google's speech recognition service
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"Recognized with Google: {text}")
                
                return text
                
            except sr.WaitTimeoutError:
                logger.info("No speech detected within timeout")
                return None
            except sr.UnknownValueError:
                logger.info("Speech not understood")
                return None
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {str(e)}")
                if self.speech_engine == 'google':
                    logger.info("Google API failed - consider switching to Whisper for offline recognition")
                
                # Try to fallback to alternate recognition engine
                if self.speech_engine == 'google' and WHISPER_AVAILABLE and self.whisper_model:
                    logger.info("Attempting fallback to Whisper for this request")
                    try:
                        # Re-process with Whisper
                        temp_dir = "temp"
                        os.makedirs(temp_dir, exist_ok=True)
                        temp_file = os.path.join(temp_dir, "temp_speech.wav")
                        
                        # Save audio to temporary file
                        with open(temp_file, "wb") as f:
                            f.write(audio.get_wav_data())
                        
                        # Transcribe with Whisper
                        result = self.whisper_model.transcribe(temp_file)
                        text = result["text"].strip()
                        
                        # Clean up temporary file
                        try:
                            os.remove(temp_file)
                        except Exception as e:
                            logger.warning(f"Could not remove temp file: {str(e)}")
                        
                        logger.info(f"Fallback recognition with Whisper successful: {text}")
                        return text
                    except Exception as fallback_error:
                        logger.error(f"Fallback recognition failed: {str(fallback_error)}")
                
                return None
            except Exception as e:
                logger.error(f"Error in speech recognition: {str(e)}")
                return None
    
    def _speak_result(self, result: Dict[str, Any]) -> None:
        """
        Speak the result of a command
        
        Args:
            result (Dict[str, Any]): Command result
        """
        success = result.get('success', False)
        
        if success:
            # Basic order confirmation
            if 'order' in result:
                symbol = result.get('symbol', '')
                quantity = result.get('quantity', 0)
                side = result.get('side', '')
                
                self.speak(f"Successfully placed {side} order for {quantity} shares of {symbol}")
                
            # Ladder order confirmation
            elif 'ladder_id' in result:
                symbol = result.get('symbol', '')
                quantity = result.get('quantity', 0)
                side = result.get('side', '')
                steps = result.get('steps', 0)
                orders_placed = result.get('orders_placed', 0)
                
                self.speak(f"Created {side} ladder for {quantity} shares of {symbol} with {orders_placed} of {steps} orders placed")
                
            # Help response
            elif 'help_text' in result:
                self.speak("Here are the available commands. Please check the screen for details.")
                
            # Status response
            elif 'account' in result:
                positions = len(result.get('positions', []))
                
                if positions > 0:
                    self.speak(f"Account status retrieved. You have {positions} open positions.")
                else:
                    self.speak("Account status retrieved. You have no open positions.")
                    
            # Default success
            else:
                self.speak("Command executed successfully")
                
        else:
            # Error response
            error = result.get('error', 'Unknown error')
            self.speak(f"Command failed. {error}")
            
            if 'help' in result:
                self.speak("Try saying help for a list of commands") 