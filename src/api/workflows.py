from typing import Dict, List
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.database.models import WorkflowModel, ActivityModel
from src.workflow import Connection


class CreateWorkflowRequest(BaseModel):
    """Request model for creating a workflow."""
    workflow_name: str
    activities: Dict[str, UUID]  # Map of activity name to activity UUID
    connections: List[Connection]  # List of connections between activities


# Create router for user workflows
router = APIRouter(
    prefix="/users/{user_id}/workflows",
    tags=["workflows"]
)


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
            - activities: Map of activity name to activity UUID
            - connections: List of connections between activities
        response: FastAPI response object for setting headers
        session: Database session dependency
            
    Returns:
        The created workflow instance with its ID
        
    Raises:
        HTTPException: If activities not found or name already exists
    """
    try:
        # Verify all activities exist
        for activity_id in request.activities.values():
            stmt = select(ActivityModel).where(ActivityModel.id == activity_id)
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                raise ValueError(f"Activity {activity_id} not found")

        # Generate workflow ID
        workflow_id = uuid4()

        # Convert connections to dictionaries with string UUIDs
        connection_dicts = [
            {
                "source_activity_id": str(conn.source_activity_id),
                "source_output": conn.source_output,
                "target_activity_id": str(conn.target_activity_id),
                "target_input": conn.target_input
            }
            for conn in request.connections
        ]

        # Create database model
        db_workflow = WorkflowModel(
            id=workflow_id,
            workflow_name=request.workflow_name,
            activities=request.activities,
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
            "activities": {
                name: str(uuid) for name, uuid in request.activities.items()
            },
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
            "activities": {
                name: str(uuid) for name, uuid in workflow.activities.items()
            },
            "connections": workflow.connections,
            "created_at": workflow.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
