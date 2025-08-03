#!/usr/bin/env python3
"""Test the parser directly to debug issues"""

import sys
import traceback
from parser.parser_autonomous import parse_autonomous_pdf

def test_direct_parsing():
    """Test parsing directly without Flask"""
    
    files_to_test = [
        "sample_autonomous.pdf",
        "sample_autonomous_new.pdf"
    ]
    
    for filename in files_to_test:
        print(f"\n{'='*60}")
        print(f"TESTING: {filename}")
        print(f"{'='*60}")
        
        try:
            results = parse_autonomous_pdf(filename)
            print(f"SUCCESS: Parsed {len(results)} students")
            if results:
                sample = results[0]
                print(f"Sample student: {sample['student_id']}")
                print(f"Semester: {sample['semester']}")
                print(f"University: {sample['university']}")
                print(f"Subjects: {len(sample['subjectGrades'])}")
                print(f"SGPA: {sample['sgpa']}")
        except Exception as e:
            print(f"ERROR: {str(e)}")
            print("Full traceback:")
            traceback.print_exc()

if __name__ == "__main__":
    test_direct_parsing()
