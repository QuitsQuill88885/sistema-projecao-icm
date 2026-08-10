# -*- coding: utf-8 -*-
"""Instalador do Sistema — copia o programa para a pasta de Programas do Windows,
cria os atalhos e as pastas onde o usuário pode largar os arquivos dele."""
import os, sys, shutil, threading, time, subprocess

VERSAO = "1.2.0"
NOME = "Sistema"
DESTINO = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Programs", NOME)
DADOS = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Sistema Projecao")
# pastas visíveis: o operador pode largar arquivos aqui
PASTAS_USUARIO = [
    ("Meus fundos", "Coloque aqui imagens de fundo (JPG/PNG) para usar na projeção."),
    ("Minhas apresentações", "Coloque aqui os PowerPoint e PDF da Escola Bíblica."),
    ("Meus louvores", "Louvores que você adicionar pelo Sistema ficam guardados aqui."),
]


def origem():
    return sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def instalar(progresso):
    base = origem()
    pacote = os.path.join(base, "programa")          # a pasta do app vai embutida no instalador
    progresso(5, "Preparando…")
    os.makedirs(DESTINO, exist_ok=True)

    progresso(10, "Fechando o Sistema, se estiver aberto…")
    fechar_sistema_aberto()

    progresso(15, "Copiando os arquivos do Sistema…")
    falhas = []
    if os.path.isdir(pacote):
        for raiz, _, arquivos in os.walk(pacote):
            rel = os.path.relpath(raiz, pacote)
            alvo = os.path.join(DESTINO, rel) if rel != "." else DESTINO
            os.makedirs(alvo, exist_ok=True)
            for a in arquivos:
                try:
                    shutil.copy2(os.path.join(raiz, a), os.path.join(alvo, a))
                except Exception as e:
                    falhas.append((a, e))
    # NUNCA mais engolir isto calado. Instalar por cima com o Sistema aberto
    # falhava arquivo por arquivo, o instalador dizia "Pronto!" e o programa
    # continuava na versão velha — sem uma palavra de aviso.
    if falhas:
        raise RuntimeError(
            "Não consegui substituir %d arquivo(s). Feche o Sistema e instale de novo. "
            "(primeiro: %s)" % (len(falhas), falhas[0][0]))

    progresso(65, "Criando as suas pastas…")
    os.makedirs(DADOS, exist_ok=True)
    for nome, explicacao in PASTAS_USUARIO:
        p = os.path.join(DADOS, nome)
        os.makedirs(p, exist_ok=True)
        leia = os.path.join(p, "LEIA-ME.txt")
        if not os.path.exists(leia):
            with open(leia, "w", encoding="utf-8") as f:
                f.write(explicacao + "\n")

    progresso(80, "Criando os atalhos…")
    exe = os.path.join(DESTINO, "Sistema.exe")
    for pasta in (pasta_area_de_trabalho(), pasta_menu_iniciar()):
        if pasta and os.path.isdir(pasta):
            atalho(os.path.join(pasta, NOME + ".lnk"), exe)

    progresso(85, "Instalando o conteúdo…")
    copiar_conteudo_extra(progresso)

    progresso(90, "Fixando no menu Iniciar…")
    fixar_no_iniciar(exe)

    progresso(95, "Finalizando…")
    time.sleep(0.4)
    progresso(100, "Pronto!")
    return exe


def copiar_conteudo_extra(progresso=None):
    """Instala a pasta "Conteudo" que vier AO LADO do instalador.

    É o que separa a versão completa da enxuta sem existirem dois programas:
    o mesmo instalador, com ou sem a pasta do lado. Dentro dela vão as
    animações dos CIAS e as cifras, que são pesadas demais para viajar dentro
    do .exe (juntas passam de 200 MB).

        Instalar o Sistema.exe
        Conteudo\\animacoes\\...
        Conteudo\\cifras\\...

    Nada aqui é obrigatório: sem a pasta, o Sistema instala igual e os botões
    de cifra e animação simplesmente não aparecem.
    """
    origem_pasta = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "Conteudo")
    if not os.path.isdir(origem_pasta):
        origem_pasta = os.path.join(os.getcwd(), "Conteudo")
    if not os.path.isdir(origem_pasta):
        return 0

    copiados = 0
    for raiz, _, arquivos in os.walk(origem_pasta):
        rel = os.path.relpath(raiz, origem_pasta)
        alvo = os.path.join(DADOS, rel) if rel != "." else DADOS
        os.makedirs(alvo, exist_ok=True)
        for a in arquivos:
            try:
                shutil.copy2(os.path.join(raiz, a), os.path.join(alvo, a))
                copiados += 1
                if progresso and copiados % 40 == 0:
                    progresso(85, "Instalando o conteúdo… (%d arquivos)" % copiados)
            except Exception:
                pass          # um arquivo de conteúdo que falhe não derruba a instalação
    return copiados


def fechar_sistema_aberto(espera=6.0):
    """Fecha o Sistema se ele estiver rodando.

    Atualizar por cima com o programa aberto é o caso NORMAL — o operador clica
    no instalador com o Sistema na tela. E o Windows não deixa sobrescrever um
    .exe em uso: a cópia falhava arquivo por arquivo e a versão velha continuava.
    Pedimos para fechar com jeito primeiro; só insistimos se ele não sair.
    """
    alvo = os.path.join(DESTINO, "Sistema.exe").lower()
    try:
        subprocess.run(["taskkill", "/IM", "Sistema.exe"],
                       capture_output=True, timeout=10, **SEM_JANELA)
    except Exception:
        pass
    fim = time.time() + espera
    while time.time() < fim:
        try:
            r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Sistema.exe", "/NH"],
                               capture_output=True, timeout=10, text=True, **SEM_JANELA)
            if "Sistema.exe" not in (r.stdout or ""):
                return True
        except Exception:
            return True
        time.sleep(0.4)
    try:                                   # não saiu com jeito: encerra mesmo
        subprocess.run(["taskkill", "/F", "/IM", "Sistema.exe"],
                       capture_output=True, timeout=10, **SEM_JANELA)
        time.sleep(0.6)
    except Exception:
        pass
    return True


def fechar_splash():
    """Some com a telinha de carregamento do instalador."""
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass


def centro_da_tela(larg, alt):
    """Canto superior esquerdo para a janela cair no MEIO do monitor principal.

    Sem passar x/y o pywebview larga a janela onde o Windows quiser — foi por
    isso que o instalador apareceu torto, encostado na esquerda.
    """
    try:
        import ctypes
        u = ctypes.windll.user32
        u.SetProcessDPIAware()

        # ÁREA ÚTIL (SPI_GETWORKAREA = 0x30): desconta a barra de tarefas. Usando
        # a tela cheia, a borda de baixo da janela — justo onde ficam os botões
        # "Instalar" e "Abrir o Sistema" — nascia atrás da barra.
        class RETANGULO(ctypes.Structure):
            _fields_ = [("esq", ctypes.c_long), ("topo", ctypes.c_long),
                        ("dir", ctypes.c_long), ("base", ctypes.c_long)]
        r = RETANGULO()
        if u.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0):
            x0, y0, lt, at = r.esq, r.topo, r.dir - r.esq, r.base - r.topo
        else:
            x0, y0, lt, at = 0, 0, u.GetSystemMetrics(0), u.GetSystemMetrics(1)

        if lt > 0 and at > 0:
            # trava dentro da área útil: com escala de tela (125%/150%) a conta do
            # centro pode passar da borda, e aí a janela nasce cortada
            x = min(max(x0, x0 + (lt - larg) // 2), max(x0, x0 + lt - larg))
            y = min(max(y0, y0 + (at - alt) // 2), max(y0, y0 + at - alt))
            return x, y
    except Exception:
        pass
    return None, None          # sem saber, deixa o Windows escolher


def pasta_area_de_trabalho():
    """Onde fica a Área de Trabalho DESTE computador.

    Não dá para montar "~/Desktop" na mão: se o micro tiver OneDrive, o
    Windows redireciona a Área de Trabalho para dentro do OneDrive, e o
    atalho iria parar numa pasta que o dono nunca vê. Quem sabe o caminho
    certo é o próprio Windows — então perguntamos a ele.
    """
    try:
        import win32com.client
        p = win32com.client.Dispatch("WScript.Shell").SpecialFolders("Desktop")
        if p and os.path.isdir(p):
            return p
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), "Desktop")      # reserva


def pasta_menu_iniciar():
    try:
        import win32com.client
        p = win32com.client.Dispatch("WScript.Shell").SpecialFolders("Programs")
        if p and os.path.isdir(p):
            return p
    except Exception:
        pass
    return os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")


def fixar_no_iniciar(exe):
    """Fixa o Sistema no menu Iniciar.

    A barra de tarefas NÃO entra aqui: a Microsoft tirou o verbo "Fixar na
    barra de tarefas" a partir do Windows 10, justamente para instalador
    nenhum se enfiar lá sozinho. O que existe por fora são mexidas no
    registro que o Windows 11 confere e desfaz — e que antivírus tratam como
    coisa de programa mal-intencionado. Então fixamos no Iniciar (que é
    permitido) e a tela final ensina o clique para a barra de tarefas.
    """
    try:
        import win32com.client
        pasta = win32com.client.Dispatch("Shell.Application").Namespace(os.path.dirname(exe))
        item = pasta.ParseName(os.path.basename(exe))
        for v in item.Verbs():
            baixo = v.Name.replace("&", "").lower()
            # na SEGUNDA instalação o Windows oferece "Desafixar de Iniciar" —
            # sem este filtro o instalador tirava o que ele mesmo tinha posto
            if any(x in baixo for x in ("desafixar", "unpin", "remover")):
                continue
            if "iniciar" in baixo or "start" in baixo:    # PT e EN
                v.DoIt()
                return True
    except Exception:
        pass
    return False


def atalho(caminho, alvo):
    try:
        import win32com.client
        s = win32com.client.Dispatch("WScript.Shell").CreateShortcut(caminho)
        s.TargetPath = alvo
        s.WorkingDirectory = os.path.dirname(alvo)
        s.IconLocation = alvo + ",0"
        s.Description = "Sistema — projeção da igreja"
        s.Save()
    except Exception:
        pass


def abrir_pasta_dados():
    try: os.startfile(DADOS)
    except Exception: pass


HTML = """<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><title>Instalar o Sistema</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;font-family:'Segoe UI',system-ui,sans-serif;color:#eaf0fb;overflow:hidden;
  background:radial-gradient(ellipse at 50% 30%, #16294a 0%, #0b1526 72%)}
.tudo{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;padding:26px;text-align:center}
h1{font-size:25px;font-weight:800;letter-spacing:.4px}
.sub{font-size:13.5px;color:#8fa8cf;max-width:46ch;line-height:1.6}
.dica{font-size:12.5px;color:#7f96b8;max-width:46ch;line-height:1.6;margin:14px 0 0;
      padding:11px 13px;background:#101d33;border-left:3px solid #e8b93c;border-radius:0 7px 7px 0;text-align:left}
.dica b{color:#cfe0f5}
.barra{width:330px;height:7px;border-radius:6px;background:#1e2d49;overflow:hidden;margin-top:8px}
.barra i{display:block;height:100%;width:0;border-radius:6px;transition:width .35s ease;
  background:linear-gradient(90deg,#a31a1a,#f5d76e)}
.passo{font-size:12.5px;color:#9db3d6;min-height:18px}
.itens{list-style:none;display:flex;flex-direction:column;gap:7px;margin-top:6px;text-align:left}
.itens li{font-size:12.5px;color:#cdd9ee;padding-left:19px;position:relative}
.itens li::before{content:'';position:absolute;left:0;top:6px;width:7px;height:7px;border-radius:50%;background:#f5d76e}
button{font-family:inherit;font-size:14px;font-weight:600;border:none;border-radius:9px;padding:12px 24px;cursor:pointer;color:#fff}
.ok{background:#2e8b57}.ok:hover{background:#37a066}
.sec{background:#1e2d49;border:1px solid #2c3d5c}.sec:hover{background:#26375a}
.linha{display:flex;gap:9px;margin-top:14px;justify-content:center}
.linha.um{margin-top:22px}
.grande{padding:15px 40px;font-size:15px}
.oculto{display:none}
#tela1,#tela2,#tela3{display:flex;flex-direction:column;align-items:center;gap:10px;width:100%}
#tela1.oculto,#tela2.oculto,#tela3.oculto{display:none}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
</style></head><body>
<div class="tudo">
  <div id="marca"></div>
  <h1>Instalar o Sistema</h1>

  <div id="tela1">
    <p class="sub">O Sistema será instalado neste computador e ficará pronto para usar no culto — sem internet e sem depender de mais nada.</p>
    <ul class="itens">
      <li>2.459 louvores da ICM e a Bíblia completa</li>
      <li>Slides de PowerPoint e PDF da Escola Bíblica</li>
      <li>Atalho na Área de Trabalho e no menu Iniciar</li>
      <li>Pastas suas para fundos e apresentações</li>
    </ul>
    <div class="linha"><button class="ok" onclick="comecar()">Instalar</button></div>
  </div>

  <div id="tela2" class="oculto">
    <div class="barra"><i id="preenche"></i></div>
    <p class="passo" id="passo">Preparando…</p>
  </div>

  <div id="tela3" class="oculto">
    <p class="sub">Tudo pronto. O <b>Sistema</b> já está na sua Área de Trabalho e no menu Iniciar.</p>
    <p class="dica">Para deixar ele fixo na barra de tarefas: com o Sistema aberto,
      clique com o <b>botão direito</b> no ícone dele lá embaixo e escolha
      <b>“Fixar na barra de tarefas”</b>.</p>
    <div class="linha um"><button class="ok grande" onclick="abrir()">Abrir o Sistema</button></div>
  </div>
</div>
<script src="icones.js"></script>
<script>
  document.getElementById('marca').innerHTML = (window.Icones && window.Icones.MARCA) ? window.Icones.MARCA(78) : '';
  function comecar(){ tela(2); window.pywebview.api.instalar(); }
  function tela(n){ for(const k of [1,2,3]) document.getElementById('tela'+k).classList.toggle('oculto', k!==n); }
  window.avancar = (pct, txt) => {
    document.getElementById('preenche').style.width = pct + '%';
    document.getElementById('passo').textContent = txt;
    if (pct >= 100) setTimeout(() => tela(3), 500);
  };
  function abrir(){ window.pywebview.api.abrir(); }
  function pastas(){ window.pywebview.api.pastas(); }
  function sair(){ window.pywebview.api.sair(); }
</script></body></html>
"""


class Api:
    def __init__(self):
        self.janela = None
        self.exe = ""

    def instalar(self):
        def tarefa():
            # COM PRECISA ser inicializado nesta thread. Sem isto, as chamadas de
            # atalho e de fixar no Iniciar (WScript.Shell e Shell.Application)
            # travam a janela inteira — o Windows chega a dizer "não está
            # respondendo". A cópia dos arquivos não tem culpa: leva 0,8 segundo.
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pythoncom = None
            def progresso(pct, txt):
                try:
                    self.janela.evaluate_js("window.avancar(%d, %s)" % (pct, repr(txt).replace("'", '"')))
                except Exception:
                    pass
            try:
                self.exe = instalar(progresso)
            except Exception as e:
                progresso(100, "Erro: " + str(e))
            finally:
                if pythoncom:
                    try: pythoncom.CoUninitialize()
                    except Exception: pass
        threading.Thread(target=tarefa, daemon=True).start()
        return True

    def abrir(self):
        try:
            if self.exe and os.path.exists(self.exe):
                subprocess.Popen([self.exe], cwd=os.path.dirname(self.exe),
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            pass
        self.sair()

    def pastas(self):
        abrir_pasta_dados()

    def sair(self):
        try: self.janela.destroy()
        except Exception: pass


def main():
    import webview, tempfile
    api = Api()
    pasta = tempfile.mkdtemp()
    with open(os.path.join(pasta, "instalar.html"), "w", encoding="utf-8") as f:
        f.write(HTML)
    ico = os.path.join(origem(), "icones.js")
    if os.path.exists(ico):
        shutil.copy2(ico, os.path.join(pasta, "icones.js"))
    LARG, ALT = 620, 560
    x, y = centro_da_tela(LARG, ALT)
    api.janela = webview.create_window("Instalar o Sistema", os.path.join(pasta, "instalar.html"),
                                       width=LARG, height=ALT, x=x, y=y, resizable=False,
                                       background_color="#0b1526", js_api=api)
    # a janela já está montada: pode tirar a telinha de carregamento.
    # Sem isto ela ficava na tela para sempre, sobrando por cima do instalador.
    webview.start(fechar_splash, gui="edgechromium")


if __name__ == "__main__":
    main()
