# -*- coding: utf-8 -*-
"""Grava o textos.json de uma apresentação que JÁ está no Sistema (a busca "nº ou palavra" da tela nova).

Nova tela de apresentação, 12/10/2026. Na importação o Sistema grava sozinho o texto das formas do pptx e o
texto do PDF (sistema.py: gravar_textos). Mas nas duas apresentações de fábrica da Evangelização quase todo o
texto está DENTRO das imagens (a fala da filha de Jairo, os títulos), e o pptx não tem nada para ler.
Então, uma vez, aqui na máquina: o texto das formas do pptx (quando houver) + o OCR local de cada tela.

uso: python textos_das_telas.py "<pasta da apresentação>" ["<pptx de origem>"]
O OCR é o RapidOCR (local, zero internet). Precisa do python que tem rapidocr_onnxruntime.
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))


def ocr_das_telas(telas):
    import numpy as np
    from PIL import Image
    from rapidocr_onnxruntime import RapidOCR
    motor = RapidOCR()
    saida = []
    for p in telas:
        im = Image.open(p)
        im.seek(0)                                   # webp animado: o primeiro quadro basta
        res, _ = motor(np.asarray(im.convert("RGB")))
        linhas = [t for _, t, conf in (res or []) if float(conf) >= 0.6 and len(t.strip()) > 1]
        saida.append("\n".join(linhas))
        print(os.path.basename(p), "|", " / ".join(linhas)[:110])
    return saida


def main():
    import sistema
    pasta = sys.argv[1]
    telas = sistema._telas_da_pasta(pasta)
    n = len(telas)
    forma = [""] * n
    if len(sys.argv) > 2:
        forma = sistema._alinha_notas(sistema.textos_do_pptx(sys.argv[2]), n)
    ocr = ocr_das_telas(telas)
    textos = [("\n".join(x for x in (a, b) if x)).strip() for a, b in zip(forma, ocr)]
    with open(os.path.join(pasta, sistema.ARQ_TEXTOS), "w", encoding="utf-8") as f:
        json.dump(textos, f, ensure_ascii=False, indent=0)
    print("gravado:", n, "telas,", sum(1 for t in textos if t), "com texto")


if __name__ == "__main__":
    main()
