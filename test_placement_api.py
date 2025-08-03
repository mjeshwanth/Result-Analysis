#!/usr/bin/env python3
"""Test the placement API endpoints"""

import requests
import json

def test_placement_api():
    """Test the placement API endpoints"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing Training & Placement API")
    print("=" * 50)
    
    # Test 1: Get class ranges
    print("\n1. Testing /api/placement/class-ranges")
    try:
        response = requests.get(f"{base_url}/api/placement/class-ranges")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Class ranges found: {data.get('total_ranges', 0)}")
            for range_info in data.get('class_ranges', [])[:3]:  # Show first 3
                print(f"  - {range_info['range']} ({range_info['student_count']} students)")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Get eligible students
    print("\n2. Testing /api/placement/eligible-students")
    try:
        params = {
            'min_cgpa': '6.0',
            'max_backlogs': '4'
        }
        response = requests.get(f"{base_url}/api/placement/eligible-students", params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_eligible', 0)
            print(f"Eligible students found: {total}")
            
            # Show top 5 students
            students = data.get('eligible_students', [])[:5]
            for student in students:
                print(f"  - {student['student_id']}: CGPA {student['cgpa']}, Backlogs: {student['backlogs']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Test with specific class range
    print("\n3. Testing with class range filter")
    try:
        params = {
            'min_cgpa': '7.0',
            'max_backlogs': '2',
            'class_range': '23B81A1266-23B81A12D0'
        }
        response = requests.get(f"{base_url}/api/placement/eligible-students", params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_eligible', 0)
            print(f"Eligible students in range: {total}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Test placement dashboard page
    print("\n4. Testing /placement dashboard page")
    try:
        response = requests.get(f"{base_url}/placement")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Placement dashboard page loads successfully")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_placement_api()
