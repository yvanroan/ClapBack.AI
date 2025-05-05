from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any

# Import models
from backend.app.api.models.schema import ChatInput, AIResponse

# Import services
from backend.app.services.scenarios import get_scenario, get_conversation_history, add_conversation_message
from backend.app.services.chat import process_chat
from backend.app.services.vector_service import VectorService

router = APIRouter()

@router.post("/process_chat", response_model=AIResponse)
async def process_chat_message(request: Request, chat_input: ChatInput):
    """
    Handles a chat message: retrieves context, formats prompt, gets AI response,
    and updates conversation history.
    """
    print(f"Received chat input: {chat_input}")
    
    # 1. Access resources initialized in lifespan
    chat_model = request.app.state.chat_model
    qdrant_client = getattr(request.app.state, "qdrant_client", None)
    collection_name = getattr(request.app.state, "collection_name", None)
    
    # Check if chat model is available
    if not chat_model:
        raise HTTPException(status_code=503, detail="Chat model service not available")
    
    # 2. Retrieve scenario details and history from storage
    scenario_data = get_scenario(chat_input.scenario_id)
    print(f"Scenario data")
    if not scenario_data:
        raise HTTPException(status_code=404, detail=f"Scenario '{chat_input.scenario_id}' not found.")
    
    # Get conversation history before adding the new message
    try:
        conversation_history = get_conversation_history(chat_input.scenario_id)
        print(f"Conversation history")
    except Exception as e:
        raise HTTPException(status_code=402, detail=f"Error getting conversation history: {str(e)}")

    # 3. Initialize vector service if available
    
    vector_service = VectorService(
        qdrant_client,
        collection_name
    )
        
    print(f"Vector service")
    # 4. Process the chat message
    try:
        print(f"DEBUG ROUTE: About to call process_chat for scenario {chat_input.scenario_id}")
        
        result = await process_chat(
            user_input=chat_input.user_input,
            scenario_id=chat_input.scenario_id,
            scenario_data=scenario_data,
            conversation_history=conversation_history,
            chat_model=chat_model,
            vector_service=vector_service
        )
        print(f"Result")
        if result["status"] == "error":

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing chat: {result.get('error', 'Unknown error')}"
            )
        
        ai_response_text = result["response"]
    except Exception as e:
        import traceback # Add import
        print("\n--- UNHANDLED EXCEPTION IN process_chat_message ---") # Header
        print(f"ERROR TYPE: {type(e).__name__}") # Print the type of error
        print(f"ERROR DETAILS: {e}\n")
        print("--- TRACEBACK ---")
        traceback.print_exc() # Print the full traceback
        print("--- END TRACEBACK ---\n")

        raise HTTPException(
            status_code=400,
            # status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing chat: {str(e)}"
        )
    print(f"AI response text")
    # 5. Update conversation history
    try:
        # Add user message
        add_conversation_message(
            chat_input.scenario_id, 
            {"role": "user", "content": chat_input.user_input}
        )
        
        # Add assistant message
        add_conversation_message(
            chat_input.scenario_id, 
            {"role": "assistant", "content": ai_response_text}
        )
        
        print(f"Updated history for scenario: {chat_input.scenario_id}")
    except Exception as e:
        print(f"Error updating conversation history: {e}")
        # Continue even if history update fails, just log the error
    
    # 6. Return the AI response
    return AIResponse(content=ai_response_text)
    
@router.post("/chat")
async def handle_chat(request: Request, prompt_request: Any):
    """
    General chat endpoint
    """
    # This is a placeholder for the future implementation
    
    return {"response": "Chat endpoint placeholder"} 