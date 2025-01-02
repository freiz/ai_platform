from typing import Dict, List, Set, Tuple

from src.database.models import ActivityModel
from .schemas import WorkflowNodeCreate, WorkflowConnectionCreate


def has_cycle(graph: Dict[str, List[str]], node: str, visited: Set[str], path: Set[str]) -> bool:
    """
    Check for cycles in a directed graph using DFS.
    
    Args:
        graph: Adjacency list representation of the graph
        node: Current node being visited
        visited: Set of all visited nodes
        path: Set of nodes in the current DFS path
        
    Returns:
        bool: True if a cycle is detected, False otherwise
    """
    visited.add(node)
    path.add(node)

    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if has_cycle(graph, neighbor, visited, path):
                return True
        elif neighbor in path:
            return True

    path.remove(node)
    return False


def validate_workflow_structure(
        nodes: Dict[str, WorkflowNodeCreate],
        connections: List[WorkflowConnectionCreate],
        activities: Dict[str, ActivityModel]
) -> Tuple[Set[str], Set[str]]:
    """
    Validate workflow structure including connections and parameter types.
    
    Args:
        nodes: Map of node_id to node info
        connections: List of connections between nodes
        activities: Map of activity_id to activity model
        
    Returns:
        Tuple of (root_nodes, leaf_nodes) sets
        
    Raises:
        ValueError: If any validation fails
    """
    # If there are multiple nodes but no connections, that's an error
    if not connections and len(nodes) > 1:
        raise ValueError("Multiple nodes present but no connections between them")

    # Build connection maps for validation
    connected_inputs = {
        f"{conn.target_node}.{conn.target_input}"
        for conn in connections
    }
    connected_outputs = {
        f"{conn.source_node}.{conn.source_output}"
        for conn in connections
    }

    # Check for multiple connections to the same input
    input_connection_count = {}
    for conn in connections:
        input_key = f"{conn.target_node}.{conn.target_input}"
        input_connection_count[input_key] = input_connection_count.get(input_key, 0) + 1
        if input_connection_count[input_key] > 1:
            raise ValueError(f"Multiple connections to the same input parameter: {input_key}")

    # Build adjacency list for cycle detection
    graph = {}
    for conn in connections:
        if conn.source_node not in graph:
            graph[conn.source_node] = []
        graph[conn.source_node].append(conn.target_node)

    # Check each node for cycles
    visited = set()
    for node in nodes:
        if node not in visited:
            if has_cycle(graph, node, visited, set()):
                raise ValueError("Cyclic dependency detected in workflow")

    # Find root and leaf nodes by analyzing connections
    target_nodes = {conn.target_node for conn in connections}
    source_nodes = {conn.source_node for conn in connections}

    # A node is a root if it's never a target
    root_nodes = set(nodes.keys()) - target_nodes
    # A node is a leaf if it's never a source
    leaf_nodes = set(nodes.keys()) - source_nodes

    # Special case: single node is both root and leaf
    if len(nodes) == 1:
        node_id = next(iter(nodes))
        root_nodes.add(node_id)
        leaf_nodes.add(node_id)

    # Verify all connection nodes exist and parameters are compatible
    if connections:
        for conn in connections:
            # Verify nodes exist
            if conn.source_node not in nodes:
                raise ValueError(f"Source node not found: {conn.source_node}")
            if conn.target_node not in nodes:
                raise ValueError(f"Target node not found: {conn.target_node}")

            # Get source and target activities
            source_activity = activities[str(nodes[conn.source_node].activity_id)]
            target_activity = activities[str(nodes[conn.target_node].activity_id)]

            # Verify parameters exist
            if conn.source_output not in source_activity.output_params_schema:
                raise ValueError(f"Output parameter {conn.source_output} not found in source node {conn.source_node}")
            if conn.target_input not in target_activity.input_params_schema:
                raise ValueError(f"Input parameter {conn.target_input} not found in target node {conn.target_node}")

            # Verify parameter types match
            source_type = source_activity.output_params_schema[conn.source_output]['type']
            target_type = target_activity.input_params_schema[conn.target_input]['type']
            if source_type != target_type:
                raise ValueError(
                    f"Type mismatch in connection: {conn.source_node}.{conn.source_output} ({source_type}) "
                    f"→ {conn.target_node}.{conn.target_input} ({target_type})"
                )

    # Verify all non-root inputs are connected
    for node_id, node in nodes.items():
        activity = activities[str(node.activity_id)]
        for input_param in activity.input_params_schema:
            param_key = f"{node_id}.{input_param}"
            if node_id not in root_nodes and param_key not in connected_inputs:
                raise ValueError(
                    f"Input parameter {input_param} of non-root node {node_id} is not connected"
                )

    # Verify all non-leaf outputs are connected
    for node_id, node in nodes.items():
        activity = activities[str(node.activity_id)]
        for output_param in activity.output_params_schema:
            param_key = f"{node_id}.{output_param}"
            if node_id not in leaf_nodes and param_key not in connected_outputs:
                raise ValueError(
                    f"Output parameter {output_param} of non-leaf node {node_id} is not connected"
                )

    # Find connected nodes and check for disconnected ones
    connected_nodes = {conn.source_node for conn in connections} | {conn.target_node for conn in connections}

    # If a node is not in any connection, it's an error (unless it's the only node)
    disconnected_nodes = set(nodes.keys()) - connected_nodes
    if disconnected_nodes and len(nodes) > 1:
        raise ValueError(f"Nodes are disconnected from the workflow: {', '.join(disconnected_nodes)}")

    return root_nodes, leaf_nodes
