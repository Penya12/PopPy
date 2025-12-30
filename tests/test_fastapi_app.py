import pytest
from fastapi.testclient import TestClient

from poppy.api.app import app
from poppy.core.events import EventCreate


@pytest.fixture
def test_client() -> TestClient:
    """Provides a TestClient for the FastAPI app."""
    return TestClient(app)


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
