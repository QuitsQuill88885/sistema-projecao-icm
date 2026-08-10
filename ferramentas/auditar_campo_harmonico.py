# -*- coding: utf-8 -*-
"""Audita as cifras pela SEQUENCIA de acordes, nao pela aparencia.

A IDEIA
=======
Um louvor da igreja anda dentro do campo harmonico do seu tom. Em Sol maior os
acordes sao G Am Bm C D Em F#dim, mais um ou outro emprestimo (dominante
secundaria, acorde da menor paralela). Se um louvor "em Sol" tem Bbm, F#m e
Ebm, uma de duas coisas aconteceu: o OCR estragou os acordes, ou o tom anotado
nao e' o tom do louvor. Ler cifra por cifra a olho nao acha isso; contar acha.

DUAS CONTAS POR LOUVOR
----------------------
fora_estrito  acorde que nao esta' na tabela diatonica do tom (com a dominante
              na V e a menor harmonica ja' liberadas). E' o numero que a
              pergunta pede: "metade fora" e' o sinal de alarme.
fora_grave    fora_estrito E TAMBEM sem explicacao musical nenhuma: nao e'
              dominante secundaria, nao vem da paralela (maior<->menor), nao e'
              diminuto de passagem. Esse e' o detector de estrago: um Bbm em
              Sol maior nao tem desculpa.

E ainda: reajusta o tom. Para cada louvor procura, entre os 24 tons, qual
explicaria melhor os acordes que estao la'. Se outro tom explica MUITO melhor
que o anotado, o problema e' o tom (erro de leitura do "Tonalidade"), nao os
acordes. Isso separa dois defeitos que se parecem.

Uso:
    python auditar_campo_harmonico.py
    python auditar_campo_harmonico.py --piores 40
    python auditar_campo_harmonico.py --csv saida.csv
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# --------------------------------------------------------------------------
#  Notas e acordes
# --------------------------------------------------------------------------
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NOME = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

RE_ACORDE = re.compile(r"^([A-G])([#b]?)(.*)$")


def altura(letra, acidente):
    """Letra + acidente -> classe de altura 0..11 (Bb e A# sao a mesma coisa)."""
    n = PC[letra]
    if acidente == "#":
        n += 1
    elif acidente == "b":
        n -= 1
    return n % 12


def ler_acorde(s):
    """'C#m7(9)/E' -> (altura=1, qualidade='min', baixo=4). None se nao e' acorde.

    qualidade: maj, min, dom, dim, hdim, aug, amb
      amb  = sus/5, que nao diz se e' maior ou menor; combina com os dois.
      dom  = tem 7 menor de verdade (C7). "C9" NAO e' dom: na cifra brasileira
             C9 e' C com nona acrescentada, acorde MAIOR. Confundir os dois
             inventaria dominante secundaria em 84 lugares so' com "A9".
    """
    if not s:
        return None
    s = s.strip().strip("|").strip()
    m = RE_ACORDE.match(s)
    if not m:
        return None
    raiz = altura(m.group(1), m.group(2))
    resto = m.group(3)

    baixo = None
    if "/" in resto:
        resto, parte = resto.split("/", 1)
        mb = RE_ACORDE.match(parte.strip())
        if mb and not mb.group(3):
            baixo = altura(mb.group(1), mb.group(2))
        elif mb:
            baixo = altura(mb.group(1), mb.group(2))
        else:
            return None                      # "/" sem nota depois: token quebrado

    r = resto
    if re.search(r"\(?b5\)?", r) and r.lstrip().startswith("m"):
        q = "hdim"
    elif r.startswith(("dim", "°", "º")):
        q = "dim"
    elif r.startswith("aug") or r == "+":
        q = "aug"
    elif r.startswith("maj") or r.startswith("min"):
        q = "maj" if r.startswith("maj") else "min"
    elif r.startswith("m"):
        q = "min"
    elif r.startswith("sus") or r in ("4", "5", "4M"):
        q = "amb"
    elif re.match(r"^7(?![M+])", r) or re.match(r"^(9|13)?7(?![M+])", r):
        q = "dom"
    elif re.match(r"^(6|9|11|13|2|add)", r):
        q = "maj"
    elif r == "":
        q = "maj"
    elif r.startswith(("M", "7M", "+")):
        q = "maj"
    else:
        q = "maj"

    # sufixo de diminuto depois do numero: "E°7", "B#º"
    if "°" in resto or "º" in resto:
        q = "dim"
    return (raiz, q, baixo)


# --------------------------------------------------------------------------
#  Campo harmonico
# --------------------------------------------------------------------------
# grau (semitons a partir da tonica) -> qualidades que o campo aceita.
CAMPO_MAIOR = {
    0:  {"maj", "amb"},
    2:  {"min", "hdim", "amb"},
    4:  {"min", "amb"},
    5:  {"maj", "amb"},
    7:  {"maj", "dom", "amb"},          # a dominante com 7 e' do campo
    9:  {"min", "amb"},
    11: {"dim", "hdim"},
}
# menor natural + harmonica juntas: a V maior e o VII# diminuto sao do idioma.
CAMPO_MENOR = {
    0:  {"min", "amb"},
    2:  {"dim", "hdim", "amb"},
    3:  {"maj", "amb"},
    5:  {"min", "amb"},
    7:  {"min", "maj", "dom", "amb"},
    8:  {"maj", "amb"},
    10: {"maj", "dom", "amb"},
    11: {"dim", "hdim"},
}
GRAU_MAIOR = "I ii iii IV V vi vii".split()
GRAU_MENOR = "i ii III iv V VI VII vii".split()


def campo(modo):
    return CAMPO_MAIOR if modo == "maior" else CAMPO_MENOR


def ler_tom(t):
    """'Bb' -> (10,'maior'); 'F#m' -> (6,'menor'). None se nao der."""
    if not t:
        return None
    m = RE_ACORDE.match(t.strip())
    if not m:
        return None
    modo = "menor" if m.group(3).strip().startswith("m") else "maior"
    return (altura(m.group(1), m.group(2)), modo)


def nome_tom(tom):
    return NOME[tom[0]] + ("m" if tom[1] == "menor" else "")


def dentro(ac, tom):
    """O acorde pertence ao campo harmonico do tom?"""
    raiz, q, _ = ac
    grau = (raiz - tom[0]) % 12
    return q in campo(tom[1]).get(grau, set())


def explicavel(ac, tom, raizes_do_louvor):
    """Fora do campo, mas com explicacao musical corrente na igreja?

    (a) dominante secundaria: acorde maior/com-7 uma quinta acima de um acorde
        que REALMENTE aparece no louvor (D7 antes de G).
    (b) emprestimo modal: pertence ao campo da paralela (maior<->menor).
    (c) diminuto de passagem: qualquer diminuto e' ligacao, anda por fora.
    (d) aumentado: idem, e' passagem.
    """
    raiz, q, _ = ac
    if q in ("dim", "hdim", "aug"):
        return True
    paralela = (tom[0], "menor" if tom[1] == "maior" else "maior")
    if dentro(ac, paralela):
        return True
    if q in ("maj", "dom", "amb"):
        alvo = (raiz + 5) % 12
        if alvo in raizes_do_louvor and alvo != raiz:
            return True
    return False


def pontuar(acordes, tom):
    """Quantos acordes deste louvor cabem neste tom (peso por ocorrencia)."""
    return sum(1 for ac in acordes if dentro(ac, tom))


TODOS_OS_TONS = [(r, m) for m in ("maior", "menor") for r in range(12)]


# --------------------------------------------------------------------------
#  Modulacao — o louvor pode trocar de tom no meio, e troca mesmo
# --------------------------------------------------------------------------
# Medido: EXALTADO, DE HOJE EM DIANTE e TUDO PRA MIM TU ES passam por tres ou
# quatro tons cada um. Cobrar um tom so' do louvor inteiro condenaria arranjo
# bom como se fosse cifra estragada. Entao o caminho pelos tons e' procurado com
# Viterbi: cada acorde paga por nao caber no tom do momento, e trocar de tom
# custa TROCA. Assim uma secao inteira em outro tom compensa a troca; um acorde
# solto e esquisito nao compensa, e fica marcado como o defeito que e'.
TROCA = 3.0


def custo(ac, tom):
    if dentro(ac, tom):
        return 0.0
    raiz, q, _ = ac
    if q in ("dim", "aug"):
        return 0.4                       # passagem cromatica, anda por fora
    grau_alvo = (raiz + 5 - tom[0]) % 12
    if q in ("maj", "dom", "amb") and grau_alvo in campo(tom[1]):
        return 0.4                       # dominante secundaria
    return 1.0


def caminho_dos_tons(acordes):
    """(inexplicados, num_trocas, [tons na ordem]) pelo melhor caminho."""
    if not acordes:
        return 0, 0, []
    tons = TODOS_OS_TONS
    ant = {t: (custo(acordes[0], t), [t]) for t in tons}
    for ac in acordes[1:]:
        melhor_geral = min(ant.values(), key=lambda v: v[0])
        novo = {}
        for t in tons:
            fica = ant[t]
            vem = (melhor_geral[0] + TROCA, melhor_geral[1])
            base = fica if fica[0] <= vem[0] else vem
            novo[t] = (base[0] + custo(ac, t), base[1] + [t])
        ant = novo
    _c, caminho = min(ant.values(), key=lambda v: v[0])
    inexp = sum(1 for ac, t in zip(acordes, caminho) if custo(ac, t) >= 1.0)
    trocas = sum(1 for a, b in zip(caminho, caminho[1:]) if a != b)
    return inexp, trocas, caminho


# --------------------------------------------------------------------------
#  Leitura dos dados
# --------------------------------------------------------------------------
def diagnosticar(texto, ac, tom):
    """O acorde nao cabe. Que edicao de UMA letra faria caber?

    Isto amarra o defeito ao mecanismo: o extrator cola sufixo solto
    (colar_sufixos), e o OCR do livro escaneado solta 492 "m" e 534 "7". Quando
    um "m" solto e' colado no acorde errado, "E" vira "Em" — e "Em" no tom de
    Mi maior e' exatamente o que este audit acha. Se tirar o "m" faz caber, o
    culpado tem nome e endereco.
    """
    for rot, alvo in (
            ("m sobrando (E -> Em)", re.sub(r"m", "", texto, count=1)
             if re.search(r"^[A-G][#b]?m", texto) else None),
            ("m faltando (Em -> E)", re.sub(r"^([A-G][#b]?)", r"\1m", texto)
             if not re.search(r"^[A-G][#b]?m", texto) else None),
            ("7 sobrando", texto.replace("7", "", 1) if "7" in texto else None),
            ("# ou b trocado", texto.replace("#", "", 1) if "#" in texto else
             (texto.replace("b", "", 1) if re.match(r"^[A-G]b", texto) else None)),
    ):
        if not alvo:
            continue
        a2 = ler_acorde(alvo)
        if a2 and dentro(a2, tom):
            return rot
    if ac[1] in ("min", "maj") and ((ac[0] - tom[0]) % 12) in campo(tom[1]):
        return "qualidade errada no grau certo"
    return "raiz fora da escala"


def pasta(*p):
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Sistema Projecao", *p)


def carregar_melodias():
    """titulo -> tom do caderno C (instrumento em do = mesmo tom da cifra)."""
    arq = pasta("melodias", "indice.json")
    if not os.path.exists(arq):
        return {}
    with open(arq, encoding="utf-8") as f:
        idx = json.load(f)
    saida = {}
    for chave, reg in idx.get("louvores", {}).items():
        t = (reg.get("tons") or {}).get("C")
        if t:
            saida[chave.strip().upper()] = t
        tit = (reg.get("titulo") or "").strip().upper()
        if t and tit:
            saida[tit] = t
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piores", type=int, default=30)
    ap.add_argument("--csv", default="")
    ap.add_argument("--min-acordes", type=int, default=6)
    args = ap.parse_args()

    with open(pasta("cifras", "acordes.json"), encoding="utf-8") as f:
        dados = json.load(f)
    mel = carregar_melodias()

    linhas = []
    lixo_global = Counter()
    fora_por_acorde = Counter()
    diagnostico = Counter()
    exemplos = defaultdict(list)
    total_acordes = 0
    total_fora = 0
    total_grave = 0

    for chave, reg in dados.items():
        partes = chave.split("|")
        titulo = partes[1].strip().upper() if len(partes) > 1 else chave.upper()
        pdf = reg.get("pdf", "")
        tom_txt = reg.get("tom")
        tom = ler_tom(tom_txt)

        brutos = []
        for L in reg.get("linhas", []):
            for _col, a in L.get("a", []):
                brutos.append(a)
        lidos, lixo = [], []
        for b in brutos:
            ac = ler_acorde(b)
            if ac is None:
                lixo.append(b)
                lixo_global[b] += 1
            else:
                lidos.append((b, ac))

        n = len(lidos)
        total_acordes += n
        raizes = {ac[0] for _b, ac in lidos}

        melodia = mel.get(titulo)
        tom_mel = ler_tom(melodia)

        # assinatura: mesmo titulo + mesma sequencia de acordes = mesmo louvor.
        # O acervo tem o mesmo louvor gravado duas vezes (numero "55" e "055",
        # prefixo "AV" e o numero). Sem juntar, todo numero sai inflado.
        assin = (titulo, tuple(b for b, _ac in lidos))

        if not tom or n == 0:
            reg2 = dict(chave=chave, titulo=titulo, pdf=pdf, tom=tom_txt,
                        n=n, fora=None, grave=None, frac=None,
                        melhor=None, ganho=None, tom_mel=melodia,
                        piores="", lixo=len(lixo), sem_tom=not tom,
                        assin=assin, cobertura=None, intervalo=None,
                        inexp=None, finexp=None, trocas=None, rota="",
                        tom_inicial=None, inexp_nomes="")
            if n:
                i2, t2, c2 = caminho_dos_tons([ac for _b, ac in lidos])
                reg2.update(inexp=i2, finexp=i2 / n, trocas=t2,
                            tom_inicial=nome_tom(c2[0]))
            linhas.append(reg2)
            continue

        fora, grave, nomes_grave = 0, 0, []
        for b, ac in lidos:
            if dentro(ac, tom):
                continue
            fora += 1
            fora_por_acorde[b] += 1
            if not explicavel(ac, tom, raizes):
                grave += 1
                nomes_grave.append(b)
        total_fora += fora
        total_grave += grave

        acs = [ac for _b, ac in lidos]
        base = pontuar(acs, tom)
        melhor, melhor_pt = tom, base
        for cand in TODOS_OS_TONS:
            pt = pontuar(acs, cand)
            if pt > melhor_pt:
                melhor, melhor_pt = cand, pt
        ganho = melhor_pt - base
        # Cobertura: mesmo o MELHOR dos 24 tons explica quanto do louvor?
        # Se nem o melhor chega a 60%, nao e' tom errado — a cifra esta' quebrada
        # (acorde estragado, ou dois louvores misturados na leitura das colunas).
        cobertura = melhor_pt / n
        intervalo = (melhor[0] - tom[0]) % 12 if melhor[1] == tom[1] else None
        inexp, trocas, caminho = caminho_dos_tons(acs)
        nomes_inexp = [b for (b, ac), t in zip(lidos, caminho)
                       if custo(ac, t) >= 1.0]
        for (b, ac), t in zip(lidos, caminho):
            if custo(ac, t) >= 1.0:
                diagnostico[diagnosticar(b, ac, t)] += 1
                exemplos[diagnosticar(b, ac, t)].append(
                    "%s em %s (%s)" % (b, nome_tom(t), titulo[:30]))
        tons_usados = []
        for t in caminho:
            if not tons_usados or tons_usados[-1] != t:
                tons_usados.append(t)

        linhas.append(dict(
            chave=chave, titulo=titulo, pdf=pdf, tom=tom_txt, n=n,
            fora=fora, grave=grave, frac=fora / n, fgrave=grave / n,
            melhor=nome_tom(melhor), ganho=ganho, tom_mel=melodia,
            piores=" ".join(w for w, _c in Counter(nomes_grave).most_common(6)),
            lixo=len(lixo), sem_tom=False, cobertura=cobertura,
            intervalo=intervalo, assin=assin,
            inexp=inexp, finexp=inexp / n, trocas=trocas,
            tom_inicial=nome_tom(caminho[0]),
            rota=" ".join(nome_tom(t) for t in tons_usados[:6]),
            inexp_nomes=" ".join(w for w, _c in Counter(nomes_inexp).most_common(6)),
            bate_melodia=(None if not tom_mel else (tom_mel == tom)),
        ))

    # ---------------- relatorio ----------------
    vistos = set()
    unicos = []
    for r in linhas:
        if r["assin"] in vistos:
            continue
        vistos.add(r["assin"])
        unicos.append(r)
    com_tom = [r for r in unicos
               if not r["sem_tom"] and r["n"] >= args.min_acordes]

    print("=" * 78)
    print("CAMPO HARMONICO — auditoria de %d registros, %d acordes"
          % (len(dados), total_acordes))
    print("=" * 78)
    print("registros duplicados (mesmo titulo+acordes) . %d -> %d louvores unicos"
          % (len(linhas) - len(unicos), len(unicos)))
    sem_tom = [r for r in unicos if r["sem_tom"]]
    print("louvores sem tom anotado .................... %d" % len(sem_tom))
    print("louvores analisaveis (tom e >=%d acordes) .... %d"
          % (args.min_acordes, len(com_tom)))
    print("acordes fora do campo ....................... %d de %d  (%.1f%%)"
          % (total_fora, total_acordes, 100.0 * total_fora / max(1, total_acordes)))
    print("  destes, SEM explicacao musical ............ %d  (%.1f%% do acervo)"
          % (total_grave, 100.0 * total_grave / max(1, total_acordes)))
    print("tokens que nem acorde sao ................... %d ocorrencias, %d distintos"
          % (sum(lixo_global.values()), len(lixo_global)))
    if lixo_global:
        print("   " + ", ".join("%s(%d)" % (w, c)
                                for w, c in lixo_global.most_common(12)))

    # faixas
    print()
    print("DISTRIBUICAO — fracao de acordes fora do campo")
    faixas = [(0.0, 0.05), (0.05, 0.10), (0.10, 0.20), (0.20, 0.35),
              (0.35, 0.50), (0.50, 1.01)]
    for lo, hi in faixas:
        g = [r for r in com_tom if lo <= r["frac"] < hi]
        gp = [r for r in g if "2018" in r["pdf"]]
        print("  %3.0f%%–%3.0f%% .... %4d louvores   (%d = %.0f%% do escaneado 2018)"
              % (lo * 100, hi * 100, len(g), len(gp),
                 100.0 * len(gp) / max(1, len(g))))

    # por PDF
    print()
    print("POR PDF")
    porpdf = defaultdict(lambda: [0, 0, 0, 0])       # louvores, acordes, fora, grave
    for r in com_tom:
        s = porpdf[r["pdf"]]
        s[0] += 1
        s[1] += r["n"]
        s[2] += r["fora"]
        s[3] += r["grave"]
    for pdf, (nl, na, nf, ng) in sorted(porpdf.items(), key=lambda kv: -kv[1][1]):
        print("  %-46s %4d louvores %6d acordes  fora %5d (%4.1f%%)  grave %4d (%4.1f%%)"
              % (pdf[:46], nl, na, nf, 100.0 * nf / max(1, na),
                 ng, 100.0 * ng / max(1, na)))

    # --- a conta que sobra depois de perdoar modulacao ---
    print()
    print("DESCONTANDO A MODULACAO  (louvor pode trocar de tom; muitos trocam)")
    tot_n = sum(r["n"] for r in com_tom)
    tot_i = sum(r["inexp"] for r in com_tom)
    print("  acordes sem NENHUMA explicacao ... %d de %d  (%.1f%%)"
          % (tot_i, tot_n, 100.0 * tot_i / max(1, tot_n)))
    print("  louvores que modulam (>=1 troca) . %d de %d  (%.0f%%)"
          % (sum(1 for r in com_tom if r["trocas"] >= 1), len(com_tom),
             100.0 * sum(1 for r in com_tom if r["trocas"] >= 1) / max(1, len(com_tom))))
    for lo, hi in ((0.0, 0.02), (0.02, 0.05), (0.05, 0.10),
                   (0.10, 0.20), (0.20, 1.01)):
        g = [r for r in com_tom if lo <= r["finexp"] < hi]
        g18 = [r for r in g if "2018" in r["pdf"]]
        print("   %3.0f%%–%3.0f%% inexplicavel ... %4d louvores  (%d do 2018 escaneado)"
              % (lo * 100, hi * 100, len(g), len(g18)))
    print("  POR PDF (taxa de acorde inexplicavel):")
    agr = defaultdict(lambda: [0, 0, 0])
    for r in com_tom:
        s = agr[r["pdf"]]
        s[0] += 1
        s[1] += r["n"]
        s[2] += r["inexp"]
    for pdf, (nl, na, ni) in sorted(agr.items(), key=lambda kv: -kv[1][1]):
        print("    %-46s %6d acordes  %4d inexplicaveis (%.1f%%)"
              % (pdf[:46], na, ni, 100.0 * ni / max(1, na)))

    print()
    print("QUE EDICAO DE UMA LETRA CONSERTARIA O ACORDE INEXPLICAVEL")
    tdiag = sum(diagnostico.values())
    for rot, c in diagnostico.most_common():
        print("   %-30s %4d  (%4.1f%%)" % (rot, c, 100.0 * c / max(1, tdiag)))
        for ex in exemplos[rot][:3]:
            print("        ex: %s" % ex)

    print()
    print("OS %d COM MAIS ACORDE INEXPLICAVEL (ja' perdoada a modulacao)"
          % args.piores)
    for r in sorted([x for x in com_tom if x["n"] >= 10],
                    key=lambda r: (-r["finexp"], -r["inexp"]))[:args.piores]:
        marca = "2018" if "2018" in r["pdf"] else ("2025" if "2025" in r["pdf"] else "AVUL")
        print("  %-34s %s tom %-4s %3d/%-3d=%2.0f%% rota %-18s %s"
              % (r["titulo"][:34], marca, r["tom"], r["inexp"], r["n"],
                 100 * r["finexp"], r["rota"][:18], r["inexp_nomes"][:26]))

    # separar os dois defeitos
    print()
    print("SEPARANDO OS DOIS DEFEITOS  (louvores com >=20%% fora do campo)")
    ruins = [r for r in com_tom if r["frac"] >= 0.20]
    quebrado = [r for r in ruins if r["cobertura"] < 0.80]
    so_tom = [r for r in ruins if r["cobertura"] >= 0.80]
    print("  %d louvores com >=20%% dos acordes fora" % len(ruins))
    print("    tom errado, acordes bons ... %4d  (algum dos 24 tons explica >=80%%)"
          % len(so_tom))
    print("    a cifra e' que esta' rota .. %4d  (NENHUM tom explica 80%%)"
          % len(quebrado))
    for corte, rot in ((0.80, "<80%"), (0.70, "<70%"), (0.60, "<60%"), (0.50, "<50%")):
        g = [r for r in com_tom if r["cobertura"] < corte]
        g18 = [r for r in g if "2018" in r["pdf"]]
        print("  melhor tom cobre %-4s ....... %4d louvores  (%d do 2018 escaneado)"
              % (rot, len(g), len(g18)))

    print()
    print("SE O TOM ESTA' ERRADO, ERRADO POR QUANTO (mesmo modo, %d louvores)"
          % sum(1 for r in com_tom if r["ganho"] >= 3))
    hist = Counter(r["intervalo"] for r in com_tom if r["ganho"] >= 3)
    for iv, c in sorted(hist.items(), key=lambda kv: -kv[1])[:8]:
        rot = "modo diferente (relativa/paralela)" if iv is None else (
            "%+d semitom(s)" % (iv - 12 if iv > 6 else iv))
        print("   %-36s %3d" % (rot, c))

    # tom errado
    print()
    print("TOM ANOTADO x TOM EM QUE O LOUVOR COMECA (pelo caminho dos acordes)")
    disc = [r for r in com_tom if r["tom_inicial"] != r["tom"]]
    d18 = [r for r in disc if "2018" in r["pdf"]]
    print("  %d de %d louvores (%.0f%%) comecam em tom diferente do anotado; %d do 2018"
          % (len(disc), len(com_tom), 100.0 * len(disc) / max(1, len(com_tom)), len(d18)))
    limpos = [r for r in disc if r["finexp"] < 0.05 and r["n"] >= 12]
    print("  destes, %d tem cifra LIMPA (<5%% inexplicavel): o errado e' o tom, "
          "nao os acordes" % len(limpos))
    for r in sorted(limpos, key=lambda r: -r["n"])[:15]:
        marca = "2018" if "2018" in r["pdf"] else ("2025" if "2025" in r["pdf"] else "AVUL")
        print("     %-36s %s tom %-4s -> comeca em %-4s  melodica:%s"
              % (r["titulo"][:36], marca, r["tom"], r["tom_inicial"],
                 r["tom_mel"] or "-"))

    print()
    print("TOM PROVAVELMENTE ERRADO (outro tom explica >=3 acordes a mais)")
    trocar = sorted([r for r in com_tom if r["ganho"] >= 3],
                    key=lambda r: -r["ganho"])
    p2018 = sum(1 for r in trocar if "2018" in r["pdf"])
    print("  %d louvores; %d (%.0f%%) vem do escaneado 2018"
          % (len(trocar), p2018, 100.0 * p2018 / max(1, len(trocar))))
    for r in trocar[:20]:
        print("   %-42s tom %-4s -> %-4s (+%d)  fora %d/%d  melodia:%s"
              % (r["titulo"][:42], r["tom"], r["melhor"], r["ganho"],
                 r["fora"], r["n"], r["tom_mel"] or "-"))

    # discordancia com a melodica
    print()
    print("CONFERE COM A MELODICA (caderno C)")
    com_mel = [r for r in com_tom if r.get("bate_melodia") is not None]
    bate = [r for r in com_mel if r["bate_melodia"]]
    print("  %d louvores tem melodica; tom bate em %d (%.1f%%), diverge em %d"
          % (len(com_mel), len(bate), 100.0 * len(bate) / max(1, len(com_mel)),
             len(com_mel) - len(bate)))

    # piores
    print()
    print("OS %d PIORES (por fracao fora do campo, desempate pelo grave)" % args.piores)
    piores = sorted(com_tom, key=lambda r: (-r["frac"], -r["fgrave"]))[:args.piores]
    for r in piores:
        marca = "2018" if "2018" in r["pdf"] else ("2025" if "2025" in r["pdf"] else "AVUL")
        print("  %-36s %s tom %-4s fora %3d/%-3d=%3.0f%%  melhor %-4s cobre %3.0f%%  %s"
              % (r["titulo"][:36], marca, r["tom"], r["fora"], r["n"],
                 100 * r["frac"], r["melhor"], 100 * r["cobertura"],
                 r["piores"][:26]))

    print()
    print("OS %d MAIS ROTOS (nem o melhor dos 24 tons explica o louvor)" % args.piores)
    for r in sorted(com_tom, key=lambda r: r["cobertura"])[:args.piores]:
        marca = "2018" if "2018" in r["pdf"] else ("2025" if "2025" in r["pdf"] else "AVUL")
        print("  %-36s %s tom %-4s  %d acordes  melhor tom %-4s cobre so' %3.0f%%"
              % (r["titulo"][:36], marca, r["tom"], r["n"], r["melhor"],
                 100 * r["cobertura"]))

    print()
    print("OS %d PIORES SO' PELO GRAVE (acorde sem explicacao nenhuma)" % args.piores)
    for r in sorted(com_tom, key=lambda r: (-r["fgrave"], -r["grave"]))[:args.piores]:
        marca = "2018" if "2018" in r["pdf"] else ("2025" if "2025" in r["pdf"] else "AVUL")
        print("  %-38s %s tom %-4s  grave %3d/%-3d = %3.0f%%   %s"
              % (r["titulo"][:38], marca, r["tom"], r["grave"], r["n"],
                 100 * r["fgrave"], r["piores"][:40]))

    print()
    print("ACORDES QUE MAIS CAEM FORA (em todo o acervo)")
    for w, c in fora_por_acorde.most_common(25):
        print("   %-10s %4d" % (w, c))

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            wr = csv.writer(f, delimiter=";")
            wr.writerow(["chave", "titulo", "pdf", "tom", "acordes", "fora",
                         "frac_fora", "inexplicavel", "frac_inexplicavel",
                         "trocas_de_tom", "tom_inicial", "rota", "melhor_tom",
                         "ganho", "cobertura", "tom_melodica",
                         "acordes_inexplicaveis"])
            for r in sorted(linhas, key=lambda r: -(r["finexp"] or 0)):
                wr.writerow([r["chave"], r["titulo"], r["pdf"], r["tom"], r["n"],
                             r["fora"], "" if r["frac"] is None else "%.3f" % r["frac"],
                             r["inexp"],
                             "" if r["finexp"] is None else "%.3f" % r["finexp"],
                             r["trocas"], r["tom_inicial"], r.get("rota", ""),
                             r["melhor"], r["ganho"],
                             "" if r["cobertura"] is None else "%.3f" % r["cobertura"],
                             r["tom_mel"], r.get("inexp_nomes", "")])
        print("\nCSV: %s" % os.path.abspath(args.csv))


if __name__ == "__main__":
    main()
