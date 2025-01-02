from typing import Dict, List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.activities.activity_registry import ActivityRegistry
from src.database.models import ActivityModel, ActivityOwnership, WorkflowActivityRelation, WorkflowModel
from .schemas import CreateActivityRequest


async def list_activities(session: AsyncSession, user_id: str) -> List[Dict]:
    """List all activities owned by the user."""
    stmt = select(ActivityModel).join(
        ActivityOwnership,
        ActivityOwnership.activity_id == ActivityModel.id
    ).where(ActivityOwnership.user_id == user_id)
    
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


async def create_activity(request: CreateActivityRequest, user_id: str, session: AsyncSession) -> Dict:
    """Create a new activity and assign ownership to the user."""
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

    # Create ownership record
    ownership = ActivityOwnership(
        activity_id=activity.id,
        user_id=user_id,
        activity_name=activity.activity_name
    )

    try:
        # Save both records to database
        session.add(db_activity)
        session.add(ownership)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,  # Conflict
            detail=f"Activity with name '{activity.activity_name}' already exists for this user"
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


async def get_activity(activity_id: UUID, user_id: str, session: AsyncSession) -> Dict:
    """Get an activity by its ID if owned by the user."""
    stmt = select(ActivityModel).join(
        ActivityOwnership,
        ActivityOwnership.activity_id == ActivityModel.id
    ).where(
        ActivityModel.id == activity_id,
        ActivityOwnership.user_id == user_id
    )
    result = await session.execute(stmt)
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(
            status_code=404,
            detail=f"Activity {activity_id} not found or not owned by user"
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


async def delete_activity(activity_id: UUID, user_id: str, session: AsyncSession) -> None:
    """Delete an activity by its ID if owned by the user and not used in any workflows."""
    # First check if activity exists and is owned by user, and load workflow relations
    stmt = (
        select(ActivityModel)
        .join(
            ActivityOwnership,
            ActivityOwnership.activity_id == ActivityModel.id
        )
        .outerjoin(
            WorkflowActivityRelation,
            WorkflowActivityRelation.activity_id == ActivityModel.id
        )
        .outerjoin(
            WorkflowModel,
            WorkflowModel.id == WorkflowActivityRelation.workflow_id
        )
        .where(
            ActivityModel.id == activity_id,
            ActivityOwnership.user_id == user_id
        )
        .options(
            selectinload(ActivityModel.workflow_relations).selectinload(WorkflowActivityRelation.workflow)
        )
    )
    result = await session.execute(stmt)
    activity = result.unique().scalar_one_or_none()

    if not activity:
        raise HTTPException(
            status_code=404,
            detail=f"Activity {activity_id} not found or not owned by user"
        )

    # Check if activity is used in any workflows
    if activity.workflow_relations:
        # Get workflow names for better error message
        workflow_names = [
            relation.workflow.workflow_name
            for relation in activity.workflow_relations
        ]
        raise HTTPException(
            status_code=409,  # Conflict
            detail=(
                f"Cannot delete activity '{activity.activity_name}' as it is used in the following workflows: "
                f"{', '.join(workflow_names)}"
            )
        )

    await session.delete(activity)  # This will cascade delete the ownership record
    await session.commit() 