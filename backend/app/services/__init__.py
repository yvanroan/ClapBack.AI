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
    generate_scenario_id,
    flush_conversation_to_s3,
    save_assessment_to_s3
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
    initialize_qdrant_client,
    get_or_create_collection,
    generate_embedding,
    store_document,
    process_and_store_blocks,
    retrieve_relevant_examples
)

# Import VectorService class
from backend.app.services.vector_service import VectorService


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
    'initialize_qdrant_client',
    'get_or_create_collection',
    'generate_embedding',
    'store_document',
    'process_and_store_blocks',
    'retrieve_relevant_examples',
    'VectorService'
]
