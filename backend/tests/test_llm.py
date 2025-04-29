"""
Tests for the LLM service functionality.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.app.services.llm import (
    initialize_gemini,
    get_chat_model,
    start_chat_session,
    generate_text,
    process_chat_with_context
)
from backend.tests import SAMPLE_MESSAGES


def test_start_chat_session():
    """
    Test starting a chat session.
    
    Reasoning: Verifies that a chat session is created correctly with the
    GenerativeModel, optionally including history. This is essential for
    maintaining context in conversations.
    """
    # Mock objects
    mock_model = MagicMock()
    mock_chat = MagicMock()
    mock_model.start_chat.return_value = mock_chat
    
    test_history = [{"role": "user", "parts": "Hello"}, {"role": "model", "parts": "Hi there!"}]
    
    # Test with provided model and history
    session1 = start_chat_session(model=mock_model, history=test_history)
    mock_model.start_chat.assert_called_with(history=test_history)
    assert session1 == mock_chat
    
    # Test with provided model but default history
    mock_model.start_chat.reset_mock()
    session2 = start_chat_session(model=mock_model)
    mock_model.start_chat.assert_called_with(history=[])  # Default is empty list
    
    # Test with default model (need to mock get_chat_model)
    with patch('backend.app.services.llm.gemini.get_chat_model') as mock_get_model:
        mock_default_model = MagicMock()
        mock_get_model.return_value = mock_default_model
        mock_default_model.start_chat.return_value = mock_chat
        
        session3 = start_chat_session()
        mock_get_model.assert_called_once()
        mock_default_model.start_chat.assert_called_with(history=[])

@pytest.mark.asyncio
async def test_generate_text_success():
    """
    Test successful text generation with the LLM.
    
    Reasoning: Verifies that the function correctly sends the prompt to the model
    and returns the expected response format on success.
    """
    # Test data
    test_prompt = "Tell me a short story"
    test_response_text = "Once upon a time, in a land far away..."
    
    # Mock objects
    mock_response = MagicMock()
    mock_response.text = test_response_text
    
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    
    # Patch dependencies
    with patch('backend.app.services.llm.gemini.genai.GenerativeModel', return_value=mock_model) as mock_model_cls:
        result = await generate_text(test_prompt)
        
        # Assertions
        mock_model_cls.assert_called_once_with('gemini-2.0-flash')  # Default model
        mock_model.generate_content.assert_called_once_with(test_prompt)
        
        assert result["status"] == "success"
        assert result["text"] == test_response_text

@pytest.mark.asyncio
async def test_generate_text_custom_model():
    """
    Test text generation with a custom model.
    
    Reasoning: Verifies that the function respects the requested model name,
    which is important for flexibility in choosing different models based on needs.
    """
    # Test data
    test_prompt = "Summarize this paragraph"
    test_model = "gemini-1.5-pro"
    
    # Mock objects
    mock_response = MagicMock()
    mock_response.text = "Summary text"
    
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    
    # Patch dependencies
    with patch('backend.app.services.llm.gemini.genai.GenerativeModel', return_value=mock_model) as mock_model_cls:
        result = await generate_text(test_prompt, model_name=test_model)
        
        # Assertions
        mock_model_cls.assert_called_once_with(test_model)  # Should use custom model
        assert result["status"] == "success"

@pytest.mark.asyncio
async def test_generate_text_error():
    """
    Test error handling during text generation.
    
    Reasoning: Verifies that the function correctly handles errors from the LLM
    and returns an appropriate error response rather than crashing.
    """
    # Test data
    test_prompt = "Generate some text"
    test_error = Exception("API quota exceeded")
    
    # Patch dependencies to raise an exception
    with patch('backend.app.services.llm.gemini.genai.GenerativeModel') as mock_model_cls:
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_model.generate_content.side_effect = test_error
        
        result = await generate_text(test_prompt)
        
        # Assertions
        assert result["status"] == "error"
        assert "error" in result
        assert str(test_error) in result["error"]
        assert "Error generating text" in result["text"]

@pytest.mark.asyncio
async def test_process_chat_with_context():
    """
    Test processing a chat with context.
    
    Reasoning: Verifies that the function correctly processes a user message
    with conversation history, system prompt, and relevant context. This tests
    the high-level chat processing logic.
    
    Note: This is testing a placeholder implementation based on the code review.
    The actual implementation may need different tests.
    """
    # Test data
    user_message = "Hello there"
    system_prompt = "You are a helpful assistant"
    relevant_context = "The user is interested in AI"
    
    # Mock dependencies
    mock_session = MagicMock()
    
    with patch('backend.app.services.llm.gemini.get_chat_model') as mock_get_model, \
         patch('backend.app.services.llm.gemini.start_chat_session', return_value=mock_session) as mock_start_session:
        
        # Call the function
        result = await process_chat_with_context(
            user_message=user_message,
            conversation_history=SAMPLE_MESSAGES,
            system_prompt=system_prompt,
            relevant_context=relevant_context
        )
        
        # Assertions
        mock_get_model.assert_called_once()
        mock_start_session.assert_called_once()
        
        # Since the implementation is a placeholder, we just verify the basic response structure
        assert "response" in result
        assert "status" in result
        assert result["status"] == "success"

@pytest.mark.asyncio
async def test_process_chat_with_context_error():
    """
    Test error handling in chat processing.
    
    Reasoning: Verifies that the function handles errors appropriately during
    chat processing, returning an error response rather than crashing.
    """
    # Test data
    user_message = "Hello there"
    system_prompt = "You are a helpful assistant"
    
    # Mock dependencies to raise an exception
    with patch('backend.app.services.llm.gemini.get_chat_model', side_effect=Exception("Session error")):
        
        # Call the function
        result = await process_chat_with_context(
            user_message=user_message,
            conversation_history=SAMPLE_MESSAGES,
            system_prompt=system_prompt
        )
        
        # Assertions
        assert "response" in result
        assert "status" in result
        assert result["status"] == "error"
        assert "error" in result
        assert "Session error" in result["error"] 