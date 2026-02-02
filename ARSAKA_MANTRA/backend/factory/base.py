"""
Base Factory - Common utilities and protocols for factory modules.

This module provides shared utilities used by all factory modules.
"""

import logging
from typing import Optional, TypeVar, Generic
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar("T")


class FactoryMixin:
    """Mixin providing common factory utilities."""

    @staticmethod
    def log_using(service_name: str, implementation: str, details: str = ""):
        """Log which implementation is being used."""
        if details:
            logger.info(f"Using {implementation} for {service_name}: {details}")
        else:
            logger.info(f"Using {implementation} for {service_name}")

    @staticmethod
    def log_fallback(service_name: str, reason: str, fallback: str):
        """Log fallback to alternative implementation."""
        logger.warning(f"{service_name}: {reason}, falling back to {fallback}")

    @staticmethod
    def log_disabled(service_name: str):
        """Log that a service is disabled."""
        logger.debug(f"{service_name} feature is disabled")


class SingletonMeta(type):
    """
    Metaclass for singleton pattern.

    Usage:
        class MyClass(metaclass=SingletonMeta):
            pass
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def reset(mcs, cls):
        """Reset singleton instance for testing."""
        if cls in mcs._instances:
            del mcs._instances[cls]
