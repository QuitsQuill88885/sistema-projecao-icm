# -*- coding: utf-8 -*-
"""Ajusta o splash.png da tela de carregamento.

Parte do splash original (preserva logo, degrade e o titulo exatos) e faz
duas correcoes:

  1. apaga o trecho dourado da barra, deixando so o trilho vazio. O dourado
     passa a ser escrito pelo proprio programa, caractere a caractere,
     conforme as etapas reais do carregamento terminam (marcar_splash em
     sistema.py). Barra pintada na imagem fica parada e parece travada.
  2. reescreve o subtitulo com acento: "Projecao" -> "Projeção".

Rodar: python gerar_splash.py    (usa splash_antigo_backup.png como base)
"""
import os
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, "splash_antigo_backup.png")
DESTINO = os.path.join(AQUI, "splash.png")

SUAVE = (150, 172, 205)
TRILHO = (38, 57, 88)

# geometria da barra — precisa bater com o text_pos dos .spec
BARRA_X, BARRA_Y, BARRA_L, BARRA_ALT = 117, 220, 186, 7
FAIXA_SUB = (100, 190, 320, 214)      # onde mora o subtitulo


def fonte(nomes, tam):
    for n in nomes:
        try:
            return ImageFont.truetype(n, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def cor_fundo(im, y):
    """Cor do degrade naquela altura, colhida na margem (longe de tudo)."""
    return im.getpixel((4, y))


def main():
    im = Image.open(BASE).convert("RGB")
    d = ImageDraw.Draw(im)
    L = im.width

    # 1. trilho limpo no lugar da barra dourada
    for y in range(BARRA_Y - 2, BARRA_Y + BARRA_ALT + 2):
        d.line([(0, y), (L, y)], fill=cor_fundo(im, y))
    d.rounded_rectangle(
        [BARRA_X, BARRA_Y, BARRA_X + BARRA_L, BARRA_Y + BARRA_ALT],
        radius=BARRA_ALT // 2, fill=TRILHO)

    # 2. subtitulo com acento
    x0, y0, x1, y1 = FAIXA_SUB
    for y in range(y0, y1):
        d.line([(x0, y), (x1, y)], fill=cor_fundo(im, y))
    d.text((L // 2, (y0 + y1) // 2), "Projeção da igreja",
           font=fonte(["segoeui.ttf", "arial.ttf"], 14), fill=SUAVE, anchor="mm")

    im.save(DESTINO)
    print("splash gravado:", DESTINO, im.size)


if __name__ == "__main__":
    main()
