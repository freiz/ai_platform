from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.database.models import WorkflowModel, ActivityModel


class WorkflowNodeCreate(BaseModel):
    """Request model for creating a node in the workflow API."""
    activity_id: UUID
    label: str  # User-provided label for this instance


class WorkflowConnectionCreate(BaseModel):
    """Request model for creating a connection in the workflow API."""
    source_node: str  # Node ID
    source_output: str
    target_node: str  # Node ID
    target_input: str


class CreateWorkflowRequest(BaseModel):
    """Request model for creating a workflow."""
    workflow_name: str
    nodes: Dict[str, WorkflowNodeCreate]  # Map of node_id to node info
    connections: Optional[List[WorkflowConnectionCreate]] = Field(
        default_factory=list)  # Optional connections between nodes


# Create router for user workflows
router = APIRouter(
    prefix="/users/{user_id}/workflows",
    tags=["workflows"]
)


@router.get("")
async def list_workflows(
        user_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """
    List all workflows for a user.
    
    Args:
        user_id: UUID of the user
        session: Database session dependency
            
    Returns:
        List of workflows with their nodes and connections
    """
    try:
        # Query all workflows
        stmt = select(WorkflowModel)
        result = await session.execute(stmt)
        workflows = result.scalars().all()

        return [
            {
                "id": str(workflow.id),
                "workflow_name": workflow.workflow_name,
                "nodes": workflow.nodes,
                "connections": workflow.connections,
                "created_at": workflow.created_at.isoformat()
            }
            for workflow in workflows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", status_code=201)
async def create_workflow(
        user_id: UUID,
        request: CreateWorkflowRequest,
        response: Response,
        session: AsyncSession = Depends(get_session)
):
    """
    Create a new workflow for a user.
    
    Args:
        user_id: UUID of the user
        request: The workflow creation request containing:
            - workflow_name: Name of the workflow
            - nodes: Map of node_id to node info (activity_id and label)
            - connections: Optional list of connections between nodes
        response: FastAPI response object for setting headers
        session: Database session dependency
            
    Returns:
        The created workflow instance with its ID
        
    Raises:
        HTTPException: If activities not found, name already exists, or node labels are duplicated
    """
    try:
        # Verify all activities exist and check for duplicate labels
        node_labels = set()
        for node in request.nodes.values():
            # Check activity exists
            stmt = select(ActivityModel).where(ActivityModel.id == node.activity_id)
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                raise ValueError(f"Activity {node.activity_id} not found")

            # Check for duplicate labels
            if node.label in node_labels:
                raise ValueError(f"Duplicate node label found: {node.label}")
            node_labels.add(node.label)

        # Verify all connection nodes exist in the nodes dictionary
        if request.connections:
            for conn in request.connections:
                if conn.source_node not in request.nodes:
                    raise ValueError(f"Source node not found: {conn.source_node}")
                if conn.target_node not in request.nodes:
                    raise ValueError(f"Target node not found: {conn.target_node}")

        # Generate workflow ID
        workflow_id = uuid4()

        # Convert nodes to dictionary format
        node_dicts = {
            node_id: {
                "activity_id": str(node.activity_id),
                "label": node.label
            }
            for node_id, node in request.nodes.items()
        }

        # Convert connections to dictionary format
        connection_dicts = [
            {
                "source_node": conn.source_node,
                "source_output": conn.source_output,
                "target_node": conn.target_node,
                "target_input": conn.target_input
            }
            for conn in (request.connections or [])
        ]

        # Create database model
        db_workflow = WorkflowModel(
            id=workflow_id,
            workflow_name=request.workflow_name,
            nodes=node_dicts,
            connections=connection_dicts
        )

        try:
            # Save to database
            session.add(db_workflow)
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,  # Conflict
                detail=f"Workflow with name '{request.workflow_name}' already exists"
            )

        # Set Location header to point to the new resource
        response.headers["Location"] = f"/users/{user_id}/workflows/{workflow_id}"

        return {
            "id": str(workflow_id),
            "workflow_name": request.workflow_name,
            "nodes": node_dicts,
            "connections": connection_dicts,
            "created_at": db_workflow.created_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}")
async def get_workflow(
        user_id: UUID,
        workflow_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """
    Get a workflow by its ID.
    
    Args:
        user_id: UUID of the user
        workflow_id: UUID of the workflow to retrieve
        session: Database session dependency
        
    Returns:
        The workflow if found
        
    Raises:
        HTTPException: If workflow not found
    """
    try:
        # Query the database
        stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
        result = await session.execute(stmt)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )

        return {
            "id": str(workflow.id),
            "workflow_name": workflow.workflow_name,
            "nodes": workflow.nodes,
            "connections": workflow.connections,
            "created_at": workflow.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
