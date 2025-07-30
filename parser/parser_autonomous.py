import pdfplumber
import re
from datetime import datetime

def parse_autonomous_pdf(file_path):
    results = []
    
    with pdfplumber.open(file_path) as pdf:
        full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # → Extract subject codes
    # Sample match: 1) 24BS1003-Communicative English
    code_name_pattern = r'\d\)\s*(\w+)\s*-\s*(.+)'
    code_name_map = re.findall(code_name_pattern, full_text)

    # Build ordered list of subject codes and names
    subject_list = []
    seen = set()
    for code, name in code_name_map:
        if code not in seen:  # avoid duplicates from the bottom list
            subject_list.append((code.strip(), name.strip()))
            seen.add(code)

    num_subjects = len(subject_list)

    # → Match rows with student results: starts with H.T.No like 24B81A0501 followed by grades and SGPA
    row_pattern = re.compile(r'(?P<htno>24B81A\d{4,})\s+([A-FS\-]{1,3}\s+){' + str(num_subjects) + r'}(\d+\.\d{2}|0\.00)', re.MULTILINE)

    for match in row_pattern.finditer(full_text):
        line = match.group(0).strip()
        parts = line.split()
        if len(parts) >= num_subjects + 2:
            htno = parts[0]
            grades = parts[1:1+num_subjects]
            sgpa = parts[-1]

            subjects = []
            for i in range(num_subjects):
                subjects.append({
                    "code": subject_list[i][0],
                    "subject": subject_list[i][1],
                    "grade": grades[i]
                })

            student_result = {
                "student_id": htno,
                "semester": "1-1",
                "university": "Autonomous",
                "upload_date": datetime.now().strftime("%Y-%m-%d"),
                "sgpa": float(sgpa),
                "subjectGrades": subjects
            }

            results.append(student_result)

    return results
