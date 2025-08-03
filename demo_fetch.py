#!/usr/bin/env python3
"""
Live Demo: Fetch actual student data
"""

import requests
import json

def demo_student_fetch():
    """Demonstrate fetching real student data"""
    
    print("LIVE DEMO: Fetching Student Data")
    print("=" * 50)
    
    # Test with actual student ID from database
    student_id = "17B81A0502"
    base_url = "http://127.0.0.1:5000"
    
    print(f"Searching for student: {student_id}")
    print(f"URL: {base_url}/api/students/{student_id}/results")
    
    try:
        response = requests.get(f"{base_url}/api/students/{student_id}/results", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\nSUCCESS! Found {data['count']} records")
            print("-" * 30)
            
            if data['count'] > 0:
                for i, result in enumerate(data['results'], 1):
                    print(f"\nRecord {i}:")
                    print(f"  Student ID: {result.get('student_id')}")
                    print(f"  Student Name: {result.get('student_name', 'N/A')}")
                    print(f"  Semester: {result.get('semester', 'N/A')}")
                    print(f"  Year: {result.get('year', 'N/A')}")
                    print(f"  Exam Type: {result.get('exam_type', 'N/A')}")
                    print(f"  SGPA: {result.get('sgpa', result.get('grades', {}).get('sgpa', 'N/A'))}")
                    
                    # Show some grades if available
                    grades = result.get('grades', {})
                    if grades and len(grades) > 1:  # More than just SGPA
                        print("  Subject Grades:")
                        for subject, grade in list(grades.items())[:5]:  # Show first 5
                            if subject != 'sgpa':
                                print(f"    {subject}: {grade}")
                        if len(grades) > 6:
                            print(f"    ... and {len(grades)-6} more subjects")
            else:
                print("No records found for this student ID")
                
        else:
            print(f"ERROR: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server")
        print("Make sure Flask app is running on http://127.0.0.1:5000")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    demo_student_fetch()
    
    print(f"\n" + "=" * 50)
    print("WHERE TO ACCESS THIS DATA:")
    print("1. Web Interface: http://127.0.0.1:5000/student-search")
    print("2. API Endpoint: /api/students/{student_id}/results") 
    print("3. Admin Dashboard: http://127.0.0.1:5000/admin/dashboard")
    print("4. Direct Firebase: Use Python Firebase SDK")
