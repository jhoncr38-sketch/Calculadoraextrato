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
    """Lê a primeira planilha de um Excel sem assumir onde está o cabeçalho
    (header=None). Cada parser decide qual linha é o cabeçalho -- isso permite
    ler planilhas que têm linhas de título antes da tabela de verdade."""
    return pd.read_excel(file_obj, header=None)
