import json
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb

# --- Configuration ---
load_dotenv()

INPUT_FILE = "downloads/-ftgC4oWf6s_tagged_with_scenario.json"
CHROMA_DB_PATH = "chroma_db" # Directory to store persistent DB
COLLECTION_NAME = "transcript_blocks"
EMBEDDING_MODEL_NAME = "models/embedding-001"
BATCH_SIZE = 100 # Number of items to add to ChromaDB at a time
ARCHETYPES_FILE = "archetypes.json"
with open(ARCHETYPES_FILE, 'r', encoding='utf-8') as f:
    archetypes = json.load(f)



# --- Initialize Services ---
def initialize_embedding_model():
    """Initializes and returns the Google Generative AI embedding model."""
    print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}")
    api_key = os.getenv("GEMINI_API_KEY_EMBEDDING")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(EMBEDDING_MODEL_NAME)
        print("Embedding model initialized successfully.")
        return model
    except Exception as e:
        print(f"Error initializing embedding model: {e}")
        return None

def initialize_chroma_client():
    """Initializes and returns a persistent ChromaDB client."""
    print(f"Initializing ChromaDB client (persistent path: {CHROMA_DB_PATH})")
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        print("ChromaDB client initialized successfully.")
        return client
    except Exception as e:
        print(f"Error initializing ChromaDB client: {e}")
        return None

def get_or_create_collection(client):
    """Gets or creates the ChromaDB collection."""
    if not client:
        return None
    print(f"Getting or creating ChromaDB collection: {COLLECTION_NAME}")
    try:
        # You might specify metadata for the embedding function if needed,
        # but here we are adding pre-computed embeddings.
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' ready.")
        return collection
    except Exception as e:
        print(f"Error getting or creating collection '{COLLECTION_NAME}': {e}")
        return None

# --- Core Processing Function ---
def process_and_store_blocks(input_filepath, collection, embedding_model):
    """Loads data, generates embeddings, and stores them in ChromaDB."""
    if not collection or not embedding_model:
        print("Error: ChromaDB collection or embedding model not initialized.")
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
                # print(f"  Generating embedding for {unique_doc_id}...") # Verbose logging
                response = genai.embed_content(model=EMBEDDING_MODEL_NAME, content=text_to_embed, task_type="retrieval_document")
                embedding = response['embedding']
                if not embedding:
                     raise ValueError("API returned empty embedding")
                     
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
            if len(batch_ids) >= BATCH_SIZE:
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
    print(f"Data stored in ChromaDB collection '{COLLECTION_NAME}' at '{CHROMA_DB_PATH}'")

# --- Embedding Helper ---
def generate_embedding(text: str, model_name: str):
    """Generates embedding for the given text using the provided model name."""
    # Removed check for initialized model object, as we only need the name
    try:
        response = genai.embed_content(
            model=model_name, # Pass the model name string
            content=text, 
            task_type="retrieval_query"
        )
        return response["embedding"]
    except Exception as e:
        print(f"Error generating embedding for text (model: {model_name}): ", e)
        return None

# --- Retrieval Function ---
# Removed embedding_model object parameter, uses global constant instead
def retrieve_relevant_examples(collection, user_input: str, conversation_history: list, scenario: dict, n_results: int = 5):
    """Retrieves relevant examples from ChromaDB based on input, history, and scenario.

    Args:
        user_input: The latest user message.
        conversation_history: List of conversation turns (dicts with role/content).
        scenario: Dictionary describing the current scenario.
        collection: Initialized ChromaDB collection object.
        n_results: Number of results to retrieve.

    Returns:
        The query results from ChromaDB, filtered by the scenario.
    """
    if not collection:
        print("Error: ChromaDB collection not initialized for retrieval.")
        return None

    # 1. Construct combined query text
    history_str = " ".join([turn.get("content", "") for turn in conversation_history[-3:]]) # Last 3 turns
    scenario_str = " ".join([f"{k}:{v}" for k, v in scenario.items() if v is not None])
    query_text = f"{user_input} [History: {history_str}] [Scenario: {scenario_str}]"
    

    # 2. Generate embedding for query
    # Pass the global model name string
    query_embedding = generate_embedding(query_text, EMBEDDING_MODEL_NAME) 
    if not query_embedding:
        print("Failed to generate query embedding.")
        return None
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
        # print(f"Constructed ChromaDB Where Filter: {where_filter}")
    else:
        print("No scenario filters applied.")
        

    # 4. Query ChromaDB with embedding and metadata filter
    # print(f"Querying ChromaDB collection '{collection.name}' for {n_results} results...")
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter, # Apply the filter here
            include=["metadatas", "documents", "distances"] # Include relevant data
        )
        print(f"ChromaDB query successful. Found {len(results.get('ids', [[]])[0])} results.")
        return results
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return None

# --- Main Execution --- 
if __name__ == "__main__":
    print("--- Starting Vector Store Script ---")
    model = initialize_embedding_model() # Still initialize for populating
    chroma_client = initialize_chroma_client()
    chroma_collection = get_or_create_collection(chroma_client)


    # --- Test Retrieval AFTER Populating --- 
    if chroma_collection: # Only need collection for retrieval now
        try: 
             
            print("\n--- Testing Retrieval --- ")
            # Example Usage Data (from user query)
            example_user_input = "That sounds exciting. I've never tried it."
            example_conversation_history = [
                {"role": "system", "content": "You are engaging in a first date scenario at a coffee shop."},
                {"role": "user", "content": "So, what do you do for fun on weekends?"},
                {"role": "assistant", "content": "I'm really into rock climbing lately. The adrenaline rush is addictive!"},
                {"role": "user", "content": "That sounds exciting. I've never tried it."}
            ]

            archetype_key = "The Certified Baddie"
            example_scenario = {
                "type": "dating",
                "setting": "coffee_shop",
                "goal": "first_impression",
                "system_archetype": archetype_key+ ", " + archetypes["system_archetypes"][archetype_key],
                "roast_level": 3,
                "player_sex": "male",
                "system_sex": "female"
            }

            # Remove the embedding_model parameter from the call
            retrieved_examples = retrieve_relevant_examples(
                collection=chroma_collection,
                user_input=example_user_input,
                conversation_history=example_conversation_history,
                scenario=example_scenario,
                n_results=5
            )

            if retrieved_examples:
                print("\n--- Retrieved Examples --- ")
                # Pretty print the results (or relevant parts)
                ids = retrieved_examples.get("ids", [[]])[0]
                distances = retrieved_examples.get("distances", [[]])[0]
                metadatas = retrieved_examples.get("metadatas", [[]])[0]
                documents = retrieved_examples.get("documents", [[]])[0]

                for i, doc_id in enumerate(ids):
                    print(f"  Result {i+1}:")
                    print(f"    ID: {doc_id}")
                    print(f"    Distance: {distances[i]:.4f}")
                    print(f"    Metadata: {metadatas[i]}")
                    print(f"    Document: {documents[i][:100]}...") # Print start of doc
                    print("---")
            else:
                print("Retrieval failed or returned no results.")
        except Exception as e:
             print(f"Could not get collection count or run retrieval: {e}")

    else:
         print("Cannot populate or test retrieval due to initialization errors.")
    
    print("--- Vector Store Script Finished ---") 