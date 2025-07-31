import pdfplumber
import re
from datetime import datetime

def parse_autonomous_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    # --- Dynamically extract subjects ---
    subject_code_map = re.findall(r'\d\)\s*([A-Z0-9]+)\s*-\s*(.+)', text)
    subject_list = []
    seen = set()
    for code, name in subject_code_map:
        if code not in seen:
            subject_list.append((code.strip(), name.strip()))
            seen.add(code)
    num_subjects = len(subject_list)
    # --- Flexible hallticket regex: (\d{2}B81A\w{3,4}) for all years ---
    row_pattern = re.compile(
        rf'(\d{{2}}B81A\w{{3,4}})\s+((?:[A-FS\-]{{1,3}}\s+){{{num_subjects}}})(\d+\.\d{{2}}|0\.00)',
        re.MULTILINE
    )
    results = []
    for match in row_pattern.finditer(text):
        student_id = match.group(1)
        grades = match.group(2).strip().split()
        sgpa = float(match.group(3))
        subjects = []
        for i in range(num_subjects):
            subjects.append({
                "code": subject_list[i][0],
                "subject": subject_list[i][1],
                "grade": grades[i]
            })
        results.append({
            "student_id": student_id,
            "semester": "1-1",
            "university": "Autonomous",
            "upload_date": datetime.now().strftime("%Y-%m-%d"),
            "sgpa": sgpa,
            "subjectGrades": subjects
        })
    return results
