import re

from .base import Transaction, parse_valor_brl, formatar_documento

TITULAR_RE = re.compile(r"^(?P<nome>[^\n]+)\nCNPJ:\s*(?P<doc>[\d./-]+)", re.MULTILINE)


def extrair_titular(text: str):
    m = TITULAR_RE.search(text)
    if not m:
        return "", ""
    return m.group("nome").strip(), formatar_documento(m.group("doc"))


LINHA_RE = re.compile(
    r"^(?P<data>\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}\s+Pagbank\b.*?"
    r"R\$\s*(?P<bruto>-?[\d.]*\d,\d{2})\s+"
    r"R\$\s*(?P<taxa>-?[\d.]*\d,\d{2})\s+"
    r"R\$\s*(?P<liquido>-?[\d.]*\d,\d{2})$"
)


def parse(text: str) -> list[Transaction]:
    transacoes = []
    for linha in text.splitlines():
        linha = linha.strip()
        m = LINHA_RE.match(linha)
        if not m:
            continue
        valor = parse_valor_brl(m.group("liquido"))
        transacoes.append(
            Transaction(
                date=m.group("data"),
                description="Venda recebida (líquido)",
                value=valor,
                tipo="entrada",
            )
        )
    return transacoes
