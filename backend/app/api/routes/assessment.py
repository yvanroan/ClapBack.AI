from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any, Optional
import json
import os

# Import models
from backend.app.api.models.schema import AssessmentResponse

# Import services
from backend.app.services.scenarios import get_scenario, get_conversation_history
from backend.app.services.assessments import generate_conversation_assessment
from backend.app.utils.cleaner import clean_gemini_output
from backend.app.core import settings

router = APIRouter()

@router.post("/conversation/{scenario_id}/assess", response_model=AssessmentResponse)
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

    # 1. Retrieve conversation data using the scenarios service
    scenario_data = get_scenario(scenario_id)
    if not scenario_data:
        raise HTTPException(status_code=404, detail=f"Conversation scenario '{scenario_id}' not found.")
    
    conversation_history = get_conversation_history(scenario_id)
    if not conversation_history:
        raise HTTPException(status_code=400, detail="Cannot assess an empty conversation.")

    # 2. Generate assessment using the service
    try:
        # Use the updated service method that takes the chat_model
        result = await generate_conversation_assessment(
            conversation_history, 
            scenario_data,
            chat_model
        )
        
        if result["status"] == "error":
            print(f"ERROR: Assessment generation failed for {scenario_id}: {result.get('error', 'Unknown error')}")
            assessment_result = AssessmentResponse(raw_text_response=result["raw_text_response"])
        else:
            assessment_json = result["assessment"]
            try:
                assessment_result = AssessmentResponse(**assessment_json)
           
            except Exception as validation_error: # Catch potential Pydantic validation errors
                print(f"WARNING: Assessment JSON failed validation for {scenario_id}: {validation_error}")
                # Create a fallback response object with raw text
                assessment_result = AssessmentResponse(raw_text_response=generated_text)

        
    except Exception as e:
        print(f"Error generating assessment for {scenario_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the assessment: {str(e)}"
        )

    # 3. Save assessment to file
    if assessment_result:
        try:
            # Ensure downloads directory exists
            os.makedirs(settings.DOWNLOADS_DIR, exist_ok=True)
            
            # Construct file path
            file_path = os.path.join(settings.DOWNLOADS_DIR, f"{scenario_id}.json")
            
            # Structure the data to save
            data_to_save = {
                "scenario_id": scenario_id,
                "scenario_details": scenario_data,
                "conversation_history": conversation_history,
                "assessment_result": assessment_result
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

    # 4. Return the assessment
    return assessment_result 