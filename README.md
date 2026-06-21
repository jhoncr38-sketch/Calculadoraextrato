# Calculadora de Extrato

App web que recebe extratos bancários em PDF (ou Excel) e calcula o somatório de entradas, saídas e saldo — detectando automaticamente o banco pelo layout do documento, e identificando o titular/CNPJ-CPF da conta.

## Bancos reconhecidos hoje

- Banco do Brasil
- Itaú
- Banco Inter
- Mercado Pago
- Relatório de Vendas PagBank

Outros bancos podem ser adicionados criando um novo módulo em `parsers/` seguindo o padrão dos existentes (função `parse(texto) -> list[Transaction]` e, opcionalmente, `extrair_titular(texto)`).

## Rodando localmente

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python -m flask --app app run --debug
```

Acesse `http://127.0.0.1:5000`.

## Deploy na Vercel

Este projeto já está pronto para deploy na Vercel sem configuração extra:

1. Conecte este repositório no [dashboard da Vercel](https://vercel.com/new) (Import Git Repository).
2. A Vercel detecta o Python automaticamente pelo `requirements.txt` e usa `app.py` (variável `app`) como ponto de entrada — não é necessário `vercel.json`.
3. A versão do Python é fixada em `.python-version` (3.12).
4. Clique em Deploy.

### Limitações importantes a saber

- **Tamanho de upload**: a Vercel limita o corpo de cada requisição a **4,5MB**. O app já recusa de forma amigável qualquer envio acima de 4MB — para extratos grandes, envie em lotes menores.
- **Sem persistência**: nada é salvo em banco de dados; cada upload é processado na hora e descartado depois da resposta.

## Segurança

- A pasta `modelos/` (extratos de exemplo com dados reais de pessoas/CNPJ) está no `.gitignore` e **nunca deve ser versionada** nem enviada a um repositório, ainda mais se for público.
- O modo debug do Flask só liga se a variável de ambiente `FLASK_DEBUG=1` for definida explicitamente — nunca em produção.
- Arquivos são processados inteiramente em memória (nenhum upload é salvo em disco).
- Qualquer erro ao ler um arquivo retorna uma mensagem genérica ao usuário; o detalhe técnico fica só no log do servidor.
