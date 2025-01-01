import pytest

from src.activities import LLMActivity, Parameter
from src.activities.activity_registry import ActivityRegistry
from src.utils.llm import LLMConfig


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


def test_capital_finder_dump(capital_finder):
    model_json = capital_finder.model_dump_json(exclude_none=True, indent=4)
    print(f'\n{model_json}')


def test_capital_finder_output_schema(capital_finder):
    schema = capital_finder._create_output_json_schema()
    print(f'\n{schema}')


def test_capital_finder_system_message(capital_finder):
    system_message = capital_finder._add_output_type()
    print(f'\n{system_message}')
