from typing import Dict, Type, Any, Optional

from pydantic import BaseModel, Field

from src.activities.activity import Activity, Parameter


class ActivityTypeInfo(BaseModel):
    """
    Information about an activity type that can be used to create instances.
    
    Attributes:
        activity_type_name: The unique name of this activity type
        activity_type: The actual activity class
        required_params: Additional parameters required to instantiate the activity
        description: Human-readable description of what the activity does
        allow_custom_params: If True, input/output params can be defined per instance
    """
    model_config = {
        'arbitrary_types_allowed': True,
    }

    activity_type_name: str
    activity_type: Type[Activity] = Field(exclude=True)
    required_params: Dict[str, Parameter]
    description: str
    allow_custom_params: bool = False


class ActivityRegistry:
    """
    Registry for activity types that can be instantiated.
    Follows the singleton pattern to ensure only one registry exists.
    """
    _instance = None
    _registry: Dict[str, ActivityTypeInfo] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActivityRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def clear(cls):
        """Clear all registered activities. Should only be used in tests."""
        cls._registry.clear()

    @staticmethod
    def _convert_to_parameter(value: Any) -> Parameter:
        """Convert a value to a Parameter if it's not already one."""
        if isinstance(value, Parameter):
            return value
        if isinstance(value, dict):
            return Parameter.model_validate(value)
        raise ValueError(f"Cannot convert {type(value)} to Parameter")

    @staticmethod
    def _convert_params_dict(params: Dict[str, Any]) -> Dict[str, Parameter]:
        """Convert a dictionary of parameters to use Parameter objects."""
        return {
            k: ActivityRegistry._convert_to_parameter(v)
            for k, v in params.items()
        }

    @classmethod
    def register(cls,
                 activity_name: str,
                 activity_type: Type[Activity],
                 required_params: Dict[str, Parameter],
                 description: str,
                 allow_custom_params: bool = False) -> None:
        """
        Register a new activity type.
        
        Args:
            activity_name: Unique name for the activity type
            activity_type: The activity class
            required_params: Parameters required to instantiate the activity
            description: Human-readable description of the activity
            allow_custom_params: If True, input/output params can be defined per instance
        """
        if activity_name in cls._registry:
            raise ValueError(f"Activity type {activity_name} already registered")

        cls._registry[activity_name] = ActivityTypeInfo(
            activity_type_name=activity_name,
            activity_type=activity_type,
            required_params=required_params,
            description=description,
            allow_custom_params=allow_custom_params
        )

    @classmethod
    def create_activity(cls,
                        activity_type_name: str,
                        params: Dict[str, Any]) -> Activity:
        """
        Create an instance of a registered activity type.
        
        Args:
            activity_type_name: Name of the registered activity type
            params: Parameters required to instantiate the activity
            
        Returns:
            An instance of the requested activity type
            
        Raises:
            ValueError: If activity type not found or params are invalid
        """
        if activity_type_name not in cls._registry:
            raise ValueError(f"Activity type {activity_type_name} not found")

        info = cls._registry[activity_type_name]

        # Convert input_params and output_params to Parameter objects if they exist
        if "input_params" in params:
            params = {**params, "input_params": cls._convert_params_dict(params["input_params"])}
        if "output_params" in params:
            params = {**params, "output_params": cls._convert_params_dict(params["output_params"])}

        # Validate required params
        for param_name, param in info.required_params.items():
            if param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")
            if not param.validate_value(params[param_name]):
                raise ValueError(
                    f"Invalid value for {param_name}. "
                    f"Expected {param.type}, got {type(params[param_name]).__name__}"
                )

        # If custom params aren't allowed, ensure no input/output params are provided
        if not info.allow_custom_params:
            if any(key in params for key in ['input_params', 'output_params']):
                raise ValueError(
                    f"Activity type {activity_type_name} does not allow custom input/output parameters"
                )
            # For fixed parameter activities, don't pass input/output params to constructor
            creation_params = {k: v for k, v in params.items()
                               if k not in ['input_params', 'output_params']}
            return info.activity_type(**creation_params)

        # For customizable parameter activities, pass all params
        return info.activity_type(**params)

    @classmethod
    def get_activity_types(cls) -> Dict[str, ActivityTypeInfo]:
        """
        Get all registered activity types and their metadata.
        Used by the API to expose available activity types.
        
        Returns:
            Dictionary mapping activity type names to their ActivityTypeInfo objects
        """
        return cls._registry

    @classmethod
    def get_activity_type(cls, activity_type_name: str) -> ActivityTypeInfo:
        """
        Get activity type info for a specific activity type.
        
        Args:
            activity_type_name: Name of the registered activity type
            
        Returns:
            ActivityTypeInfo for the requested activity type
            
        Raises:
            ValueError: If activity type not found
        """
        if activity_type_name not in cls._registry:
            raise ValueError(f"Activity type {activity_type_name} not found")
        return cls._registry[activity_type_name]

    @classmethod
    def get_activity_class(cls, activity_type_name: str) -> Type[Activity]:
        """
        Get the activity class for a specific activity type.
        
        Args:
            activity_type_name: Name of the registered activity type
            
        Returns:
            The activity class
            
        Raises:
            ValueError: If activity type not found
        """
        if activity_type_name not in cls._registry:
            raise ValueError(f"Activity type {activity_type_name} not found")
        return cls._registry[activity_type_name].activity_type

    @classmethod
    def register_activity(cls,
                          activity_type_name: str,
                          description: str,
                          required_params: Optional[Dict[str, Parameter]] = None,
                          allow_custom_params: bool = False):
        """
        Class decorator for registering activities.
        
        Args:
            activity_type_name: Unique name for the activity type (class-level constant)
            description: Human-readable description of what the activity does
            required_params: Additional parameters required to instantiate the activity
            allow_custom_params: If True, input/output params can be defined per instance
            
        Returns:
            The decorated activity class
        """

        def decorator(activity_cls: Type[Activity]):
            # Store registration info on the class itself
            activity_cls._registration_info = {
                "activity_type_name": activity_type_name,
                "description": description,
                "required_params": required_params or {
                    "activity_name": Parameter(name="activity_name", type="string")
                },
                "allow_custom_params": allow_custom_params
            }
            return activity_cls

        return decorator

    @classmethod
    def register_class(cls, activity_cls: Type[Activity]):
        """Register an activity class using its stored registration info."""
        if not hasattr(activity_cls, '_registration_info'):
            raise ValueError(
                f"Class {activity_cls.__name__} has no registration info. Did you forget the @register_activity decorator?"
            )

        info = activity_cls._registration_info
        cls.register(
            activity_name=info["activity_type_name"],
            activity_type=activity_cls,
            required_params=info["required_params"],
            description=info["description"],
            allow_custom_params=info["allow_custom_params"]
        )
