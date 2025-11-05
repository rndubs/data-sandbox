"""Integration tests for the Time Series Platform.

These tests verify the end-to-end functionality without mocks.
They require the services to be running (docker-compose up).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk.client import TimeSeriesClient


@pytest.fixture
def client():
    """Create SDK client."""
    return TimeSeriesClient("http://localhost:8000")


@pytest.fixture
def sample_dataset():
    """Create a temporary sample dataset."""
    # Generate small dataset
    num_samples = 1000
    timestamps = pd.date_range('2024-01-01', periods=num_samples, freq='1ms')

    data = []
    for channel_id in range(2):  # 2 channels
        for i, ts in enumerate(timestamps):
            # Simple sine wave
            value = np.sin(2 * np.pi * 10 * i / 1000)  # 10 Hz signal
            data.append({
                'timestamp': ts,
                'channel_id': channel_id,
                'value': value
            })

    df = pd.DataFrame(data)

    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    df.to_csv(temp_file.name, index=False)

    yield Path(temp_file.name)

    # Cleanup
    Path(temp_file.name).unlink()


def test_health_check(client):
    """Test that the API is responsive."""
    import httpx
    response = httpx.get("http://localhost:8000/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_upload_dataset(client, sample_dataset):
    """Test dataset upload."""
    dataset_id = client.upload_dataset(
        sample_dataset,
        name="Test Dataset",
        description="Integration test dataset"
    )

    assert dataset_id is not None

    # Verify dataset metadata
    metadata = client.get_dataset(dataset_id)
    assert metadata["name"] == "Test Dataset"
    assert metadata["row_count"] == 2000  # 2 channels * 1000 samples


def test_create_workflow(client):
    """Test workflow creation."""
    workflow_id = client.create_workflow(
        name="Test Workflow",
        description="Integration test workflow"
    )

    assert workflow_id is not None

    # Verify workflow
    workflow = client.get_workflow(workflow_id)
    assert workflow["name"] == "Test Workflow"
    assert workflow["status"] == "draft"


def test_simple_workflow_execution(client, sample_dataset):
    """Test complete workflow execution."""
    # Upload dataset
    dataset_id = client.upload_dataset(sample_dataset, name="Test Data")

    # Create workflow
    workflow_id = client.create_workflow("Integration Test Workflow")

    # Add FFT operation
    fft_node = client.add_operation(
        workflow_id,
        operation_type="fft",
        name="FFT Transform",
        config={"normalize": True},
        dataset_id=dataset_id
    )

    # Execute workflow
    result = client.execute_workflow(workflow_id)

    assert result["status"] == "completed"
    assert result["nodes_executed"] == 1

    # Verify output exists
    output = client.get_node_output(fft_node, limit=10)
    assert len(output["data"]) > 0
    assert "frequency" in output["columns"]
    assert "magnitude" in output["columns"]


def test_filter_operation(client, sample_dataset):
    """Test filter operation."""
    # Upload dataset
    dataset_id = client.upload_dataset(sample_dataset, name="Filter Test Data")

    # Create workflow
    workflow_id = client.create_workflow("Filter Test Workflow")

    # Add low-pass filter
    filter_node = client.add_operation(
        workflow_id,
        operation_type="filter",
        name="Low-pass Filter",
        config={
            "filter_type": "lowpass",
            "cutoff": 20,  # 20 Hz cutoff
            "order": 4
        },
        dataset_id=dataset_id
    )

    # Execute
    result = client.execute_workflow(workflow_id)
    assert result["status"] == "completed"

    # Verify output has same structure as input
    output = client.get_node_output(filter_node, limit=10)
    assert "timestamp" in output["columns"]
    assert "channel_id" in output["columns"]
    assert "value" in output["columns"]


def test_unit_conversion(client, sample_dataset):
    """Test unit conversion operation."""
    # Upload dataset
    dataset_id = client.upload_dataset(sample_dataset, name="Unit Test Data")

    # Create workflow
    workflow_id = client.create_workflow("Unit Conversion Workflow")

    # Add unit conversion
    conv_node = client.add_operation(
        workflow_id,
        operation_type="unit_conversion",
        name="Scale by 2",
        config={
            "conversion": "scale",
            "factor": 2.0
        },
        dataset_id=dataset_id
    )

    # Execute
    result = client.execute_workflow(workflow_id)
    assert result["status"] == "completed"

    # Verify output
    output = client.get_node_output(conv_node, limit=1)
    assert len(output["data"]) > 0


def test_multi_operation_workflow(client, sample_dataset):
    """Test workflow with multiple connected operations."""
    # Upload dataset
    dataset_id = client.upload_dataset(sample_dataset, name="Multi-op Test Data")

    # Create workflow
    workflow_id = client.create_workflow("Multi-Operation Workflow")

    # Add operations
    filter_node = client.add_operation(
        workflow_id,
        operation_type="filter",
        name="Low-pass Filter",
        config={
            "filter_type": "lowpass",
            "cutoff": 30,
            "order": 4
        },
        dataset_id=dataset_id
    )

    fft_node = client.add_operation(
        workflow_id,
        operation_type="fft",
        name="FFT Analysis",
        config={"normalize": True}
    )

    # Connect operations
    client.connect_nodes(workflow_id, filter_node, fft_node)

    # Verify DAG structure
    dag = client.get_workflow_dag(workflow_id)
    assert len(dag["nodes"]) == 2
    assert len(dag["edges"]) == 1

    # Execute workflow
    result = client.execute_workflow(workflow_id)
    assert result["status"] == "completed"
    assert result["nodes_executed"] == 2

    # Verify both nodes have output
    filter_output = client.get_node_output(filter_node, limit=1)
    fft_output = client.get_node_output(fft_node, limit=1)

    assert len(filter_output["data"]) > 0
    assert len(fft_output["data"]) > 0


def test_workflow_dag_visualization(client, sample_dataset):
    """Test DAG retrieval and structure."""
    # Create workflow with operations
    dataset_id = client.upload_dataset(sample_dataset, name="DAG Test Data")
    workflow_id = client.create_workflow("DAG Test Workflow")

    node1 = client.add_operation(
        workflow_id,
        "filter",
        config={"filter_type": "lowpass", "cutoff": 50},
        dataset_id=dataset_id
    )

    node2 = client.add_operation(workflow_id, "fft")
    client.connect_nodes(workflow_id, node1, node2)

    # Get DAG
    dag = client.get_workflow_dag(workflow_id)

    assert "nodes" in dag
    assert "edges" in dag
    assert len(dag["nodes"]) == 2
    assert len(dag["edges"]) == 1

    # Verify node structure
    for node in dag["nodes"]:
        assert "id" in node
        assert "name" in node
        assert "operation_type" in node
        assert "status" in node

    # Verify edge structure
    for edge in dag["edges"]:
        assert "from_node" in edge
        assert "to_node" in edge


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
