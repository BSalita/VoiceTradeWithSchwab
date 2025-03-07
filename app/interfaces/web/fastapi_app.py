"""
FastAPI Application - FastAPI-based REST API for trading application
"""

import logging
import os
from typing import List, Dict, Any, Optional, Union
from fastapi import FastAPI, Query, Path, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import app

from .models import (
    # Request models
    OrderRequest, StrategyRequest, BacktestRequest, CompareStrategiesRequest,
    # Response models
    HealthResponse, OrderResponse, OrdersResponse, QuoteResponse, QuotesResponse,
    AccountResponse, StrategyResponse, StrategiesResponse, TradeHistoryResponse,
    ExportResponse, BacktestResponse, StrategyComparisonResponse, BacktestsResponse
)
from ...services import ServiceRegistry, get_service
from ...models.order import TradingSession

logger = logging.getLogger(__name__)

def create_fastapi_app() -> FastAPI:
    """
    Create and configure a FastAPI app
    
    Returns:
        FastAPI app instance
    """
    description = """
    ## AutomatedTrading API
    
    API endpoints for the Automated Trading application.
    
    ### Features
    
    * **Trading:** Place, cancel, and retrieve orders
    * **Market Data:** Get quotes and stream price updates
    * **Strategies:** Start, stop, and monitor trading strategies
    * **Account:** View account information and positions
    * **History:** Retrieve and export trade history
    * **Backtesting:** Backtest strategies and compare their performance
    """
    
    tags_metadata = [
        {
            "name": "health",
            "description": "Health check and system information",
        },
        {
            "name": "account",
            "description": "Account information and positions",
        },
        {
            "name": "orders",
            "description": "Place, cancel, and retrieve orders",
        },
        {
            "name": "quotes",
            "description": "Get quotes and market data",
        },
        {
            "name": "strategies",
            "description": "Start, stop, and monitor trading strategies",
        },
        {
            "name": "history",
            "description": "Retrieve and export trade history",
        },
        {
            "name": "backtesting",
            "description": "Backtest strategies and compare performance",
        }
    ]
    
    # Create FastAPI app
    fastapi_app = FastAPI(
        title="AutomatedTrading API",
        description=description,
        version="1.0.0",
        openapi_tags=tags_metadata
    )
    
    # Add CORS middleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app = fastapi_app
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup"""
        logger.info("Starting FastAPI application")
        
        # Initialize services
        from ...services.service_registry import ServiceRegistry
        ServiceRegistry.initialize_services()
        
        logger.info("Services initialized")
    
    # Service dependencies
    def get_trading_service():
        """Get the trading service dependency"""
        return get_service("trading")
    
    def get_market_data_service():
        """Get the market data service dependency"""
        return get_service("market_data")
    
    def get_strategy_service():
        """Get the strategy service dependency"""
        return get_service("strategies")
    
    def get_backtesting_service():
        """Get the backtesting service dependency"""
        return get_service("backtesting")
    
    # Health check endpoint
    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    async def health_check():
        """
        Health check endpoint
        Returns the API status and version
        """
        return {
            "success": True,
            "message": "API is operational",
            "status": "healthy",
            "version": "1.0.0"
        }

    # Account endpoints
    @app.get("/api/account", response_model=AccountResponse, tags=["account"])
    async def get_account_info(
        trading_service = Depends(get_trading_service)
    ):
        """Get account information, positions, and balances"""
        result = trading_service.get_account_info()
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get account info"))
            
        return result
    
    # Order endpoints
    @app.post("/api/orders", response_model=OrderResponse, tags=["orders"])
    async def place_order(
        order: OrderRequest,
        trading_service = Depends(get_trading_service)
    ):
        """Place a new trading order"""
        result = trading_service.place_order(order.dict(exclude_none=True))
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to place order"))
            
        return result
    
    @app.get("/api/orders", response_model=OrdersResponse, tags=["orders"])
    async def get_orders(
        status: Optional[str] = None,
        trading_service = Depends(get_trading_service)
    ):
        """Get list of orders with optional status filter"""
        result = trading_service.get_orders(status)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get orders"))
            
        return result
    
    @app.delete("/api/orders/{order_id}", response_model=OrderResponse, tags=["orders"])
    async def cancel_order(
        order_id: str = Path(..., description="ID of the order to cancel"),
        trading_service = Depends(get_trading_service)
    ):
        """Cancel an existing order"""
        result = trading_service.cancel_order(order_id)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to cancel order"))
            
        return result
    
    # Quote endpoints
    @app.get("/api/quotes/{symbol}", response_model=QuoteResponse, tags=["quotes"])
    async def get_quote(
        symbol: str = Path(..., description="Stock symbol"),
        market_data_service = Depends(get_market_data_service)
    ):
        """Get quote for a specific symbol"""
        result = market_data_service.get_quote(symbol)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get quote"))
            
        return result
    
    @app.get("/api/quotes", response_model=QuotesResponse, tags=["quotes"])
    async def get_quotes(
        symbols: str = Query(..., description="Comma-separated list of stock symbols"),
        market_data_service = Depends(get_market_data_service)
    ):
        """Get quotes for multiple symbols"""
        symbols_list = [s.strip() for s in symbols.split(",") if s.strip()]
        
        if not symbols_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
            
        result = market_data_service.get_quotes(symbols_list)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get quotes"))
            
        return result
    
    # Strategy endpoints
    @app.post("/api/strategies", response_model=StrategyResponse, tags=["strategies"])
    async def start_strategy(
        strategy: StrategyRequest,
        strategy_service = Depends(get_strategy_service)
    ):
        """Start a trading strategy"""
        strategy_data = strategy.dict(exclude_none=True)
        strategy_type = strategy_data.pop("strategy_type")
        
        result = strategy_service.start_strategy(strategy_type, **strategy_data)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to start strategy"))
            
        return result
    
    @app.get("/api/strategies", response_model=StrategiesResponse, tags=["strategies"])
    async def get_all_strategies(
        strategy_service = Depends(get_strategy_service)
    ):
        """Get status of all active trading strategies"""
        result = strategy_service.get_all_strategies_status()
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get strategies"))
            
        return result
    
    @app.get("/api/strategies/{strategy_key}", response_model=StrategyResponse, tags=["strategies"])
    async def get_strategy_status(
        strategy_key: str = Path(..., description="Key of the strategy"),
        strategy_service = Depends(get_strategy_service)
    ):
        """Get status of a specific trading strategy"""
        result = strategy_service.get_strategy_status(strategy_key)
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail=result.get("error", "Strategy not found"))
            
        return result
    
    @app.delete("/api/strategies/{strategy_key}", response_model=StrategyResponse, tags=["strategies"])
    async def stop_strategy(
        strategy_key: str = Path(..., description="Key of the strategy to stop"),
        strategy_service = Depends(get_strategy_service)
    ):
        """Stop a running trading strategy"""
        result = strategy_service.stop_strategy(strategy_key)
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail=result.get("error", "Failed to stop strategy"))
            
        return result
    
    # Trade history endpoints
    @app.get("/api/history", response_model=TradeHistoryResponse, tags=["history"])
    async def get_trade_history(
        symbol: Optional[str] = None,
        limit: int = 10,
        strategy: Optional[str] = None,
        trading_service = Depends(get_trading_service)
    ):
        """Get trade history with optional filters"""
        result = trading_service.get_trade_history(
            symbol=symbol,
            limit=limit,
            strategy=strategy
        )
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get trade history"))
            
        return result
    
    @app.get("/api/history/export", response_model=ExportResponse, tags=["history"])
    async def export_trade_history(
        filename: Optional[str] = None,
        trading_service = Depends(get_trading_service)
    ):
        """Export trade history to CSV file"""
        result = trading_service.export_trade_history(filename)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to export trade history"))
            
        return result
    
    # Backtesting endpoints
    @app.post("/api/backtest", response_model=BacktestResponse, tags=["backtesting"])
    async def run_backtest(
        backtest: BacktestRequest,
        backtesting_service = Depends(get_backtesting_service)
    ):
        """
        Run a backtest for a trading strategy
        
        - **strategy_name**: Name of the strategy to backtest
        - **symbol**: Stock symbol to backtest
        - **start_date**: Start date in YYYY-MM-DD format
        - **end_date**: End date in YYYY-MM-DD format
        - **initial_capital**: Initial capital for the backtest (default: 10000.0)
        - **trading_session**: Trading session (default: REGULAR)
        - **strategy_params**: Additional parameters for the strategy
        """
        try:
            # Convert trading session string to enum
            if backtest.trading_session == "REGULAR":
                trading_session = TradingSession.REGULAR
            elif backtest.trading_session == "EXTENDED":
                trading_session = TradingSession.EXTENDED
            else:
                trading_session = TradingSession.REGULAR
            
            # Run backtest
            result = backtesting_service.run_backtest(
                strategy_name=backtest.strategy_name,
                symbol=backtest.symbol,
                start_date=backtest.start_date,
                end_date=backtest.end_date,
                initial_capital=backtest.initial_capital,
                trading_session=trading_session,
                strategy_params=backtest.strategy_params
            )
            
            if not result.success:
                return {
                    "success": False,
                    "error": result.error or "Backtest failed",
                    "message": f"Failed to run backtest for {backtest.strategy_name} on {backtest.symbol}"
                }
            
            # Get summary and metrics
            summary = result.get_summary()
            metrics = result.get_trade_statistics()
            
            # Build response
            return {
                "success": True,
                "message": f"Backtest for {backtest.strategy_name} on {backtest.symbol} completed successfully",
                "backtest_id": result.backtest_id,
                "summary": summary,
                "metrics": metrics,
                "trades": result.trades,
                "equity_curve": result.equity_curve
            }
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")
    
    @app.post("/api/backtest/compare", response_model=StrategyComparisonResponse, tags=["backtesting"])
    async def compare_strategies(
        comparison: CompareStrategiesRequest,
        backtesting_service = Depends(get_backtesting_service)
    ):
        """
        Compare multiple strategies over the same time period
        
        - **strategies**: List of strategy names to compare
        - **symbol**: Stock symbol to backtest
        - **start_date**: Start date in YYYY-MM-DD format
        - **end_date**: End date in YYYY-MM-DD format
        - **initial_capital**: Initial capital for each backtest (default: 10000.0)
        - **trading_session**: Trading session (default: REGULAR)
        - **strategy_params**: Parameters for each strategy, keyed by strategy name
        """
        try:
            # Convert trading session string to enum
            if comparison.trading_session == "REGULAR":
                trading_session = TradingSession.REGULAR
            elif comparison.trading_session == "EXTENDED":
                trading_session = TradingSession.EXTENDED
            else:
                trading_session = TradingSession.REGULAR
            
            # Compare strategies
            result = backtesting_service.compare_strategies(
                strategies=comparison.strategies,
                symbol=comparison.symbol,
                start_date=comparison.start_date,
                end_date=comparison.end_date,
                initial_capital=comparison.initial_capital,
                trading_session=trading_session,
                strategy_params=comparison.strategy_params
            )
            
            return {
                "success": True,
                "message": f"Strategy comparison for {comparison.symbol} completed successfully",
                "backtest_period": result["backtest_period"],
                "metrics_comparison": result["metrics_comparison"],
                "overall_ranking": result["overall_ranking"],
                "best_strategy": result["best_strategy"],
                "metric_rankings": result["metric_rankings"]
            }
            
        except Exception as e:
            logger.error(f"Error comparing strategies: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error comparing strategies: {str(e)}")
    
    @app.get("/api/backtest/history", response_model=BacktestsResponse, tags=["backtesting"])
    async def get_backtest_history(
        strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        backtesting_service = Depends(get_backtesting_service)
    ):
        """
        Get backtest history
        
        - **strategy**: Filter by strategy name (optional)
        - **symbol**: Filter by symbol (optional)
        """
        try:
            # Get backtest history
            history = backtesting_service.get_backtest_history()
            
            # Filter by strategy and symbol if provided
            filtered_history = []
            for backtest_id, backtest in history.items():
                if strategy and backtest["strategy_name"] != strategy:
                    continue
                if symbol and backtest["symbol"] != symbol:
                    continue
                
                # Add to filtered history if it has a result
                if backtest["status"] == "completed" and backtest["result"]:
                    summary = backtest["result"].get_summary()
                    filtered_history.append(summary)
            
            return {
                "success": True,
                "message": f"Retrieved {len(filtered_history)} backtests",
                "backtests": filtered_history,
                "count": len(filtered_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting backtest history: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting backtest history: {str(e)}")
    
    @app.get("/api/backtest/{backtest_id}", response_model=BacktestResponse, tags=["backtesting"])
    async def get_backtest_result(
        backtest_id: str = Path(..., description="ID of the backtest"),
        backtesting_service = Depends(get_backtesting_service)
    ):
        """
        Get a specific backtest result
        
        - **backtest_id**: ID of the backtest
        """
        try:
            # Get backtest result
            result = backtesting_service.get_backtest_result(backtest_id)
            
            if not result:
                return {
                    "success": False,
                    "error": f"Backtest with ID {backtest_id} not found",
                    "message": "Backtest not found"
                }
            
            # Get summary and metrics
            summary = result.get_summary()
            metrics = result.get_trade_statistics()
            
            # Build response
            return {
                "success": True,
                "message": f"Retrieved backtest {backtest_id}",
                "backtest_id": result.backtest_id,
                "summary": summary,
                "metrics": metrics,
                "trades": result.trades,
                "equity_curve": result.equity_curve
            }
            
        except Exception as e:
            logger.error(f"Error getting backtest result: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error getting backtest result: {str(e)}")
    
    @app.delete("/api/backtest/history", response_model=BacktestsResponse, tags=["backtesting"])
    async def clear_backtest_history(
        backtesting_service = Depends(get_backtesting_service)
    ):
        """
        Clear backtest history
        """
        try:
            # Clear backtest history
            backtesting_service.clear_backtest_history()
            
            return {
                "success": True,
                "message": "Backtest history cleared",
                "backtests": [],
                "count": 0
            }
            
        except Exception as e:
            logger.error(f"Error clearing backtest history: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error clearing backtest history: {str(e)}")
    
    logger.info("FastAPI application initialized")
    return app 