from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, messaging
from parser.parser_jntuk import parse_jntuk_pdf
from parser.parser_autonomous import parse_autonomous_pdf
import os

app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# ✅ Root route
@app.route("/", methods=["GET"])
def index():
    return "✅ Flask server is running! Use /upload-pdf to upload results."

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    file = request.files['pdf']
    student_id = request.form.get('student_id')
    format_type = request.form.get('format')    # jntuk / autonomous
    exam_type = request.form.get('exam_type')   # regular / supply

    # Save temporarily
    file_path = os.path.join('temp', file.filename)
    os.makedirs('temp', exist_ok=True)
    file.save(file_path)

    # Parse based on input format
    if format_type == 'jntuk':
        result_json = parse_jntuk_pdf(file_path)
    else:
        result_json = parse_autonomous_pdf(file_path)

    result_json.update({
        'student_id': student_id,
        'exam_type': exam_type
    })

    # Save to Firestore
    db.collection('students').document(student_id).collection('results').add(result_json)

    # Send FCM Notification
    send_result_notification(student_id)

    os.remove(file_path)
    return jsonify({ 'message': 'Result uploaded and student notified.' })

def send_result_notification(student_id):
    doc_ref = db.collection('students').document(student_id)
    doc = doc_ref.get()
    if doc.exists:
        token = doc.to_dict().get('fcmToken')
        if token:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="New Result Posted",
                    body="A new result has been uploaded for you.",
                ),
                token=token
            )
            messaging.send(message)

if __name__ == '__main__':
    app.run(debug=True)
