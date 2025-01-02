from typing import Any, Dict

from src.activities import Parameter
from src.activities.activity_registry import ActivityRegistry
from src.activities.tool_activity import ToolActivity


@ActivityRegistry.register_activity(
    activity_type_name="adder_activity",
    description="Adds two numbers",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string"),
    },
    allow_custom_params=False
)
class AdderActivity(ToolActivity):
    # Define fixed parameters at class level
    fixed_input_params = {
        'num1': Parameter(name='num1', type="number"),
        'num2': Parameter(name='num2', type="number")
    }
    fixed_output_params = {
        'sum': Parameter(name='sum', type="number")
    }

    def run(self, num1, num2) -> Dict[str, Any]:
        return {'sum': num1 + num2}
