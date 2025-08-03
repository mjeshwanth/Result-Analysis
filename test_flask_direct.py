#!/usr/bin/env python3
"""Test Flask upload endpoint directly with error handling"""

import requests
import json
import traceback

def test_flask_upload():
    """Test the Flask upload endpoint with detailed error handling"""
    
    # Try different possible endpoints
    endpoints = [
        "http://127.0.0.1:5000/upload-pdf",
        "http://127.0.0.1:5000/api/upload-result",
        "http://127.0.0.1:5000/upload"
    ]
    
    # Test with smaller matrix format file first
    pdf_path = "sample_autonomous_new.pdf"
    
    for upload_url in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing upload to: {upload_url}")
        print(f"File: {pdf_path}")
        print(f"{'='*60}")
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'pdf': (pdf_path, pdf_file, 'application/pdf')}
                data = {
                    'format': 'autonomous',
                    'exam_type': 'regular',
                    'overwrite': 'true'
                }
                
                print("Making request...")
                response = requests.post(upload_url, files=files, data=data, timeout=300)
                
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print("SUCCESS!")
                    try:
                        result = response.json()
                        print(f"Response JSON: {json.dumps(result, indent=2)}")
                    except:
                        print(f"Response Text: {response.text[:500]}...")
                    break
                elif response.status_code == 401:
                    print("Authentication required")
                    print(f"Response: {response.text}")
                elif response.status_code == 404:
                    print("Endpoint not found")
                elif response.status_code == 405:
                    print("Method not allowed")
                else:
                    print("FAILED!")
                    print(f"Response Text: {response.text}")
                        
        except Exception as e:
            print(f"Exception occurred: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    test_flask_upload()
