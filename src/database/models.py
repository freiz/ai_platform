from datetime import datetime, UTC
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy import JSON, DateTime, String, UniqueConstraint, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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

    # Relationships
    ownership: Mapped["ActivityOwnership"] = relationship(
        "ActivityOwnership",
        back_populates="activity",
        cascade="all, delete-orphan",
        uselist=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return (
            f"Activity(id={self.id}, "
            f"type={self.activity_type_name}, "
            f"name={self.activity_name})"
        )


class ActivityOwnership(Base):
    """SQLAlchemy model for storing activity ownership."""
    __tablename__ = "activity_ownership"
    __table_args__ = (
        UniqueConstraint('activity_id', 'user_id', name='uq_activity_user'),
    )

    # Composite primary key using activity_id and user_id
    activity_id: Mapped[UUID] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Relationships
    activity: Mapped["ActivityModel"] = relationship(
        "ActivityModel",
        back_populates="ownership",
        single_parent=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"ActivityOwnership(activity_id={self.activity_id}, user_id={self.user_id})"


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
    nodes: Mapped[Dict[str, Dict[str, Any]]] = mapped_column(JSON)  # Map of node_id to {activity_id: UUID, label: str}
    connections: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON)  # List of {source_node: str, source_output: str, target_node: str, target_input: str}

    # Relationships
    ownership: Mapped["WorkflowOwnership"] = relationship(
        "WorkflowOwnership",
        back_populates="workflow",
        cascade="all, delete-orphan",
        uselist=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"Workflow(id={self.id}, name={self.workflow_name})"


class WorkflowOwnership(Base):
    """SQLAlchemy model for storing workflow ownership."""
    __tablename__ = "workflow_ownership"
    __table_args__ = (
        UniqueConstraint('workflow_id', 'user_id', name='uq_workflow_user'),
    )

    # Composite primary key using workflow_id and user_id
    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("workflows.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Relationships
    workflow: Mapped["WorkflowModel"] = relationship(
        "WorkflowModel",
        back_populates="ownership",
        single_parent=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"WorkflowOwnership(workflow_id={self.workflow_id}, user_id={self.user_id})"
