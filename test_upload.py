import requests
import os

def test_autonomous_upload():
    """Test uploading the autonomous PDF via API"""
    
    # Check if sample PDF exists
    pdf_path = "sample_autonomous.pdf"
    if not os.path.exists(pdf_path):
        print("❌ Sample PDF not found")
        return
    
    print(f"📄 Testing upload of: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path)} bytes")
    
    # Upload URL
    url = "http://127.0.0.1:5000/upload"
    
    # Prepare the upload
    with open(pdf_path, 'rb') as pdf_file:
        files = {'pdf': ('sample_autonomous.pdf', pdf_file, 'application/pdf')}  # Changed 'file' to 'pdf'
        data = {
            'format': 'autonomous',  # Changed 'format_type' to 'format'
            'exam_type': 'regular',
            'overwrite': 'true'
        }
        
        print("🚀 Uploading PDF...")
        try:
            response = requests.post(url, files=files, data=data, timeout=300)
            
            print(f"📋 Status Code: {response.status_code}")
            print(f"📝 Response: {response.text[:500]}...")
            
            if response.status_code == 200:
                print("✅ Upload successful!")
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_autonomous_upload()
