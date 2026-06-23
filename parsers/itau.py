import re

from .base import Transaction, parse_valor_brl, is_saldo_line, formatar_documento

DATE_PREFIX_RE = re.compile(r"^(\d{2}/\d{2}/\d{4})\b")
VALOR_END_RE = re.compile(r"(-?[\d.]*\d,\d{2})$")
TITULAR_RE = re.compile(r"^(?P<nome>.+?)\s+CNPJ\s+(?P<doc>[\d./-]+)\s+Agência", re.MULTILINE)


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
        # Linhas antes da primeira data são cabeçalho (resumo de saldo/limite
        # da conta, ex.: "R$ 0,00 R$ 27.000,00 R$ 0,00 R$ 27.000,00").
        # Não são lançamentos e não podem ser somados.
        if not current_date:
            continue
        if is_saldo_line(linha):
            continue
        m_valor = VALOR_END_RE.search(linha)
        if not m_valor:
            continue
        valor = parse_valor_brl(m_valor.group(1))
        descricao = linha[: m_valor.start()].strip()
        descricao = DATE_PREFIX_RE.sub("", descricao).strip() or "Lançamento Itaú"
        tipo = "entrada" if valor >= 0 else "saida"
        transacoes.append(
            Transaction(date=current_date, description=descricao, value=valor, tipo=tipo)
        )
    return transacoes
