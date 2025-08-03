import requests
import os
import time

def test_both_formats():
    """Test uploading both autonomous PDF formats"""
    
    formats_to_test = [
        {
            "file": "sample_autonomous.pdf",
            "name": "Tabular Format (2-2 Results)"
        },
        {
            "file": "sample_autonomous_new.pdf", 
            "name": "Matrix Format (1st BTech 1st Sem)"
        }
    ]
    
    upload_url = "http://127.0.0.1:5000/api/upload-result"
    progress_url = "http://127.0.0.1:5000/api/upload-progress"
    
    for format_info in formats_to_test:
        pdf_path = format_info["file"]
        format_name = format_info["name"]
        
        if not os.path.exists(pdf_path):
            print(f"SKIP: {format_name} - File not found: {pdf_path}")
            continue
            
        print(f"\n{'='*60}")
        print(f"TESTING: {format_name}")
        print(f"File: {pdf_path}")
        print(f"Size: {os.path.getsize(pdf_path)} bytes")
        print(f"{'='*60}")
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'pdf': (os.path.basename(pdf_path), pdf_file, 'application/pdf')}
                data = {
                    'format': 'autonomous',
                    'exam_type': 'regular',
                    'overwrite': 'true'
                }
                
                print("Uploading...")
                response = requests.post(upload_url, files=files, data=data, timeout=30)
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    response_data = response.json()
                    upload_id = response_data.get('upload_id')
                    print(f"SUCCESS! Upload ID: {upload_id}")
                    
                    if upload_id:
                        # Check progress
                        print("Checking progress...")
                        for i in range(30):  # Check for up to 30 seconds
                            try:
                                progress_response = requests.get(f"{progress_url}/{upload_id}")
                                if progress_response.status_code == 200:
                                    progress_data = progress_response.json()
                                    status = progress_data.get('status', 'unknown')
                                    print(f"Progress: {status}")
                                    
                                    if status == 'completed':
                                        print(f"COMPLETED! Students: {progress_data.get('students_processed', 'N/A')}")
                                        break
                                    elif status == 'failed':
                                        print(f"FAILED! Error: {progress_data.get('error', 'Unknown')}")
                                        break
                                        
                                time.sleep(1)
                            except:
                                break
                else:
                    print("FAILED!")
                    print(f"Response: {response.text[:200]}...")
                    
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_both_formats()
