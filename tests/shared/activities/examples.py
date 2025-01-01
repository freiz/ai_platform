from src.activities.activity import Activity, Parameter
from src.activities.activity_registry import ActivityRegistry


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


@ActivityRegistry.register_activity(
    activity_type_name="uppercase",
    description="Converts text to uppercase",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string")
    },
    allow_custom_params=False
)
class UppercaseActivity(Activity):
    # Define fixed parameters at class level
    fixed_input_params = {
        'text': Parameter(name='text', type="string")
    }
    fixed_output_params = {
        'uppercase_text': Parameter(name='uppercase_text', type="string")
    }

    def run(self, text):
        return {'uppercase_text': text.upper()}


@ActivityRegistry.register_activity(
    activity_type_name="concat",
    description="Concatenates two strings",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string")
    },
    allow_custom_params=False
)
class ConcatActivity(Activity):
    # Define fixed parameters at class level
    fixed_input_params = {
        'text1': Parameter(name='text1', type="string"),
        'text2': Parameter(name='text2', type="string")
    }
    fixed_output_params = {
        'concatenated': Parameter(name='concatenated', type="string")
    }

    def run(self, text1, text2):
        return {'concatenated': text1 + text2}


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
