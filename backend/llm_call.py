import json
import requests
import os # Added for path manipulation
import time
from prompts import chunking_prompt, tagging_prompt
from cleaner import clean_gemini_output
# --- Configuration ---
TRANSCRIPTION_FILE = "downloads/-ftgC4oWf6s_with_speakers.txt"
API_ENDPOINT = "http://localhost:8000/generate" # Assumes Gemini API server
# API_ENDPOINT = "http://localhost:8001/generate" # Uncomment for DeepSeek

CHUNK_SIZE = 300
OVERLAP = 20
STEP = CHUNK_SIZE - OVERLAP

# --- Main Execution ---
if __name__ == "__main__":
    print(f"Reading text transcript from: {TRANSCRIPTION_FILE}")

    # 1. Read the plain text transcription file into lines
    lines = []
    try:
        with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Transcription file not found at {TRANSCRIPTION_FILE}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        exit(1)

    if not lines:
        print(f"Error: File {TRANSCRIPTION_FILE} is empty or could not be read.")
        exit(1)

    print(f"Successfully read {len(lines)} lines from transcription file.")

    all_results = [] # List to store results from each chunk
    num_lines = len(lines)
    chunk_num = 0

    # 2. Process the text in overlapping chunks
    for i in range(0, num_lines, STEP):
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

        
        time.sleep(5) 

    # 6. Save all collected results to a single file
    print(f"\n--- Finished Processing All Chunks ({len(all_results)} results collected) ---")
    # Adjust output filename
    output_filename = os.path.basename(TRANSCRIPTION_FILE).replace('.txt', '_gemini_output_chunked_cleaned.json')
    output_path = os.path.join(os.path.dirname(TRANSCRIPTION_FILE), output_filename)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved all collected results to: {output_path}")
    except Exception as e:
        print(f"Error saving collected results to {output_path}: {e}")

    print("--- Script Finished ---")
