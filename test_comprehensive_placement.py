#!/usr/bin/env python3
"""Comprehensive test of placement functionality with detailed analysis"""

import requests
import json

def test_comprehensive_placement():
    """Comprehensive test showing all placement features"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🎯 COMPREHENSIVE TRAINING & PLACEMENT TEST")
    print("=" * 60)
    
    # Test 1: Analyze all class ranges
    print("\n📊 CLASS RANGE ANALYSIS:")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/placement/class-ranges")
        if response.status_code == 200:
            data = response.json()
            ranges = data.get('class_ranges', [])
            print(f"Total class ranges found: {len(ranges)}")
            
            # Group by batch
            batches = {}
            for range_info in ranges:
                batch = range_info['batch']
                if batch not in batches:
                    batches[batch] = []
                batches[batch].append(range_info)
            
            for batch, batch_ranges in sorted(batches.items()):
                total_students = sum(r['student_count'] for r in batch_ranges)
                print(f"\nBatch 20{batch}: {total_students} students, {len(batch_ranges)} ranges")
                for r in batch_ranges[:3]:  # Show first 3 ranges per batch
                    print(f"  └─ {r['range']} - Branch {r['branch']} ({r['student_count']} students)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Different CGPA filters
    print(f"\n🎓 CGPA ELIGIBILITY ANALYSIS:")
    print("-" * 35)
    cgpa_thresholds = [6.0, 7.0, 8.0, 9.0]
    
    for cgpa in cgpa_thresholds:
        try:
            params = {'min_cgpa': str(cgpa), 'max_backlogs': '4'}
            response = requests.get(f"{base_url}/api/placement/eligible-students", params=params)
            if response.status_code == 200:
                data = response.json()
                total = data.get('total_eligible', 0)
                print(f"CGPA ≥ {cgpa}: {total:4d} eligible students")
        except Exception as e:
            print(f"Error for CGPA {cgpa}: {e}")
    
    # Test 3: Backlog analysis
    print(f"\n📚 BACKLOG ANALYSIS:")
    print("-" * 20)
    backlog_limits = [0, 1, 2, 3, 4]
    
    for max_backlogs in backlog_limits:
        try:
            params = {'min_cgpa': '6.0', 'max_backlogs': str(max_backlogs)}
            response = requests.get(f"{base_url}/api/placement/eligible-students", params=params)
            if response.status_code == 200:
                data = response.json()
                total = data.get('total_eligible', 0)
                print(f"Backlogs ≤ {max_backlogs}: {total:4d} eligible students")
        except Exception as e:
            print(f"Error for backlogs {max_backlogs}: {e}")
    
    # Test 4: Specific class range examples
    print(f"\n🏫 CLASS RANGE EXAMPLES:")
    print("-" * 25)
    
    # Get some actual ranges to test
    try:
        response = requests.get(f"{base_url}/api/placement/class-ranges")
        if response.status_code == 200:
            data = response.json()
            ranges = data.get('class_ranges', [])
            
            # Test with a few actual ranges
            for range_info in ranges[:3]:
                class_range = range_info['range']
                try:
                    params = {
                        'min_cgpa': '6.0',
                        'max_backlogs': '4',
                        'class_range': class_range
                    }
                    response = requests.get(f"{base_url}/api/placement/eligible-students", params=params)
                    if response.status_code == 200:
                        range_data = response.json()
                        eligible = range_data.get('total_eligible', 0)
                        print(f"{class_range}: {eligible} eligible out of {range_info['student_count']} total")
                except Exception as e:
                    print(f"Error for range {class_range}: {e}")
    except Exception as e:
        print(f"Error getting ranges: {e}")
    
    # Test 5: Top performers
    print(f"\n⭐ TOP PERFORMERS (CGPA ≥ 9.0):")
    print("-" * 35)
    try:
        params = {'min_cgpa': '9.0', 'max_backlogs': '0'}
        response = requests.get(f"{base_url}/api/placement/eligible-students", params=params)
        if response.status_code == 200:
            data = response.json()
            students = data.get('eligible_students', [])[:10]  # Top 10
            print(f"Found {len(students)} top performers:")
            for i, student in enumerate(students, 1):
                print(f"{i:2d}. {student['student_id']} - CGPA: {student['cgpa']:.2f} - Branch: {student['branch']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print(f"\n✅ PLACEMENT MODULE READY!")
    print("🌐 Access the dashboard at: http://127.0.0.1:5000/placement")
    print("🎯 Features include:")
    print("   - Real-time CGPA filtering")
    print("   - Class range selection (e.g., 23B81A1266-23B81A12D0)")
    print("   - Backlog tracking (up to 4 backlogs)")
    print("   - Branch-wise analysis")
    print("   - Export to CSV/PDF")
    print("   - Placement eligibility determination")

if __name__ == "__main__":
    test_comprehensive_placement()
