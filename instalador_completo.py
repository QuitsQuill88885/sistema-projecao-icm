# -*- coding: utf-8 -*-
"""O Sistema COMPLETO num arquivo só — sem nenhum zip na frente do usuário.

Por que existe: o leigo não sabe descompactar. Então o pacote inteiro
(instalador + animações + cifras + melodias) viaja DENTRO deste executável.
Dois cliques: a telinha de carregamento aparece enquanto o carregador do
PyInstaller descompacta tudo numa pasta temporária, e daí quem assume é o
"Instalar o Sistema.exe" de sempre — que acha a pasta Conteudo do lado dele
e copia tudo sozinho, como se tivesse vindo num pendrive.

A pasta temporária é do PyInstaller (_MEIPASS): esperamos o instalador
TERMINAR antes de sair, porque na saída o carregador apaga a pasta — e o
instalador ainda está lendo dela enquanto instala.
"""
import os
import subprocess
import sys


def main():
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass
    exe = os.path.join(base, "Instalar o Sistema.exe")
    # repassa as bandeiras (--silencioso, --reabrir) para o instalador real.
    # DEVNULL nos canais: este processo não tem console, e sem um destino
    # válido o print do filho estourava com janela de erro na cara do usuário
    subprocess.run([exe] + sys.argv[1:], cwd=base,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   stdin=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
