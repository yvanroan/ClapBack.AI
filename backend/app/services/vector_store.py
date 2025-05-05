import os
import json
import qdrant_client
from qdrant_client.http import models
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from backend.app.core import settings, get_api_key_or_raise

def initialize_embedding_model():
    """Initialize the embedding model for vector search."""
    try:
        # Configure the Gemini API with the embedding-specific key
        embedding_api_key = get_api_key_or_raise("GEMINI_API_KEY")
        genai.configure(api_key=embedding_api_key)
        return settings.EMBEDDING_MODEL_NAME
    except Exception as e:
        print(f"Error initializing embedding model: {e}")
        return None

def initialize_qdrant_client():
    """Initialize connection to Qdrant."""
    try:
        # Check if we're using local or cloud Qdrant
        if settings.QDRANT_URL:
            client = qdrant_client.QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        else:
            print("the qdrant url is wrong")
            return None
        
        return client
    except Exception as e:
        print(f"Error initializing Qdrant client: {e}")
        return None

def get_or_create_collection(client, collection_name: str = settings.COLLECTION_NAME):
    """Get or create a Qdrant collection."""
    if not client:
        print("Qdrant client is not initialized.")
        return None
    
    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name not in collection_names:
            # Create the collection with the appropriate dimension
            # For Gemini embeddings, typically 768 dimensions
            vector_size = settings.EMBEDDING_DIMENSION  # Define this in settings (e.g. 768 for Gemini)
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                ),
            )
            print(f"Created new collection: {collection_name}")
        else:
            print(f"Using existing collection: {collection_name}")
            
        return collection_name  # Return collection name as Qdrant uses it directly
    except Exception as e:
        print(f"Error getting or creating collection: {e}")
        return None

def generate_embedding(text: str, model_name: str = settings.EMBEDDING_MODEL_NAME):
    """
    Generates embedding for the given text using the provided model name.
    
    Args:
        text: Text to generate embedding for
        model_name: Model name to use, defaults to settings.EMBEDDING_MODEL_NAME
        
    Returns:
        List of embedding values or None if generation fails
    """
    
    try:
        response = genai.embed_content(
            model=model_name,
            content=text, 
            task_type="retrieval_query"
        )
        return response["embedding"]
    except Exception as e:
        print(f"Error generating embedding for text (model: {model_name}): {e}")
        return None

def store_document(
    client,
    collection_name: str,
    document_id: str,
    text: str,
    metadata: Dict[str, Any]
):
    """
    Store a document in the vector database.
    
    Args:
        client: The Qdrant client
        collection_name: Name of the collection
        document_id: Unique ID for the document
        text: The text content to embed and store
        metadata: Additional metadata for the document
    """
    try:
        # Generate embedding
        embedding = generate_embedding(text, settings.EMBEDDING_MODEL_NAME)
        if not embedding:
            print(f"Error: Failed to generate embedding for document {document_id}")
            return False
            
        # Add to collection
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=document_id,
                    vector=embedding,
                    payload={
                        "text": text,
                        **metadata
                    }
                )
            ]
        )
        return True
    except Exception as e:
        print(f"Error storing document: {e}")
        return False

def process_and_store_blocks(input_filepath: str, client, collection_name: str):
    """
    Loads data, generates embeddings, and stores them in Qdrant.
    
    Args:
        input_filepath: Path to the JSON file containing chunk data
        client: Qdrant client to store embeddings
        collection_name: Name of the Qdrant collection
    """
    if not client or not collection_name:
        print("Error: Qdrant client or collection not initialized.")
        return

    # 1. Load the tagged data
    print(f"Loading tagged data from: {input_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_filepath}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from input file {input_filepath}. Error: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred while reading {input_filepath}: {e}")
        return

    if not isinstance(chunk_data, list):
        print(f"Error: Expected {input_filepath} to contain a JSON list of chunks.")
        return
    print(f"Loaded data for {len(chunk_data)} chunks.")

    # Lists for batch insertion
    batch_points = []
    total_blocks_processed = 0
    total_errors = 0

    # 2. Iterate through chunks and blocks
    for chunk_index, chunk in enumerate(chunk_data):
        chunk_num = chunk.get('chunk_num', chunk_index + 1)
        processed_blocks = chunk.get('processed_blocks', [])
        
        if not isinstance(processed_blocks, list):
             print(f"Warning: No valid 'processed_blocks' list found in chunk {chunk_num}. Skipping chunk.")
             continue
             
        print(f"Processing Chunk {chunk_num} ({len(processed_blocks)} blocks)")

        for block_index, block in enumerate(processed_blocks):
            block_id_from_data = block.get('block_id')
            # Use block_id if present, otherwise generate one based on index
            block_identifier = block_id_from_data if block_id_from_data is not None else f"idx_{block_index + 1}"
            unique_doc_id = f"chunk_{chunk_num}_block_{block_identifier}" 
            
            lines = block.get('lines')
            tagging_result = block.get('tagging_result')
            summary = block.get('summary') # Optional
            
            if not lines or not isinstance(lines, list):
                print(f"  Skipping block {block_identifier} in chunk {chunk_num} due to missing/invalid lines.")
                total_errors += 1
                continue

            # Prepare text and metadata
            text_to_embed = "\n".join(lines)
            metadata = {
                "chunk_num": chunk_num,
                "block_id": block_identifier, # Store the identifier we used
                "start_line": block.get("start_line"),
                "end_line": block.get("end_line"),
                "summary": summary if summary else "", # Ensure basic type
            }

            # Extract fields from tagging_result[0] and add to metadata
            if isinstance(tagging_result, list) and tagging_result:
                tagging_data = tagging_result[0] # Get the first element
                if isinstance(tagging_data, dict):
                    for key, value in tagging_data.items():
                        if isinstance(value, list) or isinstance(value, dict):
                            metadata[key] = json.dumps(value)
                        elif value is not None: # Add if not None
                             metadata[key] = value
                        # else: skip None values implicitly
                else:
                    print(f"  Warning: tagging_result[0] for block {unique_doc_id} is not a dictionary. Skipping tags.")
            else:
                print(f"  Warning: Missing or invalid tagging_result for block {unique_doc_id}. Skipping tags.")

            # Remove None values from metadata for Qdrant compatibility
            metadata = {k: v for k, v in metadata.items() if v is not None}

            # 3. Generate Embedding
            try:
                # Use the generate_embedding function
                embedding = generate_embedding(text_to_embed, settings.EMBEDDING_MODEL_NAME)
                if not embedding:
                     raise ValueError("Failed to generate embedding")
                     
            except Exception as e:
                print(f"  Error generating embedding for {unique_doc_id}: {e}")
                total_errors += 1
                continue # Skip adding this block if embedding failed
            
            # Add to batch
            batch_points.append(
                models.PointStruct(
                    id=unique_doc_id,
                    vector=embedding,
                    payload={
                        "text": text_to_embed,
                        **metadata
                    }
                )
            )
            total_blocks_processed += 1

            # 4. Add batch to Qdrant if size reached
            if len(batch_points) >= settings.BATCH_SIZE:
                print(f"  Adding batch of {len(batch_points)} items to Qdrant...")
                try:
                    client.upsert(
                        collection_name=collection_name,
                        points=batch_points
                    )
                    print(f"  Batch added successfully.")
                    # Clear batch
                    batch_points = []
                except Exception as e:
                    print(f"  Error adding batch to Qdrant: {e}")
                    total_errors += len(batch_points) # Count errors for the whole batch
                    batch_points = []

    # 5. Add any remaining items after the loop
    if batch_points:
        print(f"Adding final batch of {len(batch_points)} items to Qdrant...")
        try:
            client.upsert(
                collection_name=collection_name,
                points=batch_points
            )
            print(f"Final batch added successfully.")
        except Exception as e:
            print(f"Error adding final batch to Qdrant: {e}")
            total_errors += len(batch_points)

    print(f"\n--- Embedding and Storage Complete ---")
    print(f"Total blocks processed and attempted to add: {total_blocks_processed}")
    print(f"Total errors encountered: {total_errors}")


def retrieve_relevant_examples(
    client,
    collection_name: str,
    user_input: str,
    conversation_history: List[Dict[str, str]],
    scenario: Dict[str, Any],
    n_results: int = 5
):
    """
    Retrieve relevant examples from the vector database.
    
    Args:
        client: The Qdrant client
        collection_name: Name of the collection
        user_input: The current user input
        conversation_history: The conversation history
        scenario: The scenario data
        n_results: Number of results to retrieve
        
    Returns:
        Dict with retrieved examples
    """
    if not client or not collection_name:
        print("Error: Qdrant client or collection not initialized for retrieval.")
        return {
            "ids": [],
            "scores": [],
            "payloads": [],
            "documents": []
        }

    # 1. Construct combined query text
    history_str = " ".join([turn.get("content", "") for turn in conversation_history[-3:]])  # Last 3 turns
    scenario_str = " ".join([f"{k}:{v}" for k, v in scenario.items() if v is not None])
    query_text = f"{user_input} [History: {history_str}] [Scenario: {scenario_str}]"
    
    # 2. Generate embedding for query
    query_embedding = generate_embedding(query_text, settings.EMBEDDING_MODEL_NAME)
    if not query_embedding:
        print("Failed to generate query embedding.")
        return {
            "ids": [],
            "scores": [],
            "payloads": [],
            "documents": []
        }
    print("Generated query embedding.")

    # 3. Construct Qdrant metadata filter from scenario
    # Only include filters for keys present in the scenario dict
    filter_conditions = []
    for key, value in scenario.items():
        if value is not None:
            # Basic equality check for simplicity
            filter_conditions.append(
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                )
            )
    
    filter_query = None
    if filter_conditions:
        filter_query = models.Filter(
            must=filter_conditions  # All conditions must match (AND)
            # To use OR logic, use should=filter_conditions instead
        )
    else:
        print("No scenario filters applied.")
    
    # 4. Query Qdrant with embedding and metadata filter
    try:
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=n_results,
            query_filter=filter_query,
            with_payload=True
        )
        
        # 5. Format results to match the previous format
        formatted_results = {
            "ids": [point.id for point in results],
            "scores": [point.score for point in results],
            "payloads": [point.payload for point in results],
            "documents": [point.payload.get("text", "") for point in results]
        }
        
        print(f"Qdrant query successful. Found {len(formatted_results['ids'])} results.")
        return formatted_results
    except Exception as e:
        print(f"Error querying Qdrant: {e}")
        return {
            "ids": [],
            "scores": [],
            "payloads": [],
            "documents": []
        }

# Add these to your settings.py file:
"""
# Qdrant settings
QDRANT_URL = os.getenv("QDRANT_URL", "")  # For cloud instance
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")  # For cloud instance
EMBEDDING_DIMENSION = 768  # For Gemini embeddings
"""