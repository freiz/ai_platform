import uuid
from typing import Any, Dict, Type, Optional
from dataclasses import dataclass

@dataclass
class ActivityParameter:
    """Represents a parameter for an activity with name and type."""
    name: str
    type: Type

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
        
        # Check for missing inputs
        for param_name, param in self.input_params.items():
            if param_name not in inputs:
                raise ValueError(f"Missing required input parameter: {param_name}")
        
        # Validate input types
        for param_name, value in inputs.items():
            if param_name not in self.input_params:
                raise ValueError(f"Unexpected input parameter: {param_name}")
            
            param = self.input_params[param_name]
            if not isinstance(value, param.type):
                raise ValueError(f"Invalid type for {param_name}. Expected {param.type}, got {type(value)}")
            
            validated_inputs[param_name] = value
        
        return validated_inputs
    
    def validate_outputs(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate output values against defined output_params.
        
        Args:
            outputs (Dict[str, Any]): Output values to validate
        
        Returns:
            Dict[str, Any]: Validated outputs
        
        Raises:
            ValueError: If output validation fails
        """
        validated_outputs = {}
        
        # Check for missing outputs
        for param_name in self.output_params:
            if param_name not in outputs:
                raise ValueError(f"Missing output parameter: {param_name}")
        
        # Validate output types
        for param_name, value in outputs.items():
            if param_name not in self.output_params:
                raise ValueError(f"Unexpected output parameter: {param_name}")
            
            param = self.output_params[param_name]
            if not isinstance(value, param.type):
                raise ValueError(f"Invalid type for {param_name}. Expected {param.type}, got {type(value)}")
            
            validated_outputs[param_name] = value
        
        return validated_outputs
    
    def __call__(self, **inputs: Any) -> Dict[str, Any]:
        """
        Execute the activity with the given inputs.
        
        Args:
            **inputs: Input values for the activity
        
        Returns:
            Dict[str, Any]: Output values from the activity
        """
        validated_inputs = self.validate_inputs(inputs)
        outputs = self.run(**validated_inputs)
        return self.validate_outputs(outputs)
    
    def run(self, **inputs: Any) -> Dict[str, Any]:
        """
        Run the activity with validated inputs.
        
        Args:
            **inputs: Validated input values
        
        Returns:
            Dict[str, Any]: Output values
        
        Raises:
            NotImplementedError: If the activity doesn't implement this method
        """
        raise NotImplementedError("Activity must implement run method")
