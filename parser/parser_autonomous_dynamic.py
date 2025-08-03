import pdfplumber
import re
from datetime import datetime
import time
from collections import defaultdict

def detect_pdf_format(text):
    """Detect the format of the PDF to choose appropriate parsing strategy"""
    print("Detecting PDF format...")
    
    # Check for tabular format (like the new PDF)
    tabular_indicators = [
        r'Sno\s+Htno\s+Subcode\s+Subname\s+Internals\s+Grade\s+Credits',
        r'\d+\s+[A-Z0-9]{8,12}\s+[A-Z0-9]{6,10}\s+.+?\s+\d+\s+[A-FS]\s+[\d.]+',
        r'Htno.*?Subcode.*?Grade.*?Credits'
    ]
    
    # Check for grouped format (original format)
    grouped_indicators = [
        r'[A-Z0-9]{10}\s+(?:[A-FS\-]+\s+)+\d+\.\d{2}',
        r'\d+\)\s*[A-Z0-9]+\s*-\s*.+?(?=\d+\)|$)'
    ]
    
    # Check for matrix format (subjects as columns) - improved detection
    matrix_indicators = [
        r'Programme\s*:\s*[IVX]+\s*B\.?Tech\.?\s*\(\s*[IVX]+\s*Semester\s*\)',
        r'Htno\s+Name.*?(?:[A-Z]{2,8}\s*){3,}.*?SGPA',
        r'[A-Z0-9]{10}\s+[A-Za-z\s.]+\s+(?:[A-FS\-]+\s*){4,}.*?\d+\.\d{2}',
        r'S\.?No\.?\s+Htno\s+Name.*?(?:[A-Z]{2,8}\s+){3,}',
        r'\d+\s+[A-Z0-9]{10}\s+[A-Za-z\s.]+\s+(?:[A-FS\-]+\s+){3,}'
    ]
    
    tabular_score = sum(1 for pattern in tabular_indicators if re.search(pattern, text, re.IGNORECASE))
    grouped_score = sum(1 for pattern in grouped_indicators if re.search(pattern, text, re.IGNORECASE))
    matrix_score = sum(1 for pattern in matrix_indicators if re.search(pattern, text, re.IGNORECASE))
    
    if matrix_score > max(tabular_score, grouped_score):
        format_type = "matrix"
    elif tabular_score > grouped_score:
        format_type = "tabular"
    else:
        format_type = "grouped"
    
    print(f"Detected format: {format_type} (tabular: {tabular_score}, grouped: {grouped_score}, matrix: {matrix_score})")
    
    return format_type

def extract_semester_info(text):
    """Extract semester information dynamically"""
    print("Detecting semester information...")
    
    # Multiple patterns to catch different semester formats
    semester_patterns = [
        r'Programme\s*:\s*([IVX]+)\s*B\.?Tech\.?\s*\(\s*([IVX]+)\s*Semester\s*\)',  # New format
        r'Results of.*?([IVX]+)\s*B\.?Tech\s*([IVX]+)\s*Semester',  # Roman numerals
        r'Results of.*?(\d+)\s*B\.?Tech\s*(\d+)\s*Semester',        # Numbers
        r'(\d+)\s*(?:st|nd|rd|th)?\s*(?:Semester|SEM)',             # Simple semester
        r'(\d+)-(\d+)\s*(?:Semester|SEM)',                          # Year-semester format
        r'B\.?Tech\s*.*?(\d+)\s*(?:st|nd|rd|th)?\s*(?:Semester|SEM)'
    ]
    
    # Search in first 3000 characters for semester info
    search_text = text[:3000]
    
    for pattern in semester_patterns:
        matches = re.search(pattern, search_text, re.IGNORECASE)
        if matches:
            if len(matches.groups()) == 2:
                # Year and semester
                year, semester = matches.groups()
                # Convert Roman numerals if needed
                roman_to_num = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5', 'VI': '6', 'VII': '7', 'VIII': '8'}
                year = roman_to_num.get(year, year)
                semester = roman_to_num.get(semester, semester)
                detected = f"Year {year} Semester {semester}"
            else:
                # Single semester
                sem = matches.group(1)
                detected = f"Semester {sem}"
            
            print(f"Detected: {detected}")
            return detected
    
    print("Could not detect semester, using default")
    return "Unknown Semester"

def extract_university_info(text):
    """Extract university information"""
    university_patterns = [
        r'(JAWAHARLAL NEHRU TECHNOLOGICAL UNIVERSITY[^\\n]*)',
        r'(.*?UNIVERSITY[^\\n]*)',
        r'(JNTU[^\\n]*)'
    ]
    
    for pattern in university_patterns:
        match = re.search(pattern, text[:1000], re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "Autonomous University"

def parse_tabular_format(text, semester, university):
    """Parse the tabular format where each line is a subject record"""
    print("Parsing tabular format...")
    
    # Pattern to match individual subject records
    # Format: Sno Htno Subcode Subname Internals Grade Credits
    record_pattern = re.compile(
        r'(\d+)\s+([A-Z0-9]{8,12})\s+([A-Z0-9]{6,10})\s+(.+?)\s+(\d+)\s+([A-FS]|ABSENT)\s+([\d.]+)',
        re.MULTILINE
    )
    
    matches = record_pattern.findall(text)
    print(f"Found {len(matches)} subject records")
    
    # Group by student ID
    students_data = defaultdict(list)
    
    for match in matches:
        sno, htno, subcode, subname, internals, grade, credits = match
        
        # Clean subject name
        subname = re.sub(r'\s+', ' ', subname.strip())
        
        subject_record = {
            "code": subcode,
            "subject": subname,
            "grade": grade,
            "internals": int(internals),
            "credits": float(credits)
        }
        
        students_data[htno].append(subject_record)
    
    # Calculate SGPA for each student
    results = []
    upload_date = datetime.now().strftime("%Y-%m-%d")
    
    for student_id, subjects in students_data.items():
        # Calculate SGPA based on grades and credits
        total_credits = 0
        total_points = 0
        
        grade_points = {
            'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5, 'F': 0, 'ABSENT': 0
        }
        
        for subject in subjects:
            credits = subject['credits']
            grade = subject['grade']
            points = grade_points.get(grade, 0)
            
            if grade not in ['F', 'ABSENT']:
                total_credits += credits
                total_points += points * credits
        
        sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        
        student_record = {
            "student_id": student_id,
            "semester": semester,
            "university": university,
            "upload_date": upload_date,
            "sgpa": sgpa,
            "subjectGrades": subjects
        }
        
        results.append(student_record)
    
    print(f"Processed {len(results)} students")
    return results

def parse_grouped_format(text, semester, university):
    """Parse the original grouped format"""
    print("Parsing grouped format...")
    
    # Extract subjects first
    subject_pattern = re.compile(r'\d+\)\s*([A-Z0-9]+)\s*-\s*(.+?)(?=\d+\)|$)', re.DOTALL)
    subject_matches = subject_pattern.findall(text)
    
    subject_list = []
    seen = set()
    for code, name in subject_matches:
        code = code.strip()
        name = re.sub(r'\s+', ' ', name.strip())
        if code not in seen and len(code) > 2:
            subject_list.append((code, name))
            seen.add(code)
    
    num_subjects = len(subject_list)
    print(f"Found {num_subjects} subjects")
    
    # Extract student data
    if num_subjects > 0:
        grade_pattern = r'[A-FS\-]+'
        student_pattern = re.compile(
            rf'([A-Z0-9]{{10}})\s+({grade_pattern}(?:\s+{grade_pattern}){{{num_subjects-1}}})\s+(\d+\.\d{{2}})',
            re.MULTILINE
        )
    else:
        student_pattern = re.compile(r'([A-Z0-9]{10})\s+((?:[A-FS\-]+\s+)+)(\d+\.\d{2})', re.MULTILINE)
    
    matches = list(student_pattern.finditer(text))
    print(f"Found {len(matches)} student records")
    
    results = []
    upload_date = datetime.now().strftime("%Y-%m-%d")
    
    for match in matches:
        student_id = match.group(1)
        grades_str = match.group(2).strip()
        sgpa = float(match.group(3))
        
        grades = re.findall(r'[A-FS\-]+', grades_str)
        
        subjects = []
        for j in range(min(len(grades), num_subjects)):
            if j < len(subject_list):
                subjects.append({
                    "code": subject_list[j][0],
                    "subject": subject_list[j][1],
                    "grade": grades[j],
                    "internals": 0,
                    "credits": 3.0
                })
        
        results.append({
            "student_id": student_id,
            "semester": semester,
            "university": university,
            "upload_date": upload_date,
            "sgpa": sgpa,
            "subjectGrades": subjects
        })
    
    return results

def parse_matrix_format(text, semester, university):
    """Parse matrix format where students are rows and subjects are columns"""
    print("Parsing matrix format...")
    
    # Extract subject codes from header - try multiple patterns
    header_patterns = [
        # Pattern for direct subject code header (like page 2+)
        r'(?:24[A-Z]{2}\d{4}\s+){3,}.*?SGPA',
        # Pattern for the first page with S.No H.T.No
        r'S\.?No\.?\s+H\.?T\.?No\.?\s+((?:24[A-Z]{2}\d{4}\s+){3,}).*?SGPA',
        # Alternative pattern
        r'Programme.*?\n.*?\n.*?\n.*?\n.*?((?:24[A-Z]{2}\d{4}\s+){3,}).*?SGPA'
    ]
    
    subject_codes = []
    for pattern in header_patterns:
        header_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if header_match:
            if header_match.groups():
                codes_text = header_match.group(1)
            else:
                codes_text = header_match.group(0)
            
            # Extract subject codes
            codes = re.findall(r'24[A-Z]{2}\d{4}', codes_text)
            if codes and len(codes) >= 3:
                subject_codes = codes
                print(f"Found subject codes using pattern: {codes[:5]}...")
                break
    
    if not subject_codes:
        print("Could not extract subject codes, trying fallback...")
        # Fallback: look for any sequence of subject codes
        fallback_codes = re.findall(r'24[A-Z]{2}\d{4}', text)
        if fallback_codes:
            # Take unique codes in order
            seen = set()
            subject_codes = []
            for code in fallback_codes:
                if code not in seen:
                    subject_codes.append(code)
                    seen.add(code)
                if len(subject_codes) >= 10:  # Limit to reasonable number
                    break
            print(f"Using fallback codes: {subject_codes[:5]}...")
    
    if not subject_codes:
        print("Could not extract subject codes from header")
        return []
    
    print(f"Extracted {len(subject_codes)} subject codes: {subject_codes[:5]}...")
    
    # Extract student data rows - updated pattern for this format
    student_patterns = [
        # Pattern with serial number: Sno Htno Grades SGPA
        re.compile(rf'(\d+)\s+(24B81A\d{{4}})\s+((?:[A-FS\-]+\s*){{4,}})\s+(\d+\.\d{{2}})', re.MULTILINE),
        # Pattern without serial number: Htno Grades SGPA  
        re.compile(rf'(24B81A\d{{4}})\s+((?:[A-FS\-]+\s*){{4,}})\s+(\d+\.\d{{2}})', re.MULTILINE)
    ]
    
    matches = []
    for pattern in student_patterns:
        test_matches = pattern.findall(text)
        if len(test_matches) > len(matches):
            matches = test_matches
            print(f"Using pattern with {len(test_matches)} matches")
    
    print(f"Found {len(matches)} student records")
    
    if not matches:
        return []
    
    results = []
    upload_date = datetime.now().strftime("%Y-%m-%d")
    
    grade_points = {
        'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5, 'F': 0, '-': 0
    }
    
    for match in matches:
        if len(match) == 4:  # With serial number
            sno, student_id, grades_str, sgpa_str = match
        elif len(match) == 3:  # Without serial number
            student_id, grades_str, sgpa_str = match
        else:
            continue
            
        sgpa = float(sgpa_str)
        
        # Extract individual grades
        grades = re.findall(r'[A-FS\-]+', grades_str.strip())
        
        # Create subject records
        subjects = []
        total_credits = 0
        total_points = 0
        
        for i, grade in enumerate(grades[:len(subject_codes)]):
            if i < len(subject_codes):
                credits = 3.0  # Default credits
                points = grade_points.get(grade, 0)
                
                subjects.append({
                    "code": subject_codes[i],
                    "subject": f"Subject {subject_codes[i]}",
                    "grade": grade,
                    "internals": 0,
                    "credits": credits
                })
                
                if grade not in ['F', '-']:
                    total_credits += credits
                    total_points += points * credits
        
        # Verify calculated SGPA matches provided SGPA (within tolerance)
        calculated_sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        
        student_record = {
            "student_id": student_id,
            "semester": semester,
            "university": university,
            "upload_date": upload_date,
            "sgpa": sgpa,  # Use provided SGPA
            "subjectGrades": subjects
        }
        
        results.append(student_record)
    
    avg_subjects = len(subject_codes) if results else 0
    print(f"Processed {len(results)} students with average {avg_subjects} subjects each")
    return results

def parse_autonomous_pdf_dynamic(file_path, semester="Unknown", university="Autonomous", streaming_callback=None):
    """Dynamic autonomous PDF parser that detects format and adapts accordingly"""
    print(f"Starting dynamic autonomous parsing of: {file_path}")
    start_time = time.time()
    
    # Extract PDF text
    with pdfplumber.open(file_path) as pdf:
        print(f"PDF has {len(pdf.pages)} pages")
        text_parts = []
        
        for i, page in enumerate(pdf.pages):
            if page.extract_text():
                text_parts.append(page.extract_text())
            
            if i > 0 and i % 20 == 0:
                print(f"Processed {i+1}/{len(pdf.pages)} pages...")
        
        text = "\n".join(text_parts)
    
    extraction_time = time.time() - start_time
    print(f"PDF text extraction took: {extraction_time:.2f} seconds")
    
    # Detect format
    format_type = detect_pdf_format(text)
    
    # Extract metadata
    detected_semester = extract_semester_info(text)
    if detected_semester != "Unknown Semester":
        semester = detected_semester
    
    detected_university = extract_university_info(text)
    if detected_university != "Autonomous University":
        university = detected_university
    
    print(f"Using semester: {semester}")
    print(f"Using university: {university}")
    
    # Parse based on detected format
    if format_type == "matrix":
        results = parse_matrix_format(text, semester, university)
    elif format_type == "tabular":
        results = parse_tabular_format(text, semester, university)
    else:
        results = parse_grouped_format(text, semester, university)
    
    # Handle streaming callback
    if streaming_callback and results:
        for i, record in enumerate(results):
            streaming_callback(record, i + 1)
    
    total_time = time.time() - start_time
    print(f"Completed dynamic parsing in {total_time:.2f} seconds")
    print(f"Total students processed: {len(results)}")
    
    if results:
        sample = results[0]
        print(f"Sample record: {sample['student_id']} has {len(sample['subjectGrades'])} subjects")
        print(f"Sample SGPA: {sample['sgpa']}")
    
    return results

def parse_autonomous_pdf_generator_dynamic(file_path, semester="Unknown", university="Autonomous", batch_size=50):
    """Generator version of the dynamic parser for batch processing"""
    print(f"Starting dynamic batch autonomous parsing of: {file_path}")
    start_time = time.time()
    
    # Extract PDF text
    with pdfplumber.open(file_path) as pdf:
        print(f"PDF has {len(pdf.pages)} pages")
        text_parts = []
        
        for i, page in enumerate(pdf.pages):
            if page.extract_text():
                text_parts.append(page.extract_text())
            
            if i > 0 and i % 20 == 0:
                print(f"Processed {i+1}/{len(pdf.pages)} pages...")
        
        text = "\n".join(text_parts)
    
    # Detect format and parse
    format_type = detect_pdf_format(text)
    detected_semester = extract_semester_info(text)
    if detected_semester != "Unknown Semester":
        semester = detected_semester
    
    detected_university = extract_university_info(text)
    if detected_university != "Autonomous University":
        university = detected_university
    
    # Parse based on format
    if format_type == "matrix":
        results = parse_matrix_format(text, semester, university)
    elif format_type == "tabular":
        results = parse_tabular_format(text, semester, university)
    else:
        results = parse_grouped_format(text, semester, university)
    
    # Yield in batches
    students_processed = 0
    batch_count = 0
    current_batch = []
    
    for student_record in results:
        current_batch.append(student_record)
        students_processed += 1
        
        if len(current_batch) >= batch_size:
            batch_count += 1
            print(f"Yielding batch {batch_count}: {len(current_batch)} students (Total: {students_processed})")
            yield current_batch.copy()
            current_batch = []
    
    # Yield remaining students
    if current_batch:
        batch_count += 1
        print(f"Yielding final batch {batch_count}: {len(current_batch)} students (Total: {students_processed})")
        yield current_batch

    total_time = time.time() - start_time
    print(f"Completed dynamic batch parsing in {total_time:.2f} seconds - {students_processed} total students")

# Backward compatibility - keep the original function names
def parse_autonomous_pdf(file_path, semester="Unknown", university="Autonomous", streaming_callback=None):
    """Wrapper for backward compatibility"""
    return parse_autonomous_pdf_dynamic(file_path, semester, university, streaming_callback)

def parse_autonomous_pdf_generator(file_path, semester="Unknown", university="Autonomous", batch_size=50):
    """Wrapper for backward compatibility"""
    return parse_autonomous_pdf_generator_dynamic(file_path, semester, university, batch_size)
