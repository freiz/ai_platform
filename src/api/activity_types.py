from typing import Dict, Optional

from fastapi import APIRouter, HTTPException

from src.activities.activity_registry import ActivityRegistry, ActivityTypeInfo
from src.activities.llm_activity import LLMActivity

# Create router instead of app
router = APIRouter(
    prefix="/activity-types",
    tags=["activity-types"]
)


def register_activities():
    """Register all available activities. Called during application startup."""
    try:
        ActivityRegistry.register_class(LLMActivity)
    except ValueError as e:
        # If already registered, we can ignore
        if "already registered" not in str(e):
            raise


@router.get("", response_model=Dict[str, ActivityTypeInfo])
async def get_activity_types(search: Optional[str] = None):
    """
    Get all registered activity types.
    
    Args:
        search: Optional search string to filter activity types by description
        
    Returns:
        Dictionary of activity type names to their metadata
    """
    activity_types = ActivityRegistry().get_activity_types()

    if search:
        # Filter activity types whose description contains the search string (case-insensitive)
        activity_types = {
            name: info for name, info in activity_types.items()
            if search.lower() in info.description.lower()
        }

    return activity_types


@router.get("/{activity_type_name}", response_model=ActivityTypeInfo)
async def get_activity_type(activity_type_name: str):
    """
    Get activity type info by name.
    
    Args:
        activity_type_name: Name of the activity type to retrieve
        
    Returns:
        Activity type metadata
        
    Raises:
        HTTPException: If activity type not found
    """
    try:
        return ActivityRegistry().get_activity_type(activity_type_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
