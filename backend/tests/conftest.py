"""
Pytest configuration and fixtures.
"""
import pytest
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock, patch, AsyncMock
from backend.app import create_application
from backend.tests import SAMPLE_SCENARIO, SAMPLE_MESSAGES

@pytest.fixture(scope="session")
def app():
    # Create a test instance of the app
    application = create_application()
    # --- Add a mock model to the state for tests ---
    application.state.chat_model = AsyncMock() # Add a simple mock

    application.state.qdrant_client = MagicMock()
    application.state.collection_name = "test_collection"
    
    return application

@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture
def sample_scenario_data():
    """Return sample scenario data for testing."""
    return SAMPLE_SCENARIO.copy()

@pytest.fixture
def sample_chat_message():
    """Return a sample chat message for testing."""
    return SAMPLE_MESSAGES[0].copy()

# @pytest.fixture(autouse=True)
# def reset_scenarios_state():
#     """
#     Automatically clears the in-memory scenarios_db before each test.
#     'autouse=True' ensures it runs for every test function.
#     """
#     scenarios_db.clear()
#     yield

@pytest.fixture
def sample_conversation():
    """Return a sample conversation history for testing."""
    return SAMPLE_MESSAGES.copy()

@pytest.fixture
def cleanup_scenarios():
    """Fixture to clean up scenarios created during testing."""
    # Setup - nothing to do here
    yield
    # Teardown - could clear the in-memory scenarios in a real implementation
    # For example: 
    # from backend.app.services.scenarios import scenarios_db
    # scenarios_db.clear()
    pass 