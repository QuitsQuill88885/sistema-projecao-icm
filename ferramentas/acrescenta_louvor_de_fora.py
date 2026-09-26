# -*- coding: utf-8 -*-
"""Acrescenta ao acervo um louvor que NAO esta em livro nenhum desta maquina,
a partir de uma pagina do louvando.app — slide do telao E cifra, da MESMA fonte.

POR QUE ASSIM (26/09/2026, ensaio das criancas): o louvor 'Fui lavado no sangue
do Cordeiro' (avulso das CIAs) nao existia no acervo. Ordem dele: "lance tudo
nas cifras e tudo mais. Slide, etc."

  * telao e cifra saem do MESMO texto -> a trava da letra da 100% por construcao
    (regra da casa: telao e cifra sao a mesma letra);
  * a chave da cifra e' montada igual ao app.js:1540 (num|titulo|primeira linha
    do primeiro slide, SEM normalizar) -> a cifra nao fica orfa calada;
  * o louvor entra em dados/consertos_louvores.json -> "acrescimos", que o
    aplicar_consertos_louvores.py repoe depois de TODA regeneracao do acervo.
    Sem isso ele sumiria na proxima vez que o gen_louvores.py rodasse.

Uso:
  python ferramentas/acrescenta_louvor_de_fora.py <pagina.html> --col "Avulsos 2018" --num AV
  ... --gravar      (sem --gravar so mostra o que faria)
"""
import argparse, html, io, json, os, re, shutil, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CON = os.path.join(RAIZ, "dados", "consertos_louvores.json")
ACO = os.path.join(RAIZ, "conteudo_leve", "cifras", "acordes.json")
MAX_LINHAS_SLIDE = 4


def payload_next(pagina):
    """O louvando.app manda a pagina em pedacos do Next.js; junta e desescapa."""
    t = io.open(pagina, encoding="utf-8", errors="replace").read()
    pedacos = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', t, re.S)
    bruto = "".join(pedacos)
    return (bruto.encode("utf-8").decode("unicode_escape")
            .encode("latin-1", errors="ignore").decode("utf-8", errors="ignore"))


def dados_do_louvor(bruto):
    m = re.search(r'"title":"([^"]+)","tone":"([^"]*)"', bruto)
    if not m:
        sys.exit("nao achei titulo/tom na pagina — PAREI")
    titulo, tom = m.group(1).strip(), m.group(2)
    ref = re.search(r'"chords":"\$(\w+)"', bruto)
    if not ref:
        sys.exit("a pagina nao tem cifra — PAREI")
    i = bruto.find(ref.group(1) + ":T")
    if i < 0:
        sys.exit("referencia da cifra $%s nao resolvida — PAREI" % ref.group(1))
    corpo = bruto[bruto.index(",", i) + 1:]
    # a cifra termina onde comeca o proximo bloco do Next.js ("</p>9:[...")
    fim = re.search(r"</p>(?=[0-9a-f]+:[\[\"T])", corpo)
    if not fim:
        sys.exit("nao achei o fim da cifra na pagina — PAREI")
    return titulo, tom, corpo[:fim.start() + 4]


def le_paragrafos(corpo):
    """Cada <p> vira (texto, [[pos, acorde]...], eh_titulo).
    Acorde 'bellowBar' fica EM CIMA da silaba seguinte -> vira posicao.
    Acorde sem bellowBar (introducao, instrumentos) e' texto corrido."""
    saida = []
    for p in re.findall(r"<p>(.*?)</p>", corpo, re.S):
        if html.unescape(re.sub(r"<[^>]+>", "", p)).strip() == "":
            continue
        eh_titulo = bool(re.fullmatch(r"\s*<strong>.*</strong>\s*", p, re.S)) \
            and "bellowBar" not in p
        texto, acordes = "", []
        for pedaco in re.split(r'(<span class="chord[^"]*">.*?</span>)', p, flags=re.S):
            m = re.match(r'<span class="(chord[^"]*)">(.*?)</span>', pedaco, re.S)
            if m:
                nome = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
                if "bellowBar" in m.group(1):
                    acordes.append([len(texto), nome])
                else:
                    texto += nome
            else:
                texto += html.unescape(re.sub(r"<[^>]+>", "", pedaco))
        texto = texto.replace("\xa0", " ").rstrip()
        saida.append((texto, acordes, eh_titulo))
    return saida


def monta(paragrafos):
    """Letra em MAIUSCULA (padrao do telao), titulos e ritmo como estao.
    Devolve (linhas_da_cifra, slides)."""
    cifra, slides, rotulo, bloco = [], [], "", []

    def fecha():
        nonlocal bloco, rotulo
        for i in range(0, len(bloco), MAX_LINHAS_SLIDE):
            slides.append({"label": rotulo if i == 0 else "",
                           "linhas": bloco[i:i + MAX_LINHAS_SLIDE]})
        bloco = []

    for texto, acordes, eh_titulo in paragrafos:
        nome_bloco = texto.strip().rstrip(":").upper()
        eh_letra = not eh_titulo and not re.match(r"(?i)\s*(ritmo|introdu|instrumentos)", texto)
        if eh_titulo and nome_bloco in ("CORO", "FINAL"):
            fecha()
            rotulo = nome_bloco
            cifra.append({"t": texto.strip(), "a": []})
        elif eh_letra:
            linha = texto.strip().upper()
            desloc = len(texto) - len(texto.lstrip())
            cifra.append({"t": linha, "a": [[max(0, p - desloc), a] for p, a in acordes]})
            bloco.append(linha)
        else:
            # ritmo/introducao podem vir no MESMO <p> separados por quebra: uma linha cada
            for pedaco in texto.split("\n"):
                if pedaco.strip():
                    cifra.append({"t": " ".join(pedaco.split()), "a": []})
    fecha()
    return cifra, slides


def grava_json(caminho, obj, **kw):
    novo = caminho + ".novo"
    with io.open(novo, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, **kw))
    os.replace(novo, caminho)


def estilo_do(caminho):
    """Grava do mesmo jeito que o arquivo ja esta (acento cru ou escapado, indentado ou nao)."""
    cab = io.open(caminho, encoding="utf-8").read(4000)
    return {"ensure_ascii": "\\u00" in cab and not re.search(r"[À-ÿ]", cab),
            **({"indent": 1} if cab.startswith("{\n") else {"separators": (",", ":")})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pagina")
    ap.add_argument("--col", required=True)
    ap.add_argument("--num", required=True)
    ap.add_argument("--fonte", default="")
    ap.add_argument("--ordem", default="",
                    help="ordem CANTADA dos slides, 1-based, ex. 1,2,1,3 (tirada OUVINDO a gravacao)")
    ap.add_argument("--gravar", action="store_true")
    a = ap.parse_args()

    titulo, tom, corpo = dados_do_louvor(payload_next(a.pagina))
    cifra, slides = monta(le_paragrafos(corpo))

    if a.ordem:
        # a pagina escreve cada bloco UMA vez; a gravacao diz quando ele VOLTA.
        # Slide que volta vira slide repetido (padrao do acervo: CORO de novo com
        # rotulo CORO), e a cifra ganha a marca "(volta ao Coro)" onde a volta acontece.
        idx = [int(x) - 1 for x in a.ordem.split(",")]
        if any(i < 0 or i >= len(slides) for i in idx):
            sys.exit("--ordem fora do numero de slides (%d) — PAREI" % len(slides))
        vistos, novos = set(), []
        for k, i in enumerate(idx):
            if i in vistos and k > 0:
                ultima = novos[-1]["linhas"][-1]
                pos = max(j for j, c in enumerate(cifra) if c["t"] == ultima)
                nome = (slides[i]["label"] or "estrofe").capitalize()
                cifra.insert(pos + 1, {"t": "(volta ao %s)" % nome, "a": []})
            vistos.add(i)
            novos.append({"label": slides[i]["label"], "linhas": list(slides[i]["linhas"])})
        slides = novos
    louvor = {"num": a.num, "titulo": titulo, "col": a.col, "slides": slides}
    chave = "%s|%s|%s" % (a.num, titulo, slides[0]["linhas"][0])  # = app.js chaveLouvor

    print("titulo:", titulo, "| tom:", tom, "| colecao:", a.col, "| num:", a.num)
    print("chave da cifra:", chave)
    print("\nTELAO (%d slides):" % len(slides))
    for s in slides:
        print("  [%s]" % (s["label"] or "-"))
        for l in s["linhas"]:
            print("     ", l)
    print("\nCIFRA (%d linhas):" % len(cifra))
    for c in cifra:
        acima = [" "] * (max([p + len(n) for p, n in c["a"]] + [0]) + 1)
        for p, n in c["a"]:
            acima[p:p + len(n)] = list(n)
        if c["a"]:
            print("      " + "".join(acima).rstrip())
        print("      " + c["t"])

    # prova: telao e cifra com a MESMA letra (nos dois sentidos; slide repetido e'
    # a mesma letra de novo, entao compara o CONJUNTO de linhas, nao a sequencia)
    letra_telao = {l for s in slides for l in s["linhas"]}
    letra_cifra = {c["t"] for c in cifra if c["t"].isupper()}
    igual = letra_telao == letra_cifra
    print("\nPROVA telao == cifra (%d linhas distintas):" % len(letra_telao),
          "OK" if igual else "!! DIFERENTE %s" % (letra_telao ^ letra_cifra))
    if not igual:
        sys.exit("PAREI: telao e cifra divergem")

    if not a.gravar:
        print("\n(so mostrei; rode com --gravar)")
        return

    stamp = time.strftime("%Y%m%d_%H%M")
    # 1. acrescimo duravel
    con = json.load(io.open(CON, encoding="utf-8"))
    shutil.copy2(CON, "%s.antes_de_%s.bak" % (CON, stamp))
    acr = [x for x in con.get("acrescimos", [])
           if not (x["num"] == a.num and x["col"] == a.col and x["titulo"] == titulo)]
    acr.append(dict(louvor, fonte=a.fonte, quando=stamp, tom=tom))
    con["acrescimos"] = acr
    grava_json(CON, con, **estilo_do(CON))
    print("\n1. consertos_louvores.json: acrescimos =", len(acr))

    # 2. cifra no banco
    ACOR = json.load(io.open(ACO, encoding="utf-8"))
    ja = chave in ACOR
    bak = os.path.join(os.path.dirname(ACO), "acordes_antes_de_%s.json" % stamp)
    shutil.copy2(ACO, bak)
    ACOR[chave] = {"linhas": cifra}
    grava_json(ACO, ACOR, **estilo_do(bak))
    print("2. acordes.json: cifra %s (%d cifras) | backup %s"
          % ("SUBSTITUIDA" if ja else "nova", len(ACOR), os.path.basename(bak)))
    print("\nFALTA: rodar aplicar_consertos_louvores.py (poe no louvores.js), "
          "recompilar, e refazer_conteudo_zip.py")


if __name__ == "__main__":
    main()
