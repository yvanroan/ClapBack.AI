"""
Tests for the assessment service functionality.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.services.assessments import (
    format_assessment_prompt,
    generate_conversation_assessment,
    load_archetype_definitions, 
    load_conversation_aspects
)
from backend.app.utils.cleaner import clean_gemini_output
from backend.tests import SAMPLE_SCENARIO, SAMPLE_MESSAGES
from backend.data import ARCHETYPES_FILE

@pytest.mark.asyncio
async def test_load_archetype_definitions():
    """
    Test loading and formatting archetype definitions.

    Reasoning: Verifies that archetype definitions are loaded from the source
    and formatted correctly into a string for the prompt.
    """
    # Ensure the archetypes file exists first
    import os
    assert os.path.exists(ARCHETYPES_FILE)
    
    definitions = await load_archetype_definitions()
    
    assert isinstance(definitions, str)
    assert len(definitions) > 0
    # Check for expected structure (e.g., presence of known archetype names)
    assert "Rizz God" in definitions
    assert "NPC Vibes" in definitions
    assert ":" in definitions # Check for key: description format

@pytest.mark.asyncio
async def test_load_conversation_aspects():
    """
    Test loading and formatting conversation aspects.

    Reasoning: Verifies that conversation aspects are loaded and formatted
    correctly, including descriptions and good/bad examples, for the prompt.
    """
    import os
    assert os.path.exists(ARCHETYPES_FILE)
    
    aspects = await load_conversation_aspects()
    
    assert isinstance(aspects, str)
    assert len(aspects) > 0
    # Check for expected structure
    assert "Vocal Swagger" in aspects
    assert "Good:" in aspects
    assert "Bad:" in aspects

@pytest.mark.asyncio
async def test_format_assessment_prompt():
    """
    Test the formatting of the assessment prompt.

    Reasoning: Ensures the final prompt includes history, definitions, and aspects,
    as this structure is critical for the LLM to generate a good assessment.
    """
    # Mock the helper functions to provide predictable output
    mock_definitions = "Mock Archetype Definitions"
    mock_aspects = "Mock Conversation Aspects"
    
    #i use patch here because the functionality that i want to test is not the load_archetype_definitions 
    #or load_conversation_aspects functions, but the format_assessment_prompt function
    with patch('backend.app.services.assessments.load_archetype_definitions', 
               return_value=mock_definitions),\
         patch('backend.app.services.assessments.load_conversation_aspects', 
               return_value=mock_aspects):
        
        formatted_prompt = await format_assessment_prompt(
            conversation_history=SAMPLE_MESSAGES,
            scenario_data=SAMPLE_SCENARIO # Scenario data isn't directly used in formatting but passed
        )
        
        assert isinstance(formatted_prompt, str)
        assert len(formatted_prompt) > 0
        # Check that mocked definitions and aspects are included
        assert mock_definitions in formatted_prompt
        assert mock_aspects in formatted_prompt
        # Check that history is included (e.g., content from a sample message)
        assert SAMPLE_MESSAGES[0]["content"] in formatted_prompt
        assert SAMPLE_MESSAGES[1]["content"] in formatted_prompt

@pytest.mark.asyncio
async def test_generate_assessment_success():
    """
    Test successful generation and parsing of an assessment.

    Reasoning: Verifies the happy path: prompt is formatted, LLM responds with
    valid JSON-like text, cleaner parses it, and a successful result is returned.
    """
    mock_prompt = "Formatted assessment prompt"
    mock_raw_llm_response = "{\"primary_archetype\": \"Rizz God\", \"strengths\": \"Good flow\"}" # Simplified JSON string
    mock_parsed_assessment = {"primary_archetype": "Rizz God", "strengths": "Good flow"}
    
    # Mock dependencies
    mock_chat_model = AsyncMock()
    mock_chat_model.generate_content_async.return_value = AsyncMock(text=mock_raw_llm_response)
    
    with patch('backend.app.services.assessments.format_assessment_prompt', 
               return_value=mock_prompt) as mock_format,\
         patch('backend.app.services.assessments.clean_gemini_output', 
               return_value=mock_parsed_assessment) as mock_cleaner:
        
        result = await generate_conversation_assessment(
            conversation_history=SAMPLE_MESSAGES,
            scenario_data=SAMPLE_SCENARIO,
            chat_model=mock_chat_model
        )
        
        # Assertions
        mock_format.assert_awaited_once_with(SAMPLE_MESSAGES, SAMPLE_SCENARIO)
        mock_chat_model.generate_content_async.assert_awaited_once_with(mock_prompt)
        mock_cleaner.assert_called_once_with(mock_raw_llm_response)
        
        assert result.get("status") == "success"
        assert "assessment" in result
        # Compare assessment content
        assert result["assessment"]["primary_archetype"] == mock_parsed_assessment["primary_archetype"]
        assert result["assessment"]["strengths"] == mock_parsed_assessment["strengths"]

@pytest.mark.asyncio
async def test_generate_assessment_parsing_failure():
    """
    Test handling of LLM response parsing failure.

    Reasoning: Ensures that if the LLM response is malformed and the cleaner fails,
    the function returns a proper error status and includes the raw text.
    """
    mock_prompt = "Formatted assessment prompt for parsing failure"
    mock_raw_llm_response = "This is not JSON { definitely not parsable" 
    
    # Mock dependencies
    mock_chat_model = AsyncMock()
    mock_chat_model.generate_content_async.return_value = AsyncMock(text=mock_raw_llm_response)
    
    # Mock cleaner to return None, simulating parsing failure
    with patch('backend.app.services.assessments.format_assessment_prompt', 
               return_value=mock_prompt),\
         patch('backend.app.services.assessments.clean_gemini_output', 
               return_value=None) as mock_cleaner:
        
        result = await generate_conversation_assessment(
            conversation_history=SAMPLE_MESSAGES,
            scenario_data=SAMPLE_SCENARIO,
            chat_model=mock_chat_model
        )
        
        # Assertions
        mock_cleaner.assert_called_once_with(mock_raw_llm_response)
        assert result.get("status") == "error"
        assert "error" in result
        assert "Failed to parse assessment response" in result.get("error")
        assert "raw_text_response" in result
        assert result["raw_text_response"] == mock_raw_llm_response # Check raw text is preserved

@pytest.mark.asyncio
async def test_generate_assessment_llm_error():
    """
    Test handling of errors during LLM interaction.

    Reasoning: Verifies that if the call to the LLM fails (e.g., network issue),
    the exception is caught and an appropriate error result is returned.
    """
    mock_prompt = "Formatted assessment prompt for LLM error"
    llm_error = Exception("LLM API Error")
    
    # Mock dependencies
    mock_chat_model = AsyncMock()
    mock_chat_model.generate_content_async.side_effect = llm_error # Make LLM call raise an error
    
    with patch('backend.app.services.assessments.format_assessment_prompt', 
               return_value=mock_prompt):
        
        result = await generate_conversation_assessment(
            conversation_history=SAMPLE_MESSAGES,
            scenario_data=SAMPLE_SCENARIO,
            chat_model=mock_chat_model
        )
        
        # Assertions
        assert result.get("status") == "error"
        assert "error" in result
        assert str(llm_error) in result.get("error") # Check original error is in message
        # raw_text should be accessible but could be None (depending on when error occurs)
        assert "raw_text_response" in result
