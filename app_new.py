from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
import json

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Load Firebase configuration
with open('serviceAccount.json', 'r') as f:
    service_account = json.load(f)

# Initialize Firebase with explicit project ID
cred = credentials.Certificate('serviceAccount.json')
firebase_app = firebase_admin.initialize_app(cred, {
    'projectId': service_account['project_id'],
    'storageBucket': 'plant-ec218.firebasestorage.app'
})

# Initialize Firestore and Storage using Firebase Admin SDK
db = firestore.client(app=firebase_app)
bucket = storage.bucket(app=firebase_app)

# Firebase configuration for frontend
firebase_config = {
    'projectId': service_account['project_id'],
    'storageBucket': 'plant-ec218.firebasestorage.app'
}

@app.route('/')
def dashboard():
    return render_template('dashboard.html', firebase_config=firebase_config)

@app.route('/api/notices', methods=['GET', 'POST'])
def handle_notices():
    if request.method == 'GET':
        # Get filter parameters
        category = request.args.get('category', 'all')
        priority = request.args.get('priority', 'all')
        
        # Query notices
        query = db.collection('notices')
        if category != 'all':
            query = query.where('category', '==', category)
        if priority != 'all':
            query = query.where('priority', '==', priority)
            
        notices = []
        for doc in query.stream():
            notice_data = doc.to_dict()
            notice_data['id'] = doc.id
            notices.append(notice_data)
            
        return jsonify({'notices': notices})
    
    elif request.method == 'POST':
        try:
            print("Received POST request for notice creation")
            print("Request form:", request.form)
            print("Request files:", request.files)
            data = request.form.to_dict()
            print("Form data:", data)
            files = request.files.getlist('attachments')
            print("Number of files:", len(files))
            
            # Process attachments if any
            attachments = []
            for file in files:
                if file:
                    try:
                        # Create a unique path for the file
                        filename = f"notices/{os.urandom(16).hex()}/{file.filename}"
                        blob = bucket.blob(filename)
                        
                        # Debug information
                        print(f"Uploading file {file.filename} to bucket {bucket.name}")
                        print(f"Full path: {blob.path}")
                        
                        # Upload the file with explicit content type
                        content = file.read()
                        content_type = file.content_type or 'application/octet-stream'
                        
                        # Upload with metadata
                        blob.upload_from_string(
                            content,
                            content_type=content_type,
                            timeout=120  # Increase timeout to 120 seconds
                        )
                        
                        # Make the file public and get URL
                        blob.make_public()
                        public_url = blob.public_url
                        print(f"File uploaded successfully. Public URL: {public_url}")
                        
                        attachments.append({
                            'fileName': file.filename,
                            'fileUrl': public_url
                        })
                    except Exception as e:
                        print(f"Error uploading file {file.filename}: {str(e)}")
                        # Continue with other files if one fails
                        continue
            
            # Create notice document
            notice_data = {
                'title': data.get('title'),
                'content': data.get('content'),
                'category': data.get('category', 'general'),
                'priority': data.get('priority', 'medium'),
                'attachments': attachments,
                'createdAt': firestore.SERVER_TIMESTAMP
            }
            
            print("Notice data to save:", notice_data)
            
            # Create a clean document ID from the title
            doc_id = data.get('title', '').strip()
            if not doc_id:
                return jsonify({'error': 'Title is required'}), 400
            
            # Clean the title to make it a valid Firestore document ID
            # Remove special characters and replace spaces with underscores
            import re
            import time
            doc_id = re.sub(r'[^\w\s-]', '', doc_id)  # Remove special chars except spaces and hyphens
            doc_id = re.sub(r'[-\s]+', '_', doc_id)   # Replace spaces and hyphens with underscores
            doc_id = doc_id.strip('_')                # Remove leading/trailing underscores
            
            # Ensure the ID is not empty and not too long (Firestore limit is 1500 bytes)
            if not doc_id:
                doc_id = "notice_" + str(int(time.time()))
            elif len(doc_id.encode('utf-8')) > 1000:  # Keep it under 1000 bytes for safety
                doc_id = doc_id[:100] + "_" + str(int(time.time()))
            
            print(f"Using document ID: {doc_id}")
            
            # Save to Firestore with the title-based ID
            doc_ref = db.collection('notices').document(doc_id)
            doc_ref.set(notice_data)
            
            print("Notice saved successfully with ID:", doc_id)
            return jsonify({'message': 'Notice created successfully', 'id': doc_id})
            
        except Exception as e:
            print("Error creating notice:", str(e))
            return jsonify({'error': str(e)}), 500

@app.route('/api/notices/<notice_id>', methods=['PUT', 'DELETE'])
def update_or_delete_notice(notice_id):
    if request.method == 'PUT':
        try:
            print(f"Received PUT request for notice {notice_id}")
            data = request.form.to_dict()
            print("Update data:", data)
            files = request.files.getlist('attachments')
            print("Number of new files:", len(files))
            
            # Get existing notice
            doc_ref = db.collection('notices').document(notice_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return jsonify({'error': 'Notice not found'}), 404
            
            existing_data = doc.to_dict()
            
            # Process new attachments if any
            new_attachments = []
            for file in files:
                if file:
                    try:
                        filename = f"notices/{os.urandom(16).hex()}/{file.filename}"
                        blob = bucket.blob(filename)
                        
                        content = file.read()
                        content_type = file.content_type or 'application/octet-stream'
                        
                        blob.upload_from_string(
                            content,
                            content_type=content_type,
                            timeout=120
                        )
                        
                        blob.make_public()
                        public_url = blob.public_url
                        print(f"New file uploaded successfully. Public URL: {public_url}")
                        
                        new_attachments.append({
                            'fileName': file.filename,
                            'fileUrl': public_url
                        })
                    except Exception as e:
                        print(f"Error uploading file {file.filename}: {str(e)}")
                        continue
            
            # Keep existing attachments and add new ones
            all_attachments = existing_data.get('attachments', []) + new_attachments
            
            # Update notice document
            updated_data = {
                'title': data.get('title'),
                'content': data.get('content'),
                'category': data.get('category', 'general'),
                'priority': data.get('priority', 'medium'),
                'attachments': all_attachments,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            
            doc_ref.update(updated_data)
            print("Notice updated successfully")
            
            return jsonify({'message': 'Notice updated successfully'})
            
        except Exception as e:
            print("Error updating notice:", str(e))
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            # Get the notice document
            doc_ref = db.collection('notices').document(notice_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return jsonify({'error': 'Notice not found'}), 404
                
            # Delete attachments from storage if they exist
            notice_data = doc.to_dict()
            if 'attachments' in notice_data:
                for attachment in notice_data['attachments']:
                    try:
                        file_path = attachment['fileUrl'].split('/o/')[1].split('?')[0]
                        blob = bucket.blob(file_path)
                        blob.delete()
                    except Exception as e:
                        print(f"Failed to delete file: {str(e)}")
            
            # Delete the notice document
            doc_ref.delete()
            return jsonify({'message': 'Notice deleted successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

def generate_json_file(student_results, original_filename, format_type, exam_types, year, semesters):
    """Generate JSON file in both data and temp folders with the same format as existing data folder"""
    import datetime
    
    # Create directories if they don't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    exam_type_str = "_".join(exam_types)
    json_filename = f"parsed_results_{format_type}_{exam_type_str}_{timestamp}.json"
    
    # Prepare data in the same format as existing JSON with Firebase and Cloud Storage status
    json_data = {
        "metadata": {
            "format": format_type,
            "exam_type": exam_types[0] if len(exam_types) == 1 else "mixed",  # Match existing format
            "processed_at": datetime.datetime.now().isoformat(),
            "total_students": len(student_results),
            "original_filename": original_filename
        },
        "students": student_results,
        "firebase_status": {
            "firebase_available": True,
            "saved_count": 0,  # Will be updated after saving
            "failed_count": 0,
            "errors": [],
            "firebase_error": None,
            "status": "pending"
        },
        "cloud_storage": {
            "uploaded": False,
            "url": "",
            "filename": json_filename,
            "upload_completed_at": ""
        }
    }
    
    # Save to data folder first (primary location)
    data_file_path = os.path.join(data_dir, json_filename)
    with open(data_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # Also save to temp folder for backward compatibility
    temp_file_path = os.path.join(temp_dir, json_filename)
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated JSON files:\n- Data folder: {data_file_path}\n- Temp folder: {temp_file_path}")
    
    return data_file_path

def update_json_firebase_status(json_file_path, students_saved, total_students, file_url, json_filename):
    """Update JSON file with Firebase and Cloud Storage status"""
    import datetime
    
    try:
        # Read existing JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Update Firebase status
        json_data['firebase_status'] = {
            "firebase_available": True,
            "saved_count": students_saved,
            "failed_count": total_students - students_saved,
            "errors": [],
            "firebase_error": None,
            "status": "success" if students_saved > 0 else "failed"
        }
        
        # Update Cloud Storage status
        json_data['cloud_storage'] = {
            "uploaded": True,
            "url": file_url,
            "filename": json_filename,
            "upload_completed_at": datetime.datetime.now().isoformat()
        }
        
        # Write updated JSON back to file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        # Also update the temp folder copy
        temp_file_path = json_file_path.replace('data', 'temp')
        if os.path.exists(temp_file_path):
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"Updated JSON file with Firebase status: {students_saved}/{total_students} saved")
        
    except Exception as e:
        print(f"Error updating JSON file status: {str(e)}")

def handle_supply_results(student_results, year, semesters, exam_types, format_type, doc_id, track_attempts):
    """Handle supply results with attempt tracking and data matching"""
    students_processed = 0
    batch = db.batch()
    
    for student_data in student_results:
        student_id = student_data.get('student_id', '')
        if not student_id:
            continue
            
        # Search for existing student records
        existing_query = db.collection('student_results').where('student_id', '==', student_id)
        existing_docs = list(existing_query.stream())
        
        if existing_docs:
            # Update existing records with supply data
            for existing_doc in existing_docs:
                existing_data = existing_doc.to_dict()
                
                # Create new attempt entry
                attempt_number = existing_data.get('attempts', 0) + 1 if track_attempts else 1
                
                # Merge subject grades for supply
                updated_subjects = merge_supply_subjects(
                    existing_data.get('subjectGrades', []), 
                    student_data.get('subjectGrades', [])
                )
                
                # Update the record
                updated_data = {
                    'subjectGrades': updated_subjects,
                    'attempts': attempt_number,
                    'lastSupplyUpdate': firestore.SERVER_TIMESTAMP,
                    'supplyExamTypes': existing_data.get('supplyExamTypes', []) + exam_types,
                    'lastUploadId': doc_id
                }
                
                batch.update(existing_doc.reference, updated_data)
                students_processed += 1
        else:
            # Create new record for supply (student not found in regular results)
            student_doc_id = f"{student_id}_{year.replace(' ', '_')}_{format_type}_supply"
            
            student_data.update({
                'year': year,
                'semester': semesters[0] if semesters else 'Unknown',
                'examType': 'supply',
                'format': format_type,
                'uploadId': doc_id,
                'attempts': 1 if track_attempts else 0,
                'isSupplyOnly': True,
                'uploadedAt': firestore.SERVER_TIMESTAMP
            })
            
            student_ref = db.collection('student_results').document(student_doc_id)
            batch.set(student_ref, student_data)
            students_processed += 1
        
        # Commit batch every 500 operations
        if students_processed % 500 == 0:
            batch.commit()
            batch = db.batch()
    
    # Commit remaining operations
    if students_processed % 500 != 0:
        batch.commit()
    
    return students_processed

def merge_supply_subjects(existing_subjects, supply_subjects):
    """Merge supply subject results with existing ones"""
    subject_map = {}
    
    # Add existing subjects
    for subject in existing_subjects:
        subject_map[subject['code']] = subject
    
    # Update with supply results
    for supply_subject in supply_subjects:
        code = supply_subject['code']
        if code in subject_map:
            # Update existing subject with supply result
            subject_map[code].update({
                'supplyGrade': supply_subject.get('grade'),
                'supplyInternals': supply_subject.get('internals'),
                'hasSupply': True
            })
        else:
            # Add new supply subject
            supply_subject['hasSupply'] = True
            subject_map[code] = supply_subject
    
    return list(subject_map.values())

def create_json_file_header(original_filename, format_type, exam_types, year, semesters):
    """Create initial JSON file with metadata and return file path"""
    import datetime
    
    # Create directories if they don't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    exam_type_str = "_".join(exam_types)
    json_filename = f"parsed_results_{format_type}_{exam_type_str}_{timestamp}.json"
    
    # Initial JSON structure
    json_data = {
        "metadata": {
            "format": format_type,
            "exam_type": exam_types[0] if len(exam_types) == 1 else "mixed",
            "processed_at": datetime.datetime.now().isoformat(),
            "total_students": 0,  # Will be updated as we process
            "original_filename": original_filename,
            "processing_status": "in_progress"
        },
        "students": [],
        "firebase_upload": {
            "uploaded": False,
            "batches_completed": 0,
            "students_saved": 0,
            "duplicates_skipped": 0,
            "upload_started_at": "",
            "upload_completed_at": ""
        }
    }
    
    # Create initial file
    data_file_path = os.path.join(data_dir, json_filename)
    with open(data_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Created initial JSON file: {data_file_path}")
    return data_file_path

def append_batch_to_json(json_file_path, batch_records, batch_num, students_saved, students_skipped):
    """Append a batch of records to the JSON file and update metadata"""
    import json
    from datetime import datetime
    
    try:
        # Read current JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Append new records
        json_data['students'].extend(batch_records)
        
        # Update metadata
        json_data['metadata']['total_students'] = len(json_data['students'])
        json_data['metadata']['last_batch_processed'] = batch_num
        json_data['metadata']['last_updated'] = datetime.now().isoformat()
        
        # Update Firebase status
        json_data['firebase_upload']['batches_completed'] = batch_num
        json_data['firebase_upload']['students_saved'] = students_saved
        json_data['firebase_upload']['duplicates_skipped'] = students_skipped
        
        # Write back to file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Updated JSON file: Batch {batch_num}, Total students: {len(json_data['students'])}")
        
    except Exception as e:
        print(f"❌ Error updating JSON file: {str(e)}")

def finalize_json_file(json_file_path, total_saved, total_skipped):
    """Mark JSON file as completed and update final statistics"""
    import json
    from datetime import datetime
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Update final metadata
        json_data['metadata']['processing_status'] = "completed"
        json_data['metadata']['completed_at'] = datetime.now().isoformat()
        
        # Update final Firebase status
        json_data['firebase_upload']['uploaded'] = True
        json_data['firebase_upload']['students_saved'] = total_saved
        json_data['firebase_upload']['duplicates_skipped'] = total_skipped
        json_data['firebase_upload']['upload_completed_at'] = datetime.now().isoformat()
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Finalized JSON file: {total_saved} saved, {total_skipped} skipped")
        
    except Exception as e:
        print(f"❌ Error finalizing JSON file: {str(e)}")

def batch_upload_to_firebase(batch_records, year, semesters, exam_types, format_type, doc_id):
    """Enhanced Firebase batch upload with optimized batch management"""
    students_saved = 0
    students_skipped = 0
    errors = []
    
    # Firebase batch limit is 500 operations
    FIREBASE_BATCH_LIMIT = 500
    current_batch = db.batch()
    current_batch_count = 0
    
    print(f"💾 Processing {len(batch_records)} records for Firebase upload...")
    
    # Pre-check duplicates in bulk to reduce individual queries
    student_ids = [student_data.get('student_id', '') for student_data in batch_records]
    detected_semester = batch_records[0].get('semester', semesters[0] if semesters else 'Unknown') if batch_records else 'Unknown'
    detected_exam_type = exam_types[0] if exam_types else 'regular'
    
    # Bulk duplicate check
    duplicate_doc_ids = []
    for student_id in student_ids:
        if student_id:
            student_doc_id = f"{student_id}_{year.replace(' ', '_')}_{detected_semester.replace(' ', '_')}_{detected_exam_type}"
            duplicate_doc_ids.append(student_doc_id)
    
    # Check for existing documents in smaller batches to avoid overwhelming Firebase
    existing_docs = set()
    for i in range(0, len(duplicate_doc_ids), 10):  # Check 10 at a time
        batch_doc_ids = duplicate_doc_ids[i:i+10]
        try:
            for doc_id in batch_doc_ids:
                existing_doc = db.collection('student_results').document(doc_id).get()
                if existing_doc.exists:
                    existing_docs.add(doc_id)
        except Exception as e:
            print(f"⚠️ Error in bulk duplicate check: {str(e)}")
    
    print(f"📊 Found {len(existing_docs)} existing records out of {len(batch_records)}")
    
    # Process each student record
    for student_data in batch_records:
        student_id = student_data.get('student_id', '')
        if not student_id:
            continue
        
        # Create unique document ID for this student's record
        student_doc_id = f"{student_id}_{year.replace(' ', '_')}_{detected_semester.replace(' ', '_')}_{detected_exam_type}"
        
        # Skip if already exists (from our bulk check)
        if student_doc_id in existing_docs:
            students_skipped += 1
            continue
        
        # Add metadata to student record
        student_data.update({
            'year': year,
            'semester': detected_semester,
            'examType': detected_exam_type,
            'availableSemesters': semesters,
            'availableExamTypes': exam_types,
            'format': format_type,
            'uploadId': doc_id,
            'attempts': 0,
            'uploadedAt': firestore.SERVER_TIMESTAMP,
            'supplyExamTypes': [],
            'isSupplyOnly': False
        })
        
        # Add to current Firebase batch
        student_ref = db.collection('student_results').document(student_doc_id)
        current_batch.set(student_ref, student_data)
        students_saved += 1
        current_batch_count += 1
        
        # Commit batch when it reaches Firebase limit
        if current_batch_count >= FIREBASE_BATCH_LIMIT:
            try:
                current_batch.commit()
                print(f"✅ Committed Firebase batch: {current_batch_count} records")
                current_batch = db.batch()
                current_batch_count = 0
            except Exception as e:
                print(f"❌ Error committing Firebase batch: {str(e)}")
                errors.append(f"Firebase batch commit failed: {str(e)}")
                # Reset batch and continue
                current_batch = db.batch()
                current_batch_count = 0
                students_saved -= current_batch_count  # Adjust count on failure
    
    # Commit any remaining operations
    if current_batch_count > 0:
        try:
            current_batch.commit()
            print(f"✅ Committed final Firebase batch: {current_batch_count} records")
        except Exception as e:
            print(f"❌ Error committing final Firebase batch: {str(e)}")
            errors.append(f"Final Firebase batch commit failed: {str(e)}")
            students_saved -= current_batch_count  # Adjust count on failure
    
    print(f"📊 Firebase batch upload complete: {students_saved} new, {students_skipped} duplicates")
    return students_saved, students_skipped, errors

def upload_json_to_firebase(json_file_path, year, semesters, exam_types, format_type, doc_id):
    """Upload data to Firebase from a saved JSON file"""
    import json
    from datetime import datetime
    
    print(f"📂 Reading JSON file: {json_file_path}")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Extract student results from JSON
        student_results = json_data.get('students', [])
        if not student_results:
            print("❌ No student data found in JSON file")
            return 0
        
        print(f"📊 Found {len(student_results)} student records in JSON file")
        
        # Use the existing save_regular_results function
        students_saved = save_regular_results(student_results, year, semesters, exam_types, format_type, doc_id)
        
        # Update JSON file with Firebase upload status
        json_data['firebase_upload'] = {
            'uploaded': True,
            'students_saved': students_saved,
            'upload_timestamp': datetime.now().isoformat(),
            'duplicates_skipped': len(student_results) - students_saved
        }
        
        # Write back the updated JSON
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated JSON file with Firebase upload status")
        return students_saved
        
    except Exception as e:
        print(f"❌ Error uploading from JSON: {str(e)}")
        return 0

def streaming_firebase_saver(year, semesters, exam_types, format_type, doc_id):
    """Create a streaming callback function to save data to Firebase in real-time"""
    students_saved = 0
    students_skipped = 0
    errors = []
    batch = db.batch()
    batch_count = 0
    MAX_BATCH_SIZE = 100  # Smaller batches for faster commits
    
    def save_student_record(student_data, total_processed):
        nonlocal students_saved, students_skipped, errors, batch, batch_count
        
        student_id = student_data.get('student_id', '')
        if not student_id:
            return
        
        # Detect semester and exam type from student data if possible
        detected_semester = student_data.get('semester', semesters[0] if semesters else 'Unknown')
        detected_exam_type = exam_types[0] if exam_types else 'regular'
        
        # Create unique document ID for this student's record
        student_doc_id = f"{student_id}_{year.replace(' ', '_')}_{detected_semester.replace(' ', '_')}_{detected_exam_type}"
        
        # Check for duplicates
        try:
            existing_doc = db.collection('student_results').document(student_doc_id).get()
            if existing_doc.exists:
                students_skipped += 1
                print(f"💨 [{total_processed}] Skipping duplicate: {student_id}")
                return
        except Exception as e:
            print(f"❌ Error checking duplicate {student_doc_id}: {str(e)}")
            errors.append(f"Duplicate check failed for {student_id}: {str(e)}")
            return
        
        # Add metadata to student record
        student_data.update({
            'year': year,
            'semester': detected_semester,
            'examType': detected_exam_type,
            'availableSemesters': semesters,
            'availableExamTypes': exam_types,
            'format': format_type,
            'uploadId': doc_id,
            'attempts': 0,
            'uploadedAt': firestore.SERVER_TIMESTAMP,
            'supplyExamTypes': [],
            'isSupplyOnly': False
        })
        
        student_ref = db.collection('student_results').document(student_doc_id)
        batch.set(student_ref, student_data)
        students_saved += 1
        batch_count += 1
        
        print(f"✅ [{total_processed}] Added to batch: {student_id} - {detected_semester}")
        
        # Commit batch when it reaches the limit
        if batch_count >= MAX_BATCH_SIZE:
            try:
                batch.commit()
                print(f"🚀 Committed batch of {batch_count} records (Total saved: {students_saved})")
                batch = db.batch()
                batch_count = 0
            except Exception as e:
                print(f"❌ Error committing batch: {str(e)}")
                errors.append(f"Batch commit failed: {str(e)}")
                batch = db.batch()
                batch_count = 0
    
    def finalize():
        """Commit any remaining operations and return stats"""
        nonlocal batch, batch_count
        
        if batch_count > 0:
            try:
                batch.commit()
                print(f"🏁 Committed final batch of {batch_count} records")
            except Exception as e:
                print(f"❌ Error committing final batch: {str(e)}")
                errors.append(f"Final batch commit failed: {str(e)}")
        
        print(f"📊 Streaming complete: {students_saved} saved, {students_skipped} skipped")
        if errors:
            print(f"⚠️ Encountered {len(errors)} errors")
        
        return students_saved, students_skipped, errors
    
    # Return the callback function and finalizer
    save_student_record.finalize = finalize
    save_student_record.get_stats = lambda: (students_saved, students_skipped, errors)
    return save_student_record

def save_regular_results(student_results, year, semesters, exam_types, format_type, doc_id):
    """Save regular results to Firestore with duplicate prevention"""
    import time
    students_saved = 0
    students_skipped = 0
    errors = []
    batch = db.batch()
    batch_count = 0
    MAX_BATCH_SIZE = 500  # Firestore batch limit
    
    for student_data in student_results:
        student_id = student_data.get('student_id', '')
        if not student_id:
            continue
        
        # Detect semester and exam type from student data if possible
        detected_semester = student_data.get('semester', semesters[0] if semesters else 'Unknown')
        detected_exam_type = exam_types[0] if exam_types else 'regular'
        
        # Create unique document ID for this student's record
        student_doc_id = f"{student_id}_{year.replace(' ', '_')}_{detected_semester.replace(' ', '_')}_{detected_exam_type}"
        
        # Check for duplicates
        try:
            existing_doc = db.collection('student_results').document(student_doc_id).get()
            if existing_doc.exists:
                students_skipped += 1
                print(f"Skipping duplicate record for {student_id} - {detected_semester} - {detected_exam_type}")
                continue
        except Exception as e:
            print(f"Error checking for duplicate {student_doc_id}: {str(e)}")
            errors.append(f"Duplicate check failed for {student_id}: {str(e)}")
            continue
        
        # Add metadata to student record
        student_data.update({
            'year': year,
            'semester': detected_semester,
            'examType': detected_exam_type,
            'availableSemesters': semesters,
            'availableExamTypes': exam_types,
            'format': format_type,
            'uploadId': doc_id,
            'attempts': 0,  # Initial attempt count
            'uploadedAt': firestore.SERVER_TIMESTAMP,
            'supplyExamTypes': [],
            'isSupplyOnly': False
        })
        
        student_ref = db.collection('student_results').document(student_doc_id)
        batch.set(student_ref, student_data)
        students_saved += 1
        batch_count += 1
        
        # Commit batch when it reaches the limit
        if batch_count >= MAX_BATCH_SIZE:
            try:
                batch.commit()
                print(f"Committed batch of {batch_count} records")
                batch = db.batch()
                batch_count = 0
            except Exception as e:
                print(f"Error committing batch: {str(e)}")
                errors.append(f"Batch commit failed: {str(e)}")
                batch = db.batch()
                batch_count = 0
    
    # Commit remaining operations
    if batch_count > 0:
        try:
            batch.commit()
            print(f"Committed final batch of {batch_count} records")
        except Exception as e:
            print(f"Error committing final batch: {str(e)}")
            errors.append(f"Final batch commit failed: {str(e)}")
    
    print(f"Saved {students_saved} new records, skipped {students_skipped} duplicates")
    if errors:
        print(f"Encountered {len(errors)} errors: {errors}")
    
    return students_saved

@app.route('/api/upload-result', methods=['POST'])
def upload_result():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Get form data
        year = request.form.get('year')
        semesters_json = request.form.get('semesters')
        exam_types_json = request.form.get('exam_types')
        format_type = request.form.get('format')
        
        # Supply-specific options
        generate_json = request.form.get('generate_json') == 'true'
        push_to_firebase = request.form.get('push_to_firebase') == 'true'
        track_attempts = request.form.get('track_attempts') == 'true'
        
        # Parse JSON data
        import json
        try:
            semesters = json.loads(semesters_json) if semesters_json else []
            exam_types = json.loads(exam_types_json) if exam_types_json else []
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid semester or exam type data'}), 400
        
        print(f"Received file upload: {file.filename}")
        print(f"Upload parameters - Year: {year}, Semesters: {semesters}, Exam Types: {exam_types}, Format: {format_type}")
        print(f"Supply options - Generate JSON: {generate_json}, Push to Firebase: {push_to_firebase}, Track Attempts: {track_attempts}")
        
        # Validation
        if not all([year, semesters, exam_types, format_type]):
            return jsonify({'error': 'Missing required parameters: year, semesters, exam_types, format'}), 400
        
        # Create a meaningful document ID based on the metadata
        import time
        import tempfile
        import os
        timestamp = int(time.time())
        
        # Create a meaningful document ID with multiple semesters and exam types
        semesters_str = "_".join([s.replace(' ', '_') for s in semesters])
        exam_types_str = "_".join(exam_types)
        doc_id = f"{format_type}_{year.replace(' ', '_')}_{semesters_str}_{exam_types_str}_{timestamp}"
        
        filename = f"results/{format_type}/{year}/multi_semester/{timestamp}_{file.filename}"
        
        # Save file temporarily for parsing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.seek(0)  # Reset file pointer
            temp_file.write(file.read())
            temp_file_path = temp_file.name
        
        try:
            # OPTIMIZED BATCH PROCESSING: Parse + JSON + Firebase in real-time
            print(f"🚀 Starting optimized batch processing with format: {format_type}")
            parse_start_time = time.time()
            
            # Create initial JSON file
            json_file_path = create_json_file_header(file.filename, format_type, exam_types, year, semesters)
            
            # Initialize counters
            total_students = 0
            total_saved = 0
            total_skipped = 0
            batch_num = 0
            all_errors = []
            
            # Process in batches using generators
            if format_type.lower() == 'jntuk':
                from parser.parser_jntuk import parse_jntuk_pdf_generator
                batch_generator = parse_jntuk_pdf_generator(temp_file_path, batch_size=50)
            elif format_type.lower() == 'autonomous':
                from parser.parser_autonomous import parse_autonomous_pdf_generator
                semester_info = f"{year} {semesters[0]}" if semesters else f"{year} Mixed"
                batch_generator = parse_autonomous_pdf_generator(temp_file_path, semester=semester_info, university="Autonomous", batch_size=50)
            else:
                return jsonify({'error': f'Unsupported format: {format_type}'}), 400
            
            # Process each batch as it's generated
            firebase_start_time = time.time()
            
            for batch_records in batch_generator:
                batch_num += 1
                batch_start = time.time()
                
                # Upload batch to Firebase
                if 'supply' in exam_types and push_to_firebase:
                    # Handle supply results differently
                    batch_saved = handle_supply_results(batch_records, year, semesters, exam_types, format_type, doc_id, track_attempts)
                    batch_skipped = len(batch_records) - batch_saved
                else:
                    # Regular batch upload
                    batch_saved, batch_skipped, batch_errors = batch_upload_to_firebase(
                        batch_records, year, semesters, exam_types, format_type, doc_id
                    )
                    all_errors.extend(batch_errors)
                
                # Update counters
                total_students += len(batch_records)
                total_saved += batch_saved
                total_skipped += batch_skipped
                
                # Append batch to JSON file
                append_batch_to_json(json_file_path, batch_records, batch_num, total_saved, total_skipped)
                
                batch_time = time.time() - batch_start
                print(f"🚀 Batch {batch_num} complete: {len(batch_records)} records, {batch_saved} saved, {batch_skipped} duplicates ({batch_time:.2f}s)")
                print(f"📊 Running totals: {total_students} processed, {total_saved} saved, {total_skipped} duplicates")
            
            # Finalize JSON file
            finalize_json_file(json_file_path, total_saved, total_skipped)
            
            firebase_time = time.time() - firebase_start_time
            parse_time = time.time() - parse_start_time
            
            print(f"⏱️ Optimized processing completed in {parse_time:.2f} seconds")
            print(f"📊 Final results: {total_students} extracted, {total_saved} saved, {total_skipped} duplicates")
            
            if total_students == 0:
                print("❌ Warning: No student records were extracted from the PDF")
                return jsonify({'error': 'No student data found in the PDF. Please check if the file format matches the selected parser.'}), 400
            
            # Set student_results for compatibility with rest of the code
            # We'll read a sample from the JSON file for validation
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                student_results = json_data.get('students', [])
            
            students_saved = total_saved  # Use the batch processing results
            json_time = 0  # JSON processing was done incrementally
            
            # Upload file to Firebase Storage
            print("☁️ Uploading PDF to Firebase Storage...")
            storage_start_time = time.time()
            
            file.seek(0)  # Reset file pointer again
            blob = bucket.blob(filename)
            content = file.read()
            
            blob.upload_from_string(
                content,
                content_type='application/pdf'
            )
            
            # Make the file public and get URL
            blob.make_public()
            file_url = blob.public_url
            
            storage_time = time.time() - storage_start_time
            print(f"✅ File uploaded to storage in {storage_time:.2f} seconds: {file_url}")
            
            # Save file metadata to Firestore
            file_data = {
                'originalName': file.filename,
                'storagePath': filename,
                'fileUrl': file_url,
                'fileSize': len(content),
                'year': year,
                'semesters': semesters,
                'examTypes': exam_types,
                'format': format_type,
                'uploadedAt': firestore.SERVER_TIMESTAMP,
                'status': 'processed',
                'processed': True,
                'studentsCount': len(student_results),
                'studentsSaved': students_saved,
                'duplicatesSkipped': len(student_results) - students_saved
            }
            
            doc_ref = db.collection('uploaded_results').document(doc_id)
            doc_ref.set(file_data)
            
            total_time = time.time() - timestamp
            print(f"🏁 TOTAL PROCESSING TIME: {total_time:.2f} seconds")
            print(f"📊 Performance breakdown (Optimized Batch Processing):")
            print(f"   - Parse + JSON + Firebase (Batched): {parse_time:.2f}s")
            print(f"   - File Storage: {storage_time:.2f}s")
            
            print(f"✅ Optimized Flow: Parse → Batch Upload → JSON → Storage")
            print(f"📁 JSON file: {os.path.basename(json_file_path) if json_file_path else 'Not generated'}")
            print(f"💾 Firebase: {students_saved} student records uploaded in {batch_num} batches")
            print(f"⚡ Average batch time: {(firebase_time/batch_num):.2f}s per batch")
            
            # Determine upload status
            upload_success = students_saved > 0
            duplicates_skipped = len(student_results) - students_saved
            
            # Prepare response message
            message_parts = []
            if upload_success:
                message_parts.append(f'✅ File processed with optimized batching! Extracted {len(student_results)} student records')
                message_parts.append(f'📊 Saved {students_saved} new records to Firebase in {batch_num} batches')
                if duplicates_skipped > 0:
                    message_parts.append(f'⚠️ Skipped {duplicates_skipped} duplicate records')
                message_parts.append(f'⚡ Average batch time: {(firebase_time/batch_num if batch_num > 0 else 0):.1f}s per batch')
            else:
                message_parts.append(f'⚠️ File processed but no new records saved. All {len(student_results)} records were duplicates')
            
            if 'supply' in exam_types:
                message_parts.append('🔄 Supply results have been matched and updated with attempt tracking')
            message_parts.append(f'📁 JSON file saved with real-time updates: {os.path.basename(json_file_path)}')
            message_parts.append('💾 Data uploaded to Firebase with optimized batching')
            
            response_data = {
                'success': upload_success,
                'message': '. '.join(message_parts),
                'fileId': doc_id,
                'fileUrl': file_url,
                'studentsExtracted': len(student_results),
                'studentsProcessed': students_saved,
                'duplicatesSkipped': duplicates_skipped,
                'jsonGenerated': True,  # Always true now
                'jsonFilePath': os.path.basename(json_file_path) if json_file_path else None,
                'processingFlow': 'Optimized Batch Processing',
                'batchesProcessed': batch_num,
                'averageBatchTime': round(firebase_time/batch_num if batch_num > 0 else 0, 2),
                'uploadStatus': 'success' if upload_success else 'partial_success',
                'metadata': {
                    'year': year,
                    'semesters': semesters,
                    'examTypes': exam_types,
                    'format': format_type,
                    'supplyProcessing': 'supply' in exam_types,
                    'timestamp': timestamp
                }
            }
            
            return jsonify(response_data)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/student-results', methods=['GET'])
def get_student_results():
    try:
        # Get query parameters
        year = request.args.get('year')
        semester = request.args.get('semester')
        exam_type = request.args.get('exam_type')
        format_type = request.args.get('format')
        student_id = request.args.get('student_id')
        
        # Start with all student results
        results_ref = db.collection('student_results')
        
        # Apply filters if provided
        if year:
            results_ref = results_ref.where('year', '==', year)
        if semester:
            results_ref = results_ref.where('semester', '==', semester)
        if exam_type:
            results_ref = results_ref.where('examType', '==', exam_type)
        if format_type:
            results_ref = results_ref.where('format', '==', format_type)
        if student_id:
            results_ref = results_ref.where('student_id', '==', student_id)
        
        # Execute query
        docs = results_ref.limit(100).stream()  # Limit for performance
        results = []
        
        for doc in docs:
            result = doc.to_dict()
            result['id'] = doc.id
            results.append(result)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        print(f"Error retrieving student results: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/uploaded-results', methods=['GET'])
def get_uploaded_results():
    try:
        docs = db.collection('uploaded_results').order_by('uploadedAt', direction=firestore.Query.DESCENDING).limit(50).stream()
        results = []
        
        for doc in docs:
            result = doc.to_dict()
            result['id'] = doc.id
            results.append(result)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        print(f"Error retrieving uploaded results: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
