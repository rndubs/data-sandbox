"""SQLAlchemy models for the metadata database."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Float,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class Dataset(Base):
    """Time series dataset metadata."""

    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    file_location = Column(String(500), nullable=False)
    schema_info = Column(JSONB)
    row_count = Column(BigInteger)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    channel_count = Column(Integer)
    sample_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    input_nodes = relationship("Node", foreign_keys="Node.input_dataset_id", back_populates="input_dataset")
    output_nodes = relationship("Node", foreign_keys="Node.output_dataset_id", back_populates="output_dataset")


class Workflow(Base):
    """Computation graph workflow."""

    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    nodes = relationship("Node", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="workflow", cascade="all, delete-orphan")


class Node(Base):
    """Individual operation in a workflow."""

    __tablename__ = "nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    operation_type = Column(String(100), nullable=False)
    operation_config = Column(JSONB)
    input_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    output_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    status = Column(String(50), default="pending")
    error_message = Column(Text)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")
    input_dataset = relationship("Dataset", foreign_keys=[input_dataset_id], back_populates="input_nodes")
    output_dataset = relationship("Dataset", foreign_keys=[output_dataset_id], back_populates="output_nodes")
    outgoing_edges = relationship("Edge", foreign_keys="Edge.from_node_id", back_populates="from_node", cascade="all, delete-orphan")
    incoming_edges = relationship("Edge", foreign_keys="Edge.to_node_id", back_populates="to_node", cascade="all, delete-orphan")


class Edge(Base):
    """Connection between nodes in a workflow DAG."""

    __tablename__ = "edges"
    __table_args__ = (UniqueConstraint("workflow_id", "from_node_id", "to_node_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    from_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    to_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="edges")
    from_node = relationship("Node", foreign_keys=[from_node_id], back_populates="outgoing_edges")
    to_node = relationship("Node", foreign_keys=[to_node_id], back_populates="incoming_edges")
