"""Signal filtering operations (low-pass, high-pass, band-pass)."""

import numpy as np
import pandas as pd
from typing import Dict, Any
from scipy import signal
import logging

from src.operations.base import Operation

logger = logging.getLogger(__name__)


class FilterOperation(Operation):
    """Apply digital filter to time series data.

    Supports low-pass, high-pass, and band-pass Butterworth filters.
    """

    @property
    def operation_type(self) -> str:
        return "filter"

    def _validate_config(self):
        """Validate filter configuration."""
        self.filter_type = self.config.get('filter_type', 'lowpass')
        if self.filter_type not in ['lowpass', 'highpass', 'bandpass']:
            raise ValueError(f"Invalid filter_type: {self.filter_type}")

        self.cutoff = self.config.get('cutoff')
        if self.cutoff is None:
            raise ValueError("cutoff frequency is required")

        # For bandpass, cutoff should be a list [low, high]
        if self.filter_type == 'bandpass':
            if not isinstance(self.cutoff, (list, tuple)) or len(self.cutoff) != 2:
                raise ValueError("bandpass filter requires cutoff as [low, high]")

        self.order = self.config.get('order', 4)  # Filter order

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Execute filter operation on time series data.

        Args:
            data: Input time series with columns [timestamp, channel_id, value]

        Returns:
            Filtered time series with same structure
        """
        logger.info(f"Executing {self.filter_type} filter (cutoff={self.cutoff} Hz, order={self.order})")

        results = []

        # Process each channel separately
        for channel_id in data['channel_id'].unique():
            channel_data = data[data['channel_id'] == channel_id].sort_values('timestamp')

            # Extract values and compute sample rate
            values = channel_data['value'].values
            timestamps = pd.to_datetime(channel_data['timestamp'])
            time_diffs = timestamps.diff().dt.total_seconds().dropna()
            sample_rate = 1.0 / time_diffs.mean() if len(time_diffs) > 0 else 1.0

            # Design Butterworth filter
            nyquist = sample_rate / 2.0

            if self.filter_type == 'bandpass':
                critical_freq = [self.cutoff[0] / nyquist, self.cutoff[1] / nyquist]
            else:
                critical_freq = self.cutoff / nyquist

            # Create filter coefficients
            b, a = signal.butter(
                self.order,
                critical_freq,
                btype=self.filter_type,
                analog=False
            )

            # Apply filter (forward and backward to avoid phase shift)
            filtered_values = signal.filtfilt(b, a, values)

            # Create result records
            for timestamp, value in zip(timestamps, filtered_values):
                results.append({
                    'timestamp': timestamp,
                    'channel_id': channel_id,
                    'value': value
                })

        result_df = pd.DataFrame(results)
        logger.info(f"Filter complete: {len(result_df)} samples across {data['channel_id'].nunique()} channels")

        return result_df
