# -*- coding: utf-8 -*-
"""Uma regua so' para as quatro lentes, para o ANTES e o DEPOIS serem compraveis.

Os quatro agentes mediram com quatro scripts diferentes, em snapshots diferentes
do acordes.json. Isso serve para achar o defeito, nao para provar o conserto:
numero medido com regua diferente nao se subtrai. Este script mede tudo de uma
vez, no mesmo arquivo, e imprime uma linha por medida.

Uso:  python medir_tudo.py                 (mede o acordes.json de producao)
      python medir_tudo.py caminho.json    (mede uma copia)
      python medir_tudo.py a.json b.json   (antes e depois, lado a lado)
"""
import io
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extrair_cifras import so_letras, eh_acorde, pasta_cifras  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NOTA = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "Fb": 4,
        "F": 5, "E#": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
        "A#": 10, "Bb": 10, "B": 11, "Cb": 11}


# --------------------------------------------------------------------------
#  bases
# --------------------------------------------------------------------------

def carregar_louvores():
    s = io.open(os.path.join(RAIZ, "dados", "louvores.js"), encoding="utf-8").read()
    L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    if isinstance(L, dict):
        L = L.get("louvores", L)
    return L


def por_chave(L):
    """chave do app -> conjunto de linhas ACEITAVEIS como letra costurada.

    Nao basta a letra daquela chave. O extrator grava a MESMA cifra sob todas as
    chaves do mesmo louvor (irmaos), e costura usando a letra de UM deles; as
    outras coletaneas escrevem o mesmo louvor com pequenas diferencas. Medindo
    so' contra a propria chave, a letra certa do irmao era contada como crua --
    e o numero PIORAVA justamente quando a costura passava a funcionar melhor.
    """
    linhas_de = {}
    por_titulo = defaultdict(set)
    for l in L:
        linhas = [li for sl in l.get("slides", []) for li in sl.get("linhas", [])]
        ch = "%s|%s|%s" % (l.get("num") or "", l.get("titulo") or "",
                           linhas[0] if linhas else "")
        linhas_de[ch] = linhas
        t = so_letras(l.get("titulo") or "")
        por_titulo[t].update(so_letras(x) for x in linhas)
    m = {}
    for ch, linhas in linhas_de.items():
        t = so_letras(ch.split("|")[1])
        m[ch] = (linhas, por_titulo.get(t, set()) | set(so_letras(x) for x in linhas))
    return m


def vocabulario(L):
    v = set()
    for l in L:
        txt = l.get("titulo", "") + " " + " ".join(
            li for sl in l.get("slides", []) for li in sl.get("linhas", []))
        for w in re.split(r"[^A-Za-zÀ-ÿ]+", so_letras(txt)):
            if w:
                v.add(w)
    return v


def melodias():
    cam = os.path.join(os.path.dirname(pasta_cifras()), "melodias", "indice.json")
    if not os.path.exists(cam):
        return {}
    idx = json.load(io.open(cam, encoding="utf-8")).get("louvores", {})
    out = {}
    for k, v in idx.items():
        tom = (v.get("tons") or {}).get("C")
        if tom:
            out[so_letras(v.get("titulo") or k)] = tom
    return out


# --------------------------------------------------------------------------
#  1. posicao do acorde
# --------------------------------------------------------------------------

def inicio_de_palavra(t, c):
    if c < 0 or c >= len(t) or not t[c].isalnum():
        return False
    return c == 0 or not t[c - 1].isalnum()


def medir_posicao(ac):
    n = grampeado = alem = no_espaco = ini_pal = empilhado = 0
    tudo_zero = 0
    louv_grampo = set()
    louv_qualquer = set()
    votos = Counter()
    for ch, reg in ac.items():
        tem = False
        for l in reg["linhas"]:
            t, a = l["t"], l["a"]
            if not a:
                continue
            cols = Counter(c for c, _ in a)
            if len(a) >= 3 and set(cols) == {0}:
                tudo_zero += len(a)
            for c, _nm in a:
                n += 1
                if c > len(t):
                    alem += 1
                elif c == len(t) and len(t):
                    grampeado += 1
                    louv_grampo.add(ch)
                    tem = True
                elif c < len(t) and t[c] == " ":
                    no_espaco += 1
                    tem = True
                if inicio_de_palavra(t, c):
                    ini_pal += 1
            empilhado += sum(v - 1 for v in cols.values() if v > 1)
            if any(v > 1 for v in cols.values()):
                tem = True
            # voto de deslocamento
            melhor, quanto = 0, sum(1 for c, _ in a if inicio_de_palavra(t, c))
            for d in (-3, -2, -1, 1, 2, 3):
                q = sum(1 for c, _ in a if inicio_de_palavra(t, c + d))
                if q > quanto:
                    melhor, quanto = d, q
            votos[melhor] += 1
        if tem:
            louv_qualquer.add(ch)
    return {"acordes": n, "grampeado": grampeado, "alem": alem,
            "no_espaco": no_espaco, "empilhado": empilhado,
            "tudo_zero": tudo_zero, "inicio_palavra": ini_pal,
            "louv_grampo": len(louv_grampo), "louv_defeito": len(louv_qualquer),
            "votos": votos}


# --------------------------------------------------------------------------
#  2. letra crua / corrompida
# --------------------------------------------------------------------------

IMPOSSIVEL = re.compile(r"[¡¿\[\]~^{}<>\\_]")
APOSTROFO = re.compile(r"(?:^|\s)['´`]\w")


def linha_corrompida(t, voc):
    if IMPOSSIVEL.search(t):
        return True
    if APOSTROFO.search(t):
        return True
    pal = [w for w in re.split(r"[^A-Za-zÀ-ÿ]+", so_letras(t)) if len(w) >= 4]
    if not pal:
        return False
    fora = [w for w in pal if w not in voc]
    if not fora:
        return False
    # letra enfiada no meio: tirar um caractere devolve palavra do hinario
    for w in fora:
        for i in range(1, len(w)):
            if w[:i] + w[i + 1:] in voc:
                return True
    return len(fora) >= max(1, len(pal) // 3)


def medir_letra(ac, mapa, voc):
    tot = costurada = crua = corrompida = 0
    crua_com_acorde = 0
    louv_crua, louv_corr = set(), set()
    grav = Counter()
    for ch, reg in ac.items():
        certas = mapa.get(ch, ([], set()))[1]
        n_corr = 0
        for l in reg["linhas"]:
            t = l["t"]
            tot += 1
            if so_letras(t) in certas and certas:
                costurada += 1
                continue
            if len(so_letras(t)) < 6:
                continue
            crua += 1
            louv_crua.add(ch)
            if l["a"]:
                crua_com_acorde += 1
            if linha_corrompida(t, voc):
                corrompida += 1
                n_corr += 1
                louv_corr.add(ch)
        # A GRAVIDADE, nao o sim/nao. "Tem pelo menos uma linha corrompida"
        # acende com um credito de autor no rodape da pagina e nao distingue o
        # louvor que perdeu 26 linhas de 36 daquele que perdeu uma.
        grav["limpo" if not n_corr else
             "1a4" if n_corr <= 4 else
             "5a9" if n_corr <= 9 else "10+"] += 1
    return {"linhas": tot, "costurada": costurada, "crua": crua,
            "corrompida": corrompida, "crua_com_acorde": crua_com_acorde,
            "louv_crua": len(louv_crua), "louv_corr": len(louv_corr),
            "grav": grav}


# --------------------------------------------------------------------------
#  3. acorde fora do campo harmonico
# --------------------------------------------------------------------------

RAIZ_AC = re.compile(r"^([A-G](?:#|b)?)(.*)$")


def parte(nome):
    m = RAIZ_AC.match(nome or "")
    if not m:
        return None, None
    r, resto = m.group(1), m.group(2)
    resto = resto.split("/")[0]
    if resto.startswith("m") and not resto.startswith("maj") and not resto.startswith("M"):
        q = "m"
    elif resto.startswith("dim") or resto.startswith("°") or resto.startswith("º"):
        q = "dim"
    elif resto.startswith("aug") or resto.startswith("+"):
        q = "aug"
    else:
        q = "M"
    return NOTA.get(r), q


def campo(tonica, menor):
    graus = ((0, "M"), (2, "m"), (4, "m"), (5, "M"), (7, "M"), (9, "m"), (11, "dim"))
    if menor:
        graus = ((0, "m"), (2, "dim"), (3, "M"), (5, "m"), (7, "m"), (7, "M"),
                 (8, "M"), (10, "M"))
    return set(((tonica + g) % 12, q) for g, q in graus)


def medir_campo(ac):
    fora = tot = 0
    tira_m = 0
    louv = set()
    com_tom = 0
    for ch, reg in ac.items():
        tom = reg.get("tom")
        if not tom:
            continue
        com_tom += 1
        t = tom.split(",")[0].split("/")[0].strip()
        menor = t.endswith("m")
        raiz = NOTA.get(t[:-1] if menor else t)
        if raiz is None:
            continue
        cf = campo(raiz, menor)
        ruim = 0
        for l in reg["linhas"]:
            for _c, nm in l["a"]:
                p = parte(nm)
                tot += 1
                if p[0] is None:
                    continue
                if p not in cf:
                    fora += 1
                    ruim += 1
                    if nm.startswith(nm[0]) and "m" in nm:
                        alt = nm.replace("m", "", 1)
                        if eh_acorde(alt) and parte(alt) in cf:
                            tira_m += 1
        if ruim:
            louv.add(ch)
    return {"acordes_com_tom": tot, "fora": fora, "tira_m": tira_m,
            "louvores": len(louv), "regs_com_tom": com_tom}


# --------------------------------------------------------------------------
#  4. tom contra a melodica
# --------------------------------------------------------------------------

def altura(tom):
    """(classe de altura, menor?) — 'Bb' e 'A#' sao a MESMA tecla. Comparar a
    grafia acusaria erro onde os dois livros so' escolheram nomes diferentes."""
    t = (tom or "").split(",")[0].split("/")[0].strip().replace(" ", "")
    menor = t.endswith("m") and not t.endswith("M")
    if menor:
        t = t[:-1]
    return NOTA.get(t[:1].upper() + t[1:2].replace("B", "b")), menor


def medir_tom(ac, mel):
    bate = erra = 0
    lista = []
    vistos = set()
    for ch, reg in ac.items():
        tom = reg.get("tom")
        if not tom:
            continue
        tit = so_letras(ch.split("|")[1])
        m = mel.get(tit)
        if not m or tit in vistos:
            continue
        a = tom.split(",")[0].split("/")[0].strip()
        pa, ma_ = altura(a)
        pb, mb = altura(m)
        if pa is None or pb is None:
            continue
        vistos.add(tit)
        if (pa, ma_) == (pb, mb):
            bate += 1
        else:
            erra += 1
            lista.append((tit, a, m))
    return {"pares": bate + erra, "bate": bate, "erra": erra, "lista": lista}


# --------------------------------------------------------------------------

def medir(caminho, L, mapa, voc, mel):
    ac = json.load(io.open(caminho, encoding="utf-8"))
    r = {"arquivo": caminho, "registros": len(ac)}
    r["pos"] = medir_posicao(ac)
    r["letra"] = medir_letra(ac, mapa, voc)
    r["campo"] = medir_campo(ac)
    r["tom"] = medir_tom(ac, mel)
    r["sem_tom"] = sum(1 for v in ac.values() if not v.get("tom"))
    r["poucos"] = sum(1 for v in ac.values()
                      if sum(len(l["a"]) for l in v["linhas"]) < 8)
    return r


def pct(a, b):
    return "%5.1f%%" % (100.0 * a / b) if b else "   -  "


def mostrar(rs):
    def linha(rot, f, base=None):
        vs = []
        for r in rs:
            v = f(r)
            b = base(r) if base else None
            vs.append("%8d %s" % (v, pct(v, b)) if b is not None else "%8d       " % v)
        print("  %-34s %s" % (rot, "".join(vs)))

    print("\n" + "=" * 78)
    print("  %-34s %s" % ("", "".join("%15s " % os.path.basename(r["arquivo"])[:15]
                                      for r in rs)))
    print("=" * 78)
    linha("registros", lambda r: r["registros"])
    print("\n-- POSICAO DO ACORDE " + "-" * 56)
    linha("acordes posicionados", lambda r: r["pos"]["acordes"])
    linha("GRAMPEADOS no fim da linha", lambda r: r["pos"]["grampeado"],
          lambda r: r["pos"]["acordes"])
    linha("empilhados (mesma coluna)", lambda r: r["pos"]["empilhado"],
          lambda r: r["pos"]["acordes"])
    linha("caindo em cima de espaco", lambda r: r["pos"]["no_espaco"],
          lambda r: r["pos"]["acordes"])
    linha("tudo na coluna zero", lambda r: r["pos"]["tudo_zero"],
          lambda r: r["pos"]["acordes"])
    linha("no INICIO de uma palavra (bom)", lambda r: r["pos"]["inicio_palavra"],
          lambda r: r["pos"]["acordes"])
    linha("louvores com grampo", lambda r: r["pos"]["louv_grampo"],
          lambda r: r["registros"])
    linha("louvores com defeito de posicao", lambda r: r["pos"]["louv_defeito"],
          lambda r: r["registros"])
    for r in rs:
        v = r["pos"]["votos"]
        tot = sum(v.values()) or 1
        print("      deslocamento que melhoraria: " + ", ".join(
            "%+d:%.0f%%" % (d, 100.0 * n / tot) for d, n in v.most_common(4)))
    print("\n-- LETRA " + "-" * 68)
    linha("linhas", lambda r: r["letra"]["linhas"])
    linha("COSTURADA (letra certa do app)", lambda r: r["letra"]["costurada"],
          lambda r: r["letra"]["linhas"])
    linha("crua (nao costurou)", lambda r: r["letra"]["crua"],
          lambda r: r["letra"]["linhas"])
    linha("CORROMPIDA pelo OCR", lambda r: r["letra"]["corrompida"],
          lambda r: r["letra"]["linhas"])
    linha("crua COM acorde por cima", lambda r: r["letra"]["crua_com_acorde"],
          lambda r: r["letra"]["linhas"])
    linha("louvores com linha crua", lambda r: r["letra"]["louv_crua"],
          lambda r: r["registros"])
    linha("louvores com linha corrompida", lambda r: r["letra"]["louv_corr"],
          lambda r: r["registros"])
    for rot in ("limpo", "1a4", "5a9", "10+"):
        linha("   gravidade: %s linhas corrompidas" % rot,
              lambda r, x=rot: r["letra"]["grav"][x], lambda r: r["registros"])
    print("\n-- CAMPO HARMONICO " + "-" * 58)
    linha("acordes em louvor com tom", lambda r: r["campo"]["acordes_com_tom"])
    linha("fora do campo (estrito)", lambda r: r["campo"]["fora"],
          lambda r: r["campo"]["acordes_com_tom"])
    linha("   dos quais: some tirando um 'm'", lambda r: r["campo"]["tira_m"],
          lambda r: r["campo"]["fora"])
    linha("louvores com acorde fora", lambda r: r["campo"]["louvores"],
          lambda r: r["registros"])
    print("\n-- TOM " + "-" * 70)
    linha("pares conferiveis com a melodica", lambda r: r["tom"]["pares"])
    linha("tom BATE com a melodica", lambda r: r["tom"]["bate"],
          lambda r: r["tom"]["pares"])
    linha("tom ERRADO", lambda r: r["tom"]["erra"], lambda r: r["tom"]["pares"])
    linha("registros SEM tom nenhum", lambda r: r["sem_tom"],
          lambda r: r["registros"])
    linha("registros com menos de 8 acordes", lambda r: r["poucos"],
          lambda r: r["registros"])
    print()


def main():
    alvos = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not alvos:
        alvos = [os.path.join(pasta_cifras(), "acordes.json")]
    L = carregar_louvores()
    mapa, voc, mel = por_chave(L), vocabulario(L), melodias()
    sys.stderr.write("banco: %d louvores, %d palavras, %d melodicas com tom\n"
                     % (len(L), len(voc), len(mel)))
    rs = [medir(a, L, mapa, voc, mel) for a in alvos]
    mostrar(rs)
    if len(rs) == 1 and rs[0]["tom"]["erra"]:
        print("  tom divergente (cifra -> melodica):")
        for t, a, m in sorted(rs[0]["tom"]["lista"])[:40]:
            print("    %-46s %-5s -> %s" % (t[:46], a, m))


if __name__ == "__main__":
    main()
