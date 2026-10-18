# -*- coding: utf-8 -*-
"""CIFRA SÓ SE FOR VERIFICADA (pedido dele, 18/10/2026 13h08: "Se o louvor não tiver uma cifra verificada, nem
apareça o botão de cifra"). Gera dados/cifras_ocultas.json = {chave: motivo}, que o servidor tira do catálogo do
músico (catalogo_do_musico): some o botão no painel E no celular do músico.

Duas regras, decididas pela HD em 18/10 15h48:
1. AUTOMÁTICA: a cifra cobre menos de 90% da letra do telão (a régua oficial, cobertura_de_um do
   refazer_conteudo_zip.py, a mesma do conta_ruins.py). Abaixo disso é cifra incompleta ou de outro louvor.
2. À MÃO: dados/cifras_lista_negra.json = {chave: "motivo, data"}. O que ele ou o músico reprovar e a régua não vê
   (OCR quebrado, acorde errado). Para DESFAZER: tirar a linha da lista e rodar este script de novo.

Uso:  python ferramentas\\gera_cifras_ocultas.py            (mostra o que some, não grava)
      python ferramentas\\gera_cifras_ocultas.py --gravar
"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from refazer_conteudo_zip import cobertura_de_um, BANCO_APP, LOUVORES_JS

MINIMO = 0.90
NEGRA = os.path.join(APP, "dados", "cifras_lista_negra.json")
SAIDA = os.path.join(APP, "dados", "cifras_ocultas.json")


def main():
    b = open(LOUVORES_JS, encoding="utf-8").read().strip()
    louvores = json.loads(b[b.index("=") + 1:].rstrip(";"))
    banco = json.load(open(BANCO_APP, encoding="utf-8"))
    negra = json.load(open(NEGRA, encoding="utf-8")) if os.path.exists(NEGRA) else {}
    ocultas, linhas = {}, []
    for s in louvores:
        if not s.get("slides") or not s["slides"][0].get("linhas"):
            continue
        ch = "%s|%s|%s" % (s.get("num", ""), s["titulo"], s["slides"][0]["linhas"][0])
        if ch not in banco:
            continue
        c = cobertura_de_um(s, banco)
        motivo = None
        if ch in negra:
            motivo = "lista negra: " + negra[ch]
        elif c is not None and c < MINIMO:
            motivo = "cobre %d%% da letra (mínimo %d%%)" % (round(100 * c), round(100 * MINIMO))
        if motivo:
            ocultas[ch] = motivo
            linhas.append((s.get("col", ""), s.get("num", ""), s["titulo"], motivo, c))
    sobra = [k for k in negra if k not in banco]
    print("cifras no banco: %d | somem: %d (régua: %d, lista negra: %d)" % (
        len(banco), len(ocultas), sum(1 for x in linhas if not x[3].startswith("lista")), sum(1 for x in linhas if x[3].startswith("lista"))))
    if sobra:
        print("ATENÇÃO: chaves da lista negra que não existem no banco:", sobra)
    if "--gravar" in sys.argv:
        json.dump(ocultas, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
        print("gravado:", SAIDA)
    if "--lista" in sys.argv:
        for col, num, tit, mot, c in sorted(linhas, key=lambda x: (x[4] if x[4] is not None else 9)):
            print("%-18s %-6s %-46s | %s" % (col[:18], num, tit[:46], mot))


if __name__ == "__main__":
    main()
