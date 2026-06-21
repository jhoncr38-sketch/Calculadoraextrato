import re

from .base import Transaction, parse_valor_brl, is_saldo_line, formatar_documento

VALOR_RE = re.compile(r"(-?)R\$\s*([\d.]*\d,\d{2})")
TITULAR_RE = re.compile(
    r"^(?P<nome>[^\n]+)\nCPF/CNPJ:\s*(?P<doc>[\d./-]+)", re.MULTILINE
)


def extrair_titular(text: str):
    m = TITULAR_RE.search(text)
    if not m:
        return "", ""
    return m.group("nome").strip(), formatar_documento(m.group("doc"))
DATA_CABECALHO_RE = re.compile(
    r"^(\d{1,2}) de (\w+) de (\d{4})\b", re.IGNORECASE
)
MESES = {
    "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
    "abril": "04", "maio": "05", "junho": "06", "julho": "07",
    "agosto": "08", "setembro": "09", "outubro": "10",
    "novembro": "11", "dezembro": "12",
}


def parse(text: str) -> list[Transaction]:
    transacoes = []
    current_date = ""
    for linha in text.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        m_cab = DATA_CABECALHO_RE.match(linha)
        if m_cab:
            dia, mes_nome, ano = m_cab.groups()
            mes = MESES.get(mes_nome.lower(), "01")
            current_date = f"{int(dia):02d}/{mes}/{ano}"
        if is_saldo_line(linha):
            continue
        matches = list(VALOR_RE.finditer(linha))
        if not matches:
            continue
        primeiro = matches[0]
        sinal, numero = primeiro.groups()
        valor = parse_valor_brl(numero)
        if sinal == "-":
            valor = -valor
        descricao = linha[: primeiro.start()].strip().rstrip(":").strip() or "Lançamento Inter"
        tipo = "entrada" if valor >= 0 else "saida"
        transacoes.append(
            Transaction(date=current_date, description=descricao, value=valor, tipo=tipo)
        )
    return transacoes
