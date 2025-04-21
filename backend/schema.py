from pydantic import BaseModel, Field
from typing import Optional

class PromptRequest(BaseModel):
    prompt: str

class ScenarioData(BaseModel):
    # Define fields expected from the frontend form
    scenario_type: str = Field(..., description="Type of scenario (e.g., dating)")
    setting: str = Field(..., description="Setting of the scenario (e.g., coffee_shop)")
    goal: str = Field(..., description="Goal of the scenario (e.g., first_impression)")
    system_archetype: str = Field(..., description="Description of the AI character/archetype")
    roast_level: int = Field(..., ge=1, le=5, description="Roast level (1-5)")
    player_sex: str
    system_sex: str
    # Add any other fields from your formSchema

class ScenarioIDResponse(BaseModel):
    id: str = Field(..., description="The unique identifier generated for the scenario")

# Example model for a chat endpoint that might use the initialized resources
class ChatInput(BaseModel):
    scenario_id: str
    user_input: str

class AIResponse(BaseModel):
    content: str

class AssessmentResponse(BaseModel):
    # Define the expected structure of the assessment JSON
    primary_archetype: Optional[str] = None
    secondary_archetype: Optional[str] = None
    strengths: Optional[list[str]] = None # Changed to list based on prompt example
    weaknesses: Optional[list[str]] = None # Changed to list based on prompt example
    justification: Optional[str] = None
    highlights: Optional[list[str]] = None
    cringe_moments: Optional[list[str]] = None
    # Add overall_score, feedback, stats if the prompt actually requests them
    # overall_score: Optional[int] = None
    # feedback: Optional[str] = None
    # stats: Optional[dict] = None
    raw_text_response: Optional[str] = None # Field for fallback