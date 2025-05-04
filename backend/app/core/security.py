from typing import Dict
from backend.app.core.config import settings

def validate_api_keys() -> Dict[str, bool]:
    """
    Validates that all required API keys are present in the environment.
    
    Returns:
        Dict[str, bool]: A dictionary with API key names as keys and validation status as values
    """
    return {
        "GEMINI_API_KEY": settings.GEMINI_API_KEY is not None,
        "HUGGINGFACE_TOKEN": settings.HUGGINGFACE_TOKEN is not None,
        "DEEPSEEK_API_KEY": settings.DEEPSEEK_API_KEY is not None
    }

def get_api_key_or_raise(key_name: str) -> str:
    """
    Get an API key from environment or raise an error if it's not available.
    
    Args:
        key_name (str): Name of the environment variable for the API key
        
    Returns:
        str: The API key value
        
    Raises:
        ValueError: If the API key is not found
    """
    api_key = getattr(settings, key_name, None)
    if not api_key:
        raise ValueError(f"API key {key_name} not configured")
    return api_key 