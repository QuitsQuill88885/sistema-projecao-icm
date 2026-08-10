# -*- coding: utf-8 -*-
"""Tira os acordes dos PDFs e transforma a cifra em texto do Sistema.

POR QUE: hoje a cifra é um PDF de 89 MB aberto no leitor do navegador. No
computador da igreja isso pesa, e no celular — que puxa o arquivo do próprio
computador da igreja — pesa muito mais. Depois desta extração a cifra vira
alguns kilobytes de texto, desenhada no visual do Sistema, instantânea.

O QUE FOI MEDIDO ANTES DE ESCREVER ISTO
=======================================
Os três PDFs são três livros diferentes, feitos por gente diferente, e o que
funciona num quebra no outro. Tudo abaixo foi conferido em páginas reais.

TODOS OS TRÊS SÃO EM DUAS COLUNAS. Agrupar fragmentos por altura (y) sem
separar as colunas antes mistura a letra da esquerda com a da direita na mesma
linha. Este é o erro que estraga tudo, e é silencioso: o texto sai, só que
embaralhado.

O ACORDE SE LIGA À LETRA PELO X, não pelas barras "|". As barras existem, e
onde existem coincidem com o x do acorde (mediana da diferença: 0,00 pt), mas
não dá para contar uma barra por acorde — o primeiro acorde não ganha barra
quando cai no começo da linha, acordes vizinhos dividem a mesma barra, e "|"
também é usado para anotação ("|BIS", "|2x final"). Nos Avulsos, barra só
aparece em 28 das 369 páginas.

A LINHA DE ACORDE SE RECONHECE PELA FONTE: negrito é acorde, regular é letra.
Nos Avulsos são 11.293 linhas de acorde contra 15.150 de letra, com apenas 3
enganos no PDF inteiro.

CADA LIVRO TEM SUA ÂNCORA
-------------------------
Cifras 2025      um louvor por página; página == número + 3, sem exceção
Avulsos 2024     cabeçalho "N - TÍTULO" em negrito, NA MARGEM DA COLUNA
Coletânea 2018   a palavra "Tonalidade", não o cabeçalho

A última é a menos óbvia e a mais importante. A Coletânea 2018 é escaneada, e o
OCR come o número do cabeçalho em uns 59 louvores e lê 7 como 1 em outros. Mas
"Tonalidade" quase nunca é estragada: 1.035 ocorrências contra 886 cabeçalhos
reconhecíveis. Ancorar no que sobrevive.

SAÍDA — %APPDATA%\\Sistema Projecao\\cifras\\acordes.json
    { "<chave do louvor>": {
        "tom": "G",
        "linhas": [ {"t": "linha", "a": [[coluna, "acorde"], ...]}, ... ] } }

Uso:  python extrair_cifras.py
      python extrair_cifras.py --limite 30     (só as 30 primeiras, para conferir)
      python extrair_cifras.py --conferir      (mede contra a letra já conhecida)
"""
import io
import json
import os
import re
import sys
import unicodedata
import difflib
from collections import Counter, defaultdict

# "A", "Bm", "C#m7", "F#", "Bb", "G/B", "Dsus4", "E7M", "A7(9)"
# Os numeros que EXISTEM em cifra: 2,4,5,6,7,9,11,13. Aceitar "[0-9]{0,2}"
# solto deixava passar "E0" e "A1", que sao lixo de OCR e apareciam na folha do
# musico como se fossem acorde.
# "°" e "o" sao o diminuto, e aparecem 42 vezes so nas primeiras 200 paginas
ACORDE = re.compile(r"^[A-G](#|b)?(m|M|maj|min|dim|aug|sus|add|°|º)?"
                    r"(2|4|5|6|7|9|11|13)?(M|m|maj)?(\+|-)?"
                    r"(\([#b]?(2|4|5|6|7|9|11|13)\))?(/[A-G](#|b)?)?$")

# separador do cabecalho: hifen comum, en dash, em dash, ou NADA
TRACO = "-‐‑‒–—―−"


def pasta_cifras():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Sistema Projecao", "cifras")


def eh_acorde(t):
    t = t.strip().strip("|")
    return bool(t) and len(t) <= 9 and bool(ACORDE.match(t))


# Erros do OCR que FORAM MEDIDOS, nao supostos. Contagem nas 400 primeiras
# paginas dos tres livros, olhando os tokens rejeitados dentro de linhas que
# sao claramente de acorde:
#     534x  "7" solto        492x  "m" solto     122x  "/A", "/E", "/C#"...
#      72x  "Pm"              47x  "CIE", "CIO"   42x  "A°"
# O "7" e o "m" soltos sao sufixo que nao colou; o "/X" e' o baixo que se
# desprendeu; e "CIE" e' "C/E" com a barra lida como I.

NOTA_N = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
          "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10,
          "Bb": 10, "B": 11}
_RAIZ = re.compile(r"^([A-G](?:#|b)?)(.*)$")


def _grau(nome):
    """(altura, qualidade) do acorde, ou None. So' a triade importa aqui."""
    m = _RAIZ.match(nome or "")
    if not m:
        return None
    resto = m.group(2).split("/")[0]
    if resto.startswith("m") and not resto.startswith("maj"):
        q = "m"
    elif resto[:3] == "dim" or resto[:1] in ("°", "º"):
        q = "dim"
    else:
        q = "M"
    a = NOTA_N.get(m.group(1))
    return None if a is None else (a, q)


def campo_do_tom(tom):
    """O que cabe neste tom: os sete graus MAIS as dominantes secundarias.

    Nao e' teoria de conservatorio, e' o que um hino publicado usa de fato. Sem
    as dominantes secundarias este juiz reprovaria arranjo bom, e ele so' serve
    para DESEMPATAR duas leituras de OCR — nunca para apagar acorde.
    """
    t = (tom or "").split(",")[0].split("/")[0].strip()
    if not t:
        return None
    menor = t.endswith("m") and not t.endswith("M")
    r = NOTA_N.get(t[:-1] if menor else t)
    if r is None:
        return None
    if menor:
        graus = [(0, "m"), (2, "dim"), (3, "M"), (5, "m"), (7, "M"), (7, "m"),
                 (8, "M"), (10, "M")]
    else:
        graus = [(0, "M"), (2, "m"), (4, "m"), (5, "M"), (7, "M"), (9, "m"),
                 (11, "dim")]
    ok = set(((r + g) % 12, q) for g, q in graus)
    # dominante secundaria: acorde MAIOR uma quinta acima de cada grau. O grau
    # diminuto fica de fora -- "V/vii°" nao existe em hino nenhum, e incluir ele
    # abria o campo de La para D#, que foi o que fez "Do" ser lido como "D#" em
    # vez de "D" na primeira tentativa.
    for g, q in graus:
        if q != "dim":
            ok.add(((r + g + 7) % 12, "M"))
    return ok


def cabe_no_tom(nome, campo):
    if not campo:
        return None                      # sem tom nao ha' juiz
    g = _grau(nome)
    return None if g is None else (g in campo)


def colar_sufixos(pares, campo=None):
    """[(x,'A'), (x,'7')] -> [(x,'A7')]. Junta o pedaco solto no acorde anterior.

    Sem isto o acorde inteiro e' perdido duas vezes: o "A" entra sozinho (errado,
    porque era A7) e o "7" e' descartado como lixo.

    A REGRA E' ESTRUTURAL, nao uma lista de sufixos: cola quando o pedaco NAO e'
    acorde sozinho e COMPLETA o anterior num acorde de verdade. A lista fixa
    deixava "D" + "7m" (Dmaj7 lido pelo OCR) passar sem colar, perdendo o acorde.

    A TRAVA DO TOM: onde o tom e' conhecido, nao cola se o anterior JA cabia no
    tom e o resultado nao cabe. E' assim que "A" + "m" solto parava de virar "Am"
    em louvor de La maior — o "m" sozinho nao e' acorde, entao nao colar so' o
    descarta, enquanto colar PLANTA um acorde errado na folha do musico.
    """
    saida = []
    for x, w in pares:
        junto = (saida[-1][1] + w) if saida else ""
        if saida and not eh_acorde(w) and eh_acorde(junto):
            antes_ok = cabe_no_tom(saida[-1][1], campo)
            if antes_ok and cabe_no_tom(junto, campo) is False:
                continue                 # o pedaco e' lixo: descarta, nao cola
            saida[-1] = (saida[-1][0], junto)
        else:
            saida.append((x, w))
    return saida


# As trocas que o OCR faz, cada uma com o preco medido contra a Tonalidade
# impressa na propria pagina (auditar_p_e_sustenido.py, Coletanea 2018):
#
#   "I","l","|" -> "/"   o baixo: "CIE" e' "C/E"
#   "P"  -> "F#"         194 ocorrencias em linha de acorde. Onde as duas
#                        leituras discordam, F# cabe no tom 98 vezes e E cabe
#                        14: F# ganha por 7 para 1. A regra antiga escrevia "E"
#                        e era ela que plantava o "Em em tom de Mi" que a
#                        auditoria de campo harmonico acusava. Prova visual, pg
#                        37, tom La: "A E/G# Pm F#m/E" -- o baixo desce
#                        La-Sol#-Fa#-Mi, e a MESMA linha soletra F#m do jeito
#                        certo logo adiante.
#   "o"  -> "#"          o OCR le o sustenido como a letra o ("Com"=C#m,
#                        "Fom"=F#m). 104 ocorrencias, "#" cabe no tom 68 vezes
#                        contra 1 do diminuto. Antes eh_acorde recusava e o
#                        acorde SUMIA. Prova, pg 30, tom La: "A Bm Com Pm" =
#                        A Bm C#m F#m, o I-ii-iii-vi de La -- uma linha so'
#                        confirmando as duas regras.
#
# A ORDEM IMPORTA POUCO porque quem decide e' o tom: quando mais de uma leitura
# da' acorde valido, ganha a que cabe no campo harmonico da pagina.
TROCAS = (("I", "/"), ("l", "/"), ("|", "/"), ("P", "F#"), ("o", "#"),
          ("P", "E"))


def consertar_ocr(w, campo=None):
    """Desfaz as trocas de letra que o OCR faz, e SO aceita se o resultado for
    acorde de verdade. Assim uma palavra comum nunca vira acorde por acidente.

    Com o tom em mao, escolhe ENTRE as leituras validas a que cabe no tom. Sem
    tom, fica com a primeira valida, na ordem medida acima.
    """
    if eh_acorde(w):
        return w
    validos = []
    for antes, depois in TROCAS:
        alvo = w.replace(antes, depois)
        if alvo != w and eh_acorde(alvo) and alvo not in validos:
            validos.append(alvo)
    # tirar o "o" tambem e' leitura: "Do" pode ser "D" com sujeira colada
    if "o" in w:
        alvo = w.replace("o", "")
        if alvo and eh_acorde(alvo) and alvo not in validos:
            validos.append(alvo)
    if not validos:
        return w
    for alvo in validos:
        if cabe_no_tom(alvo, campo):
            return alvo
    return validos[0]


def negrito(fonte):
    f = str(fonte or "")
    return "Bold" in f or "bold" in f


# --------------------------------------------------------------------------
#  Leitura crua: fragmentos com posição, fonte e tamanho
# --------------------------------------------------------------------------

def fragmentos(pagina):
    """[(x, y, texto, fonte, tamanho)] — cada pedaço que o PDF desenhou.

    O pypdf entrega o texto em pedaços com a matriz de transformação; tm[4] e
    tm[5] são o x e o y de onde aquele pedaço começa.

    O '\\t' é quebrado à parte de propósito: o pypdf só o insere quando detecta
    um salto horizontal grande, e é exatamente ali que um mesmo comando de
    desenho atravessou a calha entre as duas colunas. Sem quebrar, meia linha
    da coluna direita fica pendurada na linha da esquerda.
    """
    saida = []

    def visita(texto, cm, tm, fonte, tam):
        t = (texto or "").replace("\n", "")
        if not t.strip():
            return
        nome = ""
        try:
            nome = str(fonte.get("/BaseFont", "")) if hasattr(fonte, "get") else str(fonte)
        except Exception:
            pass
        x, y = tm[4], tm[5]
        if "\t" in t:
            # reparte e reposiciona cada pedaço pela largura do que veio antes
            corte = 0.0
            for pedaco in t.split("\t"):
                if pedaco.strip():
                    saida.append((x + corte, y, pedaco, nome, tam))
                corte += largura(pedaco, tam) + tam * 0.9      # o tab vale um vão
        else:
            saida.append((x, y, t, nome, tam))

    pagina.extract_text(visitor_text=visita)
    return juntar_sobrescritos(saida)


# Larguras da Arial em milésimos de em. Não é preciso ler /Widths do PDF: os
# três livros usam Arial (regular e bold) e o que importa aqui é a posição
# RELATIVA do acorde dentro da linha, não a tipografia exata.
_W = {" ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667,
      "'": 191, "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333,
      ".": 278, "/": 278, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584,
      "?": 556, "@": 1015, "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556,
      "`": 333, "{": 334, "|": 260, "}": 334, "~": 584}
for _c in "0123456789":
    _W[_c] = 556
for _c, _v in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                  (667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556,
                   833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667,
                   667, 611)):
    _W[_c] = _v
for _c, _v in zip("abcdefghijklmnopqrstuvwxyz",
                  (556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222,
                   833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500,
                   500, 500)):
    _W[_c] = _v


def _largura_car(c):
    if c in _W:
        return _W[c]
    # acentuado: usa a largura da letra-base ("á" -> "a")
    base = unicodedata.normalize("NFD", c)[0]
    return _W.get(base, 556)


def largura(texto, tam):
    return sum(_largura_car(c) for c in texto) * tam / 1000.0


def coluna_do_x(texto, x, tam):
    """Em que caractere do texto cai a posição x (medida do início da linha)."""
    if x <= 0:
        return 0
    andado, i = 0.0, 0
    for c in texto:
        w = _largura_car(c) * tam / 1000.0
        if andado + w / 2 >= x:
            return i
        andado += w
        i += 1
    return len(texto)


# --------------------------------------------------------------------------
#  Colunas e linhas
# --------------------------------------------------------------------------

def achar_calha(frags, vao_min=30.0, sep_min=140.0):
    """O x que separa as duas colunas, ou None se a página tiver uma só.

    Duas medidas, porque nenhuma sozinha cobre os três livros:

    1. O MAIOR VÃO VAZIO no meio da página. Serve na Coletânea 2025, onde a
       calha tem 70 pt de largura.

    2. Se não houver vão largo, as DUAS MARGENS. Nos Avulsos as colunas quase
       se encostam — a calha tem 13 pt — e nenhum limiar de vão que não
       estrague o resto consegue vê-la. Mas as margens são nítidas: 28 e 223,
       195 pt de distância, cada uma com dezenas de linhas começando ali.

    Sem a segunda medida, os Avulsos saíam com as duas colunas grudadas: o
    cabeçalho da direita entrava colado no da esquerda, e o louvor virava
    "AGEU (Bm) 09 - AGRADECEMOS A TI, SENHOR (E)" — dois louvores num título só,
    que não casa com nada e é descartado.
    """
    if len(frags) < 12:
        return None
    fins = sorted((f[0], f[0] + largura(f[2], f[4])) for f in frags)
    x0 = fins[0][0]
    x1 = max(f[1] for f in fins)
    esq, dir_ = x0 + (x1 - x0) * 0.28, x0 + (x1 - x0) * 0.72

    melhor, corte = 0.0, None
    alcance = fins[0][1]
    for ini, fim in fins[1:]:
        if ini - alcance > melhor and esq <= (ini + alcance) / 2 <= dir_:
            melhor, corte = ini - alcance, (ini + alcance) / 2
        alcance = max(alcance, fim)
    if melhor >= vao_min:
        return corte

    # --- segunda medida: as margens ---
    # x inicial de cada faixa horizontal, agrupando por y sem olhar coluna
    inicios = {}
    for x, y, _t, _f, _tam in frags:
        k = round(y / 2.4)
        if k not in inicios or x < inicios[k]:
            inicios[k] = x
    # e tambem os inicios "de dentro": fragmento que comeca depois de um vao
    por_y = defaultdict(list)
    for f in frags:
        por_y[round(f[1] / 2.4)].append(f)
    dentro = []
    for fs in por_y.values():
        fs.sort(key=lambda f: f[0])
        alc = None
        for x, _y, t, _f, tam in fs:
            if alc is not None and x - alc > tam * 2.5:
                dentro.append(x)
            alc = max(alc or 0, x + largura(t, tam))
    if not dentro:
        return None
    h = Counter(round(v / 3) * 3 for v in dentro)
    margem_esq = min(inicios.values()) if inicios else x0
    fortes = [b for b, n in h.items() if n >= 3 and b - margem_esq >= sep_min]
    if not fortes:
        return None
    return min(fortes) - 4.0


def juntar_sobrescritos(frags):
    """Cola o expoente do acorde de volta nele: "D" + "7" pequeno = "D7".

    Nas cifras o número do acorde é desenhado sobrescrito — fonte menor e uns
    8 pt acima da linha. Sem juntar, "D7" vira o acorde "D" mais um "7" solto
    que não é acorde nenhum, e a linha inteira deixa de ser reconhecida como
    linha de acordes.
    """
    if not frags:
        return frags
    normal = Counter(round(f[4], 1) for f in frags).most_common(1)[0][0]
    pequenos = [f for f in frags if f[4] < normal * 0.82]
    if not pequenos:
        return frags
    grandes = [f for f in frags if f[4] >= normal * 0.82]
    sobrou = []
    for p in pequenos:
        # o dono é o fragmento grande que termina logo à esquerda, na linha
        # imediatamente abaixo do sobrescrito
        dono, perto = None, 1e9
        for i, g in enumerate(grandes):
            dy = p[1] - g[1]
            if not (0 < dy < normal * 1.2):
                continue
            d = p[0] - (g[0] + largura(g[2], g[4]))
            if -1.5 <= d < normal * 1.6 and abs(d) < perto:
                dono, perto = i, abs(d)
        if dono is None:
            sobrou.append(p)
        else:
            g = grandes[dono]
            grandes[dono] = (g[0], g[1], g[2] + p[2], g[3], g[4])
    return grandes + sobrou


def linhas_da_pagina(frags, tol=2.4):
    """[(col, y, [frag...])] na ordem de leitura: coluna esquerda inteira de
    cima a baixo, DEPOIS a direita inteira. Nunca por y global."""
    calha = achar_calha(frags)
    por = defaultdict(list)
    for f in frags:
        col = 1 if (calha is not None and f[0] >= calha) else 0
        por[(col, round(f[1] / tol))].append(f)
    saida = []
    for (col, _), fs in por.items():
        fs.sort(key=lambda f: f[0])
        saida.append((col, fs[0][1], fs))
    saida.sort(key=lambda r: (r[0], -r[1]))
    return saida


def tokens_com_x(fs):
    """[(x, palavra)] — as palavras da linha e onde cada uma comeca.

    Tem que sair da MESMA colagem que monta o texto: se aqui "Gm/" e "D" ainda
    forem dois tokens, o acorde "Gm/D" e' lido como dois acordes errados, e a
    linha inteira deixa de ser reconhecida como linha de acordes, porque "Gm/"
    sozinho nao e' acorde nenhum. Foi isso que derrubou a contagem para 9
    acordes por louvor na primeira tentativa; agora sao 82 nesta mesma pagina.
    """
    saida, ant = [], ""
    for x, _y, t, _f, tam in fs:
        colar = ant.rstrip().endswith("/") and len(ant.strip()) <= 6
        andado, resto = 0.0, t
        while resto:
            m = re.match(r"(\s*)(\S+)", resto)
            if not m:
                break
            andado += largura(m.group(1), tam)
            if colar and saida:
                saida[-1] = (saida[-1][0], saida[-1][1] + m.group(2))
            else:
                saida.append((x + andado, m.group(2)))
            andado += largura(m.group(2), tam)
            resto = resto[m.end():]
            colar = False
        ant = t
    return saida


def texto_da_linha(fs):
    """Junta os fragmentos numa string, pondo espaço onde havia vão de verdade.

    Sem isto o título sai com os acordes colados nele, e a letra sai com
    palavras grudadas."""
    partes, fim, ant = [], None, ""
    for x, _y, t, _f, tam in fs:
        # Regra estrutural, nao limiar de distancia: medi os vaos e os dois
        # casos se sobrepoem por inteiro (mediana 0,60 contra 0,29 do tamanho
        # da fonte), entao nenhum numero separa "Gm/" + "D" de "pois" + "a".
        # O que separa e' a FORMA: baixo de acorde sempre termina em barra.
        colar = ant.rstrip().endswith("/") and len(ant.strip()) <= 6
        if fim is not None and not colar and x - fim > tam * 0.22 and not t.startswith(" "):
            partes.append(" ")
        partes.append(t)
        fim = x + largura(t, tam)
        ant = t
    return "".join(partes).rstrip()


# --------------------------------------------------------------------------
#  Cabeçalhos — uma âncora por livro
# --------------------------------------------------------------------------

CAB_NUM = re.compile(r"^\s*(\d{1,3})\s*[" + TRACO + r"]?\s*(\S.*?)\s*$")
TONALIDADE = re.compile(r"[Tt7][o0O]n[a4]l[il1]d[a4]d[e3]")
SO_TOM = re.compile(r"^\s*[Tt7][o0O]n[a4]l[il1]d[a4]d[e3]\s*:?\s*"
                    r"([A-G][#b]?m?(?:\s*[,/]\s*[A-G][#b]?m?)?)")
TOM_PAREN = re.compile(r"\(\s*([A-G][#b]?(?:m|min)?(?:\s*[,/]\s*[A-G][#b]?m?)?)\s*\)\s*$")


def titulo_plausivel(t):
    """O corpo do livro escreve o título em CAIXA ALTA; o índice temático usa
    Title Case. Sem este teste, as três páginas de índice dos Avulsos entram
    como 377 louvores fantasmas."""
    nucleo = t.split("(")[0]
    nucleo = "".join(c for c in nucleo if c.isalpha())
    if not nucleo:
        return False
    return nucleo.upper() == nucleo and any(c.isalpha() for c in nucleo)


def cabecalhos_por_margem(linhas):
    """Avulsos: cabeçalho é linha em negrito, em CAIXA, e na MARGEM da coluna.

    O teste da margem não é enfeite: sem ele, o "3X" que marca repetição no meio
    do louvor 424 entra como se fosse o louvor 3, e a numeração inteira do livro
    passa a ter um buraco."""
    margem = {}
    for col, _y, fs in linhas:
        x0 = fs[0][0]
        if col not in margem or x0 < margem[col]:
            margem[col] = x0
    achados = []
    for i, (col, y, fs) in enumerate(linhas):
        if abs(fs[0][0] - margem.get(col, 0)) > 1.5:
            continue
        if not negrito(fs[0][3]):
            continue
        t = texto_da_linha(fs)
        m = CAB_NUM.match(t)
        if not m or not titulo_plausivel(m.group(2)):
            continue
        achados.append((i, int(m.group(1)), m.group(2)))
    return achados


def cabecalhos_por_tonalidade(linhas):
    """Coletânea 2018: ancora na palavra "Tonalidade", que o OCR respeita.

    O título é a linha em caixa alta mais próxima acima dela — o bloco de
    abertura é TÍTULO / AUTOR / TONALIDADE."""
    achados = []
    for i, (_col, _y, fs) in enumerate(linhas):
        t = texto_da_linha(fs)
        if not TONALIDADE.search(t):
            continue
        num, titulo, ini = None, "", i
        for j in range(i - 1, max(-1, i - 5), -1):
            tj = texto_da_linha(linhas[j][2])
            if TONALIDADE.search(tj):
                break
            m = CAB_NUM.match(tj)
            if m and titulo_plausivel(m.group(2)):
                num, titulo, ini = int(m.group(1)), m.group(2), j
                break
            if titulo_plausivel(tj) and len(tj) > 6 and not titulo:
                titulo, ini = tj, j
        achados.append((ini, num, titulo))
    return achados


def cabecalho_unico(linhas):
    """Cifras 2025: um louvor por página. O título é o primeiro fragmento
    grande (12 pt), na coluna esquerda, no alto."""
    for i, (col, _y, fs) in enumerate(linhas):
        if col != 0 or fs[0][0] > 300:
            continue
        if fs[0][4] < 11.5:
            continue
        t = texto_da_linha([f for f in fs if f[0] < 300])
        m = CAB_NUM.match(t)
        if m and titulo_plausivel(m.group(2)):
            return [(i, int(m.group(1)), m.group(2))]
        if titulo_plausivel(t) and len(t) > 5:
            return [(i, None, t)]
    return []


# --------------------------------------------------------------------------
#  Montagem da cifra
# --------------------------------------------------------------------------

def linha_e_lixo(t):
    """Linha que nao e' letra nem acorde: so ruido do scanner.

    O OCR da Coletanea 2018 produz coisas como "137(1,9)  Esum E" e
    "F9E3  137(b9)  Est\" E" -- restos de simbolo musical e de numeracao que
    ele nao soube ler. Nao viram acorde (nao passam no teste) e por isso caiam
    como se fossem LETRA, aparecendo no meio do louvor na tela do musico.

    Uma linha de letra de verdade e' feita de palavras. Se menos da metade dos
    caracteres for letra, ou se nao houver nenhuma palavra de tres letras, o que
    esta ali nao e' letra de louvor.
    """
    t = (t or "").strip()
    if not t:
        return True
    letras = sum(1 for c in t if c.isalpha())
    if letras < len(t) * 0.5:
        return True
    palavras = [w for w in re.split(r"[^A-Za-zÀ-ÿ]+", t) if len(w) >= 3]
    return not palavras


def montar_bloco(linhas, ini, fim):
    """[{'t': letra, 'a': [[coluna, acorde], ...]}] de um louvor.

    Le' o bloco DUAS vezes. Na primeira so' procura a Tonalidade; na segunda usa
    ela para desempatar as leituras de OCR. Antes era uma passada so', e o tom
    chegava tarde demais para os acordes que vinham antes da linha "Tonalidade:"
    -- justamente a introducao, onde estao os acordes mais estranhos.
    """
    tom = None
    for _col, _y, fs in linhas[ini:fim]:
        m = SO_TOM.search(texto_da_linha(fs))
        if m:
            tom = m.group(1).strip()
            break
    campo = campo_do_tom(tom)

    saida, guardados = [], None
    for col, _y, fs in linhas[ini:fim]:
        t = texto_da_linha(fs)
        if not t.strip():
            continue
        if SO_TOM.search(t):
            continue
        # por TOKEN, nao por fragmento: o PDF pode desenhar "Gm  Gm/F Gm/Eb"
        # num pedaco so, e ai o pedaco inteiro nao e' acorde nenhum.
        toks = [f for f in fs if f[2].strip()]
        # O conserto do OCR so vale em linha que JA parece de acorde. Sem essa
        # trava, "DIA" -- de "O DIA ESTA CHEGANDO" -- vira "D/A" e a linha de
        # letra e' promovida a linha de acordes. Aparece 70 vezes nos livros.
        crus = tokens_com_x(fs)
        ja_bons = sum(1 for _x, w in crus if eh_acorde(w))
        palavras = (colar_sufixos([(x, consertar_ocr(w, campo)) for x, w in crus],
                                  campo)
                    if crus and ja_bons >= len(crus) * 0.5 else crus)
        # ate 1/4 de lixo tolerado: no PDF escaneado o OCR estraga um acorde
        # aqui e ali, e exigir 100%% jogava a linha inteira fora -- com todos os
        # acordes bons que estavam nela.
        bons = sum(1 for _x, w in palavras if eh_acorde(w))
        so_acorde = (bool(palavras) and bons >= max(1, len(palavras) * 3 // 4)
                     and any(negrito(f[3]) for f in toks))
        if so_acorde:
            guardados = palavras      # espera a linha de letra logo abaixo
            continue
        letra = t.replace("|", "")     # a barra é enfeite: a posição vem do x
        if not letra.strip() or linha_e_lixo(letra):
            guardados = None           # o acorde de cima nao tem onde cair
            continue
        acordes = []
        if guardados:
            x0 = fs[0][0]
            tam = fs[0][4] or 9.0
            for fx, palavra in guardados:
                nome = palavra.strip("|")
                if not eh_acorde(nome):
                    continue
                acordes.append([max(0, coluna_do_x(letra, fx - x0, tam)), nome])
            guardados = None
        saida.append({"t": letra, "a": acordes})
    return saida, tom


ESTRATEGIA = {
    "2025": ("unico", cabecalho_unico),
    "Avulsos": ("margem", cabecalhos_por_margem),
    "2018": ("tonalidade", cabecalhos_por_tonalidade),
}


def estrategia_do_pdf(nome):
    for chave, (rot, fn) in ESTRATEGIA.items():
        if chave in nome:
            return rot, fn
    return "margem", cabecalhos_por_margem


def louvores_da_pagina(pagina, nome_pdf):
    """[(numero, titulo, [linhas de cifra], tom)] — os louvores desta página."""
    frags = fragmentos(pagina)
    if not frags:
        return []
    linhas = linhas_da_pagina(frags)
    _rot, achar = estrategia_do_pdf(nome_pdf)
    cabs = achar(linhas)
    if not cabs:
        return []
    saida = []
    for k, (ini, num, titulo) in enumerate(cabs):
        fim = cabs[k + 1][0] if k + 1 < len(cabs) else len(linhas)
        corpo, tom = montar_bloco(linhas, ini + 1, fim)
        if not tom:
            m = TOM_PAREN.search(titulo or "")
            if m:
                tom = m.group(1)
        saida.append((num, (titulo or "").strip(), corpo, tom))
    return saida


# --------------------------------------------------------------------------
#  Extração completa
# --------------------------------------------------------------------------

def so_letras(t):
    t = unicodedata.normalize("NFD", (t or "").upper())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9 ]+", " ", t).strip()


def _parecido(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def achatar(t):
    """Versao comparavel do texto SEM mudar o comprimento: cada caractere entra
    como exatamente um caractere.

    Tem que ser 1 para 1 porque a coluna do acorde e' um INDICE dentro desta
    string. so_letras() nao serve aqui: ele encolhe "  ," num espaco so' e
    desloca todas as colunas seguintes.
    """
    saida = []
    for c in t or "":
        d = unicodedata.normalize("NFD", c)
        b = (d[0] if d else c).upper()
        saida.append(b if (b.isalnum() and b.isascii()) else " ")
    return "".join(saida)


# Sujeira do OCR que derruba a semelhanca sem mudar o que esta escrito. Usada
# SO' para comparar -- o texto que vai para a tela e' sempre o do app.
_SUJEIRA = re.compile(r"[¡¿\[\]{}~^\\_|*\"]")
_APOSTROFO = re.compile(r"(?<![A-Za-zÀ-ÿ])['´`]+")


def para_comparar(t):
    """A linha do OCR do jeito que da' para compara-la com a letra do app.

    MEDIDO: 62,9% das linhas corrompidas ficam entre 0,30 e 0,50 de semelhanca
    com a linha certa, e o piso de aceitacao e' 0,50. Ou seja, o alinhador
    recusava exatamente as linhas que mais precisavam de conserto. Boa parte
    dessa perda e' enfeite, nao dano: colchete, apostrofo solto, o hifen que
    separa silaba ("co--racao") e a sobra da linha de acorde grudada no comeco
    ("P 7 Bm Am D7 Pelo sangue..." -- 18% das linhas corrompidas comecam assim).
    """
    # APAGA, nao troca por espaco: o OCR enfia esse lixo DENTRO da palavra
    # ("Sen[hor"). Trocando por espaco sairia "SEN HOR", que nao casa com
    # "SENHOR"; apagando sai "SENHOR", que casa.
    t = _SUJEIRA.sub("", t or "")
    t = _APOSTROFO.sub("", t)
    toks = t.split()
    n = quantos_acordes_no_comeco(toks)
    # DOIS acordes, nao um: "A" e "E" sozinhos sao acorde E sao palavra
    # portuguesa. Exigindo dois seguidos, "P 7 Bm Am D7 Pelo sangue" perde o
    # bloco de acordes e "A GLORIA DE DEUS" fica inteiro.
    if n >= 2 and n < len(toks):
        t = " ".join(toks[n:])
    return so_letras(t)


def _tirar_um(w, palavras, minimo=4):
    """A palavra que sobra tirando UM caractere, se ela existir no louvor."""
    if len(w) < minimo:
        return None
    for i in range(len(w)):
        alt = w[:i] + w[i + 1:]
        if alt in palavras:
            return alt
    return None


def desenfiar(texto, palavras):
    """Aproxima a linha do OCR das palavras que ESTE louvor realmente tem.

    Dois estragos, um criterio so'. A TRAVA E' A MESMA DAS OUTRAS CORRECOES:
    a troca so' vale quando o resultado e' palavra do proprio louvor. Sem a
    trava seria adivinhacao, e adivinhar aqui casa a linha com a estrofe errada.

      letra enfiada no meio   JELSUS -> JESUS, POLDER -> PODER   (1.444 linhas)
      silaba partida          DA + DO -> DADO,  JE + 1SUS -> JESUS

    A silaba partida e' a tipografia do hino antigo, que separa as silabas para
    a melodia: o livro imprime "Oh! Que amor que Je -1sus nos tem da - do". Em
    palavra, isso se resolve juntando os pedacos; em caractere, nao se resolve
    -- foi o que sobrou de fora quando a costura era so' por caractere.

    Juntar pedacos tambem cobre o hifen de separacao ("co--racao" -> CO RACAO ->
    CORACAO), e cobre SEM o risco de estragar o pronome: "purificar-me" vira
    "PURIFICAR ME", e "PURIFICARME" so' seria aceito se o louvor tivesse essa
    palavra -- que nao tem. Sao 1.288 pronomes assim no acervo contra 2 hifens
    de silaba, entao uma regra de hifen que errasse esse lado custaria caro.
    """
    if not palavras:
        return texto
    toks = texto.split()
    saida, i = [], 0
    while i < len(toks):
        w = toks[i]
        if w in palavras:
            saida.append(w)
            i += 1
            continue
        alt = _tirar_um(w, palavras)
        if alt:
            saida.append(alt)
            i += 1
            continue
        if i + 1 < len(toks):
            junto = w + toks[i + 1]
            achado = junto if junto in palavras else _tirar_um(junto, palavras)
            if achado:
                saida.append(achado)
                i += 2
                continue
        saida.append(w)
        i += 1
    return " ".join(saida)


def quantos_acordes_no_comeco(toks):
    """Quantos tokens do comeco da linha sao acorde, contando o sufixo solto."""
    n, ultimo = 0, ""
    for w in toks:
        c = consertar_ocr(w)
        if eh_acorde(c):
            ultimo, n = c, n + 1
        elif ultimo and eh_acorde(ultimo + w):
            ultimo, n = ultimo + w, n + 1
        else:
            break
    return n


def repartir(linha, alvos):
    """Uma linha do PDF contra VARIAS linhas do app: devolve uma linha por alvo.

    ESTE E' O CONSERTO DO GRAMPO. O PDF traz a frase inteira numa linha so'
    ("Sou feliz! Tenho Jesus em meu co--racao.", 40 caracteres, 7 acordes) e o
    app quebra a mesma frase em linhas curtas de projecao ("SOU FELIZ!", 10
    caracteres). O alinhador casava 1 para 1 e o que caia depois do fim era
    grampeado no ultimo caractere por min(len(nova), c) -- cinco acordes
    empilhados na silaba final. Repartindo, cada acorde cai na linha em que a
    silaba dele realmente esta.
    """
    velha = achatar(linha["t"])
    pedacos = [achatar(x) for x in alvos]
    inicio, p = [], 0
    for s in pedacos:
        inicio.append(p)
        p += len(s) + 1
    nova = " ".join(pedacos)

    mapa = {}
    for a, b, n in difflib.SequenceMatcher(None, velha, nova,
                                           autojunk=False).get_matching_blocks():
        for c in range(n):
            mapa[a + c] = b + c

    saida = [(x, []) for x in alvos]
    for col, nome in linha["a"]:
        if not eh_acorde(nome):
            continue                     # lixo de OCR nao vai para a tela
        if col in mapa:
            h = mapa[col]
        else:                            # caiu num trecho que o OCR inventou
            antes = [c for c in mapa if c <= col]
            h = mapa[max(antes)] + (col - max(antes)) if antes else 0
        k = 0
        for idx in range(len(alvos)):
            if h >= inicio[idx]:
                k = idx
        c2 = h - inicio[k]
        # caiu na juntura entre duas linhas do app: pertence a' de baixo, no
        # comeco -- e' o comeco da frase seguinte, nao o fim da anterior
        if c2 >= len(pedacos[k]) and k + 1 < len(alvos):
            k, c2 = k + 1, 0
        saida[k][1].append([max(0, min(len(alvos[k]), c2)), nome])
    for _t, a in saida:
        a.sort()
    return [{"t": t, "a": a} for t, a in saida]


LIVRE = 0.70            # piso da costura sem ordem (ver segunda passada)


def consertar_pela_letra(corpo, letra_certa, minimo=0.5, juntos=6):
    """Troca a letra que saiu do OCR pela letra certa do app, sem perder onde
    cada acorde cai.

    POR QUE: a Coletanea 2018 e' escaneada, e o OCR devolve "Roichedo fonte é
    'o 'Se - inhor" no lugar de "ROCHEDO FORTE É O SENHOR". Os ACORDES, porem,
    saem certos -- sao curtos, em negrito, e o que importa neles e' a posicao,
    que vem do x e nao do reconhecimento de caractere. Temos a letra certa de
    um lado e a marcacao certa do outro; falta costurar.

    COMO: alinhamento de SEQUENCIA, nao casamento livre. As duas listas contam
    a mesma historia na mesma ordem, e casar cada linha com a mais parecida que
    ainda esteja livre parece igual mas nao e': a primeira linha processada
    escolhe a melhor para si e rouba a correspondencia da linha certa. Foi o
    que aconteceu -- "REFÚGIO NA TRIBULAÇÃO" costurou e "Rochedo forte", que
    era a primeira do louvor, ficou com o OCR cru.

    O alinhamento e' o mesmo do "diff": uma matriz onde cada passo ou casa duas
    linhas, ou pula uma de um lado. Respeitando a ordem, ninguem rouba nada.

    UMA LINHA DO PDF VALE VARIAS DO APP. Esta e' a correcao que devolve mais
    acorde de uma vez. O passo de casamento consome 1 linha do PDF e ate
    `juntos` linhas do app, porque e' isso que os dois lados sao: o PDF imprime
    a frase inteira, o app quebra a mesma frase em linhas curtas de projecao.
    Casando 1 para 1, a linha longa do PDF nao se parecia com nenhuma linha
    curta do app -- ficava abaixo do piso, a letra do OCR nao era trocada, e os
    acordes que caiam depois do fim eram grampeados no ultimo caractere.
    """
    if not letra_certa:
        return corpo, 0
    uteis = [i for i, l in enumerate(corpo) if len(so_letras(l["t"])) >= 6]
    if not uteis:
        return corpo, 0
    B = [so_letras(x) for x in letra_certa]
    vocab = set(w for linha in B for w in linha.split())
    A = [desenfiar(para_comparar(corpo[i]["t"]), vocab) for i in uteis]
    n, m = len(A), len(B)
    if not m:
        return corpo, 0
    K = max(1, juntos)

    # semelhanca de cada linha do PDF com cada RUN de 1..K linhas do app.
    # O laco tem o alvo por fora de proposito: o SequenceMatcher guarda o indice
    # da segunda sequencia, entao trocar so' a primeira reaproveita esse indice.
    sem = [[[0.0] * (K + 1) for _ in range(m)] for _ in range(n)]
    sm = difflib.SequenceMatcher(autojunk=False)
    for j in range(m):
        for k in range(1, K + 1):
            if j + k > m:
                break
            alvo = " ".join(B[j:j + k]).strip()
            if len(alvo) < 3:
                continue
            sm.set_seq2(alvo)
            for i in range(n):
                sm.set_seq1(A[i])
                # dois limites superiores baratos antes da conta cara
                if sm.real_quick_ratio() < 0.34 or sm.quick_ratio() < 0.34:
                    continue
                sem[i][j][k] = sm.ratio()

    VAZIO = -0.28                       # custo de pular uma linha de um lado
    MENOS = float("-inf")
    pont = [[MENOS] * (m + 1) for _ in range(n + 1)]
    veio = [[None] * (m + 1) for _ in range(n + 1)]
    pont[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            base = pont[i][j]
            if base == MENOS:
                continue
            if i < n and base + VAZIO > pont[i + 1][j]:
                pont[i + 1][j] = base + VAZIO
                veio[i + 1][j] = (i, j, 0)
            if j < m and base + VAZIO > pont[i][j + 1]:
                pont[i][j + 1] = base + VAZIO
                veio[i][j + 1] = (i, j, 0)
            if i < n:
                for k in range(1, K + 1):
                    if j + k > m:
                        break
                    s = sem[i][j][k]
                    if s <= 0.0:
                        continue
                    v = base + (s - 0.45)
                    if v > pont[i + 1][j + k]:
                        pont[i + 1][j + k] = v
                        veio[i + 1][j + k] = (i, j, k)

    plano, trocadas, cobertas = {}, 0, 0
    i, j = n, m
    while (i, j) != (0, 0):
        v = veio[i][j]
        if v is None:
            break
        pi, pj, k = v
        if k and sem[pi][pj][k] >= minimo:
            plano[uteis[pi]] = repartir(corpo[uteis[pi]], letra_certa[pj:pj + k])
            trocadas += 1
            cobertas += k
        i, j = pi, pj

    # SEGUNDA PASSADA, esta SEM ordem. O alinhamento respeita a ordem de
    # proposito: e' o que impede uma linha de roubar a correspondencia de outra.
    # Mas isso gasta cada linha do app UMA vez, e o livro REPETE o coro. Medido
    # no acervo: das linhas que sobraram cruas tendo par obvio (semelhanca 0,70
    # ou mais), 1.076 sao repeticao de uma linha que o app so' tem uma vez, e
    # 914 ficaram de fora porque as estrofes estao em ordem diferente dos dois
    # lados. Aqui elas casam com a linha mais parecida, ja usada ou nao.
    # O piso e' mais alto (0,70) porque sem a ordem para proteger, so'
    # semelhanca alta pode decidir sozinha.
    for pi in range(n):
        if uteis[pi] in plano:
            continue
        melhor, quanto = None, LIVRE
        for pj in range(m):
            s = sem[pi][pj][1]
            if s > quanto:
                melhor, quanto = pj, s
        if melhor is not None:
            plano[uteis[pi]] = repartir(corpo[uteis[pi]], [letra_certa[melhor]])
            trocadas += 1

    saida = []
    for k, linha in enumerate(corpo):
        if k in plano:
            saida.extend(plano[k])
        else:
            # nao costurou: a letra fica como o OCR deixou, mas o lixo que o
            # extrator leu como acorde ('E91#" 4)', '13') nao vai para a tela
            saida.append({"t": linha["t"],
                          "a": [[c, nm] for c, nm in linha["a"] if eh_acorde(nm)]})
    return saida, trocadas, cobertas / float(m)


def tons_das_melodias(pasta=None):
    """{titulo normalizado: tom} lido das melodicas, caderno C.

    POR QUE A MELODICA MANDA NO TOM: ela saiu boa e e' fonte INDEPENDENTE da
    cifra — outro arquivo, outra extracao, outro PDF. O caderno C e' o que soa
    de verdade (os outros sao transpostos para o instrumento). Onde os dois
    discordam, quem erra e' quase sempre a linha "Tonalidade:" lida pelo OCR.

    Isto tambem tira o tom da disputa entre livros: antes o tom vinha do PDF que
    tivesse ganhado o louvor, e trocar de PDF trocava o tom junto.
    """
    pasta = pasta or os.path.join(os.path.dirname(pasta_cifras()), "melodias")
    cam = os.path.join(pasta, "indice.json")
    if not os.path.exists(cam):
        return {}
    try:
        idx = json.load(io.open(cam, encoding="utf-8")).get("louvores", {})
    except Exception:
        return {}
    mapa = {}
    for k, v in idx.items():
        tom = (v.get("tons") or {}).get("C")
        if not tom:
            continue
        titulo = v.get("titulo") or k
        for forma in {so_letras(titulo), sem_parenteses(titulo)}:
            if forma:
                mapa.setdefault(forma, tom)
                # o tom as vezes vazou para o fim do titulo ("CLAMO A TI D")
                corte = forma.rsplit(" ", 1)
                if len(corte) == 2 and eh_acorde(corte[1].title()):
                    mapa.setdefault(corte[0], tom)
    return mapa


def quanto_cabe(corpo, tom):
    """Que fracao dos acordes desta cifra cabe no tom. -1 se nao da' para dizer."""
    campo = campo_do_tom(tom)
    if not campo:
        return -1.0
    vistos = [g for l in corpo for _c, nm in l["a"] for g in (_grau(nm),) if g]
    if len(vistos) < 4:
        return -1.0
    return sum(1 for g in vistos if g in campo) / float(len(vistos))


def escolher_tom(tom_pdf, tom_melodia, corpo):
    """Qual tom vai para a folha do musico, e de onde ele veio.

    A melodica e' fonte confiavel e INDEPENDENTE, e ganha da linha "Tonalidade:"
    lida pelo OCR. Mas ela nao ganha no escuro: o tom tem que descrever OS
    ACORDES QUE ESTAO NESTA CIFRA. As duas coletaneas as vezes publicam o mesmo
    louvor em tons diferentes de verdade — e ai carimbar o tom da melodica sobre
    uma cifra escrita noutro tom troca um erro que se ve por um que nao se ve: o
    musico leria "tom G" com os acordes todos em La, e a transposicao do app
    sairia errada.

    Entao: quando os dois discordam, quem decide sao os acordes. Empate, ou
    poucos acordes para julgar, fica com a melodica.
    """
    if not tom_melodia:
        return tom_pdf, None
    if not tom_pdf:
        return tom_melodia, "melodia"
    if tom_melodia == tom_pdf:
        return tom_pdf, None
    q_mel, q_pdf = quanto_cabe(corpo, tom_melodia), quanto_cabe(corpo, tom_pdf)
    if q_mel < 0 or q_pdf < 0 or q_mel >= q_pdf:
        return tom_melodia, "melodia"
    return tom_pdf, "acordes"


def sem_parenteses(t):
    """"DEIXA O MEU POVO IR (Vai Moises)" -> "DEIXA O MEU POVO IR".

    Os PDFs põem entre parênteses o subtítulo, o tom e a versão ("Arautos do
    Rei", "(D)", "(SALMO 23)"). O banco de louvores do app não tem nada disso.
    """
    return so_letras(re.sub(r"\([^)]*\)", " ", t or ""))


def letras_dos_louvores(raiz=None):
    """{titulo normalizado: [linha, linha, ...]} — a letra certa, do app."""
    raiz = raiz or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    s = io.open(os.path.join(raiz, "dados", "louvores.js"), encoding="utf-8").read()
    L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    if isinstance(L, dict):
        L = L.get("louvores", L)
    mapa = {}
    for l in L:
        linhas = [li for sl in l.get("slides", []) for li in sl.get("linhas", [])]
        for forma in {so_letras(l["titulo"]), sem_parenteses(l["titulo"])}:
            if forma and forma not in mapa:
                mapa[forma] = linhas
    return mapa


# --------------------------------------------------------------------------
#  Casamento: de QUAL louvor do app é esta cifra?
# --------------------------------------------------------------------------

def compacto(t):
    """so_letras sem os espaços. O OCR erra o espaço o tempo todo — lê
    "QUÃOCEGOANDEI" onde está "QUÃO CEGO ANDEI" — e comparar sem espaço nenhum
    tira essa fonte de erro do caminho."""
    return so_letras(t).replace(" ", "")


def gramas(t, n=4):
    """Os pedaços de n letras seguidas. Duas grafias do mesmo texto compartilham
    quase todos; um erro de OCR só estraga os n gramas que o cercam."""
    return set(t[i:i + n] for i in range(len(t) - n + 1))


class Casador(object):
    """Diz de que louvor do app é cada cifra lida do PDF.

    POR QUE ISTO EXISTE: casar só por título IDÊNTICO jogava fora 824 das 1.563
    cifras lidas — mais da metade do trabalho da extração, medido nos três PDFs.
    Foi assim que "O SANGUE DE JESUS TEM PODER PARA SALVAR" (nº 2 da Coletânea)
    apareceu sem cifra no Sistema: a cifra foi lida certa, com tom e acordes, e
    descartada porque o título não coube na coluna do PDF e chegou aqui como
    "O SANGUE DE JESUS TEM PODER PARA" — faltando a última palavra.

    O título chega quebrado de quatro jeitos, e nenhum é raro:

        cortado pela coluna   "DE MADRUGADA EU BUSCO A"      (...A FACE DO SENHOR)
        dois num só           "OH! QUE PRECIOSO SANGUE  32 - O SANGUE DE JESU..."
        estragado pelo OCR    "HÁ VITÓRIA SEMPRE EM 11, SENHOR"     (era EM TI)
        sumido de vez         ""                      (sobrou só o corpo da cifra)

    O CONSERTO é usar três sinais em vez de um. Nenhum decide sozinho:

    TÍTULO  parecido, não idêntico. E o corte importa: título que é PREFIXO do
            outro — nos DOIS sentidos, porque tanto o PDF corta o título quanto
            cola dois num só — é o mesmo louvor.
    LETRA   4-gramas de caractere do corpo da cifra contra a letra que o app já
            tem. Sobrevive ao OCR: "Jelsus tem polder" ainda divide SUST, USTE,
            TEMP, EMPO com "JESUS TEM PODER". É o único sinal que sobra quando o
            título sumiu — e sozinho recupera 294 cifras.
    NÚMERO  só onde ele vale, e isso é MEDIDO por PDF, não suposto. Na Coletânea
            2018 o número lido bate com o do app em 398 de 404 conferências; nos
            Avulsos bate em 0 de 263, porque lá o app numera tudo como "AV".
            Confiar nele nos Avulsos casaria cifra com louvor sorteado.

    RESULTADO: 1.015 louvores com cifra passaram a 1.609, sem perder nenhum dos
    que já funcionavam, e sem piorar a qualidade — a conferência contra a letra
    conhecida continua em 94% de mediana e 87% de média, como antes.
    """

    def __init__(self, raiz=None):
        # A referência é dados/louvores.js, o BANCO DO APP, e não o indice.json
        # das cifras: o índice existe para o botão de cifra achar a página do
        # PDF e cobre só 1.030 dos 2.459 louvores. Enquanto a gravação dependeu
        # dele, 25 de cada 37 cifras certas eram jogadas fora.
        raiz = raiz or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        s = io.open(os.path.join(raiz, "dados", "louvores.js"), encoding="utf-8").read()
        L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
        if isinstance(L, dict):
            L = L.get("louvores", L)

        self.louvores = []
        self.titulos = []                        # o titulo cru, para agrupar irmaos
        self.por_titulo = defaultdict(list)      # titulo normalizado -> [indice]
        self.por_compacto = defaultdict(list)    # o mesmo, sem espaco nenhum
        self.por_numero = defaultdict(list)
        idx_letra, idx_titulo = defaultdict(list), defaultdict(list)
        for i, l in enumerate(L):
            linhas = [li for sl in l.get("slides", []) for li in sl.get("linhas", [])]
            texto, titulo = compacto(" ".join(linhas)), compacto(l["titulo"])
            g = gramas(texto)
            reg = {"chave": "%s|%s|%s" % (l.get("num") or "", l.get("titulo") or "",
                                          linhas[0] if linhas else ""),
                   "linhas": linhas, "titulo": titulo, "g": g,
                   # o número do app vem com zero à esquerda na Coletânea Antiga
                   # ("001"); o do PDF vem sem. Comparar sempre sem.
                   "num": (l.get("num") or "").lstrip("0") or (l.get("num") or "")}
            self.louvores.append(reg)
            self.titulos.append(l["titulo"] or "")
            for forma in {so_letras(l["titulo"]), sem_parenteses(l["titulo"])}:
                if forma:
                    self.por_titulo[forma].append(i)
            self.por_compacto[titulo].append(i)
            self.por_numero[reg["num"]].append(i)
            for x in g:
                idx_letra[x].append(i)
            for x in gramas(titulo, 3):
                idx_titulo[x].append(i)
        self.idx_letra, self.idx_titulo = idx_letra, idx_titulo
        # Grama que aparece em mais de 6% dos louvores ("DEUS", "SENH") não
        # distingue ninguém e ainda faz a busca varrer meio catálogo por grama.
        self.comuns = set(g for g, v in idx_letra.items()
                          if len(v) > len(self.louvores) * 0.06)
        self.confia_no_numero = {}

    # -- o caminho rápido, que já funcionava: título igual ao do app --
    def por_titulo_exato(self, titulo):
        return (self.por_titulo.get(so_letras(titulo))
                or self.por_titulo.get(sem_parenteses(titulo)))

    def calibrar(self, blocos, pdf):
        """A numeração DESTE PDF corresponde à do app? Mede nos blocos em que o
        título casou sozinho — ali sabemos a resposta certa e podemos conferir o
        número contra ela. Sem esta medida seria preciso escrever o nome de cada
        PDF no código, e o próximo livro que o operador importar chegaria com a
        regra errada."""
        bate = total = 0
        for num, titulo, _corpo, _tom in blocos:
            alvo = self.por_titulo_exato(titulo)
            if not alvo or num is None:
                continue
            total += 1
            if any(self.louvores[i]["num"] == str(num) for i in alvo):
                bate += 1
        self.confia_no_numero[pdf] = total >= 20 and bate >= total * 0.6
        return bate, total

    def casar(self, num, titulo, corpo, pdf):
        """(indice do louvor no app, como casou) — ou (None, "perdido")."""
        alvo = self.por_titulo_exato(titulo)
        if alvo:
            return alvo[0], "exato"

        texto = compacto(" ".join(l["t"] for l in corpo))
        g_letra = gramas(texto) - self.comuns
        t_pdf = compacto(titulo)
        usa_num = self.confia_no_numero.get(pdf) and num is not None

        # Só os candidatos plausíveis entram na conta cara: comparar o bloco com
        # os 2.459 louvores um a um levaria minutos por página.
        votos = Counter()
        for x in g_letra:
            for i in self.idx_letra.get(x, ()):
                votos[i] += 1
        cand = set(i for i, _ in votos.most_common(25))
        votos = Counter()
        for x in gramas(t_pdf, 3):
            for i in self.idx_titulo.get(x, ()):
                votos[i] += 1
        cand.update(i for i, _ in votos.most_common(15))
        if usa_num:
            cand.update(self.por_numero.get(str(num), ()))

        melhor, ponto = None, (-1, 0.0, 0.0)
        for i in cand:
            a = self.louvores[i]
            util = a["g"] - self.comuns
            # QUANTO da letra do app apareceu na leitura do PDF. Contenção, não
            # semelhança: o bloco do PDF pode trazer sobra da coluna vizinha, e
            # isso não deve baixar a nota de quem está todo lá dentro.
            n_letra = len(util & g_letra) / float(len(util)) if len(util) >= 12 else 0.0
            n_tit = 0.0
            if t_pdf and a["titulo"]:
                n_tit = difflib.SequenceMatcher(None, t_pdf, a["titulo"]).ratio()
                if len(t_pdf) >= 12 and a["titulo"].startswith(t_pdf):
                    n_tit = max(n_tit, 0.92)         # o PDF cortou o título
                if len(a["titulo"]) >= 12 and t_pdf.startswith(a["titulo"]):
                    n_tit = max(n_tit, 0.92)         # dois cabeçalhos colados
            num_ok = 1 if (usa_num and a["num"] == str(num)) else 0
            # Um sinal forte basta; dois médios também. O número sozinho nunca:
            # ele só abaixa a exigência dos outros dois, porque no PDF escaneado
            # o OCR troca 7 por 1 e faria a cifra cair no louvor vizinho.
            if not (n_letra >= 0.45 or n_tit >= 0.80
                    or (n_tit >= 0.62 and n_letra >= 0.25)
                    or (num_ok and (n_tit >= 0.5 or n_letra >= 0.30))):
                continue
            # o número desempata primeiro: "DAS PROFUNDEZAS CLAMO A TI," casa
            # igualmente bem com o nº 89 e com o nº 295, e só o número sabe qual
            p = (num_ok, round(max(n_letra, n_tit), 2), n_letra + n_tit)
            if p > ponto:
                melhor, ponto = i, p
        if melhor is None:
            return None, "perdido"
        return melhor, ("numero" if ponto[0] else "texto")

    def irmaos(self, i):
        """Todas as chaves do app que são ESTE louvor. O mesmo louvor está no
        catálogo até quatro vezes — "Coletânea 2018" nº 1 e "Coletânea Antiga"
        nº 001 são a mesma música — e a cifra vale para todas.

        São TRÊS formas do título, porque o mesmo louvor foi digitado de jeitos
        diferentes em cada coletânea e nenhuma forma sozinha junta todas:

            título inteiro   o caso comum, o mesmo texto nas duas coletâneas
            sem parênteses   o app separa "O SENHOR É O MEU PASTOR (REFRIGERA A
                             MINHA ALMA)" de "(BONDADE E MISERICÓRDIA)"; o PDF
                             traz só "O SENHOR É O MEU PASTOR"
            sem espaço       "GUIA, Ó CRISTO, MINHA NAU" e "GUIA CRISTO MINHA
                             NAU" só ficam iguais quando a pontuação some

        Tirar qualquer uma das três custa cifras: só o título inteiro perde 8
        louvores que já funcionavam, só as duas primeiras perde outros 81.
        """
        titulo = self.titulos[i]
        iguais = []
        for grupo in (self.por_titulo.get(so_letras(titulo)),
                      self.por_titulo.get(sem_parenteses(titulo)),
                      self.por_compacto.get(compacto(titulo))):
            for j in (grupo or ()):
                if j not in iguais:
                    iguais.append(j)
        return [self.louvores[j]["chave"] for j in (iguais or [i])]


def extrair(pasta=None, limite=0, aviso=None):
    from pypdf import PdfReader
    pasta = pasta or pasta_cifras()
    caminho_idx = os.path.join(pasta, "indice.json")
    if not os.path.exists(caminho_idx):
        raise SystemExit("Nao achei o indice das cifras. Rode indexar_cifras.py antes.")
    indice = json.load(io.open(caminho_idx, encoding="utf-8"))
    casador = Casador()
    if aviso:
        aviso("banco do app: %d louvores" % len(casador.louvores))

    acordes, feitos, paginas_lidas, sem_par = {}, 0, 0, 0
    qualidade = {}                       # chave -> nota da cifra que esta la'
    tons_mel = tons_das_melodias()
    trocou_tom = {}
    if aviso:
        aviso("melodicas com tom no caderno C: %d" % len(tons_mel))
    como = Counter()
    for nome in sorted({r["pdf"] for r in indice.values()}):
        cam = os.path.join(pasta, nome)
        if not os.path.exists(cam):
            if aviso:
                aviso("PDF ausente: %s" % nome)
            continue
        rot, _ = estrategia_do_pdf(nome)
        r = PdfReader(cam)
        if aviso:
            aviso("%s - %d paginas, ancora: %s" % (nome[:44], len(r.pages), rot))

        # O LIVRO INTEIRO ANTES DE CASAR: a calibração do número precisa ver
        # todas as páginas para saber se a numeração deste PDF corresponde à do
        # app. É a leitura do PDF que custa caro (minutos); guardar as cifras já
        # lidas custa o tamanho do acordes.json, cerca de 1 MB.
        blocos = []
        for p in range(len(r.pages)):
            try:
                achados = louvores_da_pagina(r.pages[p], nome)
            except Exception:
                continue
            paginas_lidas += 1
            blocos.extend(b for b in achados if any(l["a"] for l in b[2]))
            if limite and len(blocos) >= limite:
                break
        bate, total = casador.calibrar(blocos, nome)
        if aviso:
            aviso("   numero do PDF confere com o do app em %d de %d -> %s"
                  % (bate, total,
                     "usa" if casador.confia_no_numero[nome] else "ignora"))

        for num, titulo, corpo, tom in blocos:
            i, jeito = casador.casar(num, titulo, corpo, nome)
            como[jeito] += 1
            if i is None:
                sem_par += 1
                continue
            # a letra certa é a do louvor que ACABAMOS de identificar, não a do
            # título lido — que pode estar cortado ou estragado
            corpo2, trocadas, cobertura = consertar_pela_letra(
                corpo, casador.louvores[i]["linhas"])
            # QUAL cifra fica com o louvor quando mais de um livro tem ele.
            # Antes era "o primeiro que aparece manda", e o primeiro é sempre o
            # mesmo: os PDFs são lidos em ordem alfabética e "Coletânea 2018" —
            # o livro ESCANEADO, o de pior leitura — vem antes dos dois de texto
            # nativo. Toda vez que o mesmo louvor existia nos dois, a folha do
            # músico ficava com a versão do scanner. Medido: 430 louvores
            # tinham a cifra limpa dos Avulsos trocada pela do escaneado.
            # A nota é QUANTO DA LETRA DO APP a cifra conseguiu costurar — ou
            # seja, o quanto ela é mesmo este louvor — e desempata pelo número
            # de acordes. É medida do resultado, não preferência por livro.
            nota = (round(cobertura, 2), sum(len(l["a"]) for l in corpo2))
            mel = (tons_mel.get(so_letras(casador.titulos[i]))
                   or tons_mel.get(sem_parenteses(casador.titulos[i])))
            for chave in casador.irmaos(i):
                if chave in acordes and qualidade.get(chave, (0, 0)) >= nota:
                    continue
                reg = {"linhas": corpo2, "pdf": nome}
                if trocadas:
                    reg["ok"] = trocadas
                escolhido, de_onde = escolher_tom(tom, mel, corpo2)
                if escolhido != tom:
                    trocou_tom[chave] = (tom, escolhido)
                if escolhido:
                    reg["tom"] = escolhido
                    if de_onde:
                        reg["tom_de"] = de_onde
                if chave not in acordes:
                    feitos += 1
                acordes[chave] = reg
                qualidade[chave] = nota
        if limite and feitos >= limite:
            break
    if aviso:
        aviso("casamento: %s" % ", ".join("%s %d" % (k, v) for k, v in como.most_common()))
        aviso("cifras lidas sem louvor correspondente no app: %d" % sem_par)
        novos = sum(1 for a, _b in trocou_tom.values() if not a)
        aviso("tom corrigido pela melodica: %d (%d ganharam tom que nao tinham)"
              % (len(trocou_tom), novos))

    destino = os.path.join(pasta, "acordes.json")
    tmp = destino + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(acordes, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, destino)
    return acordes, destino, paginas_lidas


def conferir(acordes, raiz=None):
    """Mede o resultado contra a letra que já temos em louvores.js.

    Sem isto a extração "funciona" sempre: gera arquivo, imprime número bonito,
    e ninguém sabe se o que saiu é a letra do louvor ou lixo de OCR."""
    raiz = raiz or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cam = os.path.join(raiz, "dados", "louvores.js")
    if not os.path.exists(cam):
        return None
    s = io.open(cam, encoding="utf-8").read()
    L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    if isinstance(L, dict):
        L = L.get("louvores", L)
    conhecida = {}
    for l in L:
        t = so_letras(l["titulo"])
        txt = " ".join(so_letras(li) for sl in l.get("slides", [])
                       for li in sl.get("linhas", []))
        if t and txt:
            conhecida.setdefault(t, txt)

    notas = []
    for chave, reg in acordes.items():
        alvo = conhecida.get(so_letras(chave.split("|")[1]))
        if not alvo:
            continue
        saiu = so_letras(" ".join(l["t"] for l in reg["linhas"]))
        pals = {w for w in alvo.split() if len(w) > 3}
        if len(pals) < 8:
            continue
        notas.append(sum(1 for w in pals if w in saiu) / len(pals))
    if not notas:
        return None
    notas.sort()
    return {"n": len(notas), "mediana": notas[len(notas) // 2],
            "media": sum(notas) / len(notas),
            "bons": sum(1 for x in notas if x >= 0.8) / len(notas),
            "ruins": sum(1 for x in notas if x < 0.5) / len(notas)}


def main():
    limite = 0
    if "--limite" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--limite") + 1])
    acordes, destino, pgs = extrair(limite=limite,
                                    aviso=lambda m: sys.stderr.write("  " + m + "\n"))
    n_ac = sum(len(l["a"]) for v in acordes.values() for l in v["linhas"])
    n_li = sum(len(v["linhas"]) for v in acordes.values())
    com_tom = sum(1 for v in acordes.values() if v.get("tom"))
    print("paginas lidas               : %d" % pgs)
    print("louvores com cifra em texto : %d" % len(acordes))
    print("com tonalidade              : %d" % com_tom)
    print("linhas                      : %d  (%.1f por louvor)"
          % (n_li, n_li / max(1, len(acordes))))
    print("acordes posicionados        : %d  (%.1f por louvor)"
          % (n_ac, n_ac / max(1, len(acordes))))
    print("arquivo                     : %s (%.0f KB)"
          % (destino, os.path.getsize(destino) / 1024.0))
    if "--conferir" in sys.argv or True:
        m = conferir(acordes)
        if m:
            print("\nCONFERENCIA contra a letra que ja temos (n=%d):" % m["n"])
            print("  palavras da letra que saíram certas: mediana %.0f%%, media %.0f%%"
                  % (m["mediana"] * 100, m["media"] * 100))
            print("  acima de 80%%: %.0f%%    abaixo de 50%%: %.0f%%"
                  % (m["bons"] * 100, m["ruins"] * 100))


if __name__ == "__main__":
    main()
