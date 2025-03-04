"""
Voice command performance test scenarios.

This module contains performance tests for voice command processing
in the Automated Trading System.
"""

import os
import json
import random
import logging
import time
from pathlib import Path
from datetime import datetime

import numpy as np
from tests.performance.lib.base import PerformanceTest, LoadTest


class VoiceCommandProcessingTest(PerformanceTest):
    """Performance test for voice command processing pipeline."""
    
    def setup(self):
        """Set up the test environment."""
        self.logger.info("Setting up VoiceCommandProcessingTest")
        
        # Initialize services
        self.voice_command_handler = self.get_service("voice_command")
        self.command_processor = self.get_service("command_processor")
        
        # Load test voice samples
        self.voice_samples = self._load_voice_samples()
        if not self.voice_samples:
            self.logger.error("No voice samples found. Test cannot proceed.")
            return False
            
        # Test configuration
        self.test_iterations = self.config.get("iterations", 50)
        self.engine = self.config.get("speech_engine", "whisper")
        
        return True
    
    def _load_voice_samples(self):
        """Load test voice samples from data directory.
        
        Returns:
            dict: Dictionary of voice samples by command type.
        """
        samples = {}
        
        # Find voice sample files
        sample_dir = Path(__file__).parent.parent / "data" / "voice_samples"
        if not sample_dir.exists():
            self.logger.warning(f"Voice sample directory not found: {sample_dir}")
            
            # Create directory and add a note about missing samples
            sample_dir.mkdir(parents=True, exist_ok=True)
            note_file = sample_dir / "README.md"
            if not note_file.exists():
                with open(note_file, "w") as f:
                    f.write("# Voice Sample Files\n\n"
                           "Place voice sample WAV files in this directory for testing.\n"
                           "Organize samples in subdirectories by command type:\n"
                           "- buy_orders/\n"
                           "- sell_orders/\n"
                           "- quotes/\n"
                           "- account/\n"
                           "- strategy/\n")
            
            # Use mock data for testing if no real samples
            return self._generate_mock_voice_data()
        
        # Load voice samples by type
        for command_type in ["buy_orders", "sell_orders", "quotes", "account", "strategy"]:
            type_dir = sample_dir / command_type
            if not type_dir.exists():
                continue
                
            samples[command_type] = []
            for sample_file in type_dir.glob("*.wav"):
                samples[command_type].append(str(sample_file))
                
        return samples
    
    def _generate_mock_voice_data(self):
        """Generate mock voice data for testing when real samples aren't available.
        
        This creates synthetic audio-like data for testing the performance
        of the processing pipeline without actual audio files.
        
        Returns:
            dict: Dictionary of mock voice samples by command type.
        """
        self.logger.info("Generating mock voice data for testing")
        
        mock_samples = {
            "buy_orders": [f"mock_buy_{i}" for i in range(10)],
            "sell_orders": [f"mock_sell_{i}" for i in range(10)],
            "quotes": [f"mock_quote_{i}" for i in range(10)],
            "account": [f"mock_account_{i}" for i in range(5)],
            "strategy": [f"mock_strategy_{i}" for i in range(5)]
        }
        
        return mock_samples
    
    def execute(self):
        """Execute the test scenario."""
        self.logger.info(f"Executing VoiceCommandProcessingTest with {self.test_iterations} iterations")
        
        success_count = 0
        recognition_times = []
        processing_times = []
        total_times = []
        
        # Set speech recognition engine
        self.voice_command_handler.set_speech_engine(self.engine)
        
        for i in range(self.test_iterations):
            # Select random command type and sample
            command_type = random.choice(list(self.voice_samples.keys()))
            
            if not self.voice_samples[command_type]:
                continue
                
            sample = random.choice(self.voice_samples[command_type])
            
            try:
                start_time = time.time()
                
                # Recognition phase
                with self.measure("speech_recognition"):
                    if sample.startswith("mock_"):
                        # For mock data, simulate recognition with predefined outputs
                        if "buy" in sample:
                            text = f"Buy {random.randint(10, 100)} shares of {random.choice(['Apple', 'Microsoft', 'Google'])}"
                        elif "sell" in sample:
                            text = f"Sell {random.randint(10, 100)} shares of {random.choice(['Tesla', 'Amazon', 'Netflix'])}"
                        elif "quote" in sample:
                            text = f"Get quote for {random.choice(['Apple', 'Microsoft', 'Google', 'Amazon'])}"
                        elif "account" in sample:
                            text = "What is my account balance"
                        elif "strategy" in sample:
                            text = f"Start ladder strategy for {random.choice(['Apple', 'Microsoft'])} with {random.randint(3, 5)} steps"
                        else:
                            text = "Unknown command"
                    else:
                        # Process actual voice sample
                        text = self.voice_command_handler.recognize_speech(sample)
                
                recognition_time = time.time() - start_time
                recognition_times.append(recognition_time * 1000)  # Convert to ms
                
                # Command processing phase
                with self.measure("command_processing"):
                    parsed_command = self.command_processor.parse_command(text)
                    
                processing_time = time.time() - start_time - recognition_time
                processing_times.append(processing_time * 1000)  # Convert to ms
                
                # Total time
                total_time = time.time() - start_time
                total_times.append(total_time * 1000)  # Convert to ms
                
                # Log the results
                self.logger.debug(f"Iteration {i}: Sample={os.path.basename(str(sample))}, "
                                 f"Text='{text}', Recognition={recognition_time:.2f}s, "
                                 f"Processing={processing_time:.2f}s, Total={total_time:.2f}s")
                
                if parsed_command and parsed_command.get("valid", False):
                    success_count += 1
                
            except Exception as e:
                self.logger.error(f"Error in iteration {i}: {str(e)}")
                continue
        
        # Record overall metrics
        if recognition_times:
            self.metrics.set_gauge("recognition_time_avg", np.mean(recognition_times))
            self.metrics.set_gauge("processing_time_avg", np.mean(processing_times))
            self.metrics.set_gauge("total_time_avg", np.mean(total_times))
            self.metrics.set_gauge("success_rate", success_count / self.test_iterations)
            
            self.logger.info(f"Test completed: Success rate: {success_count / self.test_iterations:.2%}")
            self.logger.info(f"Average times: Recognition={np.mean(recognition_times):.2f}ms, "
                            f"Processing={np.mean(processing_times):.2f}ms, "
                            f"Total={np.mean(total_times):.2f}ms")
        
        return True
    
    def cleanup(self):
        """Clean up after the test."""
        self.logger.info("Cleaning up VoiceCommandProcessingTest")
        return True


class VoiceCommandAccuracyTest(PerformanceTest):
    """Test for measuring accuracy of voice command recognition."""
    
    def setup(self):
        """Set up the test environment."""
        self.logger.info("Setting up VoiceCommandAccuracyTest")
        
        # Initialize services
        self.voice_command_handler = self.get_service("voice_command")
        self.command_processor = self.get_service("command_processor")
        
        # Load test voice samples with known transcriptions
        self.voice_samples = self._load_labeled_samples()
        if not self.voice_samples:
            self.logger.error("No labeled voice samples found. Test cannot proceed.")
            return False
            
        # Test configuration
        self.engines = self.config.get("speech_engines", ["google", "whisper"])
        
        return True
    
    def _load_labeled_samples(self):
        """Load labeled voice samples from data directory.
        
        Each sample should have a corresponding JSON file with the
        expected transcription and command.
        
        Returns:
            list: List of (sample_path, expected_text, expected_command) tuples.
        """
        samples = []
        
        # Find labeled voice sample files
        sample_dir = Path(__file__).parent.parent / "data" / "labeled_voice_samples"
        if not sample_dir.exists():
            self.logger.warning(f"Labeled voice sample directory not found: {sample_dir}")
            
            # Create directory and add a note about missing samples
            sample_dir.mkdir(parents=True, exist_ok=True)
            note_file = sample_dir / "README.md"
            if not note_file.exists():
                with open(note_file, "w") as f:
                    f.write("# Labeled Voice Sample Files\n\n"
                           "Place voice sample WAV files in this directory with corresponding JSON files.\n"
                           "Example: sample1.wav and sample1.json\n\n"
                           "JSON format:\n"
                           "```json\n"
                           "{\n"
                           "  \"expected_text\": \"Buy 100 shares of Apple\",\n"
                           "  \"expected_command\": {\n"
                           "    \"type\": \"buy_order\",\n"
                           "    \"symbol\": \"AAPL\",\n"
                           "    \"quantity\": 100\n"
                           "  }\n"
                           "}\n"
                           "```\n")
            
            # Use mock data for testing if no real samples
            return self._generate_mock_labeled_data()
        
        # Load labeled samples
        for sample_file in sample_dir.glob("*.wav"):
            json_file = sample_file.with_suffix(".json")
            if not json_file.exists():
                continue
                
            try:
                with open(json_file, "r") as f:
                    label_data = json.load(f)
                    
                expected_text = label_data.get("expected_text", "")
                expected_command = label_data.get("expected_command", {})
                
                samples.append((str(sample_file), expected_text, expected_command))
                
            except Exception as e:
                self.logger.warning(f"Error loading label file {json_file}: {str(e)}")
                
        return samples
    
    def _generate_mock_labeled_data(self):
        """Generate mock labeled data for testing.
        
        Returns:
            list: List of (sample_id, expected_text, expected_command) tuples.
        """
        self.logger.info("Generating mock labeled data for testing")
        
        mock_samples = []
        
        # Buy orders
        for i in range(5):
            symbol = random.choice(["AAPL", "MSFT", "GOOG", "AMZN"])
            quantity = random.randint(10, 100)
            text = f"Buy {quantity} shares of {symbol}"
            command = {
                "type": "buy_order",
                "symbol": symbol,
                "quantity": quantity,
                "order_type": "market"
            }
            mock_samples.append((f"mock_buy_{i}", text, command))
        
        # Sell orders
        for i in range(5):
            symbol = random.choice(["TSLA", "META", "NFLX", "DIS"])
            quantity = random.randint(10, 100)
            price = random.randint(100, 500)
            text = f"Sell {quantity} shares of {symbol} at {price} dollars"
            command = {
                "type": "sell_order",
                "symbol": symbol,
                "quantity": quantity,
                "order_type": "limit",
                "price": price
            }
            mock_samples.append((f"mock_sell_{i}", text, command))
        
        # Quotes
        for i in range(5):
            symbol = random.choice(["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"])
            text = f"Get quote for {symbol}"
            command = {
                "type": "quote",
                "symbol": symbol
            }
            mock_samples.append((f"mock_quote_{i}", text, command))
        
        # Account commands
        account_commands = [
            ("What is my account balance", {"type": "account_balance"}),
            ("Show my positions", {"type": "positions"}),
            ("Show my open orders", {"type": "open_orders"}),
            ("How much buying power do I have", {"type": "buying_power"})
        ]
        
        for i, (text, command) in enumerate(account_commands):
            mock_samples.append((f"mock_account_{i}", text, command))
        
        return mock_samples
    
    def execute(self):
        """Execute the test scenario."""
        results = {}
        
        for engine in self.engines:
            self.logger.info(f"Testing speech recognition engine: {engine}")
            
            # Set speech recognition engine
            self.voice_command_handler.set_speech_engine(engine)
            
            engine_results = {
                "text_accuracy": [],
                "command_accuracy": [],
                "recognition_times": []
            }
            
            for sample_path, expected_text, expected_command in self.voice_samples:
                try:
                    # Recognize speech
                    start_time = time.time()
                    
                    with self.measure(f"{engine}_recognition"):
                        if isinstance(sample_path, str) and sample_path.startswith("mock_"):
                            # For mock data, simulate recognition with the expected text
                            recognized_text = expected_text
                        else:
                            # Process actual voice sample
                            recognized_text = self.voice_command_handler.recognize_speech(sample_path)
                    
                    recognition_time = time.time() - start_time
                    engine_results["recognition_times"].append(recognition_time * 1000)  # Convert to ms
                    
                    # Parse command
                    with self.measure(f"{engine}_command_processing"):
                        parsed_command = self.command_processor.parse_command(recognized_text)
                    
                    # Calculate text similarity score (simplified)
                    text_similarity = self._calculate_text_similarity(expected_text, recognized_text)
                    engine_results["text_accuracy"].append(text_similarity)
                    
                    # Calculate command match score
                    command_match = self._calculate_command_match(expected_command, parsed_command)
                    engine_results["command_accuracy"].append(command_match)
                    
                    self.logger.debug(f"Sample: {os.path.basename(str(sample_path))}")
                    self.logger.debug(f"Expected: '{expected_text}'")
                    self.logger.debug(f"Recognized: '{recognized_text}'")
                    self.logger.debug(f"Text Similarity: {text_similarity:.2f}")
                    self.logger.debug(f"Command Match: {command_match:.2f}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing sample {sample_path}: {str(e)}")
                    continue
            
            # Calculate average metrics for this engine
            avg_text_accuracy = np.mean(engine_results["text_accuracy"]) if engine_results["text_accuracy"] else 0
            avg_command_accuracy = np.mean(engine_results["command_accuracy"]) if engine_results["command_accuracy"] else 0
            avg_recognition_time = np.mean(engine_results["recognition_times"]) if engine_results["recognition_times"] else 0
            
            self.logger.info(f"Engine: {engine}, Text Accuracy: {avg_text_accuracy:.2%}, "
                           f"Command Accuracy: {avg_command_accuracy:.2%}, "
                           f"Avg Recognition Time: {avg_recognition_time:.2f}ms")
            
            # Record metrics
            self.metrics.set_gauge(f"{engine}_text_accuracy", avg_text_accuracy)
            self.metrics.set_gauge(f"{engine}_command_accuracy", avg_command_accuracy)
            self.metrics.set_gauge(f"{engine}_recognition_time", avg_recognition_time)
            
            results[engine] = {
                "text_accuracy": avg_text_accuracy,
                "command_accuracy": avg_command_accuracy,
                "recognition_time": avg_recognition_time
            }
        
        return True
    
    def _calculate_text_similarity(self, expected, actual):
        """Calculate similarity between expected and actual text.
        
        This is a simplified implementation. In a real system, you might
        use more sophisticated NLP techniques.
        
        Args:
            expected: Expected text string.
            actual: Actual recognized text string.
            
        Returns:
            float: Similarity score between 0 and 1.
        """
        if not expected or not actual:
            return 0
            
        # Convert to lowercase and split into words
        expected_words = expected.lower().split()
        actual_words = actual.lower().split()
        
        # Count matching words
        matches = sum(1 for word in actual_words if word in expected_words)
        
        # Calculate similarity score
        score = matches / max(len(expected_words), len(actual_words))
        
        return score
    
    def _calculate_command_match(self, expected_command, parsed_command):
        """Calculate match score between expected and parsed commands.
        
        Args:
            expected_command: Expected command dictionary.
            parsed_command: Parsed command dictionary.
            
        Returns:
            float: Match score between 0 and 1.
        """
        if not expected_command or not parsed_command:
            return 0
            
        # Check command type
        if expected_command.get("type") != parsed_command.get("type"):
            return 0
            
        # Count matching fields
        matches = 0
        total_fields = 0
        
        for key, value in expected_command.items():
            total_fields += 1
            
            if key in parsed_command:
                if isinstance(value, (int, float)) and isinstance(parsed_command[key], (int, float)):
                    # For numeric values, allow some tolerance
                    if abs(value - parsed_command[key]) / max(1, value) < 0.05:  # 5% tolerance
                        matches += 1
                elif str(value).lower() == str(parsed_command[key]).lower():
                    matches += 1
        
        # Calculate match score
        score = matches / total_fields if total_fields > 0 else 0
        
        return score
    
    def cleanup(self):
        """Clean up after the test."""
        self.logger.info("Cleaning up VoiceCommandAccuracyTest")
        return True 