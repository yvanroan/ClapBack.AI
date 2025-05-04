"""
Data module for the ChatMatch application.

This module provides access to prompt templates and archetype definitions
used for generating AI responses and evaluating user interactions.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Import prompt functions
from backend.data.prompts.prompts import (
    chunking_prompt,
    tagging_prompt,
    main_convo_prompt,
    assessment_prompt
)

# Path settings
DATA_DIR = Path(__file__).parent
ARCHETYPES_FILE = os.path.join(DATA_DIR, "archetypes.json")

def load_archetypes(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load archetypes data from the archetypes.json file.
    
    Args:
        file_path: Optional custom path to the archetypes file.
                  If None, uses the default path.
    
    Returns:
        dict: The parsed archetypes data
    """
    try:
        path_to_use = file_path if file_path else ARCHETYPES_FILE
        with open(path_to_use, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading archetypes data: {e}")
        return {}

async def load_archetypes_async(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Async version of load_archetypes.
    
    Args:
        file_path: Optional custom path to the archetypes file.
                  If None, uses the default path.
    
    Returns:
        dict: The parsed archetypes data
    """
    return load_archetypes(file_path)

# Export all components
__all__ = [
    # Prompt functions
    'chunking_prompt',
    'tagging_prompt',
    'main_convo_prompt',
    'assessment_prompt',
    
    # Data access functions
    'load_archetypes',
    'load_archetypes_async',
    
    # Path constants
    'DATA_DIR',
    'ARCHETYPES_FILE'
]
