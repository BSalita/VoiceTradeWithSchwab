"""
OTO Ladder Strategy - Implementation of a step-based strategy with one-triggers-other (OTO) order chains

This strategy will:
1. Sell 5% of original shares at defined price steps 
2. Trigger a buy back at 2x step lower from the sale price
3. Trigger a take profit at the next step higher from the buy-back price
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import os
import tempfile
import time
from datetime import datetime
from ..strategies.base_strategy import BaseStrategy
from ..models.order import OrderDuration, TradingSession

logger = logging.getLogger(__name__)

class OTOLadderStrategy(BaseStrategy):
    """
    Implementation of a step-based trading strategy using one-triggers-other (OTO) order chains
    """
    
    def __init__(self):
        """Initialize the strategy"""
        super().__init__()
        self.strategy_name = "OTOLadderStrategy"
        self.oto_ladder_code = self._generate_oto_ladder_code()
        
    def _generate_oto_ladder_code(self) -> str:
        """
        Generate the OTO Ladder code for this strategy
        
        Returns:
            str: OTO Ladder code
        """
        return """
# Title: One-Triggers-Other Step Strategy with Extended Hours
# Description: Sells 5% at price steps with EXTO TIF, triggers buy orders 2x step lower, which trigger take profits at the next step higher

# Input parameters
input symbol = {default "SPY", type = string};
input startPrice = {default 400.0, type = float};
input step = {default 5.0, type = float};
input initialShares = {default 100, type = integer}; # Starting number of shares
input debugMode = {default false, type = yes_no}; # Show detailed debugging info

# Constants
def SELL_PERCENTAGE = 5.0; # Percentage of initial shares to sell at each step
def sharesToSell = Round(initialShares * (SELL_PERCENTAGE / 100), 0);
def TIF = "EXTO"; # Time In Force: Extended Hours

# Price tracking
def currentPrice = close;

# Track the step level
def currentStepLevel = if currentPrice >= startPrice then floor((currentPrice - startPrice) / step) else -1;

# Record the highest step level where we've sold
rec highestStepLevelSold = if !IsNaN(highestStepLevelSold[1]) then 
                            max(highestStepLevelSold[1], 
                                if currentStepLevel > highestStepLevelSold[1] and currentPrice >= startPrice 
                                then currentStepLevel else highestStepLevelSold[1])
                           else -1;

# Determine if this is a new step level we haven't sold at yet
def isNewStepToSell = currentStepLevel > highestStepLevelSold[1] and currentPrice >= startPrice;

# Calculate price levels for the OTO orders
def sellPrice = if isNewStepToSell then startPrice + (currentStepLevel * step) else Double.NaN;
def buyBackPrice = if isNewStepToSell then sellPrice - (2 * step) else Double.NaN;
def takeProfitPrice = if isNewStepToSell then sellPrice + step else Double.NaN;

# Order management - The OTO chain
# First leg: Sell order
def sellSignal = isNewStepToSell;

# Track active OTO orders
rec activeOtoOrders = if !IsNaN(activeOtoOrders[1]) then
                        if sellSignal then activeOtoOrders[1] + 1
                        else activeOtoOrders[1]
                      else 0;

# Debug information
AddLabel(debugMode, "Current price: " + currentPrice, Color.WHITE);
AddLabel(debugMode, "Current step level: " + currentStepLevel, Color.WHITE);
AddLabel(debugMode, "Highest step sold: " + highestStepLevelSold, Color.WHITE);
AddLabel(debugMode, "Active OTO orders: " + activeOtoOrders, Color.WHITE);
AddLabel(debugMode, "TIF Setting: " + TIF, Color.WHITE);

# Main strategy outputs and signals
AddLabel(true, "Current Step: " + currentStepLevel, Color.CYAN);
AddLabel(true, "Shares to sell per step: " + sharesToSell + " (" + SELL_PERCENTAGE + "%)", Color.YELLOW);
AddLabel(true, "Time In Force: " + TIF, Color.MAGENTA);

# Order alerts with OTO instructions and EXTO TIF
alert(sellSignal, 
      "SELL " + sharesToSell + " shares at $" + sellPrice + " [TIF: " + TIF + "] " +
      "with OTO BUY " + sharesToSell + " at $" + buyBackPrice + " [TIF: " + TIF + "] " +
      "with OTO SELL " + sharesToSell + " at $" + takeProfitPrice + " [TIF: " + TIF + "]", 
      Alert.BAR, Sound.Ding);

# Visualization
# Plot the sell signals
plot SellSignal = if sellSignal then currentPrice else Double.NaN;
SellSignal.SetPaintingStrategy(PaintingStrategy.ARROW_DOWN);
SellSignal.SetDefaultColor(Color.RED);
SellSignal.SetLineWeight(3);

# Plot the OTO chain prices
plot BuyBackLevel = if sellSignal then buyBackPrice else Double.NaN;
plot TakeProfitLevel = if sellSignal then takeProfitPrice else Double.NaN;

BuyBackLevel.SetDefaultColor(Color.GREEN);
BuyBackLevel.SetPaintingStrategy(PaintingStrategy.DASHES);
BuyBackLevel.SetLineWeight(2);

TakeProfitLevel.SetDefaultColor(Color.BLUE);
TakeProfitLevel.SetPaintingStrategy(PaintingStrategy.DASHES);
TakeProfitLevel.SetLineWeight(2);

# Plot step lines for reference
plot StepLine = startPrice + (HighestAll(currentStepLevel) * step);
StepLine.SetDefaultColor(Color.GRAY);
StepLine.SetPaintingStrategy(PaintingStrategy.DASHES);
StepLine.SetLineWeight(1);

# Add text describing the OTO chain
AddChartBubble(sellSignal, currentPrice, 
               "SELL → BUY (" + (sellPrice - buyBackPrice) + " lower) → TP (" + (takeProfitPrice - buyBackPrice) + " higher)" +
               "\nTIF: " + TIF,
               Color.WHITE, 0);
"""
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the trading strategy
        
        Args:
            symbol (str): Trading symbol (e.g., "SPY")
            start_price (float): Starting price level for the strategy
            step (float): Price step increment that triggers sells
            initial_shares (int): Initial number of shares
            price_target (float, optional): Price at which to terminate the strategy. Default: None (no target)
            **kwargs: Additional strategy parameters
            
        Returns:
            Dict[str, Any]: Result of strategy execution including OTO Ladder code
        """
        symbol = kwargs.get('symbol', 'SPY')
        start_price = kwargs.get('start_price', 0.0)
        step = kwargs.get('step', 5.0)
        initial_shares = kwargs.get('initial_shares', 100)
        price_target = kwargs.get('price_target', None)
        
        logger.info(f"Executing {self.strategy_name} for {symbol} with start price: {start_price}, step: {step}, initial shares: {initial_shares}, price target: {price_target}")
        
        # Update the strategy configuration
        self.config.update({
            'symbol': symbol,
            'start_price': start_price,
            'step': step,
            'initial_shares': initial_shares,
            'price_target': price_target,
            'sell_percentage': 5.0,
            'tif': 'EXTO'
        })
        
        # Calculate strategy parameters
        shares_to_sell = int(initial_shares * 0.05)  # 5% of initial shares
        current_price = self._get_current_price(symbol)
        
        if current_price <= 0:
            logger.error(f"Failed to get current price for {symbol}")
            return {
                'success': False,
                'error': f"Failed to get current price for {symbol}",
                'oto_ladder_code': self.oto_ladder_code
            }
        
        # Check if price target has been reached
        if price_target is not None and current_price >= price_target:
            logger.info(f"Price target reached: current price {current_price} >= target {price_target}. Terminating strategy.")
            return {
                'success': True,
                'strategy': self.strategy_name,
                'symbol': symbol,
                'target_reached': True,
                'current_price': current_price,
                'price_target': price_target,
                'message': f"Price target reached: {current_price} >= {price_target}. Strategy terminated.",
                'oto_ladder_code': self.oto_ladder_code,
                'timestamp': datetime.now().isoformat()
            }
        
        if start_price <= 0:
            # If no start price is provided, use current price
            start_price = current_price
            logger.info(f"Using current price as start price: {start_price}")
            self.config['start_price'] = start_price
        
        # Calculate current step level
        current_step_level = max(0, int((current_price - start_price) / step)) if current_price >= start_price else -1
        
        # Generate OTO Ladder file
        oto_ladder_file = self._save_oto_ladder_to_file(symbol)
        
        result = {
            'success': True,
            'strategy': self.strategy_name,
            'symbol': symbol,
            'start_price': start_price,
            'step': step,
            'current_price': current_price,
            'current_step_level': current_step_level,
            'initial_shares': initial_shares,
            'shares_to_sell': shares_to_sell,
            'price_target': price_target,
            'oto_ladder_file': oto_ladder_file,
            'oto_ladder_code': self.oto_ladder_code,
            'next_sell_price': start_price + ((current_step_level + 1) * step) if current_step_level >= 0 else start_price,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Strategy execution result: {result}")
        return result
    
    def _get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            float: Current price, or 0 if not available
        """
        try:
            # Attempt to get the price from the API client
            quote_response = self.api_client.get_quote(symbol)
            if quote_response and 'success' in quote_response and quote_response['success']:
                price = quote_response.get('last_price', 0.0)
                return float(price)
            return 0.0
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return 0.0
    
    def _save_oto_ladder_to_file(self, symbol: str) -> str:
        """
        Save the OTO Ladder code to a file
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            str: Path to the saved file
        """
        try:
            # Create a directory for OTO Ladder files if it doesn't exist
            script_dir = os.path.join(os.getcwd(), 'oto_ladder')
            os.makedirs(script_dir, exist_ok=True)
            
            # Create a filename with timestamp
            timestamp = int(time.time())
            filename = f"{symbol}_OTOLadderStrategy_{timestamp}.ts"
            filepath = os.path.join(script_dir, filename)
            
            # Write the OTO Ladder code to the file
            with open(filepath, 'w') as f:
                f.write(self.oto_ladder_code)
            
            logger.info(f"Saved OTO Ladder code to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving OTO Ladder code: {str(e)}")
            return ""
    
    def place_oto_order_chain(self, symbol: str, sell_quantity: int, sell_price: float, 
                             buy_price: float, take_profit_price: float) -> Dict[str, Any]:
        """
        Place an OTO (one-triggers-other) order chain
        
        Args:
            symbol (str): Trading symbol
            sell_quantity (int): Quantity to sell in the first order
            sell_price (float): Price for the first sell order
            buy_price (float): Price for the buy order (triggered by first sell)
            take_profit_price (float): Price for the take profit sell (triggered by buy)
            
        Returns:
            Dict[str, Any]: Result of order placement
        """
        logger.info(f"Placing OTO order chain for {symbol}: SELL {sell_quantity} @ {sell_price} -> BUY {sell_quantity} @ {buy_price} -> SELL {sell_quantity} @ {take_profit_price}")
        
        try:
            # This is a placeholder for the actual OTO order chain implementation
            # In a real system, you would use the broker's API to create this chain
            
            # For demonstration, we'll create a result dictionary
            result = {
                'success': True,
                'message': f"OTO order chain created for {symbol}",
                'details': {
                    'first_order': {
                        'type': 'SELL',
                        'quantity': sell_quantity,
                        'price': sell_price,
                        'tif': 'EXTO'
                    },
                    'second_order': {
                        'type': 'BUY',
                        'quantity': sell_quantity,
                        'price': buy_price,
                        'tif': 'EXTO'
                    },
                    'third_order': {
                        'type': 'SELL',
                        'quantity': sell_quantity,
                        'price': take_profit_price,
                        'tif': 'EXTO'
                    }
                }
            }
            
            return result
        except Exception as e:
            logger.error(f"Error placing OTO order chain: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the strategy configuration
        
        Returns:
            Dict[str, Any]: Validation result
        """
        required_fields = ['symbol', 'start_price', 'step', 'initial_shares']
        missing_fields = [field for field in required_fields if field not in self.config]
        
        if missing_fields:
            return {
                'valid': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        # Validate values
        if self.config['step'] <= 0:
            return {
                'valid': False,
                'error': "Step must be greater than 0"
            }
        
        if self.config['initial_shares'] <= 0:
            return {
                'valid': False,
                'error': "Initial shares must be greater than 0"
            }
        
        # Validate price_target if provided
        if 'price_target' in self.config and self.config['price_target'] is not None:
            if not isinstance(self.config['price_target'], (int, float)) or self.config['price_target'] <= 0:
                return {
                    'valid': False,
                    'error': "Price target must be a positive number"
                }
            
            # Price target should be greater than start price to be meaningful
            if 'start_price' in self.config and self.config['start_price'] > 0 and self.config['price_target'] <= self.config['start_price']:
                return {
                    'valid': False,
                    'error': "Price target should be greater than start price"
                }
        
        return {
            'valid': True
        } 