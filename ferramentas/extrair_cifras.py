# -*- coding: utf-8 -*-
"""Tira os acordes dos PDFs e transforma a cifra em texto do Sistema.

POR QUE: hoje a cifra é um PDF de 89 MB aberto no leitor do navegador. No
computador da igreja isso pesa, e no celular — que puxa o arquivo do próprio
computador da igreja — pesa muito mais. Depois desta extração a cifra vira
alguns kilobytes de texto, desenhada no visual do Sistema, instantânea.

COMO: o pypdf entrega cada pedaço de texto com a coordenada (x, y). Agrupando
por altura chega-se às linhas; uma linha em que TODOS os pedaços são acordes
("Gm", "D", "Bm", "E7", "A/C#") é linha de acorde, e o x de cada um diz sobre
qual sílaba da linha de baixo ele cai.

SAÍDA — %APPDATA%\\Sistema Projecao\\cifras\\acordes.json
    { "<chave do louvor>": {
        "tom": "G",
        "linhas": [ {"t": "linha", "a": [[coluna, "acorde"], ...]}, ... ] } }

Uso:  python extrair_cifras.py
      python extrair_cifras.py --limite 30     (só as 30 primeiras, para conferir)
"""
import io, json, os, re, sys
from collections import defaultdict

# "A", "Bm", "C#m7", "F#", "Bb", "G/B", "Dsus4", "E7M"
ACORDE = re.compile(r"^[A-G](#|b)?(m|M|maj|min|dim|aug|sus|add)?[0-9]{0,2}(\+|-)?(/[A-G](#|b)?)?$")
LARG_CAR = 5.0          # largura média de um caractere, em pontos de PDF


def pasta_cifras():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Sistema Projecao", "cifras")


def eh_acorde(t):
    t = t.strip()
    return bool(t) and len(t) <= 8 and bool(ACORDE.match(t))


def linhas_da_pagina(pagina):
    """[(y, [(x, texto), ...])], de cima para baixo."""
    itens = []

    def visita(texto, cm, tm, fonte, tam):
        t = (texto or "").rstrip("\n")
        if t.strip():
            itens.append((round(tm[5], 1), tm[4], t))

    pagina.extract_text(visitor_text=visita)
    por_y = defaultdict(list)
    for y, x, t in itens:
        por_y[round(y)].append((x, t))
    return [(y, sorted(por_y[y])) for y in sorted(por_y, reverse=True)]


def montar(pagina):
    """[{'t': linha, 'a': [[coluna, acorde], ...]}] — o acorde cai na linha de baixo."""
    saida = []
    guardados = None
    for _y, frags in linhas_da_pagina(pagina):
        toks = [(x, t.strip()) for x, t in frags if t.strip()]
        if not toks:
            continue
        if all(eh_acorde(t) for _x, t in toks):
            guardados = toks          # espera a linha de letra que vem abaixo
            continue
        texto = "".join(t for _x, t in frags).rstrip()
        if not texto.strip():
            continue
        acordes = []
        if guardados:
            x0 = frags[0][0]
            for x, a in guardados:
                acordes.append([max(0, int(round((x - x0) / LARG_CAR))), a])
            guardados = None
        saida.append({"t": texto, "a": acordes})
    return saida


def extrair(pasta=None, limite=0, aviso=None):
    from pypdf import PdfReader
    pasta = pasta or pasta_cifras()
    caminho_idx = os.path.join(pasta, "indice.json")
    if not os.path.exists(caminho_idx):
        raise SystemExit("Nao achei o indice das cifras. Rode indexar_cifras.py antes.")
    indice = json.load(io.open(caminho_idx, encoding="utf-8"))

    por_pdf = defaultdict(list)           # abrir cada PDF uma vez só
    for chave, ref in indice.items():
        por_pdf[ref["pdf"]].append((chave, ref))

    acordes, feitos = {}, 0
    for nome, itens in sorted(por_pdf.items()):
        cam = os.path.join(pasta, nome)
        if not os.path.exists(cam):
            continue
        if aviso:
            aviso("lendo %s (%d louvores)" % (nome, len(itens)))
        r = PdfReader(cam)
        cache = {}
        for chave, ref in itens:
            p = ref["pag"] - 1
            if p < 0 or p >= len(r.pages):
                continue
            if p not in cache:
                try:
                    cache[p] = montar(r.pages[p])
                except Exception:
                    cache[p] = []
            linhas = cache[p]
            if not any(l["a"] for l in linhas):      # página sem acorde não serve
                continue
            reg = {"linhas": linhas}
            if ref.get("tom"):
                reg["tom"] = ref["tom"]
            acordes[chave] = reg
            feitos += 1
            if limite and feitos >= limite:
                break
        if limite and feitos >= limite:
            break

    destino = os.path.join(pasta, "acordes.json")
    tmp = destino + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(acordes, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, destino)
    return acordes, destino


def main():
    limite = 0
    if "--limite" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--limite") + 1])
    acordes, destino = extrair(limite=limite, aviso=lambda m: sys.stderr.write("  " + m + "\n"))
    n_ac = sum(len(l["a"]) for v in acordes.values() for l in v["linhas"])
    n_li = sum(len(v["linhas"]) for v in acordes.values())
    print("louvores com cifra em texto : %d" % len(acordes))
    print("linhas                      : %d" % n_li)
    print("acordes posicionados        : %d" % n_ac)
    print("arquivo                     : %s (%.0f KB)"
          % (destino, os.path.getsize(destino) / 1024.0))


if __name__ == "__main__":
    main()
