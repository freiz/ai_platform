import json
from uuid import UUID

import pytest

from src.activities import Activity, Parameter
from src.workflow import Workflow, Connection


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
        workflow.add_activity("uppercase", upper)  # First activity
        workflow.add_activity("length", str_len)   # Second activity

        # Connect activities using UUIDs - text input goes to uppercase, then uppercase output goes to length
        workflow.connect_activities(upper.id, 'uppercase_text', str_len.id, 'text')

        # Set input - goes to the first activity (uppercase)
        input_data = {'text': 'hello'}
        result = workflow.run(input_data)

        # Final output should be the length of the uppercase text
        assert result['length'] == 5

    def test_workflow_serialization(self):
        workflow = Workflow()
        str_len = StringLengthActivity()
        workflow.add_activity(str_len.activity_name, str_len)

        serialized = workflow.model_dump()
        assert 'activities' in serialized
        assert len(serialized['activities']) == 1
        assert str_len.activity_name in serialized['activities']

    def test_input_validation(self):
        workflow = Workflow()
        str_len = StringLengthActivity()
        workflow.add_activity(str_len.activity_name, str_len)

        with pytest.raises(ValueError):
            workflow.run({})  # Missing required input

        with pytest.raises(ValueError):
            workflow.run({'text': 123})  # Wrong type (integer instead of string)

    def test_connection_model(self):
        # Test creating a valid connection with UUIDs
        str_len = StringLengthActivity()
        upper = UppercaseActivity()
        
        connection = Connection(
            source_activity_id=upper.id,
            source_output="uppercase_text",
            target_activity_id=str_len.id,
            target_input="text"
        )
        assert isinstance(connection.source_activity_id, UUID)
        assert connection.source_output == "uppercase_text"
        assert isinstance(connection.target_activity_id, UUID)
        assert connection.target_input == "text"

        # Test connection serialization
        connection_dict = connection.model_dump()
        assert str(connection_dict["source_activity_id"]) == str(upper.id)
        assert connection_dict["source_output"] == "uppercase_text"
        assert str(connection_dict["target_activity_id"]) == str(str_len.id)
        assert connection_dict["target_input"] == "text"

    def test_connection_json_serialization(self):
        """Test Connection JSON serialization/deserialization."""
        # Create activities to get UUIDs
        str_len = StringLengthActivity()
        upper = UppercaseActivity()
        
        # Create a connection
        connection = Connection(
            source_activity_id=upper.id,
            source_output="uppercase_text",
            target_activity_id=str_len.id,
            target_input="text"
        )

        # Test serialization to JSON
        json_str = connection.model_dump_json()

        # Test deserialization from JSON
        loaded_connection = Connection.model_validate_json(json_str)

        # Verify the deserialized object matches the original
        assert str(loaded_connection.source_activity_id) == str(connection.source_activity_id)
        assert loaded_connection.source_output == connection.source_output
        assert str(loaded_connection.target_activity_id) == str(connection.target_activity_id)
        assert loaded_connection.target_input == connection.target_input

    def test_workflow_json_serialization(self):
        """Test Workflow JSON serialization/deserialization."""
        # Create a workflow with activities and connections
        workflow = Workflow()

        # Add activities
        str_len = StringLengthActivity()
        upper = UppercaseActivity()
        workflow.add_activity("uppercase", upper)  # First activity
        workflow.add_activity("length", str_len)   # Second activity

        # Add connection using UUIDs - uppercase output goes to length input
        workflow.connect_activities(
            upper.id, 'uppercase_text',
            str_len.id, 'text'
        )

        # Test serialization to JSON
        json_str = workflow.model_dump_json()

        # Test deserialization from JSON
        data = json.loads(json_str)

        # Create a mapping of activity names to their original UUIDs
        activity_ids = {
            name: UUID(activity_data['id']) 
            for name, activity_data in data['activities'].items()
        }

        # Reconstruct activities with original UUIDs
        loaded_workflow = Workflow()
        for name, activity_data in data['activities'].items():
            activity_id = activity_ids[name]
            if activity_data['activity_name'] == 'string_length':
                activity = StringLengthActivity(activity_name=activity_data['activity_name'])
                activity.id = activity_id  # Restore original UUID
            else:
                activity = UppercaseActivity(activity_name=activity_data['activity_name'])
                activity.id = activity_id  # Restore original UUID
            loaded_workflow.add_activity(name, activity)

        # Reconstruct connections
        for conn_data in data['connections']:
            loaded_workflow.connect_activities(
                UUID(conn_data['source_activity_id']),
                conn_data['source_output'],
                UUID(conn_data['target_activity_id']),
                conn_data['target_input']
            )

        # Verify activities
        assert len(loaded_workflow.activities) == len(workflow.activities)
        for name, activity in workflow.activities.items():
            loaded_activity = loaded_workflow.activities[name]
            assert loaded_activity.activity_name == activity.activity_name
            assert loaded_activity.id == activity.id  # Verify UUIDs match
            assert len(loaded_activity.input_params) == len(activity.input_params)
            assert len(loaded_activity.output_params) == len(activity.output_params)

        # Verify connections
        assert len(loaded_workflow.connections) == len(workflow.connections)
        for conn, loaded_conn in zip(workflow.connections, loaded_workflow.connections):
            assert str(loaded_conn.source_activity_id) == str(conn.source_activity_id)
            assert loaded_conn.source_output == conn.source_output
            assert str(loaded_conn.target_activity_id) == str(conn.target_activity_id)
            assert loaded_conn.target_input == conn.target_input

        # Test that the loaded workflow can still execute
        result = loaded_workflow.run({'text': 'hello'})
        assert result['length'] == 5


if __name__ == '__main__':
    pytest.main()
