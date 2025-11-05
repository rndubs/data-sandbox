"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


# Dataset schemas
class DatasetCreate(BaseModel):
    """Schema for creating a dataset."""
    name: str
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    """Schema for dataset response."""
    id: UUID
    name: str
    description: Optional[str]
    file_location: str
    row_count: Optional[int]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    channel_count: Optional[int]
    sample_rate: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# Workflow schemas
class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""
    name: str
    description: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Schema for workflow response."""
    id: UUID
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Node schemas
class NodeCreate(BaseModel):
    """Schema for creating a node."""
    workflow_id: UUID
    name: str
    operation_type: str
    operation_config: Optional[Dict[str, Any]] = None
    input_dataset_id: Optional[UUID] = None


class NodeResponse(BaseModel):
    """Schema for node response."""
    id: UUID
    workflow_id: UUID
    name: str
    operation_type: str
    operation_config: Optional[Dict[str, Any]]
    input_dataset_id: Optional[UUID]
    output_dataset_id: Optional[UUID]
    status: str
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# Edge schemas
class EdgeCreate(BaseModel):
    """Schema for creating an edge."""
    workflow_id: UUID
    from_node_id: UUID
    to_node_id: UUID


class EdgeResponse(BaseModel):
    """Schema for edge response."""
    id: UUID
    workflow_id: UUID
    from_node_id: UUID
    to_node_id: UUID

    class Config:
        from_attributes = True


# DAG schema
class DAGNode(BaseModel):
    """Node in DAG visualization."""
    id: str
    name: str
    operation_type: str
    status: str


class DAGEdge(BaseModel):
    """Edge in DAG visualization."""
    from_node: str
    to_node: str


class DAGResponse(BaseModel):
    """Complete DAG structure."""
    workflow_id: str
    workflow_name: str
    nodes: List[DAGNode]
    edges: List[DAGEdge]


# Data preview schema
class DataPreview(BaseModel):
    """Schema for data preview."""
    columns: List[str]
    data: List[Dict[str, Any]]
    total_rows: int
    preview_rows: int


# Plot data schema
class PlotData(BaseModel):
    """Schema for plot visualization data."""
    channel_id: int
    x: List[Any]  # timestamps or frequencies
    y: List[float]  # values or magnitudes
    x_label: str
    y_label: str
    title: str
