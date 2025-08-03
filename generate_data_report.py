#!/usr/bin/env python3
"""
Data Files Summary Report
Generate a comprehensive report of all JSON data files
"""

import json
import os
from pathlib import Path
from datetime import datetime

def generate_data_files_report():
    """Generate a comprehensive report of all data files"""
    data_dir = Path("data")
    
    print("📊 Data Files Summary Report")
    print("=" * 60)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not data_dir.exists():
        print("❌ Data directory not found!")
        return
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print("❌ No JSON files found!")
        return
    
    # Summary statistics
    total_files = len(json_files)
    total_students = 0
    formats = {}
    exam_types = {}
    upload_status = {"uploaded": 0, "not_uploaded": 0}
    
    print(f"\n📁 Total Files: {total_files}")
    print("\n📋 File Details:")
    print("-" * 60)
    
    for i, json_file in enumerate(sorted(json_files), 1):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get("metadata", {})
            firebase_upload = data.get("firebase_upload", {})
            students = data.get("students", [])
            
            format_type = metadata.get("format", "unknown")
            exam_type = metadata.get("exam_type", "unknown")
            student_count = len(students)
            is_uploaded = firebase_upload.get("uploaded", False)
            original_filename = metadata.get("original_filename", "N/A")
            
            # Update statistics
            total_students += student_count
            formats[format_type] = formats.get(format_type, 0) + 1
            exam_types[exam_type] = exam_types.get(exam_type, 0) + 1
            
            if is_uploaded:
                upload_status["uploaded"] += 1
            else:
                upload_status["not_uploaded"] += 1
            
            # File info
            status = "✅ Uploaded" if is_uploaded else "⏳ Not Uploaded"
            print(f"{i:2d}. {json_file.name}")
            print(f"    📄 Original: {original_filename}")
            print(f"    📊 Format: {format_type.upper()} | Type: {exam_type.upper()}")
            print(f"    👥 Students: {student_count} | Status: {status}")
            print()
            
        except Exception as e:
            print(f"{i:2d}. {json_file.name} - ❌ Error: {e}")
            print()
    
    # Summary statistics
    print("=" * 60)
    print("📈 Summary Statistics:")
    print("-" * 30)
    print(f"Total Students Processed: {total_students:,}")
    print(f"Average Students per File: {total_students/total_files:.1f}")
    
    print("\n📊 By Format:")
    for format_type, count in formats.items():
        percentage = (count/total_files)*100
        print(f"  {format_type.upper()}: {count} files ({percentage:.1f}%)")
    
    print("\n📋 By Exam Type:")
    for exam_type, count in exam_types.items():
        percentage = (count/total_files)*100
        print(f"  {exam_type.upper()}: {count} files ({percentage:.1f}%)")
    
    print("\n☁️  Upload Status:")
    uploaded_pct = (upload_status["uploaded"]/total_files)*100
    not_uploaded_pct = (upload_status["not_uploaded"]/total_files)*100
    print(f"  Uploaded to Firebase: {upload_status['uploaded']} files ({uploaded_pct:.1f}%)")
    print(f"  Not Uploaded: {upload_status['not_uploaded']} files ({not_uploaded_pct:.1f}%)")
    
    print("\n" + "=" * 60)
    print("✅ Report Generation Complete!")
    
    # Generate JSON report for API
    report_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_files": total_files,
            "total_students": total_students,
            "average_students_per_file": round(total_students/total_files, 1),
            "formats": formats,
            "exam_types": exam_types,
            "upload_status": upload_status
        },
        "files": []
    }
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get("metadata", {})
            firebase_upload = data.get("firebase_upload", {})
            students = data.get("students", [])
            
            file_info = {
                "filename": json_file.name,
                "original_filename": metadata.get("original_filename", "N/A"),
                "format": metadata.get("format", "unknown"),
                "exam_type": metadata.get("exam_type", "unknown"),
                "student_count": len(students),
                "processed_at": metadata.get("processed_at", ""),
                "uploaded": firebase_upload.get("uploaded", False),
                "file_size_kb": round(json_file.stat().st_size / 1024, 2)
            }
            report_data["files"].append(file_info)
            
        except Exception as e:
            file_info = {
                "filename": json_file.name,
                "error": str(e),
                "status": "corrupted"
            }
            report_data["files"].append(file_info)
    
    # Save report
    with open("data_files_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Detailed JSON report saved: data_files_report.json")

if __name__ == "__main__":
    generate_data_files_report()
