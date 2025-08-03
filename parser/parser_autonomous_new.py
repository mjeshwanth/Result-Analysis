# Clean autonomous PDF parser without emojis - imports from dynamic parser
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
