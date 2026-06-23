import pandas as pd

from . import bb, itau, inter, mercadopago, pagbank_vendas, pagbank_extrato, nubank, rede, generic_excel
from .base import Transaction

# Ordem importa: checagens mais específicas primeiro. Cuidado: o nome de outro
# banco pode aparecer DENTRO de uma descrição de Pix (ex: um extrato Nubank
# que tem "BANCO INTER" como destinatário de uma transferência) -- por isso
# cada checagem usa uma frase exclusiva do cabeçalho daquele banco, nunca só
# o nome do banco isolado.
DETECTORES_PDF = [
    ("PagBank - Relatório de Vendas", lambda t: "relatório de vendas" in t.lower() and "pagbank" in t.lower(), pagbank_vendas),
    ("PagBank - Extrato da conta", lambda t: "pagseguro internet" in t.lower() and "extrato da conta" in t.lower(), pagbank_extrato),
    ("Banco do Brasil", lambda t: "extrato de conta corrente" in t.lower() and "agência" in t.lower() and "lote" in t.lower(), bb),
    ("Itaú", lambda t: "razão social" in t.lower() and "cnpj/cpf" in t.lower(), itau),
    ("Nubank", lambda t: "nubank.com.br" in t.lower() or "nu pagamentos" in t.lower(), nubank),
    ("Banco Inter", lambda t: "instituição: banco inter" in t.lower(), inter),
    ("Mercado Pago", lambda t: "mercadopago" in t.lower() or "id da operação" in t.lower(), mercadopago),
]


def detect_bank(text: str):
    """Retorna (nome_banco, modulo_parser) com base em palavras-chave no texto extraído."""
    for nome, checagem, modulo in DETECTORES_PDF:
        if checagem(text):
            return nome, modulo
    return None, None


# Para Excel não dá pra usar o texto: olhamos o conteúdo das primeiras linhas
# da planilha (crua) procurando uma pista exclusiva daquele relatório. Quem
# não casar com nenhum formato específico cai no parser genérico.
DETECTORES_EXCEL = [
    ("Rede - Relatório de Vendas", lambda t: "extrato para simples conferência" in t or ("valor líquido" in t and "status da venda" in t and "bandeira" in t), rede),
]


def detect_excel(df: pd.DataFrame):
    """Retorna (nome_formato, modulo_parser) olhando o conteúdo da planilha.
    Cai no parser genérico quando nenhum formato específico é reconhecido."""
    amostra = " ".join(str(c) for c in df.head(20).values.flatten()).lower()
    for nome, checagem, modulo in DETECTORES_EXCEL:
        if checagem(amostra):
            return nome, modulo
    return "Excel (genérico)", generic_excel
