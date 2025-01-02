import copy
import uuid

from tests.functional_tests.conftest import BASE_URL


def test_create_activity_success(http_session, user_id, test_activity_data):
    """Test successful activity creation."""
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=test_activity_data
    )

    assert response.status_code == 201
    data = response.json()

    assert data["activity_type"] == "adder_activity"
    assert data["activity_name"] == test_activity_data["activity_name"]
    assert "id" in data
    assert "created_at" in data
    assert "input_params" in data
    assert "output_params" in data

    # Verify input/output params match adder activity specs
    assert set(data["input_params"].keys()) == {"num1", "num2"}
    assert set(data["output_params"].keys()) == {"sum"}

    # Verify Location header
    assert response.headers["Location"] == f"/users/{user_id}/activities/{data['id']}"


def test_create_activity_duplicate_name(http_session, user_id, test_activity_data):
    """Test creating activity with duplicate name fails."""
    # Create first activity
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=test_activity_data
    )
    assert response.status_code == 201

    # Try to create second activity with same name
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=test_activity_data
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_activity_invalid_params(http_session, user_id):
    """Test creating activity with invalid parameters fails."""
    invalid_data = {
        "activity_type_name": "adder_activity",
        "activity_name": "test_adder",
        "allow_custom_params": True,  # This should be False for adder_activity
        "params": {
            "activity_name": "test_adder"
        }
    }
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=invalid_data
    )
    assert response.status_code == 400


def test_list_activities(http_session, user_id, test_activity_data):
    """Test listing activities for a user."""
    # Create two activities with different names
    activity1 = copy.deepcopy(test_activity_data)
    activity2 = copy.deepcopy(test_activity_data)
    activity2["activity_name"] = f"test_adder_{uuid.uuid4().hex[:8]}"
    activity2["params"]["activity_name"] = activity2["activity_name"]

    # Create first activity
    response1 = http_session.post(f"{BASE_URL}/users/{user_id}/activities", json=activity1)
    assert response1.status_code == 201

    # Create second activity
    response2 = http_session.post(f"{BASE_URL}/users/{user_id}/activities", json=activity2)
    assert response2.status_code == 201

    # List activities
    response = http_session.get(f"{BASE_URL}/users/{user_id}/activities")
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 2
    assert all(isinstance(activity["id"], str) for activity in activities)
    assert all(activity["activity_type"] == "adder_activity" for activity in activities)


def test_get_activity(http_session, user_id, test_activity_data):
    """Test getting a specific activity."""
    # Create an activity
    create_response = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=test_activity_data
    )
    activity_id = create_response.json()["id"]

    # Get the activity
    response = http_session.get(f"{BASE_URL}/users/{user_id}/activities/{activity_id}")
    assert response.status_code == 200
    activity = response.json()
    assert activity["id"] == activity_id
    assert activity["activity_type"] == "adder_activity"
    assert activity["activity_name"] == test_activity_data["activity_name"]


def test_get_nonexistent_activity(http_session, user_id):
    """Test getting a non-existent activity returns 404."""
    fake_id = str(uuid.uuid4())
    response = http_session.get(f"{BASE_URL}/users/{user_id}/activities/{fake_id}")
    assert response.status_code == 404


def test_delete_activity(http_session, user_id, test_activity_data):
    """Test deleting an activity."""
    # Create an activity
    create_response = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=test_activity_data
    )
    activity_id = create_response.json()["id"]

    # Delete the activity
    response = http_session.delete(f"{BASE_URL}/users/{user_id}/activities/{activity_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = http_session.get(f"{BASE_URL}/users/{user_id}/activities/{activity_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_activity(http_session, user_id):
    """Test deleting a non-existent activity returns 404."""
    fake_id = str(uuid.uuid4())
    response = http_session.delete(f"{BASE_URL}/users/{user_id}/activities/{fake_id}")
    assert response.status_code == 404


def test_cross_user_activity_access(http_session, test_activity_data):
    """Test that users cannot access other users' activities."""
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    # Create activity as user1
    create_response = http_session.post(
        f"{BASE_URL}/users/{user1_id}/activities",
        json=test_activity_data
    )
    activity_id = create_response.json()["id"]

    # Try to access as user2
    get_response = http_session.get(f"{BASE_URL}/users/{user2_id}/activities/{activity_id}")
    assert get_response.status_code == 404

    # Try to delete as user2
    delete_response = http_session.delete(f"{BASE_URL}/users/{user2_id}/activities/{activity_id}")
    assert delete_response.status_code == 404
