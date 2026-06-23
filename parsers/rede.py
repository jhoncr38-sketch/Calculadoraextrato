import pandas as pd

from .base import Transaction, formatar_documento, parse_valor_brl

# Relatório de Vendas da Rede (adquirente/maquininha de cartão), em Excel.
# Particularidades deste arquivo:
#  - A 1ª linha da planilha é um título ("EXTRATO PARA SIMPLES CONFERÊNCIA...");
#    o cabeçalho de verdade só aparece na 2ª linha. Por isso procuramos a linha
#    do cabeçalho em vez de assumir que é a primeira.
#  - Cada linha é uma venda. O valor que de fato entra na conta é o "valor
#    líquido" (a venda já com as taxas da maquininha descontadas).
#  - Só somamos vendas com status "aprovada" (uma venda negada não traz dinheiro).
COL_DATA = "data da venda"
COL_STATUS = "status da venda"
COL_LIQUIDO = "valor líquido"


def _achar_linha_cabecalho(df_cru: pd.DataFrame):
    """Acha em qual linha está o cabeçalho (a que contém 'data da venda')."""
    for i in range(min(len(df_cru), 15)):
        celulas = [str(c).strip().lower() for c in df_cru.iloc[i].tolist()]
        if COL_DATA in celulas and COL_LIQUIDO in celulas:
            return i
    return None


def _montar_tabela(df_cru: pd.DataFrame):
    """Devolve um DataFrame com o cabeçalho certo aplicado, ou None."""
    i = _achar_linha_cabecalho(df_cru)
    if i is None:
        return None
    cabecalho = [str(c).strip() for c in df_cru.iloc[i].tolist()]
    dados = df_cru.iloc[i + 1:].copy()
    dados.columns = cabecalho
    return dados


def _formatar_data(valor) -> str:
    """Converte a data da venda para o formato DD/MM/AAAA usado no resto do app."""
    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%d/%m/%Y")
    try:
        return pd.to_datetime(valor, dayfirst=True).strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(valor)


def extrair_titular(df_cru: pd.DataFrame):
    dados = _montar_tabela(df_cru)
    if dados is None or dados.empty:
        return "", ""
    primeira = dados.iloc[0]
    nome = ""
    doc = ""
    if "nome do estabelecimento" in dados.columns:
        nome = str(primeira["nome do estabelecimento"]).strip()
    if "CNPJ" in dados.columns:
        doc = formatar_documento(str(primeira["CNPJ"]))
    return nome, doc


def parse(df_cru: pd.DataFrame) -> list[Transaction]:
    dados = _montar_tabela(df_cru)
    if dados is None:
        return []

    transacoes = []
    for _, linha in dados.iterrows():
        status = str(linha.get(COL_STATUS, "")).strip().lower()
        if status != "aprovada":
            continue
        bruto = linha.get(COL_LIQUIDO)
        if isinstance(bruto, (int, float)) and not pd.isna(bruto):
            valor = float(bruto)
        else:
            try:
                valor = parse_valor_brl(str(bruto))
            except (ValueError, TypeError):
                continue
        transacoes.append(
            Transaction(
                date=_formatar_data(linha.get(COL_DATA, "")),
                description="Venda recebida (líquido)",
                value=valor,
                tipo="entrada",
            )
        )
    return transacoes
