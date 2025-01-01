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
def extractor():
    """Create the extractor activity."""
    return ActivityRegistry.create_activity(
        activity_type_name="llm_activity",
        params={
            "activity_name": "Extractor",
            "system_message": "You are a helpful assistant that extracts all persons information mentioned in a message."
                          "Make best guess about age.",
            "llm_config": LLMConfig(model_name='gpt-4o-mini', temperature=0.1, top_p=0.9),
            "input_params": {
                'message': Parameter(name="message", type='string')
            },
            "output_params": {
                'persons': Parameter(
                    name="persons",
                    type='array',
                    items=Parameter(name="person", type='object', properties={
                        'name': Parameter(name="name", type='string'),
                        'age': Parameter(name="age", type='integer')
                    })
                )
            }
        }
    )


def test_extractor_dump(extractor):
    model_json = extractor.model_dump_json(exclude_none=True, indent=4)
    print(f'\n{model_json}')


def test_extractor_output_schema(extractor):
    schema = extractor._create_output_json_schema()
    print(f'\n{schema}')


def test_extractor_system_message(extractor):
    system_message = extractor._add_output_type()
    print(f'\n{system_message}')
