import os
import json
import chromadb
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from backend.app.core import settings, get_api_key_or_raise

def initialize_embedding_model():
    """Initialize the embedding model for vector search."""
    try:
        # Configure the Gemini API with the embedding-specific key
        embedding_api_key = get_api_key_or_raise("GEMINI_API_KEY_EMBEDDING")
        genai.configure(api_key=embedding_api_key)
        model = genai.GenerativeModel(settings.EMBEDDING_MODEL_NAME)
        print("Embedding model initialized successfully.")
        return model
    except Exception as e:
        print(f"Error initializing embedding model: {e}")
        return None

def initialize_chroma_client():
    """Initialize connection to the ChromaDB."""
    try:
        # Ensure the ChromaDB directory exists
        os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
        
        # Initialize the persistent client
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        return client
    except Exception as e:
        print(f"Error initializing ChromaDB client: {e}")
        return None

def get_or_create_collection(client, collection_name: str = settings.COLLECTION_NAME):
    """Get or create a ChromaDB collection."""
    if not client:
        print("ChromaDB client is not initialized.")
        return None
    
    try:
        # Get or create the collection
        collection = client.get_or_create_collection(
            name=collection_name
        )
        return collection
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

def embed_text(text: str) -> List[float]:
    """
    Generate embeddings for a text string.
    
    Args:
        text: The text to embed
        
    Returns:
        List of embedding values
    """
    return generate_embedding(text, settings.EMBEDDING_MODEL_NAME)

def store_document(
    collection,
    document_id: str,
    text: str,
    metadata: Dict[str, Any]
):
    """
    Store a document in the vector database.
    
    Args:
        collection: The ChromaDB collection
        document_id: Unique ID for the document
        text: The text content to embed and store
        metadata: Additional metadata for the document
    """
    try:
        # Generate embedding
        embedding = embed_text(text)
        if not embedding:
            print(f"Error: Failed to generate embedding for document {document_id}")
            return False
            
        # Add to collection
        collection.add(
            ids=[document_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        return True
    except Exception as e:
        print(f"Error storing document: {e}")
        return False

def process_and_store_blocks(input_filepath: str, collection, embedding_model=None):
    """
    Loads data, generates embeddings, and stores them in ChromaDB.
    
    Args:
        input_filepath: Path to the JSON file containing chunk data
        collection: ChromaDB collection to store embeddings
        embedding_model: Optional embedding model for generating embeddings
    """
    if not collection:
        print("Error: ChromaDB collection not initialized.")
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
    batch_embeddings = []
    batch_metadatas = []
    batch_ids = []
    batch_documents = [] # Store original text
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
                        # Handle potential non-JSON serializable types if necessary
                        # For now, assume values are basic types or lists/dicts compatible with ChromaDB
                        if isinstance(value, list) or isinstance(value, dict):
                             # ChromaDB often prefers storing complex types as JSON strings
                            metadata[key] = json.dumps(value)
                        elif value is not None: # Add if not None
                             metadata[key] = value
                        # else: skip None values implicitly
                else:
                    print(f"  Warning: tagging_result[0] for block {unique_doc_id} is not a dictionary. Skipping tags.")
            else:
                print(f"  Warning: Missing or invalid tagging_result for block {unique_doc_id}. Skipping tags.")

            # Remove None values from metadata for ChromaDB compatibility
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
            batch_embeddings.append(embedding)
            batch_metadatas.append(metadata)
            batch_ids.append(unique_doc_id)
            batch_documents.append(text_to_embed)
            total_blocks_processed += 1

            # 4. Add batch to ChromaDB if size reached
            if len(batch_ids) >= settings.BATCH_SIZE:
                print(f"  Adding batch of {len(batch_ids)} items to ChromaDB...")
                try:
                    collection.add(
                        embeddings=batch_embeddings,
                        metadatas=batch_metadatas,
                        documents=batch_documents, # Store the text itself
                        ids=batch_ids
                    )
                    print(f"  Batch added successfully.")
                    # Clear batches
                    batch_embeddings, batch_metadatas, batch_ids, batch_documents = [], [], [], []
                except Exception as e:
                    print(f"  Error adding batch to ChromaDB: {e}")
                    total_errors += len(batch_ids) # Count errors for the whole batch
                    # Decide how to handle batch errors (e.g., skip, retry individual items?)
                    # For now, clear batch and continue
                    batch_embeddings, batch_metadatas, batch_ids, batch_documents = [], [], [], [] 
                    

    # 5. Add any remaining items after the loop
    if batch_ids:
        print(f"Adding final batch of {len(batch_ids)} items to ChromaDB...")
        try:
            collection.add(
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                documents=batch_documents,
                ids=batch_ids
            )
            print(f"Final batch added successfully.")
        except Exception as e:
            print(f"Error adding final batch to ChromaDB: {e}")
            total_errors += len(batch_ids)

    print(f"\n--- Embedding and Storage Complete ---")
    print(f"Total blocks processed and attempted to add: {total_blocks_processed}")
    print(f"Total errors encountered: {total_errors}")
    print(f"Data stored in ChromaDB collection '{collection.name}' at '{settings.CHROMA_DB_DIR}'")

def retrieve_relevant_examples(
    collection,
    user_input: str,
    conversation_history: List[Dict[str, str]],
    scenario: Dict[str, Any],
    n_results: int = 5
):
    """
    Retrieve relevant examples from the vector database.
    
    Args:
        collection: The ChromaDB collection
        user_input: The current user input
        conversation_history: The conversation history
        scenario: The scenario data
        n_results: Number of results to retrieve
        
    Returns:
        Dict with retrieved examples
    """
    if not collection:
        print("Error: ChromaDB collection not initialized for retrieval.")
        return {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
            "documents": [[]]
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
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
            "documents": [[]]
        }
    print("Generated query embedding.")

    # 3. Construct ChromaDB metadata filter from scenario
    # Only include filters for keys present in the scenario dict
    scenario_filters = []
    for key, value in scenario.items():
        if value is not None:
            # Basic equality check for simplicity. Adjust if ranges or other operators are needed.
            scenario_filters.append({key: {"$eq": value}})
    
    where_filter = None
    if scenario_filters:
        where_filter = {"$or": scenario_filters}
    else:
        print("No scenario filters applied.")
    
    # 4. Query ChromaDB with embedding and metadata filter
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,  # Apply the filter here
            include=["metadatas", "documents", "distances"]  # Include relevant data
        )
        print(f"ChromaDB query successful. Found {len(results.get('ids', [[]])[0])} results.")
        return results
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
            "documents": [[]]
        } 