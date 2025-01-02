from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.activities import LLMActivity, Parameter
from src.activities.activity_registry import ActivityRegistry
from src.utils.llm import LLMConfig

# Get the absolute path of the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_PATH = PROJECT_ROOT / '.env'

# Load environment variables from .env file
load_dotenv_succeeded = load_dotenv(ENV_PATH)
assert load_dotenv_succeeded, f"Failed to load .env file from {ENV_PATH}"


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for all tests in this file."""
    # Clear registry before tests
    ActivityRegistry.clear()
    # Register the activity for our tests
    ActivityRegistry.register_class(LLMActivity)

    yield

    # Clear registry after tests
    ActivityRegistry.clear()


@pytest.fixture
def capital_finder():
    """Create the capital finder activity."""
    return ActivityRegistry.create_activity(
        activity_type_name="llm_activity",
        params={
            "activity_name": "CapitalFinder",
            "system_message": "You are a helpful assistant that returns the capital of a country.",
            "llm_config": LLMConfig(model_name='gpt-4o-mini', temperature=0.1, top_p=0.9),
            "input_params": {
                'country': Parameter(name="country", type='string')
            },
            "output_params": {
                'capital': Parameter(name="capital", type='string')
            }
        }
    )


def test_capital_finder(capital_finder):
    inputs = {'country': 'France'}
    outputs = capital_finder(**inputs)
    print(f'\n{outputs}')
    assert outputs['capital'].lower() == 'paris'
