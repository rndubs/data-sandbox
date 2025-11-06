"""API routes for node management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pathlib import Path
import pandas as pd
import logging

from src.database import get_db_session
from src.models import Node, Workflow
from src.api.schemas import NodeCreate, NodeResponse, DataPreview, PlotData
from src.data_layer import MinIOClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=NodeResponse, status_code=201)
def create_node(
    node: NodeCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new node in a workflow.

    Args:
        node: Node creation data
        db: Database session

    Returns:
        Created node
    """
    # Verify workflow exists
    workflow = db.query(Workflow).filter(Workflow.id == node.workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    db_node = Node(
        workflow_id=node.workflow_id,
        name=node.name,
        operation_type=node.operation_type,
        operation_config=node.operation_config,
        input_dataset_id=node.input_dataset_id
    )

    db.add(db_node)
    db.commit()
    db.refresh(db_node)

    logger.info(f"Created node {db_node.id}: {db_node.name}")
    return db_node


@router.get("/{node_id}", response_model=NodeResponse)
def get_node(
    node_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get node by ID.

    Args:
        node_id: Node UUID
        db: Database session

    Returns:
        Node details
    """
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/{node_id}/data", response_model=DataPreview)
def get_node_output_data(
    node_id: UUID,
    limit: int = 1000,
    db: Session = Depends(get_db_session)
):
    """Get output data from a node.

    Args:
        node_id: Node UUID
        limit: Number of rows to return
        db: Database session

    Returns:
        Node output data preview
    """
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if not node.output_dataset_id:
        raise HTTPException(status_code=400, detail="Node has not been executed yet")

    try:
        # Get output dataset
        from src.models import Dataset
        dataset = db.query(Dataset).filter(Dataset.id == node.output_dataset_id).first()

        # Download from MinIO
        minio_client = MinIOClient()
        temp_path = Path(f"/tmp/node_output_{node_id}.csv")
        minio_client.download_file(dataset.file_location, temp_path)

        # Load and preview
        df = pd.read_csv(temp_path, nrows=limit)

        return DataPreview(
            columns=df.columns.tolist(),
            data=df.to_dict('records'),
            total_rows=dataset.row_count or len(df),
            preview_rows=len(df)
        )

    except Exception as e:
        logger.error(f"Error getting node output data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{node_id}/plot")
def get_node_plot_data(
    node_id: UUID,
    channel_id: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db_session)
):
    """Get plot data for a node's output.

    Args:
        node_id: Node UUID
        channel_id: Channel to plot
        limit: Number of points to return
        db: Database session

    Returns:
        Plot data for visualization
    """
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    if not node.output_dataset_id:
        raise HTTPException(status_code=400, detail="Node has not been executed yet")

    try:
        # Get output dataset
        from src.models import Dataset
        dataset = db.query(Dataset).filter(Dataset.id == node.output_dataset_id).first()

        # Download from MinIO
        minio_client = MinIOClient()
        temp_path = Path(f"/tmp/node_plot_{node_id}.csv")
        minio_client.download_file(dataset.file_location, temp_path)

        # Load data
        df = pd.read_csv(temp_path)

        # Filter by channel if column exists
        if 'channel_id' in df.columns:
            df = df[df['channel_id'] == channel_id]

        # Limit rows
        df = df.head(limit)

        # Determine plot type based on columns
        if 'frequency' in df.columns:
            # FFT output
            x = df['frequency'].tolist()
            y = df['magnitude'].tolist()
            x_label = "Frequency (Hz)"
            y_label = "Magnitude"
            title = f"Frequency Domain - Channel {channel_id}"
        elif 'timestamp' in df.columns:
            # Time series
            x = df['timestamp'].tolist()
            y = df['value'].tolist()
            x_label = "Time"
            y_label = "Value"
            title = f"Time Series - Channel {channel_id}"
        else:
            raise HTTPException(status_code=400, detail="Unknown data format")

        return PlotData(
            channel_id=channel_id,
            x=x,
            y=y,
            x_label=x_label,
            y_label=y_label,
            title=title
        )

    except Exception as e:
        logger.error(f"Error getting plot data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{node_id}", status_code=204)
def delete_node(
    node_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Delete a node.

    Args:
        node_id: Node UUID
        db: Database session
    """
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    db.delete(node)
    db.commit()

    logger.info(f"Deleted node {node_id}")
