# -*- coding: utf-8 -*-
"""Arbitro do tom: quando cifra e melodia discordam, de que lado esta o erro?

Nenhum dos dois rotulos e' confiavel sozinho -- o da cifra sai de uma linha
"Tonalidade:" lida por OCR, o da melodia sai do cabecalho do PDF. Mas o
CONTEUDO fala: a cifra tem os acordes, a melodia tem as notas.

O juiz principal sao os ACORDES da cifra (raiz de acorde e' sinal forte). Antes
de usar o juiz, o script MEDE o quanto ele erra: nos louvores em que a cifra e
a melodia ja concordam no rotulo, o rotulo e' quase certamente certo, entao a
taxa de acerto do juiz ali e' o seu piso de ruido.

    set PYTHONIOENCODING=utf-8
    python conferir_tom_arbitro.py
"""
from __future__ import unicode_literals

import io
import json
import os
import re
import sys
import unicodedata
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conferir_tom import (BASE, CIFRAS, MELODIAS, agrupar, escaneado, ler_tom,  # noqa
                          nfc, nome, relacao, so_letras, TOM_NO_FIM)

AQUI = os.path.dirname(os.path.abspath(__file__))
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NOMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAIOR = (0, 2, 4, 5, 7, 9, 11)
MIN_ACORDES = 8          # menos que isso nao da' pra deduzir tom nenhum
FOLGA_MIN = 0.02         # folga sobre o 2o colocado pra deducao valer

# grau -> qualidade que o acorde tem naquele grau. 'x' = o V do menor, que
# aparece maior (harmonico) ou menor (natural); 'd' = diminuto.
GRAU_MAIOR = {0: "M", 2: "m", 4: "m", 5: "M", 7: "M", 9: "m", 11: "d"}
GRAU_MENOR = {0: "m", 2: "d", 3: "M", 5: "m", 7: "x", 8: "M", 10: "M"}


def pc_de(x):
    m = re.match(r"^([A-G])([#b]?)", nfc(x).strip())
    if not m:
        return None
    return (PC[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)) % 12


def ler_acorde(ac):
    """'Am7/G' -> (9, 'm'). A QUALIDADE e' o que decide o tom: so' com a raiz,
    G maior e D maior tem quase as mesmas notas e o juiz erra o tempo todo --
    e' o 'A' contra o 'Am' que separa um do outro."""
    m = re.match(r"^([A-G])([#b]?)(.*)$", nfc(ac).strip())
    if not m:
        return None
    pc = (PC[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)) % 12
    r = m.group(3).split("/")[0]
    if re.match(r"^(dim|°|º)", r) or "b5" in r:
        q = "d"
    elif re.match(r"^(m|min)(?!aj|a7)", r):
        q = "m"
    elif re.match(r"^(sus|5)", r):
        q = "n"                                  # nao diz maior nem menor
    else:
        q = "M"
    return pc, q


def deduzir_acordes(acs):
    """Tom deduzido dos acordes. Prova os 24 tons: cada acorde vale pelo tanto
    que a QUALIDADE dele cabe no grau que ocuparia naquele tom. Devolve a folga
    sobre o 2o colocado -- deducao apertada nao serve de prova."""
    ps = [ler_acorde(a) for a in acs]
    ps = [p for p in ps if p]
    if len(ps) < 4:
        return None, 0.0
    n = float(len(ps))
    cont = Counter(ps)
    mx = float(max(cont.values()))
    melhor, primeiro, segundo = None, -1.0, -1.0
    for pc in range(12):
        for menor in (False, True):
            tab = GRAU_MENOR if menor else GRAU_MAIOR
            enc = 0.0
            for (r, q), v in cont.items():
                g = (r - pc) % 12
                if g not in tab:
                    continue                     # nota de fora da escala
                esp = tab[g]
                if esp == "x":
                    enc += v * (1.0 if q in "Mm" else 0.5)
                elif q == esp or q == "n":
                    enc += v
                else:
                    enc += v * 0.25              # grau certo, qualidade torta
            ton = cont.get((pc, "m" if menor else "M"), 0) + cont.get((pc, "n"), 0)
            nota = (0.30 * (enc / n) + 0.40 * min(ton / mx, 1.0)
                    + 0.18 * (1.0 if ps[-1][0] == pc else 0.0)
                    + 0.12 * (1.0 if ps[0][0] == pc else 0.0))
            if nota > primeiro:
                melhor, segundo, primeiro = (pc, menor), primeiro, nota
            elif nota > segundo:
                segundo = nota
    return melhor, primeiro - segundo


def deduzir_notas(pcs):
    """Tom deduzido das notas da melodia. Sinal mais fraco que o dos acordes --
    nota solta nao diz maior nem menor, e melodia que para na quinta engana o
    juiz. Serve de indicio, nao de prova."""
    pcs = [p for p in pcs if p is not None]
    if len(pcs) < 6:
        return None, 0.0
    n = float(len(pcs))
    cont = Counter(pcs)
    mx = float(max(cont.values()))
    melhor, primeiro, segundo = None, -1.0, -1.0
    for pc in range(12):
        for menor in (False, True):
            base = (pc + 3) % 12 if menor else pc
            esc = set((base + i) % 12 for i in MAIOR)
            if menor:
                esc.add((pc + 11) % 12)
            nota = (0.34 * (sum(v for k, v in cont.items() if k in esc) / n)
                    + 0.40 * (cont.get(pc, 0) / mx)
                    + 0.16 * (1.0 if pcs[-1] == pc else 0.0)
                    + 0.10 * (1.0 if pcs[0] == pc else 0.0))
            if nota > primeiro:
                melhor, segundo, primeiro = (pc, menor), primeiro, nota
            elif nota > segundo:
                segundo = nota
    return melhor, primeiro - segundo


def notas_da_melodia(arq):
    d = json.load(io.open(os.path.join(MELODIAS, arq), encoding="utf-8"))
    return [pc_de(n) for l in d["cadernos"]["C"]["linhas"] for n in l.get("n", [])]


def acordes_da_cifra(reg):
    return [a[1] for l in reg.get("linhas", []) for a in l.get("a", [])]


def bate(a, b):
    """Rotulo e deducao 'batem' se sao o mesmo tom ou o relativo."""
    if a is None or b is None:
        return False
    if a == b:
        return True
    if a[1] != b[1]:
        menor, maior = (a, b) if a[1] else (b, a)
        return menor[0] == (maior[0] + 9) % 12
    return False


def main():
    acordes = json.load(io.open(os.path.join(CIFRAS, "acordes.json"), encoding="utf-8"))
    mel = json.load(io.open(os.path.join(MELODIAS, "indice.json"),
                            encoding="utf-8"))["louvores"]
    melt = {}
    for t, m in mel.items():
        melt.setdefault(so_letras(t), m)
        melt.setdefault(TOM_NO_FIM.sub("", so_letras(t)).strip(), m)
    louvores = agrupar(acordes)
    sus = json.load(io.open(os.path.join(AQUI, "tom_divergente.json"), encoding="utf-8"))
    L_ = "-" * 76

    # ---- 1) quanto o juiz erra? mede onde os dois livros ja concordam ------
    acerto = erro = 0
    for (tn, _h), Lv in louvores.items():
        reg, m = Lv["reg"], melt.get(tn)
        if not m:
            continue
        rc, rm = ler_tom(reg.get("tom")), ler_tom((m.get("tons") or {}).get("C"))
        if not rc or not rm or relacao(rc, rm) not in ("igual", "relativo"):
            continue                      # so' o gabarito: os dois de acordo
        acs = acordes_da_cifra(reg)
        if len(acs) < MIN_ACORDES:
            continue
        d, folga = deduzir_acordes(acs)
        if folga < FOLGA_MIN:
            continue
        if bate(rc, d):
            acerto += 1
        else:
            erro += 1
    piso = 100.0 * erro / max(1, acerto + erro)
    print("=" * 76)
    print("O JUIZ (deduzir o tom pelos acordes) -- primeiro, o quanto ele erra")
    print("=" * 76)
    print("gabarito = louvores em que cifra e melodia ja dizem o mesmo tom")
    print("  gabarito com acordes bastantes            : %d" % (acerto + erro))
    print("  o juiz reproduziu o tom do gabarito       : %d (%.1f%%)"
          % (acerto, 100.0 - piso))
    print("  o juiz errou                              : %d (%.1f%%)  <- PISO DE RUIDO"
          % (erro, piso))

    # ---- 2) o rotulo da cifra bate com os acordes dela? -------------------
    print(L_)
    print("ROTULO DA CIFRA x ACORDES DA PROPRIA CIFRA (todo o acervo)")
    tot = bate_n = nao_n = curto = fraco = semtom = 0
    por_pdf = {}
    lista_ruim = []
    for (tn, _h), Lv in louvores.items():
        reg = Lv["reg"]
        tot += 1
        pdf = nfc(reg.get("pdf"))
        d_pdf = por_pdf.setdefault(pdf, Counter())
        rc = ler_tom(reg.get("tom"))
        if not rc:
            semtom += 1
            d_pdf["sem tom"] += 1
            continue
        acs = acordes_da_cifra(reg)
        if len(acs) < MIN_ACORDES:
            curto += 1
            d_pdf["poucos acordes"] += 1
            continue
        d, folga = deduzir_acordes(acs)
        if folga < FOLGA_MIN:
            fraco += 1
            d_pdf["indeciso"] += 1
            continue
        if bate(rc, d):
            bate_n += 1
            d_pdf["bate"] += 1
        else:
            nao_n += 1
            d_pdf["NAO BATE"] += 1
            lista_ruim.append((Lv["titulo"], reg.get("tom"), nome(d), pdf, len(acs)))
    jul = bate_n + nao_n
    print("  cifras distintas                          : %d" % tot)
    print("  julgaveis (tem tom + %d acordes + decisao) : %d" % (MIN_ACORDES, jul))
    print("    rotulo BATE com os acordes              : %d (%.1f%%)"
          % (bate_n, 100.0 * bate_n / max(1, jul)))
    print("    rotulo NAO BATE com os acordes          : %d (%.1f%%)"
          % (nao_n, 100.0 * nao_n / max(1, jul)))
    print("      (piso de ruido do juiz: %.1f%% -- o que passa disso e' erro de verdade)"
          % piso)
    print("  fora do julgamento: %d sem tom, %d com menos de %d acordes, %d indecisos"
          % (semtom, curto, MIN_ACORDES, fraco))
    print(L_)
    print("  %-46s %6s %6s %7s" % ("POR PDF", "julg.", "erra", "taxa"))
    for p, c in sorted(por_pdf.items(), key=lambda x: -sum(x[1].values())):
        j = c["bate"] + c["NAO BATE"]
        print("  %-46s %6d %6d %6.1f%%%s"
              % (p[:46], j, c["NAO BATE"], 100.0 * c["NAO BATE"] / max(1, j),
                 "   <- ESCANEADO" if escaneado(p) else ""))

    # ---- 3) os divergentes, julgados --------------------------------------
    print(L_)
    print("OS DIVERGENTES DO CRUZAMENTO COM A MELODIA, JULGADOS")
    print("%-30s %-6s %-6s %-6s %-6s %s"
          % ("LOUVOR", "cifra", "acord", "melod", "notas", "VEREDITO"))
    ver = Counter()
    for d in sus:
        reg = acordes[d["chaves"][0]]
        m = melt.get(so_letras(d["titulo"]))
        rc, rm = ler_tom(d["tom_cifra"]), ler_tom(d["tom_melodia"])
        acs = acordes_da_cifra(reg)
        dc, fc = deduzir_acordes(acs) if len(acs) >= MIN_ACORDES else (None, 0)
        dm, fm = deduzir_notas(notas_da_melodia(m["arq"])) if m else (None, 0)
        c_ok, m_ok = bate(rc, dc), bate(rm, dm)
        acorde_na_melodia = bate(rm, dc)
        if dc is None:
            v = "sem acorde pra julgar"
        elif acorde_na_melodia and not c_ok:
            v = "CIFRA ERRADA"            # os acordes tocam no tom da melodia
        elif c_ok and not m_ok and bate(rc, dm):
            v = "melodia errada"
        elif c_ok and m_ok:
            v = "livros em tons diferentes"
        elif c_ok:
            v = "melodia suspeita"
        else:
            v = "cifra suspeita"
        ver[v] += 1
        d.update({"tom_acordes": nome(dc) if dc else None,
                  "folga_acordes": round(fc, 3),
                  "tom_notas_melodia": nome(dm) if dm else None,
                  "veredito": v})
        print("%-30s %-6s %-6s %-6s %-6s %s"
              % (d["titulo"][:30], d["tom_cifra"], nome(dc) if dc else "-",
                 d["tom_melodia"], nome(dm) if dm else "-", v))
    print(L_)
    for k, v in ver.most_common():
        print("  %-26s: %d" % (k, v))
    for rot in ("CIFRA ERRADA", "cifra suspeita"):
        n = sum(1 for d in sus if d["veredito"] == rot)
        e = sum(1 for d in sus if d["veredito"] == rot and d["escaneado"])
        print("  '%s': %d, sendo %d do PDF escaneado" % (rot, n, e))

    with io.open(os.path.join(AQUI, "tom_divergente.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(sus, ensure_ascii=False, indent=1))
    alvo = os.path.join(AQUI, "tom_x_acordes.json")
    with io.open(alvo, "w", encoding="utf-8") as f:
        f.write(json.dumps([{"titulo": t, "tom_rotulo": r, "tom_acordes": a,
                             "pdf": p, "n_acordes": n, "escaneado": escaneado(p)}
                            for t, r, a, p, n in sorted(lista_ruim)],
                           ensure_ascii=False, indent=1))
    print(L_)
    print("gravado: %s" % alvo)


if __name__ == "__main__":
    main()
