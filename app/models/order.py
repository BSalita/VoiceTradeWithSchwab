"""
Order Model - Data model for trading orders
"""

import time
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

class OrderType(Enum):
    """Enum representing order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderSide(Enum):
    """Enum representing order sides"""
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    """Enum representing order statuses"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class OrderDuration(Enum):
    """Enum representing order durations"""
    DAY = "DAY"
    GTC = "GTC"  # Good Till Canceled
    GTD = "GTD"  # Good Till Date
    FOK = "FOK"  # Fill Or Kill
    IOC = "IOC"  # Immediate Or Cancel

class TradingSession(Enum):
    """Enum representing trading sessions"""
    REGULAR = "REGULAR"
    EXTENDED = "EXTENDED"
    ALL = "ALL"

@dataclass
class Order:
    """Order data model"""
    
    symbol: str
    quantity: int
    side: OrderSide
    order_type: OrderType
    price: Optional[float] = None
    stop_price: Optional[float] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    submitted_at: float = field(default_factory=time.time)
    filled_at: Optional[float] = None
    cancelled_at: Optional[float] = None
    extended_hours: bool = False
    duration: OrderDuration = OrderDuration.DAY
    session: TradingSession = TradingSession.REGULAR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary for API requests"""
        order_dict = {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "order_type": self.order_type.value,
            "side": self.side.value,
            "session": self.session.value,
            "duration": self.duration.value
        }
        
        if self.price is not None and self.order_type != OrderType.MARKET:
            order_dict["price"] = self.price
            
        if self.stop_price is not None and self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            order_dict["stopPrice"] = self.stop_price
        
        # Add orderType for external API compatibility
        order_dict["orderType"] = self.order_type.value
            
        return order_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Create an order from a dictionary"""
        # Get order_type from either order_type or orderType for compatibility
        order_type_value = data.get("order_type")
        if order_type_value is None:
            order_type_value = data.get("orderType", "MARKET")
            
        return cls(
            symbol=data.get("symbol", ""),
            quantity=data.get("quantity", 0),
            side=OrderSide(data.get("side", "BUY")),
            order_type=OrderType(order_type_value),
            price=data.get("price"),
            stop_price=data.get("stopPrice"),
            order_id=data.get("orderId"),
            status=OrderStatus(data.get("status", "PENDING")),
            filled_quantity=data.get("filledQuantity", 0),
            filled_price=data.get("filledPrice"),
            submitted_at=data.get("submittedAt", time.time()),
            filled_at=data.get("filledAt"),
            cancelled_at=data.get("cancelledAt"),
            extended_hours=data.get("extendedHours", False),
            duration=OrderDuration(data.get("duration", "DAY")),
            session=TradingSession(data.get("session", "REGULAR"))
        )
    
    def is_complete(self) -> bool:
        """Check if the order is complete (filled or cancelled)"""
        return self.status in [
            OrderStatus.FILLED, 
            OrderStatus.CANCELLED, 
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED
        ]
    
    def update_from_api(self, api_data: Dict[str, Any]) -> None:
        """Update order data from API response"""
        if "status" in api_data:
            self.status = OrderStatus(api_data["status"])
            
        if "filledQuantity" in api_data:
            self.filled_quantity = api_data["filledQuantity"]
            
        if "filledPrice" in api_data:
            self.filled_price = api_data["filledPrice"]
            
        if "filledAt" in api_data:
            self.filled_at = api_data["filledAt"]
            
        if "cancelledAt" in api_data:
            self.cancelled_at = api_data["cancelledAt"]
            
        if "orderId" in api_data:
            self.order_id = api_data["orderId"]