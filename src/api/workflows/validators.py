from typing import Dict, List, Set, Tuple
from uuid import UUID

from src.database.models import ActivityModel
from .schemas import WorkflowNodeCreate, WorkflowConnectionCreate


def validate_workflow_structure(
        nodes: Dict[str, WorkflowNodeCreate],
        connections: List[WorkflowConnectionCreate],
        activities: Dict[str, ActivityModel]
) -> Tuple[Set[str], Set[str]]:
    """
    Validate workflow structure including node labels, connections, and parameter types.
    
    Args:
        nodes: Map of node_id to node info
        connections: List of connections between nodes
        activities: Map of activity_id to activity model
        
    Returns:
        Tuple of (root_nodes, leaf_nodes) sets
        
    Raises:
        ValueError: If any validation fails
    """
    # Check for duplicate labels
    node_labels = set()
    for node_id, node in nodes.items():
        if node.label in node_labels:
            raise ValueError(f"Duplicate node label found: {node.label}")
        node_labels.add(node.label)

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