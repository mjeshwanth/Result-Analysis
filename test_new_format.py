import sys
sys.path.append('parser')

from parser_autonomous import parse_autonomous_pdf

def test_new_format():
    """Test the parser with the new matrix format PDF"""
    pdf_path = "sample_autonomous_new.pdf"
    
    print("Testing new format autonomous parser...")
    
    try:
        results = parse_autonomous_pdf(pdf_path)
        
        if results:
            print(f"\nSUCCESS! Parsed {len(results)} students")
            
            # Show sample results
            for i, student in enumerate(results[:3]):
                print(f"\nStudent {i+1}:")
                print(f"  ID: {student['student_id']}")
                print(f"  Semester: {student['semester']}")
                print(f"  University: {student['university'][:50]}...")
                print(f"  SGPA: {student['sgpa']}")
                print(f"  Subjects: {len(student['subjectGrades'])}")
                
                # Show first few subjects
                for j, subject in enumerate(student['subjectGrades'][:3]):
                    print(f"    {j+1}. {subject['code']}: {subject['subject'][:30]}... -> {subject['grade']} (Credits: {subject['credits']})")
                
                if len(student['subjectGrades']) > 3:
                    print(f"    ... and {len(student['subjectGrades']) - 3} more subjects")
            
            # Show statistics
            total_subjects = sum(len(student['subjectGrades']) for student in results)
            avg_subjects = total_subjects / len(results) if results else 0
            
            sgpas = [student['sgpa'] for student in results if student['sgpa'] > 0]
            avg_sgpa = sum(sgpas) / len(sgpas) if sgpas else 0
            
            print(f"\nStatistics:")
            print(f"  Total students: {len(results)}")
            print(f"  Total subject records: {total_subjects}")
            print(f"  Average subjects per student: {avg_subjects:.1f}")
            print(f"  Average SGPA: {avg_sgpa:.2f}")
            
        else:
            print("No results found - check PDF format")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_format()
