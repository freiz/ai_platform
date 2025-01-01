from pydantic import BaseModel

from src.activities import Activity


class WorkflowNode(BaseModel):
    """
    Represents a node in the workflow.
    
    Attributes:
        id (str): Unique identifier for this node in the workflow
        activity (Activity): The activity instance for this node
        label (str): User-provided label for this node
    """
    id: str
    activity: Activity
    label: str

    class Config:
        arbitrary_types_allowed = True


class Connection(BaseModel):
    """
    Represents a connection between two nodes in a workflow.
    
    Attributes:
        source_node (str): ID of the source node
        source_output (str): Output parameter name of the source node
        target_node (str): ID of the target node
        target_input (str): Input parameter name of the target node
    """
    source_node: str
    source_output: str
    target_node: str
    target_input: str 