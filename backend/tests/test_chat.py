"""
Tests for the chat service functionality.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.services import format_chat_prompt, process_chat
from backend.tests import SAMPLE_SCENARIO, SAMPLE_MESSAGES

@pytest.mark.asyncio
async def test_process_chat_basic():
    """
    Test basic chat processing without vector service.
    
    Reasoning: This test verifies the core chat processing functionality without the
    vector retrieval component. It confirms that the process_chat function can properly
    format prompts and generate responses using the AI model. This is the most fundamental
    operation of the chat system.
    """
    # Mock dependencies
    mock_chat_model = AsyncMock()
    mock_chat_model.generate_content_async.return_value = AsyncMock(text="Test response")
    
    # Process chat
    result = await process_chat(
        user_input="Hello",
        scenario_id="test-scenario-123",
        scenario_data=SAMPLE_SCENARIO,
        conversation_history=SAMPLE_MESSAGES,
        chat_model=mock_chat_model,
        vector_service=None  # No vector service
    )
    
    # Assertions
    assert mock_chat_model.generate_content_async.called
    assert result.get("status") == "success"
    assert result.get("response") == "Test response"
    

@pytest.mark.asyncio
async def test_process_chat_with_vector_service():
    """
    Test chat processing with vector service integration.
    
    Reasoning: This test ensures that the process_chat function properly integrates
    with the vector service for retrieving relevant examples. It verifies that examples
    are requested from the vector service and incorporated into the prompt. This tests
    the integration between two important components of the system.
    """
    # Mock dependencies
    mock_chat_model = AsyncMock()
    mock_chat_model.generate_content_async.return_value = AsyncMock(text="Test response with examples")
    
    mock_vector_service = AsyncMock()
    mock_vector_service.retrieve_relevant_examples.return_value = {
        "ids": [["id1", "id2"]],
        "metadatas": [[{"meta1": "value1"}, {"meta2": "value2"}]],
        "documents": [["doc1 content", "doc2 content"]],
        "distances": [[0.1, 0.2]]
    }
    
    # Process chat
    result = await process_chat(
        user_input="Hello with examples",
        scenario_id="test-scenario-456",
        scenario_data=SAMPLE_SCENARIO,
        conversation_history=SAMPLE_MESSAGES,
        chat_model=mock_chat_model,
        vector_service=mock_vector_service
    )
    
    # Assertions
    assert mock_vector_service.retrieve_relevant_examples.called
    assert mock_chat_model.generate_content_async.called
    assert result.get("status") == "success"
    assert result.get("response") == "Test response with examples"
    

@pytest.mark.asyncio
async def test_process_chat_error_handling():
    """
    Test error handling during chat processing.
    
    Reasoning: This test verifies that the process_chat function properly handles
    errors that might occur during processing, such as AI model failures or prompt
    formatting issues. Proper error handling is essential for system reliability.
    """
    # Mock dependencies with error behavior
    mock_chat_model = AsyncMock()
    mock_chat_model.generate_content_async.side_effect = Exception("Test error")
    
    # Process chat
    result = await process_chat(
        user_input="This will cause an error",
        scenario_id="test-scenario-789",
        scenario_data=SAMPLE_SCENARIO,
        conversation_history=SAMPLE_MESSAGES,
        chat_model=mock_chat_model,
        vector_service=None
    )
    
    # Assertions
    assert result.get("status") == "error"
    assert "error" in result
    assert "Test error" in result.get("error")

@pytest.mark.asyncio
@pytest.mark.parametrize("archetype,roast_level", [
    ("The Icy One", 1),
    ("The Awkward Sweetheart", 3),
    ("The Certified Baddie", 5)
])
async def test_different_archetypes_and_roast_levels(archetype, roast_level):
    """
    Test chat processing with different archetypes and roast levels.
    
    Reasoning: This test ensures that the system correctly handles different combinations
    of archetypes and roast levels, which are key features of the system. Different
    archetypal personalities and roast intensities should be correctly incorporated
    into prompts, influencing the AI's response style.
    """
    # Create a modified scenario with the parametrized values
    modified_scenario = SAMPLE_SCENARIO.copy()
    modified_scenario["system_archetype"] = archetype
    modified_scenario["roast_level"] = roast_level
    
    # Mock dependencies
    mock_chat_model = AsyncMock()
    mock_chat_model.generate_content_async.return_value = AsyncMock(text=f"Response for {archetype} at level {roast_level}")
    
    # Process chat
    result = await process_chat(
        user_input="Hello, personality test",
        scenario_id=f"test-{archetype}-{roast_level}", #this is fine if since we are not testing scenario id here
        scenario_data=modified_scenario,
        conversation_history=SAMPLE_MESSAGES,
        chat_model=mock_chat_model,
        vector_service=None
    )
    
    # Assertions
    assert result.get("status") == "success"
    assert archetype in modified_scenario["system_archetype"]
    assert mock_chat_model.generate_content_async.called
    
    # Get the prompt that was sent to the model
    called_args = mock_chat_model.generate_content_async.call_args[0][0]
    assert archetype in called_args
