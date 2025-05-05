from typing import Dict, List, Any, Optional
import json
from backend.app.core import settings

class VectorService:
    """Service for vector database operations."""
    
    def __init__(self, qdrant_client=None, collection_name=None):
        """
        Initialize the vector service.
        
        Args:
            qdrant_client: The Qdrant client for retrieval
            collection_name: The name of the Qdrant collection
        """
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name or settings.COLLECTION_NAME
    
    async def retrieve_relevant_examples(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        scenario: Dict[str, Any],
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant examples from the vector database.
        
        Args:
            user_input: The current user input
            conversation_history: The conversation history
            scenario: The scenario data
            n_results: Number of results to retrieve
            
        Returns:
            Dict with retrieved examples
        """
        if not self.qdrant_client or not self.collection_name:
            print("Vector service resources not available")
            return {}
        
        try:
            # Use the implementation from vector_store.py directly
            from backend.app.services.vector_store import retrieve_relevant_examples as retrieve_examples
            
            results = retrieve_examples(
                client=self.qdrant_client,
                collection_name=self.collection_name,
                user_input=user_input,
                conversation_history=conversation_history,
                scenario=scenario,
                n_results=n_results
            )
            
            return results
        except Exception as e:
            print(f"Error retrieving examples: {e}")
            return {}