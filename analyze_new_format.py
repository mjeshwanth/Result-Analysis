import pdfplumber
import re
from pathlib import Path

def analyze_new_pdf_format(file_path):
    """Analyze the new PDF format to understand its structure"""
    print(f"Analyzing new PDF format: {file_path}")
    
    with pdfplumber.open(file_path) as pdf:
        print(f"PDF has {len(pdf.pages)} pages")
        
        # Extract text from first few pages
        first_page_text = ""
        if pdf.pages:
            first_page_text = pdf.pages[0].extract_text() or ""
        
        # Extract text from a middle page
        middle_page_text = ""
        if len(pdf.pages) > 1:
            middle_idx = min(2, len(pdf.pages) - 1)
            middle_page_text = pdf.pages[middle_idx].extract_text() or ""
        
        print("\n" + "="*80)
        print("FIRST PAGE ANALYSIS")
        print("="*80)
        print(first_page_text[:2000])
        
        print("\n" + "="*80)
        print("MIDDLE PAGE ANALYSIS")
        print("="*80)
        print(middle_page_text[:2000])
        
        # Analyze patterns
        print("\n" + "="*80)
        print("PATTERN ANALYSIS")
        print("="*80)
        
        full_text = first_page_text + "\n" + middle_page_text
        
        # Look for semester patterns
        print("Semester Detection:")
        semester_patterns = [
            r'(\d+)\s*(?:st|nd|rd|th)?\s*(?:Semester|SEM|sem)',
            r'Semester\s*[:-]?\s*(\d+)',
            r'(\d+)\s*(?:st|nd|rd|th)?\s*B\.?Tech',
            r'B\.?Tech\s*(\d+)\s*(?:st|nd|rd|th)?\s*(?:Semester|SEM|sem)',
        ]
        
        for i, pattern in enumerate(semester_patterns):
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                print(f"  Pattern {i+1}: {pattern} -> {matches[:3]}")
        
        # Look for different table structures
        print("\nTable Structure Detection:")
        table_patterns = [
            r'Roll\s*No\.?\s*Name\s*.*?Grade',
            r'Htno\s*.*?Grade.*?Credits',
            r'S\.?No\.?\s*Roll\s*No\.?\s*.*?Grade',
            r'Student\s*ID\s*.*?Subject.*?Grade',
            r'\d+\s+[A-Z0-9]{8,15}\s+[A-Za-z\s]+.*?[A-FS]',
        ]
        
        for i, pattern in enumerate(table_patterns):
            matches = re.findall(pattern, full_text, re.IGNORECASE | re.DOTALL)
            if matches:
                print(f"  Table Pattern {i+1}: Found {len(matches)} matches")
                for match in matches[:2]:
                    print(f"    {str(match)[:100]}...")
        
        # Look for student records patterns
        print("\nStudent Record Patterns:")
        student_patterns = [
            r'\d+\s+([A-Z0-9]{8,15})\s+([A-Za-z\s]+?)\s+.*?([A-FS])',
            r'([A-Z0-9]{8,15})\s+([A-Za-z\s,]+?)\s+.*?([A-FS])',
            r'\d+\s+([A-Z0-9]{8,15})\s+(.+?)\s+(\d+\.\d{2})',
        ]
        
        for i, pattern in enumerate(student_patterns):
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                print(f"  Student Pattern {i+1}: Found {len(matches)} matches")
                for match in matches[:3]:
                    print(f"    {match}")
        
        # Look for subject patterns
        print("\nSubject Patterns:")
        subject_patterns = [
            r'([A-Z0-9]{4,10})\s*[-:]?\s*([A-Z][A-Za-z\s&,\-()]+)',
            r'(\d+)\)\s*([A-Z0-9]+)\s*-\s*(.+?)(?=\d+\)|$)',
            r'Subject:\s*([A-Z0-9]+)\s*-\s*(.+)',
        ]
        
        for i, pattern in enumerate(subject_patterns):
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                print(f"  Subject Pattern {i+1}: Found {len(matches)} matches")
                for match in matches[:3]:
                    print(f"    {match}")

if __name__ == "__main__":
    pdf_path = "sample_autonomous_new.pdf"
    if Path(pdf_path).exists():
        analyze_new_pdf_format(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")
