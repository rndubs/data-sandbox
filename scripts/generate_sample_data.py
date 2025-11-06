"""Generate sample time series data for testing and demonstration.

Creates realistic multi-channel time series data with:
- 10 channels
- 100 seconds at 1kHz (100,000 samples per channel)
- Mix of sine waves, noise, and transient events
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


def generate_channel_data(
    channel_id: int,
    num_samples: int,
    sample_rate: float,
    base_freq: float = 10.0,
    noise_level: float = 0.1
) -> np.ndarray:
    """Generate realistic time series data for a single channel.

    Args:
        channel_id: Channel identifier (affects frequency and phase)
        num_samples: Number of samples to generate
        sample_rate: Sampling frequency in Hz
        base_freq: Base frequency for signal generation
        noise_level: Noise amplitude relative to signal

    Returns:
        Array of samples
    """
    # Create time vector
    t = np.arange(num_samples) / sample_rate

    # Main signal: combination of sine waves at different frequencies
    freq1 = base_freq + channel_id * 2  # Unique frequency per channel
    freq2 = base_freq * 3 + channel_id  # Harmonic component
    signal = (
        np.sin(2 * np.pi * freq1 * t) +
        0.3 * np.sin(2 * np.pi * freq2 * t) +
        0.2 * np.sin(2 * np.pi * (freq1 / 2) * t)
    )

    # Add some transient events (spikes)
    event_times = [20, 50, 80]  # seconds
    for event_time in event_times:
        event_idx = int(event_time * sample_rate)
        if event_idx < num_samples:
            # Create a decaying exponential pulse
            pulse_duration = int(0.5 * sample_rate)  # 0.5 second pulse
            pulse_t = np.arange(pulse_duration) / sample_rate
            pulse = 2.0 * np.exp(-5 * pulse_t) * np.sin(2 * np.pi * 50 * pulse_t)

            end_idx = min(event_idx + pulse_duration, num_samples)
            actual_pulse_len = end_idx - event_idx
            signal[event_idx:end_idx] += pulse[:actual_pulse_len]

    # Add noise
    noise = noise_level * np.random.randn(num_samples)
    signal += noise

    return signal


def generate_dataset(
    num_channels: int = 10,
    duration_seconds: float = 100.0,
    sample_rate: float = 1000.0,
    output_path: Path = None
) -> pd.DataFrame:
    """Generate multi-channel time series dataset.

    Args:
        num_channels: Number of channels to generate
        duration_seconds: Duration in seconds
        sample_rate: Sampling frequency in Hz
        output_path: Path to save CSV file (optional)

    Returns:
        DataFrame with columns: timestamp, channel_id, value
    """
    num_samples = int(duration_seconds * sample_rate)

    # Generate timestamp array
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    timestamps = [
        start_time + timedelta(seconds=i / sample_rate)
        for i in range(num_samples)
    ]

    # Generate data for all channels
    data_records = []
    for channel_id in range(num_channels):
        print(f"Generating channel {channel_id + 1}/{num_channels}...")
        channel_data = generate_channel_data(
            channel_id=channel_id,
            num_samples=num_samples,
            sample_rate=sample_rate
        )

        # Create records for this channel
        for timestamp, value in zip(timestamps, channel_data):
            data_records.append({
                'timestamp': timestamp,
                'channel_id': channel_id,
                'value': value
            })

    # Create DataFrame
    df = pd.DataFrame(data_records)

    # Save to CSV if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\nDataset saved to: {output_path}")
        print(f"Total rows: {len(df):,}")
        print(f"File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

    return df


def print_dataset_info(df: pd.DataFrame):
    """Print summary information about the dataset."""
    print("\n" + "="*60)
    print("DATASET SUMMARY")
    print("="*60)
    print(f"Total rows: {len(df):,}")
    print(f"Channels: {df['channel_id'].nunique()}")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Duration: {(df['timestamp'].max() - df['timestamp'].min()).total_seconds():.2f} seconds")
    print(f"\nValue statistics:")
    print(df['value'].describe())
    print("\nFirst few rows:")
    print(df.head(10))
    print("="*60)


if __name__ == "__main__":
    # Generate sample dataset
    output_file = Path("data/sample_timeseries.csv")

    print("Generating sample time series dataset...")
    print(f"Configuration:")
    print(f"  - Channels: 10")
    print(f"  - Duration: 100 seconds")
    print(f"  - Sample rate: 1000 Hz")
    print(f"  - Total samples: 1,000,000\n")

    df = generate_dataset(
        num_channels=10,
        duration_seconds=100.0,
        sample_rate=1000.0,
        output_path=output_file
    )

    print_dataset_info(df)
