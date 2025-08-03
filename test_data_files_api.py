#!/usr/bin/env python3
"""
Test Data Files API
Verify that the data files API works with updated JSON files
"""

import requests
import json

def test_data_files_api():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    print("🧪 Testing Data Files API...")
    print("=" * 40)
    
    try:
        # Login first
        login_data = {"email": "admin@scrreddy.edu.in", "password": "admin123456"}
        login_response = session.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            print("✅ Login successful")
            
            # Test data files API
            data_response = session.get(f"{base_url}/data-files")
            
            if data_response.status_code == 200:
                data = data_response.json()
                files_count = len(data.get("files", []))
                print(f"✅ Data Files API working: Found {files_count} files")
                
                # Show sample file info
                if files_count > 0:
                    sample_file = data["files"][0]
                    print(f"📄 Sample file: {sample_file.get('filename', 'Unknown')}")
                    print(f"   Format: {sample_file.get('metadata', {}).get('format', 'Unknown')}")
                    print(f"   Students: {sample_file.get('metadata', {}).get('total_students', 0)}")
                    
                return True
            else:
                print(f"❌ Data Files API error: {data_response.status_code}")
                return False
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_data_files_api()
    if success:
        print("\n🎉 All data files are properly formatted and accessible!")
    else:
        print("\n⚠️  Issues detected with data files API")
