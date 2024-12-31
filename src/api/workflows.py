from typing import Dict, List, Set, Tuple
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
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
    connections: List[WorkflowConnectionCreate] | None = None  # Optional connections between nodes

    def __init__(self, **data):
        super().__init__(**data)
        if self.connections is None:
            self.connections = []


def validate_workflow_structure(
        nodes: Dict[str, WorkflowNodeCreate],
        connections: List[WorkflowConnectionCreate],
        activities: Dict[str, ActivityModel]
) -> Tuple[Set[str], Set[str]]:
    """
    Validate workflow structure including node labels, connections, and parameter types.
    
    Args:
        nodes: Map of node_id to node info
        connections: List of connections between nodes
        activities: Map of activity_id to activity model
        
    Returns:
        Tuple of (root_nodes, leaf_nodes) sets
        
    Raises:
        ValueError: If any validation fails
    """
    # Check for duplicate labels
    node_labels = set()
    for node_id, node in nodes.items():
        if node.label in node_labels:
            raise ValueError(f"Duplicate node label found: {node.label}")
        node_labels.add(node.label)

    # If there are multiple nodes but no connections, that's an error
    if not connections and len(nodes) > 1:
        raise ValueError("Multiple nodes present but no connections between them")

    # Build connection maps for validation
    connected_inputs = {
        f"{conn.target_node}.{conn.target_input}"
        for conn in connections
    }
    connected_outputs = {
        f"{conn.source_node}.{conn.source_output}"
        for conn in connections
    }

    # Find root and leaf nodes by analyzing connections
    target_nodes = {conn.target_node for conn in connections}
    source_nodes = {conn.source_node for conn in connections}

    # A node is a root if it's never a target
    root_nodes = set(nodes.keys()) - target_nodes
    # A node is a leaf if it's never a source
    leaf_nodes = set(nodes.keys()) - source_nodes

    # Special case: single node is both root and leaf
    if len(nodes) == 1:
        node_id = next(iter(nodes))
        root_nodes.add(node_id)
        leaf_nodes.add(node_id)

    # Verify all connection nodes exist and parameters are compatible
    if connections:
        for conn in connections:
            # Verify nodes exist
            if conn.source_node not in nodes:
                raise ValueError(f"Source node not found: {conn.source_node}")
            if conn.target_node not in nodes:
                raise ValueError(f"Target node not found: {conn.target_node}")

            # Get source and target activities
            source_activity = activities[str(nodes[conn.source_node].activity_id)]
            target_activity = activities[str(nodes[conn.target_node].activity_id)]

            # Verify parameters exist
            if conn.source_output not in source_activity.output_params_schema:
                raise ValueError(f"Output parameter {conn.source_output} not found in source node {conn.source_node}")
            if conn.target_input not in target_activity.input_params_schema:
                raise ValueError(f"Input parameter {conn.target_input} not found in target node {conn.target_node}")

            # Verify parameter types match
            source_type = source_activity.output_params_schema[conn.source_output]['type']
            target_type = target_activity.input_params_schema[conn.target_input]['type']
            if source_type != target_type:
                raise ValueError(
                    f"Type mismatch in connection: {conn.source_node}.{conn.source_output} ({source_type}) "
                    f"→ {conn.target_node}.{conn.target_input} ({target_type})"
                )

    # Verify all non-root inputs are connected
    for node_id, node in nodes.items():
        activity = activities[str(node.activity_id)]
        for input_param in activity.input_params_schema:
            param_key = f"{node_id}.{input_param}"
            if node_id not in root_nodes and param_key not in connected_inputs:
                raise ValueError(
                    f"Input parameter {input_param} of non-root node {node_id} is not connected"
                )

    # Verify all non-leaf outputs are connected
    for node_id, node in nodes.items():
        activity = activities[str(node.activity_id)]
        for output_param in activity.output_params_schema:
            param_key = f"{node_id}.{output_param}"
            if node_id not in leaf_nodes and param_key not in connected_outputs:
                raise ValueError(
                    f"Output parameter {output_param} of non-leaf node {node_id} is not connected"
                )

    # Find connected nodes and check for disconnected ones
    connected_nodes = {conn.source_node for conn in connections} | {conn.target_node for conn in connections}

    # If a node is not in any connection, it's an error (unless it's the only node)
    disconnected_nodes = set(nodes.keys()) - connected_nodes
    if disconnected_nodes and len(nodes) > 1:
        raise ValueError(f"Nodes are disconnected from the workflow: {', '.join(disconnected_nodes)}")

    return root_nodes, leaf_nodes


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
        HTTPException: If activities not found, name already exists, or validations fail
    """
    try:
        # Verify all activities exist and load them
        activities = {}  # Store activity instances for validation
        for node_id, node in request.nodes.items():
            # Check activity exists
            stmt = select(ActivityModel).where(ActivityModel.id == node.activity_id)
            result = await session.execute(stmt)
            activity = result.scalar_one_or_none()
            if not activity:
                raise ValueError(f"Activity {node.activity_id} not found")

            # Store activity for validation using activity ID as key
            activities[str(node.activity_id)] = activity

        # Validate workflow structure
        validate_workflow_structure(request.nodes, request.connections, activities)

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


# noinspection DuplicatedCode
@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
        user_id: UUID,
        workflow_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """
    Delete a workflow by its ID.
    
    Args:
        user_id: UUID of the user
        workflow_id: UUID of the workflow to delete
        session: Database session dependency
        
    Returns:
        No content on success
        
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

        # Delete the workflow
        await session.delete(workflow)
        await session.commit()

        # Return no content (204)
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
