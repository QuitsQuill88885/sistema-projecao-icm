# -*- coding: utf-8 -*-
"""Confere DUAS leituras de OCR contra a Tonalidade impressa na propria pagina.

O extrator hoje troca "P" por "E" (consertar_ocr) e nao tem regra nenhuma para o
"o". A pergunta e' se essas escolhas cabem no tom que o livro imprimiu:

    "Pm"  e' "Em" ou e' "F#m"?
    "Com" e' lixo  ou e' "C#m"?

O juiz nao sou eu: e' a linha "Tonalidade:" da mesma pagina, que o OCR quase
nunca estraga. Para cada ocorrencia, conto de que lado a leitura cai dentro do
campo harmonico do tom impresso.

SO OLHA LINHA QUE JA E' DE ACORDE. Sem essa trava as palavras portuguesas
"com", "bom", "dom", "ao" entram na conta e estragam a medida.

Uso:  python auditar_p_e_sustenido.py
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extrair_cifras as E  # noqa: E402

NOTA = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
        "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10,
        "Bb": 10, "B": 11}


def campo(tom):
    """Os pares (altura, qualidade) que cabem no tom, com dominante secundaria.

    Nao e' teoria de conservatorio: e' a lista do que um hino publicado nesse
    tom realmente usa. Sem as dominantes secundarias o juiz reprovaria arranjo
    bom e a medida viraria ruido.
    """
    t = tom.split(",")[0].split("/")[0].strip()
    menor = t.endswith("m")
    r = NOTA.get(t[:-1] if menor else t)
    if r is None:
        return None
    if menor:
        graus = [(0, "m"), (2, "dim"), (3, "M"), (5, "m"), (7, "M"), (7, "m"),
                 (8, "M"), (10, "M")]
    else:
        graus = [(0, "M"), (2, "m"), (4, "m"), (5, "M"), (7, "M"), (9, "m"),
                 (11, "dim")]
    ok = set(((r + g) % 12, q) for g, q in graus)
    # dominante secundaria: acorde MAIOR uma quinta acima de cada grau
    for g, _q in graus:
        ok.add(((r + g + 7) % 12, "M"))
    return ok


RAIZ_AC = re.compile(r"^([A-G](?:#|b)?)(.*)$")


def par(nome):
    m = RAIZ_AC.match(nome or "")
    if not m:
        return None
    resto = m.group(2).split("/")[0]
    if resto.startswith("m") and not resto.startswith("maj"):
        q = "m"
    elif resto[:3] in ("dim",) or resto[:1] in ("°", "º"):
        q = "dim"
    else:
        q = "M"
    return (NOTA.get(m.group(1)), q)


def cabe(nome, ok):
    p = par(nome)
    return bool(p and p[0] is not None and p in ok)


TOK_P = re.compile(r"^P(m|7|m7|M|maj7|sus4|9|6|m6|m9)?$")
TOK_O = re.compile(r"^([A-G])o(m|m7|7|M|maj7|sus4|9|6|m6)?$")


def main():
    pdf = [f for f in glob.glob(os.path.join(E.pasta_cifras(), "*.pdf"))
           if "2018" in f]
    if not pdf:
        raise SystemExit("nao achei a Coletanea 2018")
    from pypdf import PdfReader
    r = PdfReader(pdf[0])

    c = Counter()
    exemplos = {"P": [], "o": []}
    for p in range(len(r.pages)):
        try:
            frags = E.fragmentos(r.pages[p])
        except Exception:
            continue
        if not frags:
            continue
        linhas = E.linhas_da_pagina(frags)
        cabs = E.cabecalhos_por_tonalidade(linhas)
        if not cabs:
            continue
        # tom de cada bloco
        blocos = []
        for k, (ini, _num, tit) in enumerate(cabs):
            fim = cabs[k + 1][0] if k + 1 < len(cabs) else len(linhas)
            tom = None
            for _col, _y, fs in linhas[ini:fim]:
                m = E.SO_TOM.search(E.texto_da_linha(fs))
                if m:
                    tom = m.group(1).strip()
                    break
            blocos.append((ini, fim, tom, tit))

        for ini, fim, tom, tit in blocos:
            ok = campo(tom) if tom else None
            if not ok:
                continue
            for _col, _y, fs in linhas[ini:fim]:
                toks = E.tokens_com_x(fs)
                if not toks:
                    continue
                # A TRAVA: a linha ja tem que parecer de acorde SEM as duas
                # leituras em julgamento, senao a medida se auto-confirma.
                bons = sum(1 for _x, w in toks if E.eh_acorde(w.strip("|")))
                if bons < max(2, len(toks) * 0.5):
                    continue
                if not any(E.negrito(f[3]) for f in fs):
                    continue
                for _x, w in toks:
                    w = w.strip("|")
                    m = TOK_P.match(w)
                    if m:
                        c["P_total"] += 1
                        e = "E" + (m.group(1) or "")
                        f = "F#" + (m.group(1) or "")
                        ce, cf = cabe(e, ok), cabe(f, ok)
                        if ce and not cf:
                            c["P_so_E"] += 1
                        elif cf and not ce:
                            c["P_so_Fsus"] += 1
                            if len(exemplos["P"]) < 6:
                                exemplos["P"].append(
                                    (p + 1, tit[:34], tom, E.texto_da_linha(fs)[:60]))
                        elif ce and cf:
                            c["P_ambos"] += 1
                        else:
                            c["P_nenhum"] += 1
                    m = TOK_O.match(w)
                    if m:
                        c["o_total"] += 1
                        sus = m.group(1) + "#" + (m.group(2) or "")
                        dim = m.group(1) + "°" + (m.group(2) or "")
                        cs, cd = cabe(sus, ok), cabe(dim, ok)
                        if cs and not cd:
                            c["o_so_sustenido"] += 1
                            if len(exemplos["o"]) < 6:
                                exemplos["o"].append(
                                    (p + 1, tit[:34], tom, E.texto_da_linha(fs)[:60]))
                        elif cd and not cs:
                            c["o_so_dim"] += 1
                        elif cs and cd:
                            c["o_ambos"] += 1
                        else:
                            c["o_nenhum"] += 1

    print("\nTOKEN 'P' em linha de acorde  (hoje o extrator le como E)")
    print("  ocorrencias                    : %d" % c["P_total"])
    print("  so' F# cabe no tom da pagina   : %d" % c["P_so_Fsus"])
    print("  so' E  cabe no tom da pagina   : %d" % c["P_so_E"])
    print("  os dois cabem (nao decide)     : %d" % c["P_ambos"])
    print("  nenhum cabe                    : %d" % c["P_nenhum"])
    if c["P_so_E"]:
        print("  --> F# ganha de E por %.1f para 1" % (c["P_so_Fsus"] / float(c["P_so_E"])))
    for e in exemplos["P"]:
        print("     pg %-4d %-34s tom %-4s | %s" % e)

    print("\nTOKEN 'Xo'/'Xom' em linha de acorde  (hoje o extrator JOGA FORA)")
    print("  ocorrencias                    : %d" % c["o_total"])
    print("  so' '#' cabe no tom da pagina  : %d" % c["o_so_sustenido"])
    print("  so' diminuto cabe              : %d" % c["o_so_dim"])
    print("  os dois cabem                  : %d" % c["o_ambos"])
    print("  nenhum cabe                    : %d" % c["o_nenhum"])
    for e in exemplos["o"]:
        print("     pg %-4d %-34s tom %-4s | %s" % e)
    print()


if __name__ == "__main__":
    main()
