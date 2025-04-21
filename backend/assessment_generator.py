import requests
import json
import os
from cleaner import clean_gemini_output
# Assuming prompts.py is in the same directory or accessible
from prompts import assessment_prompt 

# --- Configuration ---
# Use the /generate endpoint as it's more suited for structured JSON output
API_ENDPOINT = "http://localhost:8000/chat" 
ARCHETYPES_FILE = "archetypes.json"

CONVERSATION_LOG_FILE = "downloads/final_conversation_log.json"


if not os.path.exists(CONVERSATION_LOG_FILE):
    print(f"Error: Required conversation log file not found at {CONVERSATION_LOG_FILE}")
    print("Please run api_caller.py first to generate the log, or ensure the fake log exists.")
    exit(1)

try:
    with open(CONVERSATION_LOG_FILE, 'r', encoding='utf-8') as f:
        conversation_history = json.load(f)
    if not isinstance(conversation_history, list):
        raise ValueError("Conversation log should be a JSON list.")
        
except Exception as e:
    print(f"An unexpected error occurred reading conversation log: {e}")
    exit(1)


# --- Assessment Generator Function ---
def generate_conversation_assessment(conversation_history: list):
    """
    Loads conversation history, archetypes, formats the assessment prompt,
    calls the API to get an assessment, and returns the parsed JSON assessment.

    Args:
        conversation_log_path: Path to the JSON file containing the conversation history.

    Returns:
        A dictionary containing the conversation assessment, or None if an error occurred.
    """
    
    # 1. Load Conversation History
    formatted_history = "\n".join([f"{turn.get('role', 'unknown')}: {turn.get('content', '')}" for turn in conversation_history])

    # 2. Load Archetypes and Aspects
    try:
        with open(ARCHETYPES_FILE, 'r', encoding='utf-8') as f:
            archetypes_data = json.load(f)
        
        # Format user archetypes definitions for the prompt
        user_archetypes = archetypes_data.get('user_archetypes', {})
        formatted_archetypes = "\n".join([f"- {name}: {desc}" for name, desc in user_archetypes.items()])
        
        # Format conversation aspects for the prompt
        conv_aspects = archetypes_data.get('conversation_aspects', {})
        formatted_aspects = "\n".join([
            f"- {name}: {details.get('description', '')}\n    - Good: {details.get('good', '')}\n    - Bad: {details.get('bad', '')}"
            for name, details in conv_aspects.items()
        ])

    except FileNotFoundError:
        print(f"Error: Archetypes file not found at {ARCHETYPES_FILE}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading or parsing {ARCHETYPES_FILE}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred reading {ARCHETYPES_FILE}: {e}")
        return None

    # 3. Prepare data for the prompt function
    information = {
        'list_of_archetype_definitions': formatted_archetypes,
        'conversation_aspects': formatted_aspects,
        'conversation_history': formatted_history
    }

    # 4. Generate the final prompt string
    try:
        final_prompt = assessment_prompt(information)
        # print(f"\n--- Generated Assessment Prompt ---\n{final_prompt}\n-----------------------------------\n") # Debugging
    except Exception as e:
        print(f"Error generating prompt using assessment_prompt: {e}")
        return None

    # 5. Call the API
    payload = {"prompt": final_prompt}
    assessment_json = None
    try:
        print(f"Sending request to assessment API endpoint: {API_ENDPOINT}")
        response = requests.post(API_ENDPOINT, json=payload, timeout=90) # Longer timeout for generation
        response.raise_for_status() 
        
        # Attempt to parse the response directly as JSON
        assessment_json = response.json() 
        print("API call successful and response parsed as JSON.")
        # print(f"\n--- API Assessment Response ---\n{json.dumps(assessment_json, indent=2)}\n-----------------------------") # Debugging

    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the API endpoint at {API_ENDPOINT}. Is the server running?")
        return None
    except requests.exceptions.Timeout:
        print(f"Error: Request to {API_ENDPOINT} timed out.")
        return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Status Code: {http_err.response.status_code}")
        try:
            error_detail = http_err.response.json().get('detail', http_err.response.text)
            print(f"Error Detail: {error_detail}")
        except json.JSONDecodeError:
            print(f"Error Detail: {http_err.response.text}")
        return None
    except json.JSONDecodeError:
        # Handle cases where the API might not return valid JSON as expected
        print(f"Error: API response was not valid JSON. Response text: {response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred during the API request: {req_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during API call or JSON parsing: {e}")
        return None

    # 6. Return the parsed assessment dictionary
    return assessment_json

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    print("--- Running Assessment Generator Test --- ")
    
    assessment_result = generate_conversation_assessment(conversation_history)

    if assessment_result:
        print("\n--- Assessment Generation Successful ---")
        print("Received Assessment:")
        print(json.dumps(assessment_result, indent=2))
        cleaned_assessment = clean_gemini_output(assessment_result)
        # Optionally save this assessment to another file
        try:
            output_path = "downloads/conversation_assessment.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_assessment, f, ensure_ascii=False, indent=2)
            print(f"Assessment saved to {output_path}")
        except Exception as e:
            print(f"Error saving assessment: {e}")
    else:
        print("\n--- Assessment Generation Failed --- ")

    print("--- Assessment Generator Test Finished ---") 