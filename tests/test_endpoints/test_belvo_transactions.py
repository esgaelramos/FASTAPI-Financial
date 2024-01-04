"""Tests for Belvo Transactions EndPoints for the FastAPI-Financial app."""

from unittest.mock import Mock, patch

import pytest
from requests import HTTPError
from fastapi.testclient import TestClient
from src.main import app
from src.belvo.client import Client
from src.belvo.http import APISession

client = TestClient(app)


@pytest.fixture
def mock_belvo_client():
    """Mock for Belvo Client in Tests.

    This mock is used to avoid making requests to the Belvo API.
    Need assign values for the APISession.login and APISession.get methods.
    And also simulate the Client instance, used for inject in EndPoints.
    """
    with patch.object(APISession, 'login', return_value=True), \
         patch.object(APISession, '_get') as mock_get, \
         patch.object(APISession, 'get') as mock_get_detail, \
         patch('src.belvo.instance.get_belvo_client') as mock_client:

        # Config mocks for APISession GET methods
        mock_get.return_value = {
            "results": [{"id": "123", "name": "Test Transaction"}],
            "next": None
        }
        mock_get_detail.return_value = {
            "id": "123", "name": "Test Transaction"
        }

        # Instance fake Client
        mock_client_instance = Client("fake_id", "fake_password", "fake_url")
        mock_client.return_value = mock_client_instance

        yield mock_client_instance


@pytest.fixture
def mock_belvo_client_with_error():
    """Mock for Belvo Client in Tests, raise HTTPError."""
    with patch.object(APISession, 'login', return_value=True), \
            patch.object(APISession, '_get', side_effect=HTTPError(
                response=Mock(status_code=404,
                              json=lambda: {"error": "Not found"})
            )), \
         patch('src.belvo.instance.get_belvo_client') as mock_client:

        mock_client_instance = Client("fake_id", "fake_password", "fake_url")
        mock_client.return_value = mock_client_instance

        yield mock_client_instance


def test_endpoint_transaction_get_list(mock_belvo_client):
    """Test for getting a list of Belvo Transactions."""
    response = client.get(
        "/v1/belvo/transactions",
        params={"page": 1, "account": "123", "link": "123"}
    )

    assert response.status_code == 200
    assert "transactions" in response.json()["data"]
    assert response.json()["data"]["transactions"][0]["id"] == "123"
    assert response.json()["data"]["transactions"][0]["name"] == \
        "Test Transaction"


def test_endpoint_transaction_get_http_error(mock_belvo_client_with_error):
    """Test for handling HTTPError when getting Belvo Transaction by ID."""
    response = client.get(
        "/v1/belvo/transactions", params={"id": "nonexistent_id"}
    )

    assert response.status_code == 500
    assert "success" in response.json()
    assert not response.json()["success"]
    assert "message" in response.json()
    assert response.json()["message"] == "404: {'error': 'Not found'}"


def test_endpoint_transaction_get_error(mock_belvo_client_with_error):
    """Test for getting Belvo Transaction by ID with error."""
    response = client.get("/v1/belvo/transactions", params={"id": "999"})

    assert response.status_code == 500
    assert "success" in response.json()
    assert not response.json()["success"]
    assert "message" in response.json()
