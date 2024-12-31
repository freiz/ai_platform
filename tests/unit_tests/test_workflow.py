import json
from uuid import UUID

import pytest

from src.activities import Activity, Parameter
from src.workflow import Workflow, Connection, WorkflowNode


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


class TestWorkflow:
    def test_workflow_execution(self):
        # Create activities
        str_len = StringLengthActivity()
        upper = UppercaseActivity()

        # Create workflow
        workflow = Workflow()
        workflow.add_node("uppercase1", upper, "First Uppercase")  # First activity
        workflow.add_node("length1", str_len, "First Length")   # Second activity

        # Connect nodes - uppercase output goes to length input
        workflow.connect_nodes(
            source_node="uppercase1",
            source_output="uppercase_text",
            target_node="length1",
            target_input="text"
        )

        # Set input - goes to the first activity (uppercase)
        input_data = {'text': 'hello'}
        result = workflow.run(input_data)

        # Final output should be the length of the uppercase text
        assert result['length'] == 5

    def test_workflow_reuse_activity(self):
        """Test that the same activity can be used multiple times in a workflow."""
        # Create activities
        str_len = StringLengthActivity()
        upper = UppercaseActivity()

        # Create workflow with multiple instances of the same activities
        workflow = Workflow()
        workflow.add_node("upper1", upper, "First Uppercase")
        workflow.add_node("upper2", upper, "Second Uppercase")  # Reusing uppercase activity

        # Connect nodes: text -> upper1 -> upper2
        # First uppercase converts 'hello' to 'HELLO'
        # Second uppercase keeps it as 'HELLO' (since it's already uppercase)
        workflow.connect_nodes("upper1", "uppercase_text", "upper2", "text")

        # Run workflow with initial input
        result = workflow.run({'text': 'hello'})

        # The final result should still be 'HELLO'
        assert result['uppercase_text'] == 'HELLO'

        # Let's also test with a more complex workflow using compatible types
        workflow2 = Workflow()
        workflow2.add_node("upper1", upper, "First Uppercase")
        workflow2.add_node("upper2", upper, "Second Uppercase")
        workflow2.add_node("upper3", upper, "Third Uppercase")

        # Create a chain of uppercase conversions (each one receives string and outputs string)
        workflow2.connect_nodes("upper1", "uppercase_text", "upper2", "text")
        workflow2.connect_nodes("upper2", "uppercase_text", "upper3", "text")

        result2 = workflow2.run({'text': 'hello'})
        assert result2['uppercase_text'] == 'HELLO'  # Still HELLO since uppercase is idempotent

    def test_workflow_node_validation(self):
        workflow = Workflow()
        str_len = StringLengthActivity()

        # Add a node
        workflow.add_node("length1", str_len, "First Length")

        # Test connecting non-existent nodes
        with pytest.raises(ValueError, match="Node not found"):
            workflow.connect_nodes("nonexistent", "output", "length1", "text")

        with pytest.raises(ValueError, match="Node not found"):
            workflow.connect_nodes("length1", "length", "nonexistent", "text")

        # Test connecting with invalid parameters
        upper = UppercaseActivity()
        workflow.add_node("upper1", upper, "First Uppercase")

        with pytest.raises(ValueError, match="Output parameter .* not found"):
            workflow.connect_nodes("upper1", "nonexistent", "length1", "text")

        with pytest.raises(ValueError, match="Input parameter .* not found"):
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

    def test_connection_model(self):
        # Test creating a valid connection
        connection = Connection(
            source_node="node1",
            source_output="output1",
            target_node="node2",
            target_input="input1"
        )
        assert connection.source_node == "node1"
        assert connection.source_output == "output1"
        assert connection.target_node == "node2"
        assert connection.target_input == "input1"

        # Test connection serialization
        connection_dict = connection.model_dump()
        assert connection_dict["source_node"] == "node1"
        assert connection_dict["source_output"] == "output1"
        assert connection_dict["target_node"] == "node2"
        assert connection_dict["target_input"] == "input1"

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
        result = loaded_workflow.run({'text': 'hello'})
        assert result['length'] == 5


if __name__ == '__main__':
    pytest.main()
