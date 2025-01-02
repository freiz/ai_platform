import copy
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


@pytest.fixture
def test_activities(http_session, user_id, test_activity_data):
    """Create three test activities and return their IDs."""
    # Create first activity
    activity1 = copy.deepcopy(test_activity_data)
    response1 = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=activity1
    )
    assert response1.status_code == 201
    activity1_id = response1.json()["id"]

    # Create second activity
    activity2 = copy.deepcopy(test_activity_data)
    activity2["activity_name"] = f"test_adder_{uuid.uuid4().hex[:8]}"
    activity2["params"]["activity_name"] = activity2["activity_name"]
    response2 = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=activity2
    )
    assert response2.status_code == 201
    activity2_id = response2.json()["id"]

    # Create third activity
    activity3 = copy.deepcopy(test_activity_data)
    activity3["activity_name"] = f"test_adder_{uuid.uuid4().hex[:8]}"
    activity3["params"]["activity_name"] = activity3["activity_name"]
    response3 = http_session.post(
        f"{BASE_URL}/users/{user_id}/activities",
        json=activity3
    )
    assert response3.status_code == 201
    activity3_id = response3.json()["id"]

    return activity1_id, activity2_id, activity3_id


@pytest.fixture
def test_workflow_data(test_activities):
    """Create test workflow data with three adder activities where node1 and node2 feed into node3."""
    activity1_id, activity2_id, activity3_id = test_activities
    return {
        "workflow_name": f"test_workflow_{uuid.uuid4().hex[:8]}",
        "nodes": {
            "node1": {"activity_id": activity1_id},
            "node2": {"activity_id": activity2_id},
            "node3": {"activity_id": activity3_id}
        },
        "connections": [
            {
                "source_node": "node1",
                "source_output": "sum",
                "target_node": "node3",
                "target_input": "num1"
            },
            {
                "source_node": "node2",
                "source_output": "sum",
                "target_node": "node3",
                "target_input": "num2"
            }
        ]
    }


def test_create_workflow_success(http_session, user_id, test_workflow_data):
    """Test successful workflow creation."""
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=test_workflow_data
    )

    assert response.status_code == 201
    data = response.json()

    assert data["workflow_name"] == test_workflow_data["workflow_name"]
    assert "id" in data
    assert "created_at" in data
    assert data["nodes"] == test_workflow_data["nodes"]
    assert data["connections"] == test_workflow_data["connections"]


def test_create_workflow_duplicate_name(http_session, user_id, test_workflow_data):
    """Test creating workflow with duplicate name fails."""
    # Create first workflow
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=test_workflow_data
    )
    assert response.status_code == 201

    # Try to create second workflow with same name
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=test_workflow_data
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_workflow_invalid_connection(http_session, user_id, test_workflow_data):
    """Test creating workflow with invalid connection fails."""
    # Modify connection to use non-existent parameter
    test_workflow_data["connections"][0]["source_output"] = "nonexistent"

    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=test_workflow_data
    )
    assert response.status_code == 400


def test_create_workflow_disconnected_nodes(http_session, user_id, test_activities):
    """Test creating workflow with disconnected nodes fails."""
    activity1_id, activity2_id, activity3_id = test_activities
    workflow_data = {
        "workflow_name": f"test_workflow_{uuid.uuid4().hex[:8]}",
        "nodes": {
            "node1": {"activity_id": activity1_id},
            "node2": {"activity_id": activity2_id},
            "node3": {"activity_id": activity3_id}
        },
        "connections": []  # No connections between nodes
    }

    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=workflow_data
    )
    assert response.status_code == 400


def test_list_workflows(http_session, user_id, test_workflow_data):
    """Test listing workflows for a user."""
    # Create two workflows with different names
    workflow1 = copy.deepcopy(test_workflow_data)
    workflow2 = copy.deepcopy(test_workflow_data)
    workflow2["workflow_name"] = f"test_workflow_{uuid.uuid4().hex[:8]}"

    # Create first workflow
    response1 = http_session.post(f"{BASE_URL}/users/{user_id}/workflows", json=workflow1)
    assert response1.status_code == 201

    # Create second workflow
    response2 = http_session.post(f"{BASE_URL}/users/{user_id}/workflows", json=workflow2)
    assert response2.status_code == 201

    # List workflows
    response = http_session.get(f"{BASE_URL}/users/{user_id}/workflows")
    assert response.status_code == 200
    workflows = response.json()
    assert len(workflows) == 2
    assert all(isinstance(workflow["id"], str) for workflow in workflows)
    assert all("activities" in workflow for workflow in workflows)


def test_get_workflow(http_session, user_id, test_workflow_data):
    """Test getting a specific workflow."""
    # Create a workflow
    create_response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=test_workflow_data
    )
    workflow_id = create_response.json()["id"]

    # Get the workflow
    response = http_session.get(f"{BASE_URL}/users/{user_id}/workflows/{workflow_id}")
    assert response.status_code == 200
    workflow = response.json()
    assert workflow["id"] == workflow_id
    assert workflow["workflow_name"] == test_workflow_data["workflow_name"]
    assert workflow["nodes"] == test_workflow_data["nodes"]
    assert workflow["connections"] == test_workflow_data["connections"]
    assert "activities" in workflow


def test_get_nonexistent_workflow(http_session, user_id):
    """Test getting a non-existent workflow returns 404."""
    fake_id = str(uuid.uuid4())
    response = http_session.get(f"{BASE_URL}/users/{user_id}/workflows/{fake_id}")
    assert response.status_code == 404


def test_delete_workflow(http_session, user_id, test_workflow_data):
    """Test deleting a workflow."""
    # Create a workflow
    create_response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=test_workflow_data
    )
    workflow_id = create_response.json()["id"]

    # Delete the workflow
    response = http_session.delete(f"{BASE_URL}/users/{user_id}/workflows/{workflow_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = http_session.get(f"{BASE_URL}/users/{user_id}/workflows/{workflow_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_workflow(http_session, user_id):
    """Test deleting a non-existent workflow returns 404."""
    fake_id = str(uuid.uuid4())
    response = http_session.delete(f"{BASE_URL}/users/{user_id}/workflows/{fake_id}")
    assert response.status_code == 404


def test_execute_workflow_success(http_session, user_id, test_workflow_data):
    """Test successful workflow execution."""
    # Create a workflow
    create_response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=test_workflow_data
    )
    workflow_id = create_response.json()["id"]

    # Execute the workflow
    execute_data = {
        "inputs": {
            "node1": {
                "num1": 5,
                "num2": 3
            },
            "node2": {
                "num1": 2,
                "num2": 4
            }
        }
    }
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows/{workflow_id}/execute",
        json=execute_data
    )
    assert response.status_code == 200
    result = response.json()

    # First node adds 5 + 3 = 8
    # Second node adds 2 + 4 = 6
    # Third node adds 8 + 6 = 14
    assert result["node3"]["sum"] == 14


def test_execute_workflow_invalid_input(http_session, user_id, test_workflow_data):
    """Test workflow execution with invalid input fails."""
    # Create a workflow
    create_response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows",
        json=test_workflow_data
    )
    workflow_id = create_response.json()["id"]

    # Execute with invalid input
    execute_data = {
        "inputs": {
            "node1": {
                "num1": "not_a_number",  # Invalid input type
                "num2": 3
            },
            "node2": {
                "num1": 2,
                "num2": 4
            }
        }
    }
    response = http_session.post(
        f"{BASE_URL}/users/{user_id}/workflows/{workflow_id}/execute",
        json=execute_data
    )
    assert response.status_code == 400


def test_cross_user_workflow_access(http_session, test_activity_data):
    """Test that users cannot access other users' workflows."""
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    # Create activities for user1
    activity1 = copy.deepcopy(test_activity_data)
    response1 = http_session.post(
        f"{BASE_URL}/users/{user1_id}/activities",
        json=activity1
    )
    assert response1.status_code == 201
    activity1_id = response1.json()["id"]

    activity2 = copy.deepcopy(test_activity_data)
    activity2["activity_name"] = f"test_adder_{uuid.uuid4().hex[:8]}"
    activity2["params"]["activity_name"] = activity2["activity_name"]
    response2 = http_session.post(
        f"{BASE_URL}/users/{user1_id}/activities",
        json=activity2
    )
    assert response2.status_code == 201
    activity2_id = response2.json()["id"]

    activity3 = copy.deepcopy(test_activity_data)
    activity3["activity_name"] = f"test_adder_{uuid.uuid4().hex[:8]}"
    activity3["params"]["activity_name"] = activity3["activity_name"]
    response3 = http_session.post(
        f"{BASE_URL}/users/{user1_id}/activities",
        json=activity3
    )
    assert response3.status_code == 201
    activity3_id = response3.json()["id"]

    # Create workflow data for user1
    workflow_data = {
        "workflow_name": f"test_workflow_{uuid.uuid4().hex[:8]}",
        "nodes": {
            "node1": {"activity_id": activity1_id},
            "node2": {"activity_id": activity2_id},
            "node3": {"activity_id": activity3_id}
        },
        "connections": [
            {
                "source_node": "node1",
                "source_output": "sum",
                "target_node": "node3",
                "target_input": "num1"
            },
            {
                "source_node": "node2",
                "source_output": "sum",
                "target_node": "node3",
                "target_input": "num2"
            }
        ]
    }

    # Create workflow as user1
    create_response = http_session.post(
        f"{BASE_URL}/users/{user1_id}/workflows",
        json=workflow_data
    )
    assert create_response.status_code == 201
    workflow_id = create_response.json()["id"]

    # Try to access as user2
    get_response = http_session.get(f"{BASE_URL}/users/{user2_id}/workflows/{workflow_id}")
    assert get_response.status_code == 404

    # Try to delete as user2
    delete_response = http_session.delete(f"{BASE_URL}/users/{user2_id}/workflows/{workflow_id}")
    assert delete_response.status_code == 404

    # Try to execute as user2
    execute_data = {
        "inputs": {
            "node1": {"num1": 5, "num2": 3},
            "node2": {"num1": 2, "num2": 4}
        }
    }
    execute_response = http_session.post(
        f"{BASE_URL}/users/{user2_id}/workflows/{workflow_id}/execute",
        json=execute_data
    )
    assert execute_response.status_code == 404
