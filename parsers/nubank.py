import re

from .base import Transaction, parse_valor_brl

MESES_ABREV = {
    "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04",
    "MAI": "05", "JUN": "06", "JUL": "07", "AGO": "08",
    "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12",
}

# Cada dia do extrato traz um "Total de entradas"/"Total de saídas" -- somar
# só essas linhas (em vez de cada Pix individual) é mais seguro: o Nubank tem
# muitos tipos de lançamento (Pix, boleto, compra, resgate...) e essa soma do
# dia já vem certa pronta, sem depender de eu conhecer todos os tipos.
TOTAL_DIA_RE = re.compile(
    r"^(?:(?P<dia>\d{2}) (?P<mes>[A-ZÇÃÕ]{3}) (?P<ano>\d{4})\s+)?"
    r"Total de (?P<tipo>entradas|sa[ií]das)\s*(?P<sinal>[+-])\s*(?P<valor>[\d.]*\d,\d{2})$"
)
TITULAR_RE = re.compile(
    r"^(?P<nome>[^\n]+)\nCPF\s+(?P<doc>[•\d./-]+)\s+Agência", re.MULTILINE
)


def extrair_titular(text: str):
    m = TITULAR_RE.search(text)
    if not m:
        return "", ""
    return m.group("nome").strip(), m.group("doc").strip()


def parse(text: str) -> list[Transaction]:
    # O resumo do topo do extrato também tem "Total de entradas"/"Total de
    # saídas" (o total do mês inteiro) -- cortamos tudo antes de
    # "Movimentações" pra não somar esse resumo de novo junto com os dias.
    partes = text.split("Movimentações", 1)
    corpo = partes[1] if len(partes) > 1 else text

    transacoes = []
    current_date = ""
    for linha in corpo.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        m = TOTAL_DIA_RE.match(linha)
        if not m:
            continue
        if m.group("dia"):
            mes = MESES_ABREV.get(m.group("mes"), "01")
            current_date = f"{m.group('dia')}/{mes}/{m.group('ano')}"
        valor = parse_valor_brl(m.group("valor"))
        if m.group("sinal") == "-":
            valor = -abs(valor)
        else:
            valor = abs(valor)
        tipo = "entrada" if m.group("tipo") == "entradas" else "saida"
        descricao = f"Total de {m.group('tipo')} do dia"
        transacoes.append(
            Transaction(date=current_date, description=descricao, value=valor, tipo=tipo)
        )
    return transacoes
