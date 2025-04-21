import os
import time
import uuid
import json
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, status, Request
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from google.genai.types import Part
from schema import (
    PromptRequest,
    ScenarioData,
    ScenarioIDResponse,
    ChatInput,
    AIResponse,
    AssessmentResponse
)
from prompts import assessment_prompt, main_convo_prompt # Add main_convo_prompt
from cleaner import clean_gemini_output
from vector_store import (
    initialize_embedding_model,
    initialize_chroma_client,
    get_or_create_collection,
    retrieve_relevant_examples # Add retrieve_relevant_examples
)

# Load environment variables
load_dotenv()

# --- Application Lifespan Management (Recommended) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("--- Initializing Embedding Model and DB Connection --- Lifespan Start")
    # Use app.state to store shared resources
    app.state.embedding_model = initialize_embedding_model()
    app.state.chroma_client = initialize_chroma_client()
    app.state.chroma_collection = get_or_create_collection(app.state.chroma_client)

    if not app.state.embedding_model or not app.state.chroma_collection:
         print("ERROR: Failed to initialize required services during startup.")
         # In a real app, you might want to raise an exception here to prevent startup
         # or implement more robust health checks.
         # For now, endpoints needing these will fail if they check.
    else:
        print("--- Services Initialized Successfully --- Lifestpan Start")

    try:
        print("Initializing Chat Model...")
        # Use the model name appropriate for your chat endpoint
        chat_model = genai.GenerativeModel('gemini-2.0-flash') 
        # Store the model instance itself
        app.state.chat_model = chat_model 
        # Optional: If /chat needs persistent history across *all* users (unlikely), 
        # start a global chat session. More likely, chat sessions should be per-user/request.
        # app.state.global_chat_session = chat_model.start_chat(history=[]) 
        print("Chat Model Initialized.")
    except Exception as e:
        print(f"ERROR: Failed to initialize Chat Model: {e}")
        app.state.chat_model = None
        # app.state.global_chat_session = None

    yield # The application runs while the context manager is active

    # Code to run on shutdown
    print("--- Cleaning up resources --- Lifespan End")
    # Add cleanup code if needed (e.g., close DB connections explicitly if necessary)
    app.state.chroma_client = None # Example cleanup
    app.state.embedding_model = None
    app.state.chroma_collection = None
    print("--- Cleanup Complete --- Lifespan End")


# --- FastAPI App Initialization ---

app = FastAPI(
    title="rizz api",
    description="API for conversation simulation and analysis",
    version="1.0.0",
    debug=True,  # Enable debug mode for more detailed logging
    lifespan=lifespan # Associate the lifespan manager
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"], # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise HTTPException(status_code=500, detail="API key not configured")

# client = genai.Client(api_key=api_key)
# chat = client.chats.create(model='gemini-2.0-flash')

# --- In-Memory Storage (Replace with database for persistence) ---
scenarios_db: Dict[str, Any] = {}

# Define the path to the archetypes file relative to main.py
ARCHETYPES_FILE = "archetypes.json"

# --- Pre-load Archetypes (Consider error handling) ---
formatted_archetypes_definitions = ""
formatted_conversation_aspects = ""
try:
    with open(ARCHETYPES_FILE, 'r', encoding='utf-8') as f:
        archetypes_data = json.load(f)
    user_archetypes = archetypes_data.get('user_archetypes', {})
    formatted_archetypes_definitions = "\n".join([f"- {name}: {desc}" for name, desc in user_archetypes.items()])
    conv_aspects = archetypes_data.get('conversation_aspects', {})
    roast_scale = archetypes_data.get('roast_scale_profile', {})
    formatted_conversation_aspects = "\n".join([
        f"- {name}: {details.get('description', '')}\n    - Good: {details.get('good', '')}\n    - Bad: {details.get('bad', '')}"
        for name, details in conv_aspects.items()
    ])
    print("Archetypes and Aspects pre-loaded successfully.")
except FileNotFoundError:
    print(f"WARNING: Archetypes file not found at {ARCHETYPES_FILE}. Assessment prompt may be incomplete.")
except Exception as e:
    print(f"WARNING: Error loading archetypes file {ARCHETYPES_FILE}: {e}. Assessment prompt may be incomplete.")

DOWNLOADS_DIR = "downloads" # Define download directory constant

# --- API Endpoints ---
@app.get("/", summary="Root endpoint for health check")
async def read_root():
    """Provides a simple welcome message."""
    return {"message": "Welcome to the Rizz API Backend"}

@app.post("/api/v1/scenario", response_model=ScenarioIDResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(scenario_input: ScenarioData):
    """
    Receives scenario details from the frontend, generates a unique ID,
    stores the scenario (in-memory), and returns the unique scenario ID.
    """
    print(f"Received scenario input: {scenario_input}")
    try:
        # 1. Generate Unique ID
        timestamp = int(time.time())
        unique_uuid = uuid.uuid4()
        scenario_id = f"conversation-{timestamp}-{unique_uuid}"

        # 2. Create ScenarioData object (useful for storage)
        scenario_data = ScenarioData(
            id=scenario_id,
            **scenario_input.dict() # Unpack validated input data
        )

        # 3. Store in our *temporary* in-memory DB
        scenarios_db[scenario_id] = {
            "scenario_data": scenario_data.dict(),
            "conversation_history": []
        }
        print(f"Scenario created and stored (in-memory): {scenario_id}")

        # 4. Return only the ID
        return ScenarioIDResponse(id=scenario_id)
    except Exception as e:
        print(f"Error creating scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while creating the scenario: {str(e)}"
        )

@app.get("/api/v1/scenario/{scenario_id}", response_model=ScenarioData)
async def get_scenario_data(scenario_id: str):
    """
    Retrieves the full scenario data for a given scenario ID.
    """
    print(f"Received request for scenario data: {scenario_id}")
    scenario_container = scenarios_db.get(scenario_id)
    if not scenario_container or "scenario_data" not in scenario_container:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    
    # Return only the scenario_data part
    return ScenarioData(**scenario_container["scenario_data"])


@app.post("/api/v1/process_chat")
async def process_chat_message(request: Request, chat_input: ChatInput):
    """
    Handles a chat message: retrieves context, formats prompt, gets AI response,
    and updates conversation history.
    """

    print(f"Received chat input: {chat_input}")
    # 1. Access resources initialized in lifespan
    embedding_model = request.app.state.embedding_model # Needed for retrieval embedding generation
    chroma_collection = request.app.state.chroma_collection
    chat_model = request.app.state.chat_model # For generating the final response

    if not embedding_model or not chroma_collection or not chat_model:
         raise HTTPException(status_code=503, detail="Required services not available")

    # 2. Retrieve scenario details and history from storage
    scenario_container = scenarios_db.get(chat_input.scenario_id)
    if not scenario_container or "scenario_data" not in scenario_container:
        raise HTTPException(status_code=404, detail=f"Scenario '{chat_input.scenario_id}' not found.")
        
    scenario = scenario_container["scenario_data"]
    # Get current history *before* adding the new user message
    conversation_history = scenario_container.get("conversation_history", [])

    # --- Start: Logic replacing simple_chat call --- 
    
    # 2a. Retrieve Relevant Examples from Vector Store
    print(f"Retrieving relevant examples for scenario: {chat_input.scenario_id}")
    retrieved_examples = retrieve_relevant_examples(
        collection=chroma_collection,
        user_input=chat_input.user_input, # Current user input
        conversation_history=conversation_history, # History *before* this message
        scenario=scenario,
        n_results=5 # Or configure as needed
    )

    if not retrieved_examples:
        print("Warning: Failed to retrieve examples from vector store. Proceeding without them.")
        retrieved_examples = {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]} 

    # 2b. Format Retrieved Examples for Prompt
    examples_for_prompt = []
    ids = retrieved_examples.get("ids")
    metadatas = retrieved_examples.get("metadatas")
    documents = retrieved_examples.get("documents")
    
    if ids and isinstance(ids, list) and ids[0] and \
       metadatas and isinstance(metadatas, list) and metadatas[0] and \
       documents and isinstance(documents, list) and documents[0]:
        num_results = len(ids[0])
        if len(metadatas[0]) == num_results and len(documents[0]) == num_results:
             for i in range(num_results):
                examples_for_prompt.append({
                    "metadata": metadatas[0][i],
                    "document": documents[0][i]
                })
        else: print("Warning: Mismatch in lengths of retrieved examples data.")
    else: print("Warning: Retrieved examples data structure is not as expected.")

    # 3. Prepare data for the main conversation prompt
    ai_response_text = None
    try:
        # Include the *current* user input in the history for the prompt
        current_turn_history = conversation_history + [{'role': 'user', 'content': chat_input.user_input}]
        formatted_history = "\n".join([f"{turn.get('role', 'unknown')}: {turn.get('content', '')}" for turn in current_turn_history])
        formatted_examples = json.dumps(examples_for_prompt, indent=2)
        roast_level = scenario.get('roast_level', 'N/A')
        system_archetype = scenario.get('system_archetype', 'N/A')
        roast_level_profile = roast_scale[system_archetype][str(roast_level)]
        information = {
            'scenario_type': scenario.get('type', 'N/A'),
            'scenario_setting': scenario.get('setting', 'N/A'),
            'scenario_goal': scenario.get('goal', 'N/A'),
            'system_archetype': system_archetype,
            'roast_level': roast_level_profile,
            'player_sex': scenario.get('player_sex', 'N/A'),
            'system_sex': scenario.get('system_sex', 'N/A'),
            'conversation_history': formatted_history, # History including current input
            'current_input': chat_input.user_input,
            'retrieved_examples': formatted_examples
        }
        
        # 4. Generate the final prompt string
        final_prompt = main_convo_prompt(information)
        
        # 5. Call the AI model (using the initialized chat_model)
        print(f"Sending final prompt to AI for scenario: {chat_input.scenario_id}")
        response = await chat_model.generate_content_async(final_prompt)
        ai_response_text = response.text
        print(f"Received AI response for scenario: {chat_input.scenario_id}")
        
    except Exception as e:
        print(f"Error during AI prompt generation or call: {e}")
        # Raise HTTPException if the AI call itself fails
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {str(e)}")

    # --- End: Logic replacing simple_chat call --- 
    
    if ai_response_text is None:
        # This case might be less likely now unless the exception above doesn't catch something
        raise HTTPException(status_code=500, detail="Failed to get AI response from chat logic (unknown error)")

    # 6. Update conversation history in storage
    try:
        scenarios_db[chat_input.scenario_id]["conversation_history"].append({"role": "user", "content": chat_input.user_input})
        scenarios_db[chat_input.scenario_id]["conversation_history"].append({"role": "assistant", "content": ai_response_text})
        print(f"Updated history for scenario: {chat_input.scenario_id}")
    except KeyError:
        # Handle case where scenario_id might have disappeared between checks (unlikely)
        raise HTTPException(status_code=500, detail="Failed to update conversation history; scenario key missing.")
    
    # 7. Return the AI response content
    return AIResponse(content=ai_response_text)
    

# --- Existing Endpoints (Refactored) --- 

@app.post("/generate")
async def generate_text_from_gemini(request: Request, prompt_request: PromptRequest):
    """
    Receives a text prompt and returns the generated text from the Gemini API.
    Uses the chat_model initialized during application lifespan.
    Adapts response to attempt JSON parsing for assessment compatibility.
    """
    chat_model = request.app.state.chat_model
    if not chat_model:
        raise HTTPException(status_code=503, detail="Gemini chat model service not available")

    try:
        # Use generate_content for stateless requests, suitable for /generate
        response = await chat_model.generate_content_async(prompt_request.prompt) # Use async version
        generated_text = response.text

        return generated_text
    except Exception as e:
        print(f"Error calling Gemini API via global chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while communicating with the Gemini API: {str(e)}"
        )

@app.post("/chat")
async def handle_chat(request: Request, prompt_request: PromptRequest):
    """
    Handles a single turn in a conversation based on the input prompt.
    Uses the chat_model initialized during application lifespan for a stateless response.
    Assumes conversation history is managed externally and included in the prompt.
    """
    chat_model = request.app.state.chat_model
    if not chat_model:
        raise HTTPException(status_code=503, detail="Gemini chat model service not available")
        
    try:
        # Use generate_content for a stateless response based on the prompt
        # Assumes the prompt_request.prompt contains necessary context (history etc.)
        response = await chat_model.generate_content_async(prompt_request.prompt) # Use async version
        generated_text = response.text
        # Returns plain text as originally intended by this endpoint
        return generated_text 

    except Exception as e:
        print(f"Error during chat generation via chat_model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the chat interaction: {str(e)}"
        )

@app.post("/api/v1/conversation/{scenario_id}/assess", response_model=AssessmentResponse)
async def get_conversation_assessment(scenario_id: str, request: Request):
    """
    Retrieves conversation history for the given scenario_id,
    generates an assessment using the AI model, and returns the assessment.
    """
    print(f"Received request to assess scenario: {scenario_id}")
    # Access resources initialized in lifespan
    chat_model = request.app.state.chat_model
    if not chat_model:
        raise HTTPException(status_code=503, detail="Gemini chat model service not available")

    # 1. Retrieve conversation data from storage
    conversation_container = scenarios_db.get(scenario_id)
    if not conversation_container:
        raise HTTPException(status_code=404, detail=f"Conversation scenario '{scenario_id}' not found.")
    
    # Get all necessary data for saving later
    scenario_data = conversation_container.get("scenario_data", {})
    conversation_history = conversation_container.get("conversation_history", [])
    
    if not conversation_history:
         raise HTTPException(status_code=400, detail="Cannot assess an empty conversation.")

    # 2. Format the assessment prompt
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
        print(f"Error formatting assessment prompt for {scenario_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to format assessment request.")

    # 3. Call the AI model
    assessment_result: Optional[AssessmentResponse] = None
    generated_text = ""
    try:
        print(f"Sending assessment prompt to AI for {scenario_id}...")
        response = await chat_model.generate_content_async(final_prompt)
        generated_text = response.text
        print(f"Received assessment text from AI for {scenario_id}")

        # 4. Parse and Validate the JSON response from the AI
        try:
            assessment_json = clean_gemini_output(generated_text) # Use cleaner if needed
            assessment_result = AssessmentResponse(**assessment_json)
            print(f"Successfully parsed and validated assessment for {scenario_id}")
            
        except (json.JSONDecodeError, TypeError) as json_error: # Catch parsing errors
            print(f"WARNING: Assessment AI response parsing error for {scenario_id}: {json_error}")
            # Create a fallback response object with raw text
            assessment_result = AssessmentResponse(raw_text_response=generated_text)
            
        except Exception as validation_error: # Catch potential Pydantic validation errors
             print(f"WARNING: Assessment JSON failed validation for {scenario_id}: {validation_error}")
             # Create a fallback response object with raw text
             assessment_result = AssessmentResponse(raw_text_response=generated_text)

    except Exception as e:
        print(f"Error calling Gemini API for assessment ({scenario_id}): {e}")
        # If the API call itself fails, return error before attempting to save
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the assessment: {str(e)}"
        )

    # --- Added File Saving Logic --- 
    if assessment_result: # Proceed only if we have some result (even if just raw text)
        try:
            # Ensure downloads directory exists
            os.makedirs(DOWNLOADS_DIR, exist_ok=True)
            
            # Construct file path
            file_path = os.path.join(DOWNLOADS_DIR, f"{scenario_id}.json")
            
            # Structure the data to save
            data_to_save = {
                "scenario_id": scenario_id,
                "scenario_details": scenario_data,
                "conversation_history": conversation_history,
                "assessment_result": assessment_result.dict() # Save assessment as dict
            }
            
            # Write to JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            print(f"Successfully saved conversation data and assessment to {file_path}")
            
        except IOError as io_err:
            print(f"ERROR: Could not write assessment log file to {file_path}: {io_err}")
            # Log the error, but don't prevent the API from returning the assessment
        except Exception as save_err:
            print(f"ERROR: An unexpected error occurred while saving assessment log: {save_err}")
            # Log the error, but don't prevent the API from returning the assessment
    # --- End File Saving Logic --- 

    # Return the assessment object (could be parsed or fallback)
    if assessment_result:
        return assessment_result
    else:
        # This case should ideally not be reached if API call succeeded
        # but as a fallback, raise error if assessment_result is still None
         raise HTTPException(
            status_code=500,
            detail="Assessment generated but final result object is missing."
        )

# --- Optional: Add Uvicorn runner for direct execution ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server...")
    # Ensure the app object used by uvicorn is the one configured with lifespan
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) # Use reload for development