"""Base classes for time series operations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class OperationConfig(BaseModel):
    """Base configuration for operations."""
    pass


class Operation(ABC):
    """Base class for all time series operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize operation with configuration.

        Args:
            config: Operation-specific configuration
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    def _validate_config(self):
        """Validate operation configuration."""
        pass

    @abstractmethod
    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Execute the operation on input data.

        Args:
            data: Input time series data

        Returns:
            Transformed time series data
        """
        pass

    @property
    @abstractmethod
    def operation_type(self) -> str:
        """Return the operation type identifier."""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get operation metadata.

        Returns:
            Dictionary with operation information
        """
        return {
            'type': self.operation_type,
            'config': self.config
        }

    def __str__(self) -> str:
        """String representation of operation."""
        return f"{self.operation_type}({self.config})"

    def __repr__(self) -> str:
        """Representation of operation."""
        return self.__str__()
