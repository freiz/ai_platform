from src.activities.activity import Activity, Parameter
from src.activities.activity_registry import ActivityRegistry


# Example activity type with fixed parameters
@ActivityRegistry.register_activity(
    activity_type_name="string_length",
    description="Calculates the length of a string",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string")
    },
    allow_custom_params=False
)
class StringLengthActivity(Activity):
    # Define fixed parameters at class level
    fixed_input_params = {
        'text': Parameter(name='text', type="string")
    }
    fixed_output_params = {
        'length': Parameter(name='length', type="integer")
    }

    def run(self, text):
        return {'length': len(text)}


# Example activity type with customizable parameters
@ActivityRegistry.register_activity(
    activity_type_name="custom_params",
    description="Activity with customizable parameters",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string")
    },
    allow_custom_params=True
)
class CustomParamsActivity(Activity):
    def run(self, **inputs):
        # Create a greeting using the input name
        return {
            "greeting": f"Hello, {inputs['name']}!"
        }
