import unittest
from pydantic import ValidationError
from src.activities import Activity, ActivityParameter, ParamType

class SampleActivity(Activity):
    """A concrete implementation of Activity for testing."""
    def __init__(self, input_params=None, output_params=None, activity_name: str = "sample_activity"):
        super().__init__(
            activity_name=activity_name,
            input_params=input_params or {},
            output_params=output_params or {}
        )
        # custom_prop will be set via property
        self._custom_prop = "test_value"

    @property
    def custom_prop(self) -> str:
        return self._custom_prop

    @custom_prop.setter
    def custom_prop(self, value: str):
        self._custom_prop = value

    def run(self, **inputs):
        # Return a dictionary with the required 'result' parameter
        return {"result": str(inputs)}


class TestActivity(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.input_params = {
            "text": ActivityParameter(name="text", type="string"),
            "count": ActivityParameter(name="count", type="integer")
        }
        self.output_params = {
            "result": ActivityParameter(name="result", type="string")
        }
        self.activity = SampleActivity(
            input_params=self.input_params,
            output_params=self.output_params
        )
        self.activity.custom_prop = "test_value"

    def test_activity_initialization(self):
        """Test basic activity initialization."""
        self.assertEqual(self.activity.activity_name, "sample_activity")
        self.assertEqual(self.activity.custom_prop, "test_value")
        self.assertEqual(len(self.activity.input_params), 2)
        self.assertEqual(len(self.activity.output_params), 1)

    def test_activity_parameter_validation(self):
        """Test ActivityParameter type validation."""
        param = ActivityParameter(name="test", type="string")
        
        # Test valid values
        self.assertTrue(param.validate_value("hello"))
        self.assertFalse(param.validate_value(123))
        
        # Test number type
        number_param = ActivityParameter(name="test", type="number")
        self.assertTrue(number_param.validate_value(123))
        self.assertTrue(number_param.validate_value(123.45))
        self.assertFalse(number_param.validate_value("123"))

    def test_input_validation(self):
        """Test input parameter validation."""
        # Test valid inputs
        valid_inputs = {"text": "hello", "count": 42}
        validated = self.activity.validate_inputs(valid_inputs)
        self.assertEqual(validated, valid_inputs)

        # Test missing input
        with self.assertRaises(ValueError):
            self.activity.validate_inputs({"text": "hello"})

        # Test invalid type
        with self.assertRaises(ValueError):
            self.activity.validate_inputs({"text": "hello", "count": "not_an_integer"})

    def test_activity_execution(self):
        """Test activity execution through __call__."""
        inputs = {"text": "hello", "count": 42}
        outputs = self.activity(**inputs)
        
        # Our sample activity just echoes inputs
        self.assertEqual(outputs, {"result": str(inputs)})

    def test_invalid_parameter_type(self):
        """Test creating ActivityParameter with invalid type."""
        # Try to create parameter with invalid type
        with self.assertRaises(ValidationError):
            ActivityParameter(name="test", type="invalid_type")

        # Verify all valid types work
        valid_types = {"string", "number", "integer", "boolean", "array", "object"}
        for valid_type in valid_types:
            try:
                ActivityParameter(name="test", type=valid_type)
            except ValidationError:
                self.fail(f"Failed to create ActivityParameter with valid type: {valid_type}")

    def test_activity_serialization(self):
        """Test activity serialization to and from JSON."""
        # Create an activity
        activity = SampleActivity(
            input_params={"text": ActivityParameter(name="text", type="string")},
            output_params={"result": ActivityParameter(name="result", type="string")}
        )
        
        # Test serialization
        activity_dict = activity.model_dump()
        self.assertEqual(activity_dict["activity_name"], "sample_activity")
        self.assertEqual(activity_dict["input_params"]["text"]["name"], "text")
        self.assertEqual(activity_dict["input_params"]["text"]["type"], "string")

    def test_activity_parameter_serialization(self):
        """Test ActivityParameter JSON serialization/deserialization."""
        param = ActivityParameter(name="test_param", type="string")
        
        # Test serialization to JSON
        json_str = param.model_dump_json()
        
        # Test deserialization from JSON
        loaded_param = ActivityParameter.model_validate_json(json_str)
        
        # Verify the deserialized object matches the original
        self.assertEqual(loaded_param.name, param.name)
        self.assertEqual(loaded_param.type, param.type)
        
        # Test all parameter types
        for param_type in ["string", "number", "integer", "boolean", "array", "object"]:
            param = ActivityParameter(name=f"test_{param_type}", type=param_type)
            json_str = param.model_dump_json()
            loaded_param = ActivityParameter.model_validate_json(json_str)
            self.assertEqual(loaded_param.type, param_type)

    def test_activity_json_serialization(self):
        """Test Activity JSON serialization/deserialization."""
        # Create an activity with some parameters
        input_params = {
            "text": ActivityParameter(name="text", type="string"),
            "count": ActivityParameter(name="count", type="integer")
        }
        output_params = {
            "result": ActivityParameter(name="result", type="string")
        }
        activity = SampleActivity(
            input_params=input_params,
            output_params=output_params
        )
        
        # Test serialization to JSON
        json_str = activity.model_dump_json()
        
        # Test deserialization from JSON
        loaded_activity = SampleActivity.model_validate_json(json_str)
        
        # Verify the deserialized object matches the original
        self.assertEqual(loaded_activity.activity_name, activity.activity_name)
        self.assertEqual(len(loaded_activity.input_params), len(activity.input_params))
        self.assertEqual(len(loaded_activity.output_params), len(activity.output_params))
        
        # Check input parameters
        for param_name, param in activity.input_params.items():
            loaded_param = loaded_activity.input_params[param_name]
            self.assertEqual(loaded_param.name, param.name)
            self.assertEqual(loaded_param.type, param.type)
        
        # Check output parameters
        for param_name, param in activity.output_params.items():
            loaded_param = loaded_activity.output_params[param_name]
            self.assertEqual(loaded_param.name, param.name)
            self.assertEqual(loaded_param.type, param.type)

    def test_complex_parameter_validation(self):
        """Test validation of complex parameter types (arrays and objects)."""
        # Test list of strings
        string_list_param = ActivityParameter(
            name="string_list",
            type="array",
            items=ActivityParameter(name="item", type="string")
        )
        
        # Valid cases
        self.assertTrue(string_list_param.validate_value(["hello", "world"]))
        self.assertTrue(string_list_param.validate_value([]))  # Empty list is valid
        
        # Invalid cases
        self.assertFalse(string_list_param.validate_value([1, 2, 3]))  # Wrong item type
        self.assertFalse(string_list_param.validate_value(["hello", 42]))  # Mixed types
        self.assertFalse(string_list_param.validate_value("not_a_list"))  # Not a list
        
        # Test list of integers
        int_list_param = ActivityParameter(
            name="int_list",
            type="array",
            items=ActivityParameter(name="item", type="integer")
        )
        
        self.assertTrue(int_list_param.validate_value([1, 2, 3]))
        self.assertFalse(int_list_param.validate_value([1, "2", 3]))
        
        # Test nested object
        person_param = ActivityParameter(
            name="person",
            type="object",
            properties={
                "name": ActivityParameter(name="name", type="string"),
                "age": ActivityParameter(name="age", type="integer"),
                "scores": ActivityParameter(
                    name="scores",
                    type="array",
                    items=ActivityParameter(name="score", type="number")
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
        original_param = ActivityParameter(
            name="user_data",
            type="object",
            properties={
                "name": ActivityParameter(name="name", type="string"),
                "friends": ActivityParameter(
                    name="friends",
                    type="array",
                    items=ActivityParameter(
                        name="friend",
                        type="object",
                        properties={
                            "name": ActivityParameter(name="name", type="string"),
                            "age": ActivityParameter(name="age", type="integer")
                        }
                    )
                )
            }
        )
        
        # Serialize to JSON
        json_str = original_param.model_dump_json()
        
        # Deserialize from JSON
        loaded_param = ActivityParameter.model_validate_json(json_str)
        
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
            "users": ActivityParameter(
                name="users",
                type="array",
                items=ActivityParameter(
                    name="user",
                    type="object",
                    properties={
                        "name": ActivityParameter(name="name", type="string"),
                        "age": ActivityParameter(name="age", type="integer")
                    }
                )
            )
        }
        
        complex_output_params = {
            "summary": ActivityParameter(
                name="summary",
                type="object",
                properties={
                    "count": ActivityParameter(name="count", type="integer"),
                    "names": ActivityParameter(
                        name="names",
                        type="array",
                        items=ActivityParameter(name="name", type="string")
                    )
                }
            )
        }
        
        activity = SampleActivity(
            input_params=complex_input_params,
            output_params=complex_output_params
        )
        
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
