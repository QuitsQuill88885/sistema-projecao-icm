# -*- coding: utf-8 -*-
"""O 'b' comido: a tonalidade que perde o bemol no OCR.

No cruzamento com a melodia, 5 das 16 divergencias sao de UM SEMITOM, e a
cifra esta sempre ACIMA. Isso tem cara de OCR: "Ab" vira "A", "Eb" vira "E", e
o louvor inteiro sobe meio tom.

Aqui a hipotese e' testada no acervo todo, sem depender da melodia: conta as
cifras cujo rotulo e' uma nota NATURAL mas cujos acordes tocam no bemol logo
abaixo. E, pra isso nao ser so' ruido do juiz, mede o CONTROLE -- o desvio pro
lado contrario (rotulo natural, acordes um semitom ACIMA), que nenhum OCR
explica. Se os dois lados derem igual, e' ruido; se um lado for muito maior,
e' o bemol comido.

O mesmo teste e' feito com o "m" comido (rotulo maior, acordes menores).

    set PYTHONIOENCODING=utf-8
    python conferir_tom_bemol.py
"""
from __future__ import unicode_literals

import io
import json
import os
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conferir_tom import CIFRAS, agrupar, escaneado, ler_tom, nfc, nome  # noqa
from conferir_tom_arbitro import (FOLGA_MIN, MIN_ACORDES, acordes_da_cifra,  # noqa
                                  deduzir_acordes)

AQUI = os.path.dirname(os.path.abspath(__file__))


def main():
    acordes = json.load(io.open(os.path.join(CIFRAS, "acordes.json"), encoding="utf-8"))
    louvores = agrupar(acordes)

    bemol_comido, subiu_sem_motivo, m_comido, m_sobrando = [], [], [], []
    julgadas = 0
    for (_tn, _h), Lv in louvores.items():
        reg = Lv["reg"]
        rot_txt = reg.get("tom")
        rc = ler_tom(rot_txt)
        if not rc:
            continue
        acs = acordes_da_cifra(reg)
        if len(acs) < MIN_ACORDES:
            continue
        d, folga = deduzir_acordes(acs)
        if d is None or folga < FOLGA_MIN:
            continue
        julgadas += 1
        pc_r, men_r = rc
        pc_d, men_d = d
        natural = "#" not in nfc(rot_txt) and "b" not in nfc(rot_txt)
        item = (Lv["titulo"], rot_txt, nome(d), nfc(reg.get("pdf")), len(acs))
        # compara a FAMILIA do tom (o relativo maior), senao Eb e o seu
        # relativo Cm contam como tons diferentes e o teste perde os casos
        fam_r = (pc_r + 3) % 12 if men_r else pc_r
        fam_d = (pc_d + 3) % 12 if men_d else pc_d
        if natural:
            if fam_d == (fam_r - 1) % 12:
                bemol_comido.append(item)        # rotulo A, acordes em Ab
            elif fam_d == (fam_r + 1) % 12:
                subiu_sem_motivo.append(item)    # controle: nada explica
        if pc_r == pc_d:
            if not men_r and men_d:
                m_comido.append(item)            # rotulo A, acordes em Am
            elif men_r and not men_d:
                m_sobrando.append(item)          # rotulo Am, acordes em A

    L_ = "-" * 74
    print("=" * 74)
    print("O BEMOL COMIDO E O 'm' COMIDO -- teste com controle")
    print("=" * 74)
    print("cifras julgadas (tom + %d acordes + juiz decidido): %d"
          % (MIN_ACORDES, julgadas))
    print(L_)

    def bloco(titulo, achados, controle, nome_controle):
        a, c = len(achados), len(controle)
        print("%s" % titulo)
        print("   achados : %3d  (%.1f%% das julgadas)" % (a, 100.0 * a / max(1, julgadas)))
        print("   controle: %3d  (%s)" % (c, nome_controle))
        if c:
            print("   excesso sobre o controle: %d  (%.1fx)" % (a - c, a / float(c)))
        else:
            print("   excesso sobre o controle: %d  (controle zerado)" % a)
        esc = sum(1 for x in achados if escaneado(x[3]))
        print("   do PDF escaneado: %d de %d (%.0f%%)"
              % (esc, a, 100.0 * esc / max(1, a)))
        for x in sorted(achados)[:12]:
            print("      %-38s rotulo %-5s acordes %-5s %s"
                  % (x[0][:38], x[1], x[2], "ESCANEADO" if escaneado(x[3]) else "texto"))
        if a > 12:
            print("      ... mais %d" % (a - 12))
        print(L_)

    bloco("BEMOL COMIDO  (rotulo natural, acordes um semitom ABAIXO)",
          bemol_comido, subiu_sem_motivo,
          "rotulo natural, acordes um semitom ACIMA -- nada explicaria")
    bloco("'m' COMIDO  (rotulo maior, acordes na menor de mesma raiz)",
          m_comido, m_sobrando,
          "rotulo menor, acordes na maior -- o erro contrario")

    saida = os.path.join(AQUI, "tom_bemol_comido.json")
    with io.open(saida, "w", encoding="utf-8") as f:
        f.write(json.dumps(
            {"bemol_comido": [{"titulo": t, "rotulo": r, "acordes": a, "pdf": p,
                               "n": n, "escaneado": escaneado(p)}
                              for t, r, a, p, n in sorted(bemol_comido)],
             "m_comido": [{"titulo": t, "rotulo": r, "acordes": a, "pdf": p,
                           "n": n, "escaneado": escaneado(p)}
                          for t, r, a, p, n in sorted(m_comido)]},
            ensure_ascii=False, indent=1))
    print("gravado: %s" % saida)


if __name__ == "__main__":
    main()
