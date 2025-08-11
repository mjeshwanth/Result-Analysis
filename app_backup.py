import os
import secrets
import logging
import traceback
import json
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

# -----------------------------------------------------------------------------
# Logging setup
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Setup Python Magic for file type checking
# -----------------------------------------------------------------------------
import magic  # Make sure you have python-magic-bin installed (on Windows)

# Initialize Firebase before importing blueprints
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Check if Firebase is already initialized
if not firebase_admin._apps:
    try:
        # Try to load service account
        if os.path.exists('serviceAccount.json'):
            cred = credentials.Certificate('serviceAccount.json')
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'plant-ec218.firebasestorage.app'
            })
            logger.info("Firebase initialized with service account")
        else:
            logger.warning("serviceAccount.json not found - Firebase features disabled")
    except Exception as e:
        logger.warning(f"Firebase initialization failed: {e}")

# Import Blueprints (after Firebase initialization)
from notices import notices

# Import your PDF parsers here (you must define these yourself)
from parser.parser_jntuk import parse_jntuk_pdf
from parser.parser_autonomous import parse_autonomous_pdf

# Import batch processing
from batch_pdf_processor import process_single_pdf

# -----------------------------------------------------------------------------
# Flask app setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'  # Required for sessions
CORS(app)  # Enable CORS for all routes
app.register_blueprint(notices)

@app.route('/')
def index():
    try:
        # Check if user is authenticated
        if 'user_token' not in session:
            return redirect(url_for('admin_login'))
        return render_template('index_new.html')
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return jsonify({"error": "Failed to load index"}), 500

@app.route('/dashboard')
def dashboard():
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return jsonify({"error": "Failed to load dashboard"}), 500

# Firebase configuration for frontend
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyBYY_k5TK-OaQnkc82w-lxJ54bJGqcWZI4",
    "authDomain": "plant-ec218.firebaseapp.com", 
    "projectId": "plant-ec218",
    "storageBucket": "plant-ec218.appspot.com",
    "messagingSenderId": "451074734549",
    "appId": "1:451074734549:web:abc123def456"
}

@app.route('/admin')
def admin_login():
    try:
        # Check if forced login or logout parameter
        force_login = request.args.get('force') == 'true'
        
        # Check if already authenticated (unless forced)
        if 'user_token' in session and not force_login:
            return redirect(url_for('index'))
        return render_template('login.html', firebase_config=FIREBASE_CONFIG)
    except Exception as e:
        logger.error(f"Error rendering login page: {e}")
        return jsonify({"error": "Failed to load login page"}), 500

@app.route('/api/auth/login', methods=['POST'])
def simple_login():
    """Simple login for testing without Firebase"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Simple demo credentials
        if email == "admin@scrreddy.edu.in" and password == "admin123456":
            session['user_token'] = "demo_token_" + email
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/verify', methods=['POST'])
def verify_auth():
    """Verify Firebase token and create session"""
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({'error': 'No token provided'}), 400
        
        # In a real app, verify the Firebase token here
        # For demo purposes, we'll just store it in session
        session['user_token'] = id_token
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Auth verification error: {e}")
        return jsonify({'error': 'Authentication failed'}), 401

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    try:
        # Check if user is authenticated
        if 'user_token' not in session:
            return redirect(url_for('admin_login'))
        return render_template('admin/dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering admin dashboard: {e}")
        return jsonify({"error": "Failed to load admin dashboard"}), 500

@app.route('/upload')
def upload_page():
    try:
        # Check if user is authenticated
        if 'user_token' not in session:
            return redirect(url_for('admin_login'))
        return render_template('upload_new.html')
    except Exception as e:
        logger.error(f"Error rendering upload page: {e}")
        return jsonify({"error": "Failed to load upload page"}), 500

@app.route('/training-placement')
def training_placement():
    try:
        # Check if user is authenticated
        if 'user_token' not in session:
            return redirect(url_for('admin_login'))
        return render_template('training_placement.html')
    except Exception as e:
        logger.error(f"Error rendering training placement page: {e}")
        return jsonify({"error": "Failed to load training placement page"}), 500

# -----------------------------------------------------------------------------
# Firebase variables and setup
# -----------------------------------------------------------------------------
try:
    db = firestore.client()
    bucket = storage.bucket()
    FIREBASE_AVAILABLE = True
    logger.info("Firebase Firestore and Storage clients initialized")
except Exception as e:
    logger.warning(f"Firebase client initialization failed: {e}")
    db = None
    bucket = None
    FIREBASE_AVAILABLE = False

# -----------------------------------------------------------------------------
# Firebase helper functions
# -----------------------------------------------------------------------------
def save_to_firebase(student_results, year, semesters, exam_types, format_type, doc_id, upload_id=None):
    """Save parsed results to Firebase Firestore with progress tracking"""
    if not FIREBASE_AVAILABLE or not db:
        logger.warning("Firebase not available - skipping Firebase upload")
        if upload_id:
            update_progress(upload_id, "firebase_disabled", firebase={"status": "disabled", "message": "Firebase not available"})
        return 0
    
    if upload_id:
        update_progress(upload_id, "firebase_uploading", firebase={"status": "uploading", "progress": 0, "batches": 0, "students_saved": 0})
    
    students_saved = 0
    students_skipped = 0
    batch = db.batch()
    batch_count = 0
    batch_number = 0
    MAX_BATCH_SIZE = 500
    total_students = len(student_results)
    
    try:
        for i, student_data in enumerate(student_results):
            student_id = student_data.get('student_id', '')
            if not student_id:
                continue
            
            # Detect semester from student data
            detected_semester = student_data.get('semester', semesters[0] if semesters else 'Unknown')
            detected_exam_type = exam_types[0] if exam_types else 'regular'
            
            # Create unique document ID
            student_doc_id = f"{student_id}_{year.replace(' ', '_')}_{detected_semester.replace(' ', '_')}_{detected_exam_type}"
            
            # Check for duplicates (with option to skip duplicate checking for fresh uploads)
            try:
                existing_doc = db.collection('student_results').document(student_doc_id).get()
                if existing_doc.exists:
                    students_skipped += 1
                    # Log first few duplicates to help user understand
                    if students_skipped <= 5:
                        logger.info(f"Duplicate found: {student_id} already exists in database")
                    elif students_skipped == 6:
                        logger.info(f"... and {total_students - i} more duplicates (suppressing further duplicate logs)")
                    continue
            except Exception as e:
                logger.warning(f"Error checking duplicate for {student_id}: {e}")
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
            
            # Add to batch
            student_ref = db.collection('student_results').document(student_doc_id)
            batch.set(student_ref, student_data)
            students_saved += 1
            batch_count += 1
            
            # Commit batch when reaching limit
            if batch_count >= MAX_BATCH_SIZE:
                try:
                    batch.commit()
                    batch_number += 1
                    logger.info(f"Committed Firebase batch {batch_number}: {batch_count} records")
                    
                    # Update progress
                    if upload_id:
                        progress = (i + 1) / total_students * 100
                        update_progress(upload_id, "firebase_uploading", firebase={
                            "status": "uploading",
                            "progress": progress,
                            "batches": batch_number,
                            "students_saved": students_saved,
                            "total_students": total_students,
                            "message": f"Batch {batch_number} uploaded: {students_saved} students saved"
                        })
                    
                    batch = db.batch()
                    batch_count = 0
                except Exception as e:
                    logger.error(f"Error committing Firebase batch: {e}")
                    batch = db.batch()
                    batch_count = 0
                    students_saved -= batch_count
        
        # Commit remaining records
        if batch_count > 0:
            try:
                batch.commit()
                batch_number += 1
                logger.info(f"Committed final Firebase batch {batch_number}: {batch_count} records")
            except Exception as e:
                logger.error(f"Error committing final Firebase batch: {e}")
                students_saved -= batch_count
        
        logger.info(f"Firebase upload complete: {students_saved} saved, {students_skipped} skipped")
        
        # Update final progress
        if upload_id:
            update_progress(upload_id, "firebase_complete", firebase={
                "status": "completed",
                "progress": 100,
                "batches": batch_number,
                "students_saved": students_saved,
                "students_skipped": students_skipped,
                "total_students": total_students,
                "message": f"Firebase upload complete: {students_saved} saved, {students_skipped} duplicates skipped"
            })
        
        return students_saved
        
    except Exception as e:
        logger.error(f"Firebase upload error: {e}")
        if upload_id:
            update_progress(upload_id, "firebase_error", firebase={"status": "error", "message": str(e)})
        return 0

def upload_pdf_to_storage(file, filename):
    """Upload PDF file to Firebase Storage"""
    if not FIREBASE_AVAILABLE or not bucket:
        logger.warning("Firebase Storage not available - skipping file upload")
        return None
    
    try:
        file.seek(0)
        blob = bucket.blob(filename)
        content = file.read()
        
        blob.upload_from_string(content, content_type='application/pdf')
        blob.make_public()
        
        logger.info(f"PDF uploaded to Firebase Storage: {filename}")
        return blob.public_url
    except Exception as e:
        logger.error(f"Error uploading PDF to storage: {e}")
        return None

# -----------------------------------------------------------------------------
# Progress tracking for upload operations
# -----------------------------------------------------------------------------
upload_progress = {}

@app.route('/api/upload-progress/<upload_id>', methods=['GET'])
def get_upload_progress(upload_id):
    """Get real-time upload progress"""
    progress = upload_progress.get(upload_id, {
        "status": "not_found",
        "message": "Upload not found"
    })
    return jsonify(progress)

def update_progress(upload_id, status, **kwargs):
    """Update progress for an upload"""
    if upload_id not in upload_progress:
        upload_progress[upload_id] = {
            "status": "starting",
            "timestamp": time.time(),
            "parsing": {"status": "pending", "progress": 0},
            "firebase": {"status": "pending", "progress": 0, "batches": 0, "students_saved": 0},
            "storage": {"status": "pending"},
            "json": {"status": "pending"}
        }
    
    upload_progress[upload_id]["status"] = status
    upload_progress[upload_id]["timestamp"] = time.time()
    
    for key, value in kwargs.items():
        if key in upload_progress[upload_id]:
            if isinstance(upload_progress[upload_id][key], dict) and isinstance(value, dict):
                upload_progress[upload_id][key].update(value)
            else:
                upload_progress[upload_id][key] = value

# -----------------------------------------------------------------------------
# API key setup for authorization (store keys safely in production!)
# -----------------------------------------------------------------------------
VALID_API_KEYS = {"my-very-secret-admin-api-key"}

def require_api_key(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key not in VALID_API_KEYS:
            return jsonify({'error': 'Unauthorized'}), 401
        return func(*args, **kwargs)
    return wrapper

# -----------------------------------------------------------------------------
# File validation class
# -----------------------------------------------------------------------------
class PDFValidator:
    MAX_SIZE = 50 * 1024 * 1024  # 50 MB
    MIN_SIZE = 128  # Accept very tiny PDFs for testing

    @staticmethod
    def validate_file(file):
        """Validates that the file is a valid PDF"""
        if not file or not file.filename:
            return False, "No file provided"
            
        if not file.filename.lower().endswith('.pdf'):
            return False, "Only PDF files are allowed"
            
        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > PDFValidator.MAX_SIZE:
            return False, f"File too large. Maximum size is {PDFValidator.MAX_SIZE / 1024 / 1024}MB"
            
        if size < PDFValidator.MIN_SIZE:
            return False, "File too small or possibly corrupted"
            
        # Check PDF header
        header = file.read(1024)
        file.seek(0)
        
        if not header.startswith(b'%PDF-'):
            return False, "Invalid PDF file format"
            
        return True, None

# -----------------------------------------------------------------------------
# Secure temp file path helper
# -----------------------------------------------------------------------------
def secure_file_handling(file):
    if not file.filename:
        raise ValueError("No filename provided.")
    safe_name = secure_filename(file.filename)
    if not safe_name:
        raise ValueError("Invalid filename.")
    ext = Path(safe_name).suffix.lower()
    unique_filename = f"{secrets.token_hex(16)}{ext}"
    temp_dir = Path("temp").resolve()
    temp_dir.mkdir(exist_ok=True)
    secure_path = temp_dir / unique_filename
    if not str(secure_path).startswith(str(temp_dir)):
        raise ValueError("Security violation: Path traversal detected.")
    return str(secure_path), unique_filename

# -----------------------------------------------------------------------------
# Custom application error for consistent JSON error results
# -----------------------------------------------------------------------------
class AppError(Exception):
    def __init__(self, message, status_code=500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

@app.errorhandler(AppError)
def handle_app_error(error):
    logger.error(f"AppError: {error.message}")
    return jsonify({'error': error.message}), error.status_code

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled Exception: {e}\n{traceback.format_exc()}")
    return jsonify({'error': 'Internal server error'}), 500

# -----------------------------------------------------------------------------
# Serve favicon.ico to avoid browser console 404s
# -----------------------------------------------------------------------------
@app.route('/favicon.ico')
def favicon():
    path = os.path.join(app.root_path, 'static')
    return send_from_directory(path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# -----------------------------------------------------------------------------
# Data Files Management
# -----------------------------------------------------------------------------
@app.route('/data-files-page')
def data_files():
    try:
        # Check if user is authenticated
        if 'user_token' not in session:
            return redirect(url_for('admin_login'))
        return render_template('data_files_new.html')
    except Exception as e:
        logger.error(f"Error rendering data files page: {e}")
        return jsonify({"error": "Failed to load data files page"}), 500

# -----------------------------------------------------------------------------
# View saved JSON files endpoint
# -----------------------------------------------------------------------------
@app.route('/data-files', methods=['GET'])
def list_data_files():
    try:
        data_dir = Path("data")
        if not data_dir.exists():
            return jsonify({"files": [], "message": "No data directory found"}), 200
            
        json_files = []
        for file_path in data_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_info = {
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                        "metadata": data.get("metadata", {}),
                        "firebase_status": data.get("firebase_status", {})
                    }
                    json_files.append(file_info)
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
        
        json_files.sort(key=lambda x: x["created"], reverse=True)
        return jsonify({"files": json_files}), 200
    except Exception as e:
        logger.error(f"Error listing data files: {e}")
        return jsonify({"error": "Failed to list data files"}), 500

@app.route('/data-files/<filename>', methods=['GET'])
def get_data_file(filename):
    try:
        file_path = Path("data") / filename
        if not file_path.exists() or not filename.endswith('.json'):
            return jsonify({"error": "File not found"}), 404
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error reading data file {filename}: {e}")
        return jsonify({"error": "Failed to read data file"}), 500

# -----------------------------------------------------------------------------
# Helper function to extract year and semester from semester string
# -----------------------------------------------------------------------------
def extract_year_sem_from_semester(semester_str):
    """
    Extract year and semester from semester string
    Examples:
    - "II B.Tech I Semester" -> year="2", sem="1"
    - "III B.Tech II Semester" -> year="3", sem="2"
    - "1-1" -> year="1", sem="1"
    - "2-2" -> year="2", sem="2"
    """
    try:
        semester_str = semester_str.strip().lower()
        
        # Handle format like "1-1", "2-2", etc.
        if '-' in semester_str and len(semester_str.split('-')) == 2:
            parts = semester_str.split('-')
            return parts[0], parts[1]
        
        # Handle format like "II B.Tech I Semester"
        # Roman numeral mapping
        roman_to_num = {
            'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5',
            'vi': '6', 'vii': '7', 'viii': '8', 'ix': '9', 'x': '10'
        }
        
        # Extract year (first roman numeral before "b.tech")
        year = "unknown"
        sem = "unknown"
        
        words = semester_str.split()
        for i, word in enumerate(words):
            if word in roman_to_num:
                if i + 1 < len(words) and words[i + 1] == 'b.tech':
                    year = roman_to_num[word]
                elif 'semester' in words and word in roman_to_num:
                    # This might be the semester part
                    if year != "unknown":  # We already found year
                        sem = roman_to_num[word]
                    else:
                        # If no year found yet, this might be year
                        year = roman_to_num[word]
        
        # If we found year but not semester, try to find semester
        if year != "unknown" and sem == "unknown":
            for word in words:
                if word in roman_to_num and roman_to_num[word] != year:
                    sem = roman_to_num[word]
                    break
        
        # Default values if parsing fails
        if year == "unknown":
            year = "1"
        if sem == "unknown":
            sem = "1"
            
        return year, sem
        
    except Exception as e:
        logger.warning(f"Failed to parse semester '{semester_str}': {e}")
        return "1", "1"  # Default fallback

# -----------------------------------------------------------------------------
# Student Results Query Functions
# -----------------------------------------------------------------------------
def get_student_results(student_id, semester=None, exam_type=None, format_type=None):
    """Get student results from JSON files"""
    results = []
    data_dir = Path("data")
    
    if not data_dir.exists():
        return {"error": None, "data": []}
        
    for json_file in data_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                file_format = data.get("metadata", {}).get("format", "").lower()
                file_exam_type = data.get("metadata", {}).get("exam_type", "").lower()
                
                # Filter by format and exam type if specified
                if (format_type and file_format != format_type.lower()) or \
                   (exam_type and file_exam_type != exam_type.lower()):
                    continue
                
                # Filter students by ID and semester
                for student in data.get("students", []):
                    if student.get("student_id") == student_id:
                        if not semester or student.get("semester") == semester:
                            # Add source file info
                            student["source_file"] = json_file.name
                            results.append(student)
        except Exception as e:
            logger.warning(f"Could not read {json_file}: {e}")
    
    return {"error": None, "data": results}

def get_all_students_by_semester(semester, exam_type=None, format_type=None):
    """Get all students for a specific semester from JSON files"""
    results = []
    data_dir = Path("data")
    
    if not data_dir.exists():
        return {"error": None, "data": []}
        
    for json_file in data_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                file_format = data.get("metadata", {}).get("format", "").lower()
                file_exam_type = data.get("metadata", {}).get("exam_type", "").lower()
                
                # Filter by format and exam type if specified
                if (format_type and file_format != format_type.lower()) or \
                   (exam_type and file_exam_type != exam_type.lower()):
                    continue
                
                # Filter students by semester
                for student in data.get("students", []):
                    if student.get("semester") == semester:
                        # Add source file info
                        student["source_file"] = json_file.name
                        results.append(student)
        except Exception as e:
            logger.warning(f"Could not read {json_file}: {e}")
    
    return {"error": None, "data": results}

# -----------------------------------------------------------------------------
# Student Results API Endpoints
# -----------------------------------------------------------------------------
@app.route('/students/<student_id>/results', methods=['GET'])
def get_student_results_api(student_id):
    """Get results for a specific student"""
    try:
        semester = request.args.get('semester')
        exam_type = request.args.get('exam_type')
        format_type = request.args.get('format')
        
        result = get_student_results(student_id, semester, exam_type, format_type)
        
        if result["error"]:
            return jsonify({"error": result["error"]}), 500
        
        return jsonify({
            "student_id": student_id,
            "results": result["data"],
            "count": len(result["data"])
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_student_results_api: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/results/semester/<semester>', methods=['GET'])
def get_semester_results_api(semester):
    """Get all students results for a specific semester"""
    try:
        exam_type = request.args.get('exam_type')
        format_type = request.args.get('format')
        
        result = get_all_students_by_semester(semester, exam_type, format_type)
        
        if result["error"]:
            return jsonify({"error": result["error"]}), 500
        
        return jsonify({
            "semester": semester,
            "results": result["data"],
            "count": len(result["data"])
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_semester_results_api: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/results/semesters', methods=['GET'])
def get_available_semesters():
    """Get list of available semesters from JSON files"""
    try:
        # Get unique semesters from all JSON files
        semesters = set()
        data_dir = Path("data")
        if not data_dir.exists():
            return jsonify({"semesters": [], "count": 0}), 200
            
        for json_file in data_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for student in data.get("students", []):
                        if "semester" in student:
                            semesters.add(student["semester"])
            except Exception as e:
                logger.warning(f"Could not read {json_file}: {e}")
        
        return jsonify({
            "semesters": sorted(list(semesters)),
            "count": len(semesters)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available semesters: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/debug/student/<student_id>', methods=['GET'])
def debug_student_data(student_id):
    """Debug endpoint to see raw student data structure"""
    try:
        results = []
        
        # Get data from Firebase
        if FIREBASE_AVAILABLE and db:
            try:
                docs = db.collection('student_results').where('student_id', '==', student_id).limit(5).stream()
                for doc in docs:
                    doc_data = doc.to_dict()
                    doc_data['source'] = 'firebase'
                    results.append(doc_data)
            except Exception as e:
                logger.warning(f"Firebase debug error: {e}")
        
        # Get data from JSON files
        json_results = get_student_results(student_id)
        if json_results and json_results.get('data'):
            for result in json_results['data'][:2]:  # Limit to 2 results
                result['source'] = 'json'
                results.append(result)
        
        return jsonify({
            "student_id": student_id,
            "debug_results": results,
            "count": len(results),
            "note": "This is a debug endpoint to examine data structure"
        }), 200
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------------------------
# Firebase-based Student Results API Endpoints
# -----------------------------------------------------------------------------
@app.route('/api/students/<student_id>/results', methods=['GET'])
def get_student_results_from_firebase(student_id):
    """Get results for a specific student from Firebase Firestore"""
    try:
        if not FIREBASE_AVAILABLE or not db:
            return jsonify({"error": "Firebase not available"}), 503
        
        # Get query parameters
        semester = request.args.get('semester')
        year = request.args.get('year')
        exam_type = request.args.get('exam_type')
        limit = int(request.args.get('limit', 50))  # Default limit to 50 results
        
        # Start with basic query
        query = db.collection('student_results').where('student_id', '==', student_id)
        
        # Add filters if provided
        if semester:
            query = query.where('semester', '==', semester)
        if year:
            query = query.where('year', '==', year)
        if exam_type:
            query = query.where('exam_type', '==', exam_type)
        
        # Execute query with limit
        docs = query.limit(limit).stream()
        
        results = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['document_id'] = doc.id
            results.append(doc_data)
        
        return jsonify({
            "student_id": student_id,
            "results": results,
            "count": len(results),
            "filters": {
                "semester": semester,
                "year": year,
                "exam_type": exam_type,
                "limit": limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching student results from Firebase: {e}")
        return jsonify({"error": f"Failed to fetch results: {str(e)}"}), 500

@app.route('/api/results/statistics', methods=['GET'])
def get_results_statistics():
    """Get overall statistics from Firebase Firestore"""
    try:
        if not FIREBASE_AVAILABLE or not db:
            return jsonify({"error": "Firebase not available"}), 503
        
        # Get query parameters
        semester = request.args.get('semester')
        year = request.args.get('year')
        exam_type = request.args.get('exam_type')
        
        # Start with the collection
        query = db.collection('student_results')
        
        # Add filters if provided
        if semester:
            query = query.where('semester', '==', semester)
        if year:
            query = query.where('year', '==', year)
        if exam_type:
            query = query.where('exam_type', '==', exam_type)
        
        # Get all documents (be careful with large datasets)
        docs = list(query.stream())
        
        if not docs:
            return jsonify({
                "statistics": {
                    "total_students": 0,
                    "average_sgpa": 0,
                    "pass_percentage": 0,
                    "grade_distribution": {},
                    "semester_distribution": {},
                    "year_distribution": {}
                }
            }), 200
        
        # Calculate statistics
        total_students = len(docs)
        sgpa_values = []
        passed_students = 0
        grade_counts = {}
        semester_counts = {}
        year_counts = {}
        
        for doc in docs:
            doc_data = doc.to_dict()
            
            # SGPA statistics
            sgpa = doc_data.get('sgpa', 0)
            if sgpa and sgpa > 0:
                sgpa_values.append(float(sgpa))
                if float(sgpa) >= 4.0:  # Assuming 4.0 is pass grade
                    passed_students += 1
            
            # Grade distribution
            for subject, grade in doc_data.get('subjects', {}).items():
                if isinstance(grade, str):
                    grade_counts[grade] = grade_counts.get(grade, 0) + 1
            
            # Semester distribution
            sem = doc_data.get('semester', 'Unknown')
            semester_counts[sem] = semester_counts.get(sem, 0) + 1
            
            # Year distribution
            yr = doc_data.get('year', 'Unknown')
            year_counts[yr] = year_counts.get(yr, 0) + 1
        
        # Calculate averages
        avg_sgpa = sum(sgpa_values) / len(sgpa_values) if sgpa_values else 0
        pass_percentage = (passed_students / total_students * 100) if total_students > 0 else 0
        
        return jsonify({
            "statistics": {
                "total_students": total_students,
                "average_sgpa": round(avg_sgpa, 2),
                "pass_percentage": round(pass_percentage, 2),
                "grade_distribution": grade_counts,
                "semester_distribution": semester_counts,
                "year_distribution": year_counts
            },
            "filters": {
                "semester": semester,
                "year": year,
                "exam_type": exam_type
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        return jsonify({"error": f"Statistics calculation failed: {str(e)}"}), 500

# -----------------------------------------------------------------------------
# PDF upload endpoint (no student_id required, all extracted by parser)
# -----------------------------------------------------------------------------
@app.route('/upload-pdf', methods=['POST'])
@require_api_key
def upload_pdf():
    file_path = None
    try:
        file = request.files.get('pdf')
        format_type = request.form.get('format')
        exam_type = request.form.get('exam_type')
        # Only require the fields you actually use:
        if not all([file, format_type, exam_type]):
            raise AppError("Missing required fields.", 400)
        if format_type.lower() not in ('jntuk', 'autonomous'):
            raise AppError("Invalid format type. Must be 'jntuk' or 'autonomous'.", 400)
        if exam_type.lower() not in ('regular', 'supply'):
            raise AppError("Invalid exam type. Must be 'regular' or 'supply'.", 400)
        valid, error_msg = PDFValidator.validate_file(file)
        if not valid:
            raise AppError(error_msg, 400)
        file_path, _ = secure_file_handling(file)
        file.save(file_path)
        # Parse all student results from the PDF using the selected parser:
        if format_type.lower() == 'autonomous':
            results = parse_autonomous_pdf(file_path)
        else:
            results = parse_jntuk_pdf(file_path)
        if not results:
            raise AppError("No valid student results found in PDF.", 400)
        
        # Save parsed data to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"parsed_results_{format_type}_{exam_type}_{timestamp}.json"
        json_filepath = os.path.join("data", json_filename)
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Generate unique document ID for Firebase
        doc_id = f"{format_type}_{exam_type}_{timestamp}"
        
        # Upload to Firebase
        firebase_start_time = time.time()
        students_saved = save_to_firebase(results, "Unknown", [exam_type], [exam_type], format_type, doc_id)
        firebase_time = time.time() - firebase_start_time
        
        # Upload PDF to Firebase Storage
        storage_url = None
        if file:
            file.seek(0)  # Reset file pointer
            storage_filename = f"pdfs/{format_type}_{exam_type}_{timestamp}_{file.filename}"
            storage_url = upload_pdf_to_storage(file, storage_filename)
        
        # Prepare data for JSON file with Firebase status
        json_data = {
            "metadata": {
                "format": format_type.lower(),
                "exam_type": exam_type.lower(),
                "processed_at": datetime.now().isoformat(),
                "total_students": len(results),
                "original_filename": file.filename
            },
            "students": results,
            "firebase_status": {
                "firebase_available": FIREBASE_AVAILABLE,
                "saved_count": students_saved,
                "failed_count": len(results) - students_saved if students_saved else len(results),
                "errors": [],
                "firebase_error": None,
                "status": "success" if students_saved > 0 else ("failed" if FIREBASE_AVAILABLE else "disabled"),
                "upload_time": firebase_time
            },
            "cloud_storage": {
                "uploaded": storage_url is not None,
                "url": storage_url or "",
                "filename": json_filename,
                "upload_completed_at": datetime.now().isoformat() if storage_url else ""
            }
        }
        
        # Save to JSON file
        with open(json_filepath, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved parsed data to {json_filepath}")
        logger.info(f"Firebase upload: {students_saved}/{len(results)} students saved")
        
        return jsonify({
            "message": f"Successfully processed {len(results)} result(s). Saved to JSON file.",
            "processed_count": len(results),
            "json_file": json_filename,
            "firebase": {
                "enabled": FIREBASE_AVAILABLE,
                "students_saved": students_saved,
                "students_total": len(results),
                "upload_time": firebase_time,
                "storage_url": storage_url
            }
        }), 200
    except AppError:
        raise
    except Exception as ex:
        logger.error(f"Upload processing error: {ex}\n{traceback.format_exc()}")
        raise AppError("Internal server error while processing upload.", 500)
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {file_path}: {e}")

# -----------------------------------------------------------------------------
# API endpoints for frontend compatibility
# -----------------------------------------------------------------------------
@app.route('/api/uploaded-results', methods=['GET'])
def api_uploaded_results():
    """API endpoint for getting uploaded results (frontend compatibility)"""
    return list_data_files()

@app.route('/api/upload-result', methods=['POST'])
def api_upload_result():
    """API endpoint for uploading results (frontend compatibility) - Async version"""
    try:
        file = request.files.get('pdf') or request.files.get('file')
        format_type = request.form.get('format') or request.form.get('resultType', 'jntuk')
        exam_type = request.form.get('exam_type') or request.form.get('examType', 'regular')
        
        if not all([file, format_type, exam_type]):
            return jsonify({"error": "Missing required fields", "required": ["file", "format", "exam_type"]}), 400
            
        if format_type.lower() not in ('jntuk', 'autonomous'):
            return jsonify({"error": "Invalid format type. Must be 'jntuk' or 'autonomous'"}), 400
            
        if exam_type.lower() not in ('regular', 'supply'):
            return jsonify({"error": "Invalid exam type. Must be 'regular' or 'supply'"}), 400
            
        valid, error_msg = PDFValidator.validate_file(file)
        if not valid:
            return jsonify({"error": error_msg}), 400
            
        # Generate upload ID immediately
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        upload_id = f"upload_{timestamp}"
        
        # Save file temporarily
        file_path, _ = secure_file_handling(file)
        file.save(file_path)
        
        # Initialize progress tracking
        update_progress(upload_id, "started", parsing={"status": "started", "message": "Upload started, processing PDF..."})
        
        # Start background processing using threading
        import threading
        thread = threading.Thread(target=process_upload_background, args=(file_path, format_type, exam_type, file.filename, upload_id))
        thread.daemon = True
        thread.start()
        
        # Return immediately with upload_id
        return jsonify({
            "success": True,
            "message": "Upload started successfully",
            "upload_id": upload_id,
            "status": "processing"
        }), 200
        
    except Exception as ex:
        logger.error(f"Upload start error: {ex}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error while starting upload"}), 500


def process_upload_background(file_path, format_type, exam_type, original_filename, upload_id):
    """Background processing function for file uploads using optimized batch processing"""
    try:
        # Use the new batch processing system
        update_progress(upload_id, "parsing", parsing={"status": "parsing", "message": "Starting optimized batch processing..."})
        
        # Use the optimized batch processor that includes PDF filename in documents
        if FIREBASE_AVAILABLE and db and bucket:
            # Use batch processing with Firebase
            result = process_single_pdf(file_path, db, bucket)
            
            # Extract results for progress tracking
            total_students = result.get('total_students', 0)
            firebase_saved = result.get('firebase_saved', 0)
            firebase_skipped = result.get('firebase_skipped', 0)
            json_filepath = result.get('json_filepath', '')
            
            # Update progress to completed
            update_progress(upload_id, "completed", 
                parsing={"status": "completed", "message": f"Processed {total_students} students"},
                firebase={"status": "completed", "saved": firebase_saved, "skipped": firebase_skipped},
                json={"status": "completed", "file": os.path.basename(json_filepath)}
            )
            
            # Store final result
            final_result = {
                "success": True,
                "message": f"Successfully processed {total_students} student(s) with PDF filename included",
                "processed_count": total_students,
                "json_file": os.path.basename(json_filepath),
                "file_id": os.path.basename(json_filepath).replace('.json', ''),
                "upload_id": upload_id,
                "firebase": {
                    "enabled": True,
                    "students_saved": firebase_saved,
                    "students_skipped": firebase_skipped,
                    "students_total": total_students
                },
                "data": {
                    "total_students": total_students,
                    "format": format_type.lower(),
                    "exam_type": exam_type.lower(),
                    "original_filename": original_filename,
                    "pdf_filename_included": True
                }
            }
        else:
            # Fallback to old system if Firebase not available
            update_progress(upload_id, "parsing", parsing={"status": "parsing", "message": "Extracting student data from PDF..."})
            
            if format_type.lower() == 'autonomous':
                results = parse_autonomous_pdf(file_path)
            else:
                results = parse_jntuk_pdf(file_path)
                
            if not results:
                update_progress(upload_id, "error", parsing={"status": "error", "message": "No valid student results found in PDF"})
                return
                
            # Add PDF filename to each student record manually
            for student in results:
                student['pdf_filename'] = original_filename
                student['source_document'] = original_filename
            
            # Save to JSON with PDF filename included
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"parsed_results_{format_type}_{exam_type}_{timestamp}.json"
            json_filepath = os.path.join("data", json_filename)
            
            os.makedirs("data", exist_ok=True)
            
            json_data = {
                "metadata": {
                    "format": format_type.lower(),
                    "exam_type": exam_type.lower(),
                    "processed_at": datetime.now().isoformat(),
                    "total_students": len(results),
                    "original_filename": original_filename,
                    "processing_status": "completed",
                    "upload_id": upload_id,
                    "pdf_filename_included": True
                },
                "students": results
            }
            
            with open(json_filepath, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, indent=2, ensure_ascii=False)
            
            update_progress(upload_id, "completed", 
                parsing={"status": "completed", "message": f"Processed {len(results)} students"},
                json={"status": "completed", "file": json_filename}
            )
            
            final_result = {
                "success": True,
                "message": f"Successfully processed {len(results)} student(s) with PDF filename included",
                "processed_count": len(results),
                "json_file": json_filename,
                "upload_id": upload_id,
                "firebase": {"enabled": False},
                "data": {
                    "total_students": len(results),
                    "format": format_type.lower(),
                    "exam_type": exam_type.lower(),
                    "original_filename": original_filename,
                    "pdf_filename_included": True
                }
            }
        
        # Store the final result in upload_progress for the frontend to access
        upload_progress[upload_id]["final_result"] = final_result
        
        logger.info(f"✅ Upload {upload_id} completed successfully with PDF filename included in documents")
        
    except Exception as ex:
        logger.error(f"Background processing error: {ex}\n{traceback.format_exc()}")
        update_progress(upload_id, "error", error={"status": "error", "message": f"Processing failed: {str(ex)}"})
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {file_path}: {e}")


# -----------------------------------------------------------------------------
# Run server if script is run directly
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    """
    Analyze students from JSON data files for placement eligibility
    """
    try:
        all_students = []
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        
        # Read all JSON files in data directory
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(data_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'students' in data:
                                for student in data['students']:
                                    # Calculate backlogs from subjectGrades
                                    backlogs = 0
                                    if 'subjectGrades' in student:
                                        for subject in student['subjectGrades']:
                                            grade = subject.get('grade', '').upper()
                                            # Count F grades as backlogs
                                            if grade == 'F':
                                                backlogs += 1
                                    
                                    # Extract branch from student ID
                                    student_id = student.get('student_id', '')
                                    branch = 'Unknown'
                                    branch_name = 'Unknown'
                                    
                                    # Pattern for autonomous: 24B81A0101 -> A01 (Computer Science)
                                    # Pattern for JNTUK: Similar patterns
                                    if len(student_id) >= 8:
                                        branch_code = student_id[6:8]  # Extract branch code
                                        if branch_code == 'A0':
                                            branch = 'A01'
                                            branch_name = 'Computer Science'
                                        elif branch_code == 'A1':
                                            branch = 'A01'
                                            branch_name = 'Computer Science'
                                        elif branch_code == 'A2':
                                            branch = 'A02'
                                            branch_name = 'Electrical'
                                        elif branch_code == 'A3':
                                            branch = 'A03'
                                            branch_name = 'Mechanical'
                                        elif branch_code == 'A4':
                                            branch = 'A04'
                                            branch_name = 'Civil'
                                        elif branch_code == 'A5':
                                            branch = 'A05'
                                            branch_name = 'Electronics'
                                        else:
                                            # Try other patterns
                                            if 'A01' in student_id:
                                                branch = 'A01'
                                                branch_name = 'Computer Science'
                                            elif 'A02' in student_id:
                                                branch = 'A02'
                                                branch_name = 'Electrical'
                                            elif 'A03' in student_id:
                                                branch = 'A03'
                                                branch_name = 'Mechanical'
                                            elif 'A04' in student_id:
                                                branch = 'A04'
                                                branch_name = 'Civil'
                                            elif 'A05' in student_id:
                                                branch = 'A05'
                                                branch_name = 'Electronics'
                                    
                                    # Get CGPA (use SGPA if CGPA not available)
                                    cgpa = student.get('cgpa', student.get('sgpa', 0.0))
                                    
                                    # Determine semesters completed (estimate from student ID)
                                    semesters_completed = 1  # Default
                                    if student_id.startswith('24'):
                                        semesters_completed = 1  # Current 1st year
                                    elif student_id.startswith('23'):
                                        semesters_completed = 3  # 2nd year
                                    elif student_id.startswith('22'):
                                        semesters_completed = 5  # 3rd year
                                    elif student_id.startswith('21'):
                                        semesters_completed = 7  # 4th year
                                    
                                    # Placement eligibility criteria
                                    # Standard criteria: CGPA >= 6.5 and backlogs <= 3
                                    eligible = cgpa >= 6.5 and backlogs <= 3
                                    
                                    # Training need assessment
                                    needs_training = cgpa < 7.0 or backlogs > 1
                                    
                                    student_analysis = {
                                        'student_id': student_id,
                                        'branch': branch,
                                        'branch_name': branch_name,
                                        'cgpa': round(cgpa, 2),
                                        'backlogs': backlogs,
                                        'semesters_completed': semesters_completed,
                                        'eligible': eligible,
                                        'needs_training': needs_training,
                                        'semester': student.get('semester', 'Unknown'),
                                        'university': student.get('university', 'Unknown'),
                                        'format': data.get('metadata', {}).get('format', 'unknown'),
                                        'exam_type': student.get('examType', 'regular')
                                    }
                                    
                                    all_students.append(student_analysis)
                                    
                    except Exception as e:
                        logger.warning(f"Error processing file {filename}: {e}")
                        continue
        
        # Sort students by CGPA (highest first)
        all_students.sort(key=lambda x: x['cgpa'], reverse=True)
        
        # Calculate statistics
        total_students = len(all_students)
        eligible_students = len([s for s in all_students if s['eligible']])
        avg_cgpa = round(sum(s['cgpa'] for s in all_students) / total_students, 2) if total_students > 0 else 0
        zero_backlogs = len([s for s in all_students if s['backlogs'] == 0])
        
        result = {
            'success': True,
            'students': all_students,
            'statistics': {
                'total_students': total_students,
                'eligible_students': eligible_students,
                'eligibility_percentage': round((eligible_students / total_students * 100), 1) if total_students > 0 else 0,
                'average_cgpa': avg_cgpa,
                'zero_backlogs': zero_backlogs,
                'zero_backlogs_percentage': round((zero_backlogs / total_students * 100), 1) if total_students > 0 else 0
            }
        }
        
        logger.info(f"Placement analysis completed: {total_students} students analyzed")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in placement analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'students': [],
            'statistics': {
                'total_students': 0,
                'eligible_students': 0,
                'eligibility_percentage': 0,
                'average_cgpa': 0,
                'zero_backlogs': 0,
                'zero_backlogs_percentage': 0
            }
        }), 500


# -----------------------------------------------------------------------------
# Run server if script is run directly
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


#Copyright (c) 2023 Nene