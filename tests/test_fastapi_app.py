from fastapi.testclient import TestClient

from poppy.core.events import EventCreate


def test_read_root(test_client: TestClient) -> None:
    """Test the root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Poppy": "Your Popeye-powered secretary"}


def test_create_event_success(test_client: TestClient) -> None:
    """Test the event creation endpoint."""
    event_payload = EventCreate(
        kind="idea",
        text="Test event description",
    )
    response = test_client.post("/event", json=event_payload.model_dump(mode="json"))
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["kind"] == "idea"
    assert response_data["text"] == "Test event description"
    assert "id" in response_data


def test_create_event_missing_field(test_client: TestClient) -> None:
    """Test event creation with a missing required field."""
    event_payload = {
        "text": "Missing kind field",
    }
    response = test_client.post("/event", json=event_payload)
    assert response.status_code == 422  # Unprocessable Entity
    response_data = response.json()
    assert response_data["detail"][0]["input"]["text"] == "Missing kind field"


def test_get_events_in_week_empty(test_client: TestClient) -> None:
    """Test retrieving events for the current week when no events exist."""
    response = test_client.get("/event/week")
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 0


def test_get_events_in_week_with_events(test_client: TestClient) -> None:
    """Test retrieving events for the current week when events exist."""
    # First, create an event
    event_payload = EventCreate(
        kind="action",
        text="Set Weekly meeting",
    )
    create_response = test_client.post("/event", json=event_payload.model_dump(mode="json"))
    assert create_response.status_code == 201

    # Now, retrieve events for the current week
    response = test_client.get("/event/week")
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == 1  # At least one event should be present
    assert any(event["text"] == "Set Weekly meeting" for event in response_data)
