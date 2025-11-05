"""Workflow execution engine using Prefect."""

from typing import List, Dict, Any, Optional
from uuid import UUID
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
from prefect import flow, task
from sqlalchemy.orm import Session

from src.models import Workflow, Node, Edge, Dataset
from src.operations import create_operation
from src.data_layer import DuckDBClient, MinIOClient

logger = logging.getLogger(__name__)


@task(name="load_dataset")
def load_dataset_task(dataset_id: UUID, db_session: Session) -> pd.DataFrame:
    """Load dataset from storage.

    Args:
        dataset_id: UUID of dataset to load
        db_session: Database session

    Returns:
        DataFrame with time series data
    """
    logger.info(f"Loading dataset: {dataset_id}")

    # Get dataset metadata
    dataset = db_session.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise ValueError(f"Dataset not found: {dataset_id}")

    # Download from MinIO to temp location
    minio_client = MinIOClient()
    temp_path = Path(f"/tmp/{dataset_id}.csv")
    minio_client.download_file(dataset.file_location, temp_path)

    # Load into DuckDB
    duckdb_client = DuckDBClient()
    table_name = f"dataset_{str(dataset_id).replace('-', '_')}"
    table = duckdb_client.load_csv(str(temp_path), table_name)

    # Get all data
    df = duckdb_client.get_all_channels(table_name)

    logger.info(f"Loaded {len(df)} rows from dataset {dataset_id}")
    return df


@task(name="execute_operation")
def execute_operation_task(
    node_id: UUID,
    operation_type: str,
    operation_config: Dict[str, Any],
    input_data: pd.DataFrame,
    db_session: Session
) -> tuple[pd.DataFrame, UUID]:
    """Execute a single operation.

    Args:
        node_id: UUID of the node
        operation_type: Type of operation to execute
        operation_config: Operation configuration
        input_data: Input DataFrame
        db_session: Database session

    Returns:
        Tuple of (output DataFrame, output dataset UUID)
    """
    logger.info(f"Executing node {node_id}: {operation_type}")

    start_time = datetime.utcnow()

    try:
        # Create and execute operation
        operation = create_operation(operation_type, operation_config)
        output_data = operation.execute(input_data)

        # Save output to MinIO
        minio_client = MinIOClient()
        output_filename = f"output_{node_id}.csv"
        temp_output = Path(f"/tmp/{output_filename}")
        output_data.to_csv(temp_output, index=False)
        minio_client.upload_file(temp_output, output_filename)

        # Create dataset record
        dataset = Dataset(
            name=f"Output of {operation_type} (node {node_id})",
            file_location=output_filename,
            row_count=len(output_data),
        )
        db_session.add(dataset)
        db_session.flush()

        # Update node with output dataset
        node = db_session.query(Node).filter(Node.id == node_id).first()
        node.output_dataset_id = dataset.id
        node.status = "completed"
        node.execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        node.completed_at = datetime.utcnow()

        db_session.commit()

        logger.info(f"Node {node_id} completed successfully")
        return output_data, dataset.id

    except Exception as e:
        # Update node with error
        node = db_session.query(Node).filter(Node.id == node_id).first()
        node.status = "failed"
        node.error_message = str(e)
        db_session.commit()

        logger.error(f"Node {node_id} failed: {e}")
        raise


@flow(name="execute_workflow")
def execute_workflow_flow(workflow_id: UUID, db_session: Session) -> Dict[str, Any]:
    """Execute a complete workflow.

    Args:
        workflow_id: UUID of workflow to execute
        db_session: Database session

    Returns:
        Dictionary with execution results
    """
    logger.info(f"Starting workflow execution: {workflow_id}")

    # Get workflow and nodes
    workflow = db_session.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise ValueError(f"Workflow not found: {workflow_id}")

    # Update workflow status
    workflow.status = "running"
    db_session.commit()

    try:
        # Get all nodes and edges
        nodes = db_session.query(Node).filter(Node.workflow_id == workflow_id).all()
        edges = db_session.query(Edge).filter(Edge.workflow_id == workflow_id).all()

        # Build dependency graph
        node_map = {node.id: node for node in nodes}
        dependencies = {node.id: [] for node in nodes}

        for edge in edges:
            dependencies[edge.to_node_id].append(edge.from_node_id)

        # Find nodes with no dependencies (starting nodes)
        starting_nodes = [
            node_id for node_id, deps in dependencies.items()
            if len(deps) == 0
        ]

        # Topological sort to determine execution order
        execution_order = topological_sort(dependencies)

        # Execute nodes in order
        node_outputs = {}

        for node_id in execution_order:
            node = node_map[node_id]

            # Get input data
            if node.input_dataset_id:
                # Load from dataset
                input_data = load_dataset_task(node.input_dataset_id, db_session)
            elif dependencies[node_id]:
                # Use output from previous node
                prev_node_id = dependencies[node_id][0]  # For POC, assume single input
                input_data = node_outputs[prev_node_id]
            else:
                raise ValueError(f"Node {node_id} has no input data source")

            # Execute operation
            output_data, output_dataset_id = execute_operation_task(
                node_id,
                node.operation_type,
                node.operation_config or {},
                input_data,
                db_session
            )

            node_outputs[node_id] = output_data

        # Update workflow status
        workflow.status = "completed"
        workflow.completed_at = datetime.utcnow()
        db_session.commit()

        logger.info(f"Workflow {workflow_id} completed successfully")

        return {
            'workflow_id': str(workflow_id),
            'status': 'completed',
            'nodes_executed': len(execution_order)
        }

    except Exception as e:
        # Update workflow status
        workflow.status = "failed"
        db_session.commit()

        logger.error(f"Workflow {workflow_id} failed: {e}")
        raise


def topological_sort(dependencies: Dict[UUID, List[UUID]]) -> List[UUID]:
    """Perform topological sort on dependency graph.

    Args:
        dependencies: Map of node_id -> list of dependency node_ids

    Returns:
        List of node_ids in execution order
    """
    # Kahn's algorithm
    in_degree = {node: len(deps) for node, deps in dependencies.items()}
    queue = [node for node, degree in in_degree.items() if degree == 0]
    result = []

    while queue:
        node = queue.pop(0)
        result.append(node)

        # Decrease in-degree for dependent nodes
        for dependent, deps in dependencies.items():
            if node in deps:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    if len(result) != len(dependencies):
        raise ValueError("Cycle detected in workflow graph")

    return result


class WorkflowExecutor:
    """High-level workflow execution interface."""

    def __init__(self, db_session: Session):
        """Initialize executor.

        Args:
            db_session: Database session
        """
        self.db_session = db_session

    def execute(self, workflow_id: UUID) -> Dict[str, Any]:
        """Execute a workflow.

        Args:
            workflow_id: UUID of workflow to execute

        Returns:
            Execution results
        """
        return execute_workflow_flow(workflow_id, self.db_session)
