import os
import argparse
import json
import time
import google.generativeai as genai
import chromadb
import requests
from typing import Optional, Dict, List, Any, Tuple

# Import existing components
from backend.app.pipeline.url_to_transcript import download_audio, transcribe_youtube_audio
from backend.app.utils.cleaner import clean_gemini_output
from backend.data.prompts.prompts import tagging_prompt, chunking_prompt
from backend.app.services.vector_store import initialize_embedding_model, initialize_chroma_client, get_or_create_collection, process_and_store_blocks


# --- Configuration ---
CHUNK_SIZE = 100
OVERLAP = 20
API_TIMEOUT = 60 
DELAY_BETWEEN_CALLS = 5
API_ENDPOINT = "http://localhost:8000/chat"  # Your Gemini API endpoint


def chunk_transcript(transcription_file: str) -> Optional[str]:
    """
    Chunk the transcript into overlapping chunks of chunk_size lines with an overlap of overlap lines.
    """

    print(f"Reading text transcript from: {transcription_file}")

    # 1. Read the plain text transcription file into lines
    lines = []
    steps = CHUNK_SIZE - OVERLAP
    try:
        with open(transcription_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Transcription file not found at {transcription_file}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        exit(1)

    if not lines:
        print(f"Error: File {transcription_file} is empty or could not be read.")
        exit(1)

    print(f"Successfully read {len(lines)} lines from transcription file.")

    all_results = [] # List to store results from each chunk
    num_lines = len(lines)
    chunk_num = 0

    # 2. Process the text in overlapping chunks
    for i in range(0, num_lines, steps):
        chunk_num += 1
        start_line = i
        end_line = min(i + CHUNK_SIZE, num_lines)
        chunk_lines = lines[start_line:end_line]

        if not chunk_lines: # Should not happen with range logic, but good practice
            continue

        print(f"\n--- Processing Chunk {chunk_num} (Lines {start_line + 1}-{end_line}) ---")
        
        # Join lines for the current chunk
        chunk_text = "".join(chunk_lines)

        # 3. Prepare prompt for the chunk
        final_prompt = chunking_prompt(chunk_text) # Use the appropriate prompt function
        print(f"Prepared prompt for chunk {chunk_num}.")
        payload = {"prompt": final_prompt}

        # 4. Send chunk to API
        print(f"Sending request for chunk {chunk_num} to {API_ENDPOINT}...")
        try:
            # Added timeout (60 seconds, adjust as needed)
            response = requests.post(API_ENDPOINT, json=payload, timeout=60) 
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            api_result = response.json()
            
            print(f"Received raw response for chunk {chunk_num}.")
            
            if api_result:
                print("Cleaning response...")
                cleaned_data = clean_gemini_output(api_result)
                if cleaned_data:
                    print(f"Successfully cleaned response for chunk {chunk_num}.")
                    # Store the cleaned data along with chunk info
                    all_results.append({
                        "chunk_num": chunk_num,
                        "start_line": start_line + 1,
                        "end_line": end_line,
                        "cleaned_data": cleaned_data
                    })
                else:
                    print(f"Error: Cleaning failed for chunk {chunk_num}.")
                    all_results.append({"chunk_num": chunk_num, "error": "Cleaning failed", "raw_response": api_result})
            else:
                 print(f"Error: 'generated_text' key not found or empty in response for chunk {chunk_num}.")
                 all_results.append({"chunk_num": chunk_num, "error": "Missing generated_text", "raw_response": api_result})
        
        except requests.exceptions.Timeout:
             print(f"Error: Request timed out for chunk {chunk_num}.")
             all_results.append({"chunk_num": chunk_num, "error": "Request timeout"})
        except requests.exceptions.RequestException as e:
            print(f"Error during API request for chunk {chunk_num}: {e}")
            # Log detailed error if available
            if hasattr(e, 'response') and e.response is not None:
                print(f"API Response Status Code: {e.response.status_code}")
                print(f"API Response Body: {e.response.text}")
                all_results.append({"chunk_num": chunk_num, "error": str(e), "status_code": e.response.status_code, "response_body": e.response.text})
            else:
                all_results.append({"chunk_num": chunk_num, "error": str(e)})
        except Exception as e:
            print(f"An unexpected error occurred processing chunk {chunk_num}: {e}")
            all_results.append({"chunk_num": chunk_num, "error": f"Unexpected error: {str(e)}"})

        print(f"    Waiting {DELAY_BETWEEN_CALLS}s...")
        time.sleep(DELAY_BETWEEN_CALLS) 

    # 6. Save all collected results to a single file
    print(f"\n--- Finished Processing All Chunks ({len(all_results)} results collected) ---")
    # Adjust output filename
    output_filename = os.path.basename(transcription_file).replace('.txt', '_gemini_output_chunked_cleaned.json')
    output_path = os.path.join(os.path.dirname(transcription_file), output_filename)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved all collected results to: {output_path}")
    except Exception as e:
        print(f"Error saving collected results to {output_path}: {e}")

    print("--- Script Finished ---")

    return output_path

def tag_transcript_chunks(chunked_file_path: str):
    print(f"--- Starting Tagging Processor ---")

    # 1. Read the chunked and cleaned input file
    chunk_data = []
    try:
        with open(chunked_file_path, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {chunked_file_path}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from input file {chunked_file_path}. Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading {chunked_file_path}: {e}")
        exit(1)

    if not isinstance(chunk_data, list):
        print(f"Error: Expected input file {chunked_file_path} to contain a JSON list.")
        exit(1)

    print(f"Successfully loaded {len(chunk_data)} chunks from input file.")

    processed_chunk_data = [] # List to store final results with tags

    # 2. Iterate through chunks
    for chunk_index, chunk in enumerate(chunk_data):
        chunk_num = chunk.get('chunk_num', chunk_index + 1) # Use index if num missing
        start_line = chunk.get("start_line", 0)
        end_line = chunk.get("end_line", 0)
        
        print(f"\n--- Processing Chunk {chunk_num} ---")
        
        original_blocks = chunk.get('cleaned_data')
        chunk_error = chunk.get('error')
        processed_chunk_info= [] # Store results for this chunk's blocks
        
        if chunk_error:
             print(f"Skipping chunk {chunk_num} due to previous error: {chunk_error}")
             processed_chunk_data.append(processed_chunk_info) # Keep error info
             continue
             
        if not isinstance(original_blocks, list):
            print(f"Warning: 'cleaned_data' for chunk {chunk_num} is not a list. Skipping blocks.")
            processed_chunk_data.append(processed_chunk_info)
            continue

        # 3. Iterate through blocks within the chunk
        for block_index, block in enumerate(original_blocks):
            block_id = block.get('block_id', block_index + 1)
            lines = block.get('lines')
            processed_block = block.copy() # Keep original block info
            
            print(f"  Processing Block {block_id}...")

            if not lines or not isinstance(lines, list):
                print(f"    Warning: Missing or invalid 'lines' for block {block_id}. Skipping tagging.")
                processed_block['tagging_error'] = "Missing or invalid lines data"
                processed_chunk_info['processed_blocks'].append(processed_block)
                continue

            
            try:
                 tagging_api_prompt = tagging_prompt(processed_block)
            except Exception as e:
                 print(f"    Error creating prompt for block {block_id}: {e}")
                 processed_block['tagging_error'] = f"Prompt creation error: {e}"
                 processed_chunk_info['processed_blocks'].append(processed_block)
                 continue # Skip API call if prompt fails
                 
            payload = {"prompt": tagging_api_prompt}

            # 5. Call API for tagging
            print(f"    Sending request for block {block_id}...")
            try:
                response = requests.post(API_ENDPOINT, json=payload, timeout=API_TIMEOUT)
                response.raise_for_status() 
                api_result = response.json()
                
                print(f"Received raw response for block {block_id}.")
                
                if api_result:
                    print("    Cleaning tagging response...")
                    cleaned_tags = clean_gemini_output(api_result)
                    if cleaned_tags:
                        print(f"    Successfully cleaned tags for block {block_id}.")
                        processed_block['tagging_result'] = cleaned_tags
                    else:
                        print(f"    Error: Cleaning failed for block {block_id} tags.")
                        processed_block['tagging_error'] = "Tag cleaning failed"
                        processed_block['raw_tagging_response'] = generated_tags_string # Store raw if cleaning fails
                else:
                    print(f"    Error: 'generated_text' key not found or empty in tagging response for block {block_id}.")
                    processed_block['tagging_error'] = "Missing generated_text in tagging response"
                    processed_block['raw_tagging_response'] = api_result

            except requests.exceptions.Timeout:
                 print(f"    Error: Request timed out for block {block_id}.")
                 processed_block['tagging_error'] = "API Request timeout"
            except requests.exceptions.RequestException as e:
                print(f"    Error during API request for block {block_id}: {e}")
                processed_block['tagging_error'] = f"API Request error: {e}"
                if hasattr(e, 'response') and e.response is not None:
                     processed_block['tagging_status_code'] = e.response.status_code
                     processed_block['tagging_response_body'] = e.response.text
            except Exception as e:
                print(f"    An unexpected error occurred processing block {block_id}: {e}")
                processed_block['tagging_error'] = f"Unexpected processing error: {e}"
            
            # Append the processed block (with tags or error) to the chunk's results
            processed_chunk_info.append(processed_block)
            
            # Add delay
            print(f"    Waiting {DELAY_BETWEEN_CALLS}s...")
            time.sleep(DELAY_BETWEEN_CALLS)
            
        # Add the fully processed chunk info to the final list
        wrapper_object = {}
        wrapper_object["chunk_num"] = chunk_num
        wrapper_object["start_line"] = start_line
        wrapper_object["end_line"] = end_line
        wrapper_object["processed_blocks"] = processed_chunk_info
        processed_chunk_data.append(wrapper_object)

    # 7. Save all collected results to the final output file
    print(f"\n--- Finished Processing All Blocks ---")

    output_filename = os.path.basename(chunked_file_path).replace('_gemini_output_chunked_cleaned.json', '_tagged.json')
    output_file_path = os.path.join(os.path.dirname(chunked_file_path), output_filename)

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_chunk_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved all processed data with tags to: {output_file_path}")
    except Exception as e:
        print(f"Error saving final tagged data to {output_file_path}: {e}")

    print("--- Tagging Processor Finished ---") 
    return output_file_path

# --- Main Pipeline Function ---
def transcript_to_vectordb_pipeline(transcript_path: str) -> bool:
    """
    Complete pipeline from Transcript to Vector DB.
    
    Args:
        transcript_path: The path to the transcript
        
    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    print(f"\n========== STARTING TRANSCRIPT TO VECTORDB PIPELINE ==========")
    print(f"URL: {transcript_path}")
    
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

    # Step 4: Initialize ChromaDB and embedding model
    embedding_model = initialize_embedding_model()
    chroma_client = initialize_chroma_client()
    collection = get_or_create_collection(chroma_client)
    
    if not embedding_model or not chroma_client or not collection:
        print("Pipeline failed at step 5: Initializing ChromaDB and embedding model")
        return False
    
    # Step 5: Generate embeddings and store in vector DB
    success = process_and_store_blocks(tagged_file_path, collection, embedding_model)
    if not success:
        print("Pipeline failed at step 6: Generating embeddings and storing in vector DB")
        return False
    
    print(f"\n========== PIPELINE COMPLETED SUCCESSFULLY ==========")
    names = os.path.basename(transcript_path).split('_')[:-2]
    video_id = "_".join(names)
    print(f"Video ID: {video_id}")
    
    return True


    