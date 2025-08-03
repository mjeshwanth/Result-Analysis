# Import the dynamic parser functions
from .parser_autonomous_dynamic import (
    parse_autonomous_pdf_dynamic,
    parse_autonomous_pdf_generator_dynamic
)

# Main exports for backward compatibility
def parse_autonomous_pdf(file_path, semester="Unknown", university="Autonomous", streaming_callback=None):
    """Main autonomous PDF parser - now uses dynamic detection"""
    return parse_autonomous_pdf_dynamic(file_path, semester, university, streaming_callback)

def parse_autonomous_pdf_generator(file_path, semester="Unknown", university="Autonomous", batch_size=50):
    """Generator version for batch processing"""
    return parse_autonomous_pdf_generator_dynamic(file_path, semester, university, batch_size)
    """Detect the format of the PDF to choose appropriate parsing strategy"""
    print("Detecting PDF format...")
    
    # Check for matrix format (subjects as columns, students as rows)
    matrix_indicators = [
        r'S\.?No\.?\s+H\.?T\.?No\.?\s+[A-Z0-9]{6,10}\s+[A-Z0-9]{6,10}.*?SGPA',
        r'\d+\s+[A-Z0-9]{8,15}\s+[A-FS]\s+[A-FS]\s+[A-FS].*?\d+\.\d{2}',
        r'Course\s+code.*?Name.*?Course\s+code.*?Name',
        r'Programme\s*:\s*.*?B\.?Tech.*?Semester'
    ]
    
    # Check for tabular format (individual subject records per line)
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
    
    matrix_score = sum(1 for pattern in matrix_indicators if re.search(pattern, text, re.IGNORECASE))
    tabular_score = sum(1 for pattern in tabular_indicators if re.search(pattern, text, re.IGNORECASE))
    grouped_score = sum(1 for pattern in grouped_indicators if re.search(pattern, text, re.IGNORECASE))
    
    # Determine format based on highest score
    scores = [
        (matrix_score, "matrix"),
        (tabular_score, "tabular"), 
        (grouped_score, "grouped")
    ]
    scores.sort(reverse=True)
    format_type = scores[0][1]
    
    print(f"Detected format: {format_type} (matrix: {matrix_score}, tabular: {tabular_score}, grouped: {grouped_score})")
    
    return format_type

def extract_semester_info(text):
    """Extract semester information dynamically"""
    print("Detecting semester information...")
    
    # Multiple patterns to catch different semester formats
    semester_patterns = [
        r'Programme\s*:\s*([IVX]+)\s*B\.?Tech\.?\s*\(\s*([IVX]+)\s*Semester\s*\)',  # Programme format
        r'Results of.*?([IVX]+)\s*B\.?Tech\s*([IVX]+)\s*Semester',  # Roman numerals
        r'Results of.*?(\d+)\s*B\.?Tech\s*(\d+)\s*Semester',        # Numbers
        r'(\d+)\s*(?:st|nd|rd|th)?\s*(?:Semester|SEM)',             # Simple semester
        r'(\d+)-(\d+)\s*(?:Semester|SEM)',                          # Year-semester format
        r'B\.?Tech\s*.*?(\d+)\s*(?:st|nd|rd|th)?\s*(?:Semester|SEM)',
        r'(\d+)\s*(?:st|nd|rd|th)?\s*B\.?Tech.*?(\d+)\s*(?:st|nd|rd|th)?\s*Semester',
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
                roman_to_num = {'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5', 'VI': '6', 'VII': '7', 'VIII': '8'}
                sem = roman_to_num.get(sem, sem)
                detected = f"Semester {sem}"
            
            print(f"Detected: {detected}")
            return detected
    
    print("Could not detect semester, using default")
    return "Unknown Semester"

def extract_university_info(text):
    """Extract university information dynamically"""
    university_patterns = [
        r'(JAWAHARLAL NEHRU TECHNOLOGICAL UNIVERSITY[^\\n]*)',
        r'(.*?TECHNOLOGICAL UNIVERSITY[^\\n]*)',
        r'(.*?UNIVERSITY[^\\n]*)',
        r'(JNTU[^\\n]*)',
        r'(.*?COLLEGE[^\\n]*)',
        r'(.*?INSTITUTE[^\\n]*)'
    ]
    
    # Search in first 1000 characters for university info
    search_text = text[:1000]
    
    for pattern in university_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            university_name = match.group(1).strip()
            # Clean up common formatting issues
            university_name = re.sub(r'\s+', ' ', university_name)
            university_name = university_name.replace('\\n', ' ').strip()
            if len(university_name) > 10:  # Valid university name
                return university_name
    
    return "Autonomous University"

def parse_tabular_format(text, semester, university):
    """Parse the tabular format where each line is a subject record"""
    print("Parsing tabular format...")
    
    # Dynamic pattern to match individual subject records
    # First, detect the column structure
    header_patterns = [
        r'Sno\s+Htno\s+Subcode\s+Subname\s+Internals\s+Grade\s+Credits',
        r'S\.?No\.?\s+Roll\.?No\.?\s+Subject\.?Code\s+Subject\.?Name\s+Internals?\s+Grade\s+Credits?',
        r'(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)'
    ]
    
    # Find the header to understand the structure
    header_found = False
    for pattern in header_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            header_found = True
            break
    
    if header_found:
        # Standard tabular format
        record_pattern = re.compile(
            r'(\d+)\s+([A-Z0-9]{8,12})\s+([A-Z0-9]{4,10})\s+(.+?)\s+(\d+)\s+([A-FS]|ABSENT|[A-Z\-]+)\s+([\d.]+)',
            re.MULTILINE
        )
    else:
        # Fallback pattern for different formats
        record_pattern = re.compile(
            r'(\d+)\s+([A-Z0-9]{8,15})\s+([A-Z0-9]{4,12})\s+(.+?)\s+(\d+)\s+([A-FS]|ABSENT|[A-Z\-]+)\s+([\d.]+)',
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
        
        # Handle different credit formats
        try:
            credits_val = float(credits)
        except ValueError:
            credits_val = 3.0  # Default fallback
        
        # Handle different internal marks formats
        try:
            internals_val = int(internals)
        except ValueError:
            internals_val = 0
        
        subject_record = {
            "code": subcode,
            "subject": subname,
            "grade": grade,
            "internals": internals_val,
            "credits": credits_val
        }
        
        students_data[htno].append(subject_record)
    
    # Calculate SGPA for each student dynamically
    results = []
    upload_date = datetime.now().strftime("%Y-%m-%d")
    
    # Dynamic grade point mapping - can be extended
    grade_points = {
        'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5, 'F': 0, 
        'ABSENT': 0, 'AB': 0, 'MP': 0, '-': 0
    }
    
    for student_id, subjects in students_data.items():
        # Calculate SGPA based on grades and credits
        total_credits = 0
        total_points = 0
        
        for subject in subjects:
            credits = subject['credits']
            grade = subject['grade'].upper()
            points = grade_points.get(grade, 0)
            
            if grade not in ['F', 'ABSENT', 'AB', 'MP', '-']:
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
    """Parse matrix format where subjects are columns and students are rows"""
    print("Parsing matrix format...")
    
    # Extract subject codes from the header
    # Look for patterns like "24BS1003 24BS1107 24BS1101 ... SGPA"
    subject_header_patterns = [
        r'H\.?T\.?No\.?\s+((?:[A-Z0-9]{6,10}\s+)+)SGPA',
        r'S\.?No\.?\s+H\.?T\.?No\.?\s+((?:[A-Z0-9]{6,10}\s+)+)SGPA',
    ]
    
    subject_codes = []
    for pattern in subject_header_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            codes_str = match.group(1).strip()
            subject_codes = re.findall(r'[A-Z0-9]{6,10}', codes_str)
            break
    
    if not subject_codes:
        print("Could not find subject codes in header, trying alternative method...")
        # Look for subject definitions like "1) 24BS1003-Communicative English"
        subject_def_pattern = r'\d+\)\s*([A-Z0-9]{6,10})-(.+?)(?=\d+\)|$)'
        subject_matches = re.findall(subject_def_pattern, text, re.IGNORECASE)
        subject_codes = [match[0] for match in subject_matches]
        subject_names = {match[0]: match[1].strip() for match in subject_matches}
    else:
        # If we found codes in header, try to find names separately
        subject_names = {}
        subject_def_pattern = r'\d+\)\s*([A-Z0-9]{6,10})-(.+?)(?=\d+\)|$)'
        subject_matches = re.findall(subject_def_pattern, text, re.IGNORECASE)
        subject_names = {match[0]: match[1].strip() for match in subject_matches}
    
    print(f"Found {len(subject_codes)} subjects: {subject_codes[:5]}...")
    
    # Extract student records in matrix format
    # Pattern: S.No H.T.No Grade1 Grade2 Grade3 ... SGPA
    # Example: 1 24B81A0101 D E C D D S S A S A 7.03
    
    # Build dynamic pattern based on number of subjects
    num_subjects = len(subject_codes)
    if num_subjects > 0:
        grade_pattern = r'[A-FS]+'
        student_pattern = re.compile(
            rf'(\d+)\s+([A-Z0-9]{{8,15}})\s+({grade_pattern}(?:\s+{grade_pattern}){{{num_subjects-1}}})\s+(\d+\.\d{{2}})',
            re.MULTILINE
        )
    else:
        # Fallback pattern if we can't determine exact number of subjects
        student_pattern = re.compile(
            r'(\d+)\s+([A-Z0-9]{8,15})\s+((?:[A-FS]+\s+)+)(\d+\.\d{2})',
            re.MULTILINE
        )
    
    matches = student_pattern.findall(text)
    print(f"Found {len(matches)} student records")
    
    results = []
    upload_date = datetime.now().strftime("%Y-%m-%d")
    
    # Default credit mapping for common subject types
    default_credits = {
        'theory': 3.0,
        'lab': 1.5,
        'project': 2.0,
        'seminar': 1.0
    }
    
    # Grade points mapping
    grade_points = {
        'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5, 'F': 0, 
        'ABSENT': 0, 'AB': 0, 'MP': 0, '-': 0
    }
    
    for match in matches:
        sno, student_id, grades_str, sgpa = match
        sgpa = float(sgpa)
        
        # Extract individual grades
        grades = re.findall(r'[A-FS]+', grades_str)
        
        # Build subject list for this student
        subjects = []
        for i, grade in enumerate(grades[:len(subject_codes)]):
            if i < len(subject_codes):
                subject_code = subject_codes[i]
                subject_name = subject_names.get(subject_code, f"Subject {i+1}")
                
                # Determine credits based on subject code pattern
                credits = 3.0  # Default
                if 'lab' in subject_name.lower() or subject_code.endswith(('1', '8')):
                    credits = 1.5
                elif 'project' in subject_name.lower():
                    credits = 2.0
                elif 'seminar' in subject_name.lower():
                    credits = 1.0
                
                subjects.append({
                    "code": subject_code,
                    "subject": subject_name,
                    "grade": grade,
                    "internals": 0,  # Not available in this format
                    "credits": credits
                })
        
        # Verify SGPA calculation if needed (optional)
        calculated_sgpa = 0.0
        if subjects:
            total_credits = 0
            total_points = 0
            
            for subject in subjects:
                credits = subject['credits']
                grade = subject['grade'].upper()
                points = grade_points.get(grade, 0)
                
                if grade not in ['F', 'ABSENT', 'AB', 'MP', '-']:
                    total_credits += credits
                    total_points += points * credits
            
            if total_credits > 0:
                calculated_sgpa = round(total_points / total_credits, 2)
        
        # Use provided SGPA or calculated one
        final_sgpa = sgpa if sgpa > 0 else calculated_sgpa
        
        student_record = {
            "student_id": student_id,
            "semester": semester,
            "university": university,
            "upload_date": upload_date,
            "sgpa": final_sgpa,
            "subjectGrades": subjects
        }
        
        results.append(student_record)
    
    print(f"Processed {len(results)} students")
    return results

def parse_autonomous_pdf_generator(file_path, semester="Unknown", university="Autonomous", batch_size=50):
    """Generator version that yields batches of student records for real-time processing"""
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
    
    print(f"Using semester: {semester}")
    print(f"Using university: {university}")
    
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

def parse_autonomous_pdf(file_path, semester="Unknown", university="Autonomous", streaming_callback=None):
    """Dynamic autonomous PDF parser that detects format and adapts accordingly"""
    print(f"Starting dynamic autonomous parsing of: {file_path}")
    start_time = time.time()
    
    students_processed = 0
    processed_students = set()  # Track processed students for streaming
    
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
            if record['student_id'] not in processed_students:
                processed_students.add(record['student_id'])
                students_processed += 1
                streaming_callback(record, students_processed)
    
    total_time = time.time() - start_time
    print(f"Completed dynamic parsing in {total_time:.2f} seconds")
    print(f"Total students processed: {len(results)}")
    
    if results:
        sample = results[0]
        print(f"Sample record: {sample['student_id']} has {len(sample['subjectGrades'])} subjects")
        print(f"Sample SGPA: {sample['sgpa']}")
    else:
        print("No student records found - check PDF format")

    return results
