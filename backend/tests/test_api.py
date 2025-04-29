"""
Tests for the API endpoints.
"""
import pytest
from fastapi import status
from backend.schema import ScenarioIDResponse
from unittest.mock import patch, AsyncMock
from backend.app.services.scenarios import create_scenario, scenarios_db, add_conversation_message
import asyncio

def test_create_scenario_endpoint(client, sample_scenario_data):
    """Test the endpoint for creating a scenario."""
    response = client.post("/api/v1/scenario", json=sample_scenario_data)
    
    # Check status code
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify response format
    data = response.json()
    assert "id" in data
    assert data["id"].startswith("conversation-")
    
    return data["id"]

def test_get_scenario_endpoint(client, sample_scenario_data):
    """Test the endpoint for retrieving a scenario."""
    # First create a scenario
    scenario_id = test_create_scenario_endpoint(client, sample_scenario_data)
    
    # Then retrieve it
    response = client.get(f"/api/v1/scenario/{scenario_id}")
    
    # Check status code
    assert response.status_code == status.HTTP_200_OK
    
    # Verify response format
    data = response.json()
    for key, value in sample_scenario_data.items():
        assert data[key] == value

def test_get_nonexistent_scenario(client):
    """Test retrieving a scenario that doesn't exist."""
    nonexistent_id = "conversation-99999999-nonexistent"
    response = client.get(f"/api/v1/scenario/{nonexistent_id}")
    
    # Should return a 404 not found
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Error message should mention the scenario ID
    assert nonexistent_id in response.json()["detail"]

@patch('backend.app.api.routes.chat.process_chat', new_callable=AsyncMock)
def test_chat_endpoint(mock_process_chat: AsyncMock, client, sample_scenario_data, sample_chat_message):
    """
    Test sending a chat message in an existing scenario.
    
    Reasoning: Verifies that the chat endpoint correctly processes user messages
    and returns appropriate AI responses. This tests the integration between
    the API layer and the underlying chat service.
    """
    # First create a scenario
    scenario_id = create_scenario(sample_scenario_data)
    assert scenario_id in scenarios_db, f"Scenario {scenario_id} NOT found in scenarios_db immediately after creation!"
    client.app.state.embedding_model = None
    client.app.state.chroma_client = None

    # Define the mock return value BEFORE making the API call
    mock_process_chat.return_value = {
        "response": "This is a mocked AI response.",
        "status": "success"
    }
    
    payload = {
        "scenario_id": scenario_id,
        "user_input": sample_chat_message["content"]
    }

    response = client.post("/api/v1/process_chat", json=payload)

    mock_process_chat.assert_called_once()
    assert response.status_code == status.HTTP_200_OK
    
    # Verify response format
    data = response.json()
    assert data["content"] == "This is a mocked AI response."

def test_chat_nonexistent_scenario(client, sample_chat_message):
    """
    Test sending a chat message to a nonexistent scenario.
    
    Reasoning: Verifies that the API properly handles error cases,
    specifically when trying to chat in a scenario that doesn't exist.
    This tests error handling in the API layer.
    """
    nonexistent_id = "conversation-99999999-nonexistent"
    
    payload = {
        "scenario_id": nonexistent_id,
        "user_input": sample_chat_message["content"]
    }
    response = client.post("/api/v1/process_chat", json=payload)
    
    # Should handle missing scenarios appropriately
    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch('backend.app.api.routes.assessment.generate_conversation_assessment', new_callable=AsyncMock)
def test_assessment_endpoint(mock_generate_conversation_assessment: AsyncMock, client, sample_scenario_data, sample_conversation):
    """
    Test generating an assessment for a conversation.
    
    Reasoning: Verifies that the assessment endpoint correctly analyzes
    a conversation history and returns structured feedback. This tests the
    integration between the API layer and the assessment service.
    """
    scenario_id = create_scenario(sample_scenario_data)
    assert scenario_id in scenarios_db, f"Scenario {scenario_id} NOT found in scenarios_db immediately after creation!"
    
    
    for message in sample_conversation:
        add_conversation_message(scenario_id, message)

    mock_generate_conversation_assessment.return_value = {
        "assessment": {
            "primary_archetype": "This is a mocked assessment.",
            "secondary_archetype": "This is a mocked assessment.",
            "strengths": "This is a mocked assessment.",
            "weaknesses": "This is a mocked assessment.",
            "justification": "This is a mocked assessment.",
            "highlights": ["This is a mocked assessment.", "This is a mocked assessment."],
            "cringe_moments": ["This is a mocked assessment.", "This is a mocked assessment."],
            "raw_text_response": "This is a mocked assessment.",
        },
        "status": "success"
    }

    # Request an assessment
    response = client.post(f"/api/v1/conversation/{scenario_id}/assess")
    
    assert mock_generate_conversation_assessment.call_count == 1

    # Check status code
    assert response.status_code == status.HTTP_200_OK
    
    # Verify response format
    assessment = response.json()
    # Verify assessment structure
    
    assert "primary_archetype" in assessment
    assert "secondary_archetype" in assessment
    assert "strengths" in assessment
    assert "weaknesses" in assessment
    assert "justification" in assessment
    assert "highlights" in assessment
    assert "cringe_moments" in assessment
    assert "raw_text_response" in assessment
    assert assessment["primary_archetype"] == "This is a mocked assessment."

def test_assessment_nonexistent_scenario(client):
    """
    Test generating an assessment for a nonexistent scenario.
    
    Reasoning: Verifies that the API properly handles error cases,
    specifically when trying to assess a scenario that doesn't exist.
    This tests error handling in the API layer.
    """
    nonexistent_id = "conversation-99999999-nonexistent"
    
    response = client.post(f"/api/v1/conversation/{nonexistent_id}/assess")
    
    # Should handle missing scenarios appropriately
    assert response.status_code == status.HTTP_404_NOT_FOUND 