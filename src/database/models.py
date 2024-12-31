from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ActivityModel(Base):
    """SQLAlchemy model for storing activities in the database."""
    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint('activity_name', name='uq_activity_name'),
    )

    # Primary key using the Activity's UUID
    id: Mapped[UUID] = mapped_column(primary_key=True)
    
    # Basic activity info
    activity_type_name: Mapped[str] = mapped_column(String(100))
    activity_name: Mapped[str] = mapped_column(String(100), unique=True)
    
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


class WorkflowModel(Base):
    """SQLAlchemy model for storing workflows in the database."""
    __tablename__ = "workflows"
    __table_args__ = (
        UniqueConstraint('workflow_name', name='uq_workflow_name'),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)
    
    # Basic workflow info
    workflow_name: Mapped[str] = mapped_column(String(100), unique=True)
    
    # Store workflow structure as JSON
    activities: Mapped[Dict[str, UUID]] = mapped_column(JSON)  # Map of activity name to UUID
    connections: Mapped[Dict] = mapped_column(JSON)  # List of connections with activity UUIDs
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"Workflow(id={self.id}, name={self.workflow_name})" 