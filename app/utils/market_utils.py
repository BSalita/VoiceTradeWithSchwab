"""
Market Utilities - Helper functions for market-related operations
"""

import logging
import datetime
import pytz
from typing import Optional, Tuple
from ..config import config

logger = logging.getLogger(__name__)

# Eastern timezone for US markets
eastern = pytz.timezone('US/Eastern')

def get_current_market_status() -> Tuple[bool, bool, datetime.datetime]:
    """
    Get the current market status (regular or extended hours)
    
    Returns:
        Tuple[bool, bool, datetime.datetime]: 
            (is_regular_hours, is_extended_hours, current_time)
    """
    # Get current time in Eastern timezone
    now = datetime.datetime.now(eastern)
    current_time = now.time()
    
    # Parse market hours from config
    regular_open = datetime.time.fromisoformat(config.REGULAR_MARKET_OPEN)
    regular_close = datetime.time.fromisoformat(config.REGULAR_MARKET_CLOSE)
    extended_open = datetime.time.fromisoformat(config.EXTENDED_HOURS_OPEN)
    extended_close = datetime.time.fromisoformat(config.EXTENDED_HOURS_CLOSE)
    
    # Check if today is a weekday (0=Monday, 4=Friday, 5=Saturday, 6=Sunday)
    is_weekday = now.weekday() < 5
    
    # Check if market is open
    is_regular_hours = (
        is_weekday and 
        regular_open <= current_time < regular_close
    )
    
    is_extended_hours = (
        is_weekday and 
        not is_regular_hours and
        extended_open <= current_time < extended_close
    )
    
    return is_regular_hours, is_extended_hours, now

def is_market_open(include_extended: bool = True) -> bool:
    """
    Check if the market is currently open
    
    Args:
        include_extended (bool): Whether to include extended hours
        
    Returns:
        bool: True if market is open, False otherwise
    """
    is_regular, is_extended, _ = get_current_market_status()
    
    if include_extended:
        return is_regular or is_extended
    else:
        return is_regular

def get_time_to_market_open() -> Optional[datetime.timedelta]:
    """
    Get time until market opens
    
    Returns:
        Optional[datetime.timedelta]: Time until market opens or None if already open
    """
    if is_market_open(include_extended=False):
        return None
        
    now = datetime.datetime.now(eastern)
    
    # If it's weekend, calculate time to Monday
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        days_to_monday = 7 - now.weekday()
        next_open = now.replace(
            hour=int(config.REGULAR_MARKET_OPEN.split(':')[0]),
            minute=int(config.REGULAR_MARKET_OPEN.split(':')[1]),
            second=0,
            microsecond=0
        ) + datetime.timedelta(days=days_to_monday)
        return next_open - now
    
    # If it's before market open today
    regular_open = datetime.time.fromisoformat(config.REGULAR_MARKET_OPEN)
    current_time = now.time()
    
    if current_time < regular_open:
        next_open = now.replace(
            hour=regular_open.hour,
            minute=regular_open.minute,
            second=0,
            microsecond=0
        )
        return next_open - now
        
    # If it's after market close, calculate time to next day
    next_open = now.replace(
        hour=int(config.REGULAR_MARKET_OPEN.split(':')[0]),
        minute=int(config.REGULAR_MARKET_OPEN.split(':')[1]),
        second=0,
        microsecond=0
    ) + datetime.timedelta(days=1)
    
    return next_open - now

def format_price(price: float) -> str:
    """
    Format a price with 2 decimal places and dollar sign
    
    Args:
        price (float): Price to format
        
    Returns:
        str: Formatted price string
    """
    return f"${price:.2f}"

def calculate_profit_loss(buy_price: float, sell_price: float, 
                         quantity: int) -> Tuple[float, float]:
    """
    Calculate profit/loss for a trade
    
    Args:
        buy_price (float): Purchase price
        sell_price (float): Sell price
        quantity (int): Number of shares
        
    Returns:
        Tuple[float, float]: (profit_loss_amount, profit_loss_percent)
    """
    pl_amount = (sell_price - buy_price) * quantity
    pl_percent = ((sell_price / buy_price) - 1) * 100
    
    return pl_amount, pl_percent 