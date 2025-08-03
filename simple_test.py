import sys
sys.path.append('parser')

print("Step 1: Import")
from parser_autonomous import parse_autonomous_pdf
print("Import successful")

print("Step 2: Check file")
import os
pdf_path = "sample_autonomous.pdf"
if os.path.exists(pdf_path):
    print(f"File exists: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path)} bytes")
else:
    print(f"File not found: {pdf_path}")
    print("Files in current dir:", os.listdir('.'))

print("Step 3: Parse PDF")
try:
    results = parse_autonomous_pdf(pdf_path)
    print(f"Parsing completed. Results: {len(results) if results else 0} students")
    if results:
        print(f"Sample student: {results[0]['student_id']}")
except Exception as e:
    print(f"Parsing error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed")
