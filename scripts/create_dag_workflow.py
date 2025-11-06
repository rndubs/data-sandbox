"""Create a DAG workflow sample with two branches.

This script creates:
1. A time-domain signal composed of two frequencies (using numpy/scipy)
2. A workflow with two branches:
   - Branch 1: units shift -> FFT
   - Branch 2: units shift -> time shift (10% of time length) -> FFT
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk.client import TimeSeriesClient


def generate_two_frequency_signal(
    duration_seconds: float = 10.0,
    sample_rate: float = 1000.0,
    freq1: float = 5.0,
    freq2: float = 20.0,
    amplitude1: float = 1.0,
    amplitude2: float = 0.5,
    num_channels: int = 3
) -> pd.DataFrame:
    """Generate a time series signal composed of two frequency components.

    Args:
        duration_seconds: Duration of the signal in seconds
        sample_rate: Sampling rate in Hz
        freq1: First frequency component in Hz
        freq2: Second frequency component in Hz
        amplitude1: Amplitude of first frequency
        amplitude2: Amplitude of second frequency
        num_channels: Number of channels to generate

    Returns:
        DataFrame with columns: timestamp, channel_id, value
    """
    # Generate time array
    num_samples = int(duration_seconds * sample_rate)
    time_array = np.linspace(0, duration_seconds, num_samples, endpoint=False)

    # Generate base timestamp
    start_time = datetime.now()

    # Create the signal: sum of two sine waves
    signal = (amplitude1 * np.sin(2 * np.pi * freq1 * time_array) +
              amplitude2 * np.sin(2 * np.pi * freq2 * time_array))

    # Add some noise
    signal += np.random.normal(0, 0.05, num_samples)

    # Create DataFrame with multiple channels
    records = []
    for channel_id in range(num_channels):
        # Add slight variation per channel
        channel_signal = signal * (1 + 0.1 * channel_id)

        for i, t in enumerate(time_array):
            timestamp = start_time + timedelta(seconds=float(t))
            records.append({
                'timestamp': timestamp,
                'channel_id': f'channel_{channel_id}',
                'value': channel_signal[i]
            })

    df = pd.DataFrame(records)
    return df


def main():
    print("="*60)
    print("Creating DAG Workflow with Two Branches")
    print("="*60)

    # Initialize client
    print("\n1. Connecting to Time Series Platform...")
    client = TimeSeriesClient("http://localhost:8000")

    # Generate two-frequency signal
    print("\n2. Generating two-frequency time series signal...")
    print("   - Frequency 1: 5 Hz (amplitude 1.0)")
    print("   - Frequency 2: 20 Hz (amplitude 0.5)")
    print("   - Duration: 10 seconds")
    print("   - Sample rate: 1000 Hz")
    print("   - Channels: 3")

    df = generate_two_frequency_signal(
        duration_seconds=10.0,
        sample_rate=1000.0,
        freq1=5.0,
        freq2=20.0,
        amplitude1=1.0,
        amplitude2=0.5,
        num_channels=3
    )

    print(f"   Generated {len(df)} samples")

    # Save to CSV and upload
    print("\n3. Uploading dataset to platform...")
    temp_csv_path = Path("/tmp/two_frequency_signal.csv")
    df.to_csv(temp_csv_path, index=False)

    dataset_id = client.upload_dataset(
        file_path=str(temp_csv_path),
        name="Two-Frequency Signal (5Hz + 20Hz)"
    )
    print(f"   ✓ Dataset uploaded: {dataset_id}")

    # Clean up temp file
    temp_csv_path.unlink()

    # Create workflow with DAG structure
    print("\n4. Creating DAG workflow with two branches...")
    workflow_id = client.create_workflow(
        name="DAG: Dual FFT Analysis with Time Shift",
        description="Branching workflow: (1) units->FFT and (2) units->time_shift->FFT"
    )
    print(f"   ✓ Workflow created: {workflow_id}")

    # Add unit conversion node (common parent for both branches)
    print("\n5. Adding unit conversion node (mV to V)...")
    units_node = client.add_operation(
        workflow_id,
        operation_type="unit_conversion",
        name="Convert mV to V",
        config={
            "conversion": "mv_to_v"
        },
        dataset_id=dataset_id
    )
    print(f"   ✓ Node created: {units_node}")

    # Branch 1: Direct FFT
    print("\n6. Creating Branch 1: Units -> FFT...")
    fft_node_1 = client.add_operation(
        workflow_id,
        operation_type="fft",
        name="FFT (Branch 1: No time shift)",
        config={
            "normalize": True,
            "window": "hann"
        }
    )
    print(f"   ✓ FFT node created: {fft_node_1}")

    client.connect_nodes(workflow_id, units_node, fft_node_1)
    print("   ✓ Connected: units -> fft_1")

    # Branch 2: Time shift then FFT
    print("\n7. Creating Branch 2: Units -> Time Shift -> FFT...")

    # Calculate 10% of time length (10 seconds * 0.1 = 1 second)
    time_shift_seconds = 10.0 * 0.1

    time_shift_node = client.add_operation(
        workflow_id,
        operation_type="time_shift",
        name=f"Time Shift (+{time_shift_seconds}s)",
        config={
            "shift_seconds": time_shift_seconds
        }
    )
    print(f"   ✓ Time shift node created: {time_shift_node}")

    fft_node_2 = client.add_operation(
        workflow_id,
        operation_type="fft",
        name="FFT (Branch 2: After time shift)",
        config={
            "normalize": True,
            "window": "hann"
        }
    )
    print(f"   ✓ FFT node created: {fft_node_2}")

    client.connect_nodes(workflow_id, units_node, time_shift_node)
    print("   ✓ Connected: units -> time_shift")

    client.connect_nodes(workflow_id, time_shift_node, fft_node_2)
    print("   ✓ Connected: time_shift -> fft_2")

    # Print DAG structure
    print("\n8. DAG Structure:")
    print("   ")
    print("                  ┌─> FFT (Branch 1)")
    print("   Dataset ─> Units ─┤")
    print("                  └─> Time Shift ─> FFT (Branch 2)")

    print("\n" + "="*60)
    print("SUCCESS! DAG workflow created with two branches.")
    print("="*60)
    print(f"\nWorkflow ID: {workflow_id}")
    print(f"Dataset ID: {dataset_id}")
    print("\nYou can now:")
    print("  1. View the workflow in the web frontend")
    print("  2. Execute the workflow to see both FFT results")
    print("  3. Compare the FFTs with and without time shift")

    # Close client
    client.close()


if __name__ == "__main__":
    main()
