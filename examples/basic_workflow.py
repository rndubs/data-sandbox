"""Example: Basic workflow using the Time Series Platform SDK.

This example demonstrates:
1. Uploading a dataset
2. Creating a workflow
3. Adding operations (filter -> FFT)
4. Executing the workflow
5. Retrieving results
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk.client import TimeSeriesClient


def main():
    # Initialize client
    print("Connecting to Time Series Platform...")
    client = TimeSeriesClient("http://localhost:8000")

    # Upload dataset
    print("\n1. Uploading sample dataset...")
    dataset_path = Path("data/sample_timeseries.csv")

    if not dataset_path.exists():
        print(f"Error: Sample dataset not found at {dataset_path}")
        print("Please run: python scripts/generate_sample_data.py")
        return

    dataset_id = client.upload_dataset(
        dataset_path,
        name="Sample Time Series Data",
        description="10 channels at 1kHz for 100 seconds"
    )
    print(f"✓ Dataset uploaded: {dataset_id}")

    # Preview dataset
    print("\n2. Previewing dataset...")
    preview = client.preview_dataset(dataset_id, limit=5)
    print(f"✓ Dataset has {preview['total_rows']} rows")
    print(f"  Columns: {preview['columns']}")
    print(f"  First few rows: {preview['data'][:2]}")

    # Create workflow
    print("\n3. Creating workflow...")
    workflow_id = client.create_workflow(
        name="Signal Processing Pipeline",
        description="Low-pass filter followed by FFT analysis"
    )
    print(f"✓ Workflow created: {workflow_id}")

    # Add operations
    print("\n4. Adding operations...")

    # First operation: Low-pass filter at 50Hz
    filter_node = client.add_operation(
        workflow_id,
        operation_type="filter",
        name="Low-pass filter (50Hz)",
        config={
            "filter_type": "lowpass",
            "cutoff": 50,
            "order": 4
        },
        dataset_id=dataset_id  # Input dataset
    )
    print(f"✓ Added filter operation: {filter_node}")

    # Second operation: FFT
    fft_node = client.add_operation(
        workflow_id,
        operation_type="fft",
        name="FFT Analysis",
        config={
            "normalize": True,
            "window": "hann"
        }
    )
    print(f"✓ Added FFT operation: {fft_node}")

    # Connect nodes
    print("\n5. Connecting operations...")
    client.connect_nodes(workflow_id, filter_node, fft_node)
    print("✓ Operations connected")

    # Visualize DAG
    print("\n6. Workflow DAG:")
    dag_text = client.visualize_dag(workflow_id)
    print(dag_text)

    # Execute workflow
    print("\n7. Executing workflow...")
    result = client.execute_workflow(workflow_id)
    print(f"✓ Workflow execution completed!")
    print(f"  Status: {result['status']}")
    print(f"  Nodes executed: {result['nodes_executed']}")

    # Get results
    print("\n8. Retrieving results...")

    # Get filter output
    print("\n  Filter output (first 5 rows):")
    filter_output = client.get_node_output(filter_node, limit=5)
    for row in filter_output['data'][:5]:
        print(f"    {row}")

    # Get FFT output
    print("\n  FFT output (first 5 frequency bins):")
    fft_output = client.get_node_output(fft_node, limit=5)
    for row in fft_output['data'][:5]:
        print(f"    {row}")

    # Get plot data
    print("\n9. Getting plot data for visualization...")
    plot_data = client.get_node_plot(fft_node, channel_id=0, limit=100)
    print(f"✓ Plot ready: {plot_data['title']}")
    print(f"  X-axis: {plot_data['x_label']}")
    print(f"  Y-axis: {plot_data['y_label']}")
    print(f"  Data points: {len(plot_data['x'])}")

    print("\n" + "="*60)
    print("SUCCESS! Workflow completed.")
    print("="*60)

    # Close client
    client.close()


if __name__ == "__main__":
    main()
