import os
import secrets
import logging
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename

import firebase_admin
from firebase_admin import credentials, firestore
import magic  # Make sure you have python-magic-bin installed (on Windows)

# Import your PDF parsers here (you must define these yourself)
from parser.parser_jntuk import parse_jntuk_pdf
from parser.parser_autonomous import parse_autonomous_pdf

# -----------------------------------------------------------------------------
# Flask app and logging setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Initialize Firebase Admin SDK (use your service account JSON)
# -----------------------------------------------------------------------------
cred = credentials.Certificate('serviceAccount.json')  
firebase_admin.initialize_app(cred)
db = firestore.client()

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
class FileValidator:
    ALLOWED_EXTENSIONS = {'.pdf'}
    ALLOWED_MIME_TYPES = {'application/pdf'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MIN_FILE_SIZE = 128  # Accept very tiny PDFs, change to 1024 (1KB) for prod

    @staticmethod
    def validate_file(file):
        if not file or not file.filename:
            return False, "No file provided."
        ext = Path(file.filename).suffix.lower()
        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            return False, "Invalid file type. Only PDF allowed."
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > FileValidator.MAX_FILE_SIZE:
            return False, "File too large. Max size is 50MB."
        if size < FileValidator.MIN_FILE_SIZE:
            return False, "File too small or corrupt."
        header = file.read(1024)
        file.seek(0)
        mime_type = magic.from_buffer(header, mime=True)
        if mime_type not in FileValidator.ALLOWED_MIME_TYPES:
            return False, f"Invalid file content type: {mime_type}"
        if not header.startswith(b'%PDF-'):
            return False, "Invalid PDF file signature."
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
    def _init_(self, message, status_code=500):
        self.message = message
        self.status_code = status_code
        super()._init_(message)

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
# Main page serves upload form (rendered from templates/upload.html)
# -----------------------------------------------------------------------------
@app.route('/', methods=['GET'])
def health_check():
    return render_template('upload.html'), 200

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
        valid, error_msg = FileValidator.validate_file(file)
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
        # Save results under students/{student_id}/results/
        for student_result in results:
            sid = student_result.get('student_id')
            db.collection('students').document(sid).collection('results').add({
                **student_result,
                "exam_type": exam_type.lower(),
                "format": format_type.lower(),
                "processed_at": firestore.SERVER_TIMESTAMP,
            })
        return jsonify({
            "message": f"Successfully processed {len(results)} result(s).",
            "processed_count": len(results)
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
# Run server if script is run directly
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


#Copyright (c) 2023 Nene