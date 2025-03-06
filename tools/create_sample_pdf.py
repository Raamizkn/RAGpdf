import os
import sys
from fpdf import FPDF

# Add parent directory to path to import config
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from backend import config
    DATA_DIR = config.DATA_DIR
except (ImportError, AttributeError):
    # Fallback to hardcoded values if import fails
    DATA_DIR = os.path.join(parent_dir, "data")
    # Create directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

def create_sample_pdf():
    """Create a sample PDF from the sample text file"""
    # Check if sample text file exists
    sample_txt = os.path.join(DATA_DIR, "sample.txt")
    if not os.path.exists(sample_txt):
        print(f"Sample text file not found at {sample_txt}")
        return
    
    # Read the text file
    with open(sample_txt, "r") as f:
        text = f.read()
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Introduction to Machine Learning", ln=True)
    pdf.ln(5)
    
    # Add content
    pdf.set_font("Arial", "", 12)
    
    # Split text into lines and add to PDF
    lines = text.split("\n")
    for line in lines:
        # Handle headings
        if line.startswith("# "):
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, line[2:], ln=True)
            pdf.ln(5)
        elif line.startswith("## "):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, line[3:], ln=True)
            pdf.ln(5)
        elif line.startswith("### "):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, line[4:], ln=True)
            pdf.ln(5)
        # Handle list items
        elif line.startswith("- ") or line.startswith("* "):
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, "  - " + line[2:], ln=True)
        elif line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. "):
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, "  " + line, ln=True)
        # Regular text
        elif line.strip():
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, line)
            pdf.ln(2)
    
    # Save the PDF
    output_path = os.path.join(DATA_DIR, "sample.pdf")
    pdf.output(output_path)
    print(f"Sample PDF created at {output_path}")

if __name__ == "__main__":
    # Create directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create sample PDF
    create_sample_pdf() 