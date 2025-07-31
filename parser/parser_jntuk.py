import pdfplumber
import re
from datetime import datetime
from collections import defaultdict

def parse_jntuk_pdf(file_path):
    results = defaultdict(lambda: {
        "subjectGrades": [],
        "totalCredits": 0
    })

    with pdfplumber.open(file_path) as pdf:
        full_text = "\n".join(
            page.extract_text() for page in pdf.pages if page.extract_text()
        )

    # Match lines like: Htno Subcode Subname Internals Grade Credits
    line_pattern = re.compile(
        r"(?P<htno>\d{2}[A-Z0-9]{6})\s+"                       # 17B81A0106
        r"(?P<subcode>[A-Z0-9]+)\s+"                           # R161202
        r"(?P<subname>.+?)\s{2,}(?P<internals>\d+|ABSENT)\s+"  # MATHS-II  10
        r"(?P<grade>[A-F][\+\-]?|MP|ABSENT)\s+"                # D, F, MP
        r"(?P<credits>\d+(?:\.\d+)?|0)",                       # 3 or 3.0
        re.MULTILINE
    )

    for match in line_pattern.finditer(full_text):
        data = match.groupdict()
        htno = data['htno']
        subcode = data['subcode']
        subname = data['subname'].strip()
        internals = 0 if data['internals'] == 'ABSENT' else int(data['internals'])
        grade = data['grade']
        credits = float(data['credits'])

        student = results[htno]
        student['student_id'] = htno
        student['university'] = "JNTUK"
        student['semester'] = "I B.Tech II Semester"
        student['upload_date'] = datetime.now().strftime("%Y-%m-%d")

        student['subjectGrades'].append({
            "code": subcode,
            "subject": subname,
            "internals": internals,
            "grade": grade,
            "credits": credits
        })

        student['totalCredits'] += credits

    return list(results.values())
