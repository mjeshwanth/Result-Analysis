import pdfplumber
import re
from datetime import datetime
from collections import defaultdict
import time

def parse_jntuk_pdf_generator(file_path, batch_size=None):
    """Generator version that yields batches of student records for real-time processing"""
    if batch_size is None:
        batch_size = 500
    print(f"🚀 Starting optimized batch JNTUK parsing of: {file_path}")
    start_time = time.time()
    
    results = defaultdict(lambda: {
        "subjectGrades": [],
        "totalCredits": 0
    })
    
    current_semester = None
    current_exam_type = "regular"
    upload_date = datetime.now().strftime("%Y-%m-%d")
    students_processed = 0
    processed_students = set()
    batch_count = 0
    
    # Grade points for SGPA calculation
    grade_points = {
        'S': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 
        'C': 5, 'D': 4, 'F': 0, 'MP': 0, 'ABSENT': 0
    }
    
    with pdfplumber.open(file_path) as pdf:
        print(f"📄 JNTUK PDF has {len(pdf.pages)} pages")
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            # Show progress for large PDFs
            if page_num > 0 and page_num % 5 == 0:
                print(f"📊 Processed {page_num+1}/{len(pdf.pages)} pages...")

            # Optimized semester detection - search only first few pages
            if not current_semester or page_num < 3:
                semester_match = re.search(r"([I|II|III|IV]+)\s+B\.Tech\s+([I|II|III|IV|V|VI|VII|VIII]+)\s+Semester", text)
                if semester_match:
                    sem_roman = semester_match.group(2)
                    roman_to_num = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8}
                    sem_num = roman_to_num.get(sem_roman, 1)
                    current_semester = f"Semester {sem_num}"
                    print(f"🎯 Detected semester: {current_semester}")
            
            # Optimized exam type detection - check once per PDF
            if page_num < 3:
                if re.search(r"supply|supplementary|supple", text, re.IGNORECASE):
                    current_exam_type = "supply"

            # Process students from this page
            page_students = []
            page_student_records = []
            
            # Table extraction
            try:
                tables = page.extract_tables()
                if tables:
                    print(f"🔍 Found {len(tables)} tables on page {page_num}")
                    for table_idx, table in enumerate(tables):
                        if not table or len(table) < 2:
                            print(f"❌ Table {table_idx} is empty or too small")
                            continue
                        
                        print(f"✅ Processing table {table_idx} with {len(table)} rows")
                        print(f"📊 Sample rows: {table[:3]}")  # Show first 3 rows
                            
                        for row_idx, row in enumerate(table[1:]):  # Skip header
                            if not row or len(row) < 6:
                                if row_idx < 5:  # Only show first few invalid rows
                                    print(f"❌ Row {row_idx} invalid: {row}")
                                continue
                            
                            if row_idx < 3:  # Show first few valid rows for debugging
                                print(f"🔍 Processing row {row_idx}: {row}")
                                
                            try:
                                if len(row) == 7:
                                    _, htno, subcode, subname, internals, grade, credits = row
                                elif len(row) == 6:
                                    htno, subcode, subname, internals, grade, credits = row
                                else:
                                    if row_idx < 3:
                                        print(f"❌ Invalid row length {len(row)} in row {row_idx}: {row}")
                                    continue

                                # Enhanced student ID pattern matching
                                htno_str = str(htno).strip()
                                if not htno_str:
                                    if row_idx < 3:
                                        print(f"❌ Empty HTNO in row {row_idx}")
                                    continue
                                
                                # Support multiple JNTUK student ID formats
                                valid_patterns = [
                                    r'^\d{2}[A-Z0-9]{8}$',          # 20B91A0501
                                    r'^\d{2}[A-Z0-9]{9}$',          # 20B91A05010  
                                    r'^\d{4}[A-Z0-9]{8}$',          # 2020B91A0501
                                ]
                                
                                is_valid_htno = any(re.match(pattern, htno_str) for pattern in valid_patterns)
                                
                                if not is_valid_htno:
                                    if row_idx < 5:
                                        print(f"❌ Invalid HTNO '{htno_str}' in row {row_idx}")
                                    continue
                                
                                if row_idx < 3:
                                    print(f"✅ Valid HTNO found: {htno_str}")

                                internals_val = 0 if str(internals).strip() == 'ABSENT' else int(internals or 0)
                                credits_val = float(credits or 0)

                                student = results[htno]
                                student['student_id'] = htno
                                student['university'] = "JNTUK"
                                student['semester'] = current_semester or "Unknown"
                                student['examType'] = current_exam_type
                                student['upload_date'] = upload_date

                                student['subjectGrades'].append({
                                    "code": str(subcode or "").strip(),
                                    "subject": str(subname or "").strip(),
                                    "internals": internals_val,
                                    "grade": str(grade or "").strip(),
                                    "credits": credits_val
                                })

                                student['totalCredits'] += credits_val
                                
                                # Add to page students if not already processed
                                if htno not in processed_students:
                                    processed_students.add(htno)
                                    page_students.append(htno)
                                    # Add full student record for batching
                                    student_data = results[htno]
                                    if student_data.get('subjectGrades'):
                                        # Calculate SGPA
                                        total_points = 0
                                        total_credits = 0
                                        for subject in student_data['subjectGrades']:
                                            grade = subject.get('grade', 'F')
                                            credits = subject.get('credits', 0)
                                            points = grade_points.get(grade, 0)
                                            total_points += points * credits
                                            total_credits += credits
                                        sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
                                        page_student_records.append({
                                            "student_id": student_data['student_id'],
                                            "semester": student_data['semester'],
                                            "university": student_data['university'],
                                            "upload_date": student_data['upload_date'],
                                            "sgpa": sgpa,
                                            "subjectGrades": student_data['subjectGrades']
                                        })
                                    
                            except (ValueError, TypeError, AttributeError):
                                continue
            except Exception:
                pass

            # Line-based extraction
            try:
                lines = text.split('\n')
                for line in lines:
                    if not line.strip() or 'Htno' in line or 'Subcode' in line:
                        continue

                    parts = line.strip().split()
                    if len(parts) >= 6:
                        try:
                            if len(parts) > 1 and len(str(parts[1])) == 10 and re.match(r'\d{2}[A-Z0-9]{8}', str(parts[1])):
                                htno = parts[1]
                                
                                if htno in processed_students:
                                    continue
                                    
                                subcode = parts[2] if len(parts) > 2 else ""
                                credits = parts[-1]
                                grade = parts[-2]
                                internals = parts[-3]

                                if (re.match(r'\d+|ABSENT', str(internals)) and 
                                    re.match(r'[A-F][\+\-]?|MP|ABSENT|S|COMPLE', str(grade)) and
                                    re.match(r'\d+(?:\.\d+)?', str(credits))):

                                    internals_val = 0 if str(internals) == 'ABSENT' else int(internals)
                                    credits_val = float(credits)
                                    subname_parts = parts[3:-3] if len(parts) > 6 else []
                                    subname = ' '.join(subname_parts)

                                    student = results[htno]
                                    student['student_id'] = htno
                                    student['university'] = "JNTUK"
                                    student['semester'] = current_semester or "Unknown"
                                    student['examType'] = current_exam_type
                                    student['upload_date'] = upload_date

                                    student['subjectGrades'].append({
                                        "code": str(subcode).strip(),
                                        "subject": subname.strip(),
                                        "internals": internals_val,
                                        "grade": str(grade).strip(),
                                        "credits": credits_val
                                    })

                                    student['totalCredits'] += credits_val
                                    
                                    # Add to page students if not already processed
                                    if htno not in processed_students:
                                        processed_students.add(htno)
                                        page_students.append(htno)
                                        # Add full student record for batching
                                        student_data = results[htno]
                                        if student_data.get('subjectGrades'):
                                            # Calculate SGPA
                                            total_points = 0
                                            total_credits = 0
                                            for subject in student_data['subjectGrades']:
                                                grade = subject.get('grade', 'F')
                                                credits = subject.get('credits', 0)
                                                points = grade_points.get(grade, 0)
                                                total_points += points * credits
                                                total_credits += credits
                                            sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
                                            page_student_records.append({
                                                "student_id": student_data['student_id'],
                                                "semester": student_data['semester'],
                                                "university": student_data['university'],
                                                "upload_date": student_data['upload_date'],
                                                "sgpa": sgpa,
                                                "subjectGrades": student_data['subjectGrades']
                                            })
                                        
                        except (ValueError, IndexError, AttributeError):
                            continue
            except Exception:
                pass
            
            # Yield batch when we have enough students
            if len(page_student_records) >= batch_size:
                batch_records = page_student_records[:batch_size]
                if batch_records:
                    batch_count += 1
                    students_processed += len(batch_records)
                    print(f"🚀 Yielding batch {batch_count}: {len(batch_records)} students (Total: {students_processed})")
                    yield batch_records
                # Remove processed students from page_students and page_student_records
                page_students = page_students[batch_size:]
                page_student_records = page_student_records[batch_size:]
            
            # Also check if we've accumulated enough students across all results
            if len(results) >= batch_size and len(results) % batch_size == 0:
                # Yield a batch from accumulated results
                batch_records = []
                students_to_yield = []
                
                for htno, student_data in list(results.items()):
                    if htno not in processed_students and len(students_to_yield) < batch_size:
                        students_to_yield.append(htno)
                        processed_students.add(htno)
                
                for htno in students_to_yield:
                    student_data = results[htno]
                    if student_data.get('subjectGrades'):
                        # Calculate SGPA
                        total_points = 0
                        total_credits = 0
                        
                        for subject in student_data['subjectGrades']:
                            grade = subject.get('grade', 'F')
                            credits = subject.get('credits', 0)
                            points = grade_points.get(grade, 0)
                            total_points += points * credits
                            total_credits += credits
                        
                        sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
                        
                        batch_records.append({
                            "student_id": student_data['student_id'],
                            "semester": student_data['semester'],
                            "university": student_data['university'],
                            "upload_date": student_data['upload_date'],
                            "sgpa": sgpa,
                            "subjectGrades": student_data['subjectGrades']
                        })
                
                if batch_records:
                    batch_count += 1
                    students_processed += len(batch_records)
                    print(f"🚀 Yielding page batch {batch_count}: {len(batch_records)} students (Total: {students_processed})")
                    yield batch_records

    # Yield remaining students in proper batches
    remaining_student_records = []
    for htno, student_data in results.items():
        if student_data.get('subjectGrades'):
            # Calculate SGPA
            total_points = 0
            total_credits = 0
            for subject in student_data['subjectGrades']:
                grade = subject.get('grade', 'F')
                credits = subject.get('credits', 0)
                points = grade_points.get(grade, 0)
                total_points += points * credits
                total_credits += credits
            sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
            remaining_student_records.append({
                "student_id": student_data['student_id'],
                "semester": student_data['semester'],
                "university": student_data['university'],
                "upload_date": student_data['upload_date'],
                "sgpa": sgpa,
                "subjectGrades": student_data['subjectGrades']
            })
    for i in range(0, len(remaining_student_records), batch_size):
        batch_records = remaining_student_records[i:i + batch_size]
        if batch_records:
            batch_count += 1
            students_processed += len(batch_records)
            print(f"🚀 Yielding final batch {batch_count}: {len(batch_records)} students (Total: {students_processed})")
            yield batch_records

    total_time = time.time() - start_time
    print(f"✅ Completed batch parsing in {total_time:.2f} seconds - {students_processed} total students")

def parse_jntuk_pdf(file_path, streaming_callback=None):
    print(f"🚀 Starting real-time JNTUK parsing of: {file_path}")
    start_time = time.time()
    
    results = defaultdict(lambda: {
        "subjectGrades": [],
        "totalCredits": 0
    })

    current_semester = None
    current_exam_type = "regular"
    upload_date = datetime.now().strftime("%Y-%m-%d")  # Calculate once
    students_processed = 0
    processed_students = set()  # Track processed students for streaming
    
    with pdfplumber.open(file_path) as pdf:
        print(f"📄 JNTUK PDF has {len(pdf.pages)} pages")
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            # Show progress for large PDFs
            if page_num > 0 and page_num % 5 == 0:
                print(f"📊 Processed {page_num+1}/{len(pdf.pages)} pages...")

            # Optimized semester detection - search only first few pages
            if not current_semester or page_num < 3:
                semester_match = re.search(r"([I|II|III|IV]+)\s+B\.Tech\s+([I|II|III|IV|V|VI|VII|VIII]+)\s+Semester", text)
                if semester_match:
                    sem_roman = semester_match.group(2)
                    roman_to_num = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8}
                    sem_num = roman_to_num.get(sem_roman, 1)
                    current_semester = f"Semester {sem_num}"
                    print(f"🎯 Detected semester: {current_semester}")
            
            # Optimized exam type detection - check once per PDF
            if page_num < 3:
                if re.search(r"supply|supplementary|supple", text, re.IGNORECASE):
                    current_exam_type = "supply"

            # Optimized table extraction
            try:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                            
                        for row in table[1:]:  # Skip header
                            if not row or len(row) < 6:
                                continue
                                
                            try:
                                if len(row) == 7:
                                    _, htno, subcode, subname, internals, grade, credits = row
                                elif len(row) == 6:
                                    htno, subcode, subname, internals, grade, credits = row
                                else:
                                    continue

                                if not htno or not re.match(r'\d{2}[A-Z0-9]{8}', str(htno)):
                                    continue

                                internals_val = 0 if str(internals).strip() == 'ABSENT' else int(internals or 0)
                                credits_val = float(credits or 0)

                                student = results[htno]
                                student['student_id'] = htno
                                student['university'] = "JNTUK"
                                student['semester'] = current_semester or "Unknown"
                                student['examType'] = current_exam_type
                                student['upload_date'] = upload_date

                                student['subjectGrades'].append({
                                    "code": str(subcode or "").strip(),
                                    "subject": str(subname or "").strip(),
                                    "internals": internals_val,
                                    "grade": str(grade or "").strip(),
                                    "credits": credits_val
                                })

                                student['totalCredits'] += credits_val
                                
                                # Send real-time update if callback provided
                                if streaming_callback and htno not in processed_students:
                                    processed_students.add(htno)
                                    students_processed += 1
                                    
                                    # Calculate and send complete student record
                                    grade_points = {
                                        'S': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 
                                        'C': 5, 'D': 4, 'F': 0, 'MP': 0, 'ABSENT': 0
                                    }
                                    
                                    total_points = 0
                                    total_credits = 0
                                    for subject in student['subjectGrades']:
                                        grade = subject.get('grade', 'F')
                                        credits = subject.get('credits', 0)
                                        points = grade_points.get(grade, 0)
                                        total_points += points * credits
                                        total_credits += credits
                                    
                                    sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
                                    
                                    complete_record = {
                                        "student_id": student['student_id'],
                                        "semester": student['semester'],
                                        "university": student['university'],
                                        "upload_date": student['upload_date'],
                                        "sgpa": sgpa,
                                        "subjectGrades": student['subjectGrades'].copy()
                                    }
                                    
                                    streaming_callback(complete_record, students_processed)
                            except (ValueError, TypeError, AttributeError):
                                continue
            except Exception:
                pass

            # Fast line-based extraction for other formats
            try:
                lines = text.split('\n')
                for line in lines:
                    if not line.strip() or 'Htno' in line or 'Subcode' in line:
                        continue

                    parts = line.strip().split()
                    if len(parts) >= 6:
                        try:
                            if len(parts) > 1 and len(str(parts[1])) == 10 and re.match(r'\d{2}[A-Z0-9]{8}', str(parts[1])):
                                htno = parts[1]
                                subcode = parts[2] if len(parts) > 2 else ""
                                credits = parts[-1]
                                grade = parts[-2]
                                internals = parts[-3]

                                if (re.match(r'\d+|ABSENT', str(internals)) and 
                                    re.match(r'[A-F][\+\-]?|MP|ABSENT|S|COMPLE', str(grade)) and
                                    re.match(r'\d+(?:\.\d+)?', str(credits))):

                                    internals_val = 0 if str(internals) == 'ABSENT' else int(internals)
                                    credits_val = float(credits)
                                    subname_parts = parts[3:-3] if len(parts) > 6 else []
                                    subname = ' '.join(subname_parts)

                                    student = results[htno]
                                    student['student_id'] = htno
                                    student['university'] = "JNTUK"
                                    student['semester'] = current_semester or "Unknown"
                                    student['examType'] = current_exam_type
                                    student['upload_date'] = upload_date

                                    student['subjectGrades'].append({
                                        "code": str(subcode).strip(),
                                        "subject": subname.strip(),
                                        "internals": internals_val,
                                        "grade": str(grade).strip(),
                                        "credits": credits_val
                                    })

                                    student['totalCredits'] += credits_val
                                    
                                    # Send real-time update if callback provided
                                    if streaming_callback and htno not in processed_students:
                                        processed_students.add(htno)
                                        students_processed += 1
                                        
                                        # Calculate and send complete student record
                                        grade_points = {
                                            'S': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 
                                            'C': 5, 'D': 4, 'F': 0, 'MP': 0, 'ABSENT': 0
                                        }
                                        
                                        total_points = 0
                                        total_credits = 0
                                        for subject in student['subjectGrades']:
                                            grade = subject.get('grade', 'F')
                                            credits = subject.get('credits', 0)
                                            points = grade_points.get(grade, 0)
                                            total_points += points * credits
                                            total_credits += credits
                                        
                                        sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
                                        
                                        complete_record = {
                                            "student_id": student['student_id'],
                                            "semester": student['semester'],
                                            "university": student['university'],
                                            "upload_date": student['upload_date'],
                                            "sgpa": sgpa,
                                            "subjectGrades": student['subjectGrades'].copy()
                                        }
                                        
                                        streaming_callback(complete_record, students_processed)
                        except (ValueError, IndexError, AttributeError):
                            continue
            except Exception:
                pass

    # Convert results to final format with SGPA calculation
    final_results = []
    grade_points = {
        'S': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 
        'C': 5, 'D': 4, 'F': 0, 'MP': 0, 'ABSENT': 0
    }
    
    for htno, student_data in results.items():
        if student_data.get('subjectGrades'):
            # Calculate SGPA
            total_points = 0
            total_credits = 0
            
            for subject in student_data['subjectGrades']:
                grade = subject.get('grade', 'F')
                credits = subject.get('credits', 0)
                points = grade_points.get(grade, 0)
                total_points += points * credits
                total_credits += credits
            
            sgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
            
            final_results.append({
                "student_id": student_data['student_id'],
                "semester": student_data['semester'],
                "university": student_data['university'],
                "upload_date": student_data['upload_date'],
                "sgpa": sgpa,
                "subjectGrades": student_data['subjectGrades']
            })

    total_time = time.time() - start_time
    print(f"✅ Extracted {len(final_results)} JNTUK student records in {total_time:.2f} seconds")
    
    if final_results:
        print(f"📝 Sample record: {final_results[0]['student_id']} has {len(final_results[0]['subjectGrades'])} subjects")
    else:
        print("⚠️ No JNTUK student records found - check PDF format")

    return final_results
