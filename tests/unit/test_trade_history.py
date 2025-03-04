"""
Unit tests for the TradeHistory class
"""

import pytest
import os
import pandas as pd
from datetime import datetime
from unittest.mock import patch, mock_open

from app.models.trade_history import TradeHistory


class TestTradeHistory:
    """Test the TradeHistory class"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Create a temporary file path for testing
        self.test_file = "test_trades.csv"
        
        # Create a TradeHistory instance with the test file
        self.trade_history = TradeHistory(file_path=self.test_file)
        
        # Ensure the file doesn't exist before each test
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def teardown_method(self):
        """Clean up after each test"""
        # Remove the test file if it exists
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_init(self):
        """Test initialization of TradeHistory"""
        # Verify the file path was set
        assert self.trade_history.file_path == self.test_file
        
        # Verify the trades DataFrame was created
        assert isinstance(self.trade_history.trades, pd.DataFrame)
        assert len(self.trade_history.trades) == 0

    @patch("builtins.open", new_callable=mock_open, read_data="order_id,symbol,quantity,price,side,timestamp,strategy\n")
    @patch("pandas.read_csv")
    def test_load_trades(self, mock_read_csv, mock_file):
        """Test loading trades from a file"""
        # Create a mock DataFrame to return
        mock_df = pd.DataFrame({
            "order_id": ["order1", "order2"],
            "symbol": ["AAPL", "MSFT"],
            "quantity": [10, 5],
            "price": [150.0, 200.0],
            "side": ["BUY", "SELL"],
            "timestamp": [datetime.now().isoformat(), datetime.now().isoformat()],
            "strategy": ["highlow", "oscillating"]
        })
        mock_read_csv.return_value = mock_df
        
        # Load trades
        self.trade_history.load_trades()
        
        # Verify the trades were loaded
        assert len(self.trade_history.trades) == 2
        assert mock_read_csv.called
        mock_read_csv.assert_called_once_with(self.test_file)

    @patch("pandas.DataFrame.to_csv")
    def test_save_trades(self, mock_to_csv):
        """Test saving trades to a file"""
        # Add some trades
        self.trade_history.add_trade(
            order_id="order1",
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="highlow"
        )
        
        self.trade_history.add_trade(
            order_id="order2",
            symbol="MSFT",
            quantity=5,
            price=200.0,
            side="SELL",
            strategy="oscillating"
        )
        
        # Save trades
        self.trade_history.save_trades()
        
        # Verify the trades were saved
        assert mock_to_csv.called
        mock_to_csv.assert_called_once_with(self.test_file, index=False)

    def test_add_trade(self):
        """Test adding a trade"""
        # Add a trade
        self.trade_history.add_trade(
            order_id="order1",
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="highlow"
        )
        
        # Verify the trade was added
        assert len(self.trade_history.trades) == 1
        assert self.trade_history.trades.iloc[0]["order_id"] == "order1"
        assert self.trade_history.trades.iloc[0]["symbol"] == "AAPL"
        assert self.trade_history.trades.iloc[0]["quantity"] == 10
        assert self.trade_history.trades.iloc[0]["price"] == 150.0
        assert self.trade_history.trades.iloc[0]["side"] == "BUY"
        assert self.trade_history.trades.iloc[0]["strategy"] == "highlow"
        assert "timestamp" in self.trade_history.trades.columns

    def test_get_trades(self):
        """Test getting all trades"""
        # Add some trades
        self.trade_history.add_trade(
            order_id="order1",
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="highlow"
        )
        
        self.trade_history.add_trade(
            order_id="order2",
            symbol="MSFT",
            quantity=5,
            price=200.0,
            side="SELL",
            strategy="oscillating"
        )
        
        # Get all trades
        trades = self.trade_history.get_trades()
        
        # Verify the trades
        assert len(trades) == 2
        assert trades[0]["order_id"] == "order1"
        assert trades[0]["symbol"] == "AAPL"
        assert trades[1]["order_id"] == "order2"
        assert trades[1]["symbol"] == "MSFT"

    def test_get_trades_by_symbol(self):
        """Test getting trades by symbol"""
        # Add some trades
        self.trade_history.add_trade(
            order_id="order1",
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="highlow"
        )
        
        self.trade_history.add_trade(
            order_id="order2",
            symbol="MSFT",
            quantity=5,
            price=200.0,
            side="SELL",
            strategy="oscillating"
        )
        
        self.trade_history.add_trade(
            order_id="order3",
            symbol="AAPL",
            quantity=5,
            price=160.0,
            side="SELL",
            strategy="highlow"
        )
        
        # Get trades for AAPL
        trades = self.trade_history.get_trades_by_symbol("AAPL")
        
        # Verify the trades
        assert len(trades) == 2
        assert trades[0]["order_id"] == "order1"
        assert trades[0]["symbol"] == "AAPL"
        assert trades[1]["order_id"] == "order3"
        assert trades[1]["symbol"] == "AAPL"

    def test_get_trades_by_strategy(self):
        """Test getting trades by strategy"""
        # Add some trades
        self.trade_history.add_trade(
            order_id="order1",
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="highlow"
        )
        
        self.trade_history.add_trade(
            order_id="order2",
            symbol="MSFT",
            quantity=5,
            price=200.0,
            side="SELL",
            strategy="oscillating"
        )
        
        self.trade_history.add_trade(
            order_id="order3",
            symbol="AAPL",
            quantity=5,
            price=160.0,
            side="SELL",
            strategy="highlow"
        )
        
        # Get trades for highlow strategy
        trades = self.trade_history.get_trades_by_strategy("highlow")
        
        # Verify the trades
        assert len(trades) == 2
        assert trades[0]["order_id"] == "order1"
        assert trades[0]["strategy"] == "highlow"
        assert trades[1]["order_id"] == "order3"
        assert trades[1]["strategy"] == "highlow"

    def test_get_trades_by_side(self):
        """Test getting trades by side"""
        # Add some trades
        self.trade_history.add_trade(
            order_id="order1",
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="highlow"
        )
        
        self.trade_history.add_trade(
            order_id="order2",
            symbol="MSFT",
            quantity=5,
            price=200.0,
            side="SELL",
            strategy="oscillating"
        )
        
        self.trade_history.add_trade(
            order_id="order3",
            symbol="AAPL",
            quantity=5,
            price=160.0,
            side="SELL",
            strategy="highlow"
        )
        
        # Get SELL trades
        trades = self.trade_history.get_trades_by_side("SELL")
        
        # Verify the trades
        assert len(trades) == 2
        assert trades[0]["order_id"] == "order2"
        assert trades[0]["side"] == "SELL"
        assert trades[1]["order_id"] == "order3"
        assert trades[1]["side"] == "SELL"

    def test_calculate_pnl(self):
        """Test calculating profit and loss"""
        # Add some trades for the same symbol
        self.trade_history.add_trade(
            order_id="order1",
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="highlow"
        )
        
        self.trade_history.add_trade(
            order_id="order2",
            symbol="AAPL",
            quantity=5,
            price=160.0,
            side="SELL",
            strategy="highlow"
        )
        
        # Calculate P&L
        pnl = self.trade_history.calculate_pnl("AAPL")
        
        # Verify the P&L
        # Buy cost: 10 * 150 = 1500
        # Sell proceeds: 5 * 160 = 800
        # Remaining position: 5 shares at cost basis of 150 = 750
        # P&L: 800 - 750 = 50
        assert pnl == 50.0

    def test_calculate_strategy_performance(self):
        """Test calculating strategy performance"""
        # Add some trades for different strategies
        self.trade_history.add_trade(
            order_id="order1",
            symbol="AAPL",
            quantity=10,
            price=150.0,
            side="BUY",
            strategy="highlow"
        )
        
        self.trade_history.add_trade(
            order_id="order2",
            symbol="AAPL",
            quantity=10,
            price=160.0,
            side="SELL",
            strategy="highlow"
        )
        
        self.trade_history.add_trade(
            order_id="order3",
            symbol="MSFT",
            quantity=5,
            price=200.0,
            side="BUY",
            strategy="oscillating"
        )
        
        self.trade_history.add_trade(
            order_id="order4",
            symbol="MSFT",
            quantity=5,
            price=190.0,
            side="SELL",
            strategy="oscillating"
        )
        
        # Calculate strategy performance
        performance = self.trade_history.calculate_strategy_performance()
        
        # Verify the performance
        # highlow: Buy 10 at 150 = 1500, Sell 10 at 160 = 1600, P&L = 100
        # oscillating: Buy 5 at 200 = 1000, Sell 5 at 190 = 950, P&L = -50
        assert "highlow" in performance
        assert "oscillating" in performance
        assert performance["highlow"] == 100.0
        assert performance["oscillating"] == -50.0 