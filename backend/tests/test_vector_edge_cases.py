"""
Tests for vector database edge cases
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.vector_store import (
    generate_embedding,
    embed_text,
    retrieve_relevant_examples
)


def test_empty_text_embedding():
    """
    Test embedding generation with empty text.
    
    This verifies that the embedding generation functions handle
    empty text gracefully without crashing.
    """
    empty_text = ""
    
    # Patch genai.embed_content to return a mock response
    mock_embedding = [0.0] * 10  # Mock 10-dim embedding of zeros
    mock_response = {"embedding": mock_embedding}
    
    with patch('backend.app.services.vector_store.genai.embed_content', return_value=mock_response):
        result = generate_embedding(empty_text)
        assert result is not None
        assert len(result) == 10
        assert all(x == 0.0 for x in result)


def test_very_long_text_embedding():
    """
    Test embedding generation with very long text.
    
    This verifies that the embedding generation functions handle
    extremely long texts without crashing.
    """
    # Create a very long text (100KB)
    very_long_text = "x" * 100000
    
    # Patch genai.embed_content to simulate success with long text
    mock_embedding = [0.1] * 10  # Mock 10-dim embedding
    mock_response = {"embedding": mock_embedding}
    
    with patch('backend.app.services.vector_store.genai.embed_content', return_value=mock_response):
        result = generate_embedding(very_long_text)
        assert result is not None
        assert len(result) == 10


def test_special_characters_embedding():
    """
    Test embedding generation with special characters and emojis.
    
    This verifies that the embedding generation functions handle
    non-standard characters appropriately.
    """
    special_text = "Test with special chars: ñáéíóú 😊🚀💡 and symbols: &*()[]{}|"
    
    # Patch genai.embed_content to simulate success with special chars
    mock_embedding = [0.2] * 10  # Mock 10-dim embedding
    mock_response = {"embedding": mock_embedding}
    
    with patch('backend.app.services.vector_store.genai.embed_content', return_value=mock_response):
        result = generate_embedding(special_text)
        assert result is not None
        assert len(result) == 10


@pytest.mark.asyncio
async def test_empty_vector_database():
    """
    Test retrieval from an empty vector database.
    
    This verifies that the retrieval functions handle empty collections
    gracefully and return appropriate empty results.
    """
    # Mock collection that returns empty results
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [[]],
        "distances": [[]],
        "metadatas": [[]],
        "documents": [[]]
    }
    
    # Mock embedding generation
    with patch('backend.app.services.vector_store.generate_embedding', return_value=[0.1] * 10):
        results = retrieve_relevant_examples(
            collection=mock_collection,
            user_input="test query",
            conversation_history=[],
            scenario={"type": "test"},
            n_results=5
        )
        
        # Verify that empty results are handled properly
        assert isinstance(results, dict)
        assert "ids" in results
        assert len(results["ids"][0]) == 0 