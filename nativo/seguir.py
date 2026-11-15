# -*- coding: utf-8 -*-
"""ESTE COMPUTADOR COMO TELA SECUNDÁRIA de outro Sistema (13/11/2026, pedido dele: "o computador que se tornar a tela
secundária já tem que ter esse comportamento dentro dele ... arrumar tudo na 4.0.0").

Até aqui só o Vaio fazia isto, com o "Gestos ICM" da 3.0.11 (uma página do computador principal dentro de um navegador
embutido). Agora o próprio Sistema Nativo faz, no Windows e no Linux, sem navegador:
  1. acha o computador principal: o endereço dado, o grito dele na rede (UDP 8766, o mesmo que o Vaio ouve) ou o último;
  2. se apresenta a cada segundo (GET /api/apoio?nome=...), como o retorno.html faz: o principal mostra o cartão
     "Nova tela encontrada" e lembra o par (par lembrado volta calado);
  3. acompanha o que está no ar (GET /api/estado) e repete AQUI, com os dados DESTE computador: a apresentação e o slide,
     o louvor e a estrofe, a tela de espera; o resto (Bíblia, texto, cronômetro, relógio) vem pronto do principal
     (/api/tela) e é desenhado pelo mesmo Palco;
  4. a janela do telão daqui mostra a TELA DE RETORNO (os gestos: AGORA + A SEGUIR) ou, se o operador escolher "igual ao
     telão" ou "Trocar", o próprio telão.
Não liga servidor nem grita na rede (não é um principal), não grava histórico, e o painel fica minimizado.

A rede roda numa linha de fundo e só põe recados numa fila; quem mexe no Sistema é a linha da interface (drenar)."""
import json, os, queue, socket, subprocess, sys, threading, time, unicodedata, urllib.parse, urllib.request

PORTA, PORTA_ANUNCIO = 8765, 8766
NFC = lambda s: unicodedata.normalize("NFC", str(s or ""))


def _pasta():
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Sistema Projecao")
    return os.path.expanduser("~/.config/icm-gestos")       # a mesma do Gestos ICM do Vaio (pc.txt, nome.txt)


def meu_nome():
    """O nome que aparece no principal ("Nova tela encontrada: Vaio"). O nome.txt do Gestos ICM vale; senão, o da máquina."""
    if os.environ.get("NATIVO_NOME"):
        return os.environ["NATIVO_NOME"][:40]
    try:
        n = open(os.path.join(_pasta(), "nome.txt"), encoding="utf-8").read().strip()
        if n: return n[:40]
    except OSError:
        pass
    return socket.gethostname()[:40]


def _base(end):
    end = (end or "").strip().replace("http://", "").split("/")[0]
    if not end: return ""
    return "http://" + (end if ":" in end else "%s:%d" % (end, PORTA))


def meus_enderecos():
    ips = {"127.0.0.1"}
    try:
        for inf in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET): ips.add(inf[4][0])
    except OSError:
        pass
    try:
        t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); t.connect(("8.8.8.8", 80)); ips.add(t.getsockname()[0]); t.close()
    except OSError:
        pass
    return ips


class Ouvido:
    """AO ABRIR (13/11, a dinâmica do "um ícone só" do Vaio, 18/10, agora dentro do programa e nos dois sistemas): escuta
    a rede por alguns segundos numa linha de fundo. Outro Sistema gritando (UDP 8766) = já existe um computador principal:
    este pode ser a tela secundária dele. O próprio grito (este computador) não conta."""
    def __init__(self, seg=4.5):
        self.achou = None                      # {"base": "http://ip:porta", "nome": "..."}
        self.pronto = threading.Event()
        threading.Thread(target=self._ouve, args=(seg,), name="ouvido", daemon=True).start()

    def _ouve(self, seg):
        try:
            eu = set() if os.environ.get("NATIVO_OUVIR") == "tudo" else meus_enderecos()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", PORTA_ANUNCIO)); s.settimeout(0.4)
            fim = time.time() + seg
            while time.time() < fim:
                try:
                    d, (ip, _) = s.recvfrom(2048)
                    m = json.loads(d.decode("utf-8"))
                    if m.get("sistema") == "icm-projecao" and ip not in eu:
                        self.achou = {"base": "http://%s:%d" % (ip, int(m.get("porta") or PORTA)), "nome": str(m.get("nome") or ip)[:40]}
                        break
                except (socket.timeout, ValueError):
                    pass
            s.close()
        except OSError as e:
            print("ouvido da rede:", e, flush=True)
        self.pronto.set()


def reabrir(extra):
    """Abre o Sistema de novo com outros argumentos (virar tela secundária / voltar a projetar daqui). Quem chama fecha este."""
    args = [a for a in sys.argv[1:] if a not in ("--principal",)]
    if "--retorno" in args:
        k = args.index("--retorno"); del args[k:k + (2 if k + 1 < len(args) and not args[k + 1].startswith("--") else 1)]
    cmd = ([sys.executable] if getattr(sys, "frozen", False) else [sys.executable, os.path.abspath(sys.argv[0])]) + args + list(extra)
    env = dict(os.environ); env.pop("NATIVO_SEGUIR", None)
    subprocess.Popen(cmd, env=env, cwd=os.getcwd(), creationflags=0x08000000 if sys.platform.startswith("win") else 0)


class Seguidor:
    def __init__(self, endereco=""):
        self.fixo = _base(endereco)                # endereço dado na mão: nunca troca
        self.base = self.fixo
        self.nome = meu_nome()
        self.fila = queue.Queue()
        self.fim = False
        self._ult = None
        self._ident = False
        self._acordar = 0.0
        threading.Thread(target=self._laco, name="seguir", daemon=True).start()

    # ---------------- a linha de fundo: só rede
    def _pega(self, u, t=2.5):
        return json.loads(urllib.request.urlopen(self.base + u, timeout=t).read().decode("utf-8"))

    def _ouvir(self, seg):
        """O grito do principal (sistema.anunciar_na_rede): {"sistema": "icm-projecao", "porta": N}."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", PORTA_ANUNCIO)); s.settimeout(0.5)
        except OSError:
            time.sleep(seg); return ""
        fim = time.time() + seg
        try:
            while time.time() < fim and not self.fim:
                try:
                    d, (ip, _) = s.recvfrom(2048)
                    m = json.loads(d.decode("utf-8"))
                    if m.get("sistema") == "icm-projecao":
                        return "http://%s:%d" % (ip, int(m.get("porta") or PORTA))
                except (socket.timeout, ValueError):
                    pass
        finally:
            s.close()
        return ""

    def _achar(self):
        b = self._ouvir(3)
        if b: return b
        try:
            b = _base(open(os.path.join(_pasta(), "pc.txt"), encoding="utf-8").read())
            if b:
                urllib.request.urlopen(b + "/api/estado", timeout=1.5).read()
                return b
        except Exception:
            pass
        return ""

    def _lembrar(self):
        if os.environ.get("NATIVO_SO_LOCAL") or self.fixo:
            return
        try:
            os.makedirs(_pasta(), exist_ok=True)
            open(os.path.join(_pasta(), "pc.txt"), "w", encoding="utf-8").write(self.base.replace("http://", ""))
        except OSError:
            pass

    def _laco(self):
        t_ap, falhas, ligado = 0.0, 0, False
        while not self.fim:
            if not self.base:
                self.fila.put(("ligacao", "procurando", ""))
                self.base = self._achar()
                if not self.base: continue
            try:
                agora = time.time()
                if agora - t_ap >= 1.0:
                    a = self._pega("/api/apoio?nome=" + urllib.parse.quote(self.nome)); t_ap = agora
                    if not ligado:
                        ligado = True; self._lembrar(); self._ult = None
                        self.fila.put(("ligacao", "ligado", self.base))
                    self.fila.put(("apoio", a, None))
                    if agora > self._acordar:          # a tela não dorme enquanto é a tela secundária
                        self._acordar = agora + 30; self._nao_dormir()
                e = self._pega("/api/estado"); e = e.get("estado", e)
                tipo = e.get("tipo") or "espera"
                ch = (tipo, e.get("apres"), e.get("slidepp"), e.get("louvor"), e.get("slide"), e.get("estilo"), e.get("agora"))
                if ch != self._ult:
                    pronto = None
                    if tipo not in ("louvor", "espera", "preto"):   # o que não se repete só pelo estado vem pronto
                        pronto = (self._pega("/api/tela") or {}).get("payload")
                    self._ult = ch
                    self.fila.put(("estado", e, pronto))
                falhas = 0
            except Exception:
                falhas += 1
                if falhas == 8:                        # ~3 s sem resposta: caiu; volta sozinho (o principal lembra o par)
                    ligado = False
                    self.fila.put(("ligacao", "caiu", self.base))
                    if not self.fixo: self.base = ""
                time.sleep(0.4)
            time.sleep(0.2)

    @staticmethod
    def _nao_dormir():
        try:
            if sys.platform.startswith("win"):
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x00000001 | 0x00000002)   # sistema + tela: zera a contagem
            else:
                for c in (["cinnamon-screensaver-command", "-d"], ["xset", "s", "reset"]):
                    try: subprocess.Popen(c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except OSError: pass
        except Exception:
            pass

    # ---------------- a linha da interface: aplica no Sistema daqui
    def drenar(self, ctl):
        for _ in range(20):
            try: oque, a, b = self.fila.get_nowait()
            except queue.Empty: return
            try:
                if oque == "estado":
                    self._estado(ctl, a, b); print("tela secundária: acompanha ·", ctl._no_ar, flush=True)
                elif oque == "apoio": self._apoio(ctl, a)
                elif oque == "ligacao": self._ligacao(ctl, a, b)
            except Exception as e:
                print("seguir:", oque, e, flush=True)

    def _ligacao(self, ctl, como, base):
        print("tela secundária:", como, base, flush=True)
        ctl.seguindo_texto = {"procurando": "Procurando o computador principal…",
                              "caiu": "Sem resposta do computador principal · reconectando…"}.get(como, "")
        ctl.telasMudou.emit()

    def _apoio(self, ctl, a):
        est, papel, modo = a.get("estado"), a.get("papel", 2), a.get("modo", "retorno")
        self.principal = a.get("pc") or getattr(self, "principal", "")
        # papel 2 = esta é a tela de retorno (os gestos); "igual ao telão" ou depois do Trocar (papel 1) = o telão
        ctl._papel(est == "aceito" and papel == 2 and modo == "retorno")
        txt = ("" if est == "aceito" else
               "Esta tela foi encontrada · responda no computador principal (%s)" % (a.get("pc") or "") if est == "pendente" else
               "O computador principal está usando só o telão")
        if txt != ctl.seguindo_texto:
            ctl.seguindo_texto = txt; ctl.telasMudou.emit()
        if (est, papel, modo) != getattr(self, "_visto", None):
            self._visto = (est, papel, modo)
            print("tela secundária:", est, "papel", papel, modo, flush=True)
        ident = float(a.get("identificar") or 0) > 0
        if ident and not self._ident:
            ctl.identificar.emit(2 if papel == 2 else 1, "Tela de retorno" if papel == 2 else "Telão")
        self._ident = ident

    def _estado(self, ctl, e, pronto):
        import cerebro
        tipo = e.get("tipo") or "espera"
        if e.get("estilo") in ("limpo", "mapa"):
            ctl.estilo = e["estilo"]
        if tipo == "slide" and e.get("apres"):
            L = ctl.listaApres(); nome = NFC(e["apres"])
            k = next((i for i, a in enumerate(L) if NFC(a["nome"]) == nome), -1)
            i = int(e.get("slidepp", -1))
            if k >= 0 and 0 <= i < len(L[k]["slides"]):
                if ctl.ap is not L[k]:
                    ctl.ap = L[k]; ctl.ap_pos = -1
                if not (ctl.vivo == "apres" and ctl.ap_pos == i):
                    ctl.projetarSlide(i)
                return
        elif tipo == "louvor" and 0 <= int(e.get("louvor", -1)) < len(ctl.A.louvores):
            ctl.projetar(int(e["louvor"]), int(e.get("slide") or 0)); return
        elif tipo == "espera":
            if ctl.vivo not in ("", "espera"): ctl.descanso()
            return
        elif tipo == "preto":
            ctl.preto(); return
        if pronto and pronto.get("modo") not in (None, "slide"):   # Bíblia, texto, cronômetro, relógio, fundo: pronto
            t = dict(pronto)
            if t.get("fundo") and not os.path.isabs(t["fundo"]):
                t["fundo"] = os.path.join(cerebro.APP, t["fundo"].replace("/", os.sep))
            ctl.vivo = tipo; ctl._no_ar = e.get("agora") or tipo
            ctl._manda(t)
