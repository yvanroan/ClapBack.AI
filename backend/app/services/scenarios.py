import uuid
import time
from typing import Dict, List, Any, Optional

# In-memory storage (replace with database in production)
scenarios_db: Dict[str, Any] = {}

def generate_scenario_id() -> str:
    """Generate a unique scenario ID."""
    timestamp = int(time.time())
    unique_uuid = uuid.uuid4()
    return f"conversation-{timestamp}-{unique_uuid}"

def create_scenario(scenario_data: Dict[str, Any]) -> str:
    """
    Create a new scenario and store it.
    
    Args:
        scenario_data: The scenario data
        
    Returns:
        The generated scenario ID
    """
    # Generate ID
    scenario_id = generate_scenario_id()
    
    
    # Store in memory (replace with database in production)
    scenarios_db[scenario_id] = {
        "scenario_data": scenario_data,
        "conversation_history": []
    }
    
    return scenario_id

def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a scenario by ID.
    
    Args:
        scenario_id: The scenario ID
        
    Returns:
        The scenario data or None if not found
    """
    scenario_container = scenarios_db.get(scenario_id)
    
    if not scenario_container or "scenario_data" not in scenario_container:
        return None
    
    return scenario_container["scenario_data"]

def add_conversation_message(scenario_id: str, message: Dict[str, Any]) -> bool:
    """
    Add a message to a conversation.
    
    Args:
        scenario_id: The scenario ID
        message: The message to add
        
    Returns:
        True if successful, False otherwise
    """
    scenario_container = scenarios_db.get(scenario_id)
    if not scenario_container:
        return False
    
    if "conversation_history" not in scenario_container:
        scenario_container["conversation_history"] = []
    
    scenario_container["conversation_history"].append(message)
    return True

def get_conversation_history(scenario_id: str) -> List[Dict[str, Any]]:
    """
    Get the conversation history for a scenario.
    
    Args:
        scenario_id: The scenario ID
        
    Returns:
        The conversation history
    """
    scenario_container = scenarios_db.get(scenario_id)
    if not scenario_container or "conversation_history" not in scenario_container:
        return []
    
    return scenario_container["conversation_history"] 