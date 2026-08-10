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
ACORDE = re.compile(r"^[A-G](#|b)?(m|M|maj|min|dim|aug|sus|add)?[0-9]{0,2}"
                    r"(\+|-)?(\([#b]?[0-9]{1,2}\))?(/[A-G](#|b)?)?$")

# separador do cabecalho: hifen comum, en dash, em dash, ou NADA
TRACO = "-‐‑‒–—―−"


def pasta_cifras():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Sistema Projecao", "cifras")


def eh_acorde(t):
    t = t.strip().strip("|")
    return bool(t) and len(t) <= 9 and bool(ACORDE.match(t))


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

def montar_bloco(linhas, ini, fim):
    """[{'t': letra, 'a': [[coluna, acorde], ...]}] de um louvor."""
    saida, guardados, tom = [], None, None
    for col, _y, fs in linhas[ini:fim]:
        t = texto_da_linha(fs)
        if not t.strip():
            continue
        m = SO_TOM.search(t)
        if m and tom is None:
            tom = m.group(1).strip()
            continue
        # por TOKEN, nao por fragmento: o PDF pode desenhar "Gm  Gm/F Gm/Eb"
        # num pedaco so, e ai o pedaco inteiro nao e' acorde nenhum.
        toks = [f for f in fs if f[2].strip()]
        palavras = tokens_com_x(fs)
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
        if not letra.strip():
            guardados = None
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


def consertar_pela_letra(corpo, letra_certa, minimo=0.5):
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
    """
    if not letra_certa:
        return corpo, 0
    uteis = [i for i, l in enumerate(corpo) if len(so_letras(l["t"])) >= 6]
    if not uteis:
        return corpo, 0
    A = [so_letras(corpo[i]["t"]) for i in uteis]
    B = [so_letras(x) for x in letra_certa]
    n, m = len(A), len(B)
    if not m:
        return corpo, 0

    VAZIO = -0.28                       # custo de pular uma linha de um lado
    pont = [[0.0] * (m + 1) for _ in range(n + 1)]
    veio = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        pont[i][0] = pont[i - 1][0] + VAZIO
        veio[i][0] = 1
    for j in range(1, m + 1):
        pont[0][j] = pont[0][j - 1] + VAZIO
        veio[0][j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            casa = pont[i - 1][j - 1] + (_parecido(A[i - 1], B[j - 1]) - 0.45)
            sobe = pont[i - 1][j] + VAZIO
            lado = pont[i][j - 1] + VAZIO
            melhor = max(casa, sobe, lado)
            pont[i][j] = melhor
            veio[i][j] = 0 if melhor == casa else (1 if melhor == sobe else 2)

    pares = {}
    i, j = n, m
    while i > 0 and j > 0:
        d = veio[i][j]
        if d == 0:
            if _parecido(A[i - 1], B[j - 1]) >= minimo:
                pares[uteis[i - 1]] = j - 1
            i -= 1
            j -= 1
        elif d == 1:
            i -= 1
        else:
            j -= 1

    saida, trocadas = [], 0
    for k, linha in enumerate(corpo):
        if k not in pares:
            saida.append(linha)
            continue
        nova = letra_certa[pares[k]]
        velha = linha["t"]
        mapa = {}
        for a, b, t in difflib.SequenceMatcher(None, velha, nova).get_matching_blocks():
            for c in range(t):
                mapa[a + c] = b + c
        acordes = []
        for col, nome in linha["a"]:
            if col in mapa:
                acordes.append([mapa[col], nome])
            else:                       # caiu num trecho que o OCR inventou
                antes = [c for c in mapa if c <= col]
                base = mapa[max(antes)] + (col - max(antes)) if antes else 0
                acordes.append([base, nome])
        # so' acorde de verdade: no PDF escaneado o OCR devolve coisas como
        # 'E91#" 4)' e '13' na linha de acordes. A linha inteira ainda vale --
        # os acordes legiveis ao lado estao certos -- mas o lixo nao pode ir
        # para a tela do musico.
        acordes = [[max(0, min(len(nova), c)), nm] for c, nm in acordes if eh_acorde(nm)]
        acordes.sort()
        saida.append({"t": nova, "a": acordes})
        trocadas += 1
    return saida, trocadas


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


def chaves_dos_louvores(raiz=None):
    """{titulo normalizado: [chave do app, ...]} lido de dados/louvores.js.

    Casamos com o BANCO DO APP, não com indice.json. O indice.json existe para
    o botão de cifra achar a página do PDF e cobre só uma parte: 1.030 títulos
    para os 2.459 louvores. Enquanto a gravação dependeu dele, 25 de cada 37
    cifras extraídas certas eram jogadas fora — títulos corretos, extração
    correta, e mesmo assim descartados.
    """
    raiz = raiz or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cam = os.path.join(raiz, "dados", "louvores.js")
    s = io.open(cam, encoding="utf-8").read()
    L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    if isinstance(L, dict):
        L = L.get("louvores", L)
    mapa = defaultdict(list)
    for l in L:
        linhas = [li for sl in l.get("slides", []) for li in sl.get("linhas", [])]
        chave = "%s|%s|%s" % (l.get("num") or "", l.get("titulo") or "",
                              linhas[0] if linhas else "")
        for forma in {so_letras(l["titulo"]), sem_parenteses(l["titulo"])}:
            if forma:
                mapa[forma].append(chave)
    return mapa


def extrair(pasta=None, limite=0, aviso=None):
    from pypdf import PdfReader
    pasta = pasta or pasta_cifras()
    caminho_idx = os.path.join(pasta, "indice.json")
    if not os.path.exists(caminho_idx):
        raise SystemExit("Nao achei o indice das cifras. Rode indexar_cifras.py antes.")
    indice = json.load(io.open(caminho_idx, encoding="utf-8"))
    banco = chaves_dos_louvores()
    letras = letras_dos_louvores()
    if aviso:
        aviso("banco do app: %d titulos" % len(banco))

    acordes, feitos, paginas_lidas, sem_par = {}, 0, 0, 0
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
        for p in range(len(r.pages)):
            try:
                achados = louvores_da_pagina(r.pages[p], nome)
            except Exception:
                continue
            paginas_lidas += 1
            for num, titulo, corpo, tom in achados:
                if not any(l["a"] for l in corpo):
                    continue                       # sem acorde nenhum: nao serve
                alvo = banco.get(so_letras(titulo)) or banco.get(sem_parenteses(titulo))
                if not alvo:
                    sem_par += 1
                    continue
                certa = letras.get(so_letras(titulo)) or letras.get(sem_parenteses(titulo))
                corpo2, trocadas = consertar_pela_letra(corpo, certa)
                for chave in alvo:
                    if chave in acordes:
                        continue                   # o primeiro que aparece manda
                    reg = {"linhas": corpo2, "pdf": nome}
                    if trocadas:
                        reg["ok"] = trocadas
                    if tom:
                        reg["tom"] = tom
                    acordes[chave] = reg
                    feitos += 1
            if limite and feitos >= limite:
                break
        if limite and feitos >= limite:
            break
    if aviso:
        aviso("cifras lidas sem louvor correspondente no app: %d" % sem_par)

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
