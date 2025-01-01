class WorkflowError(Exception):
    """Base class for workflow-related exceptions."""
    pass


class NodeNotFoundError(WorkflowError):
    """Raised when a referenced node is not found in the workflow."""
    pass


class ParameterNotFoundError(WorkflowError):
    """Raised when a referenced parameter is not found in a node."""
    pass


class TypeMismatchError(WorkflowError):
    """Raised when trying to connect incompatible parameter types."""
    pass


class CyclicDependencyError(WorkflowError):
    """Raised when a cyclic dependency is detected in the workflow."""
    pass 