from typing import Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.activities.activity_registry import ActivityRegistry

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


@router.post("")
async def create_activity(user_id: UUID, request: CreateActivityRequest):
    """
    Create a new activity for a user.
    
    Args:
        user_id: UUID of the user
        request: The activity creation request containing:
            - activity_type_name: Name of the registered activity type
            - allow_custom_params: Whether the activity allows custom I/O params
            - params: Parameters for activity creation including required_params 
                     and optionally input_params/output_params
            
    Returns:
        The created activity instance
        
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

        # For demo purposes, just print the activity and user_id
        print(f"Created activity for user {user_id}: {activity}")

        return {
            "message": "Activity created successfully",
            "user_id": str(user_id),
            "activity_type": request.activity_type_name,
            "activity": activity.model_dump()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
