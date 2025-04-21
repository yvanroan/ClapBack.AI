import json
import os

# --- Configuration ---
SCENARIO_FILE = "downloads/scenario"
TAGGED_FILE = "downloads/-ftgC4oWf6s_tagged.json"
OUTPUT_FILE = "downloads/-ftgC4oWf6s_tagged_with_scenario.json"

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Starting Scenario Merger ---")
    print(f"Loading scenario data from: {SCENARIO_FILE}")
    
    # 1. Load Scenario Data and Create Lookup Map
    scenario_lookup = {}
    try:
        with open(SCENARIO_FILE, 'r', encoding='utf-8') as f:
            scenario_data = json.load(f)
        
        if not isinstance(scenario_data, list):
            raise ValueError("Scenario file should contain a JSON list.")
            
        for chunk_scenario in scenario_data:
            chunk_num = chunk_scenario.get('chunk_num')
            blocks = chunk_scenario.get('blocks')
            if chunk_num is not None and isinstance(blocks, list):
                scenario_lookup[chunk_num] = {}
                for block_scenario in blocks:
                    block_id = block_scenario.get('block_id')
                    fields = block_scenario.get('fields')
                    if block_id is not None and isinstance(fields, dict):
                        scenario_lookup[chunk_num][block_id] = fields
                    else:
                         print(f"Warning: Invalid block format in scenario chunk {chunk_num}: {block_scenario}")
            else:
                print(f"Warning: Invalid chunk format in scenario file: {chunk_scenario}")
                
        print(f"Built scenario lookup map for {len(scenario_lookup)} chunks.")
        
    except FileNotFoundError:
        print(f"Error: Scenario file not found at {SCENARIO_FILE}")
        exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Could not load or parse scenario file {SCENARIO_FILE}. Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading scenario file: {e}")
        exit(1)

    # 2. Load Tagged Data
    print(f"Loading tagged data from: {TAGGED_FILE}")
    tagged_data = []
    try:
        with open(TAGGED_FILE, 'r', encoding='utf-8') as f:
            tagged_data = json.load(f)
        if not isinstance(tagged_data, list):
            raise ValueError("Tagged file should contain a JSON list.")
        print(f"Loaded {len(tagged_data)} chunks from tagged file.")
            
    except FileNotFoundError:
        print(f"Error: Tagged file not found at {TAGGED_FILE}")
        exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: Could not load or parse tagged file {TAGGED_FILE}. Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading tagged file: {e}")
        exit(1)

    # 3. Iterate and Merge (Modify data in place)
    print("Merging scenario data into tagged data...")
    merge_count = 0
    missing_scenario_count = 0
    invalid_tagging_result_count = 0

    for chunk_tagged in tagged_data:
        chunk_num = chunk_tagged.get('chunk_num')
        processed_blocks = chunk_tagged.get('processed_blocks')

        if chunk_num is None or not isinstance(processed_blocks, list):
            print(f"Warning: Skipping tagged chunk due to missing 'chunk_num' or 'processed_blocks': {chunk_tagged.get('chunk_num', 'N/A')}")
            continue
        
        # Check if scenario data exists for this chunk
        if chunk_num not in scenario_lookup:
            print(f"Warning: No scenario data found for chunk {chunk_num}. Skipping merge for this chunk.")
            missing_scenario_count += len(processed_blocks) # Count all blocks as missing scenario
            continue

        for block_tagged in processed_blocks:
            block_id = block_tagged.get('block_id')
            tagging_result_list = block_tagged.get('tagging_result')

            if block_id is None:
                print(f"Warning: Skipping block in chunk {chunk_num} due to missing 'block_id'.")
                continue
            
            # Find corresponding scenario fields
            scenario_fields = scenario_lookup[chunk_num].get(block_id)

            if scenario_fields:
                # Check if tagging_result exists and is a list with at least one element
                if isinstance(tagging_result_list, list) and tagging_result_list:
                    # Update the *first* object in the tagging_result list
                    if isinstance(tagging_result_list[0], dict):
                        tagging_result_list[0].update(scenario_fields)
                        merge_count += 1
                    else:
                        print(f"Warning: tagging_result[0] for chunk {chunk_num}, block {block_id} is not a dictionary. Skipping merge.")
                        invalid_tagging_result_count += 1
                else:
                    # Handle case where tagging_result is missing, empty, or not a list
                    # Optionally, create it or just log a warning
                    # print(f"Warning: Missing or invalid 'tagging_result' list for chunk {chunk_num}, block {block_id}. Creating/Updating anyway.")
                    # block_tagged['tagging_result'] = [scenario_fields] # Example: create if missing
                    print(f"Warning: Missing or invalid 'tagging_result' list for chunk {chunk_num}, block {block_id}. Cannot merge scenario.")
                    invalid_tagging_result_count += 1
                    
            else:
                print(f"Warning: No matching scenario found for chunk {chunk_num}, block {block_id}. Skipping merge for this block.")
                missing_scenario_count += 1

    print(f"Merge complete. Updated {merge_count} blocks.")
    if missing_scenario_count > 0:
        print(f"Warning: Could not find matching scenario data for {missing_scenario_count} blocks.")
    if invalid_tagging_result_count > 0:
         print(f"Warning: Found invalid or missing 'tagging_result' structure in {invalid_tagging_result_count} blocks, merge skipped for these.")

    # 4. Save Output
    print(f"Saving merged data to: {OUTPUT_FILE}")
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(tagged_data, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved merged data.")
    except Exception as e:
        print(f"Error saving merged data to {OUTPUT_FILE}: {e}")

    print("--- Scenario Merger Finished ---") 