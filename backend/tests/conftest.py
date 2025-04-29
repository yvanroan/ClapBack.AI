"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_application
from backend.tests import SAMPLE_SCENARIO, SAMPLE_MESSAGES
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture(scope="session")
def app():
    """
    Fixture to create the FastAPI application instance once per session.
    Adds a mock chat_model to the app state for testing purposes.
    """
    application = create_application()
    # --- Add a mock model to the state for tests ---
    application.state.chat_model = AsyncMock() # Add a simple mock
    # If your code also checks for embedding_model/chroma_collection in the chat route:
    application.state.embedding_model = MagicMock()
    application.state.chroma_collection = MagicMock()
    # --- End state modification ---
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