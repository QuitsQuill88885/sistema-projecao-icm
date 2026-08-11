# -*- coding: utf-8 -*-
"""Descola os marcadores que vieram grudados na letra dos louvores.

O DEFEITO
---------
O trecho amarelo do slide (o "(BIS)", o "(2X)", o eco "(SE DEUS QUISER)") é
delimitado por um caractere invisível, o \\x01. Em 1.307 linhas do cadastro
ele veio COLADO na palavra vizinha:

    \\x01CORO:\\x01SE DEUS QUISER \\x01(SE DEUS QUISER)\\x01ME

No telão isso vira "CORO:SE DEUS QUISER (SE DEUS QUISER)ME" — sem respiro,
palavra emendada na outra. Foi o que o Samuel viu na foto do "SE DEUS QUISER
ME ABENÇOAR" (11/08/2026).

O QUE ELE FAZ
-------------
1. Reconstrói a linha pelos pedaços entre \\x01 e devolve o espaço nas
   fronteiras — SEMPRE do lado de fora do amarelo, para não colorir espaço;
2. descola também o que está grudado no texto comum: ")" seguido de letra e
   letra seguida de "(";
3. "CORO", "FINAL" e "BIS" no começo da linha (com ou sem dois-pontos, com ou
   sem amarelo) saem do texto e viram o RÓTULO do slide, que é o lugar deles;
4. recolhe espaço repetido.

Conserta o dado uma única vez, em vez de gastar processador em todo slide
projetado — a máquina da igreja é fraca e não pode pagar por isso.

    python ferramentas/consertar_marcadores.py
"""
import io
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, "dados", "louvores.js")

MARCA = "\x01"
ROTULOS = ("CORO", "FINAL", "BIS")
FECHA_COLADO = re.compile(r"\)([A-ZÀ-Ú0-9])")
ABRE_COLADO = re.compile(r"([A-ZÀ-Ú0-9,.;!?])\(")
MINUSCULA_SOLTA = re.compile(r"content")
# "CORO", "CORO:", "CORO (2X)", com ou sem o amarelo em volta
SO_ROTULO = re.compile(r"^[\x01\s]*(%s)[\x01\s]*:?[\x01\s]*$" % "|".join(ROTULOS))
COMECA_ROTULO = re.compile(r"^[\x01\s]*(%s)[\x01\s]*:[\x01\s]*(.+)$" % "|".join(ROTULOS))


def descolar(linha):
    """Devolve o espaço nas fronteiras do trecho amarelo.

    Os pedaços de índice ímpar são os amarelos. O espaço entra sempre no
    pedaço comum (o de fora), nunca dentro do amarelo."""
    if MARCA not in linha:
        return linha
    p = linha.split(MARCA)
    for i in range(len(p) - 1):
        a, b = p[i], p[i + 1]
        if not a or not b:
            continue
        if a[-1].isspace() or b[0].isspace():
            continue
        if i % 2 == 0:            # comum -> amarelo: o espaço fica no comum
            p[i] = a + " "
        else:                     # amarelo -> comum: o espaço fica no comum
            p[i + 1] = " " + b
    return MARCA.join(p)


def limpar(linha):
    # PRIMEIRO junta os amarelos vizinhos ("...JESUS)\x01\x01VARÕES\x01"):
    # se isso ficasse para o fim, o descolar não veria a fronteira e as duas
    # palavras acabariam emendadas — ")VARÕES" — que é pior do que estava.
    nova = linha
    while MARCA + MARCA in nova:
        nova = nova.replace(MARCA + MARCA, "")
    nova = descolar(nova)
    nova = FECHA_COLADO.sub(r") \1", nova)
    nova = ABRE_COLADO.sub(r"\1 (", nova)
    # "contentE" no meio de uma linha toda em maiúscula é lixo da extração,
    # não palavra: 20 louvores traziam CONTENTE assim, escrito pela metade
    if MINUSCULA_SOLTA.search(nova):
        nova = nova.replace("content", "CONTENT")
    nova = re.sub(r"[ \t]{2,}", " ", nova).strip()
    return nova


def consertar(dados):
    mexidas = rotulos = removidas = 0
    for louvor in dados:
        for slide in louvor.get("slides") or []:
            linhas = slide.get("linhas") or []
            saida = []
            for linha in linhas:
                nova = limpar(linha)

                m = SO_ROTULO.match(nova)
                if m:                                  # a linha É só o rótulo
                    if not (slide.get("label") or "").strip():
                        slide["label"] = m.group(1)
                        rotulos += 1
                    removidas += 1
                    continue

                m = COMECA_ROTULO.match(nova)
                if m:                                  # "CORO: a letra vem aqui"
                    if not (slide.get("label") or "").strip():
                        slide["label"] = m.group(1)
                        rotulos += 1
                    nova = limpar(m.group(2))

                if nova != linha:
                    mexidas += 1
                saida.append(nova)
            slide["linhas"] = [l for l in saida if l.strip()]
    return mexidas, rotulos, removidas


def main():
    fonte = io.open(ARQ, encoding="utf-8").read()
    m = re.search(r"^(.*?=\s*)(\[.*\])(\s*;?\s*)$", fonte, re.S)
    if not m:
        print("não reconheci o formato de dados/louvores.js")
        return 1
    dados = json.loads(m.group(2))

    mexidas, rotulos, removidas = consertar(dados)
    if not (mexidas or rotulos or removidas):
        print("nada a consertar — as letras já estão limpas")
        return 0

    novo = m.group(1) + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + m.group(3)
    with io.open(ARQ, "w", encoding="utf-8") as f:
        f.write(novo)
    print("linhas descoladas: %d | rótulos para o lugar certo: %d | linhas de rótulo removidas: %d"
          % (mexidas, rotulos, removidas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
