import json
import os
from pathlib import Path

def fix_json_file(file_path):
    """Fix corrupted JSON files by attempting to parse and reconstruct valid JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to find the first complete JSON object
        lines = content.split('\n')
        json_lines = []
        brace_count = 0
        found_start = False
        
        for line in lines:
            if line.strip().startswith('{') and not found_start:
                found_start = True
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
            elif found_start:
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    break
        
        # Try to parse the reconstructed JSON
        json_content = '\n'.join(json_lines)
        data = json.loads(json_content)
        
        # Write back the clean JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Fixed: {file_path}")
        return True
        
    except Exception as e:
        print(f"Could not fix {file_path}: {e}")
        return False

# Fix all JSON files in data directory
data_dir = Path("data")
fixed_count = 0
total_count = 0

for json_file in data_dir.glob("*.json"):
    total_count += 1
    if fix_json_file(json_file):
        fixed_count += 1

print(f"\nFixed {fixed_count} out of {total_count} JSON files")
