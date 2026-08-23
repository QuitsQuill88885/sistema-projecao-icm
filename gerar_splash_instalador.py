# -*- coding: utf-8 -*-
"""Refaz o splash_instalador.png (a telinha que aparece enquanto o instalador
abre).

POR QUE FOI REFEITO
-------------------
O Samuel viu o instalador rodando na igreja e disse que "o símbolo do sistema
pareceu meio cortado". Estava mesmo: o anel vinho do logo encostava na borda de
cima do desenho, e um selo verde de download entrava POR CIMA do anel, cortando
ele de novo do outro lado. Três elementos disputando o mesmo espaço.

Agora o logo é colado a partir do `sistema.ico`/`sistema.png` de verdade (o
mesmo do programa), inteiro, com folga em volta, e o selo verde saiu: quem diz
que está instalando é o texto, que já está logo abaixo.

O fundo (degradê azul) é colhido do splash do programa, para as duas telas
continuarem irmãs.

Rodar:  python gerar_splash_instalador.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(AQUI, "sistema.png")
BASE_FUNDO = os.path.join(AQUI, "splash.png")       # só para colher o degradê
DESTINO = os.path.join(AQUI, "splash_instalador.png")

L, A = 420, 260
BRANCO = (255, 255, 255)
SUAVE = (150, 172, 205)
FRACO = (110, 132, 165)

LOGO_LADO = 96          # o logo desenhado
FOLGA_TOPO = 26         # respiro acima do logo — era isto que faltava


def fonte(nomes, tam):
    for n in nomes:
        try:
            return ImageFont.truetype(n, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def fundo():
    """Degradê igual ao do splash do programa, para as telas serem irmãs.

    Colhe a cor na margem esquerda (longe do logo e do texto) linha a linha.
    Se o arquivo não existir, cai num degradê equivalente."""
    if os.path.exists(BASE_FUNDO):
        b = Image.open(BASE_FUNDO).convert("RGB")
        im = Image.new("RGB", (L, A))
        d = ImageDraw.Draw(im)
        for y in range(A):
            cor = b.getpixel((4, min(y, b.height - 1)))
            d.line([(0, y), (L, y)], fill=cor)
        return im
    im = Image.new("RGB", (L, A))
    d = ImageDraw.Draw(im)
    for y in range(A):
        t = y / float(A - 1)
        d.line([(0, y), (L, y)],
               fill=(int(16 + 9 * t), int(31 + 14 * t), int(58 + 22 * t)))
    return im


def main():
    im = fundo()

    # o logo INTEIRO, com folga: nada de anel encostando na borda
    logo = Image.open(LOGO).convert("RGBA").resize((LOGO_LADO, LOGO_LADO),
                                                   Image.LANCZOS)
    im.paste(logo, ((L - LOGO_LADO) // 2, FOLGA_TOPO), logo)

    d = ImageDraw.Draw(im)
    y = FOLGA_TOPO + LOGO_LADO + 22
    d.text((L // 2, y), "Sistema",
           font=fonte(["segoeuib.ttf", "arialbd.ttf"], 30), fill=BRANCO,
           anchor="mm")
    d.text((L // 2, y + 32), "Instalando…",
           font=fonte(["segoeui.ttf", "arial.ttf"], 15), fill=SUAVE, anchor="mm")
    d.text((L // 2, y + 56), "isto leva alguns segundos",
           font=fonte(["segoeui.ttf", "arial.ttf"], 11), fill=FRACO, anchor="mm")

    im.save(DESTINO)
    print("splash do instalador gravado:", DESTINO, im.size)
    print("folga acima do logo:", FOLGA_TOPO, "px | logo:", LOGO_LADO, "px")


if __name__ == "__main__":
    main()
