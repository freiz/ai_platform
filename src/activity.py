import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Literal, Union, get_args
from pydantic import BaseModel, Field

# Define valid parameter types that map to JSON types
ParamType = Literal["string", "number", "integer", "boolean", "array", "object"]

class ActivityParameter(BaseModel):
    """
    Represents a parameter for an activity with name and JSON-compatible type.
    
    Attributes:
        name: Parameter name
        type: JSON-schema type ("string", "number", "integer", "boolean", "array", "object")
    """
    name: str
    type: ParamType
    
    @property
    def python_type(self) -> type:
        """Convert JSON-schema type to Python type."""
        type_mapping = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        return type_mapping[self.type]
    
    def validate_value(self, value: Any) -> bool:
        """Validate if a value matches the parameter type."""
        if self.type == "number":
            return isinstance(value, (int, float))
        elif self.type == "integer":
            return isinstance(value, int)
        else:
            return isinstance(value, self.python_type)

class Activity(BaseModel, ABC):
    """
    Abstract base class for creating extensible activities with input and output parameters.
    
    Attributes:
        name (str): Name of the activity
        input_params (Dict[str, ActivityParameter]): Input parameters for the activity
        output_params (Dict[str, ActivityParameter]): Output parameters for the activity
    """
    name: str = Field(alias="_name")
    input_params: Dict[str, ActivityParameter] = Field(default_factory=dict)
    output_params: Dict[str, ActivityParameter] = Field(default_factory=dict)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
    
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