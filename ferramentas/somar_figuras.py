# -*- coding: utf-8 -*-
"""Soma a leitura pela FIGURA à tabela de sugestões que já existe.

POR QUE ASSIM, E NÃO REFAZENDO A TABELA
---------------------------------------
Refiz a tabela inteira lendo o texto pela figura e medi os 20 exemplos que o
Samuel pediu. A figura acertou onde ela É o assunto (Efésios 5 puxou "A NOIVA
É A IGREJA"), mas a minha camada de palavra saiu PIOR que a que já estava:
2 Coríntios 9:8 perdeu "MARAVILHOSA GRAÇA", Sofonias 1:4 perdeu os louvores
de Jerusalém, Filipenses 1:11 perdeu "O MEU VIVER É CRISTO".

A tabela antiga é boa no que ela faz. Então ela FICA — inteira, intocada — e a
figura entra por cima, ocupando a última cadeira:

    1º e 2º  o que a tabela antiga já dizia (a palavra do texto)
    3º       a leitura pela figura, quando ela tiver algo a dizer

Assim nenhum versículo piora, e os que falam de marido, esposa, muro, azeite,
janela e herança ganham o louvor que a igreja canta sobre aquilo.

    python ferramentas/somar_figuras.py
"""
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(AQUI, "dados")
FERR = os.path.join(AQUI, "ferramentas")
POR_VERSICULO = 3


def js(caminho):
    s = io.open(caminho, encoding="utf-8").read()
    return json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))


def main():
    antiga_caminho = os.path.join(FERR, "sugestoes_original.js")
    if not os.path.exists(antiga_caminho):
        # a primeira vez guarda o original, para nunca mais precisar dele de volta
        io.open(antiga_caminho, "w", encoding="utf-8").write(
            io.open(os.path.join(DADOS, "sugestoes.js"), encoding="utf-8").read())
        print("guardei o original em ferramentas/sugestoes_original.js")

    antiga = js(antiga_caminho)
    figuras = js(os.path.join(FERR, "sugestoes_com_figuras.js"))

    saida, mexidos, novos = {}, 0, 0
    for ch, itens in antiga.items():
        base = [list(x) for x in itens][:POR_VERSICULO]
        tem = {i for i, _p in base}
        for i, p in figuras.get(ch, []):
            if len(base) >= POR_VERSICULO and base[-1][0] in tem and len(base) == POR_VERSICULO:
                if i in tem:
                    continue
                base[-1] = [i, max(1, int(p * 0.9))]   # a figura senta na última cadeira
                mexidos += 1
                break
            if i in tem:
                continue
            base.append([i, max(1, int(p * 0.9))])
            mexidos += 1
            if len(base) >= POR_VERSICULO:
                break
        saida[ch] = base

    # versículos que a tabela antiga não alcançava e a figura alcança
    for ch, itens in figuras.items():
        if ch not in saida:
            saida[ch] = [list(x) for x in itens][:POR_VERSICULO]
            novos += 1

    txt = "window.SUGESTOES=" + json.dumps(saida, ensure_ascii=False,
                                           separators=(",", ":")) + ";"
    io.open(os.path.join(DADOS, "sugestoes.js"), "w", encoding="utf-8").write(txt)
    print("versículos: %d (%d ganharam a leitura pela figura, %d são novos)"
          % (len(saida), mexidos, novos))
    print("arquivo: dados/sugestoes.js  (%.0f KB)" % (len(txt) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
