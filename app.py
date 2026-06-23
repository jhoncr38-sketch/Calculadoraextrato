import logging
import os
from datetime import datetime

from flask import Flask, render_template, request

from extraction import extract_pdf_text, extract_excel_rows
from parsers import detect_bank, detect_excel
from parsers.base import Transaction, calcular_periodo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4MB: a Vercel rejeita acima de 4,5MB por requisição

EXTENSOES_PDF = (".pdf",)
EXTENSOES_EXCEL = (".xlsx", ".xls")


def formatar_brl(valor: float) -> str:
    """Formata número no padrão brasileiro: ponto pro milhar, vírgula pros centavos."""
    texto = f"{valor:,.2f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


app.jinja_env.filters["brl"] = formatar_brl


@app.context_processor
def injetar_ano_atual():
    return {"ano_atual": datetime.now().year}


def processar_arquivo(file_storage):
    nome = file_storage.filename or "arquivo"
    extensao = os.path.splitext(nome)[1].lower()

    try:
        if extensao in EXTENSOES_PDF:
            texto = extract_pdf_text(file_storage)
            if not texto.strip():
                return {"arquivo": nome, "erro": "Não foi possível extrair texto do PDF."}
            banco, modulo = detect_bank(texto)
            if modulo is None:
                return {"arquivo": nome, "erro": "Layout de banco não reconhecido para este PDF."}
            transacoes = modulo.parse(texto)
            extrair_titular = getattr(modulo, "extrair_titular", None)
            titular, documento = extrair_titular(texto) if extrair_titular else ("", "")
        elif extensao in EXTENSOES_EXCEL:
            df = extract_excel_rows(file_storage)
            banco, modulo = detect_excel(df)
            transacoes = modulo.parse(df)
            extrair_titular = getattr(modulo, "extrair_titular", None)
            titular, documento = extrair_titular(df) if extrair_titular else ("", "")
        else:
            return {"arquivo": nome, "erro": "Formato de arquivo não suportado (use PDF ou Excel)."}
    except Exception:
        # Nunca expor o detalhe técnico do erro ao usuário (pode conter dados internos);
        # o detalhe completo vai só pro log do servidor, pra quem for investigar depois.
        logger.exception("Falha ao processar arquivo %s", nome)
        return {"arquivo": nome, "erro": "Não foi possível ler este arquivo (formato inesperado ou corrompido)."}

    if not transacoes:
        return {"arquivo": nome, "erro": "Nenhum lançamento foi identificado neste arquivo."}

    entradas = sum(t.value for t in transacoes if t.tipo == "entrada")
    saidas = sum(t.value for t in transacoes if t.tipo == "saida")
    return {
        "arquivo": nome,
        "banco": banco,
        "titular": titular,
        "documento": documento,
        "periodo": calcular_periodo(transacoes),
        "entradas": round(entradas, 2),
        "saidas": round(abs(saidas), 2),
        "saldo": round(entradas + saidas, 2),
        "transacoes": transacoes,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.errorhandler(413)
def arquivo_grande_demais(_erro):
    return render_template(
        "index.html",
        erro="O total enviado passou do limite de 4MB por envio. Envie menos arquivos por vez.",
    ), 413


@app.route("/upload", methods=["POST"])
def upload():
    arquivos = request.files.getlist("arquivos")
    arquivos = [f for f in arquivos if f and f.filename]

    if not arquivos:
        return render_template("index.html", erro="Selecione ao menos um arquivo.")

    resultados = [processar_arquivo(f) for f in arquivos]

    validos = [r for r in resultados if "erro" not in r]
    total_entradas = sum(r.get("entradas", 0) for r in validos)
    total_saidas = sum(r.get("saidas", 0) for r in validos)
    total_saldo = round(total_entradas - total_saidas, 2)

    return render_template(
        "results.html",
        resultados=resultados,
        mostrar_total_geral=len(validos) > 1,
        total_entradas=round(total_entradas, 2),
        total_saidas=round(total_saidas, 2),
        total_saldo=total_saldo,
    )


if __name__ == "__main__":
    # debug=True só liga se você ligar explicitamente no terminal (export FLASK_DEBUG=1).
    # Em produção (Vercel) este bloco nunca executa: a Vercel importa "app" direto.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
