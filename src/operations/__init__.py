"""Operations module for time series transformations."""

from typing import Dict, Any
from src.operations.base import Operation
from src.operations.fft import FFTOperation
from src.operations.filter import FilterOperation
from src.operations.unit_conversion import UnitConversionOperation

# Operation registry
OPERATIONS = {
    'fft': FFTOperation,
    'filter': FilterOperation,
    'unit_conversion': UnitConversionOperation,
}


def create_operation(operation_type: str, config: Dict[str, Any] = None) -> Operation:
    """Factory function to create operations.

    Args:
        operation_type: Type of operation to create
        config: Operation configuration

    Returns:
        Operation instance

    Raises:
        ValueError: If operation type is unknown
    """
    if operation_type not in OPERATIONS:
        raise ValueError(
            f"Unknown operation type: {operation_type}. "
            f"Available operations: {list(OPERATIONS.keys())}"
        )

    operation_class = OPERATIONS[operation_type]
    return operation_class(config)


def get_available_operations() -> list:
    """Get list of available operation types.

    Returns:
        List of operation type names
    """
    return list(OPERATIONS.keys())


__all__ = [
    'Operation',
    'FFTOperation',
    'FilterOperation',
    'UnitConversionOperation',
    'create_operation',
    'get_available_operations',
    'OPERATIONS',
]
