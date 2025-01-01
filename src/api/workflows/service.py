from typing import Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.activities.activity_registry import ActivityRegistry
from src.database.models import WorkflowModel, ActivityModel
from src.workflow import Workflow
from .schemas import CreateWorkflowRequest, WorkflowExecuteRequest
from .validators import validate_workflow_structure


async def list_workflows(session: AsyncSession) -> list[dict]:
    """List all workflows with their details."""
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


async def create_workflow(
        workflow_id: UUID,
        request: CreateWorkflowRequest,
        session: AsyncSession
) -> dict:
    """Create a new workflow."""
    # Verify all activities exist and load them
    activities = {}
    for node_id, node in request.nodes.items():
        # Check activity exists
        stmt = select(ActivityModel).where(ActivityModel.id == node.activity_id)
        result = await session.execute(stmt)
        activity = result.scalar_one_or_none()
        if not activity:
            raise HTTPException(
                status_code=404,
                detail=f"Activity {node.activity_id} not found"
            )

        # Store activity for validation using activity ID as key
        activities[str(node.activity_id)] = activity

    # Validate workflow structure
    validate_workflow_structure(request.nodes, request.connections, activities)

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

    return {
        "id": str(workflow_id),
        "workflow_name": request.workflow_name,
        "nodes": node_dicts,
        "connections": connection_dicts,
        "created_at": db_workflow.created_at.isoformat()
    }


async def get_workflow(workflow_id: UUID, session: AsyncSession) -> dict:
    """Get a workflow by its ID."""
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


async def delete_workflow(workflow_id: UUID, session: AsyncSession) -> None:
    """Delete a workflow by its ID."""
    stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
    result = await session.execute(stmt)
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found"
        )

    await session.delete(workflow)
    await session.commit()


async def execute_workflow(
        workflow_id: UUID,
        request: WorkflowExecuteRequest,
        session: AsyncSession
) -> Dict[str, Any]:
    """Execute a workflow with the given input values."""
    # Query the workflow
    stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
    result = await session.execute(stmt)
    workflow_model = result.scalar_one_or_none()

    if not workflow_model:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found"
        )

    # Create workflow instance
    workflow = Workflow()

    # Load activities and create nodes
    for node_id, node_data in workflow_model.nodes.items():
        # Get activity model
        stmt = select(ActivityModel).where(ActivityModel.id == UUID(node_data['activity_id']))
        result = await session.execute(stmt)
        activity_model = result.scalar_one_or_none()
        if not activity_model:
            raise HTTPException(
                status_code=404,
                detail=f"Activity {node_data['activity_id']} not found"
            )

        # Create activity instance
        activity_class = ActivityRegistry.get_activity_class(activity_model.activity_type_name)
        activity_type_info = ActivityRegistry.get_activity_type(activity_model.activity_type_name)
        
        # Only pass input/output params if activity allows custom params
        activity_params = {
            "activity_name": activity_model.activity_name,
        }
        if activity_type_info.allow_custom_params:
            activity_params.update({
                "input_params": activity_model.input_params_schema,
                "output_params": activity_model.output_params_schema
            })
        
        activity = activity_class(**activity_params)
        activity.id = UUID(node_data['activity_id'])

        # Add node to workflow
        workflow.add_node(node_id, activity, node_data['label'])

    # Add connections
    for conn in workflow_model.connections:
        workflow.connect_nodes(
            source_node=conn['source_node'],
            source_output=conn['source_output'],
            target_node=conn['target_node'],
            target_input=conn['target_input']
        )

    # Execute workflow
    try:
        return workflow.run(request.inputs)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow execution failed: {str(e)}"
        ) 