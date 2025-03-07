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
    strategy_type: str = Field(..., description="Type of strategy: basic, ladder, oscillating, highlow, oto_ladder")
    symbol: str = Field(..., description="Stock symbol")
    quantity: int = Field(..., description="Number of shares", gt=0)
    price_range: Optional[float] = Field(None, description="Price range for oscillating strategies")
    range_type: Optional[str] = Field(None, description="Range type: $ or %")
    steps: Optional[int] = Field(None, description="Steps for ladder strategy")
    start_price: Optional[float] = Field(None, description="Start price for ladder strategy")
    end_price: Optional[float] = Field(None, description="End price for ladder strategy")
    standard_deviation: Optional[float] = Field(None, description="Standard deviation for normal distribution")
    initial_shares: Optional[int] = Field(None, description="Initial shares for oto_ladder strategy")
    step: Optional[float] = Field(None, description="Step size for oto_ladder strategy")
    session: str = Field("REGULAR", description="Trading session: REGULAR, EXTENDED, ALL")
    duration: str = Field("DAY", description="Order duration: DAY, GTC")


class BacktestRequest(BaseModel):
    """Backtest request model"""
    strategy_name: str = Field(..., description="Name of the strategy to backtest")
    symbol: str = Field(..., description="Stock symbol to backtest")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    initial_capital: float = Field(10000.0, description="Initial capital for the backtest")
    trading_session: str = Field("REGULAR", description="Trading session: REGULAR, EXTENDED")
    strategy_params: Optional[Dict[str, Any]] = Field(None, description="Additional parameters for the strategy")


class CompareStrategiesRequest(BaseModel):
    """Compare strategies request model"""
    strategies: List[str] = Field(..., description="List of strategy names to compare")
    symbol: str = Field(..., description="Stock symbol to backtest")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    initial_capital: float = Field(10000.0, description="Initial capital for each backtest")
    trading_session: str = Field("REGULAR", description="Trading session: REGULAR, EXTENDED")
    strategy_params: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Parameters for each strategy, keyed by strategy name")


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


class TradeMetrics(BaseModel):
    """Trade metrics model"""
    total_trades: int = Field(0, description="Total number of trades")
    winning_trades: int = Field(0, description="Number of winning trades")
    losing_trades: int = Field(0, description="Number of losing trades")
    win_rate: float = Field(0.0, description="Win rate percentage")
    average_win: float = Field(0.0, description="Average win amount")
    average_loss: float = Field(0.0, description="Average loss amount")
    profit_factor: float = Field(0.0, description="Profit factor")
    expectancy: float = Field(0.0, description="Expected return per trade")


class BacktestSummary(BaseModel):
    """Backtest summary model"""
    backtest_id: str = Field(..., description="Backtest ID")
    strategy_name: str = Field(..., description="Name of the strategy")
    symbol: str = Field(..., description="Stock symbol")
    period: str = Field(..., description="Backtest period")
    initial_capital: float = Field(..., description="Initial capital")
    final_capital: float = Field(..., description="Final capital")
    total_return: str = Field(..., description="Total return percentage")
    max_drawdown: str = Field(..., description="Maximum drawdown percentage")
    sharpe_ratio: str = Field(..., description="Sharpe ratio")
    win_rate: str = Field(..., description="Win rate percentage")
    total_trades: int = Field(..., description="Total number of trades")


class BacktestResponse(BaseResponse):
    """Backtest response model"""
    backtest_id: Optional[str] = Field(None, description="Backtest ID")
    summary: Optional[BacktestSummary] = Field(None, description="Backtest summary")
    metrics: Optional[TradeMetrics] = Field(None, description="Trade metrics")
    trades: List[Dict[str, Any]] = Field(default_factory=list, description="List of trades")
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list, description="Equity curve data points")


class StrategyComparisonMetrics(BaseModel):
    """Strategy comparison metrics for a single strategy"""
    total_return: float = Field(..., description="Total return percentage")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    win_rate: float = Field(..., description="Win rate percentage")
    profit_factor: float = Field(..., description="Profit factor")
    total_trades: int = Field(..., description="Total number of trades")


class StrategyComparisonResponse(BaseResponse):
    """Strategy comparison response model"""
    backtest_period: Dict[str, Any] = Field(..., description="Backtest period information")
    metrics_comparison: Dict[str, StrategyComparisonMetrics] = Field(..., description="Metrics for each strategy")
    overall_ranking: List[str] = Field(..., description="Strategies ranked from best to worst")
    best_strategy: str = Field(..., description="Name of the best performing strategy")
    metric_rankings: Dict[str, Dict[str, int]] = Field(..., description="Ranking for each metric and strategy")


class BacktestsResponse(BaseResponse):
    """List of backtests response model"""
    backtests: List[BacktestSummary] = Field(default_factory=list, description="List of backtest summaries")
    count: int = Field(0, description="Number of backtests") 