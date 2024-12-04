import unittest
from pydantic import ValidationError
from src.activity import Activity, ActivityParameter, ParamType

class SampleActivity(Activity):
    """A concrete implementation of Activity for testing."""
    def __init__(self, input_params=None, output_params=None, name: str = "sample_activity"):
        super().__init__(
            _name=name,  # Using _name as it's the alias
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
        self.assertEqual(self.activity.name, "sample_activity")
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
        activity_dict = activity.dict()
        self.assertEqual(activity_dict["name"], "sample_activity")
        self.assertEqual(activity_dict["input_params"]["text"].dict()["name"], "text")
        self.assertEqual(activity_dict["input_params"]["text"].dict()["type"], "string")

if __name__ == '__main__':
    unittest.main()
