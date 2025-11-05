"""Python SDK for Time Series Data Platform.

This module provides a high-level abstraction layer for interacting with the
Time Series Platform without needing to understand REST APIs or underlying components.
"""

import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class TimeSeriesClient:
    """High-level client for Time Series Data Platform.

    Example:
        >>> client = TimeSeriesClient("http://localhost:8000")
        >>> dataset_id = client.upload_dataset("data.csv", name="My Data")
        >>> workflow_id = client.create_workflow("My Workflow")
        >>> client.add_operation(workflow_id, "fft", dataset_id=dataset_id)
        >>> client.execute_workflow(workflow_id)
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client.

        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=300.0)  # 5 minute timeout
        logger.info(f"Initialized TimeSeriesClient with base_url: {self.base_url}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close HTTP client."""
        self.client.close()

    # Dataset operations

    def upload_dataset(
        self,
        file_path: Union[str, Path],
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> UUID:
        """Upload a time series dataset.

        Args:
            file_path: Path to CSV file
            name: Dataset name (defaults to filename)
            description: Optional description

        Returns:
            UUID of created dataset
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Uploading dataset: {file_path}")

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/csv")}
            data = {}
            if name:
                data["name"] = name
            if description:
                data["description"] = description

            response = self.client.post(
                f"{self.base_url}/api/datasets/upload",
                files=files,
                data=data
            )
            response.raise_for_status()

        result = response.json()
        dataset_id = UUID(result["id"])
        logger.info(f"Uploaded dataset: {dataset_id}")
        return dataset_id

    def get_dataset(self, dataset_id: UUID) -> Dict[str, Any]:
        """Get dataset metadata.

        Args:
            dataset_id: Dataset UUID

        Returns:
            Dataset metadata
        """
        response = self.client.get(f"{self.base_url}/api/datasets/{dataset_id}")
        response.raise_for_status()
        return response.json()

    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all datasets.

        Returns:
            List of dataset metadata
        """
        response = self.client.get(f"{self.base_url}/api/datasets/")
        response.raise_for_status()
        return response.json()

    def preview_dataset(self, dataset_id: UUID, limit: int = 100) -> Dict[str, Any]:
        """Preview dataset contents.

        Args:
            dataset_id: Dataset UUID
            limit: Number of rows to preview

        Returns:
            Data preview with columns and sample rows
        """
        response = self.client.get(
            f"{self.base_url}/api/datasets/{dataset_id}/preview",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    # Workflow operations

    def create_workflow(
        self,
        name: str,
        description: Optional[str] = None
    ) -> UUID:
        """Create a new workflow.

        Args:
            name: Workflow name
            description: Optional description

        Returns:
            UUID of created workflow
        """
        logger.info(f"Creating workflow: {name}")

        response = self.client.post(
            f"{self.base_url}/api/workflows/",
            json={"name": name, "description": description}
        )
        response.raise_for_status()

        result = response.json()
        workflow_id = UUID(result["id"])
        logger.info(f"Created workflow: {workflow_id}")
        return workflow_id

    def get_workflow(self, workflow_id: UUID) -> Dict[str, Any]:
        """Get workflow details.

        Args:
            workflow_id: Workflow UUID

        Returns:
            Workflow metadata
        """
        response = self.client.get(f"{self.base_url}/api/workflows/{workflow_id}")
        response.raise_for_status()
        return response.json()

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows.

        Returns:
            List of workflow metadata
        """
        response = self.client.get(f"{self.base_url}/api/workflows/")
        response.raise_for_status()
        return response.json()

    def get_workflow_dag(self, workflow_id: UUID) -> Dict[str, Any]:
        """Get workflow DAG structure.

        Args:
            workflow_id: Workflow UUID

        Returns:
            DAG structure with nodes and edges
        """
        response = self.client.get(f"{self.base_url}/api/workflows/{workflow_id}/dag")
        response.raise_for_status()
        return response.json()

    def execute_workflow(self, workflow_id: UUID) -> Dict[str, Any]:
        """Execute a workflow.

        Args:
            workflow_id: Workflow UUID

        Returns:
            Execution results
        """
        logger.info(f"Executing workflow: {workflow_id}")

        response = self.client.post(
            f"{self.base_url}/api/workflows/{workflow_id}/execute"
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"Workflow execution completed: {result}")
        return result

    # Node operations

    def add_operation(
        self,
        workflow_id: UUID,
        operation_type: str,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        dataset_id: Optional[UUID] = None
    ) -> UUID:
        """Add an operation node to a workflow.

        Args:
            workflow_id: Workflow UUID
            operation_type: Type of operation (fft, filter, unit_conversion)
            name: Node name (defaults to operation type)
            config: Operation-specific configuration
            dataset_id: Input dataset UUID (for first node)

        Returns:
            UUID of created node
        """
        logger.info(f"Adding {operation_type} operation to workflow {workflow_id}")

        node_data = {
            "workflow_id": str(workflow_id),
            "name": name or f"{operation_type} operation",
            "operation_type": operation_type,
            "operation_config": config or {},
        }

        if dataset_id:
            node_data["input_dataset_id"] = str(dataset_id)

        response = self.client.post(
            f"{self.base_url}/api/nodes/",
            json=node_data
        )
        response.raise_for_status()

        result = response.json()
        node_id = UUID(result["id"])
        logger.info(f"Created node: {node_id}")
        return node_id

    def connect_nodes(
        self,
        workflow_id: UUID,
        from_node_id: UUID,
        to_node_id: UUID
    ):
        """Connect two nodes in a workflow.

        Args:
            workflow_id: Workflow UUID
            from_node_id: Source node UUID
            to_node_id: Destination node UUID
        """
        logger.info(f"Connecting nodes: {from_node_id} -> {to_node_id}")

        response = self.client.post(
            f"{self.base_url}/api/workflows/{workflow_id}/edges",
            json={
                "workflow_id": str(workflow_id),
                "from_node_id": str(from_node_id),
                "to_node_id": str(to_node_id)
            }
        )
        response.raise_for_status()

    def get_node_output(
        self,
        node_id: UUID,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Get output data from a node.

        Args:
            node_id: Node UUID
            limit: Number of rows to return

        Returns:
            Node output data
        """
        response = self.client.get(
            f"{self.base_url}/api/nodes/{node_id}/data",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def get_node_plot(
        self,
        node_id: UUID,
        channel_id: int = 0,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Get plot data for a node.

        Args:
            node_id: Node UUID
            channel_id: Channel to plot
            limit: Number of points to return

        Returns:
            Plot data
        """
        response = self.client.get(
            f"{self.base_url}/api/nodes/{node_id}/plot",
            params={"channel_id": channel_id, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    # Convenience methods

    def create_simple_workflow(
        self,
        dataset_path: Union[str, Path],
        operations: List[Dict[str, Any]],
        workflow_name: str = "Simple Workflow"
    ) -> UUID:
        """Create and execute a simple linear workflow.

        Args:
            dataset_path: Path to CSV file
            operations: List of operation configs, e.g.,
                [{"type": "filter", "config": {"cutoff": 50, "filter_type": "lowpass"}},
                 {"type": "fft"}]
            workflow_name: Name for the workflow

        Returns:
            Workflow UUID

        Example:
            >>> client.create_simple_workflow(
            ...     "data.csv",
            ...     [
            ...         {"type": "filter", "config": {"cutoff": 50, "filter_type": "lowpass"}},
            ...         {"type": "fft"}
            ...     ]
            ... )
        """
        # Upload dataset
        dataset_id = self.upload_dataset(dataset_path)

        # Create workflow
        workflow_id = self.create_workflow(workflow_name)

        # Add operations and connect them
        prev_node_id = None
        for i, op in enumerate(operations):
            node_id = self.add_operation(
                workflow_id,
                op["type"],
                name=op.get("name", f"Step {i+1}: {op['type']}"),
                config=op.get("config"),
                dataset_id=dataset_id if i == 0 else None
            )

            if prev_node_id:
                self.connect_nodes(workflow_id, prev_node_id, node_id)

            prev_node_id = node_id

        return workflow_id

    def visualize_dag(self, workflow_id: UUID) -> str:
        """Get simple text visualization of DAG.

        Args:
            workflow_id: Workflow UUID

        Returns:
            Text representation of DAG
        """
        dag = self.get_workflow_dag(workflow_id)

        output = [f"Workflow: {dag['workflow_name']} ({dag['workflow_id']})"]
        output.append("\nNodes:")
        for node in dag['nodes']:
            output.append(f"  - {node['name']} ({node['operation_type']}) [{node['status']}]")

        output.append("\nConnections:")
        for edge in dag['edges']:
            from_node = next(n for n in dag['nodes'] if n['id'] == edge['from_node'])
            to_node = next(n for n in dag['nodes'] if n['id'] == edge['to_node'])
            output.append(f"  {from_node['name']} -> {to_node['name']}")

        return "\n".join(output)
