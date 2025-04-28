import google.generativeai as genai
from typing import Dict, List, Any, Optional
from backend.app.core import settings, get_api_key_or_raise
from backend.app.utils.cleaner import clean_gemini_output

# Initialize Gemini
api_key = get_api_key_or_raise("GEMINI_API_KEY")

def initialize_gemini():
    """Initialize the Gemini API client."""
    genai.configure(api_key=api_key)

def get_chat_model(model_name: str = 'gemini-2.0-flash'):
    """Get a generative model for chat."""
    return genai.GenerativeModel(model_name)

def start_chat_session(model=None, history=None):
    """Start a new chat session with optional history."""
    if model is None:
        model = get_chat_model()
    return model.start_chat(history=history or [])

async def generate_text(prompt: str, model_name: str = 'gemini-2.0-flash') -> Dict[str, Any]:
    """
    Generate text using Gemini model.
    
    Args:
        prompt: The prompt to send to the model
        model_name: The model name to use
        
    Returns:
        Dict with response text and metadata
    """
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        return {
            "text": response.text,
            "status": "success"
        }
    except Exception as e:
        return {
            "text": f"Error generating text: {str(e)}",
            "status": "error",
            "error": str(e)
        }

async def process_chat_with_context(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    system_prompt: str,
    relevant_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a chat message with conversation history and context.
    
    Args:
        user_message: The user's message
        conversation_history: Previous conversation turns
        system_prompt: The system prompt to guide the LLM
        relevant_context: Any additional context to include
        
    Returns:
        Dict with AI response and metadata
    """
    try:
        # This is a placeholder for the implementation
        # Will be filled in with the actual implementation from main.py
        model = get_chat_model()
        session = start_chat_session(model)
        
        # Here we would format the prompt with context and history
        # and then get the response from the model
        
        # Placeholder return
        return {
            "response": "This is a placeholder response",
            "status": "success"
        }
    except Exception as e:
        return {
            "response": f"Error processing chat: {str(e)}",
            "status": "error",
            "error": str(e)
        } 