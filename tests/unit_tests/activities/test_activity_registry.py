import pytest

from src.activities import Parameter
from src.activities.activity_registry import ActivityRegistry
from src.activities.llm_activity import LLMActivity
from tests.shared.activities.examples import StringLengthActivity, CustomParamsActivity


@pytest.fixture(autouse=True)
def setup_registry():
    """Setup clean registry with test activities for each test."""
    # Clear the registry first
    ActivityRegistry.clear()

    # Register test activities using their stored registration info
    ActivityRegistry.register_class(StringLengthActivity)
    ActivityRegistry.register_class(CustomParamsActivity)
    ActivityRegistry.register_class(LLMActivity)

    yield

    # Clear registry after tests
    ActivityRegistry.clear()


def test_fixed_params_activity():
    registry = ActivityRegistry()

    # Get activity type info (already registered via decorator)
    info = registry.get_activity_type("string_length")

    # Verify activity doesn't allow custom params
    assert not info.allow_custom_params

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

    # Get activity type info (already registered via decorator)
    info = registry.get_activity_type("custom_params")

    # Verify activity allows custom params
    assert info.allow_custom_params

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

    # Get activity type info (already registered via decorator)
    info = registry.get_activity_type("llm_activity")

    # Verify parameters are customizable
    assert info.allow_custom_params

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


def test_activity_type_info_serialization():
    """Test ActivityTypeInfo serialization with automatic activity_type exclusion."""
    registry = ActivityRegistry()

    # Get a simple activity type from registry
    info = registry.get_activity_type("llm_activity")

    # Serialize to JSON (activity_type should be automatically excluded)
    json_str = info.model_dump_json()

    print(json_str)
