import os
import argparse
import json
import time
from dotenv import load_dotenv
import google.generativeai as genai
import chromadb
import requests
from typing import Optional, Dict, List, Any, Tuple

# Import existing components
from back import download_audio, transcribe_youtube_audio
from cleaner import clean_gemini_output
from prompts import tagging_prompt, chunking_prompt
from merge_scenario import extract_scenarios

# Load environment variables
load_dotenv()

# --- Configuration ---
CHROMA_DB_PATH = "chroma_db"  # Directory to store persistent DB
COLLECTION_NAME = "transcript_blocks"
EMBEDDING_MODEL_NAME = "models/embedding-001"
BATCH_SIZE = 100  # Number of items to add to ChromaDB at a time
API_ENDPOINT = "http://localhost:8000/generate"  # Your Gemini API endpoint
API_TIMEOUT = 120  # Seconds before timeout for API calls
DELAY_BETWEEN_CALLS = 2  # Seconds delay between API calls

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
        return EMBEDDING_MODEL_NAME
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
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' ready.")
        return collection
    except Exception as e:
        print(f"Error getting or creating collection '{COLLECTION_NAME}': {e}")
        return None

# --- Step 1: Download and Transcribe YouTube Video ---
def process_youtube_video(youtube_url: str) -> Optional[str]:
    """Downloads and transcribes a YouTube video, returning the path to the transcript file."""
    print(f"\n=== Step 1: Downloading and Transcribing YouTube Video ===")
    try:
        print(f"Processing YouTube URL: {youtube_url}")
        transcript_path = transcribe_youtube_audio(youtube_url)
        print(f"Transcription completed: {transcript_path}")
        return transcript_path
    except Exception as e:
        print(f"Error processing YouTube video: {e}")
        return None

# --- Step 2: Chunk and Clean Transcript ---
def chunk_transcript(transcript_path: str) -> Optional[str]:
    """Chunks the transcript into manageable pieces and cleans them."""
    print(f"\n=== Step 2: Chunking and Cleaning Transcript ===")
    
    # Read the transcript file
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        return None
    
    # Prepare chunking prompt
    try:
        chunking_api_prompt = chunking_prompt(transcript_text)
    except Exception as e:
        print(f"Error creating chunking prompt: {e}")
        return None
    
    # Call API for chunking
    print("Sending chunking request to API...")
    try:
        payload = {"prompt": chunking_api_prompt}
        response = requests.post(API_ENDPOINT, json=payload, timeout=API_TIMEOUT)
        response.raise_for_status()
        api_result = response.json()
        
        # Clean and process the response
        chunked_data = clean_gemini_output(api_result)
        if not chunked_data:
            print("Error: Failed to clean chunking output")
            return None
            
        # Save chunked data
        video_id = os.path.basename(transcript_path).split('_')[0]
        chunked_file_path = f"downloads/{video_id}_with_speakers_gemini_output_chunked_cleaned.json"
        with open(chunked_file_path, 'w', encoding='utf-8') as f:
            json.dump(chunked_data, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully chunked transcript: {chunked_file_path}")
        return chunked_file_path
    
    except requests.exceptions.RequestException as e:
        print(f"API request error during chunking: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during chunking: {e}")
        return None

# --- Step 3: Tag Transcript Chunks ---
def tag_transcript_chunks(chunked_file_path: str) -> Optional[str]:
    """Tags each chunk of the transcript with metadata."""
    print(f"\n=== Step 3: Tagging Transcript Chunks ===")
    
    # Read the chunked data
    try:
        with open(chunked_file_path, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
    except Exception as e:
        print(f"Error reading chunked file: {e}")
        return None
    
    if not isinstance(chunk_data, list):
        print(f"Error: Expected chunked file to contain a JSON list.")
        return None
    
    processed_chunk_data = []
    
    # Process each chunk
    for chunk_index, chunk in enumerate(chunk_data):
        chunk_num = chunk.get('chunk_num', chunk_index + 1)
        print(f"\nProcessing Chunk {chunk_num}")
        
        original_blocks = chunk.get('cleaned_data', [])
        chunk_error = chunk.get('error')
        processed_chunk = {
            'chunk_num': chunk_num,
            'processed_blocks': []
        }
        
        if chunk_error:
            print(f"Skipping chunk {chunk_num} due to previous error: {chunk_error}")
            processed_chunk['error'] = chunk_error
            processed_chunk_data.append(processed_chunk)
            continue
        
        # Process each block in the chunk
        for block_index, block in enumerate(original_blocks):
            block_id = block.get('block_id', block_index + 1)
            lines = block.get('lines', [])
            processed_block = block.copy()
            
            print(f"Processing Block {block_id}...")
            
            if not lines or not isinstance(lines, list):
                print(f"Warning: Missing or invalid 'lines' for block {block_id}. Skipping tagging.")
                processed_block['tagging_error'] = "Missing or invalid lines data"
                processed_chunk['processed_blocks'].append(processed_block)
                continue
            
            # Prepare tagging prompt
            try:
                tagging_api_prompt = tagging_prompt(processed_block)
            except Exception as e:
                print(f"Error creating prompt for block {block_id}: {e}")
                processed_block['tagging_error'] = f"Prompt creation error: {e}"
                processed_chunk['processed_blocks'].append(processed_block)
                continue
            
            # Call API for tagging
            try:
                payload = {"prompt": tagging_api_prompt}
                response = requests.post(API_ENDPOINT, json=payload, timeout=API_TIMEOUT)
                response.raise_for_status()
                api_result = response.json()
                
                cleaned_tags = clean_gemini_output(api_result)
                if cleaned_tags:
                    print(f"Successfully cleaned tags for block {block_id}.")
                    processed_block['tagging_result'] = cleaned_tags
                else:
                    print(f"Error: Cleaning failed for block {block_id} tags.")
                    processed_block['tagging_error'] = "Tag cleaning failed"
                    processed_block['raw_tagging_response'] = api_result
            
            except requests.exceptions.RequestException as e:
                print(f"API request error for block {block_id}: {e}")
                processed_block['tagging_error'] = f"API request error: {e}"
            except Exception as e:
                print(f"Unexpected error processing block {block_id}: {e}")
                processed_block['tagging_error'] = f"Unexpected error: {e}"
            
            processed_chunk['processed_blocks'].append(processed_block)
            time.sleep(DELAY_BETWEEN_CALLS)
        
        processed_chunk_data.append(processed_chunk)
    
    # Save tagged data
    video_id = os.path.basename(chunked_file_path).split('_')[0]
    tagged_file_path = f"downloads/{video_id}_tagged.json"
    with open(tagged_file_path, 'w', encoding='utf-8') as f:
        json.dump(processed_chunk_data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully tagged transcript: {tagged_file_path}")
    return tagged_file_path

# --- Step 4: Extract Scenarios ---
def extract_scenarios_from_tags(tagged_file_path: str) -> Optional[str]:
    """Extracts scenario information from the tagged transcript."""
    print(f"\n=== Step 4: Extracting Scenarios ===")
    
    try:
        # Call the existing extract_scenarios function
        video_id = os.path.basename(tagged_file_path).split('_')[0]
        output_file_path = f"downloads/{video_id}_tagged_with_scenario.json"
        
        extract_scenarios(tagged_file_path, output_file_path)
        
        print(f"Successfully extracted scenarios: {output_file_path}")
        return output_file_path
    
    except Exception as e:
        print(f"Error extracting scenarios: {e}")
        return None

# --- Step 5: Generate Embeddings and Store in Vector DB ---
def generate_embedding(text: str, model_name: str):
    """Generate an embedding for the provided text using the specified model."""
    try:
        response = genai.embed_content(model=model_name, content=text, task_type="retrieval_document")
        embedding = response['embedding']
        return embedding
    except Exception as e:
        print(f"Error generating embedding for text: {e}")
        return None

def process_and_store_blocks(input_filepath: str, collection, embedding_model: str):
    """Loads data, generates embeddings, and stores them in ChromaDB."""
    print(f"\n=== Step 5: Generating Embeddings and Storing in Vector DB ===")
    
    if not collection or not embedding_model:
        print("Error: ChromaDB collection or embedding model not initialized.")
        return False
    
    # Load the tagged data with scenarios
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
    except Exception as e:
        print(f"Error reading tagged data with scenarios: {e}")
        return False
    
    if not isinstance(chunk_data, list):
        print(f"Error: Expected {input_filepath} to contain a JSON list of chunks.")
        return False
    
    # Prepare batches for insertion
    batch_embeddings = []
    batch_metadatas = []
    batch_ids = []
    batch_documents = []
    total_blocks_processed = 0
    total_errors = 0
    
    # Process each chunk
    for chunk_index, chunk in enumerate(chunk_data):
        chunk_num = chunk.get('chunk_num', chunk_index + 1)
        processed_blocks = chunk.get('processed_blocks', [])
        scenario_data = chunk.get('scenario', {})
        
        print(f"Processing Chunk {chunk_num} ({len(processed_blocks)} blocks)")
        
        for block_index, block in enumerate(processed_blocks):
            block_id_from_data = block.get('block_id')
            block_identifier = block_id_from_data if block_id_from_data is not None else f"idx_{block_index + 1}"
            unique_doc_id = f"chunk_{chunk_num}_block_{block_identifier}"
            
            lines = block.get('lines')
            tagging_result = block.get('tagging_result')
            summary = block.get('summary')
            
            if not lines or not isinstance(lines, list):
                print(f"Skipping block {block_identifier} in chunk {chunk_num} due to missing/invalid lines.")
                total_errors += 1
                continue
            
            # Prepare text and metadata
            text_to_embed = "\n".join(lines)
            metadata = {
                "chunk_num": chunk_num,
                "block_id": block_identifier,
                "start_line": block.get("start_line"),
                "end_line": block.get("end_line"),
                "summary": summary if summary else ""
            }
            
            # Add scenario data to metadata
            if scenario_data:
                for key, value in scenario_data.items():
                    if value is not None:
                        if isinstance(value, (list, dict)):
                            metadata[key] = json.dumps(value)
                        else:
                            metadata[key] = value
            
            # Extract fields from tagging_result and add to metadata
            if isinstance(tagging_result, list) and tagging_result:
                tagging_data = tagging_result[0]
                if isinstance(tagging_data, dict):
                    for key, value in tagging_data.items():
                        if isinstance(value, (list, dict)):
                            metadata[key] = json.dumps(value)
                        elif value is not None:
                            metadata[key] = value
            
            # Remove None values from metadata
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            # Generate embedding
            embedding = generate_embedding(text_to_embed, embedding_model)
            if not embedding:
                print(f"Error generating embedding for {unique_doc_id}. Skipping.")
                total_errors += 1
                continue
            
            # Add to batch
            batch_embeddings.append(embedding)
            batch_metadatas.append(metadata)
            batch_ids.append(unique_doc_id)
            batch_documents.append(text_to_embed)
            total_blocks_processed += 1
            
            # Add batch to ChromaDB if size reached
            if len(batch_ids) >= BATCH_SIZE:
                print(f"Adding batch of {len(batch_ids)} items to ChromaDB...")
                try:
                    collection.add(
                        embeddings=batch_embeddings,
                        metadatas=batch_metadatas,
                        documents=batch_documents,
                        ids=batch_ids
                    )
                    print(f"Batch added successfully.")
                    batch_embeddings, batch_metadatas, batch_ids, batch_documents = [], [], [], []
                except Exception as e:
                    print(f"Error adding batch to ChromaDB: {e}")
                    total_errors += len(batch_ids)
                    batch_embeddings, batch_metadatas, batch_ids, batch_documents = [], [], [], []
    
    # Add any remaining items
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
    
    print(f"\nVector DB Population Summary:")
    print(f"Total blocks processed: {total_blocks_processed}")
    print(f"Total errors: {total_errors}")
    print(f"Success rate: {(total_blocks_processed - total_errors) / total_blocks_processed * 100:.2f}%")
    
    return total_errors == 0

# --- Main Pipeline Function ---
def youtube_to_vectordb_pipeline(youtube_url: str) -> bool:
    """
    Complete pipeline from YouTube URL to Vector DB.
    
    Args:
        youtube_url: The YouTube URL to process
        
    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    print(f"\n========== STARTING YOUTUBE TO VECTORDB PIPELINE ==========")
    print(f"YouTube URL: {youtube_url}")
    
    # Step 1: Process YouTube video (download and transcribe)
    transcript_path = process_youtube_video(youtube_url)
    if not transcript_path:
        print("Pipeline failed at step 1: Processing YouTube video")
        return False
    
    # Step 2: Chunk transcript
    chunked_file_path = chunk_transcript(transcript_path)
    if not chunked_file_path:
        print("Pipeline failed at step 2: Chunking transcript")
        return False
    
    # Step 3: Tag transcript chunks
    tagged_file_path = tag_transcript_chunks(chunked_file_path)
    if not tagged_file_path:
        print("Pipeline failed at step 3: Tagging transcript chunks")
        return False
    
    # Step 4: Extract scenarios
    scenario_file_path = extract_scenarios_from_tags(tagged_file_path)
    if not scenario_file_path:
        print("Pipeline failed at step 4: Extracting scenarios")
        return False
    
    # Step 5: Initialize ChromaDB and embedding model
    embedding_model = initialize_embedding_model()
    chroma_client = initialize_chroma_client()
    collection = get_or_create_collection(chroma_client)
    
    if not embedding_model or not chroma_client or not collection:
        print("Pipeline failed at step 5: Initializing ChromaDB and embedding model")
        return False
    
    # Step 6: Generate embeddings and store in vector DB
    success = process_and_store_blocks(scenario_file_path, collection, embedding_model)
    if not success:
        print("Pipeline failed at step 6: Generating embeddings and storing in vector DB")
        return False
    
    print(f"\n========== PIPELINE COMPLETED SUCCESSFULLY ==========")
    video_id = os.path.basename(transcript_path).split('_')[0]
    print(f"Video ID: {video_id}")
    print(f"Data stored in ChromaDB collection: {COLLECTION_NAME}")
    return True

# --- Command Line Interface ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a YouTube video and store in vector DB")
    parser.add_argument("youtube_url", help="YouTube URL to process")
    args = parser.parse_args()
    
    success = youtube_to_vectordb_pipeline(args.youtube_url)
    if success:
        print("Pipeline completed successfully!")
    else:
        print("Pipeline failed. See logs for details.") 