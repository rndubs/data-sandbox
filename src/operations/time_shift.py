"""Time shift operation for time series data."""

import pandas as pd
from typing import Dict, Any
import logging

from src.operations.base import Operation

logger = logging.getLogger(__name__)


class TimeShiftOperation(Operation):
    """Shift time series data by a specified time delta.

    This operation shifts all timestamps by a specified amount,
    effectively moving the signal forward or backward in time.
    """

    @property
    def operation_type(self) -> str:
        return "time_shift"

    def _validate_config(self):
        """Validate time shift configuration."""
        self.shift_seconds = self.config.get('shift_seconds')
        if self.shift_seconds is None:
            raise ValueError("shift_seconds is required")

        # Convert to float if needed
        self.shift_seconds = float(self.shift_seconds)

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Execute time shift on time series data.

        Args:
            data: Input time series with columns [timestamp, channel_id, value]

        Returns:
            Time-shifted time series with same structure
        """
        logger.info(f"Executing time shift: {self.shift_seconds} seconds")

        # Make a copy to avoid modifying original data
        result_df = data.copy()

        # Ensure timestamp is datetime type
        if result_df['timestamp'].dtype != 'datetime64[ns]':
            result_df['timestamp'] = pd.to_datetime(result_df['timestamp'])

        # Apply time shift
        result_df['timestamp'] = result_df['timestamp'] + pd.Timedelta(seconds=self.shift_seconds)

        logger.info(f"Time shift complete: {len(result_df)} samples shifted by {self.shift_seconds}s")

        return result_df
