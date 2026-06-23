import pandas as pd

from .base import Transaction

COLUNAS_DATA = ["data", "data da transação", "dia"]
COLUNAS_VALOR = ["valor", "valor (r$)", "valor líquido", "valor líquido (r$)", "valor bruto"]
COLUNAS_DESCRICAO = ["descrição", "descricao", "histórico", "historico", "lançamentos", "lancamentos"]


def _achar_coluna(colunas_lower: list[str], candidatos: list[str]) -> int | None:
    for candidato in candidatos:
        if candidato in colunas_lower:
            return colunas_lower.index(candidato)
    return None


def _achar_linha_cabecalho(df_cru: pd.DataFrame) -> int | None:
    """Acha a primeira linha que parece um cabeçalho (contém alguma coluna de
    valor conhecida). Assim funciona mesmo quando a planilha tem linhas de
    título antes do cabeçalho de verdade."""
    for i in range(min(len(df_cru), 15)):
        celulas = [str(c).strip().lower() for c in df_cru.iloc[i].tolist()]
        if _achar_coluna(celulas, COLUNAS_VALOR) is not None:
            return i
    return None


def parse(df_cru: pd.DataFrame) -> list[Transaction]:
    idx_cabecalho = _achar_linha_cabecalho(df_cru)
    if idx_cabecalho is None:
        return []
    df = df_cru.iloc[idx_cabecalho + 1:].copy()
    df.columns = [str(c).strip() for c in df_cru.iloc[idx_cabecalho].tolist()]

    colunas_lower = [str(c).strip().lower() for c in df.columns]
    idx_data = _achar_coluna(colunas_lower, COLUNAS_DATA)
    idx_valor = _achar_coluna(colunas_lower, COLUNAS_VALOR)
    idx_desc = _achar_coluna(colunas_lower, COLUNAS_DESCRICAO)

    if idx_valor is None:
        return []

    transacoes = []
    for _, linha in df.iterrows():
        valor_raw = linha.iloc[idx_valor]
        if isinstance(valor_raw, (int, float)):
            if pd.isna(valor_raw):
                continue
            valor = float(valor_raw)
        else:
            try:
                texto = str(valor_raw).replace("R$", "").strip()
                valor = float(texto.replace(".", "").replace(",", "."))
            except (ValueError, TypeError):
                continue
        data = str(linha.iloc[idx_data]) if idx_data is not None else ""
        descricao = str(linha.iloc[idx_desc]) if idx_desc is not None else "Lançamento"
        tipo = "entrada" if valor >= 0 else "saida"
        transacoes.append(Transaction(date=data, description=descricao, value=valor, tipo=tipo))
    return transacoes
