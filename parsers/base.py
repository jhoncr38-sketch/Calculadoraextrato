import re
from dataclasses import dataclass

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

SALDO_KEYWORDS = (
    "saldo anterior",
    "saldo do dia",
    "saldo em conta corrente",
    "saldo total disponível dia",
    "saldo total disponivel dia",
    "saldo inicial",
    "saldo final",
)


@dataclass
class Transaction:
    date: str
    description: str
    value: float
    tipo: str  # "entrada" ou "saida"


def parse_valor_brl(raw: str) -> float:
    """Converte string monetária pt-BR ("1.234,56" ou "-27,00") para float."""
    raw = raw.strip().replace("R$", "").strip()
    negativo = raw.startswith("-")
    raw = raw.lstrip("+-").strip()
    raw = raw.replace(".", "").replace(",", ".")
    valor = float(raw)
    return -valor if negativo else valor


def formatar_documento(doc: str) -> str:
    """Formata uma string de dígitos como CPF (11) ou CNPJ (14)."""
    digitos = re.sub(r"\D", "", doc or "")
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    if len(digitos) == 14:
        return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
    return doc.strip()


def is_saldo_line(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(kw in texto_lower for kw in SALDO_KEYWORDS)


def _extrair_ano_mes(data_str: str):
    """Extrai (ano, mes) de uma data no formato DD/MM/AAAA ou DD-MM-AAAA."""
    if not data_str:
        return None
    partes = re.split(r"[/-]", data_str.strip())
    if len(partes) != 3:
        return None
    _, mes, ano = partes
    if len(ano) != 4 or not mes.isdigit() or not ano.isdigit():
        return None
    mes_int = int(mes)
    if mes_int not in MESES_PT:
        return None
    return int(ano), mes_int


def calcular_periodo(transacoes: list[Transaction]) -> str:
    """Calcula o(s) mês/ano do extrato a partir das datas dos lançamentos."""
    chaves = set()
    for t in transacoes:
        info = _extrair_ano_mes(t.date)
        if info:
            chaves.add(info)
    if not chaves:
        return ""
    ordenadas = sorted(chaves)
    labels = [f"{MESES_PT[mes]}/{ano}" for ano, mes in ordenadas]
    if len(labels) == 1:
        return labels[0]
    return f"{labels[0]} a {labels[-1]}"
