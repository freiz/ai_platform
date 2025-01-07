from typing import Dict

from fastapi import HTTPException

from src.activities import AdderActivity, LLMActivity, FreightQuoteActivity, IdentityActivity
from src.activities.activity_registry import ActivityRegistry, ActivityTypeInfo


def register_activities() -> None:
    """Register all available activities. Called during application startup."""
    try:
        ActivityRegistry.register_class(LLMActivity)
        ActivityRegistry.register_class(AdderActivity)
        ActivityRegistry.register_class(FreightQuoteActivity)
        ActivityRegistry.register_class(IdentityActivity)
    except ValueError as e:
        # If already registered, we can ignore
        if "already registered" not in str(e):
            raise


def get_activity_types(search: str | None = None) -> Dict[str, ActivityTypeInfo]:
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


def get_activity_type(activity_type_name: str) -> ActivityTypeInfo:
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
