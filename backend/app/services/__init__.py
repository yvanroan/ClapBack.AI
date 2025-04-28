"""
Service layer module for the ChatMatch application.

This module provides access to the various services that manage business logic, 
including scenario management, chat processing, assessments, and vector operations.
"""

# Import and expose key services from scenarios module
from backend.app.services.scenarios import (
    create_scenario,
    get_scenario,
    add_conversation_message,
    get_conversation_history,
    generate_scenario_id
)

# Import and expose chat services
from backend.app.services.chat import (
    format_chat_prompt,
    process_chat
)

# Import and expose assessment services
from backend.app.services.assessments import (
    generate_conversation_assessment,
    format_assessment_prompt,
    load_archetypes_data,
    load_archetype_definitions,
    load_conversation_aspects
)

# Import and expose vector store services
from backend.app.services.vector_store import (
    initialize_embedding_model,
    initialize_chroma_client,
    get_or_create_collection,
    generate_embedding,
    embed_text,
    store_document,
    process_and_store_blocks,
    retrieve_relevant_examples
)

# Import VectorService class
from backend.app.services.vector_service import VectorService

# Import LLM services
from backend.app.services.llm import (
    initialize_gemini,
    get_chat_model,
    start_chat_session,
    generate_text,
    process_chat_with_context
)

# Export all services for simplified imports
__all__ = [
    # Scenario services
    'create_scenario',
    'get_scenario',
    'add_conversation_message',
    'get_conversation_history',
    'generate_scenario_id',
    
    # Chat services
    'format_chat_prompt',
    'process_chat',
    
    # Assessment services
    'generate_conversation_assessment',
    'format_assessment_prompt',
    'load_archetypes_data',
    'load_archetype_definitions',
    'load_conversation_aspects',
    
    # Vector store services
    'initialize_embedding_model',
    'initialize_chroma_client',
    'get_or_create_collection',
    'generate_embedding',
    'embed_text',
    'store_document',
    'process_and_store_blocks',
    'retrieve_relevant_examples',
    'VectorService',
    
    # LLM services
    'initialize_gemini',
    'get_chat_model',
    'start_chat_session',
    'generate_text',
    'process_chat_with_context'
]
