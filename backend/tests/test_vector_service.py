"""
Tests for the vector service functionality.
"""
import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch
from backend.app.services.vector_service import VectorService
from backend.app.services.vector_store import (
    initialize_embedding_model,
    initialize_qdrant_client,
    get_or_create_collection,
    generate_embedding,
    store_document,
    retrieve_relevant_examples
)
from backend.tests import SAMPLE_SCENARIO, SAMPLE_MESSAGES


def test_initialize_qdrant_client_success():
    """
    Test successful initialization of Qdrant client.
    
    Reasoning: Verifies the correct creation of a Qdrant client, which is essential
    for vector storage and retrieval operations.
    """
    # Mock needed dependencies
    with patch('backend.app.services.vector_store.qdrant_client.QdrantClient') as mock_client_cls:
        # Mock client instance
        
        return_val = "test"
        mock_client_cls.return_value = return_val
        
        # Mock settings
        with patch('backend.app.services.vector_store.settings.QDRANT_URL', 'http://test.url'), \
             patch('backend.app.services.vector_store.settings.QDRANT_API_KEY', 'test_key'):
            # Call the function
            client = initialize_qdrant_client()
            
            # Assertions
            mock_client_cls.assert_called_once_with(url='http://test.url', api_key='test_key')
            assert client == return_val

def test_initialize_qdrant_client_failure():
    """
    Test Qdrant client initialization failure.
    
    Reasoning: Verifies that the function handles failures gracefully, returning None
    instead of raising exceptions, ensuring fault tolerance.
    """
    # Force an exception
    with patch('backend.app.services.vector_store.qdrant_client.QdrantClient', 
               side_effect=Exception("Connection error")):
        client = initialize_qdrant_client()
        assert client is None

def test_get_or_create_collection_success():
    """
    Test successful retrieval or creation of a collection.
    
    Reasoning: Verifies that the function correctly interacts with the Qdrant client
    to get or create a collection. This is a prerequisite for storage operations.
    """
    # Create mock client and collection structures
    mock_client = MagicMock()
    mock_collection = MagicMock()
    
    # Mock the get_collections method
    mock_client.get_collections.return_value.collections = [
        MagicMock(name="existing_collection")
    ]
    
    # Test with existing collection
    with patch('backend.app.services.vector_store.settings.COLLECTION_NAME', 'existing_collection'):
        collection_name = get_or_create_collection(mock_client, "existing_collection")
        assert collection_name == "existing_collection"
        mock_client.create_collection.assert_called_once()
    
    # Test with new collection
    mock_client.get_collections.return_value.collections = [
        MagicMock(name="some_other_collection")
    ]

    with patch('backend.app.services.vector_store.settings.EMBEDDING_DIMENSION', 768):
        collection_name = get_or_create_collection(mock_client, "new_collection")
        assert collection_name == "new_collection"
        mock_client.create_collection.call_count == 2

def test_get_or_create_collection_failure():
    """
    Test failure in collection retrieval or creation.
    
    Reasoning: Verifies proper error handling when the client is None or when the
    operation fails. This helps prevent cascading failures.
    """
    # Test with None client
    collection = get_or_create_collection(None, "test_collection")
    assert collection is None
    
    # Test with exception
    mock_client = MagicMock()
    mock_client.get_collections.side_effect = Exception("Collection error")
    collection = get_or_create_collection(mock_client, "test_collection")
    assert collection is None

def test_store_document_success():
    """
    Test successful document storage.
    
    Reasoning: Verifies that documents are correctly embedded and stored in the
    vector database, which is essential for later retrieval.
    """
    # Mocks
    mock_client = MagicMock()
    mock_embeddings = [0.1, 0.2, 0.3]
    test_doc_id = "test_doc_1"
    test_text = "This is a test document"
    test_metadata = {"source": "test", "category": "unit_test"}
    test_collection = "test_collection"
    
    with patch('backend.app.services.vector_store.generate_embedding', return_value=mock_embeddings) as mock_embed, \
         patch('backend.app.services.vector_store.settings.EMBEDDING_MODEL_NAME', 'test-model'):
        # Call the real function - not through VectorService
        result = store_document(mock_client, test_collection, test_doc_id, test_text, test_metadata)
        
        # Assertions
        mock_embed.assert_called_once_with(test_text, 'test-model')
        mock_client.upsert.assert_called_once()
        assert result is True

def test_store_document_embedding_failure():
    """
    Test document storage with embedding failure.
    
    Reasoning: Verifies that the function handles embedding failures correctly,
    which is important for fault tolerance in the storage pipeline.
    """
    # Mocks
    mock_client = MagicMock()
    test_doc_id = "test_doc_1"
    test_text = "This is a test document"
    test_metadata = {"source": "test", "category": "unit_test"}
    test_collection = "test_collection"
    
    # Simulate embedding failure
    with patch('backend.app.services.vector_store.generate_embedding', return_value=None) as mock_embed, \
         patch('backend.app.services.vector_store.settings.EMBEDDING_MODEL_NAME', 'test-model'):
        # Call the real function - not through VectorService
        result = store_document(mock_client, test_collection, test_doc_id, test_text, test_metadata)
        
        # Assertions
        mock_embed.assert_called_once_with(test_text, 'test-model')
        mock_client.upsert.assert_not_called()
        assert result is False

@pytest.mark.asyncio
async def test_vector_service_retrieve_examples_success():
    """
    Test successful retrieval of examples via the VectorService class.
    
    Reasoning: Verifies that the VectorService correctly interfaces with the
    underlying vector store functions to retrieve relevant examples.
    """
    # Mock data
    mock_client = MagicMock()
    mock_collection_name = "test_collection"
    
    # Expected results from retrieve_relevant_examples
    expected_results = {
        "ids": ["id1", "id2"],
        "scores": [0.9, 0.8],
        "payloads": [{"meta1": "value1"}, {"meta2": "value2"}],
        "documents": ["doc1", "doc2"]
    }
    
    # Create service instance with mocks
    vector_service = VectorService(
        qdrant_client=mock_client,
        collection_name=mock_collection_name
    )
    
    # Mock the underlying function
    with patch('backend.app.services.vector_store.retrieve_relevant_examples', return_value=expected_results) as mock_retrieve:
        results = await vector_service.retrieve_relevant_examples(
            user_input="test query",
            conversation_history=SAMPLE_MESSAGES,
            scenario=SAMPLE_SCENARIO,
            n_results=3
        )
        
        # Assertions
        mock_retrieve.assert_called_once_with(
            client=mock_client,
            collection_name=mock_collection_name,
            user_input="test query",
            conversation_history=SAMPLE_MESSAGES,
            scenario=SAMPLE_SCENARIO,
            n_results=3
        )
        assert results == expected_results

@pytest.mark.asyncio
async def test_vector_service_retrieve_examples_missing_resources():
    """
    Test example retrieval with missing resources.
    
    Reasoning: Verifies that VectorService gracefully handles the case where
    client or collection is not initialized, preventing cascading failures.
    """
    # Create service with missing resources
    vector_service = VectorService(qdrant_client=None)
    
    results = await vector_service.retrieve_relevant_examples(
        user_input="test query",
        conversation_history=SAMPLE_MESSAGES,
        scenario=SAMPLE_SCENARIO
    )
    
    # Should return empty dict when resources not available
    assert results == {}

@pytest.mark.asyncio
async def test_vector_service_retrieve_examples_error():
    """
    Test error handling during example retrieval.
    
    Reasoning: Verifies that errors during retrieval are caught and handled
    appropriately, returning an empty result rather than failing.
    """
    # Mock data
    mock_client = MagicMock()
    mock_collection_name = "test_collection"
    
    # Create service instance with mocks
    vector_service = VectorService(
        qdrant_client=mock_client,
        collection_name=mock_collection_name
    )
    
    # Mock the underlying function to raise exception
    with patch('backend.app.services.vector_store.retrieve_relevant_examples', 
               side_effect=Exception("Retrieval error")) as mock_retrieve:
        results = await vector_service.retrieve_relevant_examples(
            user_input="test query",
            conversation_history=SAMPLE_MESSAGES,
            scenario=SAMPLE_SCENARIO
        )
        
        # Assertions
        mock_retrieve.assert_called_once()
        assert results == {} 