# -*- coding: utf-8 -*-
"""Mede QUANTA LETRA DE OCR sobrou na cifra, louvor por louvor.

A LENTE: o extrator costura a letra certa (dados/louvores.js) por cima da letra
que saiu do PDF, alinhando as duas por sequencia (consertar_pela_letra). Quando
o alinhamento nao acha par para uma linha, o que fica na tela do musico e' o
texto CRU do OCR -- "Por verdes campos  melconduzilra," no lugar de "POR VERDES
CAMPOS ME CONDUZIRA".

Este script NAO conserta nada. Ele conta.

COMO CADA LINHA E' CLASSIFICADA
    costurada   o texto e' exatamente uma linha de louvores.js -> o alinhamento pegou
    quase       >= 0.85 de semelhanca com alguma linha certa (so pontuacao muda)
    curta       menos de 6 letras: consertar_pela_letra nem tenta casar (mesmo
                criterio dele, a lista "uteis")
    acorde      a linha inteira e' acorde que nao subiu para a letra. Conta os
                acordes ja machucados pelo OCR ("Dm D7 Gm GmlF C7fE" = Gm/F, C7/E;
                "AIG Pm 7 Bm" = A/G, Em7, Bm)
    nota        credito e anotacao do PDF ("(Let. J.J.M /Mus. IAM.)", "Repetir o
                hino", "Final:", "Arranjo: ..."). Texto legitimo, so nao e' letra
    CRUA        letra de verdade que ficou com o texto do OCR. E' o que o musico
                ve estragado. Sub-dividida pelo VOCABULARIO DO PROPRIO HINARIO
                (todas as palavras de louvores.js):
                  corrompida  < 70% das palavras existem no hinario -> OCR quebrou
                  legivel     >= 70% -> texto limpo que a letra do app nao tem
                              (estrofe a mais, versao diferente)

CORPOS REPETIDOS: uma mesma cifra e' gravada em varias chaves quando o app tem o
mesmo titulo mais de uma vez (o extrator faz "for chave in alvo"). O relatorio da
o numero por registro E por corpo distinto, para nao inflar a conta.

Uso:  python medir_letra_crua.py
      python medir_letra_crua.py --piores 60
      python medir_letra_crua.py --ver "PASTOR"      (despeja as linhas do louvor)
      python medir_letra_crua.py --csv saida.csv
      python medir_letra_crua.py --arquivo copia.json   (mede uma copia parada)
"""
import difflib
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extrair_cifras import (so_letras, eh_acorde, consertar_ocr, sem_parenteses,
                            letras_dos_louvores, pasta_cifras)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MIN_LETRAS = 6      # mesmo piso de consertar_pela_letra
QUASE = 0.85        # acima disto a diferenca nao aparece na tela
VOCAB_OK = 0.70     # abaixo disto a linha esta corrompida pelo OCR

NOTA = re.compile(
    r"(^\s*[\(\[]?\s*(let|letra|mus|m[uú]s|m[uú]sica|arranjo|adapt|autor|vers[aã]o|"
    r"coro|refr[aã]o|bis|final|intro|introdu|solo|ponte|tonalidade|repetir|"
    r"\d\s*[ªº]?\s*(estrofe|vez|parte))\b)"
    r"|(\bpara\s+repetir\b)|(\bad\s*lib\b)|(\b\d\s*x\b)", re.I)


def carregar_louvores():
    cam = os.path.join(RAIZ, "dados", "louvores.js")
    s = io.open(cam, encoding="utf-8").read()
    L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    if isinstance(L, dict):
        L = L.get("louvores", L)
    return L


def vocabulario(L):
    """Todas as palavras que o hinario usa. Serve de dicionario: palavra que nao
    esta aqui, num louvor, quase sempre e' o OCR que quebrou a palavra."""
    v = set()
    for l in L:
        for sl in l.get("slides", []):
            for li in sl.get("linhas", []):
                for w in so_letras(li).split():
                    if len(w) >= 3:
                        v.add(w)
    return v


def linhas_por_chave(L):
    por_chave = {}
    for l in L:
        linhas = [li for sl in l.get("slides", []) for li in sl.get("linhas", [])]
        chave = "%s|%s|%s" % (l.get("num") or "", l.get("titulo") or "",
                              linhas[0] if linhas else "")
        por_chave.setdefault(chave, linhas)
    return por_chave


# o OCR troca / por I, l, f, 1, |  e E por P (medido: 122 baixos soltos,
# 72 "Pm", 47 "CIE"). Para DECIDIR se a linha e' de acorde, vale tentar tudo.
def acorde_machucado(w):
    w = w.strip().strip("|,.;:")
    if not w:
        return False
    if eh_acorde(w) or eh_acorde(consertar_ocr(w)):
        return True
    for a in "Ilf1|(":
        if a in w and eh_acorde(w.replace(a, "/")):
            return True
    if w.startswith("P") and eh_acorde("E" + w[1:]):
        return True
    return False


def linha_de_acorde(t):
    t = re.sub(r"\([^)]*\)", " ", t or "")          # tira "(D para repetir)"
    toks = [w for w in t.split() if w]
    if not toks or len(toks) > 14:
        return False
    bons = sum(1 for w in toks if acorde_machucado(w))
    return bons == len(toks) or (bons >= 2 and bons / len(toks) >= 0.75)


def frac_conhecida(t, voc):
    """(fracao de palavras que o hinario conhece, quantas palavras foram olhadas)"""
    ws = [w for w in so_letras(t).split() if len(w) >= 3]
    if not ws:
        return 1.0, 0
    return sum(1 for w in ws if w in voc) / len(ws), len(ws)


def vocabulario_reprova(f, nw):
    """Linha curta engana: "O coração bater;" tem duas palavras, "BATER" nao
    aparece em nenhum outro louvor, e a fracao cai para 0,5 sem que a linha
    tenha defeito nenhum. Por isso a prova do dicionario so vale com texto
    suficiente, e em linha de 2-3 palavras exige-se um estrago bem maior."""
    if nw >= 4:
        return f < VOCAB_OK
    if nw >= 2:
        return f < 0.50
    return False


# ------------------------------------------------------------------ marcas
# O vocabulario sozinho deixa passar linha estragada: "Não tinham belleza pra
# mim," tem 80% de palavras conhecidas e mesmo assim esta quebrada. Estas sao as
# marcas do OCR no caractere, conferidas nas linhas de verdade.
LIXO = re.compile(r"[¡¿\[\]{}«»~^\\\x01]")          # nao existem em letra de hino
APOSTROFO = re.compile(r"(?<=\s)['‘’](?=[a-zà-úâ-ûã-õç])")   # "'sangue"
INSERIDO = "lijI1|[']"      # caracteres que o OCR enfia no meio da palavra


def _letra_a_mais(w, voc):
    """"Jelsus"->"jesus", "belleza"->"beleza", "levantairei"->"levantarei".

    So no MEIO da palavra e so com caractere que o OCR costuma inventar. Sem
    isso "caminham" -> "caminha" acusaria flexao normal como erro."""
    if len(w) < 5 or w in voc:
        return False
    for i in range(1, len(w) - 1):
        if w[i] in INSERIDO.upper() and (w[:i] + w[i + 1:]) in voc:
            return True
    return False


def marcas_de_ocr(t, voc):
    m = []
    if LIXO.search(t):
        m.append("lixo")
    if APOSTROFO.search(t):
        m.append("apostrofo")
    if any(_letra_a_mais(w, voc) for w in so_letras(t).split() if len(w) >= 5):
        m.append("letra_a_mais")
    return m


def classificar(linhas, certas, voc):
    exatas = set(certas)
    norm = [so_letras(x) for x in certas if so_letras(x)]
    cont = Counter()
    cruas = []
    for l in linhas:
        t = l.get("t") or ""
        n = so_letras(t)
        if len(n) < MIN_LETRAS:
            cont["curta"] += 1
            continue
        if t in exatas:
            cont["costurada"] += 1
            continue
        melhor = 0.0
        for c in norm:
            r = difflib.SequenceMatcher(None, n, c).ratio()
            if r > melhor:
                melhor = r
                if melhor >= 0.999:
                    break
        if melhor >= QUASE:
            cont["quase"] += 1
        elif linha_de_acorde(t):
            cont["acorde"] += 1
        elif NOTA.search(t):
            cont["nota"] += 1
        else:
            f, nw = frac_conhecida(t, voc)
            m = marcas_de_ocr(t, voc)
            voc_ruim = vocabulario_reprova(f, nw)
            ruim = voc_ruim or bool(m)
            cont["CRUA"] += 1
            if ruim:
                cont["crua_corrompida"] += 1
                for x in m:
                    cont["marca_" + x] += 1
                if voc_ruim:
                    cont["marca_vocabulario"] += 1
            else:
                cont["crua_legivel"] += 1
            if l.get("a"):
                cont["crua_com_acorde"] += 1
            cruas.append((round(f, 2), round(melhor, 2), t, len(l.get("a") or []),
                          ",".join(m) if ruim else ""))
    return cont, cruas


def main():
    piores = 25
    if "--piores" in sys.argv:
        piores = int(sys.argv[sys.argv.index("--piores") + 1])
    ver = sys.argv[sys.argv.index("--ver") + 1].upper() if "--ver" in sys.argv else None
    csv = sys.argv[sys.argv.index("--csv") + 1] if "--csv" in sys.argv else None
    # o extrator pode estar rodando agora e reescrevendo acordes.json no meio da
    # medida; --arquivo mede uma copia parada, para o numero nao mudar sozinho
    alvo = (sys.argv[sys.argv.index("--arquivo") + 1] if "--arquivo" in sys.argv
            else os.path.join(pasta_cifras(), "acordes.json"))

    L = carregar_louvores()
    voc = vocabulario(L)
    por_chave = linhas_por_chave(L)
    letras = letras_dos_louvores()
    acordes = json.load(io.open(alvo, encoding="utf-8"))

    total = Counter()
    regs = []
    corpos = {}                      # assinatura do corpo -> primeira chave
    por_pdf = defaultdict(Counter)

    for chave, reg in acordes.items():
        pdf = reg.get("pdf", "?")
        linhas = reg.get("linhas") or []
        partes = chave.split("|")
        tit = partes[1] if len(partes) > 1 else ""
        certas = (por_chave.get(chave) or letras.get(so_letras(tit))
                  or letras.get(sem_parenteses(tit)) or [])
        assin = "\n".join(l.get("t", "") for l in linhas)
        novo = assin not in corpos
        if novo:
            corpos[assin] = chave
        if not certas:
            total["sem_referencia"] += 1
            continue
        cont, cruas = classificar(linhas, certas, voc)
        for k, v in cont.items():
            total[k] += v
            if novo:
                total["u_" + k] += v
        total["linhas"] += len(linhas)
        total["louvores"] += 1
        p = por_pdf[pdf]
        p["louvores"] += 1
        p["linhas"] += len(linhas)
        p["CRUA"] += cont["CRUA"]
        p["corrompida"] += cont["crua_corrompida"]
        p["acorde"] += cont["acorde"]
        if cont["CRUA"]:
            total["afetados"] += 1
            p["afetados"] += 1
        if cont["crua_corrompida"]:
            total["afetados_corrompidos"] += 1
            p["afetados_corr"] += 1
        if novo:
            total["corpos"] += 1
            if cont["CRUA"]:
                total["corpos_afetados"] += 1
            if cont["crua_corrompida"]:
                total["corpos_corrompidos"] += 1
        uteis = sum(cont[k] for k in ("costurada", "quase", "acorde", "nota", "CRUA"))
        regs.append({"chave": chave, "pdf": pdf, "novo": novo,
                     "crua": cont["CRUA"], "corr": cont["crua_corrompida"],
                     "leg": cont["crua_legivel"], "costurada": cont["costurada"],
                     "quase": cont["quase"], "acorde": cont["acorde"],
                     "nota": cont["nota"], "curta": cont["curta"],
                     "linhas": len(linhas), "ok": reg.get("ok", 0),
                     "pct": cont["CRUA"] / uteis if uteis else 0.0, "cruas": cruas})

    if ver:
        for r in regs:
            if ver in r["chave"].upper():
                print("=" * 74)
                print(r["chave"], "|", r["pdf"], "| corpo repetido" if not r["novo"] else "")
                print("costurada %d  quase %d  acorde %d  nota %d  curta %d  CRUA %d (corrompida %d)"
                      % (r["costurada"], r["quase"], r["acorde"], r["nota"],
                         r["curta"], r["crua"], r["corr"]))
                for f, sim, t, na, m in r["cruas"]:
                    print("   %-11s voc=%.2f sim=%.2f ac=%d | %s"
                          % (("CORROMPIDA" if m else "legivel"), f, sim, na, t))
        return

    n, nl = total["louvores"], total["linhas"]
    print("=" * 78)
    import time
    print("ARQUIVO: %s  (%s)" % (alvo, time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(os.path.getmtime(alvo)))))
    print("ACERVO: %d registros em acordes.json | %d corpos de cifra distintos"
          % (len(acordes), total["corpos"]))
    print("        (o mesmo corpo e' gravado em varias chaves quando o app repete o titulo)")
    print()
    print("LINHAS: %d por registro | %d sem contar corpo repetido" % (nl, total["u_costurada"] + total["u_quase"] + total["u_acorde"] + total["u_nota"] + total["u_curta"] + total["u_CRUA"]))
    print("   %-22s %7s %7s   %s" % ("", "linhas", "% ", "so corpos distintos"))
    for k, rot in (("costurada", "costurada (alinhou)"), ("quase", "quase igual"),
                   ("curta", "curta (<6 letras)"), ("acorde", "linha de acorde"),
                   ("nota", "credito/anotacao"), ("CRUA", "LETRA CRUA")):
        print("   %-22s %7d %6.1f%%   %7d" % (rot, total[k], 100.0 * total[k] / max(1, nl), total["u_" + k]))
    print("   %-22s %7d %6.1f%%   %7d" % ("   > corrompida OCR", total["crua_corrompida"],
          100.0 * total["crua_corrompida"] / max(1, nl), total["u_crua_corrompida"]))
    print("   %-22s %7d %6.1f%%   %7d" % ("   > legivel, fora", total["crua_legivel"],
          100.0 * total["crua_legivel"] / max(1, nl), total["u_crua_legivel"]))
    print()
    print("LOUVORES ATINGIDOS")
    print("   com >=1 linha de letra crua .......... %4d de %4d  (%.1f%%)   [corpos: %d de %d]"
          % (total["afetados"], n, 100.0 * total["afetados"] / max(1, n),
             total["corpos_afetados"], total["corpos"]))
    print("   com >=1 linha CORROMPIDA pelo OCR .... %4d de %4d  (%.1f%%)   [corpos: %d de %d]"
          % (total["afetados_corrompidos"], n, 100.0 * total["afetados_corrompidos"] / max(1, n),
             total["corpos_corrompidos"], total["corpos"]))
    print()
    print("POR PDF DE ORIGEM  (registros, nao corpos)")
    print("   %-40s %6s %6s %7s %8s %8s %7s"
          % ("pdf", "louv.", "atin.", "c/corr", "l.cruas", "l.corromp", "corr/lv"))
    for pdf in sorted(por_pdf):
        p = por_pdf[pdf]
        print("   %-40s %6d %6d %7d %8d %8d %7.1f"
              % (pdf[:40], p["louvores"], p["afetados"], p["afetados_corr"],
                 p["CRUA"], p["corrompida"], p["corrompida"] / max(1, p["louvores"])))
    print()
    print("DISTRIBUICAO (linhas de letra crua por louvor)")
    for a, b in ((0, 0), (1, 2), (3, 5), (6, 10), (11, 20), (21, 9999)):
        c = sum(1 for r in regs if a <= r["crua"] <= b)
        print("   %-8s %5d louvores" % (("%d" % a) if a == b else "%d-%d" % (a, b), c))
    print()
    print("O QUE DENUNCIA A LINHA CORROMPIDA (uma linha pode ter mais de uma marca)")
    for k, rot in (("marca_vocabulario", "palavra que o hinario nao tem"),
                   ("marca_lixo", "caractere impossivel (¡ [ ] ~ ^)"),
                   ("marca_letra_a_mais", "letra enfiada no meio (Jelsus)"),
                   ("marca_apostrofo", "apostrofo colado ('sangue)")):
        print("   %-34s %6d linhas" % (rot, total[k]))
    print("   %-34s %6d linhas" % ("(linhas cruas com acorde por cima)", total["crua_com_acorde"]))
    print()
    print("GRAVIDADE (por registro)")
    for rot, cond in (("nenhuma linha corrompida", lambda r: r["corr"] == 0),
                      ("1 a 4 linhas corrompidas", lambda r: 1 <= r["corr"] <= 4),
                      ("5 a 9 linhas corrompidas", lambda r: 5 <= r["corr"] <= 9),
                      ("10 ou mais corrompidas", lambda r: r["corr"] >= 10),
                      ("nem uma linha costurada (ok=0)", lambda r: r["costurada"] == 0)):
        print("   %-32s %5d" % (rot, sum(1 for r in regs if cond(r))))
    print()
    print("OS %d PIORES EM LETRA CORROMPIDA (o que o musico ve como lixo)" % piores)
    for r in sorted(regs, key=lambda r: -r["corr"])[:piores]:
        print("   %3d corrompidas / %3d linhas  %s%s"
              % (r["corr"], r["linhas"], r["chave"][:56],
                 "" if r["novo"] else "  [repetido]"))
        for f, sim, t, na, m in [c for c in r["cruas"] if c[4]][:2]:
            print("        > %s" % t[:86])
    print()
    print("OS %d PIORES (mais linhas de letra crua)" % piores)
    regs.sort(key=lambda r: (-r["crua"], -r["pct"]))
    for r in regs[:piores]:
        print("   %3d cruas (%2d corrompidas) / %3d linhas, %3.0f%% do corpo  %s%s"
              % (r["crua"], r["corr"], r["linhas"], 100 * r["pct"],
                 r["chave"][:56], "" if r["novo"] else "  [repetido]"))
        for f, sim, t, na, m in r["cruas"][:2]:
            print("        > %s" % t[:86])

    if csv:
        with io.open(csv, "w", encoding="utf-8") as f:
            f.write("chave;pdf;corpo_novo;linhas;crua;corrompida;legivel;costurada;"
                    "quase;acorde;nota;curta;ok_gravado;pct_crua\n")
            for r in sorted(regs, key=lambda r: -r["crua"]):
                f.write("%s;%s;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d;%.3f\n" % (
                    r["chave"].replace(";", ","), r["pdf"], int(r["novo"]), r["linhas"],
                    r["crua"], r["corr"], r["leg"], r["costurada"], r["quase"],
                    r["acorde"], r["nota"], r["curta"], r["ok"], r["pct"]))
        print("\ncsv: %s" % csv)


if __name__ == "__main__":
    main()
