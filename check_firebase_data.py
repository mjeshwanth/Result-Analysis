#!/usr/bin/env python3
"""
Check Firebase data to see what student records exist
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json

def check_firebase_data():
    """Check what data exists in Firebase"""
    print("🔍 Checking Firebase Data")
    print("=" * 50)
    
    try:
        # Initialize Firebase if not already done
        try:
            app = firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate('serviceAccount.json')
            app = firebase_admin.initialize_app(cred)
        
        db = firestore.client(app)
        
        # Get all documents from student_results collection
        docs = db.collection('student_results').limit(10).stream()
        
        count = 0
        sample_students = []
        
        for doc in docs:
            count += 1
            doc_data = doc.to_dict()
            sample_students.append({
                'id': doc.id,
                'student_id': doc_data.get('student_id'),
                'student_name': doc_data.get('student_name'),
                'semester': doc_data.get('semester'),
                'year': doc_data.get('year'),
                'sgpa': doc_data.get('sgpa', doc_data.get('grades', {}).get('sgpa'))
            })
        
        print(f"📊 Found {count} student records (showing first 10)")
        
        if count > 0:
            print("\n📋 Sample Student Records:")
            for student in sample_students:
                print(f"   🎓 {student['student_id']} - {student['student_name']} (SGPA: {student['sgpa']})")
        else:
            print("❌ No student records found in Firebase")
            print("💡 You may need to upload some PDF results first")
        
        # Get total count
        try:
            all_docs = db.collection('student_results').stream()
            total_count = sum(1 for _ in all_docs)
            print(f"\n📈 Total records in database: {total_count}")
        except Exception as e:
            print(f"⚠️ Could not get total count: {e}")
            
    except FileNotFoundError:
        print("❌ serviceAccount.json not found")
        print("💡 Make sure Firebase credentials are configured")
    except Exception as e:
        print(f"❌ Error accessing Firebase: {e}")

def get_sample_student_ids():
    """Get some sample student IDs for testing"""
    try:
        app = firebase_admin.get_app()
        db = firestore.client(app)
        
        docs = db.collection('student_results').limit(5).stream()
        student_ids = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            student_id = doc_data.get('student_id')
            if student_id:
                student_ids.append(student_id)
        
        if student_ids:
            print(f"\n🧪 Sample Student IDs for testing:")
            for sid in student_ids:
                print(f"   📝 {sid}")
        
        return student_ids
        
    except Exception as e:
        print(f"❌ Error getting sample IDs: {e}")
        return []

if __name__ == "__main__":
    check_firebase_data()
    get_sample_student_ids()
