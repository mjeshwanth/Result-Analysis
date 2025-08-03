#!/usr/bin/env python3
"""
Comprehensive JSON Data Validation and Repair
Validates and ensures all JSON files are properly formatted
"""

import json
import os
from pathlib import Path
from datetime import datetime

def validate_and_repair_all_json():
    """Validate and repair all JSON files in the data directory"""
    data_dir = Path("data")
    
    print("🔍 Comprehensive JSON Validation and Repair")
    print("=" * 50)
    
    if not data_dir.exists():
        print("❌ Data directory not found!")
        return
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print("❌ No JSON files found!")
        return
    
    valid_count = 0
    repaired_count = 0
    failed_count = 0
    
    for json_file in json_files:
        print(f"\n📄 Checking: {json_file.name}")
        
        try:
            # Try to load and validate JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate structure
            if validate_json_structure(data):
                print("  ✅ Valid JSON structure")
                valid_count += 1
                
                # Ensure proper formatting by rewriting
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
            else:
                print("  🔧 Invalid structure, attempting repair...")
                repaired_data = repair_json_structure(data, json_file.name)
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(repaired_data, f, indent=2, ensure_ascii=False)
                
                print("  ✅ Structure repaired and saved")
                repaired_count += 1
                
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON decode error: {e}")
            print("  🔧 Creating new valid structure...")
            
            # Create a new valid structure
            new_data = create_default_structure(json_file.name)
            
            try:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
                
                print("  ✅ New valid structure created")
                repaired_count += 1
            except Exception as e2:
                print(f"  ❌ Failed to repair: {e2}")
                failed_count += 1
                
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            failed_count += 1
    
    print("\n" + "=" * 50)
    print("📊 Final Report:")
    print(f"   Valid files: {valid_count}")
    print(f"   Repaired files: {repaired_count}")
    print(f"   Failed files: {failed_count}")
    print(f"   Total processed: {len(json_files)}")
    
    if failed_count == 0:
        print("🎉 All JSON files are now properly formatted!")
    else:
        print(f"⚠️  {failed_count} files could not be repaired")

def validate_json_structure(data):
    """Validate if JSON has the required structure"""
    if not isinstance(data, dict):
        return False
    
    required_keys = ["metadata", "students", "firebase_upload"]
    for key in required_keys:
        if key not in data:
            return False
    
    # Validate metadata
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        return False
    
    required_metadata_keys = ["format", "exam_type", "processed_at", "total_students"]
    for key in required_metadata_keys:
        if key not in metadata:
            return False
    
    # Validate students
    if not isinstance(data.get("students", []), list):
        return False
    
    # Validate firebase_upload
    firebase_upload = data.get("firebase_upload", {})
    if not isinstance(firebase_upload, dict):
        return False
    
    return True

def repair_json_structure(data, filename):
    """Repair JSON structure by adding missing keys"""
    if not isinstance(data, dict):
        return create_default_structure(filename)
    
    # Ensure metadata exists and is complete
    if "metadata" not in data or not isinstance(data["metadata"], dict):
        data["metadata"] = {}
    
    metadata = data["metadata"]
    
    # Parse filename for defaults
    parts = filename.replace('.json', '').split('_')
    if len(parts) >= 4:
        format_type = parts[2]
        exam_type = parts[3]
    else:
        format_type = "unknown"
        exam_type = "regular"
    
    # Required metadata fields
    metadata_defaults = {
        "format": format_type,
        "exam_type": exam_type,
        "processed_at": datetime.now().isoformat(),
        "total_students": 0,
        "original_filename": "Repaired data file",
        "processing_status": "repaired",
        "completed_at": datetime.now().isoformat()
    }
    
    for key, default_value in metadata_defaults.items():
        if key not in metadata:
            metadata[key] = default_value
    
    # Ensure students exists
    if "students" not in data or not isinstance(data["students"], list):
        data["students"] = []
    
    # Update total_students
    metadata["total_students"] = len(data["students"])
    
    # Ensure firebase_upload exists
    if "firebase_upload" not in data or not isinstance(data["firebase_upload"], dict):
        data["firebase_upload"] = {}
    
    firebase_defaults = {
        "uploaded": False,
        "batches_completed": 0,
        "students_saved": 0,
        "duplicates_skipped": 0,
        "upload_started_at": "",
        "upload_completed_at": ""
    }
    
    firebase_upload = data["firebase_upload"]
    for key, default_value in firebase_defaults.items():
        if key not in firebase_upload:
            firebase_upload[key] = default_value
    
    return data

def create_default_structure(filename):
    """Create a default JSON structure for a filename"""
    parts = filename.replace('.json', '').split('_')
    if len(parts) >= 4:
        format_type = parts[2]
        exam_type = parts[3]
        date_part = parts[4] if len(parts) > 4 else "20250802"
        time_part = parts[5] if len(parts) > 5 else "000000"
    else:
        format_type = "unknown"
        exam_type = "regular"
        date_part = "20250802"
        time_part = "000000"
    
    # Format timestamp
    try:
        processed_at = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
    except:
        processed_at = datetime.now().isoformat()
    
    return {
        "metadata": {
            "format": format_type,
            "exam_type": exam_type,
            "processed_at": processed_at,
            "total_students": 0,
            "original_filename": f"Reconstructed from {filename}",
            "processing_status": "reconstructed",
            "completed_at": datetime.now().isoformat()
        },
        "students": [],
        "firebase_upload": {
            "uploaded": False,
            "batches_completed": 0,
            "students_saved": 0,
            "duplicates_skipped": 0,
            "upload_started_at": "",
            "upload_completed_at": ""
        }
    }

if __name__ == "__main__":
    validate_and_repair_all_json()
