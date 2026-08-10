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


# Esconde a janela preta do console em taskkill/tasklist/powershell.
#
# ESTAVA FALTANDO. Era usado em quatro lugares e nunca definido: toda chamada
# levantava NameError e o "except Exception: pass" engolia sem dizer nada. O
# fechamento automatico do Sistema nunca rodou uma unica vez -- e o sintoma era
# a instalacao falhando em 34 arquivos, que nao tem cara nenhuma de erro de
# nome de variavel.
SEM_JANELA = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


def origem():
    return sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def copiar_por_cima(origem_arq, destino_arq):
    """Copia por cima MESMO com o arquivo em uso.

    O Windows não deixa sobrescrever um .exe ou .dll que algum processo abriu,
    mas deixa RENOMEAR. É por isso que todo instalador de verdade tira o arquivo
    velho do caminho em vez de brigar com ele.

    Fechamos o Sistema antes, e isso resolve o caso normal. Mas o programa vai
    rodar em computador que ninguém aqui viu: antivírus segurando a DLL,
    indexador do Windows lendo a pasta, uma segunda janela de projeção aberta,
    política que proíbe o PowerShell. Em qualquer um desses o fechamento falha
    — e aí o leigo recebe um erro que não sabe resolver, no domingo, com a
    igreja esperando.

    O arquivo velho vira ".apagar-<n>" e some na próxima instalação; se nem
    renomear der, aí sim é erro de verdade (pasta sem permissão, disco cheio).
    """
    try:
        shutil.copy2(origem_arq, destino_arq)
        return
    except (PermissionError, OSError):
        pass
    if not os.path.exists(destino_arq):
        raise
    velho = destino_arq + ".apagar-%d" % int(time.time() % 100000)
    os.replace(destino_arq, velho)          # renomear funciona com o arquivo em uso
    try:
        os.remove(velho)                    # se ninguém mais o segura, some agora
    except Exception:
        pass                                # ainda em uso: fica para a próxima
    shutil.copy2(origem_arq, destino_arq)


def limpar_sobras(pasta):
    """Apaga os restos que ficaram travados numa instalação anterior."""
    n = 0
    for raiz, _, arquivos in os.walk(pasta):
        for a in arquivos:
            if ".apagar-" in a:
                try:
                    os.remove(os.path.join(raiz, a))
                    n += 1
                except Exception:
                    pass
    return n


def instalar(progresso):
    base = origem()
    pacote = os.path.join(base, "programa")          # a pasta do app vai embutida no instalador
    progresso(5, "Preparando…")
    os.makedirs(DESTINO, exist_ok=True)

    progresso(10, "Fechando o Sistema, se estiver aberto…")
    fechar_sistema_aberto()

    limpar_sobras(DESTINO)                 # restos de uma atualização anterior
    progresso(15, "Copiando os arquivos do Sistema…")
    falhas = []
    if os.path.isdir(pacote):
        for raiz, _, arquivos in os.walk(pacote):
            rel = os.path.relpath(raiz, pacote)
            alvo = os.path.join(DESTINO, rel) if rel != "." else DESTINO
            os.makedirs(alvo, exist_ok=True)
            for a in arquivos:
                try:
                    copiar_por_cima(os.path.join(raiz, a), os.path.join(alvo, a))
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

    progresso(93, "Guardando o instalador…")
    guardar_instalador()

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


def guardar_instalador():
    """Leva uma cópia do instalador para dentro da pasta do programa.

    Assim ele não fica largado na Área de Trabalho ou em Downloads, onde um
    irmão mais velho clica sem querer e reinstala tudo do zero no meio da
    semana. Quem precisar dele de verdade acha em "Instalador" dentro dos
    dados do Sistema.
    """
    try:
        atual = os.path.abspath(sys.executable)
        if not atual.lower().endswith(".exe"):
            return ""
        destino = os.path.join(DADOS, "Instalador")
        os.makedirs(destino, exist_ok=True)
        copia = os.path.join(destino, os.path.basename(atual))
        if os.path.abspath(copia).lower() != atual.lower():
            shutil.copy2(atual, copia)
        return copia
    except Exception:
        return ""


def _sistema32(programa):
    """Caminho completo de um utilitario do Windows.

    Chamar so "taskkill" depende do PATH, e num .exe compilado rodando em
    computador alheio o PATH pode nao ter o System32 -- o comando simplesmente
    nao e' encontrado, a excecao e' engolida, e o Sistema segue aberto. Foi isso
    que fez o fechamento automatico nao acontecer, mesmo o taskkill funcionando
    perfeitamente quando digitado a mao.
    """
    raiz = os.environ.get("SystemRoot") or r"C:\Windows"
    caminho = os.path.join(raiz, "System32", programa)
    return caminho if os.path.exists(caminho) else programa


def fechar_sistema_aberto(espera=6.0):
    """Fecha o Sistema se ele estiver rodando.

    Atualizar por cima com o programa aberto é o caso NORMAL — o operador clica
    no instalador com o Sistema na tela. E o Windows não deixa sobrescrever um
    .exe em uso: a cópia falhava arquivo por arquivo e a versão velha continuava.
    Pedimos para fechar com jeito primeiro; só insistimos se ele não sair.
    """
    # Quem clicou em instalar JÁ decidiu: fecha na hora, sem pedir licença nem
    # esperar. O pedido gentil ia primeiro, mas o Sistema podia estar com uma
    # janela de projeção aberta e não sair — e a instalação ficava pendurada.
    tk = _sistema32("taskkill.exe")
    for args in ([tk, "/IM", "Sistema.exe"],
                 [tk, "/F", "/IM", "Sistema.exe"]):
        try:
            subprocess.run(args, capture_output=True, timeout=8, **SEM_JANELA)
        except Exception:
            pass
        time.sleep(0.4)
    # O MOTOR DO EDGE NAO MORRE COM O PAI. O Sistema desenha a tela com o
    # WebView2, que roda em processos SEPARADOS (msedgewebview2.exe). Matar o
    # Sistema.exe deixa esses filhos vivos, e sao ELES que seguram as 34 DLLs da
    # pasta _internal -- a instalacao falhava inteira com o Sistema ja fechado,
    # e o usuario leigo nao tinha como adivinhar o que fazer.
    #
    # So os NOSSOS: a maquina tem outros WebView2 (o Teams usa 25 deles). O
    # filtro e' a linha de comando, que carrega o nome do exe dono e a pasta de
    # dados. Matar todos fecharia o Teams do usuario no meio da instalacao.
    matar_webview()

    fim = time.time() + espera
    while time.time() < fim:
        try:
            r = subprocess.run([_sistema32("tasklist.exe"), "/FI", "IMAGENAME eq Sistema.exe", "/NH"],
                               capture_output=True, timeout=10, text=True, **SEM_JANELA)
            if "Sistema.exe" not in (r.stdout or ""):
                return True
        except Exception:
            return True
        time.sleep(0.4)
    try:                                   # não saiu com jeito: encerra mesmo
        subprocess.run([tk, "/F", "/IM", "Sistema.exe"],
                       capture_output=True, timeout=10, **SEM_JANELA)
        time.sleep(0.6)
    except Exception:
        pass
    return True


def matar_webview():
    """Encerra so os processos do motor do Edge que pertencem ao Sistema."""
    consulta = (
        r"Get-CimInstance Win32_Process -Filter ""Name='msedgewebview2.exe'"" | "
        r"Where-Object { $_.CommandLine -like '*Sistema.exe*' -or "
        r"$_.CommandLine -like '*\Programs\Sistema*' -or "
        r"$_.CommandLine -like '*Sistema Projecao*' } | "
        r"ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }")
    try:
        ps = os.path.join(os.environ.get("SystemRoot") or r"C:\Windows",
                          "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        subprocess.run([ps if os.path.exists(ps) else "powershell",
                        "-NoProfile", "-NonInteractive", "-Command", consulta],
                       capture_output=True, timeout=20, **SEM_JANELA)
    except Exception:
        pass
    time.sleep(0.8)


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
  function comecar(){ tela(2); acompanhar(); window.pywebview.api.instalar(); }
  function tela(n){ for(const k of [1,2,3]) document.getElementById('tela'+k).classList.toggle('oculto', k!==n); }
  // A TELA vem buscar o progresso. O caminho contrario (Python empurrando para
  // a tela de outra thread) travava o instalador em "Preparando..." para sempre.
  let relogio = null;
  function acompanhar(){
    if (relogio) return;
    relogio = setInterval(async () => {
      try {
        const d = await window.pywebview.api.progresso();
        document.getElementById('preenche').style.width = (d.pct || 0) + '%';
        document.getElementById('passo').textContent = d.txt || '';
        if (d.fim) {
          clearInterval(relogio); relogio = null;
          document.getElementById('preenche').style.width = '100%';
          setTimeout(() => tela(d.exe ? 3 : 2), 400);
        }
      } catch (e) {}
    }, 200);
  }
  function abrir(){ window.pywebview.api.abrir(); }
  function pastas(){ window.pywebview.api.pastas(); }
  function sair(){ window.pywebview.api.sair(); }
</script></body></html>
"""


class Api:
    def __init__(self):
        self.janela = None
        self.exe = ""
        self.estado = {"pct": 0, "txt": ""}
        self.terminou = False

    def progresso(self):
        """A tela chama isto de tempo em tempo. Chamada JS -> Python é segura;
        o contrário (Python -> JS de outra thread) trava."""
        d = dict(self.estado)
        d["fim"] = self.terminou
        d["exe"] = bool(self.exe)
        return d

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
                # SÓ guarda. Antes isto chamava evaluate_js daqui, de uma thread
                # de trabalho: o Python esperava a thread da janela, a janela
                # esperava a resposta, e o instalador congelava em "Preparando…"
                # para sempre. Agora a TELA é que vem buscar (ver progresso()).
                self.estado = {"pct": pct, "txt": txt}
            try:
                self.exe = instalar(progresso)
            except Exception as e:
                progresso(100, "Erro: " + str(e))
            finally:
                self.terminou = True
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


def main_silencioso():
    """Instala sem abrir janela. Serve para conferir a instalação de verdade e
    para instalar em vários computadores da igreja sem ficar clicando."""
    def p(pct, txt):
        print("  %3d%%  %s" % (pct, txt))
        sys.stdout.flush()
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass
    exe = instalar(p)
    print("instalado em: %s" % exe)
    # --reabrir: quem chamou foi o botão "Buscar atualizações" de dentro do
    # Sistema — o programa foi fechado para atualizar, e o operador está
    # esperando ele voltar sozinho.
    if "--reabrir" in sys.argv and exe and os.path.exists(exe):
        try:
            subprocess.Popen([exe], cwd=os.path.dirname(exe), **SEM_JANELA)
        except Exception:
            pass
    return 0


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
    if "--silencioso" in sys.argv:
        sys.exit(main_silencioso())
    main()
