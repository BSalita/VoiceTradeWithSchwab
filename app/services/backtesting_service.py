"""
Backtesting Service - Provides functionality for backtesting trading strategies
"""

import logging
import pandas as pd
import numpy as np
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

from ..api.schwab_client import SchwabAPIClient
from ..models.order import OrderType, OrderSide, OrderDuration, TradingSession
from ..models.backtest_result import BacktestResult
from ..strategies import get_strategy, create_strategy as strategies_create_strategy
from .market_data_service import MarketDataService
from .service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

class BacktestingService:
    """
    Service for backtesting trading strategies against historical data
    """
    
    def __init__(self):
        """Initialize the backtesting service"""
        self.api_client = SchwabAPIClient()
        self.market_data_service = ServiceRegistry.get("market_data") or MarketDataService()
        
        # Track backtests for later comparison
        self.backtest_history = {}
        
        # Current backtest parameters
        self.current_backtest = None
        
        logger.info("BacktestingService initialized")
    
    def run_backtest(self, 
                    strategy_name: str, 
                    symbol: str, 
                    start_date: Union[str, datetime],
                    end_date: Union[str, datetime],
                    initial_capital: float = 10000.0,
                    trading_session: TradingSession = TradingSession.REGULAR,
                    strategy_params: Optional[Dict[str, Any]] = None,
                    **kwargs) -> BacktestResult:
        """
        Run a backtest of a trading strategy
        
        Args:
            strategy_name: Name of the strategy to backtest
            symbol: Symbol to trade
            start_date: Start date for the backtest
            end_date: End date for the backtest
            initial_capital: Initial capital for the backtest
            trading_session: Trading session to use (REGULAR, EXTENDED, etc.)
            strategy_params: Additional parameters for the strategy
            **kwargs: Additional parameters
            
        Returns:
            BacktestResult: Results of the backtest
        """
        logger.info(f"Running backtest for {strategy_name} on {symbol} from {start_date} to {end_date}")
        
        # Convert string dates to datetime objects if needed
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            
        # Ensure end date is at end of day
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
        # Set up backtest parameters
        backtest_id = f"{strategy_name}_{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.current_backtest = {
            "id": backtest_id,
            "strategy_name": strategy_name,
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "trading_session": trading_session,
            "strategy_params": strategy_params or {},
            "status": "running",
            "result": None
        }
        
        try:
            # Get historical data
            historical_data = self._get_historical_data(symbol, start_date, end_date, trading_session)
            
            if not historical_data:
                logger.error(f"No historical data available for {symbol} from {start_date} to {end_date}")
                self.current_backtest["status"] = "error"
                self.current_backtest["error"] = "No historical data available"
                return BacktestResult(
                    backtest_id=backtest_id,
                    success=False,
                    error="No historical data available",
                    strategy_name=strategy_name,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    final_capital=initial_capital,
                    total_return=0,
                    trades=[],
                    metrics={}
                )
            
            # Create strategy
            strategy = strategies_create_strategy(strategy_name)
            if not strategy:
                logger.error(f"Strategy {strategy_name} not found")
                self.current_backtest["status"] = "error"
                self.current_backtest["error"] = f"Strategy {strategy_name} not found"
                return BacktestResult(
                    backtest_id=backtest_id,
                    success=False,
                    error=f"Strategy {strategy_name} not found",
                    strategy_name=strategy_name,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital,
                    final_capital=initial_capital,
                    total_return=0,
                    trades=[],
                    metrics={}
                )
            
            # Set strategy parameters
            if strategy_params:
                strategy.config.update(strategy_params)
            
            # Run the simulation
            result = self._run_simulation(
                strategy=strategy,
                historical_data=historical_data,
                symbol=symbol,
                initial_capital=initial_capital,
                **kwargs
            )
            
            # Calculate metrics
            metrics = self._calculate_metrics(result)
            
            # Create backtest result
            backtest_result = BacktestResult(
                backtest_id=backtest_id,
                success=True,
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_capital=result["final_portfolio_value"],
                total_return=result["total_return"],
                max_drawdown=metrics["max_drawdown"],
                sharpe_ratio=metrics["sharpe_ratio"],
                trades=result["trades"],
                metrics=metrics,
                equity_curve=result["equity_curve"]
            )
            
            # Update backtest history
            self.current_backtest["status"] = "completed"
            self.current_backtest["result"] = backtest_result
            self.backtest_history[backtest_id] = self.current_backtest
            
            logger.info(f"Backtest {backtest_id} completed successfully")
            return backtest_result
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}", exc_info=True)
            self.current_backtest["status"] = "error"
            self.current_backtest["error"] = str(e)
            return BacktestResult(
                backtest_id=backtest_id,
                success=False,
                error=str(e),
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                final_capital=initial_capital,
                total_return=0,
                trades=[],
                metrics={}
            )
    
    def compare_strategies(self, 
                          strategies: List[str], 
                          symbol: str, 
                          start_date: Union[str, datetime],
                          end_date: Union[str, datetime],
                          initial_capital: float = 10000.0,
                          trading_session: TradingSession = TradingSession.REGULAR,
                          strategy_params: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Compare multiple trading strategies
        
        Args:
            strategies: List of strategy names to compare
            symbol: Symbol to trade
            start_date: Start date
            end_date: End date
            initial_capital: Initial capital
            trading_session: Trading session to use
            strategy_params: Parameters for each strategy
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        logger.info(f"Comparing strategies: {strategies} on {symbol} from {start_date} to {end_date}")
        
        # Initialize results
        results = {}
        metrics_comparison = {}
        
        # Run backtests for each strategy
        for strategy_name in strategies:
            # Get strategy params if provided
            params = {}
            if strategy_params and strategy_name in strategy_params:
                params = strategy_params[strategy_name]
                
            # Run backtest
            result = self.run_backtest(
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                trading_session=trading_session,
                strategy_params=params
            )
            
            # Store result
            results[strategy_name] = result
            
            # Extract metrics for comparison
            if result.success:
                metrics_comparison[strategy_name] = {
                    "total_return": result.total_return,
                    "max_drawdown": result.max_drawdown,
                    "sharpe_ratio": result.sharpe_ratio,
                }
                
                # Add additional metrics if available
                for key, value in result.metrics.items():
                    if key not in metrics_comparison[strategy_name]:
                        metrics_comparison[strategy_name][key] = value
        
        # Generate ranking for each metric
        metric_rankings = {}
        for metric in ["total_return", "sharpe_ratio", "win_rate", "profit_factor"]:
            # Higher is better for these metrics
            ranking = sorted(strategies, key=lambda s: metrics_comparison[s][metric], reverse=True)
            metric_rankings[metric] = {strategy: i+1 for i, strategy in enumerate(ranking)}
        
        for metric in ["max_drawdown"]:
            # Lower is better for these metrics
            ranking = sorted(strategies, key=lambda s: metrics_comparison[s][metric])
            metric_rankings[metric] = {strategy: i+1 for i, strategy in enumerate(ranking)}
        
        # Calculate overall ranking
        overall_scores = {strategy: sum(metric_rankings[metric][strategy] for metric in metric_rankings) 
                         for strategy in strategies}
        overall_ranking = sorted(strategies, key=lambda s: overall_scores[s])
        
        comparison_result = {
            "results": results,
            "metrics_comparison": metrics_comparison,
            "metric_rankings": metric_rankings,
            "overall_ranking": overall_ranking,
            "best_strategy": overall_ranking[0] if overall_ranking else None,
            "backtest_period": {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "trading_session": trading_session.value
            }
        }
        
        logger.info(f"Strategy comparison complete. Best strategy: {comparison_result['best_strategy']}")
        return comparison_result
    
    def get_backtest_history(self) -> Dict[str, Any]:
        """
        Get the history of backtests
        
        Returns:
            Dict[str, Any]: History of backtests
        """
        return self.backtest_history
    
    def get_backtest_result(self, backtest_id: str) -> Optional[BacktestResult]:
        """
        Get a specific backtest result
        
        Args:
            backtest_id: ID of the backtest
            
        Returns:
            Optional[BacktestResult]: Backtest result, or None if not found
        """
        backtest = self.backtest_history.get(backtest_id)
        if backtest and backtest["status"] == "completed":
            return backtest["result"]
        return None
    
    def clear_backtest_history(self) -> None:
        """
        Clear the backtest history
        """
        self.backtest_history = {}
        logger.info("Backtest history cleared")
    
    def _get_historical_data(self, 
                           symbol: str, 
                           start_date: datetime, 
                           end_date: datetime,
                           trading_session: TradingSession) -> List[Dict[str, Any]]:
        """
        Get historical data for a symbol
        
        Args:
            symbol: Symbol to get data for
            start_date: Start date
            end_date: End date
            trading_session: Trading session to use
            
        Returns:
            List[Dict[str, Any]]: Historical data
        """
        try:
            # Request data with a slightly longer range to ensure we have enough data
            padded_start = start_date - timedelta(days=5)  # Add padding for indicators that need lookback
            
            # Get daily data for the entire period
            data = self.market_data_service.get_historical_data(
                symbol=symbol,
                interval="1day",
                start_time=padded_start,
                end_time=end_date,
                trading_session=trading_session
            )
            
            if not data or not isinstance(data, list):
                logger.error(f"Invalid historical data for {symbol}: {data}")
                return []
            
            # Filter data to the requested date range
            filtered_data = [bar for bar in data if start_date <= datetime.fromisoformat(bar["timestamp"].replace('Z', '+00:00')).replace(tzinfo=None) <= end_date]
            
            return filtered_data
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}", exc_info=True)
            return []
    
    def _run_simulation(self, 
                      strategy: Any, 
                      historical_data: List[Dict[str, Any]],
                      symbol: str,
                      initial_capital: float,
                      **kwargs) -> Dict[str, Any]:
        """
        Run a trading simulation using historical data
        
        Args:
            strategy: Trading strategy
            historical_data: Historical data
            symbol: Symbol to trade
            initial_capital: Initial capital
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Simulation results
        """
        # Initialize portfolio state
        portfolio = {
            "cash": initial_capital,
            "positions": {symbol: 0},
            "current_value": initial_capital,
            "trades": [],
            "equity_curve": []
        }
        
        # Initialize simulation variables
        last_price = 0
        open_orders = []
        
        # Sort historical data by timestamp
        sorted_data = sorted(historical_data, key=lambda x: x["timestamp"])
        
        # Process each historical data point
        for i, bar in enumerate(sorted_data):
            timestamp = datetime.fromisoformat(bar["timestamp"].replace('Z', '+00:00')).replace(tzinfo=None)
            open_price = float(bar["open"])
            high_price = float(bar["high"])
            low_price = float(bar["low"])
            close_price = float(bar["close"])
            volume = int(bar["volume"])
            
            # Save the last close price
            last_price = close_price
            
            # Create market data context
            market_data = {
                "symbol": symbol,
                "timestamp": timestamp,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
                "historical_data": sorted_data[:i+1]  # Data up to the current point
            }
            
            # Process any open orders first
            for order in list(open_orders):
                filled = self._process_order(order, market_data, portfolio)
                if filled:
                    open_orders.remove(order)
            
            # Execute strategy
            try:
                # Create a context for the strategy
                context = {
                    "market_data": market_data,
                    "portfolio": portfolio,
                    "historical_data": sorted_data[:i+1],
                    "simulation": True,
                    "timestamp": timestamp
                }
                
                # Execute strategy with the current context
                strategy_params = dict(kwargs)
                strategy_params["symbol"] = symbol
                strategy_params["context"] = context
                
                strategy_result = strategy.execute(**strategy_params)
                
                # Process any orders generated by the strategy
                if strategy_result and strategy_result.get("orders"):
                    for order_data in strategy_result["orders"]:
                        order = {
                            "id": f"backtest_order_{len(portfolio['trades'])}",
                            "symbol": symbol,
                            "side": order_data["side"],
                            "quantity": order_data["quantity"],
                            "order_type": order_data.get("order_type", "MARKET"),
                            "limit_price": order_data.get("limit_price"),
                            "timestamp": timestamp,
                            "status": "open"
                        }
                        
                        # Try to process the order immediately
                        filled = self._process_order(order, market_data, portfolio)
                        if not filled:
                            open_orders.append(order)
                
            except Exception as e:
                logger.error(f"Error executing strategy for {timestamp}: {str(e)}", exc_info=True)
            
            # Calculate portfolio value at the end of this bar
            position_value = portfolio["positions"][symbol] * close_price
            portfolio_value = portfolio["cash"] + position_value
            
            # Record portfolio value for equity curve
            portfolio["equity_curve"].append({
                "timestamp": timestamp.isoformat(),
                "portfolio_value": portfolio_value,
                "cash": portfolio["cash"],
                "position_value": position_value,
                "close_price": close_price
            })
            
            # Update current value
            portfolio["current_value"] = portfolio_value
        
        # Calculate final results
        initial_value = initial_capital
        final_value = portfolio["current_value"]
        total_return_pct = ((final_value / initial_value) - 1) * 100
        
        result = {
            "initial_portfolio_value": initial_value,
            "final_portfolio_value": final_value,
            "total_return": total_return_pct,
            "trades": portfolio["trades"],
            "equity_curve": portfolio["equity_curve"]
        }
        
        return result
    
    def _process_order(self, 
                     order: Dict[str, Any], 
                     market_data: Dict[str, Any], 
                     portfolio: Dict[str, Any]) -> bool:
        """
        Process an order in the simulation
        
        Args:
            order: Order to process
            market_data: Current market data
            portfolio: Portfolio state
            
        Returns:
            bool: True if the order was filled, False otherwise
        """
        symbol = order["symbol"]
        side = order["side"]
        quantity = order["quantity"]
        order_type = order["order_type"]
        limit_price = order.get("limit_price")
        timestamp = market_data["timestamp"]
        
        # For market orders, use the open price
        # For limit orders, check if the price was reached
        if order_type == "MARKET":
            execution_price = market_data["open"]
            can_execute = True
        elif order_type == "LIMIT":
            if not limit_price:
                return False
            
            if side == "BUY":
                # Buy limit executes if low price <= limit price
                can_execute = market_data["low"] <= limit_price
                execution_price = min(market_data["open"], limit_price)
            else:
                # Sell limit executes if high price >= limit price
                can_execute = market_data["high"] >= limit_price
                execution_price = max(market_data["open"], limit_price)
        else:
            # Unsupported order type
            return False
        
        # Check if the order can be executed
        if not can_execute:
            return False
        
        # Calculate order value
        order_value = quantity * execution_price
        
        # Check if we have enough cash for buy orders
        if side == "BUY" and portfolio["cash"] < order_value:
            # Adjust quantity based on available cash
            max_quantity = int(portfolio["cash"] / execution_price)
            if max_quantity <= 0:
                return False
            quantity = max_quantity
            order_value = quantity * execution_price
        
        # Check if we have enough shares for sell orders
        if side == "SELL" and portfolio["positions"][symbol] < quantity:
            # Adjust quantity based on available shares
            quantity = portfolio["positions"][symbol]
            if quantity <= 0:
                return False
            order_value = quantity * execution_price
        
        # Execute the order
        if side == "BUY":
            portfolio["cash"] -= order_value
            portfolio["positions"][symbol] += quantity
        else:
            portfolio["cash"] += order_value
            portfolio["positions"][symbol] -= quantity
        
        # Record the trade
        trade = {
            "id": order["id"],
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": execution_price,
            "value": order_value,
            "timestamp": timestamp.isoformat(),
            "fees": 0  # Could add simulated fees here
        }
        portfolio["trades"].append(trade)
        
        return True
    
    def _calculate_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate performance metrics from the backtest result
        
        Args:
            result: Simulation result
            
        Returns:
            Dict[str, Any]: Performance metrics
        """
        trades = result["trades"]
        equity_curve = result["equity_curve"]
        
        if not trades or not equity_curve:
            return {
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "win_rate": 0,
                "average_win": 0,
                "average_loss": 0,
                "profit_factor": 0,
                "expectancy": 0
            }
        
        # Calculate win rate, average win/loss
        profits = []
        losses = []
        buy_trades = {}
        
        # First pass: collect all buy trades
        for trade in trades:
            if trade["side"] == "BUY":
                symbol = trade["symbol"]
                if symbol not in buy_trades:
                    buy_trades[symbol] = []
                buy_trades[symbol].append(trade)
        
        # Second pass: match sells with buys to calculate P&L
        for trade in trades:
            if trade["side"] == "SELL":
                symbol = trade["symbol"]
                if symbol in buy_trades and buy_trades[symbol]:
                    buy_trade = buy_trades[symbol].pop(0)  # FIFO order matching
                    quantity = min(buy_trade["quantity"], trade["quantity"])
                    buy_value = quantity * buy_trade["price"]
                    sell_value = quantity * trade["price"]
                    trade_pnl = sell_value - buy_value
                    
                    if trade_pnl > 0:
                        profits.append(trade_pnl)
                    else:
                        losses.append(trade_pnl)
        
        # Calculate win rate
        total_trades = len(profits) + len(losses)
        win_rate = len(profits) / total_trades if total_trades > 0 else 0
        
        # Calculate average win/loss
        average_win = sum(profits) / len(profits) if profits else 0
        average_loss = sum(losses) / len(losses) if losses else 0
        
        # Calculate profit factor
        gross_profit = sum(profits) if profits else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        # Calculate expectancy
        expectancy = (win_rate * average_win - (1 - win_rate) * abs(average_loss)) if total_trades > 0 else 0
        
        # Calculate max drawdown
        equity = [point["portfolio_value"] for point in equity_curve]
        peak = equity[0]
        max_drawdown = 0
        
        for value in equity:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate daily returns and Sharpe ratio
        daily_returns = []
        
        for i in range(1, len(equity_curve)):
            today_value = equity_curve[i]["portfolio_value"]
            yesterday_value = equity_curve[i-1]["portfolio_value"]
            daily_return = (today_value / yesterday_value) - 1
            daily_returns.append(daily_return)
        
        if daily_returns:
            mean_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            risk_free_rate = 0.02 / 252  # Assume 2% annual risk-free rate
            sharpe_ratio = (mean_return - risk_free_rate) / std_return * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calculate additional metrics
        metrics = {
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "win_rate": win_rate * 100,  # Convert to percentage
            "average_win": average_win,
            "average_loss": average_loss,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "total_trades": total_trades,
            "winning_trades": len(profits),
            "losing_trades": len(losses)
        }
        
        return metrics 