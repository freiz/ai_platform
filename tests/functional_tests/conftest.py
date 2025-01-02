import uuid

import pytest
import requests
from requests.adapters import HTTPAdapter

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def http_session():
    """Create a session for all tests to reuse."""
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1)
    session.mount('http://', adapter)
    session.headers.update({'Connection': 'close'})
    yield session
    session.close()


@pytest.fixture
def user_id():
    """Generate a random user ID for tests."""
    return str(uuid.uuid4())


@pytest.fixture
def test_activity_data():
    """Create test activity data for adder activity."""
    activity_name = f"test_adder_{uuid.uuid4().hex[:8]}"
    return {
        "activity_type_name": "adder_activity",
        "activity_name": activity_name,
        "allow_custom_params": False,
        "params": {
            "activity_name": activity_name
        }
    }
