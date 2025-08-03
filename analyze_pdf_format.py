import pdfplumber
import re
from pathlib import Path

def analyze_pdf_format(file_path):
    """Analyze PDF format to understand structure and patterns"""
    print(f"🔍 Analyzing PDF format: {file_path}")
    
    with pdfplumber.open(file_path) as pdf:
        print(f"📄 PDF has {len(pdf.pages)} pages")
        
        # Extract text from first few pages to understand structure
        first_page_text = ""
        if pdf.pages:
            first_page_text = pdf.pages[0].extract_text() or ""
        
        # Extract text from a middle page to see student data format
        middle_page_text = ""
        if len(pdf.pages) > 1:
            middle_idx = len(pdf.pages) // 2
            middle_page_text = pdf.pages[middle_idx].extract_text() or ""
        
        print("\n" + "="*80)
        print("🎯 FIRST PAGE ANALYSIS (Header/Metadata)")
        print("="*80)
        print(first_page_text[:2000])
        
        print("\n" + "="*80)
        print("📊 MIDDLE PAGE ANALYSIS (Student Data)")
        print("="*80)
        print(middle_page_text[:2000])
        
        # Analyze patterns
        print("\n" + "="*80)
        print("🔍 PATTERN ANALYSIS")
        print("="*80)
        
        # Look for semester patterns
        semester_patterns = [
            r'(\d+)\s*(?:st|nd|rd|th)?\s*(?:Semester|SEM|sem)',
            r'Semester\s*[:-]?\s*(\d+)',
            r'SEM\s*[:-]?\s*(\d+)',
            r'B\.?Tech\s*.*?(\d+)\s*(?:st|nd|rd|th)?\s*(?:Semester|SEM|sem)',
            r'(\d+)-(\d+)\s*(?:Semester|SEM|sem)',
            r'(\d+)\s*-\s*(\d+)',
        ]
        
        full_text = first_page_text + "\n" + middle_page_text
        
        print("📅 Semester Detection:")
        for i, pattern in enumerate(semester_patterns):
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                print(f"  Pattern {i+1}: {pattern} -> {matches[:3]}")
        
        # Look for subject patterns
        print("\n📚 Subject Code Patterns:")
        subject_patterns = [
            r'([A-Z0-9]{4,10})\s*[-:]?\s*([A-Z][A-Za-z\s&,\-()]+)',
            r'(\d+)\)\s*([A-Z0-9]+)\s*-\s*(.+?)(?=\d+\)|$)',
            r'([A-Z]{2,4}\d{3,4})\s*(.+?)(?=\n|$)',
            r'(\w{6,10})\s+([^A-FS\-\d]+?)(?=\s+\w{6,10}|$)',
        ]
        
        for i, pattern in enumerate(subject_patterns):
            matches = re.findall(pattern, full_text[:3000], re.IGNORECASE | re.DOTALL)
            if matches:
                print(f"  Pattern {i+1}: Found {len(matches)} matches")
                for match in matches[:3]:
                    print(f"    {match}")
        
        # Look for student ID patterns
        print("\n🆔 Student ID Patterns:")
        student_id_patterns = [
            r'\b([A-Z0-9]{8,12})\b',
            r'\b(\d{8,12})\b',
            r'\b([A-Z]{2}\d{8,10})\b',
        ]
        
        for i, pattern in enumerate(student_id_patterns):
            matches = re.findall(pattern, middle_page_text)
            if matches:
                print(f"  Pattern {i+1}: {pattern} -> {matches[:5]}")
        
        # Look for grade patterns
        print("\n📊 Grade Patterns:")
        grade_lines = []
        for line in middle_page_text.split('\n'):
            if re.search(r'[A-FS\-]', line) and len(line.strip()) > 10:
                grade_lines.append(line.strip())
        
        print("Sample lines with grades:")
        for line in grade_lines[:5]:
            print(f"  {line}")
        
        # Look for SGPA patterns
        print("\n📈 SGPA Patterns:")
        sgpa_pattern = r'(\d+\.\d{2})'
        sgpa_matches = re.findall(sgpa_pattern, middle_page_text)
        if sgpa_matches:
            print(f"  Found SGPA values: {sgpa_matches[:10]}")

if __name__ == "__main__":
    pdf_path = "sample_autonomous.pdf"
    if Path(pdf_path).exists():
        analyze_pdf_format(pdf_path)
    else:
        print(f"❌ PDF file not found: {pdf_path}")
