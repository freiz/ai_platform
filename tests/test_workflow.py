import pytest
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.activity import Activity, ActivityParameter
from src.workflow import Workflow

class StringLengthActivity(Activity):
    def __init__(self, name: str = "string_length"):
        input_params = {
            'text': ActivityParameter(name='text', type="string")
        }
        output_params = {
            'length': ActivityParameter(name='length', type="integer")
        }
        super().__init__(name=name, input_params=input_params, output_params=output_params)
    
    def run(self, text):
        return {'length': len(text)}
    
    def to_str(self) -> str:
        """String representation of StringLengthActivity."""
        return self.name
    
    @classmethod
    def from_str(cls, serialized: str) -> 'Activity':
        """Create instance from string representation."""
        return cls(name=serialized)

class UppercaseActivity(Activity):
    def __init__(self, name: str = "uppercase"):
        input_params = {
            'text': ActivityParameter(name='text', type="string")
        }
        output_params = {
            'uppercase_text': ActivityParameter(name='uppercase_text', type="string")
        }
        super().__init__(name=name, input_params=input_params, output_params=output_params)
    
    def run(self, text):
        return {'uppercase_text': text.upper()}
    
    def to_str(self) -> str:
        """String representation of UppercaseActivity."""
        return self.name
    
    @classmethod
    def from_str(cls, serialized: str) -> 'Activity':
        """Create instance from string representation."""
        return cls(name=serialized)

class TestWorkflow:
    def test_workflow_execution(self):
        # Create activities
        str_len = StringLengthActivity()
        upper = UppercaseActivity()
        
        # Create workflow
        workflow = Workflow()
        workflow.add_activity(str_len.name, str_len)
        workflow.add_activity(upper.name, upper)
        
        # Connect activities
        workflow.connect_activities(upper.name, 'uppercase_text', str_len.name, 'text')
        
        # Set input
        input_data = {'text': 'hello'}
        result = workflow.run(input_data)
        
        assert result['length'] == 5
    
    def test_workflow_serialization(self):
        workflow = Workflow()
        str_len = StringLengthActivity()
        workflow.add_activity(str_len.name, str_len)
        
        serialized = workflow.to_dict()
        assert 'activities' in serialized
        assert len(serialized['activities']) == 1
        assert serialized['activities'][0]['name'] == str_len.name
    
    def test_input_validation(self):
        workflow = Workflow()
        str_len = StringLengthActivity()
        workflow.add_activity(str_len.name, str_len)
        
        with pytest.raises(ValueError):
            workflow.run({})  # Missing required input
        
        with pytest.raises(ValueError):
            workflow.run({'text': 123})  # Wrong type (integer instead of string)

if __name__ == '__main__':
    pytest.main()
