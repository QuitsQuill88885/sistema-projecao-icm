# -*- coding: utf-8 -*-
"""Servidor de TESTE do app — só para conferir a tela no navegador.

Não é o Sistema: não abre janela, não converte slide, não grava nada. Serve os
arquivos da pasta do app e responde o mínimo de /api/ que o index.html procura
no arranque, para que a página suba sem erro e a gente possa medir a lista de
sugestões com o código de verdade rodando.

O histórico pode vir de um arquivo qualquer (1º argumento), assim dá para
experimentar "e se a igreja tivesse cantado tal louvor 30 vezes" sem encostar no
historico.json do usuário.

Uso:  python servir_teste.py [historico_de_teste.json] [porta]
"""
import http.server, io, json, os, sys

AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_HIST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.environ.get("APPDATA", "."), "Sistema Projecao", "historico.json")
PORTA = int(sys.argv[2]) if len(sys.argv) > 2 else 8799


def historico():
    try:
        return json.loads(io.open(ARQ_HIST, encoding="utf-8").read())
    except Exception:
        return []


class Mao(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=AQUI, **k)

    def _json(self, d):
        b = json.dumps(d, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/api/historico"):
            return self._json({"ok": True, "registros": historico()})
        if self.path.startswith("/api/"):
            return self._json({"ok": True, "indice": {}, "violao": {}, "comandos": []})
        return super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        return self._json({"ok": True})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("servindo %s em http://localhost:%d/index.html" % (AQUI, PORTA))
    print("historico de teste: %s (%d registros)" % (ARQ_HIST, len(historico())))
    http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), Mao).serve_forever()
