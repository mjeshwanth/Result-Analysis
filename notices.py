from flask import Blueprint, request, jsonify
import firebase_admin
from firebase_admin import firestore, storage
import uuid
from datetime import datetime
import os

notices = Blueprint('notices', __name__)

# Initialize Firebase clients safely
try:
    db = firestore.client()
    bucket = storage.bucket()
    FIREBASE_ENABLED = True
except Exception as e:
    print(f"Warning: Firebase not available: {e}")
    db = None
    bucket = None
    FIREBASE_ENABLED = False

ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@notices.route('/api/notices', methods=['GET'])
def list_notices():
    if not FIREBASE_ENABLED:
        return jsonify({'error': 'Firebase not configured', 'notices': []}), 503
        
    try:
        category = request.args.get('category', 'all')
        priority = request.args.get('priority', 'all')

        # Query notices collection
        query = db.collection('notices')
        
        if category != 'all':
            query = query.where('category', '==', category)
        if priority != 'all':
            query = query.where('priority', '==', priority)
        
        # Order by creation date
        query = query.order_by('createdAt', direction=firestore.Query.DESCENDING)
        
        notices = []
        for doc in query.stream():
            notice_data = doc.to_dict()
            notice_data['id'] = doc.id
            notices.append(notice_data)

        return jsonify({
            'status': 'success',
            'notices': notices
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@notices.route('/api/notices', methods=['POST'])
def create_notice():
    if not FIREBASE_ENABLED:
        return jsonify({'error': 'Firebase not configured'}), 503
        
    try:
        # Get form data
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        priority = request.form.get('priority')
        valid_until = request.form.get('validUntil')

        if not all([title, content, category, priority]):
            return jsonify({
                'status': 'error',
                'error': 'Missing required fields'
            }), 400

        # Handle file uploads
        attachments = []
        files = request.files.getlist('attachments')
        
        for file in files:
            if file and allowed_file(file.filename):
                if file.content_length and file.content_length > MAX_FILE_SIZE:
                    return jsonify({
                        'status': 'error',
                        'error': f'File {file.filename} exceeds maximum size of 10MB'
                    }), 400

                # Generate unique filename
                ext = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4()}{ext}"
                
                # Upload to Firebase Storage
                blob = bucket.blob(f"notices/{unique_filename}")
                blob.upload_from_string(
                    file.read(),
                    content_type=file.content_type
                )
                
                # Make public and get URL
                blob.make_public()
                
                attachments.append({
                    'fileName': file.filename,
                    'fileUrl': blob.public_url,
                    'fileType': file.content_type,
                    'uploadedAt': datetime.utcnow().isoformat()
                })

        # Create notice document
        notice_data = {
            'title': title,
            'content': content,
            'category': category,
            'priority': priority,
            'attachments': attachments,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            'createdBy': 'admin',
            'status': 'active'
        }

        if valid_until:
            notice_data['validUntil'] = valid_until

        # Save to Firestore
        doc_ref = db.collection('notices').document()
        doc_ref.set(notice_data)

        return jsonify({
            'status': 'success',
            'message': 'Notice created successfully',
            'noticeId': doc_ref.id
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@notices.route('/api/notices/<notice_id>', methods=['DELETE'])
def delete_notice(notice_id):
    if not FIREBASE_ENABLED:
        return jsonify({'error': 'Firebase not configured'}), 503
        
    try:
        # Get the notice
        notice_ref = db.collection('notices').document(notice_id)
        notice = notice_ref.get()

        if not notice.exists:
            return jsonify({
                'status': 'error',
                'error': 'Notice not found'
            }), 404

        # Delete attachments from storage
        notice_data = notice.to_dict()
        if 'attachments' in notice_data:
            for attachment in notice_data['attachments']:
                if 'fileUrl' in attachment:
                    try:
                        # Extract blob name from URL
                        blob_name = attachment['fileUrl'].split('/')[-1]
                        blob = bucket.blob(f"notices/{blob_name}")
                        blob.delete()
                    except Exception as e:
                        print(f"Error deleting file: {str(e)}")

        # Delete notice document
        notice_ref.delete()

        return jsonify({
            'status': 'success',
            'message': 'Notice deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
