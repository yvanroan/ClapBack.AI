import os
import time
import uuid
from typing import Optional, Dict, Any

from google import genai
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.genai.types import Part
import json

# Load environment variables
load_dotenv()

# Create FastAPI app with logging
app = FastAPI(
    title="rizz api",
    description="API for visual reasoning and analysis",
    version="1.0.0",
    debug=True  # Enable debug mode for more detailed logging
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str


# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise HTTPException(status_code=500, detail="API key not configured")

client = genai.Client(api_key=api_key)
chat = client.chats.create(model='gemini-2.0-flash')


app = FastAPI(
    title="Gemini API Backend",
    description="A simple FastAPI backend to interact with the Google Gemini API.",
    version="0.1.0",
)

# --- In-Memory Storage (Replace with database for persistence) ---
scenarios_db: Dict[str, Any] = {}

# --- Pydantic Models ---
class ScenarioInput(BaseModel):
    # Define fields expected from the frontend form
    scenario_type: str = Field(..., description="Type of scenario (e.g., dating)")
    setting: str = Field(..., description="Setting of the scenario (e.g., coffee_shop)")
    goal: str = Field(..., description="Goal of the scenario (e.g., first_impression)")
    system_archetype: str = Field(..., description="Description of the AI character/archetype")
    roast_level: int = Field(..., ge=1, le=5, description="Roast level (1-5)")
    player_sex: str
    system_sex: str
    # Add any other fields from your formSchema

class ScenarioData(ScenarioInput):
    # Inherits fields from ScenarioInput and adds the generated ID
    id: str = Field(..., description="Unique identifier for the conversation scenario")

# --- API Endpoints ---

@app.get("/", summary="Root endpoint for health check")
async def read_root():
    """Provides a simple welcome message."""
    return {"message": "Welcome to the Gemini API Backend"}

@app.post("/api/v1/scenario", response_model=ScenarioData, status_code=status.HTTP_201_CREATED)
async def create_scenario(scenario_input: ScenarioInput):
    """
    Receives scenario details from the frontend, generates a unique ID,
    stores the scenario (in-memory), and returns the complete scenario data.
    """
    try:
        # 1. Generate Unique ID
        timestamp = int(time.time())
        unique_uuid = uuid.uuid4()
        scenario_id = f"conversation-{timestamp}-{unique_uuid}"

        # 2. Create ScenarioData object
        scenario_data = ScenarioData(
            id=scenario_id,
            **scenario_input.dict() # Unpack validated input data
        )

        # 3. Store in our *temporary* in-memory DB
        scenarios_db[scenario_id] = scenario_data.dict()
        print(f"Scenario created and stored (in-memory): {scenario_id}")
        # print(f"Current DB state: {scenarios_db}") # For debugging

        # 4. Return the created data
        return scenario_data
    except Exception as e:
        print(f"Error creating scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while creating the scenario: {str(e)}"
        )

@app.post("/generate")
async def generate_text_from_gemini(request: PromptRequest):
    """
    Receives a text prompt and returns the generated text from the Gemini API.

    Handles potential errors during the API call.
    """

    try:
        message = [
            Part(text=request.prompt),
        ]
        # NOTE: Consider if this should use a fresh client/model instance
        # instead of the global `chat` object if it's for non-conversational tasks.
        response = chat.send_message(message) 
        generated_text = response.text # Accessing .text convenience attribute

        # The /generate endpoint in the frontend expects JSON, but here we return text.
        # Let's adapt this to return JSON consistent with the assessment expectation.
        # This assumes the LLM *outputs* valid JSON string as requested by assessment_prompt.
        try:
            # Attempt to parse the LLM's text output as JSON
            json_response = json.loads(generated_text)
            return json_response
        except json.JSONDecodeError:
            print(f"Warning: /generate LLM output was not valid JSON: {generated_text}")
            # Fallback: return the raw text, but this might break assessment_generator
            # Or raise an internal server error if JSON is strictly required
            # raise HTTPException(status_code=500, detail="AI response was not valid JSON")
            return {"raw_text_response": generated_text} # Example fallback

    except Exception as e:
        print(f"Error calling Gemini API: {e}") # Log the error for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while communicating with the Gemini API: {str(e)}"
        )

@app.post("/chat")
async def handle_chat(request: PromptRequest):
    """
    Handles a single turn in a conversation with the AI.

    Receives user prompt, sends it to the ongoing chat session, 
    and returns the AI's response.
    """
    try:
        # Assuming 'chat' is the persistent chat session object
        # and Part is correctly imported/defined.
        message = [
            Part(text=request.prompt),
        ]
        response = chat.send_message(message)
        generated_text = response.text # Accessing .text convenience attribute

        # Return the text part of the response
        return generated_text 

    except Exception as e:
        print(f"Error during chat conversation: {e}") # Log the error
        # Handle errors similarly to the /generate endpoint
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during the chat interaction: {str(e)}"
        )

# --- Optional: Add Uvicorn runner for direct execution ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)