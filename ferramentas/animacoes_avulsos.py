# -*- coding: utf-8 -*-
"""Animacao dos AVULSOS das CIAS (os "AV - ..." da pasta do RAR), ligada pela CHAVE.

Por que existe (05/10/2026): quatro louvores da Evangelizacao das CIAs sao
avulsos — Fui lavado no sangue do Cordeiro, Eu clamo eu oro, Esta e a mensagem
eterna de Deus, Conhecamos e prossigamos — e o RAR tem PowerPoint animado de
todos, mas o Sistema so procurava animacao para a CIA 2018 (pelo numero).
Avulso nao tem numero que preste ("AV"), entao a ligacao e pela CHAVE do louvor
(num|TITULO|1a linha da 1a tela), a mesma que liga cifra e selo.

Cada PowerPoint e casado com o louvor do Sistema PELA LETRA (>= 85% nos dois
sentidos). Sem par seguro, fica de fora e vai para o relatorio.

Uso:  python animacoes_avulsos.py <pasta_dos_pptx> <pasta_de_saida>
"""
import difflib
import io
import json
import os
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animacoes_do_pptx as AN  # noqa: E402

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
MINIMO = 0.85
# Pares que a regua nao alcanca mas que a CONFERENCIA ABSOLUTA provou (05/10/2026):
# o PowerPoint do "Eu clamo, eu oro" escreve BIS onde o telao repete as linhas
# por extenso, e a letra cai a 77%. A lista cifrada oficial chama de "242"; no
# Sistema e Avulsos 2024 579 (letra 99%/100% contra a lista oficial).
NA_MAO = {"AV - EU CLAMO, EU ORO - 16.9.pptx": ("Avulsos 2024", "579")}


def palavras(t):
    t = "".join(c for c in unicodedata.normalize("NFD", t or "") if unicodedata.category(c) != "Mn").upper()
    t = re.sub(r"\u0001[^\u0001]*\u0001", " ", t)
    t = re.sub(r"\b(BIS|\d\s*X|FIM|CORO|INDICE)\b", " ", t)
    return re.sub(r"[^A-Z0-9 ]+", " ", t).split()


def letra_pptx(cam):
    out = []
    with zipfile.ZipFile(cam) as z:
        for n in z.namelist():
            if re.match(r"^ppt/slides/slide\d+\.xml$", n):
                for t in ET.fromstring(z.read(n)).iter(A + "t"):
                    out.append(t.text or "")
    return palavras(" ".join(out))


def cob(a, b):
    if not a:
        return 0.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(x.size for x in sm.get_matching_blocks()) / float(len(a))


def chave(s):
    return "%s|%s|%s" % (s["num"], s["titulo"], s["slides"][0]["linhas"][0] if s["slides"] and s["slides"][0]["linhas"] else "")


def slug(t):
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40]


def main():
    origem, destino = sys.argv[1], sys.argv[2]
    t = io.open(os.path.join(APP, "dados", "louvores.js"), encoding="utf-8").read()
    arr = json.loads(t[t.index("["):t.rindex("]") + 1])
    for s in arr:
        s["_p"] = palavras(" ".join(" ".join(sl["linhas"]) for sl in s["slides"]))
    arq_rel = os.path.join(destino, "relatorio.json")
    relatorio = json.load(io.open(arq_rel, encoding="utf-8")) if os.path.exists(arq_rel) else {}
    AN.fecha_os_meus(origem)

    sem_par = []
    for n in sorted(os.listdir(origem)):
        if not n.lower().endswith(".pptx") or re.match(r"^\d+\s*-", n) or n.startswith("~$"):
            continue
        cam = os.path.join(origem, n)
        try:
            p = letra_pptx(cam)
        except zipfile.BadZipFile:
            sem_par.append((n, "arquivo estragado"))
            continue
        melhor = None
        if n in NA_MAO:
            col, num = NA_MAO[n]
            s_mao = [s for s in arr if s["col"] == col and str(s["num"]) == num]
            if len(s_mao) == 1:
                melhor = (1.0, s_mao[0])
        for s in (arr if melhor is None else []):
            if not s["_p"] or not (set(p[:15]) & set(s["_p"][:40])):
                continue
            c1 = cob(s["_p"], p)            # quanto do telao esta no PowerPoint
            if c1 < 0.5:
                continue
            c2 = cob(p, s["_p"])
            nota = min(c1, c2)
            if melhor is None or nota > melhor[0]:
                melhor = (nota, s)
        if not melhor or melhor[0] < MINIMO:
            sem_par.append((n, "melhor par %.0f%%" % (100 * melhor[0]) if melhor else "nenhum par"))
            continue
        nota, s = melhor
        if s["col"] == "CIA 2018":
            sem_par.append((n, "e o CIA %s, que ja tem o PowerPoint numerado" % s["num"]))
            continue
        k = "chave:" + chave(s)
        titulo = re.sub(r"^AV\s*-\s*|\s*-?\s*16[.,]9|\.pptx$", "", n, flags=re.I).strip()
        try:
            rel = AN.monta_louvor(cam, destino, nome="av-" + slug(titulo), titulo=titulo)
            rel["par_no_sistema"] = "%s %s · %s (letra %.0f%%)" % (s["col"], s["num"], s["titulo"], 100 * nota)
        except Exception as e:
            AN.esquece_powerpoint()
            rel = {"louvor": titulo, "erro": "%s: %s" % (type(e).__name__, e), "telas": []}
        relatorio[k] = rel
        with io.open(arq_rel + ".tmp", "w", encoding="utf-8") as g:
            json.dump(relatorio, g, ensure_ascii=False, indent=1)
        os.replace(arq_rel + ".tmp", arq_rel)
        anim = sum(1 for x in rel.get("telas", []) if x.get("quadros", 1) > 1)
        print("%-44s -> %-48s %s" % (n[:44], rel.get("par_no_sistema", "")[:48],
                                     rel.get("erro") or "%d telas, %d animadas" % (len(rel["telas"]), anim)))
        sys.stdout.flush()
    AN.escreve_indice(destino, relatorio)
    print()
    print("SEM PAR SEGURO (ficaram de fora): %d" % len(sem_par))
    for n, por in sem_par:
        print("   %-50s %s" % (n[:50], por))


if __name__ == "__main__":
    main()
