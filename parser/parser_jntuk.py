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
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    # Match lines with pattern: Htno Subcode Subname Internals Grade Credits
    line_pattern = re.compile(
        r"(?P<htno>\d{2}[A-Z]{1,2}\d{4})\s+"
        r"(?P<subcode>[A-Z0-9]+)\s+"
        r"(?P<subname>.+?)\s{2,}(?P<internals>\d+|ABSENT)\s+"
        r"(?P<grade>[A-F][\+\-]?|AB|ABSENT|MP)\s+"
        r"(?P<credits>\d+(\.\d+)?|0)"
    )

    for match in line_pattern.finditer(full_text):
        data = match.groupdict()
        htno = data['htno']
        subcode = data['subcode']
        subname = data['subname'].strip()
        internals = 0 if data['internals'] == 'ABSENT' else int(data['internals'])
        grade = data['grade'].strip()
        credits = float(data['credits'])

        student = results[htno]
        student['student_id'] = htno
        student['university'] = "JNTUK"
        student['upload_date'] = datetime.now().strftime("%Y-%m-%d")
        student['semester'] = "I B.Tech II Semester"

        student['subjectGrades'].append({
            "code": subcode,
            "subject": subname,
            "internals": internals,
            "grade": grade,
            "credits": credits
        })

        student['totalCredits'] += credits

    return list(results.values())
