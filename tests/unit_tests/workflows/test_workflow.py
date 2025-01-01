import json
from uuid import UUID

import pytest

from src.activities import Activity, Parameter
from src.workflows import (
    Workflow,
    NodeNotFoundError,
    ParameterNotFoundError
)


class StringLengthActivity(Activity):
    def __init__(self, activity_name: str = "string_length"):
        input_params = {
            'text': Parameter(name='text', type="string")
        }
        output_params = {
            'length': Parameter(name='length', type="integer")
        }
        super().__init__(activity_name=activity_name, input_params=input_params, output_params=output_params)

    def run(self, text):
        return {'length': len(text)}


class UppercaseActivity(Activity):
    def __init__(self, activity_name: str = "uppercase"):
        input_params = {
            'text': Parameter(name='text', type="string")
        }
        output_params = {
            'uppercase_text': Parameter(name='uppercase_text', type="string")
        }
        super().__init__(activity_name=activity_name, input_params=input_params, output_params=output_params)

    def run(self, text):
        return {'uppercase_text': text.upper()}


class ConcatActivity(Activity):
    def __init__(self, activity_name: str = "concat"):
        input_params = {
            'text1': Parameter(name='text1', type="string"),
            'text2': Parameter(name='text2', type="string")
        }
        output_params = {
            'concatenated': Parameter(name='concatenated', type="string")
        }
        super().__init__(activity_name=activity_name, input_params=input_params, output_params=output_params)

    def run(self, text1, text2):
        return {'concatenated': text1 + text2}


class TestWorkflow:
    def test_single_node_workflow(self):
        """Test workflow with a single node (both root and leaf)."""
        # Create activity
        upper = UppercaseActivity()

        # Create workflow with single node
        workflow = Workflow()
        workflow.add_node("upper1", upper, "First Uppercase")

        # Execute workflow
        result = workflow.run({
            "upper1": {"text": "hello"}
        })

        # Single node should be both root and leaf
        assert len(result) == 1
        assert "upper1" in result
        assert result["upper1"]["uppercase_text"] == "HELLO"

    def test_linear_workflow(self):
        """Test workflow with linear chain of nodes."""
        # Create activities
        str_len = StringLengthActivity()
        upper = UppercaseActivity()

        # Create workflow
        workflow = Workflow()
        workflow.add_node("uppercase1", upper, "First Uppercase")  # First activity
        workflow.add_node("length1", str_len, "First Length")  # Second activity

        # Connect nodes - uppercase output goes to length input
        workflow.connect_nodes(
            source_node="uppercase1",
            source_output="uppercase_text",
            target_node="length1",
            target_input="text"
        )

        # Execute workflow
        result = workflow.run({
            "uppercase1": {"text": "hello"}
        })

        # Only leaf node (length1) should be in result
        assert len(result) == 1
        assert "length1" in result
        assert result["length1"]["length"] == 5

    def test_multiple_root_nodes(self):
        """Test workflow with multiple root nodes feeding into a single leaf node."""
        # Create activities
        upper1 = UppercaseActivity()
        upper2 = UppercaseActivity()
        concat = ConcatActivity()

        # Create workflow
        workflow = Workflow()
        workflow.add_node("upper1", upper1, "First Uppercase")  # First root
        workflow.add_node("upper2", upper2, "Second Uppercase")  # Second root
        workflow.add_node("concat", concat, "Concatenate")  # Leaf

        # Connect nodes
        workflow.connect_nodes(
            source_node="upper1",
            source_output="uppercase_text",
            target_node="concat",
            target_input="text1"
        )
        workflow.connect_nodes(
            source_node="upper2",
            source_output="uppercase_text",
            target_node="concat",
            target_input="text2"
        )

        # Execute workflow with inputs for both root nodes
        result = workflow.run({
            "upper1": {"text": "hello"},
            "upper2": {"text": "world"}
        })

        # Only leaf node (concat) should be in result
        assert len(result) == 1
        assert "concat" in result
        assert result["concat"]["concatenated"] == "HELLOWORLD"

    def test_multiple_leaf_nodes(self):
        """Test workflow with one root node feeding into multiple leaf nodes."""
        # Create activities
        upper = UppercaseActivity()
        len1 = StringLengthActivity()
        len2 = StringLengthActivity()

        # Create workflow
        workflow = Workflow()
        workflow.add_node("upper", upper, "Uppercase")  # Root
        workflow.add_node("len1", len1, "First Length")  # First leaf
        workflow.add_node("len2", len2, "Second Length")  # Second leaf

        # Connect nodes
        workflow.connect_nodes(
            source_node="upper",
            source_output="uppercase_text",
            target_node="len1",
            target_input="text"
        )
        workflow.connect_nodes(
            source_node="upper",
            source_output="uppercase_text",
            target_node="len2",
            target_input="text"
        )

        # Execute workflow
        result = workflow.run({
            "upper": {"text": "hello"}
        })

        # Both leaf nodes should be in result
        assert len(result) == 2
        assert "len1" in result
        assert "len2" in result
        assert result["len1"]["length"] == 5
        assert result["len2"]["length"] == 5

    def test_workflow_node_validation(self):
        workflow = Workflow()
        str_len = StringLengthActivity()

        # Add a node
        workflow.add_node("length1", str_len, "First Length")

        # Test connecting non-existent nodes
        with pytest.raises(NodeNotFoundError, match="Node not found"):
            workflow.connect_nodes("nonexistent", "output", "length1", "text")

        with pytest.raises(NodeNotFoundError, match="Node not found"):
            workflow.connect_nodes("length1", "length", "nonexistent", "text")

        # Test connecting with invalid parameters
        upper = UppercaseActivity()
        workflow.add_node("upper1", upper, "First Uppercase")

        with pytest.raises(ParameterNotFoundError, match="Output parameter .* not found"):
            workflow.connect_nodes("upper1", "nonexistent", "length1", "text")

        with pytest.raises(ParameterNotFoundError, match="Input parameter .* not found"):
            workflow.connect_nodes("upper1", "uppercase_text", "length1", "nonexistent")

    def test_workflow_serialization(self):
        workflow = Workflow()
        str_len = StringLengthActivity()
        workflow.add_node("length1", str_len, "First Length")

        serialized = workflow.model_dump()
        assert 'nodes' in serialized
        assert len(serialized['nodes']) == 1
        assert 'length1' in serialized['nodes']
        assert serialized['nodes']['length1']['label'] == "First Length"

    def test_workflow_json_serialization(self):
        """Test Workflow JSON serialization/deserialization."""
        # Create a workflow with activities and connections
        workflow = Workflow()

        # Add activities as nodes
        str_len = StringLengthActivity()
        upper = UppercaseActivity()
        workflow.add_node("uppercase1", upper, "First Uppercase")
        workflow.add_node("length1", str_len, "First Length")

        # Add connection
        workflow.connect_nodes(
            source_node="uppercase1",
            source_output="uppercase_text",
            target_node="length1",
            target_input="text"
        )

        # Test serialization to JSON
        json_str = workflow.model_dump_json()

        # Test deserialization from JSON
        data = json.loads(json_str)

        # Reconstruct workflow
        loaded_workflow = Workflow()

        # Reconstruct nodes
        for node_id, node_data in data['nodes'].items():
            # Create appropriate activity instance
            if "string_length" in node_data['activity']['activity_name']:
                activity = StringLengthActivity(activity_name=node_data['activity']['activity_name'])
            else:
                activity = UppercaseActivity(activity_name=node_data['activity']['activity_name'])

            # Set activity ID to match original
            activity.id = UUID(node_data['activity']['id'])

            # Add node to workflow
            loaded_workflow.add_node(node_id, activity, node_data['label'])

        # Reconstruct connections
        for conn_data in data['connections']:
            loaded_workflow.connect_nodes(
                conn_data['source_node'],
                conn_data['source_output'],
                conn_data['target_node'],
                conn_data['target_input']
            )

        # Verify nodes
        assert len(loaded_workflow.nodes) == len(workflow.nodes)
        for node_id, node in workflow.nodes.items():
            loaded_node = loaded_workflow.nodes[node_id]
            assert loaded_node.label == node.label
            assert loaded_node.activity.activity_name == node.activity.activity_name
            assert loaded_node.activity.id == node.activity.id
            assert len(loaded_node.activity.input_params) == len(node.activity.input_params)
            assert len(loaded_node.activity.output_params) == len(node.activity.output_params)

        # Verify connections
        assert len(loaded_workflow.connections) == len(workflow.connections)
        for conn, loaded_conn in zip(workflow.connections, loaded_workflow.connections):
            assert loaded_conn.source_node == conn.source_node
            assert loaded_conn.source_output == conn.source_output
            assert loaded_conn.target_node == conn.target_node
            assert loaded_conn.target_input == conn.target_input

        # Test that the loaded workflow can still execute
        result = loaded_workflow.run({
            "uppercase1": {"text": "hello"}
        })
        assert "length1" in result
        assert result["length1"]["length"] == 5


if __name__ == '__main__':
    pytest.main()
