import pytest
from pydantic import ValidationError
from src.activities import Activity, Parameter, ParamType
from typing import Any, Dict, get_args


class SampleActivity(Activity):
    """A concrete implementation of Activity for testing."""

    def __init__(self):
        input_params = {
            "text": Parameter(name="text", type="string"),
            "count": Parameter(name="count", type="integer")
        }
        output_params = {
            "result": Parameter(name="result", type="string")
        }
        super().__init__(activity_name="sample_activity", input_params=input_params, output_params=output_params)

    def run(self, **inputs: Any) -> Dict[str, Any]:
        text = inputs["text"]
        count = inputs["count"]
        return {"result": text * count}


@pytest.fixture
def sample_activity():
    return SampleActivity()


class TestActivity(Activity):
    """A concrete Activity implementation for testing."""

    def run(self, **inputs: Any) -> Dict[str, Any]:
        return {"result": "test"}


def test_param_type_validation():
    """Test Parameter type validation."""
    param = Parameter(name="test", type="string")
    assert param.python_type == str
    assert param.type == "string"

    # Test number type
    number_param = Parameter(name="test", type="number")
    assert number_param.python_type == float
    assert number_param.type == "number"


def test_invalid_param_type():
    """Test creating Parameter with invalid type."""
    with pytest.raises(ValidationError):
        # noinspection PyTypeChecker
        Parameter(name="test", type="invalid_type")


def test_valid_param_types():
    """Test all valid parameter types."""
    valid_types = get_args(ParamType)
    for valid_type in valid_types:
        # noinspection PyBroadException
        try:
            Parameter(name="test", type=valid_type)
        except Exception:
            pytest.fail(f"Failed to create Parameter with valid type: {valid_type}")


def test_activity_creation():
    """Test creating an activity with parameters."""
    activity = TestActivity.model_validate({
        "activity_name": "test_activity",
        "input_params": {
            "text": Parameter(name="text", type="string")
        },
        "output_params": {
            "result": Parameter(name="result", type="string")
        }
    })

    assert activity.activity_name == "test_activity"
    assert isinstance(activity.input_params["text"], Parameter)
    assert isinstance(activity.output_params["result"], Parameter)


def test_parameter_serialization():
    """Test Parameter JSON serialization/deserialization."""
    param = Parameter(name="test_param", type="string")
    json_str = param.model_dump_json()

    # Test that we can deserialize the JSON back into a Parameter
    loaded_param = Parameter.model_validate_json(json_str)
    assert param.name == loaded_param.name
    assert param.type == loaded_param.type

    # Test all parameter types
    for param_type in get_args(ParamType):
        param = Parameter(name=f"test_{param_type}", type=param_type)
        json_str = param.model_dump_json()
        loaded_param = Parameter.model_validate_json(json_str)
        assert param.type == loaded_param.type


def test_activity_validation(sample_activity):
    """Test activity input/output validation."""
    # Test valid inputs
    inputs = {"text": "hello", "count": 3}
    validated_inputs = sample_activity.validate_inputs(inputs)
    assert validated_inputs == inputs

    # Test invalid input type
    with pytest.raises(ValueError):
        sample_activity.validate_inputs({"text": "hello", "count": "3"})  # count should be int

    # Test missing input
    with pytest.raises(ValueError):
        sample_activity.validate_inputs({"text": "hello"})  # missing count

    # Test output validation
    outputs = {"result": "hello hello hello"}
    validated_outputs = sample_activity.validate_outputs(outputs)
    assert validated_outputs == outputs


def test_array_parameter():
    """Test array parameter type with item definitions."""
    # Test string array
    string_list_param = Parameter(
        name="string_list",
        type="array",
        items=Parameter(name="item", type="string")
    )
    assert string_list_param.type == "array"
    assert isinstance(string_list_param.items, Parameter)
    assert string_list_param.items.type == "string"

    # Test integer array
    int_list_param = Parameter(
        name="int_list",
        type="array",
        items=Parameter(name="item", type="integer")
    )
    assert int_list_param.items.type == "integer"


def test_object_parameter():
    """Test object parameter type with property definitions."""
    person_param = Parameter(
        name="person",
        type="object",
        properties={
            "name": Parameter(name="name", type="string"),
            "age": Parameter(name="age", type="integer"),
            "scores": Parameter(
                name="scores",
                type="array",
                items=Parameter(name="score", type="number")
            )
        }
    )

    assert person_param.type == "object"
    assert isinstance(person_param.properties, dict)
    assert person_param.properties["name"].type == "string"
    assert person_param.properties["age"].type == "integer"
    assert person_param.properties["scores"].type == "array"
    assert person_param.properties["scores"].items.type == "number"

    # Test nested object serialization
    json_str = person_param.model_dump_json()
    loaded_param = Parameter.model_validate_json(json_str)
    assert loaded_param.properties["name"].type == "string"
    assert loaded_param.properties["scores"].items.type == "number"


def test_nested_object_array():
    """Test nested object within array parameter."""
    original_param = Parameter(
        name="friends_list",
        type="array",
        items=Parameter(
            name="friend",
            type="object",
            properties={
                "name": Parameter(name="name", type="string"),
                "age": Parameter(name="age", type="integer")
            }
        )
    )

    json_str = original_param.model_dump_json()
    loaded_param = Parameter.model_validate_json(json_str)

    assert loaded_param.type == "array"
    assert loaded_param.items.type == "object"
    assert loaded_param.items.properties["name"].type == "string"
    assert loaded_param.items.properties["age"].type == "integer"


def test_activity_execution(sample_activity):
    """Test activity execution with input validation."""
    # Test valid execution
    result = sample_activity(text="hello", count=3)
    assert result["result"] == "hellohellohello"

    # Test execution with invalid input
    with pytest.raises(ValueError):
        sample_activity(text="hello", count="3")  # count should be int

    # Test execution with missing input
    with pytest.raises(ValueError):
        sample_activity(text="hello")  # missing count


def test_complex_activity():
    """Test activity with complex nested parameters."""

    class ComplexActivity(Activity):
        def __init__(self):
            input_params = {
                "users": Parameter(
                    name="users",
                    type="array",
                    items=Parameter(
                        name="user",
                        type="object",
                        properties={
                            "name": Parameter(name="name", type="string"),
                            "age": Parameter(name="age", type="integer")
                        }
                    )
                )
            }
            output_params = {
                "summary": Parameter(
                    name="summary",
                    type="object",
                    properties={
                        "count": Parameter(name="count", type="integer"),
                        "names": Parameter(
                            name="names",
                            type="array",
                            items=Parameter(name="name", type="string")
                        )
                    }
                )
            }
            super().__init__(
                activity_name="complex_activity",
                input_params=input_params,
                output_params=output_params
            )

        def run(self, **inputs: Any) -> Dict[str, Any]:
            users = inputs["users"]
            return {
                "summary": {
                    "count": len(users),
                    "names": [user["name"] for user in users]
                }
            }

    activity = ComplexActivity()

    # Test with valid input
    result = activity(users=[
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ])

    assert result["summary"]["count"] == 2
    assert result["summary"]["names"] == ["Alice", "Bob"]

    # Test with invalid input
    with pytest.raises(ValueError):
        activity(users=[
            {"name": "Alice", "age": "30"},  # age should be int
            {"name": "Bob", "age": 25}
        ])


def test_complex_parameter_validation():
    """Test validation of complex parameter types (arrays and objects)."""
    # Test list of strings
    string_list_param = Parameter(
        name="string_list",
        type="array",
        items=Parameter(name="item", type="string")
    )

    # Valid cases
    assert string_list_param.validate_value(["a", "b", "c"])
    assert not string_list_param.validate_value([1, 2, 3])  # Wrong item type
    assert not string_list_param.validate_value("not_a_list")  # Not a list

    # Test list of integers
    int_list_param = Parameter(
        name="int_list",
        type="array",
        items=Parameter(name="item", type="integer")
    )

    assert int_list_param.validate_value([1, 2, 3])
    assert not int_list_param.validate_value([1.1, 2.2, 3.3])  # Wrong item type
    assert not int_list_param.validate_value(["1", "2", "3"])  # Wrong item type

    # Test nested object
    person_param = Parameter(
        name="person",
        type="object",
        properties={
            "name": Parameter(name="name", type="string"),
            "age": Parameter(name="age", type="integer"),
            "scores": Parameter(
                name="scores",
                type="array",
                items=Parameter(name="score", type="number")
            )
        }
    )

    # Valid case
    valid_person = {
        "name": "John",
        "age": 30,
        "scores": [85.5, 92.0, 88.5]
    }
    assert person_param.validate_value(valid_person)

    # Invalid cases
    invalid_person1 = {
        "name": 123,  # Wrong type for name
        "age": 30,
        "scores": [85.5, 92.0, 88.5]
    }
    assert not person_param.validate_value(invalid_person1)

    invalid_person2 = {
        "name": "John",
        "age": "30",  # Wrong type for age
        "scores": [85.5, 92.0, 88.5]
    }
    assert not person_param.validate_value(invalid_person2)

    invalid_person3 = {
        "name": "John",
        "age": 30,
        "scores": ["85.5", "92.0", "88.5"]  # Wrong type for scores
    }
    assert not person_param.validate_value(invalid_person3)


def test_complex_parameter_serialization():
    """Test serialization and deserialization of complex parameter types."""
    # Create a complex parameter with nested types
    original_param = Parameter(
        name="user_data",
        type="object",
        properties={
            "name": Parameter(name="name", type="string"),
            "friends": Parameter(
                name="friends",
                type="array",
                items=Parameter(
                    name="friend",
                    type="object",
                    properties={
                        "name": Parameter(name="name", type="string"),
                        "age": Parameter(name="age", type="integer")
                    }
                )
            )
        }
    )

    # Serialize to JSON
    json_str = original_param.model_dump_json()

    # Deserialize from JSON
    loaded_param = Parameter.model_validate_json(json_str)

    # Verify structure is preserved
    assert loaded_param.name == "user_data"
    assert loaded_param.type == "object"
    assert loaded_param.properties["name"].type == "string"
    assert loaded_param.properties["friends"].type == "array"
    assert loaded_param.properties["friends"].items.type == "object"
    assert loaded_param.properties["friends"].items.properties["name"].type == "string"
    assert loaded_param.properties["friends"].items.properties["age"].type == "integer"

    # Test validation with the loaded parameter
    valid_data = {
        "name": "John",
        "friends": [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30}
        ]
    }
    assert loaded_param.validate_value(valid_data)

    invalid_data = {
        "name": "John",
        "friends": [
            {"name": "Alice", "age": "25"},  # Wrong type for age
            {"name": "Bob", "age": 30}
        ]
    }
    assert not loaded_param.validate_value(invalid_data)
