#!/usr/bin/env python3
"""
Complete Guide: Where and How to Fetch Student Details
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def demonstrate_api_endpoints():
    """Show all ways to fetch student data via API"""
    
    print("🚀 STUDENT DATA FETCHING GUIDE")
    print("=" * 60)
    
    # Sample student ID from Firebase
    student_id = "17B81A0502"
    
    print("📊 METHOD 1: Single Student Search")
    print("-" * 40)
    
    # 1. Basic student search
    url = f"{BASE_URL}/api/students/{student_id}/results"
    print(f"🔗 URL: {url}")
    print("📝 Description: Get all results for a specific student")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: Found {data['count']} results")
            if data['count'] > 0:
                first_result = data['results'][0]
                print(f"   📋 Student: {first_result.get('student_name', 'N/A')}")
                print(f"   🎓 SGPA: {first_result.get('sgpa', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    print(f"\n📊 METHOD 2: Filtered Search")
    print("-" * 40)
    
    # 2. Search with filters
    filters = {
        "semester": "Semester 2",
        "year": "1 Year", 
        "exam_type": "regular",
        "limit": "10"
    }
    
    url_with_filters = f"{BASE_URL}/api/students/{student_id}/results"
    print(f"🔗 URL: {url_with_filters}")
    print(f"🔧 Filters: {filters}")
    print("📝 Description: Get filtered results for a student")
    
    try:
        response = requests.get(url_with_filters, params=filters, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtered Results: {data['count']} found")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    print(f"\n📊 METHOD 3: General Student Search")
    print("-" * 40)
    
    # 3. General search endpoint
    search_url = f"{BASE_URL}/api/students/search"
    search_params = {
        "student_id": student_id,
        "limit": "5"
    }
    
    print(f"🔗 URL: {search_url}")
    print(f"🔍 Search params: {search_params}")
    print("📝 Description: Search across all students")

def show_direct_database_access():
    """Show how to access Firebase directly"""
    
    print(f"\n📊 METHOD 4: Direct Firebase Access")
    print("-" * 40)
    
    code_example = '''
# Direct Firebase Access (for advanced users)
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('serviceAccount.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

# Method 4A: Get specific student
student_id = "17B81A0502"
docs = db.collection('student_results').where('student_id', '==', student_id).stream()

for doc in docs:
    student_data = doc.to_dict()
    print(f"Student: {student_data['student_name']}")
    print(f"SGPA: {student_data.get('sgpa', 'N/A')}")

# Method 4B: Get all students (be careful with large datasets)
all_docs = db.collection('student_results').limit(100).stream()

for doc in all_docs:
    student_data = doc.to_dict()
    # Process each student...
'''
    
    print("💻 Code Example:")
    print(code_example)

def show_web_interface_guide():
    """Guide for using the web interface"""
    
    print(f"\n🌐 WEB INTERFACE LOCATIONS")
    print("=" * 60)
    
    interfaces = [
        {
            "name": "🔍 Student Search Page",
            "url": f"{BASE_URL}/student-search",
            "description": "Primary interface for searching students",
            "features": [
                "Search by Hall Ticket Number",
                "Filter by semester/year/exam type", 
                "Visual grade display",
                "Export results",
                "User-friendly interface"
            ]
        },
        {
            "name": "🏠 Admin Dashboard", 
            "url": f"{BASE_URL}/admin/dashboard",
            "description": "Main admin panel with navigation",
            "features": [
                "Link to student search",
                "Upload new results",
                "Manage notices",
                "System overview"
            ]
        },
        {
            "name": "🔐 Login Page",
            "url": f"{BASE_URL}/admin",
            "description": "Admin authentication (cleaned - no student search)",
            "features": [
                "Email/password login",
                "Firebase authentication",
                "Secure access"
            ]
        }
    ]
    
    for interface in interfaces:
        print(f"\n{interface['name']}")
        print(f"🔗 URL: {interface['url']}")
        print(f"📝 {interface['description']}")
        print("✨ Features:")
        for feature in interface['features']:
            print(f"   • {feature}")

def show_recommended_usage():
    """Show recommended usage patterns"""
    
    print(f"\n💡 RECOMMENDED USAGE PATTERNS")
    print("=" * 60)
    
    patterns = [
        {
            "scenario": "👥 Regular Users/Staff",
            "method": "Web Interface",
            "location": f"{BASE_URL}/student-search",
            "why": "User-friendly, no technical knowledge required"
        },
        {
            "scenario": "🔧 Developers/API Integration", 
            "method": "API Endpoints",
            "location": f"{BASE_URL}/api/students/{{student_id}}/results",
            "why": "Programmatic access, can integrate with other systems"
        },
        {
            "scenario": "📊 Data Analysis/Bulk Operations",
            "method": "Direct Firebase Access",
            "location": "Python script with Firebase SDK",
            "why": "Full control, can process large datasets efficiently"
        },
        {
            "scenario": "📱 Mobile App/External System",
            "method": "REST API",
            "location": f"{BASE_URL}/api/students/search",
            "why": "Standard HTTP interface, works with any programming language"
        }
    ]
    
    for pattern in patterns:
        print(f"\n{pattern['scenario']}")
        print(f"   🎯 Method: {pattern['method']}")
        print(f"   🔗 Location: {pattern['location']}")
        print(f"   💭 Why: {pattern['why']}")

if __name__ == "__main__":
    demonstrate_api_endpoints()
    show_direct_database_access()
    show_web_interface_guide()
    show_recommended_usage()
    
    print(f"\n🎯 QUICK START RECOMMENDATIONS")
    print("=" * 60)
    print("1. 🌐 For manual searches: Use Student Search Page")
    print("2. 🔧 For automation: Use API endpoints")
    print("3. 📊 For bulk analysis: Direct Firebase access")
    print("4. 🔐 Always login first at /admin for web interface")
