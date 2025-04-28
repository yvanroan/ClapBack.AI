from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any
import time
import uuid

# Import models
from backend.schema import ScenarioData, ScenarioIDResponse

# Import services
from backend.app.services.scenarios import create_scenario, get_scenario, generate_scenario_id

router = APIRouter()

@router.post("/scenario", response_model=ScenarioIDResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario_route(scenario_input: ScenarioData):
    """
    Receives scenario details from the frontend, generates a unique ID,
    stores the scenario (in-memory), and returns the unique scenario ID.
    """
    print(f"Received scenario input: {scenario_input}")
    try:
        # 1. Generate Unique ID
        scenario_id = generate_scenario_id()

        # 2. Create ScenarioData object (useful for storage)
        scenario_data = ScenarioData(
            **scenario_input.dict()  # Unpack validated input data
        )

        # 3. Store the scenario using the service
        stored_scenario_id = create_scenario(scenario_data.dict())
        print(f"Scenario created and stored (in-memory): {stored_scenario_id}")

        # 4. Return only the ID
        return ScenarioIDResponse(id=stored_scenario_id)
    except Exception as e:
        print(f"Error creating scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while creating the scenario: {str(e)}"
        )
    
@router.get("/scenario/{scenario_id}", response_model=ScenarioData)
async def get_scenario_data(scenario_id: str):
    """
    Retrieves the full scenario data for a given scenario ID.
    """
    print(f"Received request for scenario data: {scenario_id}")
    scenario_data = get_scenario(scenario_id)
    if not scenario_data:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    
    # Return the scenario data as a ScenarioData model
    return ScenarioData(**scenario_data) 