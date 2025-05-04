import json
import os
from typing import Dict, List, Any, Optional
from backend.app.core import settings
from backend.app.utils.cleaner import clean_gemini_output
from backend.data.prompts.prompts import assessment_prompt
from backend.data import load_archetypes_async

async def load_archetypes_data():
    """Load archetypes data from the JSON file."""
    return await load_archetypes_async(settings.ARCHETYPES_FILE)

async def load_archetype_definitions():
    """Load archetype definitions from archetypes.json"""
    try:
        archetypes_data = await load_archetypes_data()
        user_archetypes = archetypes_data.get('user_archetypes', {})
        formatted_archetypes_definitions = "\n".join([
            f"- {name}: {desc}" for name, desc in user_archetypes.items()
        ])
        return formatted_archetypes_definitions
    except Exception as e:
        print(f"Error loading archetype definitions: {e}")
        return "Error loading archetype definitions"

async def load_conversation_aspects():
    """Load conversation aspects from archetypes.json"""
    try:
        archetypes_data = await load_archetypes_data()
        conv_aspects = archetypes_data.get('conversation_aspects', {})
        formatted_conversation_aspects = "\n".join([
            f"- {name}: {details.get('description', '')}\n    - Good: {details.get('good', '')}\n    - Bad: {details.get('bad', '')}"
            for name, details in conv_aspects.items()
        ])
        return formatted_conversation_aspects
    except Exception as e:
        print(f"Error loading conversation aspects: {e}")
        return "Error loading conversation aspects"

async def format_assessment_prompt(
    conversation_history: List[Dict[str, str]],
    scenario_data: Dict[str, Any]
) -> str:
    """
    Format the assessment prompt with conversation history and scenario data.
    
    Args:
        conversation_history: The conversation history
        scenario_data: The scenario data
        
    Returns:
        Formatted assessment prompt
    """
    try:
        
        # Format the conversation history
        formatted_history_str = "\n".join([
            f"{turn.get('role', 'unknown')}: {turn.get('content', '')}" 
            for turn in conversation_history
        ])
        
        # Get formatted archetype definitions and conversation aspects
        formatted_archetypes_definitions = await load_archetype_definitions()
        formatted_conversation_aspects = await load_conversation_aspects()
        
        # Create information dictionary for the assessment prompt
        information = {
            'list_of_archetype_definitions': formatted_archetypes_definitions,
            'conversation_aspects': formatted_conversation_aspects,
            'conversation_history': formatted_history_str
        }
        
        # Generate the final prompt
        final_prompt = assessment_prompt(information)
        return final_prompt
    except Exception as e:
        print(f"Error formatting assessment prompt: {e}")
        raise ValueError(f"Failed to format assessment prompt: {str(e)}")

async def generate_conversation_assessment(
    conversation_history: List[Dict[str, str]],
    scenario_data: Dict[str, Any],
    chat_model
) -> Dict[str, Any]:
    """
    Generate an assessment for a conversation.
    
    Args:
        conversation_history: The conversation history
        scenario_data: The scenario data
        chat_model: The Gemini chat model to use
        
    Returns:
        Dict with assessment results
    """
    try:
        # Format assessment prompt
        assessment_prompt = await format_assessment_prompt(conversation_history, scenario_data)
        
        # Generate assessment using the provided chat model
        print(f"Sending assessment prompt to AI...")
        response = await chat_model.generate_content_async(assessment_prompt)
        generated_text = response.text
        print(f"Received assessment text from AI")
        
        # Parse the response
        assessment_json = clean_gemini_output(generated_text)
        
        if not assessment_json:
            return {
                "error": "Failed to parse assessment response",
                "status": "error",
                "raw_text_response": generated_text
            }
        
        # Add the raw text as a fallback
        assessment_json["raw_text_response"] = ""
        
        return {
            "assessment": assessment_json,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": f"Error generating assessment: {str(e)}",
            "status": "error",
            "raw_text_response": generated_text if 'generated_text' in locals() else None
        } 