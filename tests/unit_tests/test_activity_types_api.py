import pytest
from fastapi.testclient import TestClient

from src.activities.activity import Parameter, Activity
from src.activities.activity_registry import ActivityRegistry
from src.api.main import app


# Create a dummy activity class for testing
class TestActivity(Activity):
    def run(self, **inputs):
        return {}


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    # Store existing registrations
    existing_registry = ActivityRegistry._registry.copy()
    # Clear for clean test
    ActivityRegistry.clear()
    yield
    # Restore original registrations
    ActivityRegistry._registry = existing_registry


def test_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_get_activity_types_empty():
    """Test getting activity types when none are registered."""
    response = client.get("/activity-types")
    assert response.status_code == 200
    assert response.json() == {}


def test_get_activity_types():
    """Test getting all activity types."""
    # Register a test activity type
    ActivityRegistry.register(
        activity_name="test_activity",
        activity_type=TestActivity,  # Use TestActivity instead of None
        required_params={"param1": Parameter(name="param1", type="string")},
        description="Test activity description"
    )

    response = client.get("/activity-types")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert "test_activity" in data
    assert data["test_activity"]["activity_type_name"] == "test_activity"
    assert data["test_activity"]["description"] == "Test activity description"


def test_get_activity_types_with_search():
    """Test searching activity types by description."""
    # Register test activity types
    ActivityRegistry.register(
        activity_name="test1",
        activity_type=TestActivity,  # Use TestActivity instead of None
        required_params={},
        description="First test activity"
    )
    ActivityRegistry.register(
        activity_name="test2",
        activity_type=TestActivity,  # Use TestActivity instead of None
        required_params={},
        description="Second activity for testing"
    )

    # Search that should match both
    response = client.get("/activity-types?search=test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Search that should match only first
    response = client.get("/activity-types?search=first")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "test1" in data

    # Search with no matches
    response = client.get("/activity-types?search=nonexistent")
    assert response.status_code == 200
    assert response.json() == {}


def test_get_activity_type_by_name():
    """Test getting a specific activity type by name."""
    # Register a test activity type
    ActivityRegistry.register(
        activity_name="test_activity",
        activity_type=TestActivity,  # Use TestActivity instead of None
        required_params={"param1": Parameter(name="param1", type="string")},
        description="Test activity description"
    )

    response = client.get("/activity-types/test_activity")
    assert response.status_code == 200

    data = response.json()
    assert data["activity_type_name"] == "test_activity"
    assert data["description"] == "Test activity description"


def test_get_activity_type_not_found():
    """Test getting a non-existent activity type."""
    response = client.get("/activity-types/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
