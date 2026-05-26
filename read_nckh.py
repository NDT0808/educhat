import zipfile
import xml.etree.ElementTree as ET
import os

def read_docx(filename):
    with zipfile.ZipFile(filename) as docx:
        xml_content = docx.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        text = []
        for paragraph in tree.findall('.//w:p', namespaces):
            para_text = []
            for run in paragraph.findall('.//w:r', namespaces):
                for text_node in run.findall('.//w:t', namespaces):
                    if text_node.text:
                        para_text.append(text_node.text)
            text.append(''.join(para_text))
            
        return '\n'.join(text)

if __name__ == "__main__":
    filepath = r"C:\Users\ASUS\Downloads\NCKH.docx"
    output_path = r"C:\Users\ASUS\Downloads\educhat\nckh_content.txt"
    
    if os.path.exists(filepath):
        print("Đang đọc file NCKH.docx...")
        content = read_docx(filepath)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Thành công! Đã trích xuất nội dung ra file {output_path}")
    else:
        print(f"Không tìm thấy file: {filepath}")
