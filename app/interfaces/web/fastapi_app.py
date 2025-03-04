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
    OrderRequest, StrategyRequest,
    # Response models
    HealthResponse, OrderResponse, OrdersResponse, QuoteResponse, QuotesResponse,
    AccountResponse, StrategyResponse, StrategiesResponse, TradeHistoryResponse,
    ExportResponse
)
from ...services import ServiceRegistry, get_service

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
    """
    
    tags_metadata = [
        {
            "name": "health",
            "description": "Health check and system information",
        },
        {
            "name": "account",
            "description": "Account information and balances",
        },
        {
            "name": "orders",
            "description": "Order management",
        },
        {
            "name": "quotes",
            "description": "Market data and quotes",
        },
        {
            "name": "strategies",
            "description": "Trading strategies",
        },
        {
            "name": "history",
            "description": "Trade history and exports",
        },
    ]
    
    # Create the FastAPI app
    app = FastAPI(
        title="AutomatedTrading API",
        description=description,
        version=app.__version__,
        openapi_tags=tags_metadata,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Replace with specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize services if not already done
    @app.on_event("startup")
    async def startup_event():
        try:
            trading_service = get_service("trading")
            if trading_service is None:
                ServiceRegistry.initialize_services()
                logger.info("Services initialized on startup")
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
    
    # Define dependencies
    def get_trading_service():
        service = get_service("trading")
        if not service:
            raise HTTPException(status_code=503, detail="Trading service not available")
        return service
    
    def get_market_data_service():
        service = get_service("market_data")
        if not service:
            raise HTTPException(status_code=503, detail="Market data service not available")
        return service
    
    def get_strategy_service():
        service = get_service("strategies")
        if not service:
            raise HTTPException(status_code=503, detail="Strategy service not available")
        return service
    
    # Health check endpoints
    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    async def health_check():
        """Check API health status"""
        return {
            "success": True,
            "status": "ok",
            "message": "Trading API is running",
            "version": app.__version__
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
    
    logger.info("FastAPI application initialized")
    return app 