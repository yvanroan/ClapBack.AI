"""
Tests for the scenario service functionality.
"""
import pytest
import json
from backend.app.services import (
    create_scenario,
    get_scenario,
    add_conversation_message,
    get_conversation_history,
    generate_scenario_id
)
from backend.tests import SAMPLE_SCENARIO, SAMPLE_MESSAGES

def test_scenario_id_generation():
    """Test that scenario IDs are generated with the expected format."""
    scenario_id = generate_scenario_id()
    
    # Check format: conversation-{timestamp}-{uuid}
    assert scenario_id.startswith("conversation-")
    parts = scenario_id.split("-")
    assert len(parts) >= 3  # At least 3 parts
    
    # Timestamp should be numeric
    assert parts[1].isdigit()
    
    return scenario_id

def test_scenario_creation_and_retrieval():
    """Test creating and retrieving a scenario."""
    # Create scenario using common test data
    scenario_id = create_scenario(SAMPLE_SCENARIO)
    
    # Verify ID format
    assert scenario_id.startswith("conversation-")
    
    # Retrieve scenario
    retrieved_scenario = get_scenario(scenario_id)
    
    # Verify data matches
    for key, value in SAMPLE_SCENARIO.items():
        assert retrieved_scenario.get(key) == value
        
    return scenario_id

def test_conversation_messages():
    """Test adding and retrieving conversation messages."""
    # Create a scenario first
    scenario_id = test_scenario_creation_and_retrieval()
    
    # Add messages from common test data
    for message in SAMPLE_MESSAGES:
        success = add_conversation_message(scenario_id, message)
        assert success is True
    
    # Retrieve conversation history
    history = get_conversation_history(scenario_id)
    
    # Verify messages
    assert len(history) == len(SAMPLE_MESSAGES)
    for i, message in enumerate(SAMPLE_MESSAGES):
        assert history[i]["role"] == message["role"]
        assert history[i]["content"] == message["content"]

def test_nonexistent_scenario():
    """Test retrieving a scenario that doesn't exist."""
    nonexistent_id = "conversation-99999999-nonexistent"
    scenario = get_scenario(nonexistent_id)
    assert scenario is None
    
    # Test conversation operations on nonexistent scenario
    success = add_conversation_message(nonexistent_id, {"role": "user", "content": "Hello"})
    assert success is False
    
    history = get_conversation_history(nonexistent_id)
    assert history == [] 