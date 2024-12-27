import pytest

from src.activities.activity import Activity, Parameter
from src.activities.activity_registry import ActivityRegistry
from src.activities.llm_activity import LLMActivity


# Example activity type with fixed parameters
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


# Example activity type with customizable parameters
class CustomParamsActivity(Activity):
    def __init__(self, activity_name: str, input_params: dict, output_params: dict):
        super().__init__(activity_name=activity_name, input_params=input_params, output_params=output_params)

    def run(self, **inputs):
        # Create a greeting using the input name
        return {
            "greeting": f"Hello, {inputs['name']}!"
        }


def test_fixed_params_activity():
    registry = ActivityRegistry()

    # Register activity type with fixed parameters
    registry.register(
        "string_length",
        StringLengthActivity,
        required_params={
            "activity_name": Parameter(name="activity_name", type="string")
        },
        description="Calculates the length of a string",
        # No need to specify fixed params, they'll be taken from the class
        allow_custom_params=False  # This is the default
    )

    # Get activity type info
    activity_types = registry.get_activity_types()
    info = activity_types["string_length"]

    # Verify fixed parameters are exposed
    assert info["input_params"] is not None
    assert "text" in info["input_params"]
    assert info["output_params"] is not None
    assert "length" in info["output_params"]
    assert not info["allow_custom_params"]

    # Create and test instance
    activity = registry.create_activity(
        "string_length",
        {"activity_name": "my_string_length"}
    )
    result = activity(text="hello")
    assert result["length"] == 5

    # Verify we can't override fixed parameters
    with pytest.raises(ValueError, match="does not allow custom input/output parameters"):
        registry.create_activity(
            "string_length",
            {
                "activity_name": "my_string_length",
                "input_params": {"custom": Parameter(name="custom", type="string")}
            }
        )


def test_custom_params_activity():
    registry = ActivityRegistry()

    # Register activity type with customizable parameters
    registry.register(
        "custom_params",
        CustomParamsActivity,
        required_params={
            "activity_name": Parameter(name="activity_name", type="string")
        },
        description="Activity with customizable parameters",
        allow_custom_params=True
    )

    # Get activity type info
    activity_types = registry.get_activity_types()
    info = activity_types["custom_params"]

    # Verify parameters are not fixed
    assert info["input_params"] is None
    assert info["output_params"] is None
    assert info["allow_custom_params"]

    # Create and test instance with custom parameters
    activity = registry.create_activity(
        "custom_params",
        {
            "activity_name": "my_custom_activity",
            "input_params": {
                "name": Parameter(name="name", type="string"),
                "age": Parameter(name="age", type="integer")
            },
            "output_params": {
                "greeting": Parameter(name="greeting", type="string")
            }
        }
    )

    # Test the activity
    result = activity(name="Alice", age=30)
    assert result["greeting"] == "Hello, Alice!"


def test_llm_activity_registration():
    registry = ActivityRegistry()

    # Register LLM activity type with customizable parameters
    registry.register(
        "llm_activity",
        LLMActivity,
        required_params={
            "activity_name": Parameter(name="activity_name", type="string"),
            "system_message": Parameter(name="system_message", type="string"),
            "llm_config": Parameter(name="llm_config", type="object", properties={
                "model_name": Parameter(name="model_name", type="string"),
                "temperature": Parameter(name="temperature", type="number"),
                "top_p": Parameter(name="top_p", type="number")
            })
        },
        description="LLM-based activity with customizable I/O parameters",
        allow_custom_params=True
    )

    # Get activity type info
    activity_types = registry.get_activity_types()
    info = activity_types["llm_activity"]

    # Verify parameters are customizable
    assert info["input_params"] is None
    assert info["output_params"] is None
    assert info["allow_custom_params"]

    # Create an instance (capital finder) using Parameter objects
    activity = registry.create_activity(
        "llm_activity",
        {
            "activity_name": "capital_finder",
            "system_message": "You are a helpful assistant that returns the capital of a country.",
            "llm_config": {
                "model_name": "gpt-4o-mini",
                "temperature": 0.1,
                "top_p": 0.9
            },
            "input_params": {
                "country": Parameter(name="country", type="string")
            },
            "output_params": {
                "capital": Parameter(name="capital", type="string")
            }
        }
    )

    # Verify the activity has the right parameters
    assert "country" in activity.input_params
    assert "capital" in activity.output_params

    # Create an instance using JSON-like dict format
    activity_json = registry.create_activity(
        "llm_activity",
        {
            "activity_name": "capital_finder",
            "system_message": "You are a helpful assistant that returns the capital of a country.",
            "llm_config": {
                "model_name": "gpt-4o-mini",
                "temperature": 0.1,
                "top_p": 0.9
            },
            "input_params": {
                "country": {
                    "name": "country",
                    "type": "string"
                }
            },
            "output_params": {
                "capital": {
                    "name": "capital",
                    "type": "string"
                }
            }
        }
    )

    # Verify the activity created from JSON has the right parameters
    assert "country" in activity_json.input_params
    assert isinstance(activity_json.input_params["country"], Parameter)
    assert "capital" in activity_json.output_params
    assert isinstance(activity_json.output_params["capital"], Parameter)
