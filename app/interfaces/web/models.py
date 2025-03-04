"""
API Models - Pydantic models for API requests and responses
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


# Request Models

class OrderRequest(BaseModel):
    """Order request model"""
    symbol: str = Field(..., description="Stock symbol")
    quantity: int = Field(..., description="Number of shares", gt=0)
    order_type: str = Field(..., description="Order type: MARKET, LIMIT, STOP, STOP_LIMIT")
    side: str = Field(..., description="Order side: BUY, SELL")
    price: Optional[float] = Field(None, description="Price for limit orders")
    stop_price: Optional[float] = Field(None, description="Stop price for stop orders") 
    session: str = Field("REGULAR", description="Trading session: REGULAR, EXTENDED, ALL")
    duration: str = Field("DAY", description="Order duration: DAY, GTC, GTD, FOK, IOC")
    strategy: Optional[str] = Field(None, description="Strategy that placed the order")


class StrategyRequest(BaseModel):
    """Strategy request model"""
    strategy_type: str = Field(..., description="Type of strategy: basic, ladder, oscillating, highlow")
    symbol: str = Field(..., description="Stock symbol")
    quantity: int = Field(..., description="Number of shares", gt=0)
    price_range: Optional[float] = Field(None, description="Price range for oscillating strategies")
    range_type: Optional[str] = Field(None, description="Range type: $ or %")
    steps: Optional[int] = Field(None, description="Steps for ladder strategy")
    start_price: Optional[float] = Field(None, description="Start price for ladder strategy")
    end_price: Optional[float] = Field(None, description="End price for ladder strategy")
    standard_deviation: Optional[float] = Field(None, description="Standard deviation for normal distribution")
    session: str = Field("REGULAR", description="Trading session: REGULAR, EXTENDED, ALL")
    duration: str = Field("DAY", description="Order duration: DAY, GTC")


# Response Models

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = Field(..., description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Optional message")
    error: Optional[str] = Field(None, description="Error message if success is False")


class HealthResponse(BaseResponse):
    """Health check response"""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")


class OrderResponse(BaseResponse):
    """Order response model"""
    order: Optional[Dict[str, Any]] = Field(None, description="Order details")
    symbol: Optional[str] = Field(None, description="Stock symbol")
    side: Optional[str] = Field(None, description="Order side: BUY, SELL")
    quantity: Optional[int] = Field(None, description="Number of shares")
    price: Optional[float] = Field(None, description="Order price")
    order_id: Optional[str] = Field(None, description="Order ID")


class OrdersResponse(BaseResponse):
    """Orders list response model"""
    orders: List[Dict[str, Any]] = Field(default_factory=list, description="List of orders")
    count: int = Field(0, description="Number of orders")


class QuoteResponse(BaseResponse):
    """Quote response model"""
    symbol: Optional[str] = Field(None, description="Stock symbol")
    quote: Optional[Dict[str, Any]] = Field(None, description="Quote details")


class QuotesResponse(BaseResponse):
    """Quotes list response model"""
    quotes: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Quotes by symbol")


class AccountResponse(BaseResponse):
    """Account information response model"""
    account: Optional[Dict[str, Any]] = Field(None, description="Account details")
    positions: List[Dict[str, Any]] = Field(default_factory=list, description="List of positions")
    balances: Dict[str, Union[float, int]] = Field(default_factory=dict, description="Account balances")


class StrategyResponse(BaseResponse):
    """Strategy response model"""
    strategy_key: Optional[str] = Field(None, description="Strategy key")
    strategy_type: Optional[str] = Field(None, description="Strategy type")
    symbol: Optional[str] = Field(None, description="Stock symbol")
    status: Optional[Dict[str, Any]] = Field(None, description="Strategy status")


class StrategiesResponse(BaseResponse):
    """Strategies list response model"""
    strategies: List[Dict[str, Any]] = Field(default_factory=list, description="List of strategies")
    count: int = Field(0, description="Number of strategies")


class TradeResponse(BaseModel):
    """Trade model"""
    id: str = Field(..., description="Trade ID")
    dateTime: str = Field(..., description="Trade date and time")
    symbol: str = Field(..., description="Stock symbol")
    side: str = Field(..., description="Trade side: BUY, SELL")
    quantity: int = Field(..., description="Number of shares")
    price: float = Field(..., description="Trade price")
    total: float = Field(..., description="Total trade value")
    strategy: Optional[str] = Field(None, description="Strategy used")
    order_id: Optional[str] = Field(None, description="Order ID")


class TradeHistoryResponse(BaseResponse):
    """Trade history response model"""
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="List of trades")
    count: int = Field(0, description="Number of trades")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")


class ExportResponse(BaseResponse):
    """Export response model"""
    filename: str = Field(..., description="Export filename") 