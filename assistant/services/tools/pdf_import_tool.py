import pdfplumber
from ..rag_engine import RAGEngine

def import_pdf_text(file_path, title=None):
    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + '\n'
    rag = RAGEngine()
    rag.ingest_pdf_text(title or file_path, text, metadata={'source':'pdf_import'})
    return {'ok': True, 'chars': len(text)}
