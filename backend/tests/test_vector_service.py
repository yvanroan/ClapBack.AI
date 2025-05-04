"""
Tests for the vector service functionality.
"""
import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch
from backend.app.services.vector_service import VectorService
from backend.app.services.vector_store import (
    initialize_embedding_model,
    initialize_chroma_client,
    get_or_create_collection,
    generate_embedding,
    store_document,
    retrieve_relevant_examples
)
from backend.tests import SAMPLE_SCENARIO, SAMPLE_MESSAGES


def test_initialize_chroma_client_success():
    """
    Test successful initialization of ChromaDB client.
    
    Reasoning: Verifies the correct creation of a ChromaDB client, which is essential
    for vector storage and retrieval operations.
    """
    # Mock needed dependencies
    with patch('backend.app.services.vector_store.os.makedirs') as mock_makedirs, \
         patch('backend.app.services.vector_store.chromadb.PersistentClient') as mock_client_cls:
        
        # Mock client instance
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Call the function
        client = initialize_chroma_client()
        
        # Assertions
        mock_makedirs.assert_called_once()
        mock_client_cls.assert_called_once()
        assert client == mock_client

def test_initialize_chroma_client_failure():
    """
    Test ChromaDB client initialization failure.
    
    Reasoning: Verifies that the function handles failures gracefully, returning None
    instead of raising exceptions, ensuring fault tolerance.
    """
    # Force an exception
    with patch('backend.app.services.vector_store.os.makedirs', side_effect=Exception("Directory error")):
        client = initialize_chroma_client()
        assert client is None

def test_get_or_create_collection_success():
    """
    Test successful retrieval or creation of a collection.
    
    Reasoning: Verifies that the function correctly interacts with the ChromaDB client
    to get or create a collection. This is a prerequisite for storage operations.
    """
    # Create mock client
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    
    # Call the function
    collection = get_or_create_collection(mock_client, "test_collection")
    
    # Assertions
    mock_client.get_or_create_collection.assert_called_once_with(name="test_collection")
    assert collection == mock_collection

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
    mock_client.get_or_create_collection.side_effect = Exception("Collection error")
    collection = get_or_create_collection(mock_client, "test_collection")
    assert collection is None



def test_store_document_success():
    """
    Test successful document storage.
    
    Reasoning: Verifies that documents are correctly embedded and stored in the
    vector database, which is essential for later retrieval.
    """
    # Mocks
    mock_collection = MagicMock()
    mock_embeddings = [0.1, 0.2, 0.3]
    test_doc_id = "test_doc_1"
    test_text = "This is a test document"
    test_metadata = {"source": "test", "category": "unit_test"}
    
    with patch('backend.app.services.vector_store.generate_embedding', return_value=mock_embeddings) as mock_embed, \
         patch('backend.app.services.vector_store.settings.EMBEDDING_MODEL_NAME', 'test-model'):
        # Call the real function - not through VectorService
        result = store_document(mock_collection, test_doc_id, test_text, test_metadata)
        
        # Assertions
        mock_embed.assert_called_once_with(test_text, 'test-model')
        mock_collection.add.assert_called_once_with(
            ids=[test_doc_id],
            embeddings=[mock_embeddings],
            documents=[test_text],
            metadatas=[test_metadata]
        )
        assert result is True

def test_store_document_embedding_failure():
    """
    Test document storage with embedding failure.
    
    Reasoning: Verifies that the function handles embedding failures correctly,
    which is important for fault tolerance in the storage pipeline.
    """
    # Mocks
    mock_collection = MagicMock()
    test_doc_id = "test_doc_1"
    test_text = "This is a test document"
    test_metadata = {"source": "test", "category": "unit_test"}
    
    # Simulate embedding failure
    with patch('backend.app.services.vector_store.generate_embedding', return_value=None) as mock_embed, \
         patch('backend.app.services.vector_store.settings.EMBEDDING_MODEL_NAME', 'test-model'):
        # Call the real function - not through VectorService
        result = store_document(mock_collection, test_doc_id, test_text, test_metadata)
        
        # Assertions
        mock_embed.assert_called_once_with(test_text, 'test-model')
        mock_collection.add.assert_not_called()
        assert result is False

@pytest.mark.asyncio
async def test_vector_service_retrieve_examples_success():
    """
    Test successful retrieval of examples via the VectorService class.
    
    Reasoning: Verifies that the VectorService correctly interfaces with the
    underlying vector store functions to retrieve relevant examples.
    """
    # Mock data
    mock_collection = MagicMock()
    
    # Expected results from retrieve_relevant_examples
    expected_results = {
        "ids": [["id1", "id2"]],
        "metadatas": [[{"meta1": "value1"}, {"meta2": "value2"}]],
        "documents": [["doc1", "doc2"]],
        "distances": [[0.1, 0.2]]
    }
    
    # Create service instance with mocks
    vector_service = VectorService(
        chroma_collection=mock_collection
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
            collection=mock_collection,
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
    embedding model or collection is not initialized, preventing cascading failures.
    """
    # Create service with missing resources
    vector_service = VectorService(chroma_collection=None)
    
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
    mock_collection = MagicMock()
    
    # Create service instance with mocks
    vector_service = VectorService(
        chroma_collection=mock_collection
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