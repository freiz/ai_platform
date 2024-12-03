import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Literal, Union, get_args
from dataclasses import dataclass

# Define valid parameter types that map to JSON types
ParamType = Literal["string", "number", "integer", "boolean", "array", "object"]

@dataclass
class ActivityParameter:
    """
    Represents a parameter for an activity with name and JSON-compatible type.
    
    Attributes:
        name: Parameter name
        type: JSON-schema type ("string", "number", "integer", "boolean", "array", "object")
    """
    name: str
    type: ParamType
    
    def __post_init__(self):
        """Validate type after initialization."""
        valid_types = set(get_args(ParamType))  # Using get_args is more explicit than __args__
        if self.type not in valid_types:
            raise ValueError(f"Invalid type '{self.type}'. Must be one of: {', '.join(sorted(valid_types))}")
    
    @staticmethod
    def get_python_type(param_type: ParamType) -> type:
        """Convert JSON-schema type to Python type."""
        type_mapping = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        return type_mapping[param_type]
    
    def validate_value(self, value: Any) -> bool:
        """Validate if a value matches the parameter type."""
        python_type = self.get_python_type(self.type)
        
        if self.type == "number":
            return isinstance(value, (int, float))
        elif self.type == "integer":
            return isinstance(value, int)
        else:
            return isinstance(value, python_type)

class Activity(ABC):
    """
    Abstract base class for creating extensible activities with input and output parameters.
    
    Attributes:
        name (str): Name of the activity
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
        self.input_params = input_params or {}
        self.output_params = output_params or {}
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Abstract property that must return the activity name."""
        pass
    
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
            if not param.validate_value(value):
                raise ValueError(
                    f"Invalid type for {param_name}. "
                    f"Expected {param.type}, got {type(value).__name__}"
                )
            
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
            if not param.validate_value(value):
                raise ValueError(
                    f"Invalid type for {param_name}. "
                    f"Expected {param.type}, got {type(value).__name__}"
                )
            
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
    
    @abstractmethod
    def run(self, **inputs: Any) -> Dict[str, Any]:
        """
        Run the activity with validated inputs.
        
        Args:
            **inputs: Validated input values
        
        Returns:
            Dict[str, Any]: Output values
        """
        pass
    
    @abstractmethod
    def to_str(self) -> str:
        """
        Serialize the activity instance to a string representation.
        
        This method should serialize all necessary state to recreate the activity,
        including any custom attributes beyond the basic input/output parameters.
        
        Returns:
            str: String representation of the activity
        """
    
    @classmethod
    @abstractmethod
    def from_str(cls, serialized: str) -> 'Activity':
        """
        Create an activity instance from its string representation.
        
        This method should handle deserialization of all state that was serialized
        by to_str, including any custom attributes.
        
        Args:
            serialized (str): String representation from to_str
            
        Returns:
            Activity: A new instance of the activity
            
        Raises:
            ValueError: If the string representation is invalid
        """
