"""
LLM Module for handling interactions with Large Language Models.
Currently supports OpenAI's GPT models through their API.
"""

from pydantic import BaseModel
import openai


class LLMConfig(BaseModel):
    """Configuration settings for LLM interactions.

    Attributes:
        model_name (str): Name of the model to use (e.g., 'gpt-4', 'gpt-3.5-turbo')
        temperature (float): Controls randomness in the output. Higher values (e.g., 0.8) make the output more random,
                           while lower values (e.g., 0.2) make it more focused and deterministic.
        top_p (float): Controls diversity via nucleus sampling. Keeps the cumulative probability of tokens up to top_p.
    """
    model_name: str
    temperature: float
    top_p: float


class LLM():
    """Handler for Large Language Model interactions.

    Provides a unified interface for different LLM backends, currently supporting OpenAI's models.

    Args:
        config (LLMConfig): Configuration settings for the LLM interaction.

    Raises:
        ValueError: If the specified model is not supported.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.supported_models = {
            'gpt-4o': self._complete_openai,
            'gpt-4o-mini': self._complete_openai,
        }
        if self.config.model_name not in self.supported_models:
            raise ValueError(f"Unsupported model: {self.config.model_name}")
        self.completion_func = self.supported_models[self.config.model_name]

    def complete(self, system_message: str, user_message: str) -> str:
        """Generate a completion using the configured LLM.

        Args:
            system_message (str): The system message providing context or instructions.
            user_message (str): The user's input message to complete.

        Returns:
            str: The model's completion response.
        """
        return self.completion_func(system_message, user_message)

    def _complete_openai(self, system_message: str, user_message: str) -> str:
        """Generate a completion using OpenAI's API.

        Args:
            system_message (str): The system message providing context or instructions.
            user_message (str): The user's input message to complete.

        Returns:
            str: The model's completion response.

        Raises:
            Exception: If there's an error during the API call.
        """
        response = openai.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=self.config.temperature,
            top_p=self.config.top_p,
        )
        return response.choices[0].message.content
