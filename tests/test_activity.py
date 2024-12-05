import unittest
from pydantic import ValidationError
from src.activities import Activity, Parameter, ParamType
from typing import Any, Dict

class SampleActivity(Activity):
    """A concrete implementation of Activity for testing."""
    def __init__(self):
        super().__init__()
        self.activity_name = "sample_activity"
        self.input_params = {
            "text": Parameter(name="text", type="string"),
            "count": Parameter(name="count", type="integer")
        }
        self.output_params = {
            "result": Parameter(name="result", type="string")
        }

    def run(self, **inputs: Any) -> Dict[str, Any]:
        text = inputs["text"]
        count = inputs["count"]
        return {"result": text * count}


class TestActivity(unittest.TestCase):
    """Test cases for Activity class and its components."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.input_params = {
            "text": Parameter(name="text", type="string"),
            "count": Parameter(name="count", type="integer")
        }
        self.output_params = {
            "result": Parameter(name="result", type="string")
        }
        self.activity = SampleActivity()
        self.activity.input_params = self.input_params
        self.activity.output_params = self.output_params

    def test_param_type_validation(self):
        """Test Parameter type validation."""
        param = Parameter(name="test", type="string")
        self.assertEqual(param.python_type, str)
        self.assertEqual(param.type, "string")

        # Test number type
        number_param = Parameter(name="test", type="number")
        self.assertEqual(number_param.python_type, float)
        self.assertEqual(number_param.type, "number")

    def test_invalid_param_type(self):
        """Test creating Parameter with invalid type."""
        with self.assertRaises(ValidationError):
            Parameter(name="test", type="invalid_type")

    def test_valid_param_types(self):
        """Test all valid parameter types."""
        valid_types = get_args(ParamType)
        for valid_type in valid_types:
            try:
                Parameter(name="test", type=valid_type)
            except Exception as e:
                self.fail(f"Failed to create Parameter with valid type: {valid_type}")

    def test_activity_creation(self):
        """Test creating an activity with parameters."""
        activity = Activity()
        activity.activity_name = "test_activity"
        activity.input_params = {
            "text": Parameter(name="text", type="string")
        }
        activity.output_params = {
            "result": Parameter(name="result", type="string")
        }

        self.assertEqual(activity.activity_name, "test_activity")
        self.assertIsInstance(activity.input_params["text"], Parameter)
        self.assertIsInstance(activity.output_params["result"], Parameter)

    def test_parameter_serialization(self):
        """Test Parameter JSON serialization/deserialization."""
        param = Parameter(name="test_param", type="string")
        json_str = param.model_dump_json()
        
        # Test that we can deserialize the JSON back into a Parameter
        loaded_param = Parameter.model_validate_json(json_str)
        self.assertEqual(param.name, loaded_param.name)
        self.assertEqual(param.type, loaded_param.type)

        # Test all parameter types
        for param_type in get_args(ParamType):
            param = Parameter(name=f"test_{param_type}", type=param_type)
            json_str = param.model_dump_json()
            loaded_param = Parameter.model_validate_json(json_str)
            self.assertEqual(param.type, loaded_param.type)

    def test_activity_validation(self):
        """Test activity input/output validation."""
        # Test valid inputs
        inputs = {"text": "hello", "count": 3}
        validated_inputs = self.activity.validate_inputs(inputs)
        self.assertEqual(validated_inputs, inputs)

        # Test invalid input type
        with self.assertRaises(ValueError):
            self.activity.validate_inputs({"text": "hello", "count": "3"})  # count should be int

        # Test missing input
        with self.assertRaises(ValueError):
            self.activity.validate_inputs({"text": "hello"})  # missing count

        # Test output validation
        outputs = {"result": "hello hello hello"}
        validated_outputs = self.activity.validate_outputs(outputs)
        self.assertEqual(validated_outputs, outputs)

    def test_array_parameter(self):
        """Test array parameter type with item definitions."""
        # Test string array
        string_list_param = Parameter(
            name="string_list",
            type="array",
            items=Parameter(name="item", type="string")
        )
        self.assertEqual(string_list_param.type, "array")
        self.assertIsInstance(string_list_param.items, Parameter)
        self.assertEqual(string_list_param.items.type, "string")

        # Test integer array
        int_list_param = Parameter(
            name="int_list",
            type="array",
            items=Parameter(name="item", type="integer")
        )
        self.assertEqual(int_list_param.items.type, "integer")

    def test_object_parameter(self):
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

        self.assertEqual(person_param.type, "object")
        self.assertIsInstance(person_param.properties, dict)
        self.assertEqual(person_param.properties["name"].type, "string")
        self.assertEqual(person_param.properties["age"].type, "integer")
        self.assertEqual(person_param.properties["scores"].type, "array")
        self.assertEqual(person_param.properties["scores"].items.type, "number")

        # Test nested object serialization
        json_str = person_param.model_dump_json()
        loaded_param = Parameter.model_validate_json(json_str)
        self.assertEqual(loaded_param.properties["name"].type, "string")
        self.assertEqual(loaded_param.properties["scores"].items.type, "number")

    def test_nested_object_array(self):
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

        self.assertEqual(loaded_param.type, "array")
        self.assertEqual(loaded_param.items.type, "object")
        self.assertEqual(loaded_param.items.properties["name"].type, "string")
        self.assertEqual(loaded_param.items.properties["age"].type, "integer")

    def test_activity_execution(self):
        """Test activity execution with input validation."""
        # Test valid execution
        result = self.activity(text="hello", count=3)
        self.assertEqual(result["result"], "hellohellohello")

        # Test execution with invalid input
        with self.assertRaises(ValueError):
            self.activity(text="hello", count="3")  # count should be int

        # Test execution with missing input
        with self.assertRaises(ValueError):
            self.activity(text="hello")  # missing count

    def test_complex_activity(self):
        """Test activity with complex nested parameters."""
        class ComplexActivity(Activity):
            def __init__(self):
                super().__init__()
                self.activity_name = "complex_activity"
                self.input_params = {
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
                self.output_params = {
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
        
        self.assertEqual(result["summary"]["count"], 2)
        self.assertEqual(result["summary"]["names"], ["Alice", "Bob"])

        # Test with invalid input
        with self.assertRaises(ValueError):
            activity(users=[
                {"name": "Alice", "age": "30"},  # age should be int
                {"name": "Bob", "age": 25}
            ])

    def test_complex_parameter_validation(self):
        """Test validation of complex parameter types (arrays and objects)."""
        # Test list of strings
        string_list_param = Parameter(
            name="string_list",
            type="array",
            items=Parameter(name="item", type="string")
        )
        
        # Valid cases
        self.assertTrue(string_list_param.validate_value(["hello", "world"]))
        self.assertTrue(string_list_param.validate_value([]))  # Empty list is valid
        
        # Invalid cases
        self.assertFalse(string_list_param.validate_value([1, 2, 3]))  # Wrong item type
        self.assertFalse(string_list_param.validate_value(["hello", 42]))  # Mixed types
        self.assertFalse(string_list_param.validate_value("not_a_list"))  # Not a list
        
        # Test list of integers
        int_list_param = Parameter(
            name="int_list",
            type="array",
            items=Parameter(name="item", type="integer")
        )
        
        self.assertTrue(int_list_param.validate_value([1, 2, 3]))
        self.assertFalse(int_list_param.validate_value([1, "2", 3]))
        
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
        
        # Valid person object
        valid_person = {
            "name": "John",
            "age": 30,
            "scores": [85.5, 92.0, 88.5]
        }
        self.assertTrue(person_param.validate_value(valid_person))
        
        # Invalid person objects
        invalid_person1 = {
            "name": "John",
            "age": "30",  # Wrong type for age
            "scores": [85.5, 92.0, 88.5]
        }
        self.assertFalse(person_param.validate_value(invalid_person1))
        
        invalid_person2 = {
            "name": "John",
            "age": 30,
            "scores": [85.5, "92.0", 88.5]  # Wrong type in array
        }
        self.assertFalse(person_param.validate_value(invalid_person2))

    def test_complex_parameter_serialization(self):
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
        self.assertEqual(loaded_param.name, "user_data")
        self.assertEqual(loaded_param.type, "object")
        self.assertIsNotNone(loaded_param.properties)
        self.assertIn("name", loaded_param.properties)
        self.assertIn("friends", loaded_param.properties)
        
        # Verify nested array type
        friends_param = loaded_param.properties["friends"]
        self.assertEqual(friends_param.type, "array")
        self.assertIsNotNone(friends_param.items)
        
        # Verify nested object type
        friend_param = friends_param.items
        self.assertEqual(friend_param.type, "object")
        self.assertIsNotNone(friend_param.properties)
        self.assertIn("name", friend_param.properties)
        self.assertIn("age", friend_param.properties)
        
        # Test validation with the deserialized parameter
        valid_data = {
            "name": "John",
            "friends": [
                {"name": "Alice", "age": 25},
                {"name": "Bob", "age": 30}
            ]
        }
        self.assertTrue(loaded_param.validate_value(valid_data))
        
        invalid_data = {
            "name": "John",
            "friends": [
                {"name": "Alice", "age": "25"},  # Wrong type for age
                {"name": "Bob", "age": 30}
            ]
        }
        self.assertFalse(loaded_param.validate_value(invalid_data))

    def test_activity_with_complex_parameters(self):
        """Test activity with complex parameter types."""
        # Create an activity with complex input/output parameters
        complex_input_params = {
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
        
        complex_output_params = {
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
        
        activity = SampleActivity()
        activity.input_params = complex_input_params
        activity.output_params = complex_output_params
        
        # Test serialization/deserialization of the activity
        json_str = activity.model_dump_json()
        loaded_activity = SampleActivity.model_validate_json(json_str)
        
        # Verify complex parameters are preserved
        self.assertEqual(
            loaded_activity.input_params["users"].items.properties["name"].type,
            "string"
        )
        self.assertEqual(
            loaded_activity.output_params["summary"].properties["names"].items.type,
            "string"
        )

if __name__ == '__main__':
    unittest.main()
