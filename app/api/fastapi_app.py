"""
FastAPI application for the Automated Trading system.
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.service_registry import ServiceRegistry
from app.services.trading_service import TradingService

# Create FastAPI app
app = FastAPI(
    title="Automated Trading API",
    description="API for the Automated Trading system",
    version="1.0.0"
)

# Models
class OrderRequest(BaseModel):
    symbol: str
    quantity: int
    side: str
    order_type: str
    price: Optional[float] = None
    session: str = "REGULAR"
    duration: str = "DAY"
    strategy: Optional[str] = None

class StrategyRequest(BaseModel):
    name: str
    type: str
    parameters: Dict[str, Any]

# Dependency to get trading service
def get_trading_service():
    trading_service = ServiceRegistry.get("trading")
    if not trading_service:
        raise HTTPException(status_code=500, detail="Trading service not available")
    return trading_service

# Dependency to get strategy service
def get_strategy_service():
    strategy_service = ServiceRegistry.get("strategy")
    if not strategy_service:
        raise HTTPException(status_code=500, detail="Strategy service not available")
    return strategy_service

# Endpoints
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/orders")
def place_order(order: OrderRequest, trading_service: TradingService = Depends(get_trading_service)):
    """Place a new order."""
    result = trading_service.place_order(
        symbol=order.symbol,
        quantity=order.quantity,
        side=order.side,
        order_type=order.order_type,
        price=order.price,
        session=order.session,
        duration=order.duration,
        strategy=order.strategy
    )
    return result

@app.get("/orders")
def get_orders(status: Optional[str] = None, trading_service: TradingService = Depends(get_trading_service)):
    """Get all orders, optionally filtered by status."""
    return trading_service.get_orders(status=status)

@app.delete("/orders/{order_id}")
def cancel_order(order_id: str, trading_service: TradingService = Depends(get_trading_service)):
    """Cancel an order by ID."""
    return trading_service.cancel_order(order_id)

@app.get("/quotes/{symbol}")
def get_quote(symbol: str, trading_service: TradingService = Depends(get_trading_service)):
    """Get a quote for a symbol."""
    return trading_service.get_quote(symbol)

@app.post("/strategies")
def create_strategy(strategy: StrategyRequest, strategy_service = Depends(get_strategy_service)):
    """Create a new strategy."""
    result = strategy_service.create_strategy(
        name=strategy.name,
        strategy_type=strategy.type,
        parameters=strategy.parameters
    )
    return {"success": True, "strategy": strategy.name}

@app.post("/strategies/{name}/execute")
def execute_strategy(name: str, strategy_service = Depends(get_strategy_service)):
    """Execute a strategy by name."""
    result = strategy_service.execute_strategy(name)
    return {"success": True, "result": result} 