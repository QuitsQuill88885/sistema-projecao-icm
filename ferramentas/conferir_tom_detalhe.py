# -*- coding: utf-8 -*-
"""Abre cada suspeito de tom_divergente.json e mostra os dois lados lado a lado:
a letra da melodia, a letra da cifra e os acordes -- pra dar pra ver com os
olhos se e' o mesmo louvor mesmo, ou se casaram dois louvores homonimos.

    set PYTHONIOENCODING=utf-8
    python conferir_tom_detalhe.py
"""
from __future__ import unicode_literals

import io
import json
import os
import re
import sys
import unicodedata

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.join(os.environ.get("APPDATA", ""), "Sistema Projecao")
AQUI = os.path.dirname(os.path.abspath(__file__))
NOTA = re.compile(r"^[A-G][#b]?([\s|↑↓]|$)")


def so_letras(t):
    t = unicodedata.normalize("NFD", (t or "").upper())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]+", " ", t)).strip()


def letra_da_melodia(arq, quantas=6):
    d = json.load(io.open(os.path.join(BASE, "melodias", arq), encoding="utf-8"))
    saida = []
    for l in d["cadernos"]["C"]["linhas"]:
        if "n" in l:
            continue
        t = (l.get("t") or "").strip()
        if not t or t.lower().startswith("introdu") or NOTA.match(t):
            continue
        saida.append(t)
        if len(saida) >= quantas:
            break
    return saida


def main():
    sus = json.load(io.open(os.path.join(AQUI, "tom_divergente.json"), encoding="utf-8"))
    acordes = json.load(io.open(os.path.join(BASE, "cifras", "acordes.json"), encoding="utf-8"))
    mel = json.load(io.open(os.path.join(BASE, "melodias", "indice.json"),
                            encoding="utf-8"))["louvores"]
    melt = {so_letras(k): v for k, v in mel.items()}

    iguais = 0
    for d in sus:
        reg = acordes[d["chaves"][0]]
        m = melt.get(so_letras(d["titulo"]))
        lm = letra_da_melodia(m["arq"]) if m else []
        lc = [l["t"].strip() for l in reg.get("linhas", [])
              if l.get("t", "").strip()][:6]
        mesma = bool(lm and lc and so_letras(lm[0])[:18] and
                     any(so_letras(x)[:18] == so_letras(lm[0])[:18] for x in lc))
        iguais += 1 if mesma else 0
        print("=" * 74)
        print("%s   cifra=%s  melodia(C)=%s   acordes apoiam: %s   %s"
              % (d["titulo"], d["tom_cifra"], d["tom_melodia"],
                 d["quem_os_acordes_apoiam"],
                 "MESMO LOUVOR" if mesma else "*** CONFIRMAR: letra nao bate ***"))
        print("  melodia diz : " + " / ".join(lm[:3]))
        print("  cifra  diz  : " + " / ".join(lc[:3]))
        acs = [a[1] for l in reg.get("linhas", []) for a in l.get("a", [])]
        print("  acordes(%d)  : %s" % (len(acs), " ".join(acs[:16])))
        print("  ultimo      : %s" % (acs[-1] if acs else "-"))
    print("=" * 74)
    print("letra bate nos dois lados: %d de %d" % (iguais, len(sus)))


if __name__ == "__main__":
    main()
