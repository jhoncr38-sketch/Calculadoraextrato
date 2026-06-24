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


# "Pix - Rejeitado" / "Erro. Pix não efetuado": é um Pix que deu erro e NÃO foi
# concluído -- o dinheiro não entrou (nem saiu) de verdade. Então não pode contar
# como recebido. "Rejeitado" só aparece nesses casos, nunca num Pix de verdade.
PIX_NAO_REALIZADO = ("rejeitado", "não efetuado", "nao efetuado")


def is_pix_nao_realizado(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(kw in texto_lower for kw in PIX_NAO_REALIZADO)


# 9903 é o lote (código) que o Banco do Brasil usa SÓ para o "BB Rende Fácil".
# Em alguns extratos a linha do valor vem sem o texto, só com esse código
# (ex.: "9903 584,00 (+)"). Como nenhuma transação normal usa o lote 9903,
# quando ele abre a linha do valor é aplicação automática e não entra na soma.
LOTE_RENDE_FACIL = "9903"


def is_lote_rende_facil(linha: str) -> bool:
    partes = linha.split()
    return bool(partes) and partes[0] == LOTE_RENDE_FACIL


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
    linhas = [l.strip() for l in text.splitlines() if l.strip()]
    for i, linha in enumerate(linhas):
        m_data = DATE_RE.match(linha)
        if m_data:
            current_date = m_data.group(1)
            continue
        m_valor = VALOR_RE.search(linha)
        if not m_valor:
            continue
        # O texto que identifica a linha ("BB Rende Fácil", "Pix - Rejeitado")
        # às vezes cai na linha de cima do valor (depende de como o PDF é lido),
        # então analisamos a linha do valor JUNTO com a linha logo acima.
        anterior = linhas[i - 1] if i > 0 else ""
        contexto = anterior + " " + linha
        if (
            is_saldo_line(linha)
            or is_lote_rende_facil(linha)
            or is_aplicacao_automatica(contexto)
            or is_pix_nao_realizado(contexto)
        ):
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
