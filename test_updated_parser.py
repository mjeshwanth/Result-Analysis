import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'parser'))

from parser.parser_autonomous import parse_autonomous_pdf

def test_updated_parser():
    """Test the updated parser with the new PDF format"""
    pdf_path = "sample_autonomous.pdf"
    
    print("🧪 Testing updated autonomous parser...")
    
    try:
        results = parse_autonomous_pdf(pdf_path)
        
        if results:
            print(f"\n✅ SUCCESS! Parsed {len(results)} students")
            
            # Show sample results
            for i, student in enumerate(results[:2]):
                print(f"\n📋 Student {i+1}:")
                print(f"  ID: {student['student_id']}")
                print(f"  Semester: {student['semester']}")
                print(f"  University: {student['university'][:50]}...")
                print(f"  SGPA: {student['sgpa']}")
                print(f"  Subjects: {len(student['subjectGrades'])}")
                
                # Show first few subjects
                for j, subject in enumerate(student['subjectGrades'][:2]):
                    print(f"    {j+1}. {subject['code']}: {subject['subject'][:30]}... -> {subject['grade']} (Credits: {subject['credits']})")
            
            print(f"\n📊 Total: {len(results)} students processed successfully")
            
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updated_parser()
