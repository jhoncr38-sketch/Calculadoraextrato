import pdfplumber
import pandas as pd


def extract_pdf_text(file_obj) -> str:
    """Extrai e concatena o texto de todas as páginas de um PDF."""
    paginas = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            texto = page.extract_text() or ""
            paginas.append(texto)
    return "\n".join(paginas)


def extract_excel_rows(file_obj) -> pd.DataFrame:
    """Lê um arquivo Excel e retorna um DataFrame com a primeira planilha."""
    return pd.read_excel(file_obj)
