# -*- coding: utf-8 -*-
"""Transforma as Coletâneas Melódicas da ICM em cadernos por instrumento.

O QUE SÃO ESSES PDFs
====================
São a MESMA coletânea publicada em dois tons, para instrumentos diferentes:

    COLETÂNEA PARA INSTRUMENTOS EM C    136 páginas (parcial)
    COLETÂNEA PARA INSTRUMENTOS EM Bb   429 páginas (completa)

O mesmo louvor aparece em Em na primeira e F#m na segunda — os dois semitons
que separam quem lê em Dó de quem lê em Si bemol. Confirmado em três louvores:
Aquilo que fui (Em / F#m), Clamo a Ti (Dm / Em), Prostrado estou (D / E).

A DE Bb É A COMPLETA, e é dela que sai tudo. As outras são geradas por
transposição, inclusive a de Mi bemol, que não existe em PDF nenhum:

    em C   (violino, flauta, teclado, violão)   = Bb  - 2 semitons
    em Bb  (sax tenor, soprano, trompete)       = como está
    em Eb  (sax alto, sax barítono)             = Bb  + 7 semitons
    em F   (trompa)                             = Bb  + 5 semitons

FORMATO DA PÁGINA — texto nativo, alternando notas e letra:

    3 - CLAMO A TI (Em)
    Introdução: Pelo teu sangue, que é vida...
    B A# B D C A | C C B G |          <- notas da melodia, "|" separa compasso
    Clamo a ti, ó meu Senhor,         <- a letra correspondente

ISTO NÃO VAI PARA O TELÃO. É material de músico: cada instrumentista abre no
celular o caderno do SEU instrumento, e quatro pessoas podem estar lendo tons
diferentes do mesmo louvor ao mesmo tempo. Por isso a saída é um arquivo por
louvor, pequeno, servido sob demanda — nada de mandar a coletânea inteira para
um celular que quer uma página.

Uso:  python extrair_melodia.py
      python extrair_melodia.py --limite 20
"""
import io
import json
import os
import re
import sys
import unicodedata

# nota solta da melodia: A, A#, Bb, C#... (sem acorde, sem baixo)
NOTA = re.compile(r"^[A-G](#|b)?$")
# O tom e' OPCIONAL e pode vir seguido de asterisco: metade dos cabecalhos
# nao tem tom nenhum ("2 - O SANGUE DE JESUS TEM PODER") e outros marcam o
# louvor com "*" depois do tom ("16 - SE ANDARMOS NA LUZ (F#)*"). Exigir os
# parenteses jogava fora 59 de cada 119.
# DOIS regexes, e o COM tom e' tentado primeiro. Num regex so, com o grupo do
# tom opcional, o ".+?" preguicoso prefere nao casar o opcional e engole o
# "(F#)" dentro do titulo -- o louvor sai sem tom e o titulo sai sujo.
CAB_COM_TOM = re.compile(r"^\s*(\d{1,4})\s*[-‐‑‒–—―−]\s+(.+?)"
                         r"\s*\(([A-G][#b]?m?)\)\s*\**\s*$")
CABECALHO = re.compile(r"^\s*(\d{1,4})\s*[-‐‑‒–—―−]\s+(.+?)\s*\**\s*$")
CAB_SEM_NUM = re.compile(r"^\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][^a-z]{4,}?)"
                         r"\s*\(([A-G][#b]?m?)\)\s*\**\s*$")


def limpar_titulo(t):
    """"A BELEZA DA TUA SANTIDADE  D  6656" -> ("A BELEZA DA TUA SANTIDADE", "D")

    Muitos cabecalhos trazem, depois do titulo, o tom solto e o numero da
    coletanea antiga -- sem parenteses, so separados por espaco. O regex que
    aceita cabecalho sem tom engolia os dois dentro do titulo, e ai o louvor
    nao casava com nada no app: 291 melodias extraidas certas ficavam orfas.
    """
    t = (t or "").strip()
    tom = None
    # o numero da coletanea antiga no fim, com ou sem o tom antes
    t = re.sub(r"\s+\d{2,5}\s*$", "", t)
    # o tom ENTRE PARENTESES no fim: e' o caso mais comum e o que estava
    # sobrando -- "A BELEZA DA TUA SANTIDADE (D)" nao casa com nenhum louvor
    m = re.search(r"\s*\(([A-G][#b]?[Mm]?)\)\s*$", t)
    if m:
        return t[:m.start()].strip(), m.group(1)
    m = re.search(r"\s+([A-G][#b]?[Mm]?)\s+\d{1,5}\s*$", t)
    if m:
        tom, t = m.group(1), t[:m.start()]
    else:
        m = re.search(r"\s+\d{2,5}\s*$", t)
        if m:
            t = t[:m.start()]
        m = re.search(r"\s+([A-G][#b]?[Mm]?)\s*$", t)
        if m and len(t[:m.start()].strip()) > 6:
            tom, t = m.group(1), t[:m.start()]
    if tom:
        tom = tom[:-1] + "m" if tom.lower().endswith("m") else tom
    return t.strip(), tom


def em_caixa(t):
    """O titulo vem em CAIXA ALTA. Sem este teste, o cabecalho sem tom casaria
    tambem com linha de letra que comece por numero."""
    nucleo = "".join(c for c in re.sub(r"\([^)]*\)", "", t or "") if c.isalpha())
    return bool(nucleo) and nucleo.upper() == nucleo
RODAPE = re.compile(r"(O Senhor Jesus Vem|IGREJA CRIST|COLET\s*ÂNEA|INSTRUMENTOS EM)")

SEMI = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "Fb": 4,
        "E#": 5, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
        "A#": 10, "Bb": 10, "B": 11, "Cb": 11, "B#": 0}
SUSTENIDO = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BEMOL = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# nome, semitons a partir do caderno em Bb, prefere bemol
INSTRUMENTOS = [
    ("C",  "Violino, flauta, teclado, violão, baixo, oboé", -2, False),
    ("Bb", "Sax tenor, sax soprano, trompete, clarinete",    0, True),
    ("Eb", "Sax alto, sax barítono",                          7, True),
    ("F",  "Trompa",                                          5, True),
]


def so_letras(t):
    t = unicodedata.normalize("NFD", (t or "").upper())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9 ]+", " ", t).strip()


def transpor_nota(nota, passos, bemol=False):
    """Sobe a nota N semitons. Com 0 passos devolve intacta.

    O "devolve intacta" não é otimização: sem ele, "Eb" escrito pelo autor
    voltaria como "D#" — a mesma tecla, sim, mas nenhum músico espera ler
    assim, e a folha deixa de parecer a folha dele.
    """
    if not passos:
        return nota
    m = re.match(r"^([A-G])(#|b)?", nota or "")
    if not m:
        return nota
    base = m.group(1) + (m.group(2) or "")
    if base not in SEMI:
        return nota
    tabela = BEMOL if bemol else SUSTENIDO
    return tabela[(SEMI[base] + passos) % 12] + (nota[m.end():] or "")


def transpor_tom(tom, passos, bemol=False):
    if not tom:
        return tom
    menor = tom.endswith("m")
    raiz = tom[:-1] if menor else tom
    return transpor_nota(raiz, passos, bemol) + ("m" if menor else "")


def eh_linha_de_notas(linha):
    """Uma linha é de melodia quando TUDO nela é nota ou barra de compasso.

    O "bis" e o "(G#)" no fim de algumas linhas são anotação, não melodia —
    saem antes da conta, senão a linha inteira deixaria de ser reconhecida.
    """
    t = re.sub(r"\b(bis|BIS|\d+x)\b", " ", linha)
    t = re.sub(r"\(([^)]*)\)", " ", t)
    toks = [x for x in t.replace("|", " ").split() if x.strip()]
    if not toks:
        return False
    return all(NOTA.match(x) for x in toks)


def notas_da_linha(linha):
    """['B', 'A#', '|', 'C'] — as notas e as divisões de compasso, na ordem."""
    limpa = re.sub(r"\b(bis|BIS|\d+x)\b", " ", linha)
    limpa = re.sub(r"\(([^)]*)\)", " ", limpa)
    saida = []
    for tok in limpa.replace("|", " | ").split():
        if tok == "|" or NOTA.match(tok):
            saida.append(tok)
    return saida


def ler_pdf(caminho, aviso=None):
    """[{num, titulo, tom, linhas:[{n:[notas]} | {t:'letra'}]}] do PDF inteiro."""
    from pypdf import PdfReader
    r = PdfReader(caminho)
    louvores, atual = [], None
    for p in range(len(r.pages)):
        try:
            bruto = r.pages[p].extract_text() or ""
        except Exception:
            continue
        for linha in bruto.splitlines():
            linha = linha.rstrip()
            if not linha.strip() or RODAPE.search(linha):
                continue
            m = (CAB_COM_TOM.match(linha) or CAB_SEM_NUM.match(linha)
                 or CABECALHO.match(linha))
            if m and em_caixa(m.group(2) if len(m.groups()) >= 2 else m.group(1)):
                g = m.groups()
                if len(g) == 3:
                    num, titulo, tom = g[0], g[1], g[2]
                elif len(g) == 2 and (g[1] or "").replace("m", "") in SEMI:
                    num, titulo, tom = None, g[0], g[1]
                else:
                    num, titulo, tom = g[0], g[1], None
                titulo, tom_solto = limpar_titulo(titulo)
                tom = tom or tom_solto
                atual = {"num": num, "titulo": titulo, "tom": tom,
                         "pag": p + 1, "linhas": []}
                louvores.append(atual)
                continue
            if atual is None:
                continue
            if eh_linha_de_notas(linha):
                notas = notas_da_linha(linha)
                if notas:
                    atual["linhas"].append({"n": notas})
            else:
                texto = re.sub(r"\s*\|\s*$", "", linha).strip()
                if texto:
                    atual["linhas"].append({"t": texto})
    if aviso:
        aviso("%s: %d louvores em %d paginas" % (os.path.basename(caminho)[:40],
                                                 len(louvores), len(r.pages)))
    return louvores


def caderno(louvor, passos, bemol):
    """O mesmo louvor no tom de outro instrumento."""
    saida = []
    for l in louvor["linhas"]:
        if "n" in l:
            saida.append({"n": [x if x == "|" else transpor_nota(x, passos, bemol)
                                for x in l["n"]]})
        else:
            saida.append(l)
    return {"tom": transpor_tom(louvor["tom"], passos, bemol), "linhas": saida}


def pasta_saida():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Sistema Projecao", "melodias")


def achar_pdfs(pasta=None):
    """{'C': caminho, 'Bb': caminho} — acha os dois PDFs pelo que está escrito
    dentro deles, não pelo nome do arquivo, que muda a cada download."""
    from pypdf import PdfReader
    pasta = pasta or os.path.join(os.path.expanduser("~"), "Downloads")
    achados = {}
    for n in sorted(os.listdir(pasta)):
        if not n.lower().endswith(".pdf"):
            continue
        try:
            t = (PdfReader(os.path.join(pasta, n)).pages[0].extract_text() or "")[:400]
        except Exception:
            continue
        if "INSTRUMENTOS EM" not in t.replace("  ", " "):
            continue
        afinacao = "Bb" if re.search(r"INSTRUMENTOS EM\s*Bb", t) else "C"
        atual = achados.get(afinacao)
        if not atual or os.path.getsize(os.path.join(pasta, n)) > os.path.getsize(atual):
            achados[afinacao] = os.path.join(pasta, n)
    return achados


def main():
    limite = 0
    if "--limite" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--limite") + 1])
    aviso = lambda m: sys.stderr.write("  " + m + "\n")

    pdfs = achar_pdfs()
    if "Bb" not in pdfs:
        raise SystemExit("Nao achei a Coletanea Melodica em Bb na pasta Downloads.")
    aviso("caderno base (Bb): %s" % os.path.basename(pdfs["Bb"]))

    base = ler_pdf(pdfs["Bb"], aviso)
    conferencia = ler_pdf(pdfs["C"], aviso) if "C" in pdfs else []

    # confere a transposicao contra o PDF em C de verdade, quando ele existe
    if conferencia:
        porc = {so_letras(l["titulo"]): l["tom"] for l in conferencia}
        bate = erra = 0
        for l in base:
            esperado = porc.get(so_letras(l["titulo"]))
            if not esperado:
                continue
            if transpor_tom(l["tom"], -2, False) == esperado or \
               transpor_tom(l["tom"], -2, True) == esperado:
                bate += 1
            else:
                erra += 1
                if erra <= 3:
                    aviso("  tom divergente: %s  Bb=%s -> %s, PDF em C diz %s"
                          % (l["titulo"][:30], l["tom"],
                             transpor_tom(l["tom"], -2, False), esperado))
        aviso("conferencia da transposicao contra o PDF em C: %d certos, %d errados"
              % (bate, erra))

    destino = pasta_saida()
    os.makedirs(destino, exist_ok=True)
    indice, gravados = {}, 0
    for l in base:
        if not any("n" in x for x in l["linhas"]):
            continue
        chave = so_letras(l["titulo"])
        reg = {"titulo": l["titulo"], "num": l["num"], "cadernos": {}}
        for sigla, quem, passos, bemol in INSTRUMENTOS:
            reg["cadernos"][sigla] = caderno(l, passos, bemol)
        nome = re.sub(r"[^A-Za-z0-9]+", "_", chave)[:60] + ".json"
        with io.open(os.path.join(destino, nome), "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, separators=(",", ":"))
        indice[chave] = {"arq": nome, "titulo": l["titulo"], "num": l["num"],
                         "tons": {s: reg["cadernos"][s]["tom"] for s, _q, _p, _b in INSTRUMENTOS}}
        gravados += 1
        if limite and gravados >= limite:
            break

    with io.open(os.path.join(destino, "indice.json"), "w", encoding="utf-8") as f:
        json.dump({"instrumentos": [{"sigla": s, "quem": q} for s, q, _p, _b in INSTRUMENTOS],
                   "louvores": indice}, f, ensure_ascii=False, separators=(",", ":"))

    tamanhos = [os.path.getsize(os.path.join(destino, v["arq"])) for v in indice.values()]
    print("louvores com melodia   : %d" % gravados)
    print("cadernos por louvor    : %d  (%s)"
          % (len(INSTRUMENTOS), ", ".join(s for s, _q, _p, _b in INSTRUMENTOS)))
    print("arquivo por louvor     : %.1f KB em media, %.1f KB o maior"
          % (sum(tamanhos) / len(tamanhos) / 1024.0, max(tamanhos) / 1024.0))
    print("total em disco         : %.1f MB" % (sum(tamanhos) / 1024.0 / 1024.0))
    print("pasta                  : %s" % destino)


if __name__ == "__main__":
    main()
