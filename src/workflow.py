from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field

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


class Workflow(BaseModel):
    """
    Represents a workflow composed of interconnected activity nodes.
    
    Attributes:
        nodes (Dict[str, WorkflowNode]): Dictionary of nodes in the workflow, keyed by node ID
        connections (List[Connection]): Connections between nodes
    """
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict)
    connections: List[Connection] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def add_node(self, node_id: str, activity: Activity, label: str) -> None:
        """
        Add a node to the workflow.
        
        Args:
            node_id (str): Unique identifier for this node
            activity (Activity): Activity instance for this node
            label (str): User-provided label for this node
        """
        self.nodes[node_id] = WorkflowNode(
            id=node_id,
            activity=activity,
            label=label
        )

    def connect_nodes(self,
                      source_node: str,
                      source_output: str,
                      target_node: str,
                      target_input: str):
        """
        Connect two nodes by mapping an output to an input.
        
        Args:
            source_node (str): ID of the source node
            source_output (str): Output parameter name of the source node
            target_node (str): ID of the target node
            target_input (str): Input parameter name of the target node
        
        Raises:
            ValueError: If nodes or parameters are not found
        """
        # Find source and target nodes
        if source_node not in self.nodes or target_node not in self.nodes:
            raise ValueError("Node not found")

        source = self.nodes[source_node].activity
        target = self.nodes[target_node].activity

        # Validate output and input parameters
        if source_output not in source.output_params:
            raise ValueError(f"Output parameter {source_output} not found in source node")

        if target_input not in target.input_params:
            raise ValueError(f"Input parameter {target_input} not found in target node")

        # Check type compatibility
        source_param = source.output_params[source_output]
        target_param = target.input_params[target_input]

        if source_param.type != target_param.type:
            raise ValueError(f"Type mismatch: {source_output} ({source_param.type}) "
                             f"cannot be connected to {target_input} ({target_param.type})")

        # Add connection
        connection = Connection(
            source_node=source_node,
            source_output=source_output,
            target_node=target_node,
            target_input=target_input
        )
        self.connections.append(connection)

    def run(self, initial_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the workflow with optional initial inputs.
        
        Args:
            initial_inputs (Optional[Dict[str, Any]]): Initial inputs for the first node
        
        Returns:
            Dict[str, Any]: Final outputs of the workflow
        """
        # Topological sort of nodes based on connections
        sorted_nodes = self._topological_sort()

        # Track outputs of each node
        node_outputs: Dict[str, Dict[str, Any]] = {}

        # Run nodes in order
        for node_id in sorted_nodes:
            node = self.nodes[node_id]
            # Prepare inputs for this node
            node_inputs = {}

            # If it's the first node and initial inputs are provided
            if node_id == sorted_nodes[0] and initial_inputs:
                node_inputs.update(initial_inputs)

            # Check connections to fill inputs
            for connection in self.connections:
                if connection.target_node == node_id:
                    source_output = connection.source_output
                    target_input = connection.target_input

                    # Use output from previous node as input
                    node_inputs[target_input] = node_outputs[connection.source_node][source_output]

            # Run the node's activity
            outputs = node.activity(**node_inputs)
            node_outputs[node_id] = outputs

        # Return outputs of the last node
        return node_outputs[sorted_nodes[-1]]

    def _topological_sort(self) -> List[str]:
        """
        Perform a topological sort of nodes based on connections.
        
        Returns:
            List[str]: Sorted list of node IDs
        
        Raises:
            ValueError: If a cyclic dependency is detected
        """
        # Create adjacency list and in-degree map
        graph = {node_id: [] for node_id in self.nodes}
        in_degree = {node_id: 0 for node_id in self.nodes}

        # Build graph based on connections
        for connection in self.connections:
            graph[connection.source_node].append(connection.target_node)
            in_degree[connection.target_node] += 1

        # Perform topological sort
        queue = [node_id for node_id in self.nodes if in_degree[node_id] == 0]
        sorted_nodes = []

        while queue:
            current_node = queue.pop(0)
            sorted_nodes.append(current_node)

            # Find connected nodes
            for target_node in graph[current_node]:
                in_degree[target_node] -= 1
                if in_degree[target_node] == 0:
                    queue.append(target_node)

        # Check for cyclic dependencies
        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Cyclic dependencies detected in workflow")

        return sorted_nodes
