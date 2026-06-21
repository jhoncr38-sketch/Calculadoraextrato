import re

from .base import Transaction, parse_valor_brl, is_saldo_line, formatar_documento

DATE_PREFIX_RE = re.compile(r"^(\d{2}-\d{2}-\d{4})\b")
VALOR_PAIR_RE = re.compile(r"R\$\s*(-?[\d.]*\d,\d{2})\s+R\$\s*(-?[\d.]*\d,\d{2})$")
TITULAR_RE = re.compile(
    r"EXTRATO DE CONTA\n(?P<nome>[^\n]+)\nCPF/CNPJ:\s*(?P<doc>[\d./-]+)"
)


def extrair_titular(text: str):
    m = TITULAR_RE.search(text)
    if not m:
        return "", ""
    return m.group("nome").strip(), formatar_documento(m.group("doc"))


def parse(text: str) -> list[Transaction]:
    transacoes = []
    current_date = ""
    for linha in text.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        m_data = DATE_PREFIX_RE.match(linha)
        if m_data:
            current_date = m_data.group(1)
        if is_saldo_line(linha):
            continue
        m_valor = VALOR_PAIR_RE.search(linha)
        if not m_valor:
            continue
        valor = parse_valor_brl(m_valor.group(1))
        descricao = linha[: m_valor.start()].strip()
        descricao = DATE_PREFIX_RE.sub("", descricao).strip() or "Lançamento Mercado Pago"
        tipo = "entrada" if valor >= 0 else "saida"
        transacoes.append(
            Transaction(date=current_date, description=descricao, value=valor, tipo=tipo)
        )
    return transacoes
