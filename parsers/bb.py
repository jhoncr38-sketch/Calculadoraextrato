import re

from .base import Transaction, parse_valor_brl, is_saldo_line

DATE_RE = re.compile(r"^(\d{2}/\d{2}/\d{4})$")
VALOR_RE = re.compile(r"([\d.]*\d,\d{2})\s*\(([+-])\)")
TITULAR_RE = re.compile(r"Cliente\s+([^\n]+)")
AGENCIA_CONTA_RE = re.compile(r"Agência:\s*(\S+)\s+Conta:\s*(\S+)")

# "BB Rende Fácil" é a aplicação/resgate automático: o banco move dinheiro
# sozinho entre a conta e uma aplicação. O que sai volta depois, então não é
# entrada nem saída de verdade e NÃO deve entrar na soma. Casamos a frase
# inteira (e não só "rende") pra não excluir por engano um Pix de alguém com
# nome parecido (ex.: "Renderson").
APLICACAO_AUTOMATICA = ("bb rende", "rende fácil", "rende facil")


def is_aplicacao_automatica(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(kw in texto_lower for kw in APLICACAO_AUTOMATICA)


def extrair_titular(text: str):
    """Retorna (nome_titular, documento). BB não imprime CNPJ/CPF neste layout,
    então usamos Agência/Conta como identificador no lugar do documento."""
    m_nome = TITULAR_RE.search(text)
    m_ag = AGENCIA_CONTA_RE.search(text)
    nome = m_nome.group(1).strip() if m_nome else ""
    documento = f"Agência {m_ag.group(1)} / Conta {m_ag.group(2)}" if m_ag else ""
    return nome, documento


def parse(text: str) -> list[Transaction]:
    transacoes = []
    current_date = ""
    for linha in text.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        m_data = DATE_RE.match(linha)
        if m_data:
            current_date = m_data.group(1)
            continue
        m_valor = VALOR_RE.search(linha)
        if not m_valor:
            continue
        if is_saldo_line(linha) or is_aplicacao_automatica(linha):
            continue
        valor = parse_valor_brl(m_valor.group(1))
        sinal = m_valor.group(2)
        if sinal == "-":
            valor = -valor
        descricao = linha[: m_valor.start()].strip() or "Lançamento BB"
        tipo = "entrada" if valor >= 0 else "saida"
        transacoes.append(
            Transaction(date=current_date, description=descricao, value=valor, tipo=tipo)
        )
    return transacoes
