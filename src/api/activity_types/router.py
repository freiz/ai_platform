from typing import Dict, Optional

from fastapi import APIRouter

from src.activities.activity_registry import ActivityTypeInfo
from .service import get_activity_types, get_activity_type

# Create router for activity types
router = APIRouter(
    prefix="/activity-types",
    tags=["activity-types"]
)


@router.get("", response_model=Dict[str, ActivityTypeInfo])
async def get_activity_types_endpoint(search: Optional[str] = None):
    """
    Get all registered activity types.
    
    Args:
        search: Optional search string to filter activity types by description
        
    Returns:
        Dictionary of activity type names to their metadata
    """
    return get_activity_types(search)


@router.get("/{activity_type_name}", response_model=ActivityTypeInfo)
async def get_activity_type_endpoint(activity_type_name: str):
    """
    Get activity type info by name.
    
    Args:
        activity_type_name: Name of the activity type to retrieve
        
    Returns:
        Activity type metadata
    """
    return get_activity_type(activity_type_name) 