import json
import os # Need os for path manipulation

def clean_gemini_output(raw_text: str):
    """Cleans a string potentially containing JSON wrapped in markdown fences.

    Args:
        raw_text: The raw string response from Gemini, which might look like 
                  '```json\n[{"key": "value"}]\n```' or just '[{"key": "value"}]'.

    Returns:
        The parsed JSON object (list or dict), or None if cleaning/parsing fails.
    """
    if not isinstance(raw_text, str):
        print(f"Error: Input to clean_gemini_output must be a string, got {type(raw_text)}")
        return None
        
    cleaned = raw_text.strip()
    
    # Remove optional markdown fences
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-len("```")]
        
    # Strip whitespace again after removing fences
    cleaned = cleaned.strip()
    
    # Parse the cleaned string as JSON
    try:
        # json.loads handles standard JSON unescaping (e.g., \" -> ")
        parsed = json.loads(cleaned)
        return parsed
    except json.JSONDecodeError as e:
        print(f"Failed to parse cleaned Gemini output as JSON: {e}")
        print(f"Cleaned string before parsing attempt: {cleaned[:500]}...") # Log problematic string
        return None
    except Exception as e:
        print(f"An unexpected error occurred during JSON parsing: {e}")
        return None 