#!/usr/bin/env python3
"""
Quick test of the enhanced JNTUK parser
"""

import os
from parser.parser_jntuk import parse_jntuk_pdf_generator

def test_enhanced_parser():
    # Test with the SGPA format PDF
    pdf_path = "1st BTech 1st Sem (CR24) Results.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"🧪 Testing enhanced parser with: {pdf_path}")
    
    total_students = 0
    for batch_num, batch_records in enumerate(parse_jntuk_pdf_generator(pdf_path, batch_size=20), 1):
        batch_size = len(batch_records)
        total_students += batch_size
        print(f"📦 Batch {batch_num}: {batch_size} students")
        
        # Show sample records
        if batch_num == 1 and batch_records:
            sample_student = batch_records[0]
            print(f"📊 Sample student: {sample_student['student_id']}")
            print(f"📊 SGPA: {sample_student.get('sgpa', 0)}")
            print(f"📊 Subjects: {len(sample_student.get('subjectGrades', []))}")
            if sample_student.get('subjectGrades'):
                print(f"📊 First subject: {sample_student['subjectGrades'][0]}")
    
    print(f"🎯 Total students extracted: {total_students}")

if __name__ == "__main__":
    test_enhanced_parser()
