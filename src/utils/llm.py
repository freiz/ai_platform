"""
LLM Module for handling interactions with Large Language Models.
Currently supports OpenAI's GPT models through their API.
"""

from pydantic import BaseModel, Field, validator
import openai
from typing import Dict, Optional
import time
import os
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMConfig(BaseModel):
    """Configuration settings for LLM interactions.

    Attributes:
        model_name (str): Name of the model to use (e.g., 'gpt-4o', 'gpt-4o-mini')
        temperature (float): Controls randomness in the output. Higher values (e.g., 0.8) make the output more random,
                           while lower values (e.g., 0.2) make it more focused and deterministic.
        top_p (float): Controls diversity via nucleus sampling. Keeps the cumulative probability of tokens up to top_p.
    """
    model_name: str
    temperature: float = Field(ge=0.0, le=1.0)
    top_p: float = Field(ge=0.0, le=1.0)

    @validator('model_name')
    def validate_model_name(cls, v):
        valid_models = {'gpt-4o', 'gpt-4o-mini'}
        if v not in valid_models:
            raise ValueError(f"Model must be one of {valid_models}")
        return v


class LLM():
    """Handler for Large Language Model interactions.

    Provides a unified interface for different LLM backends, currently supporting OpenAI's models.

    Args:
        config (LLMConfig): Configuration settings for the LLM interaction.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.supported_models = {
            'gpt-4o': self._complete_openai,
            'gpt-4o-mini': self._complete_openai,
        }
        
        if self.config.model_name not in self.supported_models:
            raise ValueError(f"Unsupported model: {self.config.model_name}")
            
        if not os.environ.get('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable must be set")
            
        self.completion_func = self.supported_models[self.config.model_name]

    def complete(self, system_message: str, user_message: str) -> str:
        """Generate a completion using the configured LLM.

        Args:
            system_message (str): The system message providing context or instructions.
            user_message (str): The user's input message to complete.

        Returns:
            str: The model's completion response.
        """
        result = self.completion_func(system_message, user_message)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _complete_openai(self, system_message: str, user_message: str) -> str:
        """Generate a completion using OpenAI's API.

        Args:
            system_message (str): The system message providing context or instructions.
            user_message (str): The user's input message to complete.

        Returns:
            str: The model's completion response.
        """
        try:
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
        except openai.RateLimitError:
            time.sleep(20)  # Wait before retry
            raise
        except Exception as e:
            raise
