import json
from pydantic import BaseModel
from src.activities.activity import Activity, Parameter, ParamType
from src.utils.llm import LLMConfig
from typing import Any, Dict


class LLMActivity(Activity):
    system_message: str
    llm_config: LLMConfig 

    def run(self, **inputs: Any) -> Dict[str, Any]:
        system_message = self._add_output_type()
        user_message = self._to_json(inputs)

        ## Will add real implementation later, suppose we get the response from LLM
        llm_response = 'DUMMY RESPONSE'
        return self._parse_json(llm_response)

    def _to_json(self, inputs: Dict[str, Any]) -> str:
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
            raise ValueError(f"Invalid JSON response: {str(e)}")

    def _create_output_json_schema(self) -> str:
        # Build JSON structure
        json_structure = "{\n"
        param_descriptions = []
        
        for param_name, param in self.output_params.items():
            # Add to JSON structure
            json_structure += f'    "{param_name}": <{param.type}>'
            if param != list(self.output_params.items())[-1][1]:  # If not last item
                json_structure += ","
            json_structure += "\n"
            
            # Build parameter description
            desc = f"- {param_name}: {param.type}"
            
            # Handle array type
            if param.type == "array" and param.items is not None:
                desc += f" of {param.items.type}"
                
            # Handle object type
            if param.type == "object" and param.properties is not None:
                props = [f"{k}: {v.type}" for k, v in param.properties.items()]
                desc += f" with properties ({', '.join(props)})"
                
            param_descriptions.append(desc)
        
        json_structure += "}"
        
        return json_structure

    def _add_output_type(self) -> str:
        return f'''{self.system_message}
        
OUTPUT FORMAT
ONLY return a JSON object with the following structure
double check if the JSON is valid especially for escape characters
No other explainations needed

{self._create_output_json_schema()}'''