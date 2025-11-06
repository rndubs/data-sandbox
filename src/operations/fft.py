"""FFT (Fast Fourier Transform) operation for frequency domain analysis."""

import numpy as np
import pandas as pd
from typing import Dict, Any
from scipy.fft import fft, fftfreq
import logging

from src.operations.base import Operation

logger = logging.getLogger(__name__)


class FFTOperation(Operation):
    """Compute FFT to transform time series to frequency domain.

    Converts time-domain signals to frequency-domain representation.
    Output columns: frequency (Hz), magnitude, phase (radians), channel_id
    """

    @property
    def operation_type(self) -> str:
        return "fft"

    def _validate_config(self):
        """Validate FFT configuration."""
        # Optional config parameters
        self.window = self.config.get('window', None)  # Window function (e.g., 'hann', 'hamming')
        self.normalize = self.config.get('normalize', True)  # Normalize magnitude

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Execute FFT on time series data.

        Args:
            data: Input time series with columns [timestamp, channel_id, value]

        Returns:
            Frequency domain data with columns [frequency, magnitude, phase, channel_id]
        """
        logger.info(f"Executing FFT operation on {len(data)} samples")

        results = []

        # Process each channel separately
        for channel_id in data['channel_id'].unique():
            channel_data = data[data['channel_id'] == channel_id].sort_values('timestamp')

            # Extract values and compute sample rate
            values = channel_data['value'].values
            timestamps = pd.to_datetime(channel_data['timestamp'])
            time_diffs = timestamps.diff().dt.total_seconds().dropna()
            sample_rate = 1.0 / time_diffs.mean() if len(time_diffs) > 0 else 1.0

            # Apply window function if specified
            if self.window:
                if self.window == 'hann':
                    window = np.hanning(len(values))
                elif self.window == 'hamming':
                    window = np.hamming(len(values))
                elif self.window == 'blackman':
                    window = np.blackman(len(values))
                else:
                    logger.warning(f"Unknown window type: {self.window}, using no window")
                    window = np.ones(len(values))
                values = values * window

            # Compute FFT
            fft_values = fft(values)
            frequencies = fftfreq(len(values), d=1.0/sample_rate)

            # Take only positive frequencies
            positive_freq_idx = frequencies >= 0
            frequencies = frequencies[positive_freq_idx]
            fft_values = fft_values[positive_freq_idx]

            # Compute magnitude and phase
            magnitude = np.abs(fft_values)
            phase = np.angle(fft_values)

            # Normalize if requested
            if self.normalize:
                magnitude = magnitude / len(values)

            # Create result records
            for freq, mag, ph in zip(frequencies, magnitude, phase):
                results.append({
                    'frequency': freq,
                    'magnitude': mag,
                    'phase': ph,
                    'channel_id': channel_id
                })

        result_df = pd.DataFrame(results)
        logger.info(f"FFT complete: {len(result_df)} frequency bins across {data['channel_id'].nunique()} channels")

        return result_df
