"""Create sample workflows for testing the frontend."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk.client import TimeSeriesClient


def main():
    # Initialize client
    print("Connecting to Time Series Platform...")
    client = TimeSeriesClient("http://localhost:8000")

    # Get existing datasets
    print("\n1. Getting existing datasets...")
    datasets = client.list_datasets()

    if not datasets:
        print("No datasets found. Please upload some datasets first.")
        return

    print(f"Found {len(datasets)} datasets")

    # Use the first dataset for all workflows
    dataset_id = datasets[0]['id']
    dataset_name = datasets[0].get('name', 'Unknown')
    print(f"Using dataset: {dataset_name} ({dataset_id})")

    # Create workflow 1: Simple Filter
    print("\n2. Creating Workflow 1: Low-pass Filter...")
    workflow_id_1 = client.create_workflow(
        name="Low-pass Filter (50Hz)",
        description="Simple low-pass filter at 50Hz to remove high-frequency noise"
    )
    print(f"✓ Workflow created: {workflow_id_1}")

    filter_node_1 = client.add_operation(
        workflow_id_1,
        operation_type="filter",
        name="Low-pass filter",
        config={
            "filter_type": "lowpass",
            "cutoff": 50,
            "order": 4
        },
        dataset_id=dataset_id
    )
    print(f"✓ Added filter operation: {filter_node_1}")

    # Create workflow 2: Filter + FFT
    print("\n3. Creating Workflow 2: Signal Processing Pipeline...")
    workflow_id_2 = client.create_workflow(
        name="Filter + FFT Analysis",
        description="Low-pass filter followed by FFT for frequency analysis"
    )
    print(f"✓ Workflow created: {workflow_id_2}")

    filter_node_2 = client.add_operation(
        workflow_id_2,
        operation_type="filter",
        name="Low-pass filter (50Hz)",
        config={
            "filter_type": "lowpass",
            "cutoff": 50,
            "order": 4
        },
        dataset_id=dataset_id
    )
    print(f"✓ Added filter operation: {filter_node_2}")

    fft_node = client.add_operation(
        workflow_id_2,
        operation_type="fft",
        name="FFT Analysis",
        config={
            "normalize": True,
            "window": "hann"
        }
    )
    print(f"✓ Added FFT operation: {fft_node}")

    client.connect_nodes(workflow_id_2, filter_node_2, fft_node)
    print("✓ Operations connected")

    # Create workflow 3: Multiple Filters
    print("\n4. Creating Workflow 3: Multiple Filter Chain...")
    workflow_id_3 = client.create_workflow(
        name="Multi-stage Filter",
        description="High-pass filter followed by low-pass filter (band-pass effect)"
    )
    print(f"✓ Workflow created: {workflow_id_3}")

    highpass_node = client.add_operation(
        workflow_id_3,
        operation_type="filter",
        name="High-pass filter (10Hz)",
        config={
            "filter_type": "highpass",
            "cutoff": 10,
            "order": 3
        },
        dataset_id=dataset_id
    )
    print(f"✓ Added high-pass filter: {highpass_node}")

    lowpass_node = client.add_operation(
        workflow_id_3,
        operation_type="filter",
        name="Low-pass filter (100Hz)",
        config={
            "filter_type": "lowpass",
            "cutoff": 100,
            "order": 3
        }
    )
    print(f"✓ Added low-pass filter: {lowpass_node}")

    client.connect_nodes(workflow_id_3, highpass_node, lowpass_node)
    print("✓ Operations connected")

    # If there are more datasets, create a workflow for the second one
    if len(datasets) > 1:
        dataset_id_2 = datasets[1]['id']
        dataset_name_2 = datasets[1].get('name', 'Unknown')

        print(f"\n5. Creating Workflow 4 using dataset: {dataset_name_2}...")
        workflow_id_4 = client.create_workflow(
            name="Unit Conversion + Filter",
            description="Convert units and apply filtering"
        )
        print(f"✓ Workflow created: {workflow_id_4}")

        conversion_node = client.add_operation(
            workflow_id_4,
            operation_type="unit_conversion",
            name="Convert to millivolts",
            config={
                "from_unit": "V",
                "to_unit": "mV"
            },
            dataset_id=dataset_id_2
        )
        print(f"✓ Added unit conversion: {conversion_node}")

        filter_node_4 = client.add_operation(
            workflow_id_4,
            operation_type="filter",
            name="Low-pass filter (30Hz)",
            config={
                "filter_type": "lowpass",
                "cutoff": 30,
                "order": 5
            }
        )
        print(f"✓ Added filter: {filter_node_4}")

        client.connect_nodes(workflow_id_4, conversion_node, filter_node_4)
        print("✓ Operations connected")

    print("\n" + "="*60)
    print("SUCCESS! Sample workflows created.")
    print("="*60)
    print("\nYou can now view these workflows in the frontend.")

    # Close client
    client.close()


if __name__ == "__main__":
    main()
