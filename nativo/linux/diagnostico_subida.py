# -*- coding: utf-8 -*-
"""Roda NO VAIO: sobe o Nativo como o medir_no_vaio (--janela) com o faulthandler armado: se em N segundos ele não
tiver saído sozinho (NATIVO_SAIR_EM), imprime a pilha de TODAS as threads e SAI POR CONTA PRÓPRIA (nada é morto de fora).
uso: cd ~/Sistema-ICM/nativo && venv69/bin/python linux/diagnostico_subida.py 45"""
import faulthandler, os, runpy, sys
seg = int(sys.argv[1]) if len(sys.argv) > 1 else 45
faulthandler.dump_traceback_later(seg, exit=True)
os.environ.setdefault("NATIVO_SAIR_EM", str(max(10, seg - 15)))
sys.argv = ["sistema_nativo.py", "--janela"]
sys.path.insert(0, os.getcwd())
runpy.run_path("sistema_nativo.py", run_name="__main__")
