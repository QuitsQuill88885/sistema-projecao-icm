# -*- coding: utf-8 -*-
"""Confere o TOM das cifras cruzando com o tom da melodia.

O caderno "C" da melodia esta na afinacao de concerto -- e' o caderno do
violao, do teclado, do baixo. Logo o tom do caderno C do MESMO louvor tem que
bater com o tom da cifra de violao (ou ser o relativo menor/maior dele).

Roda sobre o acervo inteiro e imprime numeros: quantos foram conferidos,
quantos divergem, de qual PDF vieram, e o que os PROPRIOS acordes da cifra
dizem sobre quem esta certo (nota de aderencia a escala + acorde final).

    set PYTHONIOENCODING=utf-8
    python conferir_tom.py
"""
from __future__ import unicode_literals

import hashlib
import io
import json
import os
import re
import sys
import unicodedata
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.join(os.environ.get("APPDATA", ""), "Sistema Projecao")
CIFRAS = os.path.join(BASE, "cifras")
MELODIAS = os.path.join(BASE, "melodias")

PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NOMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAIOR = (0, 2, 4, 5, 7, 9, 11)


def nfc(t):
    return unicodedata.normalize("NFC", t or "")


def escaneado(pdf):
    """O PDF de 2018 e' o unico escaneado; o nome vem com acento e o acento
    pode estar decomposto, entao compara sem acento nenhum."""
    return "2018" in nfc(pdf or "")


def so_letras(t):
    t = unicodedata.normalize("NFD", (t or "").upper())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]+", " ", t)).strip()


TOM_NO_FIM = re.compile(r" [A-G](B|M|BM)?$")


def ler_tom(tom):
    """'F#m' -> (6, True). None se nao der pra ler."""
    if not tom:
        return None
    t = re.split(r"[,/]", nfc(tom).strip())[0].strip()
    m = re.match(r"^([A-G])([#b]?)(.*)$", t)
    if not m:
        return None
    pc = (PC[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)) % 12
    resto = m.group(3).strip()
    menor = bool(re.match(r"^(m|min)(?![aA])", resto))
    return pc, menor


def nome(t):
    return NOMES[t[0] % 12] + ("m" if t[1] else "")


def relacao(a, b):
    """Como o tom da cifra (a) se relaciona com o tom da melodia (b)."""
    if a == b:
        return "igual"
    (pa, ma), (pb, mb) = a, b
    if pa == pb:
        return "modo trocado"              # G x Gm -- mesma raiz, outro modo
    if ma != mb:
        menor, maior = (a, b) if ma else (b, a)
        if menor[0] == (maior[0] + 9) % 12:
            return "relativo"              # Am x C -- aceito
    return "DIVERGE"


def raiz(ac):
    m = re.match(r"^([A-G])([#b]?)", nfc(ac).strip())
    if not m:
        return None
    return (PC[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)) % 12


def raizes_da_cifra(reg):
    """Raizes dos acordes, na ordem em que aparecem. Baixo (/G) ignorado."""
    saida = []
    for l in reg.get("linhas", []):
        for _col, ac in l.get("a", []):
            r = raiz(ac)
            if r is not None:
                saida.append(r)
    return saida


def nota_do_tom(tom, rr):
    """Quanto os acordes da cifra combinam com este tom. 0..100.

    Tres evidencias, do jeito que um musico olharia:
      - quantos acordes cabem na escala do tom (relativo maior manda na escala);
      - se a tonica aparece muito;
      - se o ultimo acorde e' a tonica (o louvor termina no tom).
    """
    if not rr:
        return 0.0
    pc, menor = tom
    base = (pc + 3) % 12 if menor else pc          # relativo maior: mesma escala
    escala = set((base + i) % 12 for i in MAIOR)
    dentro = sum(1 for r in rr if r in escala) / float(len(rr))
    tonica = rr.count(pc) / float(len(rr))
    fim = 1.0 if rr[-1] == pc else 0.0
    ini = 1.0 if rr[0] == pc else 0.0
    return 100.0 * (0.55 * dentro + 0.20 * min(tonica * 3, 1.0) + 0.15 * fim + 0.10 * ini)


def carregar():
    acordes = json.load(io.open(os.path.join(CIFRAS, "acordes.json"), encoding="utf-8"))
    idx = json.load(io.open(os.path.join(MELODIAS, "indice.json"), encoding="utf-8"))
    return acordes, idx["louvores"]


def agrupar(acordes):
    """O extrator grava a MESMA cifra sob varias chaves do app (o mesmo louvor
    aparece com numero da coletanea, com 'AV', com zeros a esquerda...). Junta
    pelo CONTEUDO, senao o mesmo erro e' contado tres vezes."""
    louvores = {}
    for chave, reg in acordes.items():
        p = chave.split("|")
        titulo = p[1] if len(p) > 1 else chave
        corpo = json.dumps(reg.get("linhas", []), ensure_ascii=False, sort_keys=True)
        h = hashlib.md5(corpo.encode("utf-8")).hexdigest()
        ident = (so_letras(titulo), h)
        louvores.setdefault(ident, {"titulo": titulo, "chaves": [], "reg": reg})
        louvores[ident]["chaves"].append(chave)
    return louvores


def main():
    acordes, mel = carregar()
    louvores = agrupar(acordes)
    por_titulo = {}
    for (tn, _h), L in louvores.items():
        por_titulo.setdefault(tn, []).append(L)

    # indice das melodias por titulo, com um segundo indice sem o tom que
    # vazou pro fim do titulo ("COMO TU QUERES  G")
    mel_por_tit = {}
    for t, m in mel.items():
        mel_por_tit.setdefault(so_letras(t), m)
        alt = TOM_NO_FIM.sub("", so_letras(t)).strip()
        mel_por_tit.setdefault(alt, m)

    tot = len(louvores)
    com_tom_cifra = casou = mel_com_tom = conferidos = 0
    sem_tom_por_pdf = Counter()
    contagem = Counter()
    suspeitos = []
    homonimos = set()

    for (tn, _h), L in louvores.items():
        reg = L["reg"]
        tc = reg.get("tom")
        if tc:
            com_tom_cifra += 1
        else:
            sem_tom_por_pdf[nfc(reg.get("pdf"))] += 1
        m = mel_por_tit.get(tn)
        if not m:
            continue
        casou += 1
        if len(por_titulo.get(tn, [])) > 1:
            homonimos.add(tn)
        tm = (m.get("tons") or {}).get("C")
        if tm:
            mel_com_tom += 1
        if not tc or not tm:
            continue
        a, b = ler_tom(tc), ler_tom(tm)
        if a is None or b is None:
            contagem["ilegivel"] += 1
            continue
        conferidos += 1
        rel = relacao(a, b)
        contagem[rel] += 1
        if rel in ("DIVERGE", "modo trocado"):
            rr = raizes_da_cifra(reg)
            na, nb = nota_do_tom(a, rr), nota_do_tom(b, rr)
            suspeitos.append({
                "titulo": L["titulo"],
                "chaves": L["chaves"],
                "tom_cifra": tc, "tom_melodia": tm,
                "rel": rel,
                "dist": (b[0] - a[0]) % 12,
                "pdf": nfc(reg.get("pdf")),
                "escaneado": escaneado(reg.get("pdf")),
                "n_acordes": len(rr),
                "nota_tom_cifra": round(na, 1),
                "nota_tom_melodia": round(nb, 1),
                "quem_os_acordes_apoiam": ("melodia" if nb > na + 3 else
                                           "cifra" if na > nb + 3 else "empate"),
                "ultimo_acorde": NOMES[rr[-1]] if rr else None,
                "homonimo": tn in homonimos,
            })

    L_ = "-" * 76
    print("=" * 76)
    print("CIFRAS x MELODIA -- conferencia de TOM sobre o acervo inteiro")
    print("=" * 76)
    print("chaves em acordes.json                    : %d" % len(acordes))
    print("cifras DISTINTAS (mesma cifra sob varias chaves conta 1): %d" % tot)
    print("  com tonalidade declarada                : %d (%.1f%%)"
          % (com_tom_cifra, 100.0 * com_tom_cifra / tot))
    print("  SEM tonalidade declarada                : %d (%.1f%%)"
          % (tot - com_tom_cifra, 100.0 * (tot - com_tom_cifra) / tot))
    for p, q in sem_tom_por_pdf.most_common():
        print("      sem tom em %-44s: %d" % (p[:44], q))
    print("melodias no indice                        : %d" % len(mel))
    print("  cifra que casou com melodia (titulo)    : %d" % casou)
    print("  dessas, a melodia tem tom no caderno C  : %d" % mel_com_tom)
    print("PARES CONFERIVEIS (os dois lados com tom) : %d" % conferidos)
    print(L_)
    for k, v in contagem.most_common():
        print("  %-24s: %4d  (%.1f%% dos conferiveis)"
              % (k, v, 100.0 * v / conferidos if conferidos else 0))
    print(L_)
    esc = sum(1 for d in suspeitos if d["escaneado"])
    print("TOM ERRADO (diverge + modo trocado)       : %d de %d = %.1f%%"
          % (len(suspeitos), conferidos,
             100.0 * len(suspeitos) / conferidos if conferidos else 0))
    for p, q in Counter(d["pdf"] for d in suspeitos).most_common():
        print("  %-48s: %3d" % (p[:48], q))
    print("  do PDF ESCANEADO (2018)                 : %d" % esc)
    print("  dos PDFs de texto nativo                : %d" % (len(suspeitos) - esc))
    print(L_)
    ap = Counter(d["quem_os_acordes_apoiam"] for d in suspeitos)
    print("os acordes da propria cifra apoiam o tom da MELODIA : %d" % ap["melodia"])
    print("os acordes da propria cifra apoiam o tom da CIFRA   : %d" % ap["cifra"])
    print("empate                                             : %d" % ap["empate"])
    print("com titulo repetido no acervo (par pode estar torto): %d"
          % sum(1 for d in suspeitos if d["homonimo"]))
    print(L_)
    dd = Counter(d["dist"] for d in suspeitos if d["rel"] == "DIVERGE")
    print("distancia cifra -> melodia, em semitons:")
    for k in sorted(dd):
        print("   %2d semitom(s): %3d" % (k, dd[k]))
    print(L_)
    print("%-40s %-6s %-7s %-4s %-6s %s"
          % ("LOUVOR", "CIFRA", "MELODIA", "DIS", "APOIO", "PDF"))
    suspeitos.sort(key=lambda d: (d["quem_os_acordes_apoiam"] != "melodia", d["titulo"]))
    for d in suspeitos:
        print("%-40s %-6s %-7s %-4d %-6s %s%s"
              % (d["titulo"][:40], d["tom_cifra"], d["tom_melodia"], d["dist"],
                 d["quem_os_acordes_apoiam"],
                 "ESCANEADO" if d["escaneado"] else "texto",
                 "  [titulo repetido]" if d["homonimo"] else ""))

    saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tom_divergente.json")
    with io.open(saida, "w", encoding="utf-8") as f:
        f.write(json.dumps(suspeitos, ensure_ascii=False, indent=1))
    print(L_)
    print("gravado: %s" % saida)


if __name__ == "__main__":
    main()
