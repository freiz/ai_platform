import pytest

from src.activities.activity import Parameter
from src.activities.activity_registry import ActivityRegistry
from src.activities.identity_activity import IdentityActivity


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for all tests in this file."""
    # Clear registry before tests
    ActivityRegistry.clear()
    # Register the activity for our tests
    ActivityRegistry.register_class(IdentityActivity)

    yield

    # Clear registry after tests
    ActivityRegistry.clear()


def test_create_identity_activity_valid():
    # Create activity through registry with matching input/output params
    activity = ActivityRegistry.create_activity(
        activity_type_name="identity_activity",
        params={
            "activity_name": "test_identity",
            "input_params": {
                "field1": Parameter(name="field1", type="string"),
                "field2": Parameter(name="field2", type="number")
            },
            "output_params": {
                "field1": Parameter(name="field1", type="string"),
                "field2": Parameter(name="field2", type="number")
            }
        }
    )

    # Verify activity was created successfully
    assert isinstance(activity, IdentityActivity)
    assert activity.activity_name == "test_identity"

    # Test running the activity
    result = activity(field1="test", field2=42.0)
    assert result == {"field1": "test", "field2": 42.0}


def test_create_identity_activity_mismatched_params():
    # Try to create activity with mismatched input/output params
    with pytest.raises(ValueError, match="Input and output parameters must have identical structure"):
        ActivityRegistry.create_activity(
            activity_type_name="identity_activity",
            params={
                "activity_name": "test_identity",
                "input_params": {
                    "field1": Parameter(name="field1", type="string")
                },
                "output_params": {
                    "field2": Parameter(name="field2", type="number")
                }
            }
        )


def test_identity_activity_validation():
    # Create valid activity
    activity = ActivityRegistry.create_activity(
        activity_type_name="identity_activity",
        params={
            "activity_name": "test_identity",
            "input_params": {
                "field1": Parameter(name="field1", type="string")
            },
            "output_params": {
                "field1": Parameter(name="field1", type="string")
            }
        }
    )

    # Test with valid input
    result = activity(field1="test")
    assert result == {"field1": "test"}

    # Test with invalid input type
    with pytest.raises(ValueError, match="Invalid type for field1"):
        activity(field1=123)

    # Test with missing input
    with pytest.raises(ValueError, match="Missing required input parameter"):
        activity()

    # Test with extra input
    with pytest.raises(ValueError, match="Unexpected input parameter"):
        activity(field1="test", extra="value")


def test_identity_activity_complex_params():
    # Create activity with nested object parameters
    activity = ActivityRegistry.create_activity(
        activity_type_name="identity_activity",
        params={
            "activity_name": "test_identity",
            "input_params": {
                "obj": Parameter(
                    name="obj",
                    type="object",
                    properties={
                        "nested": Parameter(name="nested", type="string")
                    }
                ),
                "arr": Parameter(
                    name="arr",
                    type="array",
                    items=Parameter(name="items", type="number")
                )
            },
            "output_params": {
                "obj": Parameter(
                    name="obj",
                    type="object",
                    properties={
                        "nested": Parameter(name="nested", type="string")
                    }
                ),
                "arr": Parameter(
                    name="arr",
                    type="array",
                    items=Parameter(name="items", type="number")
                )
            }
        }
    )

    # Test with valid complex input
    result = activity(
        obj={"nested": "test"},
        arr=[1.0, 2.0, 3.0]
    )
    assert result == {
        "obj": {"nested": "test"},
        "arr": [1.0, 2.0, 3.0]
    }


def test_identity_activity_run():
    """Test that IdentityActivity.run() correctly passes through inputs."""
    # Create activity with various parameter types
    activity = ActivityRegistry.create_activity(
        activity_type_name="identity_activity",
        params={
            "activity_name": "test_identity",
            "input_params": {
                "string_val": Parameter(name="string_val", type="string"),
                "number_val": Parameter(name="number_val", type="number"),
                "integer_val": Parameter(name="integer_val", type="integer"),
                "boolean_val": Parameter(name="boolean_val", type="boolean"),
                "array_val": Parameter(
                    name="array_val",
                    type="array",
                    items=Parameter(name="items", type="string")
                ),
                "object_val": Parameter(
                    name="object_val",
                    type="object",
                    properties={
                        "nested": Parameter(name="nested", type="string")
                    }
                )
            },
            "output_params": {
                "string_val": Parameter(name="string_val", type="string"),
                "number_val": Parameter(name="number_val", type="number"),
                "integer_val": Parameter(name="integer_val", type="integer"),
                "boolean_val": Parameter(name="boolean_val", type="boolean"),
                "array_val": Parameter(
                    name="array_val",
                    type="array",
                    items=Parameter(name="items", type="string")
                ),
                "object_val": Parameter(
                    name="object_val",
                    type="object",
                    properties={
                        "nested": Parameter(name="nested", type="string")
                    }
                )
            }
        }
    )

    # Test inputs with various types
    test_inputs = {
        "string_val": "test",
        "number_val": 42.5,
        "integer_val": 42,
        "boolean_val": True,
        "array_val": ["a", "b", "c"],
        "object_val": {"nested": "value"}
    }

    # Run the activity
    result = activity(**test_inputs)

    # Verify that outputs exactly match inputs
    assert result == test_inputs
    
    # Test each value individually to ensure types are preserved
    assert isinstance(result["string_val"], str)
    assert isinstance(result["number_val"], float)
    assert isinstance(result["integer_val"], int)
    assert isinstance(result["boolean_val"], bool)
    assert isinstance(result["array_val"], list)
    assert isinstance(result["object_val"], dict)
