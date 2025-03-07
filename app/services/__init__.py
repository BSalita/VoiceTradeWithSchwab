"""
Services package - Core business logic independent of interface
"""

import logging
from typing import Dict, Any, Type, Optional

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """
    Registry for managing service instances to enable dependency injection
    and access from different interfaces
    """
    _services: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, service_name: str, service_instance: Any) -> None:
        """
        Register a service instance with the registry
        
        Args:
            service_name: Name of the service
            service_instance: The service instance
        """
        cls._services[service_name] = service_instance
        logger.debug(f"Registered service: {service_name}")
    
    @classmethod
    def get(cls, service_name: str) -> Optional[Any]:
        """
        Get a registered service by name
        
        Args:
            service_name: Name of the service
            
        Returns:
            The service instance or None if not found
        """
        service = cls._services.get(service_name)
        if service is None:
            logger.warning(f"Service not found: {service_name}")
        return service
    
    @classmethod
    def initialize_services(cls) -> None:
        """Initialize all core services needed by the application"""
        # Import services here to avoid circular imports
        from .trading_service import TradingService
        from .market_data_service import MarketDataService
        from .strategy_service import StrategyService
        from .backtesting_service import BacktestingService
        
        # Register core services
        cls.register("trading", TradingService())
        cls.register("market_data", MarketDataService())
        cls.register("strategies", StrategyService())
        cls.register("backtesting", BacktestingService())
        
        logger.info("Core services initialized")
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered services (mainly for testing)"""
        cls._services = {}
        logger.debug("Service registry cleared")

def get_service(service_name: str) -> Optional[Any]:
    """
    Get a service by name from the registry
    
    Args:
        service_name: Name of the service
        
    Returns:
        The service instance or None if not found
    """
    return ServiceRegistry.get(service_name) 