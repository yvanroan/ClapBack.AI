import json
from typing import Dict, List, Any, Optional
from backend.app.core import settings
from backend.app.utils.cleaner import clean_gemini_output
from backend.data.prompts.prompts import main_convo_prompt

async def format_chat_prompt(
    user_input: str,
    conversation_history: List[Dict[str, str]],
    scenario_data: Dict[str, Any],
    retrieved_examples: Dict[str, Any]
) -> str:
    """
    Format the chat prompt with user input, conversation history, scenario data, and retrieved examples.
    
    Args:
        user_input: The current user input
        conversation_history: The conversation history before this message
        scenario_data: The scenario data
        retrieved_examples: Examples retrieved from vector store
        
    Returns:
        Formatted chat prompt
    """
    try:
        formatted_history = "\n".join([
            f"{turn.get('role', 'unknown')}: {turn.get('content', '')}" 
            for turn in conversation_history
        ])
        
        # Format retrieved examples for prompt
        formatted_examples = json.dumps(retrieved_examples, indent=2)
        
        # Load roast scale
        roast_scale = {}
        try:
            archetypes_path = settings.ARCHETYPES_FILE
            with open(archetypes_path, 'r', encoding='utf-8') as f:
                archetypes_data = json.load(f)
                roast_scale = archetypes_data.get('roast_scale_profile', {})
        except Exception as e:
            print(f"Warning: Error loading roast scale: {e}")
        
        # Get scenario details
        roast_level = scenario_data.get('roast_level', 'N/A')
        system_archetype = scenario_data.get('system_archetype', 'N/A')
        
        # Get roast level profile
        roast_level_profile = "Cute little roast attempts. Think 'Did I say that out loud?' followed by nervous giggling. Still loves you."
        if system_archetype in roast_scale and str(roast_level) in roast_scale.get(system_archetype, {}):
            roast_level_profile = roast_scale[system_archetype][str(roast_level)]
        
        # Create information dictionary for the chat prompt
        information = {
            'scenario_type': scenario_data.get('type', 'N/A'),
            'scenario_setting': scenario_data.get('setting', 'N/A'),
            'scenario_goal': scenario_data.get('goal', 'N/A'),
            'system_archetype': system_archetype,
            'roast_level': roast_level_profile,
            'player_sex': scenario_data.get('player_sex', 'N/A'),
            'system_sex': scenario_data.get('system_sex', 'N/A'),
            'conversation_history': formatted_history,
            'current_input': user_input,
            'retrieved_examples': formatted_examples
        }
        
        # Generate the final prompt
        final_prompt = main_convo_prompt(information)
        return final_prompt
    except Exception as e:
        print(f"Error formatting chat prompt: {e}")
        raise ValueError(f"Failed to format chat prompt: {str(e)}")

async def process_chat(
    user_input: str,
    scenario_id: str,
    scenario_data: Dict[str, Any],
    conversation_history: List[Dict[str, str]],
    chat_model,
    vector_service=None
) -> Dict[str, Any]:
    """
    Process a chat message using the AI model.
    
    Args:
        user_input: The user's input text
        scenario_id: The scenario ID
        scenario_data: The scenario data
        conversation_history: The conversation history
        chat_model: The AI chat model
        vector_service: Optional service for vector retrieval
        
    Returns:
        Dict with AI response and status
    """
    try:
        # Retrieve examples from vector store if available
        retrieved_examples = []
        if vector_service:
            try:
                print(f"Retrieving relevant examples for scenario: {scenario_id}")
                retrieved_examples_raw = await vector_service.retrieve_relevant_examples(
                    user_input=user_input,
                    conversation_history=conversation_history,
                    scenario=scenario_data,
                    n_results=5
                )
                
                # Format retrieved examples
                if retrieved_examples_raw:
                    ids = retrieved_examples_raw.get("ids", [[]])
                    metadatas = retrieved_examples_raw.get("metadatas", [[]])
                    documents = retrieved_examples_raw.get("documents", [[]])
                    
                    if ids and isinstance(ids, list) and ids[0] and \
                    metadatas and isinstance(metadatas, list) and metadatas[0] and \
                    documents and isinstance(documents, list) and documents[0]:
                        num_results = len(ids[0])
                        if len(metadatas[0]) == num_results and len(documents[0]) == num_results:
                            for i in range(num_results):
                                retrieved_examples.append({
                                    "metadata": metadatas[0][i],
                                    "document": documents[0][i]
                                })
            except Exception as e:
                print(f"Error retrieving examples: {e}")
                # Continue without examples if retrieval fails
        
        # Format the chat prompt
        final_prompt = await format_chat_prompt(
            user_input=user_input,
            conversation_history=conversation_history,
            scenario_data=scenario_data,
            retrieved_examples=retrieved_examples
        )
        
        # Generate response using the AI model
        print(f"Sending final prompt to AI for scenario: {scenario_id}")
        response = await chat_model.generate_content_async(final_prompt)
        ai_response_text = response.text
        print(f"Received AI response for scenario: {scenario_id}")
        
        return {
            "response": ai_response_text,
            "status": "success"
        }
    except Exception as e:
        print(f"Error processing chat: {e}")
        return {
            "error": f"Error processing chat: {str(e)}",
            "status": "error"
        } 