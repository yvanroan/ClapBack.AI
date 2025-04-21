import requests
import json
import os
import time # Added import
from prompts import main_convo_prompt 

# Assuming vector_store.py is in the same directory or accessible
from vector_store import (
    retrieve_relevant_examples, 
    initialize_chroma_client, 
    initialize_embedding_model,
    get_or_create_collection
)


# --- Configuration ---
API_ENDPOINT = "http://localhost:8000/chat" # Assuming FastAPI runs on port 8000
NUM_TURNS = 7
OUTPUT_DIR = "downloads"
# --- Conversation Simulation Function ---
def run_conversation_simulation(scenario: dict):
    """
    Runs a 10-turn conversation simulation based on the provided scenario.

    Args:
        scenario: Dictionary describing the current scenario, including keys like 
                  type, setting, goal, system_archetype, roast_level, 
                  player_sex, system_sex.

    Returns:
        The full conversation history list, or None if initialization fails.
    """
    print("--- Initializing Services for Simulation ---")

    model = initialize_embedding_model() # Still initialize for populating
    chroma_client = initialize_chroma_client()
    chroma_collection = get_or_create_collection(chroma_client)
    
    if not chroma_collection:
        print("Error: Failed to initialize ChromaDB collection. Cannot proceed.")
        return None
    
    print("--- Starting Conversation Simulation --- ")
    conversation_history = []
    # Optional: Add initial system message based on scenario? 
    # E.g., conversation_history.append({"role": "system", "content": f"Simulating a {scenario.get('type','N/A')} scenario in a {scenario.get('setting','N/A')}. You are the {scenario.get('system_archetype','N/A')}."})

    for turn in range(NUM_TURNS):
        print(f"\n--- Turn {turn + 1}/{NUM_TURNS} ---")
        
        # 1. Get User Input
        try:
            current_input = input("User: ")
        except EOFError:
            print("\nExiting conversation early.")
            break # Exit loop if input stream is closed
            
        conversation_history.append({"role": "user", "content": current_input})
        
        # 2. Retrieve Relevant Examples
        print("Retrieving relevant examples...")
        retrieved_examples = retrieve_relevant_examples(
            collection=chroma_collection,
            user_input=current_input,
            conversation_history=conversation_history, # Pass the current history
            scenario=scenario,
            n_results=5 # Or configure as needed
        )
        
        if not retrieved_examples:
            print("Warning: Failed to retrieve examples from vector store. Proceeding without them.")
            retrieved_examples = {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]} # Provide empty structure
        
        # Extract the relevant parts for the prompt (documents and metadatas)
        examples_for_prompt = []
        ids = retrieved_examples.get("ids", [[]])[0]
        metadatas = retrieved_examples.get("metadatas", [[]])[0]
        documents = retrieved_examples.get("documents", [[]])[0]
        for i, doc_id in enumerate(ids):
             examples_for_prompt.append({
                 "metadata": metadatas[i],
                 "document": documents[i]
             }) 

        # 3. Prepare data for the prompt function
        try:
            # Format conversation history for the prompt
            formatted_history = "\n".join([f"{turn.get('role', 'unknown')}: {turn.get('content', '')}" for turn in conversation_history])
            # Format retrieved examples
            formatted_examples = json.dumps(examples_for_prompt, indent=2)

            # Create the dictionary expected by main_convo_prompt
            information = {
                'scenario_type': scenario.get('type', 'N/A'),
                'scenario_setting': scenario.get('setting', 'N/A'),
                'scenario_goal': scenario.get('goal', 'N/A'),
                'system_archetype': scenario.get('system_archetype', 'N/A'),
                'roast_level': scenario.get('roast_level', 'N/A'),
                'player_sex': scenario.get('player_sex', 'N/A'),
                'system_sex': scenario.get('system_sex', 'N/A'),
                'conversation_history': formatted_history,
                'current_input': current_input,
                'retrieved_examples': formatted_examples
            }
        except Exception as e:
            print(f"Error formatting data for prompt: {e}")
            continue # Skip this turn if formatting fails

        # 4. Generate the final prompt string
        try:
            final_prompt = main_convo_prompt(information)
            # print(f"\n--- Generated Prompt (Turn {turn+1}) ---\n{final_prompt}\n----------------------\n") # Uncomment for debugging
        except Exception as e:
            print(f"Error generating prompt using main_convo_prompt: {e}")
            continue # Skip this turn

        # 5. Call the API
        payload = {"prompt": final_prompt}
        api_response_text = None
        try:
            print(f"Sending request to API endpoint: {API_ENDPOINT}")
            response = requests.post(API_ENDPOINT, json=payload, timeout=60) # Added timeout
            response.raise_for_status() 
            api_response_text = response.text 
            print("API call successful.")
            
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to the API endpoint at {API_ENDPOINT}. Is the server running? Ending simulation.")
            break
        except requests.exceptions.Timeout:
            print(f"Error: Request to {API_ENDPOINT} timed out. Skipping turn.")
            continue
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Status Code: {http_err.response.status_code}")
            try:
                error_detail = http_err.response.json().get('detail', http_err.response.text)
                print(f"Error Detail: {error_detail}. Skipping turn.")
            except json.JSONDecodeError:
                print(f"Error Detail: {http_err.response.text}. Skipping turn.")
            continue # Skip turn on HTTP error from API
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred during the API request: {req_err}. Skipping turn.")
            continue
        except Exception as e:
            print(f"An unexpected error occurred during API call: {e}. Skipping turn.")
            continue

        # 6. Process and Print Response
        if api_response_text is not None:
            print(f"AI: {api_response_text}")
            conversation_history.append({"role": "assistant", "content": api_response_text})
        else:
             print("AI: (No response received due to error)")
             # Optionally add an error placeholder to history
             # conversation_history.append({"role": "assistant", "content": "[Error communicating with AI]"})

        time.sleep(1) # Small delay between turns

    print("\n--- Conversation Simulation Finished --- ")
    return conversation_history

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    print("--- Running Conversation Simulation Test --- ")

    # Load archetypes (assuming file exists and is needed for scenario)
    try:
        with open("archetypes.json", 'r', encoding='utf-8') as f:
            archetypes_data = json.load(f)
        archetype_key = "The Chaotic Extrovert" # Example key
        archetype_description = archetypes_data.get("system_archetypes", {}).get(archetype_key, "Default Archetype Description")
    except FileNotFoundError:
        print("Warning: archetypes.json not found. Using default archetype description.")
        archetype_key = "Default Archetype"
        archetype_description = "A default conversational partner."
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading or parsing archetypes.json: {e}. Using default archetype description.")
        archetype_key = "Default Archetype"
        archetype_description = "A default conversational partner."

    # Define the scenario using the loaded archetype data
    test_scenario = {
        "type": "dating",
        "setting": "coffee_shop",
        "goal": "first_impression",
        "system_archetype": f"{archetype_key}, {archetype_description}", # Combine key and description
        "roast_level": 4,
        "player_sex": "male",
        "system_sex": "female"
    }

    print(f"Starting simulation with scenario: {test_scenario['goal']} at {test_scenario['setting']}")
    # Make sure your FastAPI server (main.py) and ChromaDB are ready
    final_history = run_conversation_simulation(scenario=test_scenario)

    if final_history:
        print("\n--- Final Conversation History ---")
        print(json.dumps(final_history, indent=2))
        # Optionally save the final history to a file here
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            final_output_path = os.path.join(OUTPUT_DIR, "final_conversation_log.json")
            with open(final_output_path, 'w', encoding='utf-8') as f:
                json.dump(final_history, f, ensure_ascii=False, indent=2)
            print(f"Final history saved to {final_output_path}")
        except Exception as e:
            print(f"Error saving final history: {e}")
    else:
        print("\n--- Simulation ended due to errors --- ")

    print("--- API Caller Test Finished ---") 