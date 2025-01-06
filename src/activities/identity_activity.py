from typing import Any, Dict

from src.activities.activity import Activity
from src.activities.activity_registry import ActivityRegistry, Parameter


@ActivityRegistry.register_activity(
    activity_type_name="identity_activity",
    description="Identity activity that passes input values directly to output with same parameter structure",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string"),
    },
    allow_custom_params=True
)
class IdentityActivity(Activity):
    """
    An activity that passes input values directly to output with identical parameter structure.
    Input and output parameters must be defined with the same structure.
    """

    def __init__(self, activity_name: str, input_params: Dict[str, Parameter],
                 output_params: Dict[str, Parameter], **kwargs):
        # Verify that input and output parameters have identical structure
        if input_params != output_params:
            raise ValueError(
                "Input and output parameters must have identical structure for IdentityActivity"
            )
        
        super().__init__(
            activity_name=activity_name,
            input_params=input_params,
            output_params=output_params,
            **kwargs
        )

    def run(self, **inputs: Any) -> Dict[str, Any]:
        # Simply return the input values as they are already validated
        return inputs 
