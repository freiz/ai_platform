from pathlib import Path

from dotenv import load_dotenv

from src.utils.llm import LLMConfig, LLM

# Get the absolute path of the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / '.env'

# Load environment variables from .env file
load_dotenv_succeeded = load_dotenv(ENV_PATH)
assert load_dotenv_succeeded, f"Failed to load .env file from {ENV_PATH}"


def test_call_llm():
    config = LLMConfig(model_name='gpt-4o-mini', temperature=0.2, top_p=1.0)
    llm = LLM(config)
    system_message = "You are a helpful assistant."
    user_message = "What is the capital of France?"
    response = llm.complete(system_message, user_message)
    print(response)
    assert response
