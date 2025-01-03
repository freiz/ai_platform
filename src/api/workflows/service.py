from typing import Dict, Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.activities.activity_registry import ActivityRegistry
from src.database.models import WorkflowModel, ActivityModel, WorkflowOwnership, ActivityOwnership, WorkflowActivityRelation
from src.workflows import Workflow
from .schemas import CreateWorkflowRequest, WorkflowExecuteRequest
from .validators import validate_workflow_structure


async def list_workflows(session: AsyncSession, user_id: str) -> list[dict]:
    """List all workflows owned by the user."""
    # Query workflows with their activities
    stmt = (
        select(WorkflowModel)
        .join(
            WorkflowOwnership,
            WorkflowOwnership.workflow_id == WorkflowModel.id
        )
        .join(
            WorkflowActivityRelation,
            WorkflowActivityRelation.workflow_id == WorkflowModel.id
        )
        .join(
            ActivityModel,
            ActivityModel.id == WorkflowActivityRelation.activity_id
        )
        .where(WorkflowOwnership.user_id == user_id)
        .distinct()
    )

    result = await session.execute(stmt)
    workflows = result.unique().scalars().all()

    # For each workflow, fetch its activities
    workflow_list = []
    for workflow in workflows:
        # Get all activities used in this workflow
        activity_stmt = (
            select(ActivityModel)
            .join(
                WorkflowActivityRelation,
                WorkflowActivityRelation.activity_id == ActivityModel.id
            )
            .where(WorkflowActivityRelation.workflow_id == workflow.id)
        )
        activity_result = await session.execute(activity_stmt)
        activities = {
            str(activity.id): {
                "id": str(activity.id),
                "activity_type": activity.activity_type_name,
                "activity_name": activity.activity_name,
                "input_params_schema": activity.input_params_schema,
                "output_params_schema": activity.output_params_schema,
                "params": activity.params
            }
            for activity in activity_result.scalars().all()
        }

        workflow_list.append({
            "id": str(workflow.id),
            "workflow_name": workflow.workflow_name,
            "nodes": workflow.nodes,
            "connections": workflow.connections,
            "created_at": workflow.created_at.isoformat(),
            "activities": activities
        })

    return workflow_list


async def create_workflow(
        workflow_id: UUID,
        request: CreateWorkflowRequest,
        user_id: str,
        session: AsyncSession
) -> dict:
    """Create a new workflow and assign ownership to the user."""
    # Verify all activities exist and load them
    activities = {}
    for node_id, node in request.nodes.items():
        # Check activity exists and user owns it
        stmt = select(ActivityModel).join(
            ActivityOwnership,
            ActivityOwnership.activity_id == ActivityModel.id
        ).where(
            ActivityModel.id == node.activity_id,
            ActivityOwnership.user_id == user_id
        )
        result = await session.execute(stmt)
        activity = result.scalar_one_or_none()
        if not activity:
            raise HTTPException(
                status_code=404,
                detail=f"Activity {node.activity_id} not found or not owned by user"
            )

        # Store activity for validation using activity ID as key
        activities[str(node.activity_id)] = activity

    # Validate workflow structure
    try:
        validate_workflow_structure(request.nodes, request.connections, activities)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # Convert nodes to dictionary format
    node_dicts = {
        node_id: {
            "activity_id": str(node.activity_id)
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

    # Create ownership record
    ownership = WorkflowOwnership(
        workflow_id=workflow_id,
        user_id=user_id,
        workflow_name=request.workflow_name
    )

    # Create activity relations (deduplicated)
    unique_activity_ids = {
        node.activity_id
        for node in request.nodes.values()
    }
    activity_relations = [
        WorkflowActivityRelation(
            workflow_id=workflow_id,
            activity_id=activity_id
        )
        for activity_id in unique_activity_ids
    ]

    try:
        # Save all records to database
        session.add(db_workflow)
        session.add(ownership)
        session.add_all(activity_relations)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        error_msg = str(e).lower()
        
        # Handle duplicate workflow name
        if "workflow_ownership" in error_msg and "unique constraint" in error_msg:
            raise HTTPException(
                status_code=409,  # Conflict
                detail=f"A workflow named '{request.workflow_name}' already exists. Please choose a different name."
            )
        # Handle foreign key violations
        elif "foreign key constraint" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="One or more activities are invalid or have been deleted"
            )
        # Generic database error
        else:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while creating the workflow. Please try again."
            )

    return {
        "id": str(workflow_id),
        "workflow_name": request.workflow_name,
        "nodes": node_dicts,
        "connections": connection_dicts,
        "created_at": db_workflow.created_at.isoformat()
    }


async def get_workflow(workflow_id: UUID, user_id: str, session: AsyncSession) -> dict:
    """Get a workflow by its ID if owned by the user."""
    # Query workflow with its activities
    stmt = (
        select(WorkflowModel)
        .join(
            WorkflowOwnership,
            WorkflowOwnership.workflow_id == WorkflowModel.id
        )
        .where(
            WorkflowModel.id == workflow_id,
            WorkflowOwnership.user_id == user_id
        )
    )
    result = await session.execute(stmt)
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found or not owned by user"
        )

    # Get all activities used in this workflow
    activity_stmt = (
        select(ActivityModel)
        .join(
            WorkflowActivityRelation,
            WorkflowActivityRelation.activity_id == ActivityModel.id
        )
        .where(WorkflowActivityRelation.workflow_id == workflow_id)
    )
    activity_result = await session.execute(activity_stmt)
    activities = {
        str(activity.id): {
            "id": str(activity.id),
            "activity_type": activity.activity_type_name,
            "activity_name": activity.activity_name,
            "input_params_schema": activity.input_params_schema,
            "output_params_schema": activity.output_params_schema,
            "params": activity.params
        }
        for activity in activity_result.scalars().all()
    }

    return {
        "id": str(workflow.id),
        "workflow_name": workflow.workflow_name,
        "nodes": workflow.nodes,
        "connections": workflow.connections,
        "created_at": workflow.created_at.isoformat(),
        "activities": activities
    }


async def delete_workflow(workflow_id: UUID, user_id: str, session: AsyncSession) -> None:
    """Delete a workflow by its ID if owned by the user."""
    stmt = select(WorkflowModel).join(
        WorkflowOwnership,
        WorkflowOwnership.workflow_id == WorkflowModel.id
    ).where(
        WorkflowModel.id == workflow_id,
        WorkflowOwnership.user_id == user_id
    )
    result = await session.execute(stmt)
    workflow = result.scalar_one_or_none()

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found or not owned by user"
        )

    await session.delete(workflow)  # This will cascade delete the ownership record
    await session.commit()


async def execute_workflow(
        workflow_id: UUID,
        user_id: str,
        request: WorkflowExecuteRequest,
        session: AsyncSession
) -> Dict[str, Any]:
    """Execute a workflow with the given input values if owned by the user."""
    # Query the workflow with ownership check
    stmt = select(WorkflowModel).join(
        WorkflowOwnership,
        WorkflowOwnership.workflow_id == WorkflowModel.id
    ).where(
        WorkflowModel.id == workflow_id,
        WorkflowOwnership.user_id == user_id
    )
    result = await session.execute(stmt)
    workflow_model = result.scalar_one_or_none()

    if not workflow_model:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found or not owned by user"
        )

    # Create workflow instance
    workflow = Workflow()

    # Load activities and create nodes
    for node_id, node_data in workflow_model.nodes.items():
        # Get activity model with ownership check
        stmt = select(ActivityModel).join(
            ActivityOwnership,
            ActivityOwnership.activity_id == ActivityModel.id
        ).where(
            ActivityModel.id == UUID(node_data['activity_id']),
            ActivityOwnership.user_id == user_id
        )
        result = await session.execute(stmt)
        activity_model = result.scalar_one_or_none()
        if not activity_model:
            raise HTTPException(
                status_code=404,
                detail=f"Activity {node_data['activity_id']} not found or not owned by user"
            )

        # Create activity instance
        activity = ActivityRegistry().create_activity(
            activity_type_name=activity_model.activity_type_name,
            params=activity_model.params
        )
        activity.id = UUID(node_data['activity_id'])

        # Add node to workflow
        workflow.add_node(node_id, activity)

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
