from typing import Dict, List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.activities.activity_registry import ActivityRegistry
from src.database.models import ActivityModel
from .schemas import CreateActivityRequest


async def list_activities(session: AsyncSession) -> List[Dict]:
    """List all activities."""
    stmt = select(ActivityModel)
    result = await session.execute(stmt)
    activities = result.scalars().all()

    return [
        {
            "id": str(activity.id),
            "activity_type": activity.activity_type_name,
            "activity_name": activity.activity_name,
            "created_at": activity.created_at.isoformat(),
            "input_params_schema": activity.input_params_schema,
            "output_params_schema": activity.output_params_schema,
            "params": activity.params
        }
        for activity in activities
    ]


async def create_activity(request: CreateActivityRequest, session: AsyncSession) -> Dict:
    """Create a new activity."""
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

    try:
        # Save to database
        session.add(db_activity)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,  # Conflict
            detail=f"Activity with name '{activity.activity_name}' already exists"
        )

    # Merge activity instance fields with top-level fields
    activity_data = activity.model_dump(exclude={"id", "activity_name"})
    return {
        "id": str(activity.id),
        "activity_type": request.activity_type_name,
        "activity_name": activity.activity_name,
        "created_at": db_activity.created_at.isoformat(),
        **activity_data  # Spread remaining activity fields at top level
    }


async def get_activity(activity_id: UUID, session: AsyncSession) -> Dict:
    """Get an activity by its ID."""
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

    # Merge activity instance fields with top-level fields
    activity_data = activity_instance.model_dump(exclude={"id", "activity_name"})
    return {
        "id": str(activity.id),
        "activity_type": activity.activity_type_name,
        "activity_name": activity.activity_name,
        "created_at": activity.created_at.isoformat(),
        **activity_data  # Spread remaining activity fields at top level
    }


async def delete_activity(activity_id: UUID, session: AsyncSession) -> None:
    """Delete an activity by its ID."""
    stmt = select(ActivityModel).where(ActivityModel.id == activity_id)
    result = await session.execute(stmt)
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(
            status_code=404,
            detail=f"Activity {activity_id} not found"
        )

    await session.delete(activity)
    await session.commit() 