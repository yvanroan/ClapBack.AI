"""
Tests for conversation management edge cases
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from backend.app.services.scenarios import (
    create_scenario,
    get_scenario,
    add_conversation_message,
    get_conversation_history
)


def test_nonexistent_scenario_access():
    """
    Test access to a non-existent scenario.
    
    This verifies that the application gracefully handles attempts
    to access scenarios that don't exist.
    """
    # Mock the scenarios_db dictionary to be empty
    with patch('backend.app.services.scenarios.scenarios_db', {}):
        # Attempt to get a scenario that doesn't exist
        scenario = get_scenario("nonexistent-id")
        assert scenario is None


def test_very_long_conversation_history():
    """
    Test handling of very long conversation histories.
    
    This verifies that the application can handle extremely large
    conversation histories without performance issues.
    """
    scenario_id = "test-scenario"
    
    # Create a mock scenarios_db with an existing scenario
    mock_db = {
        scenario_id: {
            "scenario_data": {"type": "test"},
            "conversation_history": []
        }
    }
    
    # Generate a large number of messages (100)
    many_messages = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
        for i in range(100)
    ]
    
    with patch('backend.app.services.scenarios.scenarios_db', mock_db):
        # Add all messages to the conversation
        for message in many_messages:
            success = add_conversation_message(scenario_id, message)
            assert success is True
        
        # Retrieve the conversation history
        history = get_conversation_history(scenario_id)
        assert len(history) == 100
        assert history[0]["content"] == "Message 0"
        assert history[99]["content"] == "Message 99"


def test_malformed_message_handling():
    """
    Test handling of malformed messages in conversation history.
    
    This verifies that the application can process messages with
    missing or malformed fields without crashing.
    """
    scenario_id = "test-scenario"
    
    # Create a mock scenarios_db with an existing scenario
    mock_db = {
        scenario_id: {
            "scenario_data": {"type": "test"},
            "conversation_history": []
        }
    }
    
    with patch('backend.app.services.scenarios.scenarios_db', mock_db):
        # Test adding messages with missing fields
        malformed_messages = [
            {},  # Empty message
            {"role": "user"},  # Missing content
            {"content": "Hello"},  # Missing role
            {"role": "invalid", "content": "Test"}  # Invalid role
        ]
        
        for message in malformed_messages:
            # Should still succeed even with malformed messages
            success = add_conversation_message(scenario_id, message)
            assert success is True
        
        # Verify all messages were added
        history = get_conversation_history(scenario_id)
        assert len(history) == 4


@pytest.mark.asyncio
async def test_empty_conversation_assessment():
    """
    Test attempting to assess an empty conversation.
    
    This verifies that the application properly handles attempts
    to generate assessments for conversations with no messages.
    """
    from backend.app.api.routes.assessment import get_conversation_assessment
    
    # Mock dependencies
    request = MagicMock()
    request.app.state.chat_model = MagicMock()
    
    # Mock get_scenario to return valid data
    with patch('backend.app.api.routes.assessment.get_scenario', return_value={"type": "test"}), \
         patch('backend.app.api.routes.assessment.get_conversation_history', return_value=[]):
        
        # Should raise HTTPException for empty conversation
        with pytest.raises(HTTPException) as excinfo:
            await get_conversation_assessment("test-id", request)
        
        assert excinfo.value.status_code == 400
        assert "empty conversation" in str(excinfo.value.detail).lower() 