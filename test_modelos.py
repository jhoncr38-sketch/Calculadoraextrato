import glob
from extraction import extract_pdf_text
from parsers import detect_bank

for caminho in sorted(glob.glob("modelos/*.pdf")):
    with open(caminho, "rb") as f:
        texto = extract_pdf_text(f)
    banco, modulo = detect_bank(texto)
    if modulo is None:
        print(f"{caminho}: BANCO NAO DETECTADO")
        continue
    transacoes = modulo.parse(texto)
    entradas = sum(t.value for t in transacoes if t.tipo == "entrada")
    saidas = sum(t.value for t in transacoes if t.tipo == "saida")
    print(f"{caminho}\n  banco={banco} n_transacoes={len(transacoes)} entradas={entradas:.2f} saidas={saidas:.2f} liquido={entradas+saidas:.2f}")
