from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ActivityModel(Base):
    """SQLAlchemy model for storing activities in the database."""
    __tablename__ = "activities"

    # Primary key using the Activity's UUID
    id: Mapped[UUID] = mapped_column(primary_key=True)
    
    # Basic activity info
    activity_type_name: Mapped[str] = mapped_column(String(100))
    activity_name: Mapped[str] = mapped_column(String(100))
    
    # Store activity parameters as JSON
    input_params_schema: Mapped[Dict] = mapped_column(JSON)  # Parameter definitions
    output_params_schema: Mapped[Dict] = mapped_column(JSON)  # Parameter definitions
    params: Mapped[Dict[str, Any]] = mapped_column(JSON)  # Creation parameters
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"Activity(id={self.id}, "
            f"type={self.activity_type_name}, "
            f"name={self.activity_name})"
        ) 