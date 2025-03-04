"""
Web Application - Flask-based REST API for trading application
"""

import logging
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from ...services import ServiceRegistry, get_service

logger = logging.getLogger(__name__)

def create_app(test_config=None):
    """
    Create and configure the Flask app for the trading API
    
    Args:
        test_config: Optional test configuration
        
    Returns:
        Flask app instance
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)  # Enable CORS for all routes
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Initialize services if not already done
    try:
        trading_service = get_service("trading")
        if trading_service is None:
            ServiceRegistry.initialize_services()
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
    
    # Register routes
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'ok',
            'message': 'Trading API is running'
        })
    
    # Trading routes
    
    @app.route('/api/orders', methods=['POST'])
    def place_order():
        """Place an order"""
        trading_service = get_service("trading")
        if not trading_service:
            return jsonify({
                'success': False,
                'error': 'Trading service not available'
            }), 503
            
        order_data = request.json
        if not order_data:
            return jsonify({
                'success': False,
                'error': 'No order data provided'
            }), 400
            
        result = trading_service.place_order(order_data)
        return jsonify(result)
    
    @app.route('/api/orders/<order_id>', methods=['DELETE'])
    def cancel_order(order_id):
        """Cancel an order"""
        trading_service = get_service("trading")
        if not trading_service:
            return jsonify({
                'success': False,
                'error': 'Trading service not available'
            }), 503
            
        result = trading_service.cancel_order(order_id)
        return jsonify(result)
    
    @app.route('/api/orders', methods=['GET'])
    def get_orders():
        """Get orders with optional status filter"""
        trading_service = get_service("trading")
        if not trading_service:
            return jsonify({
                'success': False,
                'error': 'Trading service not available'
            }), 503
            
        status = request.args.get('status')
        result = trading_service.get_orders(status)
        return jsonify(result)
    
    # Account routes
    
    @app.route('/api/account', methods=['GET'])
    def get_account_info():
        """Get account information"""
        trading_service = get_service("trading")
        if not trading_service:
            return jsonify({
                'success': False,
                'error': 'Trading service not available'
            }), 503
            
        result = trading_service.get_account_info()
        return jsonify(result)
    
    # Market data routes
    
    @app.route('/api/quotes/<symbol>', methods=['GET'])
    def get_quote(symbol):
        """Get a quote for a symbol"""
        market_data_service = get_service("market_data")
        if not market_data_service:
            return jsonify({
                'success': False,
                'error': 'Market data service not available'
            }), 503
            
        result = market_data_service.get_quote(symbol)
        return jsonify(result)
    
    @app.route('/api/quotes', methods=['GET'])
    def get_quotes():
        """Get quotes for multiple symbols"""
        market_data_service = get_service("market_data")
        if not market_data_service:
            return jsonify({
                'success': False,
                'error': 'Market data service not available'
            }), 503
            
        symbols = request.args.get('symbols', '').split(',')
        symbols = [s.strip() for s in symbols if s.strip()]
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'No symbols provided'
            }), 400
            
        result = market_data_service.get_quotes(symbols)
        return jsonify(result)
    
    # Strategy routes
    
    @app.route('/api/strategies', methods=['POST'])
    def start_strategy():
        """Start a trading strategy"""
        strategy_service = get_service("strategies")
        if not strategy_service:
            return jsonify({
                'success': False,
                'error': 'Strategy service not available'
            }), 503
            
        strategy_data = request.json
        if not strategy_data or 'strategy_type' not in strategy_data:
            return jsonify({
                'success': False,
                'error': 'Missing strategy_type or strategy data'
            }), 400
            
        strategy_type = strategy_data.pop('strategy_type')
        result = strategy_service.start_strategy(strategy_type, **strategy_data)
        return jsonify(result)
    
    @app.route('/api/strategies/<strategy_key>', methods=['DELETE'])
    def stop_strategy(strategy_key):
        """Stop a trading strategy"""
        strategy_service = get_service("strategies")
        if not strategy_service:
            return jsonify({
                'success': False,
                'error': 'Strategy service not available'
            }), 503
            
        result = strategy_service.stop_strategy(strategy_key)
        return jsonify(result)
    
    @app.route('/api/strategies', methods=['GET'])
    def get_all_strategies():
        """Get status of all trading strategies"""
        strategy_service = get_service("strategies")
        if not strategy_service:
            return jsonify({
                'success': False,
                'error': 'Strategy service not available'
            }), 503
            
        result = strategy_service.get_all_strategies_status()
        return jsonify(result)
    
    @app.route('/api/strategies/<strategy_key>', methods=['GET'])
    def get_strategy_status(strategy_key):
        """Get status of a trading strategy"""
        strategy_service = get_service("strategies")
        if not strategy_service:
            return jsonify({
                'success': False,
                'error': 'Strategy service not available'
            }), 503
            
        result = strategy_service.get_strategy_status(strategy_key)
        return jsonify(result)
    
    # Trade history routes
    
    @app.route('/api/history', methods=['GET'])
    def get_trade_history():
        """Get trade history with optional filters"""
        trading_service = get_service("trading")
        if not trading_service:
            return jsonify({
                'success': False,
                'error': 'Trading service not available'
            }), 503
            
        symbol = request.args.get('symbol')
        limit = request.args.get('limit', 10, type=int)
        strategy = request.args.get('strategy')
        
        result = trading_service.get_trade_history(
            symbol=symbol,
            limit=limit,
            strategy=strategy
        )
        return jsonify(result)
    
    @app.route('/api/history/export', methods=['GET'])
    def export_trade_history():
        """Export trade history to CSV file"""
        trading_service = get_service("trading")
        if not trading_service:
            return jsonify({
                'success': False,
                'error': 'Trading service not available'
            }), 503
            
        filename = request.args.get('filename')
        result = trading_service.export_trade_history(filename)
        return jsonify(result)
    
    # Error handlers
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'success': False,
            'error': 'Not found'
        }), 404
    
    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors"""
        logger.error(f"Server error: {str(error)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    
    logger.info("Trading API initialized")
    return app 