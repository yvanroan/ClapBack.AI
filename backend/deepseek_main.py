import os
# Use the OpenAI library, compatible with DeepSeek
from openai import OpenAI 
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# --- Configuration ---\
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com" # DeepSeek API endpoint

if not DEEPSEEK_API_KEY:
    print("Error: DEEPSEEK_API_KEY not found in environment variables.")
    exit(1)
    # In a real app, raise a proper configuration error or exit
    
# Create FastAPI app
app = FastAPI(
    title="DeepSeek API Backend",
    description="A simple FastAPI backend to interact with the DeepSeek API.",
    version="1.0.0",
    debug=True  # Enable debug mode for more detailed logging
)

# Configure CORS (copied from main.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"], # Adjust origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---\
# Reusing the same request model as Gemini version
class PromptRequest(BaseModel):
    prompt: str = Field(..., description="The text prompt to send to the API.")

# --- DeepSeek Client Initialization ---
# Initialize the OpenAI client pointing to DeepSeek
try:
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
except Exception as e:
    print(f"Error initializing DeepSeek client: {e}")
    # Handle initialization error appropriately
    client = None # Ensure client is None if initialization fails

# --- API Endpoints ---\
@app.get("/", summary="Root endpoint for health check")
async def read_root():
    """Provides a simple welcome message."""
    return {"message": "Welcome to the DeepSeek API Backend"}

@app.post("/generate", 
          summary="Generate text using DeepSeek",
          status_code=status.HTTP_200_OK)
async def generate_text_from_deepseek(request: PromptRequest):
    """
    Receives a text prompt and returns the generated text from the DeepSeek API.
    Handles potential errors during the API call.
    """

    try:
        # Make the API call using the chat completions endpoint
        response = client.chat.completions.create(
            model="deepseek-chat",  # Specify the DeepSeek model
            messages=[
                {"role": "user", "content": request.prompt}
            ],
            # You can add other parameters like temperature, max_tokens here
            # temperature=0.7, 
            # max_tokens=1024, 
        )

        # Extract the generated text
        # Check response structure based on DeepSeek/OpenAI format
        if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DeepSeek API returned an empty or invalid response structure."
            )
            
        generated_text = response.choices[0].message.content.strip()

        # Return the raw text string
        return generated_text

    except Exception as e:
        print(f"Error calling DeepSeek API: {e}") # Log the error
        # More specific error handling based on openai.APIError etc. could be added
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while communicating with the DeepSeek API: {str(e)}"
        )

# --- Uvicorn Runner ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server for DeepSeek API...")
    print(f"DeepSeek API Key Loaded: {'Yes' if DEEPSEEK_API_KEY else 'No'}")
    # Run on port 8001
    uvicorn.run(app, host="0.0.0.0", port=8001) 