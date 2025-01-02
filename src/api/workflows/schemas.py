from typing import Dict, List, Any
from uuid import UUID
from pydantic import BaseModel


class WorkflowNodeCreate(BaseModel):
    """Request model for creating a node in the workflow API."""
    activity_id: UUID


class WorkflowConnectionCreate(BaseModel):
    """Request model for creating a connection in the workflow API."""
    source_node: str  # Node ID
    source_output: str
    target_node: str  # Node ID
    target_input: str


class CreateWorkflowRequest(BaseModel):
    """Request model for creating a workflow."""
    workflow_name: str
    nodes: Dict[str, WorkflowNodeCreate]  # Map of node_id to node info
    connections: List[WorkflowConnectionCreate] | None = None  # Optional connections between nodes

    def __init__(self, **data):
        super().__init__(**data)
        if self.connections is None:
            self.connections = []


class WorkflowExecuteRequest(BaseModel):
    """Request model for executing a workflow."""
    inputs: Dict[str, Dict[str, Any]]  # Map of node_id to input parameters 