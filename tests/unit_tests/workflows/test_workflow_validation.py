from uuid import UUID, uuid4

import pytest

from src.api.workflows.schemas import WorkflowNodeCreate, WorkflowConnectionCreate
from src.api.workflows.validators import validate_workflow_structure
from src.database.models import ActivityModel


def create_mock_activity_model(input_params: dict, output_params: dict, activity_id: UUID) -> ActivityModel:
    """Helper function to create a mock activity model."""
    return ActivityModel(
        id=activity_id,
        activity_type_name="mock_activity",
        activity_name="mock_activity",
        input_params_schema=input_params,
        output_params_schema=output_params,
        params={}
    )


def test_validate_missing_nodes():
    """Test that missing nodes in connections are detected."""
    activity1_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id)
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="output1",
            target_node="nonexistent",  # This node doesn't exist
            target_input="input1"
        )
    ]

    with pytest.raises(ValueError, match="Target node not found"):
        validate_workflow_structure(nodes, connections, activities)


def test_validate_parameter_types():
    """Test that parameter type mismatches are detected."""
    activity1_id = uuid4()
    activity2_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id, label="Node 1"),
        "node2": WorkflowNodeCreate(activity_id=activity2_id, label="Node 2")
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        ),
        str(activity2_id): create_mock_activity_model(
            input_params={"input1": {"type": "integer"}},  # Different type
            output_params={"output1": {"type": "string"}},
            activity_id=activity2_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="output1",
            target_node="node2",
            target_input="input1"  # String to integer mismatch
        )
    ]

    with pytest.raises(ValueError, match="Type mismatch"):
        validate_workflow_structure(nodes, connections, activities)


def test_validate_missing_parameters():
    """Test that missing parameters in connections are detected."""
    activity1_id = uuid4()
    activity2_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id, label="Node 1"),
        "node2": WorkflowNodeCreate(activity_id=activity2_id, label="Node 2")
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        ),
        str(activity2_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity2_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="nonexistent",  # This parameter doesn't exist
            target_node="node2",
            target_input="input1"
        )
    ]

    with pytest.raises(ValueError, match="Output parameter .* not found"):
        validate_workflow_structure(nodes, connections, activities)


def test_validate_unconnected_parameters():
    """Test that unconnected parameters in non-root/leaf nodes are detected."""
    activity1_id = uuid4()
    activity2_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id, label="Node 1"),
        "node2": WorkflowNodeCreate(activity_id=activity2_id, label="Node 2")
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        ),
        str(activity2_id): create_mock_activity_model(
            input_params={
                "input1": {"type": "string"},
                "input2": {"type": "string"}  # Additional input parameter
            },
            output_params={"output1": {"type": "string"}},
            activity_id=activity2_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="output1",
            target_node="node2",
            target_input="input1"  # Only input1 is connected, input2 is not
        )
    ]

    with pytest.raises(ValueError, match="Input parameter input2 of non-root node node2 is not connected"):
        validate_workflow_structure(nodes, connections, activities)


def test_validate_unconnected_outputs():
    """Test that unconnected output parameters in non-leaf nodes are detected."""
    activity1_id = uuid4()
    activity2_id = uuid4()
    activity3_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id, label="Node 1"),
        "node2": WorkflowNodeCreate(activity_id=activity2_id, label="Node 2"),
        "node3": WorkflowNodeCreate(activity_id=activity3_id, label="Node 3")
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        ),
        str(activity2_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={
                "output1": {"type": "string"},
                "output2": {"type": "string"}  # Additional output parameter
            },
            activity_id=activity2_id
        ),
        str(activity3_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity3_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="output1",
            target_node="node2",
            target_input="input1"
        ),
        WorkflowConnectionCreate(
            source_node="node2",
            source_output="output1",  # Only output1 is connected, output2 is not
            target_node="node3",
            target_input="input1"
        )
    ]

    with pytest.raises(ValueError, match="Output parameter output2 of non-leaf node node2 is not connected"):
        validate_workflow_structure(nodes, connections, activities)


def test_validate_valid_workflow():
    """Test that a valid workflow passes validation."""
    activity1_id = uuid4()
    activity2_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id),
        "node2": WorkflowNodeCreate(activity_id=activity2_id)
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        ),
        str(activity2_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity2_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="output1",
            target_node="node2",
            target_input="input1"
        )
    ]

    # Should not raise any exceptions
    root_nodes, leaf_nodes = validate_workflow_structure(nodes, connections, activities)

    # Verify root and leaf nodes
    assert root_nodes == {"node1"}
    assert leaf_nodes == {"node2"}


def test_validate_single_node_workflow():
    """Test that a workflow with a single node and no connections is valid."""
    activity1_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id)
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        )
    }

    # Should not raise any exceptions
    root_nodes, leaf_nodes = validate_workflow_structure(nodes, [], activities)

    # Single node should be both root and leaf
    assert root_nodes == {"node1"}
    assert leaf_nodes == {"node1"}


def test_validate_disconnected_nodes():
    """Test that disconnected nodes in a multi-node workflow are detected."""
    activity1_id = uuid4()
    activity2_id = uuid4()
    activity3_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id),
        "node2": WorkflowNodeCreate(activity_id=activity2_id),
        "node3": WorkflowNodeCreate(activity_id=activity3_id)  # Disconnected node
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        ),
        str(activity2_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity2_id
        ),
        str(activity3_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity3_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="output1",
            target_node="node2",
            target_input="input1"
        )
    ]

    with pytest.raises(ValueError, match="Nodes are disconnected from the workflow: node3"):
        validate_workflow_structure(nodes, connections, activities)


def test_validate_multiple_connections_to_input():
    """Test that multiple connections to the same input parameter are detected."""
    activity1_id = uuid4()
    activity2_id = uuid4()
    activity3_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id),
        "node2": WorkflowNodeCreate(activity_id=activity2_id),
        "node3": WorkflowNodeCreate(activity_id=activity3_id)
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        ),
        str(activity2_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity2_id
        ),
        str(activity3_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity3_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="output1",
            target_node="node3",
            target_input="input1"
        ),
        WorkflowConnectionCreate(
            source_node="node2",
            source_output="output1",
            target_node="node3",
            target_input="input1"  # Same input as above
        )
    ]

    with pytest.raises(ValueError, match="Multiple connections to the same input parameter"):
        validate_workflow_structure(nodes, connections, activities)


def test_validate_cyclic_reference():
    """Test that cyclic references between nodes are detected."""
    activity1_id = uuid4()
    activity2_id = uuid4()
    nodes = {
        "node1": WorkflowNodeCreate(activity_id=activity1_id),
        "node2": WorkflowNodeCreate(activity_id=activity2_id)
    }
    activities = {
        str(activity1_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity1_id
        ),
        str(activity2_id): create_mock_activity_model(
            input_params={"input1": {"type": "string"}},
            output_params={"output1": {"type": "string"}},
            activity_id=activity2_id
        )
    }
    connections = [
        WorkflowConnectionCreate(
            source_node="node1",
            source_output="output1",
            target_node="node2",
            target_input="input1"
        ),
        WorkflowConnectionCreate(
            source_node="node2",
            source_output="output1",
            target_node="node1",
            target_input="input1"  # Creates a cycle
        )
    ]

    with pytest.raises(ValueError, match="Cyclic dependency detected in workflow"):
        validate_workflow_structure(nodes, connections, activities)
