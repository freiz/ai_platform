from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.activities.activity_registry import ActivityRegistry
from src.activities.tools.freight_quote_activity import FreightQuoteActivity

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
    ActivityRegistry.register_class(FreightQuoteActivity)

    yield

    # Clear registry after tests
    ActivityRegistry.clear()


@pytest.fixture
def freight_quote():
    """Create the freight quote activity."""
    return ActivityRegistry.create_activity(
        activity_type_name="freight_quote_activity",
        params={
            "activity_name": "FreightQuoteTest",
        }
    )


def test_freight_quote(freight_quote):
    inputs = {
        'quote_details': {
            'equipment_type': 'Flatbeds',
            'feet': 53,
            'weight_lbs': 40000,
            'date': '01/10/2025',
            'origin': {
                'address': '12200 Montague St, Pacoima, CA 91331',
                'city': 'Pacoima',
                'state': 'CA'
            },
            'destination': {
                'address': '250 Newhall St, San Francisco, CA 94124',
                'city': 'San Francisco',
                'state': 'CA'
            }
        }
    }
    outputs = freight_quote(**inputs)
    assert 'response_json' in outputs
    # Add more specific assertions based on the expected response structure
    response = outputs['response_json']
    assert isinstance(response, str)  # or whatever the expected type is

    print(f'\n{response}')
