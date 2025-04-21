import json
import requests
import os
import time
from cleaner import clean_gemini_output
from prompts import tagging_prompt

# --- Configuration ---
INPUT_FILE = "downloads/-ftgC4oWf6s_with_speakers_gemini_output_chunked_cleaned.json"
OUTPUT_FILE = "downloads/-ftgC4oWf6s_tagged.json"
API_ENDPOINT = "http://localhost:8000/generate" 
API_TIMEOUT = 120 # Seconds before timeout for API calls
DELAY_BETWEEN_CALLS = 5 # Seconds delay between API calls

# --- Main Execution ---
if __name__ == "__main__":
    print(f"--- Starting Tagging Processor ---")

    # 1. Read the chunked and cleaned input file
    chunk_data = []
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            chunk_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_FILE}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from input file {INPUT_FILE}. Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading {INPUT_FILE}: {e}")
        exit(1)

    if not isinstance(chunk_data, list):
        print(f"Error: Expected input file {INPUT_FILE} to contain a JSON list.")
        exit(1)

    print(f"Successfully loaded {len(chunk_data)} chunks from input file.")

    processed_chunk_data = [] # List to store final results with tags

    # 2. Iterate through chunks
    for chunk_index, chunk in enumerate(chunk_data):
        chunk_num = chunk.get('chunk_num', chunk_index + 1) # Use index if num missing
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
        processed_chunk_data.append(processed_chunk_info)

    # 7. Save all collected results to the final output file
    print(f"\n--- Finished Processing All Blocks ({sum(len(c.get('processed_blocks', [])) for c in processed_chunk_data)} total blocks processed) ---")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(processed_chunk_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved all processed data with tags to: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving final tagged data to {OUTPUT_FILE}: {e}")

    print("--- Tagging Processor Finished ---") 