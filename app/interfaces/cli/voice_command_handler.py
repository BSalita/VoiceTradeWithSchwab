"""
Voice Command Handler - Processes voice commands for the trading system using services
"""

import logging
import time
import threading
import os
import speech_recognition as sr
import pyttsx3
from typing import Dict, Any, Optional, Callable
from ...commands.command_processor import CommandProcessor
from ...services import get_service, ServiceRegistry
from ...config import config

logger = logging.getLogger(__name__)

# Flag to track whether optional dependencies are available
WHISPER_AVAILABLE = False

# Try to import Whisper, but don't fail if it's not available
try:
    import whisper
    WHISPER_AVAILABLE = True
    logger.info("Whisper library loaded successfully for advanced voice recognition")
except ImportError:
    logger.warning("Whisper library not available. Install with 'pip install openai-whisper torch'")
    logger.warning("Falling back to basic speech recognition")

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
        self.timeout = 5  # Default timeout
        self.callback = None
        self.speech_engine = os.environ.get('SPEECH_RECOGNITION_ENGINE', 'google')
        self.whisper_model = None
        
        # Initialize services if not already done
        try:
            trading_service = get_service("trading")
            if trading_service is None:
                ServiceRegistry.initialize_services()
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
        
        # Initialize Whisper model if available
        if WHISPER_AVAILABLE:
            try:
                # Load a smaller model for faster processing
                self.whisper_model = whisper.load_model("base")
                logger.info("Loaded Whisper base model for speech recognition")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {str(e)}")
                logger.warning("Falling back to basic speech recognition")
        
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
                    'error': 'No speech detected'
                }
        except Exception as e:
            logger.error(f"Error in listen_once: {str(e)}")
            self.speak("There was an error processing your command")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _listen_loop(self) -> None:
        """Internal method for the listening loop"""
        while self.is_listening:
            try:
                # Recognize speech
                command = self._recognize_speech()
                
                # Process if we have a command
                if command:
                    result = self.process_command(command)
                    
                    # Call callback if provided
                    if self.callback:
                        self.callback(result)
                        
                    # Speak the result
                    self._speak_result(result)
                    
                    # Pause briefly to avoid repeating too quickly
                    time.sleep(1.0)
            except Exception as e:
                logger.error(f"Error in listening loop: {str(e)}")
                self.speak("There was an error processing your command")
                time.sleep(2.0)
                
            # Small delay to avoid high CPU usage
            time.sleep(0.1)
                
    def _recognize_speech(self) -> Optional[str]:
        """
        Recognize speech using the configured engine
        
        Returns:
            Optional[str]: Recognized text or None if not recognized
        """
        with sr.Microphone() as source:
            logger.info(f"Listening for speech using {self.speech_engine}...")
            
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
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
                
            # Strategy confirmation
            elif 'strategy_key' in result:
                strategy_type = result.get('strategy_type', '')
                symbol = result.get('symbol', '')
                
                self.speak(f"Started {strategy_type} strategy for {symbol}")
                
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
                    
            # Trade history response
            elif 'trades' in result:
                count = result.get('count', 0)
                self.speak(f"Retrieved {count} trades from history.")
                
            # Export confirmation
            elif 'filename' in result:
                filename = result.get('filename', '')
                self.speak(f"Exported trade history to {filename}")
                
            # Default success
            else:
                message = result.get('message', 'Command executed successfully')
                self.speak(message)
                
        else:
            # Error response
            error = result.get('error', 'Unknown error')
            self.speak(f"Command failed. {error}")
            
            if 'help' in result:
                self.speak("Try saying help for a list of commands")
    
    def listen_for_command(self) -> Optional[str]:
        """
        Listen for a voice command and return the recognized text
        
        Returns:
            Optional[str]: Recognized command text or None if not recognized
        """
        try:
            # Try to recognize speech
            command = self._recognize_speech()
            return command
        except Exception as e:
            logger.error(f"Error in listen_for_command: {str(e)}")
            return None
    
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
        
        # Process the command
        result = self.command_processor.process_command(command)
        
        return result 
        
    def process_voice_command(self, command: str) -> Dict[str, Any]:
        """
        Process a voice command (alias for process_command)
        
        Args:
            command (str): Command text
            
        Returns:
            Dict[str, Any]: Command result
        """
        return self.process_command(command) 