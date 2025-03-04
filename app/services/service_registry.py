"""
Service Registry for the Automated Trading System.

This module provides a central registry for all services used in the application.
"""
from typing import Dict, Any, Optional


class ServiceRegistry:
    """
    A central registry for services used in the application.
    
    This is a singleton class that provides access to all registered services.
    Services can be registered and retrieved by name.
    """
    
    _services: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """
        Register a service with the given name.
        
        Args:
            name: The name to register the service under
            service: The service instance to register
        """
        cls._services[name] = service
    
    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """
        Get a service by name.
        
        Args:
            name: The name of the service to retrieve
            
        Returns:
            The service instance or None if not found
        """
        return cls._services.get(name)
    
    @classmethod
    def has(cls, name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            name: The name of the service to check
            
        Returns:
            True if the service is registered, False otherwise
        """
        return name in cls._services
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister a service.
        
        Args:
            name: The name of the service to unregister
        """
        if name in cls._services:
            del cls._services[name]
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered services."""
        cls._services.clear()
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Get all registered services.
        
        Returns:
            A dictionary of service name to service instance
        """
        return cls._services.copy() 