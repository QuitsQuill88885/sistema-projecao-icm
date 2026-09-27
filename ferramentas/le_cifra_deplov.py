# -*- coding: utf-8 -*-
"""Le a LISTA DE LOUVORES CIFRADOS do DEPLOV (www.louvoricm.org.br) — a cifra OFICIAL da ICM —
e devolve cada louvor no formato do banco de cifras do Sistema: {"linhas": [{"t", "a"}]}.

COMO O PDF MARCA O ACORDE (medido em 26/09/2026, lista das CIAs de outubro/2026):
a linha de cima tem os acordes; na letra, cada "|" marca ONDE entra o proximo acorde,
na ordem. Se ha um acorde a mais que "|", o primeiro vai no comeco da linha.
    E               B            C#m
    Eu |clamo, eu |oro pelo |sangue lá da cruz,   ->  E em "clamo", B em "oro", C#m em "sangue"
Assim a posicao NAO depende do espacamento do texto extraido (que o PDF baguca).

QUATRO ARMADILHAS DESTE PDF (consertadas em 27/09/2026):
1. acorde diminuto vem com "º" (ordinal masculino, U+00BA) em Gº/Cº/Fº e com "°" (grau,
   U+00B0) em C#° — na MESMA pagina. Os dois valem.
2. a linha de acordes pode terminar com uma PASSAGEM INSTRUMENTAL em compassos
   ("C | % | Am | % | E ||"): esses acordes nao entram na letra, vao no fim da linha.
3. o PDF parte palavra com hifen bem onde entra o acorde ("cora-|ções", "von|ta - |de"):
   o hifen some e a marca fica ("cora|ções", "von|ta|de").
4. "Coro (bis)", "Coro (bis no final)" e "| Bis no final" sao MARCA de repeticao,
   nao letra.

QUANDO O LEITOR NAO TEM CERTEZA ele avisa (lv["avisos"]) — conferir esses a olho.

Uso:  python le_cifra_deplov.py <arquivo.pdf> [--mostrar N]"""
import io, json, re, sys
import pymupdf

# "º" (U+00BA) e "°" (U+00B0) aparecem os dois neste PDF, no mesmo louvor
ACORDE = re.compile(r"^[A-G](?:#|b)?(?:m|maj7|maj|min|dim|°|º|aug|sus2|sus4|sus|add9|[0-9]|M7|\+)*"
                    r"(?:\((?:sus[24]|maj[79]|add9|dim|m|[0-9b#+]+)\))?(?:/[A-G](?:#|b)?)?$")
COMPASSO = re.compile(r"^(?:\|\|?|:\|\|?|\|\|:|%)$")   # barra de compasso, ritornello, "toca igual"
CABECALHO = re.compile(r"LISTA DE LOUVORES CIFRADOS|^Tema:|louvoricm\.org|^DEPLOV")
SECAO = re.compile(r"^\s*(?:Durante|Ap[óo]s)\s+a\s+Palavra\s*:\s*$", re.I)
TITULO = re.compile(r"^\s*(?:(\d{2}(?:/\d{2})?)\s*[-–]\s*)?([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ ,!?]{6,}?)\s*(?:\((\d+)\))?\s*$")
# marcas de repeticao
CORO = re.compile(r"^(Coro|Final)\s*:?\s*(?:\(\s*bis(\s+no\s+final)?\s*\))?\s*:?$", re.I)
BIS = re.compile(r"^\|?\s*Bis(\s+no\s+final)?\s*\.?$", re.I)
SO_BARRA = re.compile(r"^[|\s]+$")


def eh_linha_de_acordes(l):
    toks = l.split()
    return bool(toks) and all(ACORDE.match(t) or COMPASSO.match(t) for t in toks) \
        and any(ACORDE.match(t) for t in toks)


def parte_cauda(pend_cru):
    """Separa a linha de acordes em (acordes da letra, cauda instrumental em texto).
    A cauda comeca na primeira barra de compasso."""
    toks = pend_cru.split()
    for i, t in enumerate(toks):
        if COMPASSO.match(t):
            return toks[:i], " ".join(toks[i:])
    return toks, ""


def ler(pdf):
    linhas = []
    for p in pymupdf.open(pdf):
        linhas += p.get_text().splitlines()
    linhas = [l.rstrip() for l in linhas if not CABECALHO.search(l)]

    louvores, atual, pend, pend_cru = [], None, None, ""
    i = 0
    while i < len(linhas):
        l = linhas[i]
        s = l.strip()
        m = TITULO.match(l)
        # titulo de louvor: em maiusculas e SEGUIDO de "Ritmo" nas proximas linhas
        if m and any(re.match(r"\s*Rit[mn]o", x) for x in linhas[i + 1:i + 4]):
            atual = {"titulo": m.group(2).strip().rstrip("?").strip(), "num": m.group(3),
                     "cab": [], "linhas": []}
            louvores.append(atual)
            pend, pend_cru = None, ""
            i += 1
            continue
        if re.match(r"EVANGELIZA[ÇC][ÃA]O DE|PER[ÍI]ODO DE LOUVOR", s, re.I):
            atual, pend = None, None                   # comecou a pagina da lista: acabou o louvor
            i += 1
            continue
        if SECAO.match(s):                             # "Durante a Palavra:" / "Após a Palavra:"
            i += 1                                     # e rotulo da lista, nao e letra
            continue
        if atual is None or not s:
            i += 1
            continue
        if re.match(r"(Rit[mn]o|Q\s*[.=]|Introdu)", s) and not atual["linhas"]:
            atual["cab"].append(re.sub(r"\s+", " ", s.replace("Ritno", "Ritmo")))
        elif eh_linha_de_acordes(s):
            pend_cru = l
            pend, _ = parte_cauda(l)
        elif SO_BARRA.match(s):
            pass                                       # colchete de repeticao sozinho
        elif BIS.match(s):
            # o PDF desenha o colchete do bis NO MEIO do texto: se a ultima linha de letra
            # termina em virgula, a frase (e o bis) ainda nao acabou -> fecha depois da proxima
            no_final = bool(re.search(r"no\s+final", s, re.I))
            ult = next((x["t"] for x in reversed(atual["linhas"]) if not x["t"].startswith("(bis")), "")
            selo = "(bis no final)" if no_final else "(bis)"
            if not re.search(r"[.!?…][\"”')\]]?\s*$", ult):
                atual["bis_pendente"] = selo
            else:
                atual["linhas"].append({"t": selo, "a": []})
        elif CORO.match(s):
            g = CORO.match(s)
            rot = g.group(1).capitalize() + (":" if s.rstrip().endswith(":") else "")
            if re.search(r"\(\s*bis", s, re.I):
                rot = rot.rstrip(":") + (" (bis no final)" if g.group(2) else " (bis)")
            atual["linhas"].append({"t": rot, "a": []})
            pend, pend_cru = None, ""
        elif re.match(r"(Final|Instrumentos?)\s*:?\s", s, re.I) and "|" in s \
                and eh_linha_de_acordes(re.sub(r"^(Final|Instrumentos?)\s*:?", "", s, flags=re.I)):
            atual["linhas"].append({"t": re.sub(r"\s+", " ", s), "a": []})   # "Final: A | B | ..."
            pend, pend_cru = None, ""
        else:
            texto = s
            g = re.match(r"^(Final|Coro)\s*:\s*(\S.*)$", texto, re.I)
            if g:                                   # "Final: Je|sus." -> rotulo + letra
                atual["linhas"].append({"t": g.group(1).capitalize() + ":", "a": []})
                texto = g.group(2)
            bis = bool(re.search(r"\|\s*Bis(\s+no\s+final)?\s*$", texto, re.I))
            bis_final = bool(re.search(r"\|\s*Bis\s+no\s+final\s*$", texto, re.I))
            texto = re.sub(r"\|\s*Bis(\s+no\s+final)?\s*$", "", texto, flags=re.I).rstrip()
            # o PDF parte a palavra com hifen exatamente onde entra o acorde: "cora-|ções",
            # "von|ta - |de" -> o hifen nao e do texto, e da quebra. Some, a marca fica.
            texto = re.sub(r"\s*-\s*\|", "|", texto)
            col_marca = texto.find("|")                # coluna da 1a marca, no texto ORIGINAL
            posicoes, limpo = [], ""
            for ch in texto:
                if ch == "|":
                    posicoes.append(len(limpo))
                else:
                    limpo += ch
            limpo = limpo.strip()
            desloc = len(texto.replace("|", "")) - len(texto.replace("|", "").lstrip())
            posicoes = [max(0, p - desloc) for p in posicoes]
            acordes = []
            if pend:
                cauda = parte_cauda(pend_cru)[1]
                usa = list(pend)
                # um acorde a mais que marca = o primeiro entra no comeco da linha.
                # so vale se ele estiver IMPRESSO a esquerda da 1a marca (senao e cauda).
                col_ac = len(pend_cru) - len(pend_cru.lstrip())
                comeco = len(usa) >= len(posicoes) + 1 and (col_marca < 0 or col_ac < col_marca)
                cabem = len(posicoes) + (1 if comeco else 0)
                sobra = usa[cabem:]
                usa = usa[:cabem]
                pos = ([0] + posicoes) if comeco else posicoes
                acordes = [[p, c] for p, c in zip(pos, usa)]
                if sobra:
                    cauda = (" ".join(sobra) + " " + cauda).strip()
                    atual.setdefault("avisos", []).append(
                        "%d acorde(s) sobrando em %r -> foram para o fim: %s"
                        % (len(sobra), limpo[:34], " ".join(sobra)))
                if len(usa) < len(posicoes):
                    atual.setdefault("avisos", []).append(
                        "faltou acorde para %d marca(s) em %r" % (len(posicoes) - len(usa), limpo[:34]))
                if cauda:
                    acordes.append([len(limpo) + 2, cauda])
            if limpo:
                atual["linhas"].append({"t": limpo.upper(), "a": acordes})
                # colchete aberto no meio do bloco: so fecha na linha que ACABA a frase
                selo = atual.get("bis_pendente")
                if selo and re.search(r"[.!?…][\"”')\]]?\s*$", limpo):
                    atual.pop("bis_pendente")
                elif selo:
                    selo = None
                if bis_final or bis:
                    selo = "(bis no final)" if bis_final else "(bis)"
                if selo:
                    atual["linhas"].append({"t": selo, "a": []})
            pend, pend_cru = None, ""
        i += 1
    return louvores


def mostra(lv):
    print("=" * 60)
    print("%s (%s)" % (lv["titulo"], lv["num"]))
    for c in lv["cab"]:
        print("  " + c)
    for ln in lv["linhas"]:
        if ln["a"]:
            topo, fim = "", -1
            for p, c in sorted(ln["a"], key=lambda z: z[0]):
                p = max(p, fim + 2 if fim >= 0 else p)
                topo = topo.ljust(p) + c
                fim = len(topo) - 1
            print("    " + topo)
        print("    " + ln["t"])
    for a in lv.get("avisos", []):
        print("  ⚠", a)


if __name__ == "__main__":
    L = ler(sys.argv[1])
    print("louvores lidos:", len(L), [x["titulo"] for x in L])
    if "--mostrar" in sys.argv:
        for lv in L[:int(sys.argv[sys.argv.index("--mostrar") + 1])]:
            mostra(lv)
