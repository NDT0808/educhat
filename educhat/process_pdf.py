import fitz  # PyMuPDF
import os

pdf_path = r"c:\Users\ASUS\Downloads\CNTT_CLC_MoTa_CTDT_2428.pdf"
output_path = r"c:\Users\ASUS\Downloads\educhat\educhat\sgu_curriculum.txt"

def extract_text():
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found.")
        return

    print(f"Extracting text from {pdf_path} using PyMuPDF...")
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for i, page in enumerate(doc):
            page_text = page.get_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n"
                text += page_text
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        print(f"Successfully extracted text to {output_path}")
        print(f"Total pages: {len(doc)}")
        print(f"Total characters: {len(text)}")
        doc.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    extract_text()
