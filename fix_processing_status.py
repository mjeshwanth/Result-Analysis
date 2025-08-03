import json
import os
from pathlib import Path

def fix_processing_status():
    """Fix processing status in all JSON files"""
    data_dir = Path("data")
    fixed_count = 0
    
    for json_file in data_dir.glob("*.json"):
        try:
            # Read the file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if processing status needs fixing
            if data.get("metadata", {}).get("processing_status") == "in_progress":
                # Update status to completed
                data["metadata"]["processing_status"] = "completed"
                
                # Write back to file
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Fixed: {json_file.name}")
                fixed_count += 1
            else:
                print(f"⏭️  Already OK: {json_file.name}")
                
        except Exception as e:
            print(f"❌ Error fixing {json_file.name}: {e}")
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == "__main__":
    fix_processing_status()
