import json
from typing import Any, Optional, List, Dict
import google.generativeai as genai # Assuming this is the library used

# Assuming prompts.py is accessible from the backend directory structure
from prompts import assessment_prompt 

async def get_ai_assessment(
    chat_model: Any, # Type hint for the specific model class if known
    conversation_history: List[Dict[str, str]],
    formatted_archetypes_definitions: str, # Pass pre-formatted strings
    formatted_conversation_aspects: str,   # Pass pre-formatted strings
) -> Optional[Dict[str, Any]]: # Return a dictionary or None on error
    """
    Generates a conversation assessment using the provided AI model.

    Args:
        chat_model: The initialized Generative AI model instance.
        conversation_history: The conversation log as a list of dicts.
        formatted_archetypes_definitions: Pre-formatted string of archetype definitions.
        formatted_conversation_aspects: Pre-formatted string of conversation aspects.

    Returns:
        A dictionary containing the parsed assessment JSON, or None if an error occurs.
    """
    
    if not chat_model:
        print("ERROR (get_ai_assessment): Chat model not provided.")
        return None
    if not conversation_history:
        print("ERROR (get_ai_assessment): Conversation history is empty.")
        return None
        
    # 1. Format the assessment prompt
    try:
        formatted_history_str = "\n".join([
            f"{turn.get('role', 'unknown')}: {turn.get('content', '')}" 
            for turn in conversation_history
        ])
        
        information = {
            'list_of_archetype_definitions': formatted_archetypes_definitions,
            'conversation_aspects': formatted_conversation_aspects,
            'conversation_history': formatted_history_str
        }
        final_prompt = assessment_prompt(information)
    except Exception as e:
        print(f"ERROR (get_ai_assessment): Failed to format assessment prompt: {e}")
        return None

    # 2. Call the AI model (using generate_content for stateless analysis)
    try:
        print("Sending assessment prompt to AI...")
        # Use generate_content_async as it's called from an async endpoint
        response = await chat_model.generate_content_async(final_prompt) 
        generated_text = response.text
        print("Received assessment text from AI.")

        # 3. Parse the JSON response from the AI
        try:
            assessment_json = json.loads(generated_text)
            # Basic validation: check if it's a dictionary
            if not isinstance(assessment_json, dict):
                 print(f"WARNING (get_ai_assessment): AI response was not a JSON object: {generated_text}")
                 # Depending on requirements, you might return the raw text or None
                 # For now, returning None as the expectation is structured JSON
                 return None 
            print("Successfully parsed assessment JSON.")
            return assessment_json # Return the parsed dictionary
        except json.JSONDecodeError:
            print(f"WARNING (get_ai_assessment): Assessment AI response was not valid JSON: {generated_text}")
            # Return None if JSON parsing fails
            return None

    except Exception as e:
        # Catch potential errors during the AI call itself
        print(f"ERROR (get_ai_assessment): Error calling Gemini API for assessment: {e}")
        return None 