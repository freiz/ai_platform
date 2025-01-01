from typing import Dict, List, Any

from pydantic import BaseModel, Field

from src.activities import Activity
from .exceptions import (
    NodeNotFoundError,
    ParameterNotFoundError,
    TypeMismatchError,
    CyclicDependencyError
)
from .models import WorkflowNode, Connection


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
                     target_input: str) -> None:
        """
        Connect two nodes by mapping an output to an input.
        
        Args:
            source_node (str): ID of the source node
            source_output (str): Output parameter name of the source node
            target_node (str): ID of the target node
            target_input (str): Input parameter name of the target node
        
        Raises:
            NodeNotFoundError: If nodes are not found
            ParameterNotFoundError: If parameters are not found
            TypeMismatchError: If parameter types are incompatible
        """
        # Find source and target nodes
        if source_node not in self.nodes or target_node not in self.nodes:
            raise NodeNotFoundError("Node not found")

        source = self.nodes[source_node].activity
        target = self.nodes[target_node].activity

        # Validate output and input parameters
        if source_output not in source.output_params:
            raise ParameterNotFoundError(f"Output parameter {source_output} not found in source node")

        if target_input not in target.input_params:
            raise ParameterNotFoundError(f"Input parameter {target_input} not found in target node")

        # Check type compatibility
        source_param = source.output_params[source_output]
        target_param = target.input_params[target_input]

        if source_param.type != target_param.type:
            raise TypeMismatchError(
                f"Type mismatch: {source_output} ({source_param.type}) "
                f"cannot be connected to {target_input} ({target_param.type})"
            )

        # Add connection
        connection = Connection(
            source_node=source_node,
            source_output=source_output,
            target_node=target_node,
            target_input=target_input
        )
        self.connections.append(connection)

    def run(self, inputs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Execute the workflow with inputs for root nodes.
        
        Args:
            inputs (Dict[str, Dict[str, Any]]): Map of node_id to input parameters for root nodes
        
        Returns:
            Dict[str, Dict[str, Any]]: Map of node_id to output parameters for leaf nodes
            
        Raises:
            CyclicDependencyError: If cyclic dependencies are detected
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

            # If this is a root node, get inputs from the inputs map
            if node_id in inputs:
                node_inputs.update(inputs[node_id])

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

        # Find leaf nodes (nodes that are never source nodes in connections)
        source_nodes = {conn.source_node for conn in self.connections}
        leaf_nodes = set(self.nodes.keys()) - source_nodes

        # Special case: single node is both root and leaf
        if len(self.nodes) == 1:
            leaf_nodes.add(next(iter(self.nodes)))

        # Return outputs from all leaf nodes
        return {
            node_id: node_outputs[node_id]
            for node_id in leaf_nodes
        }

    def _topological_sort(self) -> List[str]:
        """
        Perform a topological sort of nodes based on connections.
        
        Returns:
            List[str]: Sorted list of node IDs
        
        Raises:
            CyclicDependencyError: If a cyclic dependency is detected
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
            raise CyclicDependencyError("Cyclic dependencies detected in workflow")

        return sorted_nodes 