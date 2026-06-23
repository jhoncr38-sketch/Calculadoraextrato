# Calculadora de Extrato — Guia do Projeto

## O que esse sistema faz

É um site simples (feito em Python, com a biblioteca Flask) onde a pessoa
sobe um ou mais extratos bancários (PDF ou Excel) e o sistema:

1. Descobre **qual banco** é o extrato, só lendo o texto do arquivo (sem o
   usuário precisar informar).
2. Lê todas as **transações** (entradas e saídas de dinheiro).
3. Soma tudo e mostra: total de entradas, total de saídas, saldo, período do
   extrato e o titular da conta (nome/CPF ou CNPJ), quando consegue achar.
4. Se for enviado mais de um arquivo de uma vez, mostra também o **total
   geral** somando todos.

Não tem banco de dados. Cada arquivo é lido na hora, processado na memória
do servidor, e depois é descartado. Nada fica guardado.

## Como o projeto está organizado (pastas e arquivos)

```
app.py                  -> o "coração" do site: rotas, formulário, resultado
extraction.py           -> extrai o texto bruto do PDF / linhas do Excel
parsers/
  __init__.py            -> decide QUAL banco é, lendo pistas no texto
  base.py                -> peças reutilizadas por todos os parsers
                            (formatar dinheiro, formatar CPF/CNPJ, calcular período...)
  bb.py                  -> regras específicas do Banco do Brasil
  itau.py                -> regras específicas do Itaú
  nubank.py              -> regras específicas do Nubank
  inter.py               -> regras específicas do Banco Inter
  mercadopago.py         -> regras específicas do Mercado Pago
  pagbank_vendas.py      -> regras do relatório de vendas do PagBank
  pagbank_extrato.py     -> regras do extrato da conta do PagBank/PagSeguro
  rede.py                -> regras do relatório de vendas da Rede (Excel)
  generic_excel.py       -> regra genérica para qualquer planilha Excel
templates/
  index.html             -> a página inicial (formulário de upload)
  results.html           -> a página que mostra o resultado da soma
modelos/                 -> extratos de exemplo reais, usados só para testar
                            localmente (NUNCA vai para o Git, é sigiloso)
test_modelos.py          -> script para testar todos os modelos de uma vez
requirements.txt         -> lista das bibliotecas Python que o projeto usa
.python-version          -> versão do Python usada (3.12)
```

## Como cada banco é "reconhecido" (detect_bank)

Em `parsers/__init__.py` existe uma lista de "pistas" — uma frase exclusiva
que só aparece no cabeçalho daquele banco. Por exemplo, o Banco do Brasil só
é identificado se o texto tiver "extrato de conta corrente" **e** "agência"
**e** "lote" juntos. Isso evita confusão: se um extrato do Nubank tiver um
Pix recebido de alguém do "Banco Inter", o sistema não pode confundir e
pensar que o extrato é do Inter — por isso a pista nunca é só o nome do
banco isolado, sempre uma frase típica do cabeçalho.

A ordem da lista importa: verificações mais específicas vêm primeiro.

Para arquivos **Excel** o reconhecimento é parecido, mas em vez de ler o texto
de um PDF, a função `detect_excel` olha o conteúdo das primeiras linhas da
planilha procurando uma pista exclusiva (lista `DETECTORES_EXCEL`). Quem não
casar com nenhum formato específico cai no parser genérico (`generic_excel`).

## Como adicionar um banco novo

Para um **PDF**:

1. Criar um arquivo novo dentro de `parsers/`, por exemplo `parsers/caixa.py`.
2. Esse arquivo precisa ter uma função `parse(texto) -> list[Transaction]`
   que lê o texto do PDF e devolve a lista de transações encontradas.
3. Opcionalmente, pode ter uma função `extrair_titular(texto)` que devolve
   o nome e o CPF/CNPJ do titular da conta.
4. Registrar esse banco na lista `DETECTORES_PDF` em `parsers/__init__.py`,
   com uma pista de texto exclusiva daquele banco.

Para um **Excel** é igual, com duas diferenças: a função `parse` recebe um
DataFrame do pandas (a planilha crua, sem cabeçalho fixo) em vez de texto, e o
registro é feito na lista `DETECTORES_EXCEL`, com uma pista que procura algo
exclusivo no conteúdo das primeiras linhas (ex.: o `rede.py` se identifica pela
frase "extrato para simples conferência"). A `extrair_titular`, se existir,
também recebe o DataFrame.

## Bancos/formatos já reconhecidos hoje

- Banco do Brasil
- Itaú
- Nubank
- Banco Inter
- Mercado Pago
- Relatório de Vendas do PagBank
- Extrato da conta do PagBank/PagSeguro
- Relatório de Vendas da Rede (Excel)
- Qualquer planilha Excel (formato genérico, baseado nos nomes das colunas)

## Comandos principais

Rodar o site no computador (modo de desenvolvimento):

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m flask --app app run --debug
```

Depois acessar `http://127.0.0.1:5000` no navegador.

Testar todos os extratos de exemplo da pasta `modelos/` de uma vez
(mostra no terminal banco detectado, número de transações e totais):

```bash
python test_modelos.py
```

## Como o site funciona por dentro (fluxo de uma requisição)

1. Usuário acessa `/` (rota `index` em `app.py`) e vê o formulário de upload
   (`templates/index.html`).
2. Usuário envia os arquivos, que vão para a rota `/upload` (método POST).
3. Para cada arquivo enviado, a função `processar_arquivo`:
   - Se for PDF: extrai o texto (`extraction.extract_pdf_text`), descobre o
     banco (`detect_bank`), e chama o `parse()` daquele banco.
   - Se for Excel: lê a planilha com pandas, descobre o formato
     (`detect_excel`) e chama o `parse()` correspondente (um parser específico,
     como o da Rede, ou o genérico como reserva).
   - Se der qualquer erro (arquivo corrompido, banco não reconhecido etc.),
     devolve uma mensagem amigável — o erro técnico de verdade só fica
     registrado no log do servidor, nunca é mostrado ao usuário.
4. Soma entradas e saídas de cada arquivo, calcula o saldo e o período.
5. Se houver mais de um arquivo válido, soma também o total geral de todos.
6. Mostra tudo na página de resultado (`templates/results.html`).

## Deploy (colocar o site no ar)

O projeto já está pronto para subir na Vercel sem nenhuma configuração
extra:

1. Importar o repositório no [vercel.com/new](https://vercel.com/new).
2. A Vercel reconhece automaticamente que é um projeto Python (pelo
   `requirements.txt`) e usa a variável `app` dentro de `app.py` como
   ponto de entrada.
3. A versão do Python usada é a do arquivo `.python-version` (3.12).
4. Clicar em "Deploy".

### Limites importantes

- **Tamanho do upload**: a Vercel só aceita até 4,5MB por requisição. O
  site já recusa de forma educada qualquer envio acima de 4MB
  (`app.config["MAX_CONTENT_LENGTH"]`), pedindo para enviar menos arquivos
  por vez.
- **Sem memória entre acessos**: nada é salvo. Cada upload é processado e
  jogado fora depois de mostrar o resultado.

## Segurança — regras que não podem ser quebradas

- A pasta `modelos/` tem extratos reais de pessoas/empresas e está no
  `.gitignore`. **Nunca** deve ser enviada para o Git/GitHub.
- O modo de depuração do Flask (`debug=True`) só liga se alguém definir a
  variável de ambiente `FLASK_DEBUG=1` manualmente. Em produção (Vercel)
  isso nunca acontece.
- Os arquivos enviados são processados **só na memória**, nunca são salvos
  em disco no servidor.
- Se der erro ao ler um arquivo, o usuário só vê uma mensagem genérica
  ("não foi possível ler este arquivo..."). O detalhe técnico completo do
  erro fica só no log do servidor — isso evita expor informação sensível
  por acidente.

## Bibliotecas usadas (requirements.txt)

- `Flask` — o framework que cria o site (rotas, formulário, páginas).
- `pdfplumber` — extrai o texto de dentro dos arquivos PDF.
- `pandas` — lê e organiza os dados das planilhas Excel.
- `openpyxl` — motor que o pandas usa por trás dos panos para ler `.xlsx`.
