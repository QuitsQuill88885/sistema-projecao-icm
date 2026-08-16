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
            novo = os.path.join(pasta, NOME + ".lnk")
            limpar_atalhos_antigos(pasta, menos=novo)   # nada de dois ícones do Sistema
            atalho(novo, exe)

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
    animações das CIAS e as cifras, que são pesadas demais para viajar dentro
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
    # ATENÇÃO: NÃO usar '*Sistema.exe*' aqui — 'Instalar o Sistema.exe' também
    # contém essa substring e o filtro mataria o WebView do PRÓPRIO instalador,
    # travando a janela logo depois do clique em "Instalar".
    # Os dois filtros abaixo bastam: cobrem a pasta do programa instalado e a
    # pasta de dados do usuário, sem riscos de colateral.
    consulta = (
        r"Get-CimInstance Win32_Process -Filter ""Name='msedgewebview2.exe'"" | "
        r"Where-Object { $_.CommandLine -like '*\Programs\Sistema*' -or "
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


def limpar_atalhos_antigos(pasta, menos=None):
    """Tira da pasta o atalho de uma instalação anterior, antes de pôr o novo.

    Reescrever o .lnk de mesmo nome já funcionava; o que sobrava era o atalho de
    um nome ANTIGO, apontando para um exe que não existe mais. Ficavam dois
    ícones do Sistema na área de trabalho e um deles não abria nada. Só mexe no
    que é comprovadamente nosso: o atalho tem que apontar para dentro da pasta
    onde o Sistema mora. Atalho de outro programa não é tocado nunca.
    """
    tirados = 0
    try:
        import win32com.client
        sh = win32com.client.Dispatch("WScript.Shell")
        alvo_nosso = os.path.normcase(os.path.abspath(DESTINO))
        for a in os.listdir(pasta):
            if not a.lower().endswith(".lnk"):
                continue
            p = os.path.join(pasta, a)
            if menos and os.path.normcase(p) == os.path.normcase(menos):
                continue
            try:
                t = sh.CreateShortcut(p).TargetPath or ""
            except Exception:
                continue
            if os.path.normcase(os.path.abspath(t)).startswith(alvo_nosso):
                try:
                    os.remove(p)
                    tirados += 1
                except Exception:
                    pass
    except Exception:
        pass
    return tirados


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


def versao_do_pacote():
    """A versão que ESTE instalador carrega dentro dele."""
    exe = os.path.join(origem(), "programa", "Sistema.exe")
    if not os.path.exists(exe):
        return "?"
    try:
        import win32api
        info = win32api.GetFileVersionInfo(exe, "\\")
        ms, ls = info["FileVersionMS"], info["FileVersionLS"]
        return "%d.%d.%d" % (ms >> 16, ms & 0xFFFF, ls >> 16)
    except Exception:
        return "?"


def versao_instalada():
    """Que versão já está no micro, se houver. Serve para o instalador dizer o
    que vai fazer em vez de deixar o usuário no escuro — ele pode ter clicado
    duas vezes sem querer, ou estar reinstalando de propósito."""
    exe = os.path.join(DESTINO, "Sistema.exe")
    if not os.path.exists(exe):
        return None
    try:
        import win32api
        info = win32api.GetFileVersionInfo(exe, "\\")
        ms, ls = info["FileVersionMS"], info["FileVersionLS"]
        return "%d.%d.%d" % (ms >> 16, ms & 0xFFFF, ls >> 16)
    except Exception:
        return "?"


def abrir_pasta_dados():
    try: os.startfile(DADOS)
    except Exception: pass


def main_silencioso():
    """Instala sem abrir janela. Serve para conferir a instalação de verdade e
    para instalar em vários computadores da igreja sem ficar clicando."""
    # chamado pelo "completo" de um arquivo só, NÃO existe console nenhum:
    # sys.stdout é None e um print desprotegido derruba a instalação inteira
    # (aconteceu: AttributeError no flush, com janela de erro na cara do
    # usuário). Escrever no console é cortesia; instalar é a obrigação.
    def p(pct, txt):
        if not sys.stdout:
            return
        try:
            print("  %3d%%  %s" % (pct, txt))
            sys.stdout.flush()
        except Exception:
            pass
    # a telinha de carregamento abre sozinha com o .exe; no modo silencioso
    # ninguém a fechava e ela ficava pendurada na tela até o fim
    fechar_splash()
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass
    exe = instalar(p)
    p(100, "instalado")
    if sys.stdout:
        try:
            print("instalado em: %s" % exe)
        except Exception:
            pass
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
    # Interface em tkinter — sem dependência de WebView2.
    # O WebView2 era o motor do instalador antes, mas tinha inicialização lenta
    # e corrupção do diretório de dados entre execuções. Tkinter está embutido
    # no Python e não precisa de nada externo.
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        main_silencioso()
        return

    fechar_splash()

    FUNDO = "#0b1526"
    OURO  = "#f5d76e"
    CINZA = "#8fa8cf"
    VERDE = "#2e8b57"
    BRANCO = "#eaf0fb"
    AZUL_ESC = "#1e2d49"

    root = tk.Tk()
    root.title("Instalar o Sistema")
    root.resizable(False, False)
    root.configure(bg=FUNDO)
    ico = os.path.join(origem(), "sistema.ico")
    if os.path.exists(ico):
        try: root.iconbitmap(ico)
        except Exception: pass

    LARG, ALT = 500, 440
    x, y = centro_da_tela(LARG, ALT)
    if x is not None:
        root.geometry("%dx%d+%d+%d" % (LARG, ALT, x, y))
    else:
        root.geometry("%dx%d" % (LARG, ALT))

    try:
        style = ttk.Style(root)
        style.theme_use("default")
        style.configure("S.Horizontal.TProgressbar",
                        troughcolor=AZUL_ESC, background=OURO,
                        thickness=8, borderwidth=0)
    except Exception:
        pass

    ja_instalada = versao_instalada()
    nova = versao_do_pacote()

    # ---- Tela 1: início ----
    f1 = tk.Frame(root, bg=FUNDO, padx=44, pady=28)
    tk.Label(f1, text="Sistema", font=("Segoe UI", 26, "bold"),
             bg=FUNDO, fg=BRANCO).pack(pady=(0, 2))
    tk.Label(f1, text="Projeção da Igreja Cristã Maranata",
             font=("Segoe UI", 11), bg=FUNDO, fg=CINZA).pack()

    if ja_instalada:
        igual = (ja_instalada == nova)
        sabeNova = nova and nova != "?"
        if igual:
            msg = ("Você já está com a versão %s, que é esta mesma. "
                   "Instalar de novo só repõe os arquivos." % ja_instalada)
        elif sabeNova:
            msg = ("Você já tem a versão %s. "
                   "Isto vai atualizar para a %s." % (ja_instalada, nova))
        else:
            msg = ("Você já tem o Sistema instalado (versão %s). "
                   "Isto vai repor os arquivos do programa." % ja_instalada)
        fbox = tk.Frame(f1, bg="#2a2313", bd=1, relief="solid")
        fbox.pack(fill="x", pady=(14, 0))
        tk.Label(fbox, text=msg, font=("Segoe UI", 10), bg="#2a2313", fg=OURO,
                 wraplength=390, justify="center", padx=10, pady=8).pack()
    else:
        tk.Label(f1,
                 text="O Sistema será instalado neste computador,\n"
                      "pronto para usar no culto — sem internet.",
                 font=("Segoe UI", 10), bg=FUNDO, fg=CINZA,
                 wraplength=400, justify="center").pack(pady=(12, 0))

    tk.Label(f1, text="Seus dados, fundos e configurações não são apagados.",
             font=("Segoe UI", 10), bg=FUNDO, fg=CINZA,
             wraplength=400).pack(pady=(8, 0))

    if ja_instalada and ja_instalada == nova:
        btn_txt = "Reinstalar"
    elif ja_instalada:
        btn_txt = "Atualizar"
    else:
        btn_txt = "Instalar"

    btn = tk.Button(f1, text=btn_txt, font=("Segoe UI", 13, "bold"),
                    bg=VERDE, fg="white", relief="flat", padx=24, pady=10,
                    cursor="hand2", activebackground="#37a066",
                    activeforeground="white", bd=0)
    btn.pack(pady=(22, 0))

    # ---- Tela 2: progresso ----
    f2 = tk.Frame(root, bg=FUNDO, padx=44, pady=50)
    tk.Label(f2, text="Instalando o Sistema…", font=("Segoe UI", 16, "bold"),
             bg=FUNDO, fg=BRANCO).pack(pady=(0, 24))
    try:
        pbar = ttk.Progressbar(f2, style="S.Horizontal.TProgressbar",
                                length=400, mode="determinate")
    except Exception:
        pbar = ttk.Progressbar(f2, length=400, mode="determinate")
    pbar.pack()
    passo_var = tk.StringVar(value="Preparando…")
    tk.Label(f2, textvariable=passo_var, font=("Segoe UI", 10),
             bg=FUNDO, fg=CINZA).pack(pady=(10, 0))

    # ---- Tela 3: pronto ----
    f3 = tk.Frame(root, bg=FUNDO, padx=44, pady=28)
    tk.Label(f3, text="Pronto!", font=("Segoe UI", 26, "bold"),
             bg=FUNDO, fg=BRANCO).pack(pady=(0, 4))
    tk.Label(f3, text="O Sistema está na Área de Trabalho e no menu Iniciar.",
             font=("Segoe UI", 11), bg=FUNDO, fg=CINZA, wraplength=400).pack()
    fdica = tk.Frame(f3, bg="#101d33")
    fdica.pack(fill="x", pady=(16, 0))
    tk.Label(fdica,
             text='Para fixar na barra de tarefas: com o Sistema aberto,\n'
                  'clique com o botão direito no ícone e escolha\n'
                  '"Fixar na barra de tarefas".',
             font=("Segoe UI", 10), bg="#101d33", fg=CINZA,
             padx=14, pady=10, justify="left", wraplength=390).pack(anchor="w")

    exe_path = [""]

    def abrir_e_fechar():
        p = exe_path[0]
        if p and os.path.exists(p):
            try:
                subprocess.Popen([p], cwd=os.path.dirname(p),
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except Exception:
                pass
        root.destroy()

    tk.Button(f3, text="Abrir o Sistema", font=("Segoe UI", 13, "bold"),
              bg=VERDE, fg="white", relief="flat", padx=24, pady=10,
              cursor="hand2", activebackground="#37a066", activeforeground="white",
              bd=0, command=abrir_e_fechar).pack(pady=(22, 0))

    # ---- Troca de telas ----
    def mostrar(f):
        for fr in (f1, f2, f3):
            fr.pack_forget()
        f.pack(fill="both", expand=True)

    # ---- Lógica ----
    estado = {"pct": 0, "txt": "Preparando…", "fim": False}

    def atualizar(pct, txt):
        estado["pct"] = pct
        estado["txt"] = txt

    def verificar():
        pbar["value"] = estado["pct"]
        passo_var.set(estado["txt"])
        if estado["fim"]:
            if exe_path[0]:
                mostrar(f3)
            # sem exe_path: fica em f2 mostrando o erro no passo_var
        else:
            root.after(150, verificar)

    def iniciar():
        btn.config(state="disabled")
        mostrar(f2)

        def tarefa():
            atualizar(2, "Iniciando…")
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception:
                pass
            try:
                exe_path[0] = instalar(atualizar)
            except Exception as e:
                atualizar(100, "Erro: " + str(e))
            finally:
                estado["fim"] = True

        threading.Thread(target=tarefa, daemon=True).start()
        root.after(150, verificar)

    btn.config(command=iniciar)
    mostrar(f1)
    root.mainloop()


if __name__ == "__main__":
    if "--silencioso" in sys.argv:
        sys.exit(main_silencioso())
    main()
