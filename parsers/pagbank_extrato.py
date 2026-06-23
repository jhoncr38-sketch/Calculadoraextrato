import re

from .base import Transaction, parse_valor_brl, formatar_documento, is_saldo_line

# Este é o "Extrato da conta" do PagBank/PagSeguro (movimentação da conta,
# tipo conta corrente) -- diferente do "Relatório de Vendas" (pagbank_vendas.py),
# que lista venda por venda. Aqui cada linha é um lançamento com data,
# descrição e valor; quando o valor vem com "-R$" é saída, com "R$" é entrada.
TITULAR_RE = re.compile(
    r"PagSeguro Internet S/A\n(?P<nome>[^\n]+)\n.*?CNPJ:\s*(?P<doc>[\d./-]+)",
    re.DOTALL,
)

# Ex.: "21/05/2026 Vendas - Disponivel DEBITO MASTERCARD R$ 11,93"
#      "23/05/2026 Pix enviado - E De S Feitosa -R$ 826,05"
LINHA_RE = re.compile(
    r"^(?P<data>\d{2}/\d{2}/\d{4})\s+(?P<desc>.+?)\s+"
    r"(?P<sinal>-?)R\$\s*(?P<valor>[\d.]*\d,\d{2})$"
)


def extrair_titular(text: str):
    m = TITULAR_RE.search(text)
    if not m:
        return "", ""
    return m.group("nome").strip(), formatar_documento(m.group("doc"))


def parse(text: str) -> list[Transaction]:
    transacoes = []
    for linha in text.splitlines():
        linha = linha.strip()
        m = LINHA_RE.match(linha)
        if not m:
            continue
        descricao = m.group("desc").strip()
        # "Saldo do dia" é só um resumo do saldo, não um movimento de dinheiro.
        if is_saldo_line(descricao):
            continue
        valor = parse_valor_brl(m.group("valor"))
        if m.group("sinal") == "-":
            valor = -abs(valor)
            tipo = "saida"
        else:
            valor = abs(valor)
            tipo = "entrada"
        transacoes.append(
            Transaction(date=m.group("data"), description=descricao, value=valor, tipo=tipo)
        )
    return transacoes
