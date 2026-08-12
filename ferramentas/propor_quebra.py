# -*- coding: utf-8 -*-
"""Propõe quebrar em dois os slides longos demais — sem aplicar nada.

O PORQUÊ, na voz do Samuel (11/08/2026):

  "O louvor 108 ficou legal, mas ocupou muito espaço na tela. Talvez seria
   melhor separar. (...) O objetivo é sempre que sobre uma boa margem em cima
   e embaixo."

E ele tem razão: 1.278 louvores do catálogo têm slide de 7 linhas ou mais. Com
8 linhas o texto vai de ponta a ponta e a margem some.

COMO A QUEBRA É ESCOLHIDA
-------------------------
1. o CORO nunca é quebrado — ele é uma unidade, a igreja canta inteiro;
2. a quebra cai no MEIO, e daí procura o ponto de frase mais próximo (linha
   terminada em ponto, ponto-e-vírgula ou dois-pontos): é lá que a estrofe
   respira quando se canta;
3. nunca deixa pedaço de uma linha só;
4. slide de 6 ou menos fica como está.

Este arquivo NÃO mexe no dado. Ele grava a proposta em
`ferramentas/quebras_propostas.json` para o Samuel olhar e decidir.

    python ferramentas/propor_quebra.py            (relatório)
    python ferramentas/propor_quebra.py --aplicar  (só depois do "pode")
"""
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(AQUI, "dados", "louvores.js")
PROPOSTA = os.path.join(AQUI, "ferramentas", "quebras_propostas.json")
LIMITE = 7                      # a partir daqui a margem começa a sumir
FIM_DE_FRASE = re.compile(r"[.;:!?]\s*$")


def ponto_de_quebra(linhas):
    """Onde a estrofe respira, o mais perto possível do meio."""
    n = len(linhas)
    meio = n // 2
    melhor, dist = None, 99
    for i in range(2, n - 1):                     # nunca deixa pedaço de 1 linha
        if FIM_DE_FRASE.search(linhas[i - 1].replace("\x01", "")):
            d = abs(i - meio)
            if d < dist:
                melhor, dist = i, d
    return melhor or meio


def main():
    aplicar = "--aplicar" in sys.argv
    fonte = io.open(ARQ, encoding="utf-8").read()
    m = re.search(r"^(.*?=\s*)(\[.*\])(\s*;?\s*)$", fonte, re.S)
    dados = json.loads(m.group(2))

    proposta, tocados = [], 0
    for x in dados:
        novos = []
        mudou = False
        for sl in x.get("slides") or []:
            linhas = sl.get("linhas") or []
            rot = (sl.get("label") or "").strip()
            if len(linhas) < LIMITE or rot:        # coro inteiro, slide curto: passa
                novos.append(sl)
                continue
            i = ponto_de_quebra(linhas)
            novos.append({"label": sl.get("label", ""), "linhas": linhas[:i]})
            novos.append({"label": "", "linhas": linhas[i:]})
            mudou = True
            proposta.append({"num": x.get("num") or "AV", "titulo": x.get("titulo", ""),
                             "antes": linhas, "corte": i})
        if mudou:
            tocados += 1
            x["slides"] = novos

    with io.open(PROPOSTA, "w", encoding="utf-8") as f:
        json.dump({"limite": LIMITE, "louvores_tocados": tocados,
                   "slides_quebrados": len(proposta), "casos": proposta[:400]},
                  f, ensure_ascii=False, indent=1)
    print("louvores que ganhariam quebra : %d" % tocados)
    print("slides quebrados              : %d" % len(proposta))
    print("proposta gravada em           : ferramentas/quebras_propostas.json")

    if aplicar:
        novo = m.group(1) + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + m.group(3)
        io.open(ARQ, "w", encoding="utf-8").write(novo)
        print("APLICADO em dados/louvores.js")
    else:
        print("(nada foi aplicado — rode com --aplicar depois que o Samuel aprovar)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
