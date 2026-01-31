import os
import sys
import json
import logging

# Ensure we can import carball from current directory
sys.path.insert(0, os.getcwd())

from carball.decompile_replays import decompile_replay, analyze_replay_file
from carball.analysis.analysis_manager import AnalysisManager

TEST_FILES_DIR = 'test-files'
OUTPUT_DIR = 'output_test'

def validate_replay(replay_filename):
    replay_path = os.path.join(TEST_FILES_DIR, replay_filename)
    print(f"Processing {replay_filename}...")
    
    try:
        # 1. Decompile to get raw JSON
        raw_json = decompile_replay(replay_path)
        
        # 2. Analyze to get processed JSON
        # analyze_replay_file returns an AnalysisManager
        analysis_manager = analyze_replay_file(replay_path, logging_level=logging.ERROR)
        processed_json = analysis_manager.get_json_data()
        
        # 3. Output to files
        base_name = os.path.splitext(replay_filename)[0]
        
        raw_out_path = os.path.join(OUTPUT_DIR, f"{base_name}_raw.json")
        with open(raw_out_path, 'w') as f:
            json.dump(raw_json, f, indent=2, default=str)
            
        proc_out_path = os.path.join(OUTPUT_DIR, f"{base_name}_processed.json")
        with open(proc_out_path, 'w') as f:
            json.dump(processed_json, f, indent=2)
            
        print(f"  Outputs written to {OUTPUT_DIR}")
        
        # 4. Validate Player IDs
        raw_ids = set()
        if 'properties' in raw_json and 'PlayerStats' in raw_json['properties']:
            for p in raw_json['properties']['PlayerStats']:
                # OnlineID can be string or number in raw json depending on parser
                # carball Player class converts it.
                # In raw json from boxcars, it might be a dict or direct value.
                # Let's inspect it safely.
                oid = p.get('OnlineID')
                if isinstance(oid, dict):
                    # It might be {'online_id': ...} or similar if boxcars returns that
                    # But carball.json_parser.player.Player._get_player_id handles dict
                    # We should try to extract the ID similar to how Player does it if complex
                    # But usually decompile_replay returns the dict from boxcars directly.
                    # Looking at Player.create_from_actor_data, it handles complex IDs.
                    # Looking at Player.parse_player_stats, it expects "OnlineID" to be direct or convertible.
                    pass
                
                # Normalize to string for comparison
                raw_ids.add(str(oid))

        proc_ids = set()
        if 'players' in processed_json:
            for p in processed_json['players']:
                if 'id' in p and isinstance(p['id'], dict) and 'id' in p['id']:
                    proc_ids.add(str(p['id']['id']))
                elif 'id' in p:
                     proc_ids.add(str(p['id']))
        
        print(f"  Raw IDs: {raw_ids}")
        print(f"  Processed IDs: {proc_ids}")
        
        # Validate
        # Note: Bots might have ID '0' in raw but a generated ID in processed.
        # So we check if all non-zero raw IDs are in processed.
        
        missing = []
        for rid in raw_ids:
            if rid == '0' or rid == 'None':
                # Bot or invalid, might change in processing
                continue
            if rid not in proc_ids:
                missing.append(rid)
        
        if missing:
            print(f"  FAILED: Missing player IDs in processed data: {missing}")
        else:
            print("  SUCCESS: All player IDs match (ignoring '0' for bots).")

    except Exception as e:
        print(f"  ERROR processing {replay_filename}: {e}")
        import traceback
        traceback.print_exc()

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    files = [f for f in os.listdir(TEST_FILES_DIR) if f.endswith('.replay')]
    if not files:
        print(f"No replay files found in {TEST_FILES_DIR}")
        return

    print(f"Found {len(files)} replay files.")
    for f in files:
        validate_replay(f)
        print("-" * 40)

if __name__ == "__main__":
    main()
