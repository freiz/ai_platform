from typing import Dict
from pydantic import BaseModel


class CreateActivityRequest(BaseModel):
    """Request model for creating an activity."""
    activity_type_name: str
    allow_custom_params: bool
    params: Dict 