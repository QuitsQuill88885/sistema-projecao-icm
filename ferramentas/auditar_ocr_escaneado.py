# -*- coding: utf-8 -*-
"""Prova, contra a Tonalidade impressa, que duas regras do extrator erram.

POR QUE ESTE ARQUIVO EXISTE
===========================
auditar_campo_harmonico.py acha os acordes que nao cabem no tom. Ele diz ONDE
esta' o estrago. Este aqui diz DE ONDE ELE VEM, e prova com o proprio livro.

O truque: cada pagina da Coletanea 2018 imprime "Tonalidade: X". Essa palavra
sobrevive ao OCR (1.008 ocorrencias em 450 paginas). Entao da' para pegar um
token estragado, propor duas leituras, e perguntar ao tom da PROPRIA PAGINA
qual das duas e' acorde do campo. Onde as duas leituras cabem, o teste nao
decide e e' descartado; so' conta onde uma cabe e a outra nao.

AS DUAS REGRAS
--------------
1) extrair_cifras.consertar_ocr() troca "P" por "E", entao "Pm" vira "Em" e e'
   ACEITO. Mas na pagina 38, louvor 102, tom de Mi, esta' escrito
   "Com  Pm  B  E" -- que e' C#m F#m B E, o vi-ii-V-I de Mi. Ali "Pm" e' F#m,
   nao Em. A regra nao perde o acorde: ela PLANTA um acorde errado, e o
   plantado cai fora do campo do proprio tom.

2) O OCR le o "#" como "o": "Com"=C#m, "Fom"=F#m, "Gom"=G#m. Nao existe regra
   o->#, entao eh_acorde() recusa e o acorde SOME da cifra.

So' conta token em linha de acorde (>=60% dos tokens ja' sao acorde). Sem esse
filtro, as palavras portuguesas "com", "dom", "bom", "ao" entram na conta e
estragam a medida.

Uso:  python auditar_ocr_escaneado.py
"""
import collections
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auditar_campo_harmonico as A          # noqa: E402

RE_TON = re.compile(r"Tonalidade\s*:?\s*([A-G][#b]?m?)")
RE_O = re.compile(r"^([A-G])o(m7|m|7)?$")
RE_P = re.compile(r"^P(m7|m|7)?$")
SUSPEITO = re.compile(r"^(P(m7|m|7)?|[A-G]o(m7|m|7)?)$")


def linha_de_acorde(toks):
    if len(toks) < 2:
        return False
    bons = sum(1 for t in toks if A.ler_acorde(t) or SUSPEITO.match(t))
    return bons / len(toks) >= 0.6


def julgar(cand_a, cand_b, tom):
    """'so A', 'so B', 'os dois' ou 'nenhum' — quem cabe no campo do tom."""
    a, b = A.ler_acorde(cand_a), A.ler_acorde(cand_b)
    ca = bool(a and A.dentro(a, tom))
    cb = bool(b and A.dentro(b, tom))
    return ("so A" if ca and not cb else "so B" if cb and not ca
            else "os dois" if ca else "nenhum")


def main():
    from pypdf import PdfReader
    base = os.path.join(os.environ.get("APPDATA", ""), "Sistema Projecao", "cifras")
    alvos = [f for f in os.listdir(base) if f.endswith(".pdf") and "2018" in f]
    if not alvos:
        print("Coletanea 2018 nao encontrada em %s" % base)
        return
    caminho = os.path.join(base, alvos[0])
    print("livro: %s" % alvos[0])
    r = PdfReader(caminho)

    p, o = collections.Counter(), collections.Counter()
    nomes_o, tokens_p, exemplos = collections.Counter(), 0, collections.defaultdict(list)

    for pag in r.pages:
        try:
            txt = pag.extract_text() or ""
        except Exception:
            continue
        tom = None
        for linha in txt.splitlines():
            mt = RE_TON.search(linha)
            if mt:
                tom = A.ler_tom(mt.group(1))
                continue
            toks = [w.strip("|¡,.;:") for w in re.split(r"[\s\t]+", linha.strip())]
            toks = [t for t in toks if t]
            if not linha_de_acorde(toks):
                continue
            for w in toks:
                m = RE_P.match(w)
                if m:
                    tokens_p += 1
                    if tom:
                        suf = m.group(1) or ""
                        v = julgar("E" + suf, "F#" + suf, tom)
                        p[v] += 1
                        if v in ("so A", "so B") and len(exemplos[v]) < 4:
                            exemplos[v].append("%s na pagina em %s"
                                               % (w, A.nome_tom(tom)))
                m = RE_O.match(w)
                if m:
                    nomes_o[w] += 1
                    if tom:
                        letra, suf = m.group(1), m.group(2) or ""
                        o[julgar(letra + "#" + suf,
                                 letra + "°" + suf, tom)] += 1

    print()
    print("REGRA 1 — consertar_ocr() escreve 'E' onde o token e' 'P'")
    print("  tokens 'P'/'Pm' em linha de acorde: %d" % tokens_p)
    print("  onde SO' UMA leitura cabe no tom impresso:")
    print("     lendo como F# (nao e' o que o extrator faz) ... %d" % p["so B"])
    print("     lendo como E  (o que o extrator faz hoje) ..... %d" % p["so A"])
    if p["so A"]:
        print("     -> F# ganha de E por %.1f para 1" % (p["so B"] / p["so A"]))
    print("     (as duas cabem: %d; nenhuma: %d — nao decidem)"
          % (p["os dois"], p["nenhum"]))
    for ex in exemplos["so B"][:3]:
        print("     ex: %s" % ex)

    print()
    print("REGRA 2 — o '#' lido como 'o', e nao ha' regra o->#")
    print("  tokens 'Xo'/'Xom' em linha de acorde: %d" % sum(nomes_o.values()))
    print("     " + ", ".join("%s(%d)" % kv for kv in nomes_o.most_common(10)))
    print("  onde SO' UMA leitura cabe no tom impresso:")
    print("     lendo o 'o' como '#' ... %d" % o["so A"])
    print("     lendo o 'o' como '°' ... %d" % o["so B"])
    print("     (as duas: %d; nenhuma: %d)" % (o["os dois"], o["nenhum"]))
    print()
    print("  hoje o extrator joga TODOS esses %d fora:" % sum(nomes_o.values()))
    import extrair_cifras as E
    for w in ("Com", "Fom", "Gom", "Pm"):
        c = E.consertar_ocr(w)
        print("     %-5s -> %-5s  %s"
              % (w, c, "ACEITO" if E.eh_acorde(c) else "jogado fora"))


if __name__ == "__main__":
    main()
