#!/usr/bin/env python3
"""
Optimized Batch PDF Processor
Processes multiple JNTUK PDFs efficiently with detailed debugging
"""

import os
import glob
import json
import time
from datetime import datetime
from parser.parser_jntuk import parse_jntuk_pdf_generator
import firebase_admin
from firebase_admin import credentials, firestore, storage

def create_json_file_header(original_filename, format_type, exam_types, year, semesters):
    """Create initial JSON file with metadata and return file path"""
    # Create directories if they don't exist
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exam_type_str = "_".join(exam_types)
    json_filename = f"parsed_results_{format_type}_{exam_type_str}_{timestamp}.json"
    
    # Initial JSON structure
    json_data = {
        "metadata": {
            "format": format_type,
            "exam_type": exam_types[0] if len(exam_types) == 1 else "mixed",
            "processed_at": datetime.now().isoformat(),
            "total_students": 0,
            "original_filename": original_filename,
            "processing_status": "in_progress",
            "year": year,
            "semesters": semesters
        },
        "firebase_upload": {
            "batches_completed": 0,
            "students_saved": 0,
            "duplicates_skipped": 0,
            "upload_started_at": "",
            "upload_completed_at": ""
        },
        "students": []
    }
    
    json_file_path = os.path.join(data_dir, json_filename)
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Created JSON file: {json_filename}")
    return json_file_path

def append_batch_to_json(json_file_path, batch_records, batch_num, students_saved, students_skipped):
    """Append a batch of records to the JSON file and update metadata"""
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

def batch_upload_to_firebase(batch_records, year, semesters, exam_types, format_type, doc_id, pdf_filename=None):
    """Upload a batch of records to Firebase"""
    try:
        db = firestore.client()
        students_saved = 0
        duplicates_skipped = 0
        errors = []
        
        for student in batch_records:
            try:
                student_id = student.get('student_id')
                if not student_id:
                    errors.append("Missing student_id")
                    continue
                
                # Add PDF filename to student record
                if pdf_filename:
                    student['pdf_filename'] = pdf_filename
                    student['source_document'] = pdf_filename
                
                # Check if student already exists
                existing_docs = db.collection('student_results').where('student_id', '==', student_id).stream()
                existing_doc = None
                for doc in existing_docs:
                    existing_doc = doc
                    break
                
                if existing_doc:
                    duplicates_skipped += 1
                else:
                    # Add new student
                    db.collection('student_results').add(student)
                    students_saved += 1
                    
            except Exception as e:
                errors.append(f"Error processing {student.get('student_id', 'unknown')}: {str(e)}")
        
        return students_saved, duplicates_skipped, errors
        
    except Exception as e:
        return 0, 0, [f"Firebase error: {str(e)}"]

def setup_firebase():
    """Initialize Firebase if not already done"""
    try:
        # Check if Firebase is already initialized
        app = firebase_admin.get_app()
        print("✅ Firebase already initialized")
        return firestore.client(app), storage.bucket(app)
    except ValueError:
        # Initialize Firebase
        cred = credentials.Certificate('serviceAccount.json')
        app = firebase_admin.initialize_app(cred, {
            'storageBucket': 'result-analysis-d8a7b.appspot.com'
        })
        print("✅ Firebase initialized")
        return firestore.client(app), storage.bucket(app)
    
    return firestore.client(), storage.bucket()

def detect_pdf_metadata(pdf_path):
    """Detect semester and year from PDF filename"""
    filename = os.path.basename(pdf_path).lower()
    
    # Extract year
    year = "Unknown"
    if "i b.tech i semester" in filename or "1st btech 1st sem" in filename:
        year = "1 Year"
    elif "i b.tech ii semester" in filename or "btech 2-1" in filename:
        year = "2 Year"
    
    # Extract semester
    semester = "Unknown"
    if "i semester" in filename or "1st sem" in filename:
        semester = "Semester 1"
    elif "ii semester" in filename or "2-1" in filename:
        semester = "Semester 2"
    
    # Extract exam type
    exam_type = "regular"
    if "supplementary" in filename or "supply" in filename:
        exam_type = "supplementary"
    
    return {
        'year': year,
        'semesters': [semester],
        'exam_types': [exam_type],
        'format': 'jntuk'
    }

def process_single_pdf(pdf_path, db, bucket):
    """Process a single PDF with optimized batch processing"""
    print(f"\n🚀 Processing: {os.path.basename(pdf_path)}")
    start_time = time.time()
    
    # Detect metadata
    metadata = detect_pdf_metadata(pdf_path)
    print(f"📊 Detected: {metadata}")
    
    # Initialize JSON file and get timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = create_json_file_header(
        os.path.basename(pdf_path),
        metadata['format'], 
        metadata['exam_types'], 
        metadata['year'], 
        metadata['semesters']
    )
    doc_id = f"upload_{timestamp}"
    
    # Process PDF in batches
    total_students = 0
    total_saved = 0
    total_skipped = 0
    batch_count = 0
    
    try:
        print(f"🔍 Starting batch processing...")
        
        for batch_records in parse_jntuk_pdf_generator(pdf_path, batch_size=50):
            batch_count += 1
            batch_size = len(batch_records)
            total_students += batch_size
            
            print(f"📦 Processing batch {batch_count}: {batch_size} students")
            
            # Upload to Firebase first
            saved, skipped, errors = batch_upload_to_firebase(
                batch_records, 
                metadata['year'], 
                metadata['semesters'], 
                metadata['exam_types'], 
                metadata['format'], 
                doc_id,
                os.path.basename(pdf_path)  # Add PDF filename
            )
            
            # Then append to JSON with the results
            append_batch_to_json(json_path, batch_records, batch_count, saved, skipped)
            
            total_saved += saved
            total_skipped += skipped
            
            if errors:
                print(f"⚠️ Batch {batch_count} errors: {errors}")
            
            print(f"✅ Batch {batch_count} complete: {saved} saved, {skipped} skipped")
        
        # Finalize JSON file
        # Re-read and finalize the JSON structure
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove trailing comma and close array
            if content.endswith(',\n'):
                content = content[:-2] + '\n'
            content += '\n  ]\n}'
            
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"⚠️ Error finalizing JSON: {e}")
        
        processing_time = time.time() - start_time
        
        print(f"🎯 PDF Processing Complete!")
        print(f"📊 Total batches processed: {batch_count}")
        print(f"👥 Total students: {total_students}")
        print(f"💾 Saved to Firebase: {total_saved}")
        print(f"🔄 Duplicates skipped: {total_skipped}")
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"📁 JSON saved: {json_path}")
        
        return {
            'success': True,
            'total_students': total_students,
            'saved': total_saved,
            'skipped': total_skipped,
            'processing_time': processing_time,
            'json_path': json_path
        }
        
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {e}")
        return {
            'success': False,
            'error': str(e),
            'total_students': total_students,
            'processing_time': time.time() - start_time
        }

def main():
    """Main batch processing function"""
    print("🚀 Starting Optimized Batch PDF Processing")
    print("=" * 60)
    
    # Setup Firebase
    db, bucket = setup_firebase()
    
    # Find all PDF files and deduplicate
    pdf_files = []
    pdf_patterns = [
        "*.pdf", "*.PDF"
    ]
    
    for pattern in pdf_patterns:
        pdf_files.extend(glob.glob(pattern, recursive=False))
    
    # Remove duplicates by converting to set and back
    pdf_files = list(set(pdf_files))
    
    # Filter out non-JNTUK PDFs (optional)
    jntuk_pdfs = []
    for pdf in pdf_files:
        filename = os.path.basename(pdf).lower()
        if any(keyword in filename for keyword in ['btech', 'semester', 'result', 'jntuk', 'examination']):
            jntuk_pdfs.append(pdf)
    
    print(f"📁 Found {len(jntuk_pdfs)} JNTUK PDF files:")
    for pdf in jntuk_pdfs:
        print(f"   📄 {os.path.basename(pdf)}")
    
    if not jntuk_pdfs:
        print("❌ No JNTUK PDF files found!")
        return
    
    # Process each PDF
    results = []
    total_start_time = time.time()
    
    for i, pdf_path in enumerate(jntuk_pdfs, 1):
        print(f"\n{'='*60}")
        print(f"📄 Processing PDF {i}/{len(jntuk_pdfs)}")
        print(f"{'='*60}")
        
        result = process_single_pdf(pdf_path, db, bucket)
        results.append({
            'pdf': os.path.basename(pdf_path),
            'result': result
        })
    
    # Summary
    total_time = time.time() - total_start_time
    print(f"\n{'='*60}")
    print(f"🎯 BATCH PROCESSING COMPLETE!")
    print(f"{'='*60}")
    
    total_students = sum(r['result'].get('total_students', 0) for r in results)
    total_saved = sum(r['result'].get('saved', 0) for r in results)
    total_skipped = sum(r['result'].get('skipped', 0) for r in results)
    successful_pdfs = sum(1 for r in results if r['result'].get('success', False))
    
    print(f"📊 PDFs processed: {len(jntuk_pdfs)}")
    print(f"✅ Successful: {successful_pdfs}")
    print(f"❌ Failed: {len(jntuk_pdfs) - successful_pdfs}")
    print(f"👥 Total students extracted: {total_students}")
    print(f"💾 Total saved to Firebase: {total_saved}")
    print(f"🔄 Total duplicates skipped: {total_skipped}")
    print(f"⏱️ Total processing time: {total_time:.2f} seconds")
    print(f"⚡ Average per PDF: {total_time/len(jntuk_pdfs):.2f} seconds")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for result in results:
        pdf_name = result['pdf']
        res = result['result']
        if res.get('success'):
            print(f"✅ {pdf_name}: {res.get('total_students', 0)} students, {res.get('processing_time', 0):.1f}s")
        else:
            print(f"❌ {pdf_name}: FAILED - {res.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
