"""
Backtest Result Model - Data model for backtest results
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

@dataclass
class BacktestResult:
    """
    Data model for storing the results of a backtest
    """
    
    # Backtest metadata
    backtest_id: str
    success: bool
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    error: Optional[str] = None
    
    # Performance metrics
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Trade history
    trades: List[Dict[str, Any]] = field(default_factory=list)
    
    # Equity curve for visualization
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and process after initialization"""
        # Ensure dates are datetime objects
        if isinstance(self.start_date, str):
            self.start_date = datetime.fromisoformat(self.start_date.replace('Z', '+00:00')).replace(tzinfo=None)
        if isinstance(self.end_date, str):
            self.end_date = datetime.fromisoformat(self.end_date.replace('Z', '+00:00')).replace(tzinfo=None)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the backtest result to a dictionary
        
        Returns:
            Dict[str, Any]: Dictionary representation of the backtest result
        """
        return {
            "backtest_id": self.backtest_id,
            "success": self.success,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "error": self.error,
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "metrics": self.metrics,
            "trades": self.trades,
            "equity_curve": self.equity_curve
        }
    
    def to_json(self) -> str:
        """
        Convert the backtest result to a JSON string
        
        Returns:
            str: JSON string representation of the backtest result
        """
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestResult':
        """
        Create a BacktestResult from a dictionary
        
        Args:
            data: Dictionary containing backtest result data
            
        Returns:
            BacktestResult: BacktestResult instance
        """
        # Handle conversion of string dates to datetime objects
        if "start_date" in data and isinstance(data["start_date"], str):
            data["start_date"] = datetime.fromisoformat(data["start_date"].replace('Z', '+00:00')).replace(tzinfo=None)
        if "end_date" in data and isinstance(data["end_date"], str):
            data["end_date"] = datetime.fromisoformat(data["end_date"].replace('Z', '+00:00')).replace(tzinfo=None)
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BacktestResult':
        """
        Create a BacktestResult from a JSON string
        
        Args:
            json_str: JSON string containing backtest result data
            
        Returns:
            BacktestResult: BacktestResult instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the backtest result
        
        Returns:
            Dict[str, Any]: Summary of the backtest result
        """
        return {
            "backtest_id": self.backtest_id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "period": f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}",
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return": f"{self.total_return:.2f}%",
            "max_drawdown": f"{self.max_drawdown:.2f}%",
            "sharpe_ratio": f"{self.sharpe_ratio:.2f}",
            "win_rate": f"{self.metrics.get('win_rate', 0):.2f}%",
            "total_trades": len(self.trades),
            "success": self.success,
            "error": self.error
        }
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """
        Get trade statistics from the backtest result
        
        Returns:
            Dict[str, Any]: Trade statistics
        """
        if not self.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "average_win": 0,
                "average_loss": 0,
                "profit_factor": 0,
                "average_trade": 0
            }
        
        return {
            "total_trades": self.metrics.get("total_trades", len(self.trades)),
            "winning_trades": self.metrics.get("winning_trades", 0),
            "losing_trades": self.metrics.get("losing_trades", 0),
            "win_rate": f"{self.metrics.get('win_rate', 0):.2f}%",
            "average_win": f"${self.metrics.get('average_win', 0):.2f}",
            "average_loss": f"${abs(self.metrics.get('average_loss', 0)):.2f}",
            "profit_factor": f"{self.metrics.get('profit_factor', 0):.2f}",
            "average_trade": f"${self.metrics.get('expectancy', 0):.2f}"
        } 