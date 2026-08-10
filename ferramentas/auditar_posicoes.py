# -*- coding: utf-8 -*-
"""Mede se o acorde caiu na sílaba certa. Só POSIÇÃO — não julga o nome do acorde.

O acorde é guardado como [coluna, nome], onde coluna é o índice do caractere da
letra em que ele cai. Se a coluna estiver errada, a cifra na tela do músico
manda tocar a mudança na sílaba errada, e isso não aparece em nenhuma
conferência que só olhe se o acorde existe.

Cada defeito abaixo foi escolhido porque é IMPOSSÍVEL numa cifra correta, ou
porque a taxa dele nos dois PDFs de texto nativo serve de régua para a do PDF
escaneado.

    EMPILHADO   dois acordes na mesma coluna: dois acordes na mesma sílaba
    FORA        coluna >= tamanho da letra: acorde depois do fim da linha
    TUDO_ZERO   linha com 2+ acordes, todos na coluna 0
    SO_ZERO     linha com UM acorde só, na coluna 0
    AGLOMERADO  3+ acordes espremidos no primeiro quinto de uma letra longa
    NO_ESPACO   acorde caindo em cima de um espaço, não de uma sílaba
    DENSO       mais acordes do que palavras na linha
    DESORDEM    colunas fora de ordem crescente

E o DESLOCAMENTO: numa cifra bem alinhada o acorde cai muito mais no COMEÇO de
palavra do que no meio dela. Deslocando a linha inteira de -3 a +3 caracteres e
vendo qual deslocamento acerta mais começos de palavra, dá para dizer se a
linha está torta para um lado — e para que lado.

Uso:  set PYTHONIOENCODING=utf-8 & python auditar_posicoes.py
      python auditar_posicoes.py --piores 40
      python auditar_posicoes.py --exemplos "TRECHO DO TITULO"
"""
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict


def pasta_cifras():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Sistema Projecao", "cifras")


def carregar(caminho=None):
    caminho = caminho or os.path.join(pasta_cifras(), "acordes.json")
    return json.load(io.open(caminho, encoding="utf-8"))


def apelido(nome):
    """O nome do arquivo vem acentuado, e o mesmo "â" aparece composto num
    lugar e decomposto noutro — comparar a string inteira falha calado. Casa
    pelo pedaço que não tem acento."""
    n = nome or ""
    if "2018" in n:
        return "2018 ESCANEADO"
    if "2025" in n:
        return "2025 nativo"
    if "Avulsos" in n:
        return "Avulsos nativo"
    return n or "?"

DEFEITOS = ["EMPILHADO", "FORA", "TUDO_ZERO", "SO_ZERO", "AGLOMERADO",
            "NO_ESPACO", "DENSO", "DESORDEM"]


def comeco_de_palavra(t, c):
    """A coluna c cai no primeiro caractere de uma palavra?"""
    if c < 0 or c >= len(t):
        return False
    if not t[c].isalnum():
        return False
    return c == 0 or not t[c - 1].isalnum()


def melhor_deslocamento(t, cols, alcance=3):
    """De quanto essa linha teria que andar para acertar mais começos de palavra.

    Devolve (deslocamento, acertos_com_ele, acertos_como_está) ou None quando a
    linha não decide nada (nenhum deslocamento acerta mais que o atual)."""
    agora = sum(1 for c in cols if comeco_de_palavra(t, c))
    melhor_d, melhor_n = 0, agora
    for d in range(-alcance, alcance + 1):
        if d == 0:
            continue
        n = sum(1 for c in cols if comeco_de_palavra(t, c + d))
        if n > melhor_n or (n == melhor_n and melhor_d and abs(d) < abs(melhor_d)):
            melhor_d, melhor_n = d, n
    return melhor_d, melhor_n, agora


def auditar_linha(linha):
    """{defeito: quantos acordes} + medidas da linha."""
    t = (linha.get("t") or "").rstrip()
    pares = linha.get("a") or []
    if not pares:
        return None
    cols = [p[0] for p in pares]
    L = len(t)
    palavras = [w for w in re.split(r"\s+", t) if w]
    d = Counter()

    vistos = Counter(cols)
    d["EMPILHADO"] = sum(n - 1 for n in vistos.values() if n > 1)
    d["FORA"] = sum(1 for c in cols if c >= L)
    if len(cols) >= 2 and all(c == 0 for c in cols):
        d["TUDO_ZERO"] = len(cols)
    if len(cols) == 1 and cols[0] == 0:
        d["SO_ZERO"] = 1
    if len(cols) >= 3 and L >= 20 and max(cols) <= L * 0.2:
        d["AGLOMERADO"] = len(cols)
    d["NO_ESPACO"] = sum(1 for c in cols if 0 <= c < L and t[c].isspace())
    if palavras and len(cols) > len(palavras):
        d["DENSO"] = len(cols) - len(palavras)
    if cols != sorted(cols):
        d["DESORDEM"] = sum(1 for i in range(1, len(cols)) if cols[i] < cols[i - 1])

    desl = melhor_deslocamento(t, cols)
    return {"n": len(cols), "L": L, "d": d, "desl": desl,
            "inicio": sum(1 for c in cols if comeco_de_palavra(t, c))}


def auditar(dados):
    por_pdf = defaultdict(lambda: {"louvores": 0, "linhas": 0, "acordes": 0,
                                   "linhas_ruins": 0, "d": Counter(),
                                   "inicio": 0, "desl": Counter(),
                                   "acordes_desl": 0})
    por_louvor = {}
    for chave, reg in dados.items():
        pdf = apelido(reg.get("pdf"))
        s = por_pdf[pdf]
        s["louvores"] += 1
        d_l, n_ac, n_li, ruins, ini = Counter(), 0, 0, 0, 0
        desl_l = Counter()
        for linha in reg.get("linhas", []):
            m = auditar_linha(linha)
            if not m:
                continue
            n_li += 1
            n_ac += m["n"]
            ini += m["inicio"]
            d_l.update(m["d"])
            if sum(m["d"].values()):
                ruins += 1
            dd, nn, agora = m["desl"]
            if dd:
                desl_l[dd] += m["n"]
        s["linhas"] += n_li
        s["acordes"] += n_ac
        s["linhas_ruins"] += ruins
        s["inicio"] += ini
        s["d"].update(d_l)
        s["desl"].update(desl_l)
        s["acordes_desl"] += sum(desl_l.values())
        if n_ac:
            por_louvor[chave] = {"pdf": pdf, "acordes": n_ac, "linhas": n_li,
                                 "ruins": ruins, "d": d_l, "inicio": ini,
                                 "desl": sum(desl_l.values()),
                                 "ok": bool(reg.get("ok"))}
    return por_pdf, por_louvor


def pct(a, b):
    return (100.0 * a / b) if b else 0.0


def nota(v):
    """Quanto dessa cifra está posicionalmente suspeita, de 0 a 1."""
    graves = (v["d"]["EMPILHADO"] + v["d"]["FORA"] + v["d"]["TUDO_ZERO"]
              + v["d"]["DESORDEM"] + v["d"]["DENSO"])
    return min(1.0, graves / float(v["acordes"]))


def main():
    dados = carregar()
    por_pdf, por_louvor = auditar(dados)

    if "--exemplos" in sys.argv:
        alvo = sys.argv[sys.argv.index("--exemplos") + 1].upper()
        for chave, reg in dados.items():
            if alvo not in chave.upper():
                continue
            print("=" * 70)
            print(chave, "|", reg.get("pdf"), "| tom", reg.get("tom"))
            for linha in reg.get("linhas", []):
                m = auditar_linha(linha)
                if not m or not sum(m["d"].values()):
                    continue
                t = linha["t"]
                risca = [" "] * (max([c for c, _ in linha["a"]] + [len(t)]) + 8)
                for c, nm in linha["a"]:
                    for i, ch in enumerate(nm):
                        if c + i < len(risca):
                            risca[c + i] = ch
                print("   ", "".join(risca).rstrip())
                print("   ", t)
                print("     ->", ", ".join("%s x%d" % (k, n)
                                           for k, n in m["d"].items() if n))
        return

    print("=" * 78)
    print("POSIÇÃO DO ACORDE — %d louvores, %d linhas com acorde, %d acordes"
          % (len(por_louvor),
             sum(s["linhas"] for s in por_pdf.values()),
             sum(s["acordes"] for s in por_pdf.values())))
    print("=" * 78)

    ordem = sorted(por_pdf, key=lambda k: -por_pdf[k]["acordes"])
    larg = max(len(k) for k in ordem)
    cab = "%-*s %7s %7s %8s %8s" % (larg, "livro", "louvor", "acorde", "linha", "ac.ruim")
    print("\n" + cab)
    for k in ordem:
        s = por_pdf[k]
        ruins_ac = sum(s["d"][x] for x in DEFEITOS)
        print("%-*s %7d %7d %7.1f%% %7.1f%%"
              % (larg, k, s["louvores"], s["acordes"],
                 pct(s["linhas_ruins"], s["linhas"]), pct(ruins_ac, s["acordes"])))

    print("\nDEFEITO A DEFEITO — %% dos acordes daquele livro")
    print("%-*s %s" % (larg, "livro", " ".join("%10s" % d[:10] for d in DEFEITOS)))
    for k in ordem:
        s = por_pdf[k]
        print("%-*s %s" % (larg, k, " ".join("%9.1f%%" % pct(s["d"][d], s["acordes"])
                                             for d in DEFEITOS)))
    print("\n(números absolutos)")
    for k in ordem:
        s = por_pdf[k]
        print("%-*s %s" % (larg, k, " ".join("%10d" % s["d"][d] for d in DEFEITOS)))

    print("\nCAI NO COMEÇO DE PALAVRA (quanto maior, mais alinhado)")
    for k in ordem:
        s = por_pdf[k]
        print("%-*s %6.1f%%  |  acordes que melhorariam deslocando a linha: %5.1f%%"
              % (larg, k, pct(s["inicio"], s["acordes"]),
                 pct(s["acordes_desl"], s["acordes"])))

    print("\nPARA QUE LADO ESTÁ TORTO (deslocamento que mais acerta, em acordes)")
    for k in ordem:
        s = por_pdf[k]
        tot = max(1, sum(s["desl"].values()))
        linha = "  ".join("%+d:%4.1f%%" % (d, pct(s["desl"].get(d, 0), tot))
                          for d in range(-3, 4) if d)
        print("%-*s %s" % (larg, k, linha))

    n = 25
    if "--piores" in sys.argv:
        n = int(sys.argv[sys.argv.index("--piores") + 1])
    piores = sorted(por_louvor.items(),
                    key=lambda kv: (-nota(kv[1]), -kv[1]["acordes"]))[:n]
    print("\nOS %d PIORES (fração dos acordes com defeito grave)" % n)
    print("%-46s %5s %5s %6s  %s" % ("louvor", "acord", "ruim", "nota", "livro"))
    for chave, v in piores:
        p = chave.split("|")
        rot = ("%s %s" % (p[0], p[1]))[:46]
        graves = ", ".join("%s x%d" % (d, v["d"][d]) for d in DEFEITOS if v["d"][d])
        print("%-46s %5d %5d %5.0f%%  %s" % (rot, v["acordes"], v["ruins"],
                                             nota(v) * 100, v["pdf"]))
        print("      %s" % graves)

    # ---- o defeito dominante, medido à parte -------------------------------
    # consertar_pela_letra() troca a letra do PDF pela do app e depois grampeia
    # a coluna com min(len(nova), c). O app quebra a letra em linhas curtas de
    # projeção; o PDF traz a frase inteira numa linha só. Todo acorde que caía
    # depois do fim da linha curta é grampeado EXATAMENTE no último caractere —
    # todos no mesmo lugar, um em cima do outro.
    print("\nGRAMPEADOS NO FIM DA LINHA (col == tamanho da letra)")
    tot_ac = tot_fim = tot_emp = tot_empfim = 0
    linhas_fim = Counter()
    louv_fim = Counter()
    for chave, reg in dados.items():
        pdf = apelido(reg.get("pdf"))
        tem = 0
        for linha in reg.get("linhas", []):
            pares = linha.get("a") or []
            if not pares:
                continue
            t = (linha.get("t") or "").rstrip()
            L = len(t)
            cols = [c for c, _ in pares]
            tot_ac += len(cols)
            nofim = sum(1 for c in cols if c >= L)
            tot_fim += nofim
            for c, k in Counter(cols).items():
                if k > 1:
                    tot_emp += k - 1
                    if c >= L:
                        tot_empfim += k - 1
            if nofim >= 2:
                linhas_fim[pdf] += 1
            if nofim:
                tem += nofim
        if tem:
            louv_fim[pdf] += 1
    print("   acordes grampeados no último caractere : %d de %d (%.1f%%)"
          % (tot_fim, tot_ac, pct(tot_fim, tot_ac)))
    print("   dos %d acordes empilhados, no fim      : %d (%.0f%%)"
          % (tot_emp, tot_empfim, pct(tot_empfim, tot_emp)))
    print("   acordes ALÉM do fim (col > tamanho)    : 0  <- o grampo esconde")
    for k in ordem:
        print("   %-*s louvores atingidos %4d de %4d, linhas com 2+ no fim: %d"
              % (larg, k, louv_fim[k], por_pdf[k]["louvores"], linhas_fim[k]))

    limpos = sum(1 for v in por_louvor.values() if not sum(v["d"].values()))
    print("\nlouvores sem NENHUM defeito de posição: %d de %d (%.1f%%)"
          % (limpos, len(por_louvor), pct(limpos, len(por_louvor))))
    for k in ordem:
        lim = sum(1 for v in por_louvor.values()
                  if v["pdf"] == k and not sum(v["d"].values()))
        tot = sum(1 for v in por_louvor.values() if v["pdf"] == k)
        print("   %-*s %4d de %4d (%.1f%%)" % (larg, k, lim, tot, pct(lim, tot)))

    com_ok = [v for v in por_louvor.values() if v["ok"]]
    sem_ok = [v for v in por_louvor.values() if not v["ok"]]
    for rot, grupo in (("costurados com a letra do app", com_ok),
                       ("com a letra crua do PDF", sem_ok)):
        if not grupo:
            continue
        ac = sum(v["acordes"] for v in grupo)
        ru = sum(sum(v["d"][d] for d in DEFEITOS) for v in grupo)
        ini = sum(v["inicio"] for v in grupo)
        print("%-32s %4d louvores, %6d acordes, %5.1f%% ruins, %4.1f%% no começo"
              % (rot, len(grupo), ac, pct(ru, ac), pct(ini, ac)))


if __name__ == "__main__":
    main()
