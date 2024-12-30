from typing import Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.activities.activity_registry import ActivityRegistry
from src.database.connection import get_session
from src.database.models import ActivityModel

# Create router for user activities
router = APIRouter(
    prefix="/users/{user_id}/activities",
    tags=["activities"]
)


class CreateActivityRequest(BaseModel):
    """Request model for creating an activity."""
    activity_type_name: str
    allow_custom_params: bool
    params: Dict


@router.post("", status_code=201)
async def create_activity(
    user_id: UUID, 
    request: CreateActivityRequest,
    response: Response,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new activity for a user.
    
    Args:
        user_id: UUID of the user
        request: The activity creation request containing:
            - activity_type_name: Name of the registered activity type
            - allow_custom_params: Whether the activity allows custom I/O params
            - params: Parameters for activity creation including required_params 
                     and optionally input_params/output_params
        response: FastAPI response object for setting headers
        session: Database session dependency
            
    Returns:
        The created activity instance with its ID
        
    Raises:
        HTTPException: If activity type not found or params are invalid
    """
    try:
        # Get activity type info to verify allow_custom_params
        activity_info = ActivityRegistry().get_activity_type(request.activity_type_name)

        # Verify allow_custom_params matches
        if activity_info.allow_custom_params != request.allow_custom_params:
            raise ValueError(
                f"Activity type {request.activity_type_name} has allow_custom_params={activity_info.allow_custom_params}, "
                f"but request specified {request.allow_custom_params}"
            )

        # Create activity instance
        activity = ActivityRegistry().create_activity(
            activity_type_name=request.activity_type_name,
            params=request.params
        )

        # Create database model
        db_activity = ActivityModel(
            id=activity.id,
            activity_type_name=request.activity_type_name,
            activity_name=activity.activity_name,
            input_params_schema={
                name: param.model_dump() 
                for name, param in activity.input_params.items()
            },
            output_params_schema={
                name: param.model_dump() 
                for name, param in activity.output_params.items()
            },
            params=request.params
        )
        
        # Save to database
        session.add(db_activity)
        await session.commit()

        # Set Location header to point to the new resource
        response.headers["Location"] = f"/users/{user_id}/activities/{activity.id}"

        return {
            "id": str(activity.id),
            "activity_type": request.activity_type_name,
            "activity_name": activity.activity_name,
            "created_at": db_activity.created_at.isoformat(),
            "data": activity.model_dump(exclude={"id"})  # Exclude id since it's already at the top level
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{activity_id}")
async def get_activity(
    user_id: UUID,
    activity_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get an activity by its ID.
    
    Args:
        user_id: UUID of the user
        activity_id: UUID of the activity to retrieve
        session: Database session dependency
        
    Returns:
        The activity if found
        
    Raises:
        HTTPException: If activity not found
    """
    try:
        # Query the database
        stmt = select(ActivityModel).where(ActivityModel.id == activity_id)
        result = await session.execute(stmt)
        activity = result.scalar_one_or_none()
        
        if not activity:
            raise HTTPException(
                status_code=404,
                detail=f"Activity {activity_id} not found"
            )
            
        # Recreate activity instance
        activity_instance = ActivityRegistry().create_activity(
            activity_type_name=activity.activity_type_name,
            params=activity.params
        )
        
        return {
            "user_id": str(user_id),
            "activity": activity_instance.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
