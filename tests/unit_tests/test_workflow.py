import json

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
        workflow.add_activity(str_len.activity_name, str_len)
        workflow.add_activity(upper.activity_name, upper)

        # Connect activities
        workflow.connect_activities(upper.activity_name, 'uppercase_text', str_len.activity_name, 'text')

        # Set input
        input_data = {'text': 'hello'}
        result = workflow.run(input_data)

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
        # Test creating a valid connection
        connection = Connection(
            source_activity_name="activity1",
            source_output="output1",
            target_activity_name="activity2",
            target_input="input1"
        )
        assert connection.source_activity_name == "activity1"
        assert connection.source_output == "output1"
        assert connection.target_activity_name == "activity2"
        assert connection.target_input == "input1"

        # Test connection serialization
        connection_dict = connection.model_dump()
        assert connection_dict["source_activity_name"] == "activity1"
        assert connection_dict["source_output"] == "output1"
        assert connection_dict["target_activity_name"] == "activity2"
        assert connection_dict["target_input"] == "input1"

    def test_connection_json_serialization(self):
        """Test Connection JSON serialization/deserialization."""
        # Create a connection
        connection = Connection(
            source_activity_name="source_activity",
            source_output="output1",
            target_activity_name="target_activity",
            target_input="input1"
        )

        # Test serialization to JSON
        json_str = connection.model_dump_json()

        # Test deserialization from JSON
        loaded_connection = Connection.model_validate_json(json_str)

        # Verify the deserialized object matches the original
        assert loaded_connection.source_activity_name == connection.source_activity_name
        assert loaded_connection.source_output == connection.source_output
        assert loaded_connection.target_activity_name == connection.target_activity_name
        assert loaded_connection.target_input == connection.target_input

    def test_workflow_json_serialization(self):
        """Test Workflow JSON serialization/deserialization."""
        # Create a workflow with activities and connections
        workflow = Workflow()

        # Add activities
        str_len = StringLengthActivity()
        upper = UppercaseActivity()
        workflow.add_activity(str_len.activity_name, str_len)
        workflow.add_activity(upper.activity_name, upper)

        # Add connection
        workflow.connect_activities(
            upper.activity_name, 'uppercase_text',
            str_len.activity_name, 'text'
        )

        # Test serialization to JSON
        json_str = workflow.model_dump_json()

        # Test deserialization from JSON
        data = json.loads(json_str)

        # Reconstruct activities
        loaded_workflow = Workflow()
        for name, activity_data in data['activities'].items():
            if activity_data['activity_name'] == 'string_length':
                activity = StringLengthActivity(activity_name=activity_data['activity_name'])
            else:
                activity = UppercaseActivity(activity_name=activity_data['activity_name'])
            loaded_workflow.add_activity(name, activity)

        # Reconstruct connections
        for conn_data in data['connections']:
            loaded_workflow.connect_activities(
                conn_data['source_activity_name'],
                conn_data['source_output'],
                conn_data['target_activity_name'],
                conn_data['target_input']
            )

        # Verify activities
        assert len(loaded_workflow.activities) == len(workflow.activities)
        for name, activity in workflow.activities.items():
            loaded_activity = loaded_workflow.activities[name]
            assert loaded_activity.activity_name == activity.activity_name
            assert len(loaded_activity.input_params) == len(activity.input_params)
            assert len(loaded_activity.output_params) == len(activity.output_params)

        # Verify connections
        assert len(loaded_workflow.connections) == len(workflow.connections)
        for conn, loaded_conn in zip(workflow.connections, loaded_workflow.connections):
            assert loaded_conn.source_activity_name == conn.source_activity_name
            assert loaded_conn.source_output == conn.source_output
            assert loaded_conn.target_activity_name == conn.target_activity_name
            assert loaded_conn.target_input == conn.target_input

        # Test that the loaded workflow can still execute
        result = loaded_workflow.run({'text': 'hello'})
        assert result['length'] == 5


if __name__ == '__main__':
    pytest.main()
