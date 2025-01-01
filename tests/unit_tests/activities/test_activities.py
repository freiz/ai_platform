from src.activities.activity import Activity, Parameter
from src.activities.activity_registry import ActivityRegistry


# Example activity type with fixed parameters
@ActivityRegistry.register_activity(
    activity_type_name="string_length",
    description="Calculates the length of a string",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string")
    }
)
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
@ActivityRegistry.register_activity(
    activity_type_name="custom_params",
    description="Activity with customizable parameters",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string")
    },
    allow_custom_params=True
)
class CustomParamsActivity(Activity):
    def __init__(self, activity_name: str, input_params: dict, output_params: dict):
        super().__init__(activity_name=activity_name, input_params=input_params, output_params=output_params)

    def run(self, **inputs):
        # Create a greeting using the input name
        return {
            "greeting": f"Hello, {inputs['name']}!"
        } 