import json
from typing import Any, Dict

from src.activities.activity import Activity
from src.activities.activity_registry import ActivityRegistry, Parameter
from src.utils.llm import LLMConfig, LLM


@ActivityRegistry.register_activity(
    activity_type_name="llm_activity",
    description="LLM-based activity with customizable I/O parameters",
    required_params={
        "activity_name": Parameter(name="activity_name", type="string"),
        "system_message": Parameter(name="system_message", type="string"),
        "llm_config": Parameter(name="llm_config", type="object", properties={
            "model_name": Parameter(name="model_name", type="string"),
            "temperature": Parameter(name="temperature", type="number"),
            "top_p": Parameter(name="top_p", type="number")
        })
    },
    allow_custom_params=True
)
class LLMActivity(Activity):
    system_message: str
    llm_config: LLMConfig

    def run(self, **inputs: Any) -> Dict[str, Any]:
        system_message = self._add_output_type()
        user_message = self._to_json(inputs)

        llm = LLM(self.llm_config)
        llm_str_response = llm.complete(system_message, user_message)
        # Only keep the JSON content, consider using regex later
        llm_str_response = llm_str_response.replace('```json', '').replace('```', '')
        llm_response = self._parse_json(llm_str_response)

        return llm_response

    @staticmethod
    def _to_json(inputs: Dict[str, Any]) -> str:
        return json.dumps(inputs)

    def _parse_json(self, json_str: str) -> Dict[str, Any]:
        """
        Parse LLM's JSON response against output_params.
        
        Args:
            json_str: JSON string from LLM
            
        Returns:
            Dict[str, Any]: Validated output dictionary
            
        Raises:
            ValueError: If JSON is invalid
        """
        try:
            # Parse JSON
            data = json.loads(json_str)

            outputs = {}

            for param_name, param in self.output_params.items():
                if param_name not in data:
                    raise ValueError(f"Missing required parameter: {param_name}")
                value = data[param_name]
                outputs[param_name] = value

            return outputs

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {str(e)}, raw response: {json_str}")

    def _create_output_json_schema(self) -> str:
        def _process_parameter(param, indent_level=1) -> tuple[str, str]:
            indent = "    " * indent_level
            json_part = ""
            desc_part = ""

            # Handle basic type
            if param.type not in ["array", "object"]:
                json_part = f'<{param.type}>'
                desc_part = f"{param.type}"

            # Handle array type
            elif param.type == "array" and param.items is not None:
                item_json, item_desc = _process_parameter(param.items, indent_level + 1)
                json_part = f'[{item_json}]'
                desc_part = f"array of {item_desc}"

            # Handle object type
            elif param.type == "object" and param.properties is not None:
                props_json = []
                props_desc = []

                for prop_name, prop in param.properties.items():
                    prop_json, prop_desc = _process_parameter(prop, indent_level + 1)
                    props_json.append(f'{indent}    "{prop_name}": {prop_json}')
                    props_desc.append(f"{prop_name}: {prop_desc}")

                json_part = "{\n" + ",\n".join(props_json) + f"\n{indent}}}"
                desc_part = f"object with properties ({', '.join(props_desc)})"

            return json_part, desc_part

        # Build JSON structure and parameter descriptions
        json_structure = "{\n"
        param_descriptions = []

        for param_name, param in self.output_params.items():
            # Process the parameter
            param_json, param_desc = _process_parameter(param)

            # Add to JSON structure
            json_structure += f'    "{param_name}": {param_json}'
            if param != list(self.output_params.items())[-1][1]:  # If not last item
                json_structure += ","
            json_structure += "\n"

            # Add to parameter descriptions
            param_descriptions.append(f"- {param_name}: {param_desc}")

        json_structure += "}"

        return json_structure

    def _add_output_type(self) -> str:
        return f'''{self.system_message}
        
OUTPUT FORMAT
ONLY return a JSON object with the following structure
double check if the JSON is valid especially for escape characters
No other explanations needed

{self._create_output_json_schema()}'''
