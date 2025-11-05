"""Unit conversion operations for time series data."""

import pandas as pd
from typing import Dict, Any, Callable
import logging

from src.operations.base import Operation

logger = logging.getLogger(__name__)


# Predefined conversion functions
CONVERSIONS = {
    # Temperature
    'celsius_to_fahrenheit': lambda x: x * 9/5 + 32,
    'fahrenheit_to_celsius': lambda x: (x - 32) * 5/9,
    'celsius_to_kelvin': lambda x: x + 273.15,
    'kelvin_to_celsius': lambda x: x - 273.15,

    # Length
    'meters_to_feet': lambda x: x * 3.28084,
    'feet_to_meters': lambda x: x / 3.28084,
    'meters_to_inches': lambda x: x * 39.3701,
    'inches_to_meters': lambda x: x / 39.3701,

    # Velocity
    'mps_to_mph': lambda x: x * 2.23694,  # meters/sec to miles/hour
    'mph_to_mps': lambda x: x / 2.23694,
    'mps_to_kmph': lambda x: x * 3.6,  # meters/sec to km/hour
    'kmph_to_mps': lambda x: x / 3.6,

    # Pressure
    'pa_to_psi': lambda x: x * 0.000145038,  # Pascal to PSI
    'psi_to_pa': lambda x: x / 0.000145038,
    'pa_to_bar': lambda x: x / 100000,
    'bar_to_pa': lambda x: x * 100000,

    # Voltage scaling
    'mv_to_v': lambda x: x / 1000,  # millivolts to volts
    'v_to_mv': lambda x: x * 1000,

    # Generic scaling
    'scale': lambda x, factor: x * factor,  # Requires factor parameter
    'offset': lambda x, offset: x + offset,  # Requires offset parameter
}


class UnitConversionOperation(Operation):
    """Convert units of time series values.

    Supports common conversions and custom scaling/offset transformations.
    """

    @property
    def operation_type(self) -> str:
        return "unit_conversion"

    def _validate_config(self):
        """Validate unit conversion configuration."""
        self.conversion = self.config.get('conversion')
        if not self.conversion:
            raise ValueError("conversion type is required")

        # Check if conversion is supported
        if self.conversion not in CONVERSIONS:
            raise ValueError(
                f"Unknown conversion: {self.conversion}. "
                f"Supported conversions: {list(CONVERSIONS.keys())}"
            )

        # Get additional parameters for parameterized conversions
        self.factor = self.config.get('factor', 1.0)
        self.offset = self.config.get('offset', 0.0)

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Execute unit conversion on time series data.

        Args:
            data: Input time series with columns [timestamp, channel_id, value]

        Returns:
            Converted time series with same structure
        """
        logger.info(f"Executing unit conversion: {self.conversion}")

        # Make a copy to avoid modifying original data
        result_df = data.copy()

        # Get conversion function
        conversion_func = CONVERSIONS[self.conversion]

        # Apply conversion
        try:
            if self.conversion == 'scale':
                result_df['value'] = conversion_func(result_df['value'], self.factor)
            elif self.conversion == 'offset':
                result_df['value'] = conversion_func(result_df['value'], self.offset)
            else:
                result_df['value'] = conversion_func(result_df['value'])

            logger.info(f"Unit conversion complete: {len(result_df)} samples")

        except Exception as e:
            logger.error(f"Error during conversion: {e}")
            raise

        return result_df

    @staticmethod
    def get_supported_conversions() -> list:
        """Get list of supported conversion types.

        Returns:
            List of conversion names
        """
        return list(CONVERSIONS.keys())
