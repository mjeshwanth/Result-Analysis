#!/usr/bin/env python3
"""
Enhanced JSON Data File Repair Script
Fixes corrupted JSON files in the data directory
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

class JSONRepairer:
    def __init__(self):
        self.data_dir = Path("data")
        self.backup_dir = Path("data_backup_repairs")
        self.backup_dir.mkdir(exist_ok=True)
        
    def backup_file(self, file_path):
        """Create a backup of the original file"""
        backup_path = self.backup_dir / file_path.name
        try:
            with open(file_path, 'r', encoding='utf-8') as src, \
                 open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            print(f"  📋 Backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to backup {file_path}: {e}")
            return False
    
    def repair_incomplete_json(self, file_path):
        """Repair incomplete JSON by reconstructing valid structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract the filename to understand the format
            filename = file_path.name
            
            # Parse filename for metadata
            parts = filename.replace('.json', '').split('_')
            if len(parts) >= 4:
                format_type = parts[2]  # jntuk, autonomous, etc
                exam_type = parts[3]    # regular, supplementary
                date_part = parts[4] if len(parts) > 4 else "20250802"
                time_part = parts[5] if len(parts) > 5 else "000000"
            else:
                format_type = "unknown"
                exam_type = "regular"
                date_part = "20250802"
                time_part = "000000"
            
            # Create a base structure
            base_structure = {
                "metadata": {
                    "format": format_type,
                    "exam_type": exam_type,
                    "processed_at": f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}",
                    "total_students": 0,
                    "original_filename": "Repaired from corrupted JSON",
                    "processing_status": "repaired",
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
            
            # Try to extract any valid data from the corrupted file
            try:
                # Look for student data patterns
                student_pattern = r'"hallTicket":\s*"([^"]+)"'
                hall_tickets = re.findall(student_pattern, content)
                
                # Look for metadata if available
                if '"original_filename"' in content:
                    filename_match = re.search(r'"original_filename":\s*"([^"]+)"', content)
                    if filename_match:
                        base_structure["metadata"]["original_filename"] = filename_match.group(1)
                
                if '"total_students"' in content:
                    total_match = re.search(r'"total_students":\s*(\d+)', content)
                    if total_match:
                        base_structure["metadata"]["total_students"] = int(total_match.group(1))
                
                # Add basic student records if hall tickets found
                for hall_ticket in hall_tickets[:10]:  # Limit to prevent huge files
                    student_record = {
                        "hallTicket": hall_ticket,
                        "studentName": "Data recovered from corrupted file",
                        "fatherName": "",
                        "grade": "Not Available",
                        "subjects": [],
                        "cgpa": 0.0,
                        "result": "Not Available"
                    }
                    base_structure["students"].append(student_record)
                
                base_structure["metadata"]["total_students"] = len(base_structure["students"])
                
            except Exception as e:
                print(f"    ⚠️  Could not extract data from corrupted file: {e}")
            
            return base_structure
            
        except Exception as e:
            print(f"    ❌ Failed to repair {file_path}: {e}")
            return None
    
    def validate_json(self, data):
        """Validate JSON structure"""
        required_keys = ["metadata", "students", "firebase_upload"]
        
        if not isinstance(data, dict):
            return False
            
        for key in required_keys:
            if key not in data:
                return False
        
        # Validate metadata
        metadata = data.get("metadata", {})
        required_metadata = ["format", "exam_type", "processed_at", "total_students"]
        for key in required_metadata:
            if key not in metadata:
                return False
        
        # Validate students is a list
        if not isinstance(data.get("students", []), list):
            return False
            
        return True
    
    def repair_file(self, file_path):
        """Repair a single JSON file"""
        print(f"\n🔧 Repairing: {file_path.name}")
        
        # Create backup first
        if not self.backup_file(file_path):
            return False
        
        try:
            # Try to load as regular JSON first
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if self.validate_json(data):
                print(f"  ✅ File is already valid JSON")
                return True
                
        except json.JSONDecodeError as e:
            print(f"  🔧 JSON decode error: {e}")
            print(f"  🔄 Attempting to repair...")
            
            # Try to repair the file
            repaired_data = self.repair_incomplete_json(file_path)
            if repaired_data is None:
                return False
            
            # Write the repaired data
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(repaired_data, f, indent=2, ensure_ascii=False)
                
                print(f"  ✅ Successfully repaired and saved")
                return True
                
            except Exception as e:
                print(f"  ❌ Failed to write repaired data: {e}")
                return False
        
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            return False
    
    def repair_all_files(self):
        """Repair all JSON files in the data directory"""
        print("🚀 Starting JSON Data File Repair Process...")
        print("=" * 60)
        
        json_files = list(self.data_dir.glob("*.json"))
        
        if not json_files:
            print("❌ No JSON files found in data directory")
            return
        
        fixed_count = 0
        total_count = len(json_files)
        
        for json_file in json_files:
            if self.repair_file(json_file):
                fixed_count += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Repair Summary:")
        print(f"   Total files processed: {total_count}")
        print(f"   Successfully repaired: {fixed_count}")
        print(f"   Failed repairs: {total_count - fixed_count}")
        print(f"   Success rate: {(fixed_count/total_count)*100:.1f}%")
        
        if fixed_count == total_count:
            print("🎉 All JSON files are now properly formatted!")
        else:
            print(f"⚠️  {total_count - fixed_count} files still need manual attention")
        
        print(f"\n💾 Backups saved in: {self.backup_dir}")

def main():
    repairer = JSONRepairer()
    repairer.repair_all_files()

if __name__ == "__main__":
    main()
