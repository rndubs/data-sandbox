"""API routes for workflow management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from src.database import get_db_session
from src.models import Workflow, Node, Edge
from src.api.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    EdgeCreate,
    EdgeResponse,
    DAGResponse,
    DAGNode,
    DAGEdge
)
from src.workflow import WorkflowExecutor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=WorkflowResponse, status_code=201)
def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new workflow.

    Args:
        workflow: Workflow creation data
        db: Database session

    Returns:
        Created workflow
    """
    db_workflow = Workflow(
        name=workflow.name,
        description=workflow.description
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)

    logger.info(f"Created workflow {db_workflow.id}: {db_workflow.name}")
    return db_workflow


@router.get("/", response_model=List[WorkflowResponse])
def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """List all workflows.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of workflows
    """
    workflows = db.query(Workflow).offset(skip).limit(limit).all()
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get workflow by ID.

    Args:
        workflow_id: Workflow UUID
        db: Database session

    Returns:
        Workflow details
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.get("/{workflow_id}/dag", response_model=DAGResponse)
def get_workflow_dag(
    workflow_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Get workflow DAG structure.

    Args:
        workflow_id: Workflow UUID
        db: Database session

    Returns:
        DAG structure with nodes and edges
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get nodes
    nodes = db.query(Node).filter(Node.workflow_id == workflow_id).all()
    dag_nodes = [
        DAGNode(
            id=str(node.id),
            name=node.name,
            operation_type=node.operation_type,
            status=node.status
        )
        for node in nodes
    ]

    # Get edges
    edges = db.query(Edge).filter(Edge.workflow_id == workflow_id).all()
    dag_edges = [
        DAGEdge(
            from_node=str(edge.from_node_id),
            to_node=str(edge.to_node_id)
        )
        for edge in edges
    ]

    return DAGResponse(
        workflow_id=str(workflow_id),
        workflow_name=workflow.name,
        nodes=dag_nodes,
        edges=dag_edges
    )


@router.post("/{workflow_id}/edges", response_model=EdgeResponse, status_code=201)
def create_edge(
    workflow_id: UUID,
    edge: EdgeCreate,
    db: Session = Depends(get_db_session)
):
    """Create an edge between nodes.

    Args:
        workflow_id: Workflow UUID
        edge: Edge creation data
        db: Database session

    Returns:
        Created edge
    """
    # Verify workflow exists
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Verify nodes exist and belong to workflow
    from_node = db.query(Node).filter(
        Node.id == edge.from_node_id,
        Node.workflow_id == workflow_id
    ).first()
    to_node = db.query(Node).filter(
        Node.id == edge.to_node_id,
        Node.workflow_id == workflow_id
    ).first()

    if not from_node or not to_node:
        raise HTTPException(status_code=400, detail="Invalid nodes")

    # Create edge
    db_edge = Edge(
        workflow_id=workflow_id,
        from_node_id=edge.from_node_id,
        to_node_id=edge.to_node_id
    )

    try:
        db.add(db_edge)
        db.commit()
        db.refresh(db_edge)

        logger.info(f"Created edge in workflow {workflow_id}: {edge.from_node_id} -> {edge.to_node_id}")
        return db_edge

    except Exception as e:
        logger.error(f"Error creating edge: {e}")
        raise HTTPException(status_code=400, detail="Edge already exists or would create cycle")


@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Execute a workflow.

    Args:
        workflow_id: Workflow UUID
        db: Database session

    Returns:
        Execution results
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        executor = WorkflowExecutor(db)
        result = executor.execute(workflow_id)

        logger.info(f"Executed workflow {workflow_id}")
        return result

    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}", status_code=204)
def delete_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db_session)
):
    """Delete a workflow.

    Args:
        workflow_id: Workflow UUID
        db: Database session
    """
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    db.delete(workflow)
    db.commit()

    logger.info(f"Deleted workflow {workflow_id}")
