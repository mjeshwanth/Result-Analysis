#!/usr/bin/env python3
"""
Test Login Flow for Placement Dashboard Access
"""

import requests
import json

def test_login_flow():
    base_url = "http://127.0.0.1:5000"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("🔍 Testing Admin Portal Login Flow...")
    print("=" * 50)
    
    # Step 1: Test login page access
    print("1. Testing login page access...")
    try:
        login_page = session.get(f"{base_url}/admin")
        print(f"   ✅ Login page: {login_page.status_code}")
    except Exception as e:
        print(f"   ❌ Login page error: {e}")
        return
    
    # Step 2: Test login API
    print("2. Testing login API...")
    login_data = {
        "email": "admin@scrreddy.edu.in",
        "password": "admin123456"
    }
    
    try:
        login_response = session.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   ✅ Login API: {login_response.status_code}")
        print(f"   📄 Response: {login_response.json()}")
    except Exception as e:
        print(f"   ❌ Login API error: {e}")
        return
    
    # Step 3: Test dashboard access
    print("3. Testing main dashboard access...")
    try:
        dashboard_response = session.get(f"{base_url}/")
        print(f"   ✅ Dashboard: {dashboard_response.status_code}")
        if dashboard_response.status_code == 200:
            print("   🎉 Dashboard accessible after login!")
        else:
            print("   ⚠️  Dashboard returned non-200 status")
    except Exception as e:
        print(f"   ❌ Dashboard error: {e}")
    
    # Step 4: Test placement dashboard access
    print("4. Testing placement dashboard access...")
    try:
        placement_response = session.get(f"{base_url}/placement")
        print(f"   ✅ Placement Dashboard: {placement_response.status_code}")
        if placement_response.status_code == 200:
            print("   🎉 Placement dashboard accessible!")
        else:
            print("   ⚠️  Placement dashboard returned non-200 status")
    except Exception as e:
        print(f"   ❌ Placement dashboard error: {e}")
    
    # Step 5: Test placement API endpoints
    print("5. Testing placement API endpoints...")
    api_endpoints = [
        "/api/placement/students-analysis",
        "/api/placement/eligible-students",
        "/api/placement/class-ranges"
    ]
    
    for endpoint in api_endpoints:
        try:
            api_response = session.get(f"{base_url}{endpoint}")
            print(f"   ✅ {endpoint}: {api_response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} error: {e}")
    
    print("=" * 50)
    print("✅ Login flow test completed!")

if __name__ == "__main__":
    test_login_flow()
