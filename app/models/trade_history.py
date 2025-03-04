"""
Trade History - Tracks and manages trade history
"""

import os
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..config import config

logger = logging.getLogger(__name__)

class TradeHistory:
    """
    Tracks and manages trade history for the application
    """
    
    def __init__(self):
        """Initialize the trade history tracker"""
        self.trades = []
        self.history_file = os.path.join(config.LOGS_DIR, 'trade_history.csv')
        self._load_history()
        logger.info("Trade history initialized")
    
    def add_trade(self, trade_data: Dict[str, Any]) -> None:
        """
        Add a trade to the history
        
        Args:
            trade_data (Dict[str, Any]): Trade data including:
                - symbol: Stock symbol
                - side: BUY/SELL
                - quantity: Number of shares
                - price: Execution price
                - time: Trade timestamp (optional, defaults to now)
                - order_id: Order ID
                - strategy: Strategy name (if applicable)
                - trading_mode: LIVE/PAPER/MOCK
        """
        # Add timestamp if not provided
        if 'time' not in trade_data:
            trade_data['time'] = datetime.now()
        
        # Add to in-memory list
        self.trades.append(trade_data)
        
        # Write to CSV file
        self._append_to_csv(trade_data)
        
        logger.debug(f"Added trade to history: {trade_data}")
    
    def get_trades(self, symbol: Optional[str] = None, 
                  side: Optional[str] = None,
                  strategy: Optional[str] = None,
                  limit: int = 100,
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get trades from the history with optional filtering
        
        Args:
            symbol (Optional[str]): Filter by symbol
            side (Optional[str]): Filter by side (BUY/SELL)
            strategy (Optional[str]): Filter by strategy name
            limit (int): Maximum number of trades to return
            start_time (Optional[datetime]): Filter trades after this time
            end_time (Optional[datetime]): Filter trades before this time
            
        Returns:
            List[Dict[str, Any]]: Filtered trade history
        """
        filtered_trades = self.trades
        
        # Apply filters
        if symbol:
            filtered_trades = [t for t in filtered_trades if t.get('symbol') == symbol.upper()]
        
        if side:
            filtered_trades = [t for t in filtered_trades if t.get('side') == side.upper()]
        
        if strategy:
            filtered_trades = [t for t in filtered_trades if t.get('strategy') == strategy]
        
        if start_time:
            filtered_trades = [t for t in filtered_trades if t.get('time') >= start_time]
        
        if end_time:
            filtered_trades = [t for t in filtered_trades if t.get('time') <= end_time]
        
        # Sort by time (newest first) and limit
        filtered_trades = sorted(filtered_trades, key=lambda t: t.get('time', datetime.min), reverse=True)
        
        return filtered_trades[:limit]
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """
        Export trade history to CSV file
        
        Args:
            filename (Optional[str]): Output filename (optional)
            
        Returns:
            str: Path to exported CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(config.LOGS_DIR, f"trade_history_{timestamp}.csv")
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['time', 'symbol', 'side', 'quantity', 'price', 'order_id', 
                         'strategy', 'trading_mode', 'value', 'notes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for trade in self.trades:
                # Calculate trade value
                price = trade.get('price')
                # Handle None price (common with market orders where price isn't known at submission)
                price = float(price) if price is not None else 0.0
                quantity = int(trade.get('quantity', 0))
                value = price * quantity
                
                # Prepare row with consistent fields
                row = {
                    'time': trade.get('time', '').isoformat() if isinstance(trade.get('time'), datetime) else trade.get('time', ''),
                    'symbol': trade.get('symbol', ''),
                    'side': trade.get('side', ''),
                    'quantity': trade.get('quantity', ''),
                    'price': price,  # Use the safely converted price
                    'order_id': trade.get('order_id', ''),
                    'strategy': trade.get('strategy', ''),
                    'trading_mode': trade.get('trading_mode', ''),
                    'value': value,
                    'notes': trade.get('notes', '')
                }
                writer.writerow(row)
        
        logger.info(f"Exported trade history to {filename}")
        return filename
    
    def clear_history(self) -> None:
        """Clear the trade history"""
        self.trades = []
        
        # Create empty history file
        with open(self.history_file, 'w', newline='') as csvfile:
            fieldnames = ['time', 'symbol', 'side', 'quantity', 'price', 'order_id', 
                         'strategy', 'trading_mode', 'value', 'notes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        
        logger.info("Trade history cleared")
    
    def _load_history(self) -> None:
        """Load trade history from CSV file if it exists"""
        if not os.path.exists(self.history_file):
            # Create empty history file
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', newline='') as csvfile:
                fieldnames = ['time', 'symbol', 'side', 'quantity', 'price', 'order_id', 
                             'strategy', 'trading_mode', 'value', 'notes']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            return
        
        try:
            with open(self.history_file, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Convert string timestamp to datetime
                    if 'time' in row and row['time']:
                        try:
                            row['time'] = datetime.fromisoformat(row['time'])
                        except ValueError:
                            row['time'] = datetime.now()  # Fallback to current time if parse fails
                    
                    # Convert numeric fields
                    if 'price' in row and row['price']:
                        try:
                            row['price'] = float(row['price'])
                        except ValueError:
                            row['price'] = 0.0
                    
                    if 'quantity' in row and row['quantity']:
                        try:
                            row['quantity'] = int(row['quantity'])
                        except ValueError:
                            row['quantity'] = 0
                    
                    self.trades.append(row)
                
            logger.info(f"Loaded {len(self.trades)} trades from history file")
            
        except Exception as e:
            logger.error(f"Error loading trade history: {str(e)}")
    
    def _append_to_csv(self, trade_data: Dict[str, Any]) -> None:
        """
        Append a trade to the CSV history file
        
        Args:
            trade_data (Dict[str, Any]): Trade data to append
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            # Check if file exists to determine if we need to write header
            file_exists = os.path.exists(self.history_file)
            
            with open(self.history_file, 'a', newline='') as csvfile:
                fieldnames = ['time', 'symbol', 'side', 'quantity', 'price', 'order_id', 
                             'strategy', 'trading_mode', 'value', 'notes']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Calculate trade value - safely handle None values
                price = 0.0
                if trade_data.get('price') is not None:
                    try:
                        price = float(trade_data.get('price', 0))
                    except (ValueError, TypeError):
                        price = 0.0
                
                quantity = 0
                if trade_data.get('quantity') is not None:
                    try:
                        quantity = int(trade_data.get('quantity', 0))
                    except (ValueError, TypeError):
                        quantity = 0
                
                value = price * quantity
                
                # Prepare row with consistent fields
                row = {
                    'time': trade_data.get('time', '').isoformat() if isinstance(trade_data.get('time'), datetime) else trade_data.get('time', ''),
                    'symbol': trade_data.get('symbol', ''),
                    'side': trade_data.get('side', ''),
                    'quantity': trade_data.get('quantity', ''),
                    'price': trade_data.get('price', ''),
                    'order_id': trade_data.get('order_id', ''),
                    'strategy': trade_data.get('strategy', ''),
                    'trading_mode': trade_data.get('trading_mode', ''),
                    'value': value,
                    'notes': trade_data.get('notes', '')
                }
                writer.writerow(row)
                
        except Exception as e:
            logger.error(f"Error appending trade to history file: {str(e)}") 