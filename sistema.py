# -*- coding: utf-8 -*-
"""Sistema — projeção da igreja.
Sobe o servidor local, converte PowerPoint/PDF em slides e abre o app em janela limpa.
Feito para rodar como .EXE em Windows, sem internet."""
import http.server, socketserver, threading, webbrowser, subprocess, os, sys, json, shutil, glob, time, socket, re, io

VERSAO = "2.5.0"
PORTA = 8765

def raiz():
    """Pasta dos arquivos do app (funciona rodando como .py e como .exe do PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE = raiz()
# os slides convertidos ficam ao lado do executável (gravável), não dentro do .exe
# Os dados do usuário (igreja, louvores próprios, fundos) ficam FORA do programa,
# numa pasta fixa do Windows: assim sobrevivem a qualquer atualização do Sistema.
DADOS_USUARIO = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Sistema Projecao")
ARQ_CONFIG = os.path.join(DADOS_USUARIO, "configuracoes.json")
SAIDA = os.path.join(DADOS_USUARIO, "slides_importados")   # apresentações convertidas


# ------------------------------------------------- controle pelo celular
# O celular manda comandos; a tela do Sistema vem buscar. Tudo dentro da rede local,
# sem internet e sem nada sair do lugar.
COMANDOS = []          # fila de comandos vindos do celular
# "ts" já nasce carimbado: sem isso o celular que estivesse aberto acusava
# "O computador parou de responder" durante toda a subida do Sistema
ESTADO = {"agora": "Pronto.", "projetando": False, "congelado": False, "ts": time.time()}
TELA = {"payload": None, "n": 0}       # o que está no telão agora (para a prévia do celular)
TRAVA = threading.Lock()


def endereco_local():
    """IP deste computador na rede (o que o celular precisa digitar)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))          # não envia nada; só descobre a placa de rede usada
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def por_icone(titulo, tentativas=40):
    """Troca o ícone da janela (senão o Windows mostra o do Python)."""
    def tarefa():
        import win32gui, win32con, win32api
        ico = os.path.join(BASE, "sistema.ico")
        if not os.path.exists(ico):
            return
        for _ in range(tentativas):
            time.sleep(0.25)
            h = win32gui.FindWindow(None, titulo)
            if not h:
                continue
            try:
                for tam, msg in ((32, 1), (16, 0)):    # 1 = ícone grande, 0 = pequeno
                    hi = win32gui.LoadImage(0, ico, win32con.IMAGE_ICON, tam, tam,
                                            win32con.LR_LOADFROMFILE)
                    win32api.SendMessage(h, win32con.WM_SETICON, msg, hi)
                return
            except Exception:
                return
    threading.Thread(target=tarefa, daemon=True).start()


def qr_base64(texto):
    """Código para o celular apontar a câmera e entrar direto."""
    try:
        import qrcode, io, base64
        img = qrcode.make(texto, box_size=7, border=2)
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


# nunca deixar piscar janela preta na cara do operador
SEM_JANELA = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if os.name == "nt" else {}


def liberar_no_firewall(porta):
    """Pede ao Windows para deixar o celular chegar até aqui (só na rede local)."""
    nome = "Sistema Projecao (porta %d)" % porta
    try:
        subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", "name=" + nome],
                       capture_output=True, timeout=10, check=True, **SEM_JANELA)
        return True                                     # regra já existe
    except Exception:
        pass
    try:
        subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=" + nome,
                        "dir=in", "action=allow", "protocol=TCP", "localport=%d" % porta,
                        "profile=private,domain"],
                       capture_output=True, timeout=10, **SEM_JANELA)
        return True
    except Exception:
        return False


def pasta_usuario(nome):
    """Pasta de conteúdo importado pelo operador (animacoes, cifras...)."""
    return os.path.join(DADOS_USUARIO, nome)


def pasta_melodias():
    return pasta_usuario("melodias")


_CATALOGO = {"ts": 0, "dados": None}


def catalogo_do_musico():
    """A lista do que existe, sem o conteúdo. Fica em memória: o celular pede
    isto uma vez ao abrir, e o disco não é lido de novo a cada toque."""
    if _CATALOGO["dados"] is not None and time.time() - _CATALOGO["ts"] < 30:
        return _CATALOGO["dados"]
    violao = {}
    try:
        cam = os.path.join(pasta_usuario("cifras"), "acordes.json")
        with io.open(cam, encoding="utf-8") as f:
            for chave, reg in json.load(f).items():
                violao[chave] = reg.get("tom") or ""
    except FileNotFoundError:
        pass
    except Exception as e:
        sys.stderr.write("catalogo do musico, violao: %s" % e + chr(10))
    melodia, instrumentos = {}, []
    try:
        with io.open(os.path.join(pasta_melodias(), "indice.json"), encoding="utf-8") as f:
            idx = json.load(f)
        instrumentos = idx.get("instrumentos", [])
        for chave, v in idx.get("louvores", {}).items():
            melodia[chave] = v.get("tons", {})
    except FileNotFoundError:
        pass
    except Exception as e:
        sys.stderr.write("catalogo do musico, melodia: %s" % e + chr(10))
    d = {"violao": violao, "melodia": melodia, "instrumentos": instrumentos}
    _CATALOGO.update({"ts": time.time(), "dados": d})
    return d


def material_do_louvor(chave, afinacao="C"):
    """A cifra de violão e/ou o caderno melódico de UM louvor."""
    saida = {"ok": True, "chave": chave, "em": afinacao}
    try:
        cam = os.path.join(pasta_usuario("cifras"), "acordes.json")
        with io.open(cam, encoding="utf-8") as f:
            reg = json.load(f).get(chave)
        if reg:
            saida["violao"] = {"tom": reg.get("tom"), "linhas": reg.get("linhas", [])}
    except Exception:
        pass
    try:
        with io.open(os.path.join(pasta_melodias(), "indice.json"), encoding="utf-8") as f:
            idx = json.load(f)
        # o indice das melodias e' por TITULO, nao pela chave do app
        titulo = chave.split("|")[1] if "|" in chave else chave
        alvo = None
        for k, v in idx.get("louvores", {}).items():
            if k == _simples(titulo):
                alvo = v
                break
        if alvo:
            with io.open(os.path.join(pasta_melodias(), alvo["arq"]), encoding="utf-8") as f:
                reg = json.load(f)
            cad = reg.get("cadernos", {}).get(afinacao)
            if cad:
                saida["melodia"] = cad
                saida["tons"] = alvo.get("tons", {})
    except Exception:
        pass
    return saida


def _simples(t):
    import unicodedata as _u
    t = _u.normalize("NFD", (t or "").upper())
    t = "".join(c for c in t if _u.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9 ]+", " ", t).strip()


def ler_indice(nome):
    """indice.json de um conteúdo importado. Vazio = o operador ainda não importou,
    e aí os botões do painel simplesmente não aparecem."""
    try:
        with open(os.path.join(pasta_usuario(nome), "indice.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


ARQ_HISTORICO = os.path.join(DADOS_USUARIO, "historico.json")


def ler_historico():
    """O que ja foi projetado, culto a culto. Cada registro:
       {"q": "louvor", "rot": "5 2018 - CLAMANDO ESTOU", "chave": "...",
        "ini": <hora em segundos>, "seg": <quanto tempo ficou no telao>}"""
    try:
        with open(ARQ_HISTORICO, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def gravar_historico(registros):
    """Acrescenta ao historico, por troca atomica: um desligamento no meio do
    culto nao pode deixar o arquivo pela metade e apagar meses de registro."""
    os.makedirs(DADOS_USUARIO, exist_ok=True)
    with TRAVA:
        atual = ler_historico()
        atual.extend(registros)
        if len(atual) > 20000:            # muito alem de anos de culto
            atual = atual[-20000:]
        tmp = ARQ_HISTORICO + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(atual, f, ensure_ascii=False)
        os.replace(tmp, ARQ_HISTORICO)
    return len(atual)


def ler_config():
    try:
        with open(ARQ_CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def gravar_config(dados):
    os.makedirs(DADOS_USUARIO, exist_ok=True)
    tmp = ARQ_CONFIG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)
    os.replace(tmp, ARQ_CONFIG)   # troca atômica: nunca deixa o arquivo pela metade


# ---------------------------------------------------------------- conversão
def converter_powerpoint(caminho, destino):
    """PowerPoint instalado -> exporta cada slide como PNG (fidelidade total)."""
    import win32com.client
    app = None
    try:
        app = win32com.client.Dispatch("PowerPoint.Application")
        apres = app.Presentations.Open(os.path.abspath(caminho), WithWindow=False)
        try:
            apres.SaveAs(os.path.abspath(destino), 18)   # 18 = ppSaveAsPNG (uma imagem por slide)
        finally:
            apres.Close()
        return True
    finally:
        if app is not None:
            try: app.Quit()
            except Exception: pass


def converter_libreoffice(caminho, destino):
    """Sem PowerPoint? tenta o LibreOffice (converte para PDF e depois em imagens)."""
    for exe in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
        if os.path.exists(exe):
            subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", destino, caminho],
                           check=True, timeout=180, **SEM_JANELA)
            pdfs = glob.glob(os.path.join(destino, "*.pdf"))
            if pdfs:
                return converter_pdf(pdfs[0], destino)
    return False


def converter_pdf(caminho, destino):
    """PDF -> uma "tela" por página, usando o leitor de PDF do próprio Windows.

    Antes isto dependia do PyMuPDF, que não vem junto: o `import` falhava, o
    `except` engolia o erro e importar PDF na Escola Bíblica não fazia nada, sem
    dizer por quê. Empacotar o PyMuPDF custaria 53 MB — mais do que o Sistema
    inteiro — para fazer o que o navegador já faz de graça: ele abre PDF nativo.
    Então copiamos o arquivo e deixamos cada página ser uma tela.
    """
    try:
        alvo = os.path.join(destino, "documento.pdf")
        shutil.copy2(caminho, alvo)
        paginas = 1
        try:
            from pypdf import PdfReader
            paginas = len(PdfReader(alvo).pages)
        except Exception:
            pass                      # sem contar as páginas ainda dá para abrir a primeira
        with open(os.path.join(destino, "paginas.txt"), "w", encoding="utf-8") as f:
            f.write(str(paginas))
        return True
    except Exception:
        return False


def importar(caminho):
    """Converte o arquivo e devolve a lista de slides (URLs servidas pelo próprio servidor)."""
    nome = os.path.splitext(os.path.basename(caminho))[0]
    destino = os.path.join(SAIDA, "".join(c if c.isalnum() or c in " -_" else "_" for c in nome))
    shutil.rmtree(destino, ignore_errors=True)
    os.makedirs(destino, exist_ok=True)

    ext = os.path.splitext(caminho)[1].lower()
    ok = False
    erro = ""
    try:
        if ext in (".ppt", ".pptx", ".pps", ".ppsx", ".odp"):
            try:
                ok = converter_powerpoint(caminho, destino)
            except Exception as e:
                erro = str(e)
                ok = converter_libreoffice(caminho, destino)
        elif ext == ".pdf":
            ok = converter_pdf(caminho, destino)
        elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"):
            shutil.copy2(caminho, os.path.join(destino, "Slide001" + ext))
            ok = True
    except Exception as e:
        erro = str(e)

    imgs = sorted(glob.glob(os.path.join(destino, "**", "*.png"), recursive=True) +
                  glob.glob(os.path.join(destino, "**", "*.jpg"), recursive=True) +
                  glob.glob(os.path.join(destino, "**", "*.jpeg"), recursive=True))
    if not imgs:
        return {"ok": False, "erro": erro or "Não consegui converter este arquivo."}

    def chave(p):
        b = os.path.basename(p)
        dig = "".join(c for c in b if c.isdigit())
        return (int(dig) if dig else 0, b)
    imgs.sort(key=chave)

    # a URL precisa vir codificada: nomes de apresentação costumam ter espaço e acento
    from urllib.parse import quote
    rel = [quote("slides_importados/" + os.path.relpath(p, SAIDA).replace("\\", "/")) for p in imgs]
    return {"ok": True, "nome": nome, "slides": rel}


# ---------------------------------------------------------------- servidor
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=BASE, **kw)

    def log_message(self, *a):
        pass

    def guess_type(self, path):
        """Diz ao celular que os arquivos são UTF-8. Sem isso o navegador do celular
        adivinha outra codificação, os acentos corrompem e o script quebra."""
        tipo = super().guess_type(path)
        base = tipo.split(";")[0].strip()
        if base.startswith("text/") or base in ("application/javascript", "application/json"):
            return base + "; charset=utf-8"
        return tipo

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # celular sempre pega a versão nova
        super().end_headers()

    def translate_path(self, path):
        # os slides convertidos moram fora da pasta do app (o .exe é somente leitura)
        from urllib.parse import unquote
        limpo = unquote(path.split("?", 1)[0].split("#", 1)[0])
        # tudo o que o operador importou mora fora da pasta do app (o .exe é
        # somente leitura): slides convertidos, animações dos CIAS e as cifras
        for prefixo, base in (("/slides_importados/", SAIDA),
                              ("/animacoes/", pasta_usuario("animacoes")),
                              ("/cifras/", pasta_usuario("cifras"))):
            if limpo.startswith(prefixo):
                resto = os.path.normpath(limpo[len(prefixo):].replace("/", os.sep)).lstrip(os.sep)
                destino = os.path.normpath(os.path.join(base, resto))
                if destino.startswith(os.path.normpath(base)):   # não deixa sair da pasta
                    return destino
        return super().translate_path(path)

    def _json(self, obj, cod=200):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(cod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.startswith("/api/config"):
            return self._json({"ok": True, "versao": VERSAO, "dados": ler_config()})
        if self.path.startswith("/api/comandos"):        # a tela do Sistema vem buscar o que o celular mandou
            with TRAVA:
                fila, COMANDOS[:] = list(COMANDOS), []
            return self._json({"ok": True, "comandos": fila})
        if self.path.startswith("/api/tela"):            # a prévia: o que está no telão agora
            # O celular manda ?n= com o número do quadro que ele já tem. Se for o
            # mesmo, devolvemos só o número — sem o payload. Sem isto o fundo
            # inteiro (imagem em base64) descia de novo a cada 700ms, torrando a
            # bateria e engasgando o hotspot da igreja à toa.
            try:
                tinha = int(self.path.split("n=", 1)[1].split("&")[0]) if "n=" in self.path else -1
            except Exception:
                tinha = -1
            with TRAVA:
                if tinha == TELA["n"]:
                    return self._json({"ok": True, "n": TELA["n"]})
                return self._json({"ok": True, "n": TELA["n"], "payload": TELA["payload"]})
        if self.path.startswith("/api/estado"):          # o celular pergunta o que está no telão
            with TRAVA:
                # "idade" = há quantos segundos a tela do Sistema não publica nada.
                # Quem responde aqui é o Python, que continua de pé mesmo se a
                # tela do computador travar ou for fechada — sem isto o celular
                # ficaria mostrando "AO VIVO" para sempre.
                idade = time.time() - ESTADO.get("ts", 0) if ESTADO.get("ts") else 999
                return self._json({"ok": True, "estado": dict(ESTADO), "idade": round(idade, 1)})
        if self.path.startswith("/api/animacoes"):       # louvores de CIAS com animação
            return self._json({"ok": True, "indice": ler_indice("animacoes")})
        if self.path.startswith("/api/historico"):     # o que ja foi projetado
            return self._json({"ok": True, "registros": ler_historico()})
        if self.path.startswith("/api/cifras"):          # em que PDF e página está cada cifra
            return self._json({"ok": True, "indice": ler_indice("cifras")})
        if self.path.startswith("/api/musico"):
            # O CATÁLOGO do músico: que louvores têm cifra de violão e quais têm
            # caderno melódico, e em que tom cada instrumento lê. Só a lista —
            # o conteúdo vem depois, um louvor por vez.
            return self._json({"ok": True, **catalogo_do_musico()})
        if self.path.startswith("/api/cifra/"):
            # UM louvor, sob demanda. Quatro celulares podem estar pedindo
            # cadernos diferentes do mesmo louvor ao mesmo tempo — cada resposta
            # tem uns poucos kilobytes, e o servidor já atende em paralelo.
            from urllib.parse import unquote, urlparse, parse_qs
            u = urlparse(self.path)
            chave = unquote(u.path[len("/api/cifra/"):])
            afinacao = (parse_qs(u.query).get("em") or ["C"])[0]
            return self._json(material_do_louvor(chave, afinacao))
        if self.path.startswith("/api/rede"):            # endereço e QR para o celular entrar
            porta = self.server.server_address[1]
            url = "http://%s:%d/controle.html" % (endereco_local(), porta)
            return self._json({"ok": True, "url": url, "ip": endereco_local(), "porta": porta,
                               "qr": qr_base64(url)})
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/comando"):         # veio do celular
            try:
                n = int(self.headers.get("Content-Length", 0))
                c = json.loads(self.rfile.read(n).decode("utf-8"))
                with TRAVA:
                    COMANDOS.append(c)
                    if len(COMANDOS) > 40: del COMANDOS[:-40]
                return self._json({"ok": True})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/tela"):              # o Sistema manda o que acabou de projetar
            try:
                n = int(self.headers.get("Content-Length", 0))
                with TRAVA:
                    TELA["payload"] = json.loads(self.rfile.read(n).decode("utf-8"))
                    TELA["n"] += 1
                return self._json({"ok": True})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/estado"):           # a tela do Sistema avisa o que está no ar
            try:
                n = int(self.headers.get("Content-Length", 0))
                with TRAVA:
                    ESTADO.update(json.loads(self.rfile.read(n).decode("utf-8")))
                    ESTADO["ts"] = time.time()      # para o celular saber se isto ainda é recente
                return self._json({"ok": True})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/historico"):
            try:
                n = int(self.headers.get("Content-Length", 0))
                regs = json.loads(self.rfile.read(n).decode("utf-8"))
                return self._json({"ok": True, "total": gravar_historico(regs or [])})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/config"):
            try:
                n = int(self.headers.get("Content-Length", 0))
                gravar_config(json.loads(self.rfile.read(n).decode("utf-8")))
                return self._json({"ok": True})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/importar"):
            try:
                n = int(self.headers.get("Content-Length", 0))
                dados = json.loads(self.rfile.read(n).decode("utf-8"))
                caminho = dados.get("caminho", "")
                if not os.path.exists(caminho):
                    return self._json({"ok": False, "erro": "Arquivo não encontrado."})
                return self._json(importar(caminho))
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/limpar"):
            try:
                shutil.rmtree(SAIDA, ignore_errors=True)
                os.makedirs(SAIDA, exist_ok=True)
                return self._json({"ok": True})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/escolher"):
            try:
                return self._json({"ok": True, "caminho": escolher_arquivo()})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        self.send_error(404)


# ---------------------------------------------------------------- janela nativa
def monitores():
    """Lista os monitores pelo Windows — não depende de permissão do navegador."""
    try:
        import win32api
        saida = []
        for h, _, _ in win32api.EnumDisplayMonitors():
            info = win32api.GetMonitorInfo(h)
            x1, y1, x2, y2 = info["Monitor"]
            saida.append({"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1,
                          "principal": bool(info.get("Flags", 0) & 1)})
        return saida
    except Exception:
        return []


class Ponte:
    """O que a tela do Sistema pode pedir ao Windows."""
    def __init__(self):
        self.projecao = None
        self.url = ""

    def monitores(self):
        return monitores()

    def abrir_projecao(self):
        import webview
        if self.projecao is not None:
            try: self.projecao.show(); return {"ok": True, "externa": True}
            except Exception: self.projecao = None
        telas = monitores()
        externa = next((m for m in telas if not m["principal"]), None)
        alvo = externa or (telas[0] if telas else {"x": 0, "y": 0, "w": 1280, "h": 720})
        self.projecao = webview.create_window(
            "Projeção", self.url + "projecao.html?nativo=1",
            x=alvo["x"], y=alvo["y"], width=alvo["w"], height=alvo["h"],
            frameless=bool(externa), fullscreen=bool(externa), background_color="#000000")
        self.projecao.events.closed += self._fechou
        return {"ok": True, "externa": bool(externa)}

    def _fechou(self):
        self.projecao = None

    def projecao_aberta(self):
        """A janela do telão ainda existe?

        Sem isto, se alguém fechasse a janela da Projeção, o painel continuava
        dizendo "ao vivo" e o celular ficava com a bolinha vermelha para sempre —
        o operador achava que estava projetando sem telão nenhum.
        """
        return {"ok": True, "aberta": self.projecao is not None}

    def fechar_projecao(self):
        if self.projecao is not None:
            try: self.projecao.destroy()
            except Exception: pass
            self.projecao = None
        return {"ok": True}

    def escolher(self):
        return {"ok": True, "caminho": escolher_arquivo()}

    def importar(self, caminho):
        return importar(caminho)

    def ler_config(self):
        return {"ok": True, "versao": VERSAO, "dados": ler_config()}

    def gravar_config(self, dados):
        gravar_config(dados if isinstance(dados, dict) else json.loads(dados))
        return {"ok": True}


def escolher_arquivo():
    """Abre a janelinha do Windows para o operador escolher o arquivo."""
    import tkinter as tk
    from tkinter import filedialog
    r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
    cam = filedialog.askopenfilename(
        title="Escolha a apresentação",
        filetypes=[("Apresentações e PDF", "*.pptx *.ppt *.ppsx *.pps *.odp *.pdf"),
                   ("Imagens", "*.png *.jpg *.jpeg"), ("Todos os arquivos", "*.*")])
    r.destroy()
    return cam


def porta_livre(p):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", p)) != 0


def abrir_navegador(url):
    """Abre em janela limpa (sem barra de endereço), como um programa de verdade."""
    perfil = os.path.join(os.environ.get("LOCALAPPDATA", os.getcwd()), "SistemaProjecao", "navegador")
    os.makedirs(perfil, exist_ok=True)
    candidatos = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for exe in candidatos:
        if os.path.exists(exe):
            subprocess.Popen([exe, "--app=" + url, "--user-data-dir=" + perfil,
                              "--no-first-run", "--no-default-browser-check",
                              "--disable-features=Translate", "--start-maximized"], **SEM_JANELA)
            return True
    webbrowser.open(url)
    return False


# --- barra de carregamento -------------------------------------------------
# A barra dourada NÃO está pintada no splash.png: ela é escrita aqui em cima
# do trilho vazio, bloco a bloco, conforme cada etapa termina de verdade.
# Barra desenhada na imagem fica parada e o operador acha que travou.
#
# O caractere é o meio-bloco (U+2584) no tamanho 8: nessa combinação os blocos
# emendam LISO. O bloco cheio em corpo pequeno deixava a barra serrilhada.
BARRA_BLOCOS = 31          # 31 x 6px = 186px = a largura exata do trilho
BLOCO = "▄"
_barra = {"em": 0.0, "meta": 0.0}


def _escrever_barra(fracao):
    try:
        import pyi_splash
        pyi_splash.update_text(BLOCO * round(BARRA_BLOCOS * fracao))
    except Exception:
        pass        # rodando pelo .py solto, sem splash — segue a vida


def marcar_splash(fracao):
    """Anda a barra até `fracao` (0 a 1). Nunca volta atrás."""
    fracao = max(0.0, min(1.0, fracao))
    if fracao <= _barra["em"]:
        return
    _barra["em"] = _barra["meta"] = fracao
    _escrever_barra(fracao)


def _rastejar():
    """Etapas longas (carregar a janela leva ~1,3s) deixavam a barra parada e
    com cara de travada. Entre um marco e o outro ela caminha sozinha, devagar,
    sem nunca ultrapassar o próximo marco — anda de verdade, mas não mente."""
    while _barra["em"] < 1.0:
        time.sleep(0.08)
        folga = _barra["meta"] + 0.14 - _barra["em"]     # teto: só até perto do próximo marco
        if folga > 0.004:
            _barra["em"] += folga * 0.05
            _escrever_barra(_barra["em"])


def fechar_splash():
    """Some com a telinha de carregamento (ela aparece antes mesmo do Python subir)."""
    marcar_splash(1.0)
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass


def main():
    marcar_splash(0.10)                        # Python de pé
    threading.Thread(target=_rastejar, daemon=True).start()
    os.makedirs(SAIDA, exist_ok=True)
    porta = PORTA
    while not porta_livre(porta) and porta < PORTA + 20:
        porta += 1
    socketserver.TCPServer.allow_reuse_address = True
    # 0.0.0.0 = aceita também o celular na mesma rede (hotspot ou wi-fi da igreja)
    srv = socketserver.ThreadingTCPServer(("0.0.0.0", porta), Handler)
    marcar_splash(0.25)                        # porta achada e servidor criado
    threading.Thread(target=liberar_no_firewall, args=(porta,), daemon=True).start()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    raiz_url = "http://127.0.0.1:%d/" % porta
    time.sleep(0.3)
    marcar_splash(0.35)                        # servidor no ar

    # JANELA PRÓPRIA DO SISTEMA (sem Edge, com o nosso ícone na barra de tarefas)
    try:
        if os.environ.get("SISTEMA_NAVEGADOR") == "1":
            raise RuntimeError("modo navegador escolhido")
        import webview
        marcar_splash(0.55)                    # componente de janela carregado
        ponte = Ponte()
        ponte.url = raiz_url
        # abre JÁ na tela de carregamento e só depois troca pelo app (nada de espera muda)
        # tamanho confortável, centralizado na tela — sem ocupar tudo
        telas = monitores()
        prin = next((m for m in telas if m["principal"]), None) or {"x": 0, "y": 0, "w": 1366, "h": 768}
        larg = max(980, min(1180, int(prin["w"] * 0.82)))
        alt  = max(620, min(760,  int(prin["h"] * 0.84)))
        titulo = "Sistema v" + VERSAO
        janela = webview.create_window(
            titulo, raiz_url + "carregando.html",
            width=larg, height=alt, min_size=(940, 600),
            x=prin["x"] + (prin["w"] - larg) // 2, y=prin["y"] + (prin["h"] - alt) // 2,
            background_color="#0b1526", js_api=ponte)
        por_icone(titulo)
        # Fechou o controle, fecha o telão junto. Quem fecha o Sistema está
        # encerrando o culto — deixar a janela da projeção órfã na tela do
        # projetor, sem nada que a comande, não serve para nada.
        janela.events.closed += lambda: ponte.fechar_projecao()
        marcar_splash(0.70)                    # janela montada

        def entrar():
            t0 = time.time()
            for i in range(80):                        # espera o servidor responder
                try:
                    import urllib.request
                    urllib.request.urlopen(raiz_url + "index.html", timeout=1).read(64)
                    marcar_splash(0.92)                # o app respondeu
                    break
                except Exception:
                    marcar_splash(0.70 + 0.22 * (i / 80.0))   # anda enquanto tenta
                    time.sleep(0.05)
            resto = 0.25 - (time.time() - t0)          # só um piscar: o Sistema é rápido mesmo
            if resto > 0:
                time.sleep(resto)
            try: janela.load_url(raiz_url + "index.html")
            except Exception: pass
            fechar_splash()          # a janela já está com o app: pode tirar a telinha

        webview.start(entrar, gui="edgechromium", debug=False)
        return
    except Exception as e:
        print("janela própria indisponível (%s) — abrindo no navegador" % e)

    # Sem isto, no micro que não tem o WebView2 (justamente o notebook fraco para
    # o qual esta reserva existe) a telinha de carregamento ficava colada no meio
    # da tela, sempre por cima, sem botão de fechar — e a thread da barra ficava
    # girando para sempre, porque ela só para quando a barra chega no fim.
    fechar_splash()
    abrir_navegador(raiz_url + "index.html")   # reserva: se faltar o componente do Windows
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
