# -*- coding: utf-8 -*-
"""Refaz a tabela VERSÍCULO -> LOUVORES lendo o texto pela FIGURA, não só pela
palavra.

POR QUE ELE EXISTE
------------------
A tabela antiga casava PALAVRA com PALAVRA. Deuteronômio 24:4 fala do primeiro
marido que não pode tornar a tomar a mulher — e o Sistema sugeria "SE DEUS
QUISER ME ABENÇOAR", que não tem nada a ver. O Samuel reclamou com razão:

    "Por que que tem a ver uma coisa com a outra? (...) a revelação a respeito
     do marido é que o marido é Jesus e a esposa é a igreja."

Na doutrina da Igreja Cristã Maranata o texto se lê pela figura: o marido é
Cristo, a esposa é a Igreja, a herança é a terra prometida. Quem lê só a
palavra fica cego para isso.

COMO ELE FUNCIONA
-----------------
Para cada versículo monta uma consulta com três camadas:

  1. as PALAVRAS do versículo e dos vizinhos (o assunto raramente cabe numa
     linha só), pesadas por raridade (IDF);
  2. as FAMÍLIAS de palavras de `indexar_temas.py` — a ponte que já existia;
  3. as FIGURAS de `tipologia_maranata.json`: se o texto diz "marido", entram
     na busca esposo, noivo, bodas, Igreja, aliança... É esta camada que faz
     Deuteronômio 24 encontrar "QUEM PODERÁ" e "UM DIA EU QUIS TE DEIXAR".

Depois pontua os louvores por cosseno e guarda os três melhores por versículo,
que é o que cabe na tela sem empurrar a grade para fora.

O QUE ELE NÃO É
---------------
Não é revelação e não imita revelação. É uma ferramenta de busca que segue a
doutrina publicada da igreja onde ela foi encontrada — quem revela é o Senhor.

    python ferramentas/indexar_sugestoes.py
"""
import io
import json
import math
import os
import re
import sys
import unicodedata
from collections import defaultdict

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERR = os.path.join(AQUI, "ferramentas")
DADOS = os.path.join(AQUI, "dados")

POR_VERSICULO = 3          # o que a tela mostra de primeira
VIZINHOS = 4               # versículos de cada lado que entram na consulta
PESO_VIZINHO = 0.45
PESO_FAMILIA = 0.55
# a figura pesa MAIS que a família: ela é a leitura da igreja, não um palpite
PESO_FIGURA = {"explicita": 0.95, "forte": 0.80, "provavel": 0.60}
# os freios da ponte das figuras, medidos contra a Bíblia inteira:
#   teto 0.62 -> a figura mal aparecia; teto sem limite -> "A NOIVA É A IGREJA"
#   virava o 1º lugar de 37% dos versículos. Estes números são o meio-termo
#   que passou no gabarito do Samuel SEM virar monocultura.
TETO_FIGURA = float(os.environ.get("FIG_TETO", "0.88"))
GATILHO_RARO = float(os.environ.get("FIG_RARO", "1.8"))
MAX_FIGURAS = int(os.environ.get("FIG_MAX", "3"))


def normal(t):
    t = unicodedata.normalize("NFD", t or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def palavras(t):
    return [p for p in re.findall(r"[a-z]{3,}", normal(t))]


def carregar_js(nome):
    s = io.open(os.path.join(DADOS, nome), encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))


def preparar_figuras():
    """Lê o dicionário de figuras e devolve (gatilhos, temas) já normalizados.

    gatilho = palavra que aparece no TEXTO BÍBLICO ("marido", "muro")
    tema    = palavra que o LOUVOR usaria ("esposo", "bodas", "igreja")
    """
    # A AMPLIADA VEM PRIMEIRO. É o material dos obreiros, e ele é autoridade
    # sobre o resumo antigo. Conferido antes de ligar: a ampliada carrega as 131
    # figuras do `tipologia_maranata.json` com o significado IDÊNTICO, palavra
    # por palavra, e traz 178 a mais — é superconjunto, não versão divergente.
    # Se um dia divergirem, quem manda continua sendo o material dos obreiros.
    caminho = os.path.join(FERR, "tipologia_ampliada.json")
    if not os.path.exists(caminho):
        caminho = os.path.join(FERR, "tipologia_maranata.json")
    if not os.path.exists(caminho):
        print("!! nenhuma tipologia encontrada — seguindo sem as figuras")
        return []
    print("figuras lidas de: %s" % os.path.basename(caminho))
    d = json.load(io.open(caminho, encoding="utf-8"))
    figuras = []
    for f in d.get("figuras", []):
        gat = set()
        for g in [f.get("termo", "")] + list(f.get("variantes") or []):
            for p in palavras(g):
                if len(p) >= 4:              # "mar", "ma" pegavam dentro de outras
                    gat.add(p)
        temas = set()
        for t in f.get("temas") or []:
            temas.update(p for p in palavras(t) if len(p) >= 4)
        if gat and temas:
            figuras.append({
                "termo": f.get("termo", ""),
                "g": sorted(gat),
                "t": sorted(temas),
                "peso": PESO_FIGURA.get(f.get("confianca"), 0.6),
            })
    return figuras


def main():
    print("lendo os dados…")
    louvores = carregar_js("louvores.js")
    biblia = carregar_js("biblia.js")
    temas = carregar_js("temas.js")
    figuras = preparar_figuras()
    idf = temas["idf"]
    vetores = temas["louvores"]
    print("  louvores: %d | figuras: %d | palavras com peso: %d"
          % (len(louvores), len(figuras), len(idf)))

    # A IDENTIDADE do louvor, igual à do app (`identTitulo` em app.js): título
    # + começo da primeira linha, tudo reduzido a letras e números. É o que
    # reconhece a mesma peça repetida entre a coletânea de 2018 e a Antiga.
    def so_letras(t):
        return " ".join(re.sub(r"[^a-z0-9]+", " ", normal(t)).split())

    ident_cache = {}

    def ident(i):
        d = ident_cache.get(i)
        if d is None:
            s = louvores[i] if i < len(louvores) else {}
            slides = s.get("slides") or []
            linha1 = ((slides[0] or {}).get("linhas") or [""])[0] if slides else ""
            d = so_letras(s.get("titulo") or "") + "|" + so_letras(linha1)[:12]
            ident_cache[i] = d
        return d

    # índice invertido: palavra -> [(louvor, peso)] — sem isto seriam 63 milhões
    # de multiplicações por versículo, e a máquina da igreja não é de brincadeira
    invertido = defaultdict(list)
    normas = []
    for i, p in enumerate(vetores):
        s = 0.0
        for k, v in p.items():
            invertido[k].append((i, v))
            s += v * v
        normas.append(math.sqrt(s) or 1.0)

    familias = temas["familias"]

    # ---- a consulta de um versículo -------------------------------------
    def pontuar(q):
        """Cosseno do versículo contra todos os louvores, pelo índice invertido."""
        if not q:
            return []
        nq = math.sqrt(sum(x * x for x in q.values())) or 1.0
        pontos = defaultdict(float)
        for k, peso in q.items():
            for i, pv in invertido.get(k, ()):
                pontos[i] += peso * pv
        return sorted(((i, s / (normas[i] * nq)) for i, s in pontos.items()),
                      key=lambda a: -a[1])[:12]

    def consulta(texto, vizinhos, com_figuras=True):
        q = {}
        do_trecho = set()

        def por(t, w):
            for p in palavras(t):
                do_trecho.add(p)
                g = idf.get(p)
                if g:
                    q[p] = max(q.get(p, 0.0), w * g)

        por(texto, 1.0)
        for t in vizinhos:
            por(t, PESO_VIZINHO)

        # a ponte das famílias: duas palavras da família, não uma (uma é acaso)
        for fam in familias.values():
            if sum(1 for p in fam if p in do_trecho) < 2:
                continue
            for p in fam:
                g = idf.get(p)
                if g:
                    q[p] = max(q.get(p, 0.0), PESO_FAMILIA * g)

        # A PONTE DAS FIGURAS — com três freios, aprendidos na marra.
        #
        # Sem freio, "A NOIVA É A IGREJA" virou o primeiro lugar de 37% dos
        # versículos da Bíblia inteira: a figura afogava o texto, porque
        # "terra", "casa", "filho" e "povo" disparam em quase toda página.
        #
        #   1. o gatilho precisa ser RARO (ou vir acompanhado de outro): dois
        #      gatilhos comuns valem um raro;
        #   2. no máximo DUAS figuras por versículo, as de gatilho mais raro —
        #      um texto fala de uma coisa, não de dez;
        #   3. o tema da figura nunca pesa mais que a própria palavra do
        #      versículo: ela entra como ponte, não como dona da consulta.
        achadas = []
        if q and com_figuras:
            teto = TETO_FIGURA * max(q.values())
            candidatas = []
            for f in figuras:
                raro = 0.0
                n = 0
                for p in f["g"]:
                    if p in do_trecho:
                        n += 1
                        raro = max(raro, idf.get(p, 0.0))
                if not n:
                    continue
                if raro < GATILHO_RARO and n < 2:   # gatilho comum e sozinho: não conta
                    continue
                candidatas.append((raro + 0.3 * (n - 1), f))
            candidatas.sort(key=lambda a: -a[0])
            for _forca, f in candidatas[:MAX_FIGURAS]:
                achadas.append(f["termo"])
                for p in f["t"]:
                    g = idf.get(p)
                    if g:
                        q[p] = max(q.get(p, 0.0), min(f["peso"] * g, teto))
        return q, achadas

    saida = {}
    ordem = biblia["ordem"]
    total = 0
    for li, livro in enumerate(ordem):
        caps = biblia["livros"][livro]
        for ci, versos in enumerate(caps):
            nums = sorted(int(k) for k in versos.keys())
            for v in nums:
                texto = versos[str(v)] if str(v) in versos else versos.get(v, "")
                viz = [versos.get(str(k), versos.get(k, "")) for k in
                       range(v - VIZINHOS, v + VIZINHOS + 1) if k != v]
                vizinhos = [x for x in viz if x]
                # DUAS leituras do mesmo versículo: a da PALAVRA (como sempre
                # foi) e a da FIGURA. A da palavra fica com o primeiro lugar —
                # quando o louvor diz a mesma coisa que o texto, ninguém tem
                # que adivinhar. "NO CÉU HÁ JANELAS ABERTAS" em Malaquias 3:10
                # não pode sair da frente por causa de nenhuma figura.
                # A da figura entra logo atrás e completa: é ali que "A NOIVA É
                # A IGREJA" chega em Efésios 5, e "UM DIA EU QUIS TE DEIXAR"
                # chega em Deuteronômio 24.
                q_lit, _ = consulta(texto, vizinhos, com_figuras=False)
                q_fig, _ = consulta(texto, vizinhos, com_figuras=True)
                lit = pontuar(q_lit)
                fig = pontuar(q_fig)
                if not lit and not fig:
                    continue
                escolha, vistos = [], set()
                for fonte in (lit[:1], fig, lit):
                    for i, s in fonte:
                        # o mesmo louvor existe em DUAS coletâneas (2018 e
                        # Antiga): guardar os dois gastava uma das três vagas
                        # com o título repetido. O `montarRoda` do app já
                        # descartava a cópia na tela — então o versículo
                        # entregava dois louvores e o programa completava
                        # puxando dos vizinhos. Aqui a vaga volta a ser útil.
                        # A chave é a MESMA do app (`identTitulo`): título +
                        # começo da primeira linha.
                        if ident(i) in vistos:
                            continue
                        vistos.add(ident(i))
                        escolha.append((i, s))
                        if len(escolha) >= POR_VERSICULO:
                            break
                    if len(escolha) >= POR_VERSICULO:
                        break
                if not escolha:
                    continue
                alto = max(s for _i, s in escolha) or 1.0
                saida["%d.%d.%d" % (li, ci + 1, v)] = [
                    [i, int(round(100 * s / alto))] for i, s in escolha]
                total += 1
        if li % 10 == 0:
            print("  %-22s %6d versículos" % (livro, total))

    txt = "window.SUGESTOES=" + json.dumps(saida, ensure_ascii=False,
                                           separators=(",", ":")) + ";"
    io.open(os.path.join(DADOS, "sugestoes.js"), "w", encoding="utf-8").write(txt)
    print("versículos com sugestão: %d  (%.0f KB)" % (len(saida), len(txt) / 1024.0))

    # o runtime também precisa das figuras, para a parte que é calculada na hora
    mini = [{"g": f["g"], "t": f["t"], "p": f["peso"]} for f in figuras]
    t2 = "window.TIPOLOGIA=" + json.dumps(mini, ensure_ascii=False,
                                          separators=(",", ":")) + ";"
    io.open(os.path.join(DADOS, "tipologia.js"), "w", encoding="utf-8").write(t2)
    print("figuras para o programa: %d  (%.0f KB)" % (len(mini), len(t2) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
