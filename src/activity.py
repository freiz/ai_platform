import uuid
from typing import Any, Dict, Optional, Type
from dataclasses import dataclass, field

@dataclass
class ActivityParameter:
    """Represents a parameter for an activity with type and optional default value."""
    name: str
    type: Type
    default: Optional[Any] = None
    required: bool = True

class Activity:
    """
    Base class for creating extensible activities with input and output parameters.
    
    Attributes:
        id (str): Unique identifier for the activity
        input_params (Dict[str, ActivityParameter]): Input parameters for the activity
        output_params (Dict[str, ActivityParameter]): Output parameters for the activity
    """
    
    def __init__(self, 
                 input_params: Optional[Dict[str, ActivityParameter]] = None, 
                 output_params: Optional[Dict[str, ActivityParameter]] = None):
        """
        Initialize an Activity with optional input and output parameters.
        
        Args:
            input_params (Optional[Dict[str, ActivityParameter]]): Input parameters
            output_params (Optional[Dict[str, ActivityParameter]]): Output parameters
        """
        self.id = str(uuid.uuid4())
        self.input_params = input_params or {}
        self.output_params = output_params or {}
        self._validated_inputs = {}
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input parameters against defined input_params.
        
        Args:
            inputs (Dict[str, Any]): Input values to validate
        
        Returns:
            Dict[str, Any]: Validated inputs
        
        Raises:
            ValueError: If input validation fails
        """
        validated_inputs = {}
        
        # Check for missing required inputs
        for param_name, param_def in self.input_params.items():
            if param_name not in inputs:
                if param_def.required:
                    raise ValueError(f"Missing required input parameter: {param_name}")
                elif param_def.default is not None:
                    validated_inputs[param_name] = param_def.default
            else:
                # Type checking
                input_value = inputs[param_name]
                if not isinstance(input_value, param_def.type):
                    try:
                        # Attempt type conversion
                        validated_inputs[param_name] = param_def.type(input_value)
                    except (TypeError, ValueError):
                        raise ValueError(f"Invalid type for parameter {param_name}. "
                                         f"Expected {param_def.type}, got {type(input_value)}")
                else:
                    validated_inputs[param_name] = input_value
        
        self._validated_inputs = validated_inputs
        return validated_inputs
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the activity. To be implemented by subclasses.
        
        Args:
            **kwargs: Input parameters for the activity
        
        Returns:
            Dict[str, Any]: Output of the activity
        """
        raise NotImplementedError("Subclasses must implement the run method")
    
    def __call__(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the activity with input validation.
        
        Args:
            **kwargs: Input parameters for the activity
        
        Returns:
            Dict[str, Any]: Output of the activity
        """
        # Validate inputs before running
        self.validate_inputs(kwargs)
        
        # Execute the activity
        outputs = self.run(**self._validated_inputs)
        
        # Validate outputs
        self._validate_outputs(outputs)
        
        return outputs
    
    def _validate_outputs(self, outputs: Dict[str, Any]) -> None:
        """
        Validate output parameters against defined output_params.
        
        Args:
            outputs (Dict[str, Any]): Outputs to validate
        
        Raises:
            ValueError: If output validation fails
        """
        for param_name, param_def in self.output_params.items():
            if param_name not in outputs:
                if param_def.required:
                    raise ValueError(f"Missing required output parameter: {param_name}")
            else:
                # Type checking
                output_value = outputs[param_name]
                if not isinstance(output_value, param_def.type):
                    raise ValueError(f"Invalid type for output parameter {param_name}. "
                                     f"Expected {param_def.type}, got {type(output_value)}")
