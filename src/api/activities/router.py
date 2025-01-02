from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from .schemas import CreateActivityRequest
from .service import (
    list_activities,
    create_activity,
    get_activity,
    delete_activity
)

# Create router for user activities
router = APIRouter(
    prefix="/users/{user_id}/activities",
    tags=["activities"]
)


@router.get("")
async def list_activities_endpoint(
        user_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """
    List all activities for a user.
    
    Args:
        user_id: UUID of the user
        session: Database session dependency
            
    Returns:
        List of activities
    """
    try:
        return await list_activities(session, str(user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", status_code=201)
async def create_activity_endpoint(
        user_id: UUID,
        request: CreateActivityRequest,
        response: Response,
        session: AsyncSession = Depends(get_session)
):
    """
    Create a new activity for a user.
    
    Args:
        user_id: UUID of the user
        request: The activity creation request
        response: FastAPI response object for setting headers
        session: Database session dependency
            
    Returns:
        The created activity instance with its ID
    """
    try:
        # Create activity and save to database
        response_data = await create_activity(request, str(user_id), session)

        # Set Location header
        response.headers["Location"] = f"/users/{user_id}/activities/{response_data['id']}"

        return response_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{activity_id}")
async def get_activity_endpoint(
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
    """
    try:
        return await get_activity(activity_id, str(user_id), session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{activity_id}", status_code=204)
async def delete_activity_endpoint(
        user_id: UUID,
        activity_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    """
    Delete an activity by its ID.
    
    Args:
        user_id: UUID of the user
        activity_id: UUID of the activity to delete
        session: Database session dependency
        
    Returns:
        No content on success
    """
    try:
        await delete_activity(activity_id, str(user_id), session)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 