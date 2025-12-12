import os
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# List of files to convert (excluding CSVs)
json_files = [
    'chargenet_charging_sessions.json',
    'chargenet_stations.json',
    'ecoride_product_reviews.json',
    'vehicle_health_data.json',
]

def convert_to_jsonl(json_path, jsonl_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error reading {json_path}: {e}")
            return
    if not isinstance(data, list):
        print(f"Skipping {json_path}: not a list of objects.")
        return
    with open(jsonl_path, 'w', encoding='utf-8') as out:
        for obj in data:
            try:
                out.write(json.dumps(obj, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"Error writing object in {json_path}: {e}")

def main():
    for fname in json_files:
        json_path = os.path.join(DATA_DIR, fname)
        jsonl_path = os.path.join(DATA_DIR, fname.replace('.json', '.jsonl'))
        if not os.path.exists(json_path):
            print(f"File not found: {json_path}")
            continue
        print(f"Converting {json_path} -> {jsonl_path}")
        convert_to_jsonl(json_path, jsonl_path)

if __name__ == "__main__":
    main()

