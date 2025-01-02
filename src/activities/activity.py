from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Literal, ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# Define valid parameter types that map to JSON types
ParamType = Literal["string", "number", "integer", "boolean", "array", "object"]


class Parameter(BaseModel):
    """
    Represents a parameter for an activity with name and JSON-compatible type.
    
    Attributes:
        name: Parameter name
        type: JSON-schema type ("string", "number", "integer", "boolean", "array", "object")
        items: For array type, specifies the type of array items
        properties: For object type, specifies the structure of object properties
    """
    model_config = {
        "exclude_none": True
    }

    name: str
    type: ParamType
    items: Optional['Parameter'] = None  # Type of array items
    properties: Optional[Dict[str, 'Parameter']] = None  # Object structure

    @property
    def python_type(self) -> Any:
        """Convert JSON-schema type to Python type."""
        type_mapping = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": (dict, BaseModel)  # Allow both dict and Pydantic models
        }
        return type_mapping[self.type]

    def validate_value(self, value: Any) -> bool:
        """Validate if a value matches the parameter type."""
        # For object type, allow both dict and Pydantic models
        if self.type == "object":
            if isinstance(value, BaseModel):
                # Convert Pydantic model to dict for validation
                value = value.model_dump()
            elif not isinstance(value, dict):
                return False

        # For non-object types, check against python_type
        elif not isinstance(value, self.python_type):
            if not (self.type == "number" and isinstance(value, (int, float))):
                return False

        # Validate array items
        if self.type == "array" and self.items is not None:
            return all(self.items.validate_value(item) for item in value)

        # Validate object properties
        if self.type == "object" and self.properties is not None:
            return all(
                prop_name in self.properties and
                self.properties[prop_name].validate_value(value[prop_name])
                for prop_name in self.properties
            )

        return True


class Activity(BaseModel, ABC):
    """
    Abstract base class for creating extensible activities with input and output parameters.
    
    Attributes:
        id (UUID): Unique identifier for the activity instance
        activity_name (str): Name of the activity
        input_params (Dict[str, Parameter]): Input parameters for the activity
        output_params (Dict[str, Parameter]): Output parameters for the activity
    """
    id: UUID = Field(default_factory=uuid4)
    activity_name: str
    # noinspection PyDataclass
    input_params: Dict[str, Parameter] = Field(default_factory=dict)
    # noinspection PyDataclass
    output_params: Dict[str, Parameter] = Field(default_factory=dict)

    # Class-level parameter definitions for fixed parameter activities
    fixed_input_params: ClassVar[Dict[str, Parameter]] = {}
    fixed_output_params: ClassVar[Dict[str, Parameter]] = {}

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, activity_name: str, input_params: Optional[Dict[str, Parameter]] = None, 
                 output_params: Optional[Dict[str, Parameter]] = None, **kwargs):
        """
        Initialize an activity with its parameters.
        For fixed parameter activities (allow_custom_params=False), parameters are taken from class-level definitions.
        For customizable activities (allow_custom_params=True), parameters are passed through constructor.
        """
        # Get parameters from class-level definitions if not provided
        if input_params is None and self.fixed_input_params:
            input_params = self.fixed_input_params
        if output_params is None and self.fixed_output_params:
            output_params = self.fixed_output_params

        super().__init__(
            activity_name=activity_name,
            input_params=input_params or {},
            output_params=output_params or {},
            **kwargs
        )

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
