"""LLM service modules for interacting with various AI models.

This package contains modules for different LLM providers (Gemini, DeepSeek, etc.)
and provides a consistent interface for generating text and processing chats.
"""

# Export key functions from gemini module
from backend.app.services.llm.gemini import (
    initialize_gemini,
    get_chat_model,
    start_chat_session,
    generate_text,
    process_chat_with_context
)

# Version information
__version__ = "1.0.0"

# Define what's available when using `from backend.app.services.llm import *`
__all__ = [
    "initialize_gemini",
    "get_chat_model", 
    "start_chat_session",
    "generate_text",
    "process_chat_with_context"
]
