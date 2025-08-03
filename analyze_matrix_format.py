#!/usr/bin/env python3
"""Analyze the matrix format PDF to understand header structure"""

import pdfplumber
import re

def analyze_matrix_pdf():
    """Analyze the header structure of the matrix format PDF"""
    
    with pdfplumber.open("sample_autonomous_new.pdf") as pdf:
        # Get first few pages
        for page_num in range(min(3, len(pdf.pages))):
            page = pdf.pages[page_num]
            text = page.extract_text()
            
            print(f"\n{'='*60}")
            print(f"PAGE {page_num + 1} - First 2000 characters:")
            print(f"{'='*60}")
            print(text[:2000])
            
            # Look for header patterns
            print(f"\n{'='*40}")
            print(f"HEADER ANALYSIS:")
            print(f"{'='*40}")
            
            # Find potential subject headers
            patterns = [
                r'Htno.*?Name.*?([A-Z]{2,10}.*?)(?:SGPA|Total)',
                r'S\.?No\.?\s+Htno\s+Name.*?([A-Z]{2,10}.*?)(?:SGPA|Total)',
                r'(?:HTNO|Htno).*?(?:NAME|Name).*?([A-Z]{2,10}.*?)(?:SGPA|Total)',
                r'Programme.*?\n.*?Name.*?\n(.*?)(?:SGPA|Total)',
                r'Name.*?\s+((?:[A-Z]{2,10}\s+){3,})'
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if matches:
                    print(f"Pattern {i+1} matched:")
                    print(f"Raw match: '{matches.group(1)[:200]}...'")
                    
                    # Extract potential subject codes
                    codes = re.findall(r'[A-Z]{2,10}', matches.group(1))
                    print(f"Subject codes found: {codes[:10]}")

if __name__ == "__main__":
    analyze_matrix_pdf()
