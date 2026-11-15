# -*- coding: utf-8 -*-
"""A REDE do Sistema Nativo (03/11/2026): o celular e os aparelhos da mesma rede.

Reaproveita o servidor que já roda no culto (sistema.py da 3.0.12: rotas /api/*, o controle.html do celular, o
anúncio UDP "existe um Sistema aqui" que os outros aparelhos usam para achar o computador). Nada de navegador no
PC: o controle.html abre no navegador DO CELULAR, que é outro aparelho.
A diferença: a fila de ordens do celular é lida direto na memória (sem a tela pedir /api/comandos a cada 600 ms),
e o estado/tela do telão também é gravado direto.
"""
import os, socketserver, sys, threading, time
import cerebro

sys.path.insert(0, cerebro.APP)
import sistema as S          # só constantes e funções no import (conferido 03/11): não abre janela nem servidor

# 08/11 (o Vaio): lá o servidor é o da pasta da 3.0.12, a da igreja, que não se mexe. O pacote do Linux traz o
# controle.html da 3.0.13 (os consertos do culto de 08/11) em <programa>/web e os dados em <programa>/dados: esses
# vencem. No Windows essas pastas não existem e nada muda.
_PROG = os.path.dirname(os.path.abspath(__file__))
_MEUS = {"/controle.html": os.path.join(_PROG, "web", "controle.html")}


# e a CIFRA do celular (/api/musico, /api/cifra): o banco conferido e as ocultas do pacote, os mesmos do painel
# (cerebro.ARQ_ACORDES). Sem o pacote (Windows), o servidor lê a pasta do usuário como sempre.
if not getattr(sys, "frozen", False) and os.path.isfile(os.path.join(_PROG, "cifras", "acordes.json")):
    _pasta_usuario = S.pasta_usuario
    S.pasta_usuario = lambda nome: os.path.join(_PROG, "cifras") if nome == "cifras" else _pasta_usuario(nome)
if not getattr(sys, "frozen", False) and os.path.isfile(os.path.join(_PROG, "dados", "cifras_ocultas.json")):
    def _ocultas():
        import json
        with open(os.path.join(_PROG, "dados", "cifras_ocultas.json"), encoding="utf-8") as f:
            return set(json.load(f))
    S.cifras_ocultas = _ocultas


class _Handler(S.Handler):
    def translate_path(self, path):
        from urllib.parse import unquote
        limpo = unquote(path.split("?", 1)[0].split("#", 1)[0])
        meu = _MEUS.get(limpo)
        if meu is None and limpo.startswith("/dados/") and "/" not in limpo[7:] and ".." not in limpo:
            meu = os.path.join(_PROG, "dados", limpo[7:])
        if meu and not getattr(sys, "frozen", False) and os.path.isfile(meu):
            return meu
        return super().translate_path(path)


def ligar():
    """Sobe o servidor na 8765 (ou na próxima livre) e o anúncio na rede. Devolve (porta, endereço para o celular)."""
    if os.environ.get("NATIVO_APOIOS"):          # testes: o par lembrado (o Vaio) vai para outro arquivo, nunca o de verdade
        S.ARQ_APOIOS = os.environ["NATIVO_APOIOS"]
    porta = S.PORTA
    while not S.porta_livre(porta) and porta < S.PORTA + 20:
        porta += 1
    socketserver.TCPServer.allow_reuse_address = True
    # testes: NATIVO_SO_LOCAL=1 escuta só dentro desta máquina (o Windows não abre o aviso do Firewall na tela dele)
    so_local = bool(os.environ.get("NATIVO_SO_LOCAL"))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1" if so_local else S.ENDERECO_REDE, porta), _Handler)
    threading.Thread(target=srv.serve_forever, name="servidor", daemon=True).start()
    if not so_local:
        # 13/11: o grito leva o NOME AMIGÁVEL deste computador (o nome.txt do Vaio = "Vaio"), que é o que o cartão
        # "Outro Sistema nesta rede" do outro lado mostra; sem ele, o nome da máquina ("samuel-VPCYB35AB")
        threading.Thread(target=_anunciar, args=(porta,), name="anuncio-udp", daemon=True).start()
    S.PORTAS["comum"] = porta
    try:
        ip = "127.0.0.1" if so_local else S.endereco_local()
    except Exception:
        ip = "127.0.0.1"
    return porta, "http://%s:%d/controle.html" % (ip, porta)


def _anunciar(porta):
    """O anunciar_na_rede do sistema.py (a cada 2 s, UDP 8766), com o nome amigável; a mesma mensagem e os mesmos alvos."""
    import json, socket
    try:
        import seguir
        nome = seguir.meu_nome()
    except Exception:
        nome = socket.gethostname()
    msg = json.dumps({"sistema": "icm-projecao", "porta": porta, "nome": nome, "versao": getattr(S, "VERSAO", "")}).encode("utf-8")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except Exception:
        return
    while True:
        alvos = {"255.255.255.255"}
        try:
            for inf in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = inf[4][0]
                if not ip.startswith(("127.", "169.254.")):
                    alvos.add(ip.rsplit(".", 1)[0] + ".255")
        except Exception:
            pass
        for a in alvos:
            try: s.sendto(msg, (a, S.PORTA_ANUNCIO))
            except Exception: pass
        S.ANUNCIAR_JA.wait(2); S.ANUNCIAR_JA.clear()


def comandos():
    with S.TRAVA:
        fila, S.COMANDOS[:] = list(S.COMANDOS), []
    return fila


def publicar_tela(t):
    """A prévia do celular é o projecao.html de lá: o fundo e a tela das CIAS vão como endereço do servidor."""
    w = dict(t)
    if w.get("fundo"):
        w["fundo"] = os.path.relpath(w["fundo"], cerebro.APP).replace(os.sep, "/")
    if w.get("modo") == "apres":       # apresentação: o mesmo "slide" da 3.0.12 (src, mov e passo pelo endereço do servidor)
        w = {"modo": "slide", "src": t.get("url", ""), "transicao": t.get("fade", 700) > 0, "fade": t.get("fade", 700)}
        if t.get("movUrl"):
            w["mov"], w["passo"] = t["movUrl"], t.get("passo", 0)
    elif w.get("modo") == "slide":
        w = {"modo": "slide", "src": "/animacoes/" + os.path.basename(t.get("webp") or t.get("arquivo") or ""),
             "transicao": True, "fade": t.get("fade", 700)}
    else:
        w["transicao"] = True
    with S.TRAVA:
        S.TELA["payload"] = w
        S.TELA["n"] += 1


def publicar_estado(d):
    with S.TRAVA:
        S.ESTADO.update(d)
        S.ESTADO["ts"] = time.time()
