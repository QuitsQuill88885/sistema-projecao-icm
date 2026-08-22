# -*- coding: utf-8 -*-
"""Servidor simples SO PARA TESTE, na porta 8791.

Serve a pasta do app como arquivo estatico. Nao substitui o sistema.py (que
tem a API, o telao e a porta segura) — serve para abrir paginas de prova como
ferramentas/teste_afinador.html sem subir o Sistema inteiro.
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTA = 8791


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=RAIZ, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s\n" % (fmt % args))


if __name__ == "__main__":
    print("teste em http://localhost:%d/  (raiz: %s)" % (PORTA, RAIZ))
    ThreadingHTTPServer(("127.0.0.1", PORTA), Handler).serve_forever()
