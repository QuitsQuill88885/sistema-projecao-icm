# -*- coding: utf-8 -*-
"""Reaplica os consertos manuais no dados/louvores.js.

POR QUE: o louvores.js e' GERADO (gen_louvores.py). Os consertos feitos a mao
(143 TENHO UMA CANDEIA com o coro completo; 218 MARANATA com a linha DESPERTA
e o 2x como selo) seriam PERDIDOS numa regeneracao. Este script poe de volta.

QUANDO RODAR: sempre, logo depois de gen_louvores.py. Nao faz mal rodar a toa:
se os slides ja estao certos, nao muda nada.
"""
import io, json, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
LJS = os.path.join(RAIZ, "dados", "louvores.js")
CON = os.path.join(RAIZ, "dados", "consertos_louvores.json")


def io_json_acrescimos():
    return json.load(io.open(CON, encoding="utf-8")).get("acrescimos", [])


def main():
    consertos = json.load(io.open(CON, encoding="utf-8"))["consertos"]
    s = io.open(LJS, encoding="utf-8").read()
    pref = s[:s.index("=") + 1]
    L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    lista = L.get("louvores") if isinstance(L, dict) else L
    mudou = 0
    for c in consertos:
        for l in lista:
            if (str(l.get("num")) == str(c["num"]) and l.get("col") == c["col"]
                    and (l.get("titulo") or "").strip() == c["titulo"].strip()):
                if l.get("slides") != c["slides"]:
                    l["slides"] = c["slides"]
                    mudou += 1
                break
    # ACRESCIMOS (26/09/2026): louvor que nao existe em livro nenhum desta maquina,
    # entrado de fonte de fora (acrescenta_louvor_de_fora.py). O gen_louvores.py nao
    # sabe dele, entao sem isto ele SUMIRIA na proxima regeneracao.
    acrescentados = 0
    for c in io_json_acrescimos():
        existe = any(str(l.get("num")) == str(c["num"]) and l.get("col") == c["col"]
                     and (l.get("titulo") or "").strip() == c["titulo"].strip() for l in lista)
        if not existe:
            lista.append({"num": c["num"], "titulo": c["titulo"], "col": c["col"],
                          "slides": c["slides"]})
            acrescentados += 1
            mudou += 1
    if acrescentados:
        print("louvores acrescentados:", acrescentados)
    if mudou:
        tmp = LJS + ".tmp"
        io.open(tmp, "w", encoding="utf-8").write(
            pref + " " + json.dumps(L, ensure_ascii=False, separators=(",", ":")) + ";")
        os.replace(tmp, LJS)
    print("consertos reaplicados:", mudou, "(0 = ja estava tudo certo)")


if __name__ == "__main__":
    main()
