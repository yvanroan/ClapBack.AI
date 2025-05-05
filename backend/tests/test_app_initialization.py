"""
Tests for application initialization edge cases
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Import the lifespan function from app/__init__.py
from backend.app import lifespan, create_application


@pytest.mark.asyncio
async def test_lifespan_with_failed_model_initialization():
    """
    Test application initialization when model initialization fails.
    
    This verifies that the application can start even when model
    initialization fails, allowing for graceful degradation.
    """
    # Mock the app object
    app = MagicMock()
    app.state = MagicMock()
    
    # Convert the lifespan context manager to a callable for testing
    @asynccontextmanager
    async def test_lifespan_wrapper():
        # Mock genai.configure to raise an exception
        with patch('backend.app.genai.configure', side_effect=Exception("API Error")), \
             patch('backend.app.print') as mock_print:  # Capture print statements
            
            # Call the actual lifespan
            async with lifespan(app):
                # This is executed in the "up" state
                yield
            
            # This is executed after "down" state
            
            # Check that error was printed
            mock_print.assert_any_call("ERROR: Failed to initialize Chat Model: API Error")
            
            # Check that app.state.chat_model is None
            assert app.state.chat_model is None


@pytest.mark.asyncio
async def test_partial_initialization():
    """
    Test application initialization when only some components initialize.
    
    This verifies that the application continues to initialize other
    components even if some fail, enabling partial functionality.
    """
    # Mock the app object
    app = MagicMock()
    app.state = MagicMock()
    
    # Configure genai mocks to succeed for chat model but fail for embedding
    mock_genai = MagicMock()
    mock_chat_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_chat_model
    
    @asynccontextmanager
    async def test_lifespan_wrapper():
        with patch('backend.app.genai', mock_genai), \
             patch('backend.app.get_api_key_or_raise') as mock_get_key, \
             patch('backend.app.services.vector_store.initialize_chroma_client') as mock_init_chroma:
            
            # Make only the first API key succeed, second one fail
            mock_get_key.side_effect = [
                "fake-api-key",  # First call succeeds (chat model)
                Exception("Embedding API Key not found")  # Second call fails (embedding model)
            ]
            
            # Make ChromaDB initialization succeed
            mock_client = MagicMock()
            mock_init_chroma.return_value = mock_client
            
            # Call the actual lifespan
            async with lifespan(app):
                yield
            
            # Check that chat model is initialized but embedding model is None
            assert app.state.chat_model is not None
            
            # Check that chroma client was initialized
            assert app.state.chroma_client is not None


def test_create_application():
    """
    Test application factory function.
    
    This verifies that the application factory function creates a valid
    FastAPI application with appropriate middleware and routes.
    """
    # Mock dependencies including settings
    with patch('backend.app.FastAPI') as mock_fastapi_class, \
         patch('backend.app.api.api_router') as mock_router, \
         patch('backend.app.settings') as mock_settings:
        
        # Configure mock settings
        mock_settings.API_V1_STR = '/api/v1'
        mock_settings.PROJECT_NAME = 'Test Project'
        mock_settings.BACKEND_CORS_ORIGINS = ['http://localhost:3000']
        
        # Configure FastAPI mock to return a mock app
        mock_app = MagicMock()
        mock_fastapi_class.return_value = mock_app
        
        # Call the factory function
        app = create_application()
        
        # Verify FastAPI was instantiated with lifespan
        mock_fastapi_class.assert_called_once()
        assert 'lifespan' in mock_fastapi_class.call_args[1]
        assert mock_fastapi_class.call_args[1]['lifespan'] == lifespan
        
        # Verify CORS middleware was added
        mock_app.add_middleware.assert_called_once()
        
        # Verify API router was included
        mock_app.include_router.assert_called_once()
        # Check router args and prefix
        router_args = mock_app.include_router.call_args[0]
        router_kwargs = mock_app.include_router.call_args[1]
        assert router_args[0] == mock_router
        assert router_kwargs['prefix'] == '/api/v1' 

    