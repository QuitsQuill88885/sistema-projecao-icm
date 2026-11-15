# -*- coding: utf-8 -*-
r"""O "Instalar-o-Sistema.exe" do Sistema 4.0 (o Nativo), 08/11/2026. É o arquivo que a 3.0.12/3.0.13 já baixam no botão
Atualizar (releases/latest/download/Instalar-o-Sistema.exe) e rodam com "--silencioso --reabrir"; o 4.0 baixa o mesmo.

O que faz, nesta ordem:
  1. ESPERA o Sistema que chamou fechar SOZINHO (a 3.0.x sai 3 s depois de o instalador subir; o 4.0 também). Nunca mata
     processo: confere se o .exe ainda está preso (um programa aberto não deixa abrir o próprio .exe para escrita).
  2. Instala o 4.0 em Programs\Sistema Nativo pelo instalador_nativo (copia conferindo md5, limpa só o que era do pacote
     anterior e continua igual, Firewall, instalacao.json).
  3. TROCA OS ATALHOS: o atalho "Sistema" que apontava para a 3.0.x (Programs\Sistema\Sistema.exe), na Área de Trabalho e
     no menu Iniciar, passa a abrir o 4.0, com o mesmo nome e no mesmo lugar (o operador não procura ícone novo). Só mexe
     em atalho que aponta para DENTRO da pasta da 3.0.x (a regra do limpar_atalhos_antigos dela). Anota o alvo antigo no
     instalacao.json (o Desinstalar pode devolver). A pasta da 3.0.x fica INTACTA: é o caminho de volta.
  4. Os DADOS (configurações, louvores, fundos, %APPDATA%\Sistema Projecao) não são tocados: o 4.0 lê a mesma pasta.
  5. --reabrir: abre o Sistema instalado no fim.
O pacote: SistemaNativo.zip dentro do .exe (PyInstaller --onefile, em _MEIPASS) ou --pacote <zip ou pasta> (provas).
Desvios das provas: os do instalador_nativo (NATIVO_PROG, NATIVO_ATALHO_DESK/MENU, NATIVO_NETSH_ENSAIO) e NATIVO_PROG_312
(a pasta da 3.0.x). Log: instalar_o_sistema.log ao lado do programa instalado."""
import json, os, shutil, subprocess, sys, tempfile, threading, time, zipfile

AQUI = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))     # o atualizador.py (fora do .exe)
import instalador_nativo as I
try:
    from atualizador import VERSAO                   # o número do 4.0 que ESTE instalador carrega
except Exception:
    VERSAO = "4.0.0"

SEM_JANELA = {"creationflags": 0x08000000} if os.name == "nt" else {}
LOG = []


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    LOG.append(s)
    try:
        print(s, flush=True)          # o .exe sem console (a 3.0.x o roda escondido) não tem onde imprimir
    except Exception:
        pass


def pasta_312():
    return os.environ.get("NATIVO_PROG_312") or os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Programs", "Sistema")


def preso(exe):
    """O .exe está aberto? Um programa rodando não deixa abrir o próprio .exe para escrita (o Windows nega)."""
    if not os.path.exists(exe):
        return False
    try:
        with open(exe, "r+b"):
            return False
    except OSError:
        return True


def esperar_fechar(exes, limite=120):
    """Espera os .exe soltarem (o Sistema que chamou sai sozinho). Devolve os que continuaram presos."""
    fim = time.time() + limite
    presos = [e for e in exes if preso(e)]
    if presos:
        log("esperando fechar:", presos)
    while presos and time.time() < fim:
        time.sleep(0.5)
        presos = [e for e in presos if preso(e)]
    return presos


def pacote(args):
    if os.environ.get("NATIVO_PACOTE_ENSAIO"):                 # provas: o mesmo .exe instala outro pacote (o 4.0.1)
        return os.environ["NATIVO_PACOTE_ENSAIO"]
    if "--pacote" in args:
        return args[args.index("--pacote") + 1]
    dentro = os.path.join(AQUI, "SistemaNativo.zip")
    # 12/11/2026, o INSTALADOR COMPLETO (~1 GB): o zip vai COLADO no fim do próprio .exe (não dentro do PyInstaller, que
    # o copiaria inteiro para a pasta temporária antes de começar). O zip se lê do próprio arquivo.
    if not os.path.exists(dentro) and getattr(sys, "frozen", False) and zipfile.is_zipfile(sys.executable):
        return sys.executable
    return dentro


def abrir_pacote(p):
    """Pasta do pacote pronta para o instalador (o zip é aberto numa pasta temporária)."""
    if os.path.isdir(p):
        return p, None
    tmp = tempfile.mkdtemp(prefix="SistemaNativo_")
    with zipfile.ZipFile(p) as z:
        z.extractall(tmp)
    dentro = [d for d in os.listdir(tmp) if os.path.isdir(os.path.join(tmp, d))]
    raiz = os.path.join(tmp, dentro[0]) if len(dentro) == 1 and not os.path.exists(os.path.join(tmp, I.EXE)) else tmp
    return raiz, tmp


_PS_LER = ("$sh = New-Object -ComObject WScript.Shell; Get-ChildItem -LiteralPath $env:PASTA_LNK -Filter *.lnk | "
           "ForEach-Object { $_.FullName + '|' + $sh.CreateShortcut($_.FullName).TargetPath }")


def alvos_dos_atalhos(pasta):
    """{caminho do .lnk: alvo} de uma pasta (um PowerShell só para a pasta inteira)."""
    if not pasta or not os.path.isdir(pasta):
        return {}
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_LER], capture_output=True, text=True,
                       env=dict(os.environ, PASTA_LNK=pasta), timeout=60, **SEM_JANELA)
    out = {}
    for l in (r.stdout or "").splitlines():
        if "|" in l:
            a, b = l.split("|", 1)
            out[a.strip()] = b.strip()
    return out


def trocar_atalhos(exe_novo, dest_novo, criados):
    """O atalho que abria a 3.0.x passa a abrir o 4.0 (mesmo nome, mesmo lugar). Havendo troca numa pasta, o atalho
    "Sistema Nativo" que o instalador acabou de pôr nela sai (nada de dois ícones do Sistema)."""
    velho = os.path.normcase(os.path.abspath(pasta_312())) + os.sep
    trocados, tirados = {}, []
    for pasta in (I.pasta_desktop(), I.pasta_menu()):
        achados = {lnk: alvo for lnk, alvo in alvos_dos_atalhos(pasta).items()
                   if alvo and os.path.normcase(os.path.abspath(alvo)).startswith(velho)}
        for lnk, alvo in achados.items():
            if I.atalho(lnk, exe_novo, dest_novo):
                trocados[lnk] = alvo
                log("atalho trocado:", lnk, "(era", alvo + ")")
        if achados:
            for c in list(criados):
                if os.path.normcase(os.path.dirname(c)) == os.path.normcase(pasta) and c not in achados:
                    try:
                        os.remove(c); criados.remove(c); tirados.append(c)
                    except OSError:
                        pass
    return trocados, tirados


def versao_instalada():
    """A versão que já está no micro: o 4.0 anota no instalacao.json; a 3.0.x se lê no .exe (como o instalador dela)."""
    try:
        v = json.load(open(os.path.join(I.pasta_programa(), "instalacao.json"), encoding="utf-8")).get("versao")
        if v:
            return v
    except Exception:
        pass
    exe = os.path.join(pasta_312(), "Sistema.exe")
    if not os.path.exists(exe):
        return None
    try:
        import win32api
        info = win32api.GetFileVersionInfo(exe, "\\")
        ms, ls = info["FileVersionMS"], info["FileVersionLS"]
        return "%d.%d.%d" % (ms >> 16, ms & 0xFFFF, ls >> 16)
    except Exception:
        return "?"


def instalar_tudo(andamento, reabrir=False):
    """O serviço inteiro, com o andamento (pct, frase) para a janela. Devolve o .exe instalado ("" se não instalou)."""
    dest = I.pasta_programa()
    exe_novo = os.path.join(dest, I.EXE)
    andamento(5, "Esperando o Sistema fechar…")
    presos = esperar_fechar([exe_novo, os.path.join(pasta_312(), "Sistema.exe")])
    if presos:
        log("ERRO: o Sistema não fechou em 2 minutos:", presos)
        andamento(100, "Erro: o Sistema não fechou. Feche o Sistema e rode o instalador de novo.")
        return ""
    andamento(15, "Abrindo o pacote…")
    raiz, tmp = abrir_pacote(pacote(sys.argv[1:]))
    try:
        andamento(40, "Copiando o programa…")
        r = I.instalar(raiz)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    log("instalado:", json.dumps({k: r[k] for k in ("copiados", "iguais", "tirados", "no pacote")}, ensure_ascii=False))
    andamento(85, "Criando os atalhos…")
    criados = list(r.get("atalhos") or [])
    trocados, tirados = trocar_atalhos(exe_novo, dest, criados)
    andamento(95, "Guardando…")
    reg_arq = os.path.join(dest, "instalacao.json")
    reg = json.load(open(reg_arq, encoding="utf-8"))
    reg["versao"] = VERSAO
    reg["atalhos"] = criados + [l for l in trocados if l not in criados]
    reg["atalhos_da_312"] = {**(reg.get("atalhos_da_312") or {}), **trocados}
    with open(reg_arq, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)
    andamento(100, "Pronto.")
    if reabrir:
        reabrir_sistema(exe_novo)
    return exe_novo


def reabrir_sistema(exe):
    if exe and os.path.exists(exe):
        subprocess.Popen([exe], cwd=os.path.dirname(exe), close_fds=True,
                         creationflags=(0x00000008 | 0x00000200) if os.name == "nt" else 0)    # DETACHED | NOVO GRUPO
        log("reaberto:", exe)


def centro_da_tela(larg, alt):
    try:
        import ctypes
        u = ctypes.windll.user32
        return (u.GetSystemMetrics(0) - larg) // 2, (u.GetSystemMetrics(1) - alt) // 2
    except Exception:
        return None, None


def janela(atualizando):
    """A JANELA da 3.0.x (o main() do instalador.py dela), linha por linha: as mesmas três telas, cores, letras e frases.
    --reabrir = quem chamou foi o Atualizar de dentro do Sistema e há uma pessoa olhando: vai direto ao progresso, por
    cima de tudo, com o relógio andando, e no fim reabre o Sistema sozinho (2,5 s depois do "Pronto!")."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        return 0 if instalar_tudo(lambda p, x: None, reabrir=atualizando) else 1
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
    FUNDO = "#0b1526"
    OURO = "#f5d76e"
    CINZA = "#8fa8cf"
    VERDE = "#2e8b57"
    BRANCO = "#eaf0fb"
    AZUL_ESC = "#1e2d49"
    root = tk.Tk()
    root.title("Atualizar o Sistema" if atualizando else "Instalar o Sistema")
    root.resizable(False, False)
    root.configure(bg=FUNDO)
    ico = os.path.join(AQUI, "sistema.ico")
    if os.path.exists(ico):
        try: root.iconbitmap(ico)
        except Exception: pass
    LARG, ALT = 500, 440
    x, y = centro_da_tela(LARG, ALT)
    root.geometry("%dx%d+%d+%d" % (LARG, ALT, x, y) if x is not None else "%dx%d" % (LARG, ALT))
    try:
        style = ttk.Style(root)
        style.theme_use("default")
        style.configure("S.Horizontal.TProgressbar", troughcolor=AZUL_ESC, background=OURO, thickness=8, borderwidth=0)
    except Exception:
        pass
    ja_instalada = versao_instalada()
    nova = VERSAO

    # ---- Tela 1: início
    f1 = tk.Frame(root, bg=FUNDO, padx=44, pady=18)
    marca = tk.Canvas(f1, width=72, height=80, bg=FUNDO, highlightthickness=0)
    marca.pack(pady=(4, 2))
    marca.create_oval(4, 10, 68, 74, fill="#0d1f3c", outline="#2d5080", width=2)
    marca.create_text(36, 42, text="S", font=("Segoe UI", 34, "bold"), fill=OURO)
    tk.Label(f1, text="Sistema", font=("Segoe UI", 22, "bold"), bg=FUNDO, fg=BRANCO).pack(pady=(2, 0))
    tk.Label(f1, text="Projeção da Igreja Cristã Maranata", font=("Segoe UI", 10), bg=FUNDO, fg=CINZA).pack()
    tk.Frame(f1, height=1, bg="#1e3050").pack(fill="x", pady=(12, 0))
    if ja_instalada:
        igual = (ja_instalada == nova)
        if igual:
            msg = "Você já está com a versão %s, que é esta mesma. Instalar de novo só repõe os arquivos." % ja_instalada
        elif ja_instalada != "?":
            msg = "Você já tem a versão %s. Isto vai atualizar para a %s." % (ja_instalada, nova)
        else:
            msg = "Você já tem o Sistema instalado. Isto vai atualizar para a %s." % nova
        fbox = tk.Frame(f1, bg="#2a2313", bd=1, relief="solid")
        fbox.pack(fill="x", pady=(14, 0))
        tk.Label(fbox, text=msg, font=("Segoe UI", 10), bg="#2a2313", fg=OURO, wraplength=390, justify="center",
                 padx=10, pady=8).pack()
    else:
        tk.Label(f1, text="O Sistema será instalado neste computador,\npronto para usar no culto — sem internet.",
                 font=("Segoe UI", 10), bg=FUNDO, fg=CINZA, wraplength=400, justify="center").pack(pady=(12, 0))
    tk.Label(f1, text="Seus dados, fundos e configurações não são apagados.", font=("Segoe UI", 10), bg=FUNDO, fg=CINZA,
             wraplength=400).pack(pady=(8, 0))
    btn_txt = "Reinstalar" if ja_instalada and ja_instalada == nova else ("Atualizar" if ja_instalada else "Instalar")
    btn = tk.Button(f1, text=btn_txt, font=("Segoe UI", 13, "bold"), bg=VERDE, fg="white", relief="flat", padx=24, pady=10,
                    cursor="hand2", activebackground="#37a066", activeforeground="white", bd=0)
    btn.pack(pady=(22, 0))

    # ---- Tela 2: progresso
    f2 = tk.Frame(root, bg=FUNDO, padx=44, pady=50)
    tk.Label(f2, text="Atualizando o Sistema…" if atualizando else "Instalando o Sistema…",
             font=("Segoe UI", 16, "bold"), bg=FUNDO, fg=BRANCO).pack(pady=(0, 24))
    try:
        pbar = ttk.Progressbar(f2, style="S.Horizontal.TProgressbar", length=400, mode="determinate")
    except Exception:
        pbar = ttk.Progressbar(f2, length=400, mode="determinate")
    pbar.pack()
    passo_var = tk.StringVar(value="Preparando…")
    tk.Label(f2, textvariable=passo_var, font=("Segoe UI", 10), bg=FUNDO, fg=CINZA).pack(pady=(10, 0))
    relogio_var = tk.StringVar(value="")              # toda espera tem contagem visível (regra da casa)
    tk.Label(f2, textvariable=relogio_var, font=("Segoe UI", 10), bg=FUNDO, fg=CINZA).pack(pady=(4, 0))
    if atualizando:
        tk.Label(f2, text="Não feche esta janela e não abra o Sistema.\nEle reabre sozinho quando terminar.",
                 font=("Segoe UI", 11, "bold"), bg=FUNDO, fg=OURO, justify="center").pack(pady=(18, 0))

    # ---- Tela 3: pronto
    f3 = tk.Frame(root, bg=FUNDO, padx=44, pady=28)
    tk.Label(f3, text="Pronto!", font=("Segoe UI", 26, "bold"), bg=FUNDO, fg=BRANCO).pack(pady=(0, 4))
    tk.Label(f3, text="O Sistema está na Área de Trabalho e no menu Iniciar.", font=("Segoe UI", 11), bg=FUNDO, fg=CINZA,
             wraplength=400).pack()
    fdica = tk.Frame(f3, bg="#101d33")
    fdica.pack(fill="x", pady=(16, 0))
    tk.Label(fdica, text='Para fixar na barra de tarefas: com o Sistema aberto,\nclique com o botão direito no ícone e escolha\n'
                         '"Fixar na barra de tarefas".',
             font=("Segoe UI", 10), bg="#101d33", fg=CINZA, padx=14, pady=10, justify="left", wraplength=390).pack(anchor="w")
    exe_path = [""]

    def abrir_e_fechar():
        reabrir_sistema(exe_path[0])
        root.destroy()

    tk.Button(f3, text="Abrir o Sistema", font=("Segoe UI", 13, "bold"), bg=VERDE, fg="white", relief="flat", padx=24,
              pady=10, cursor="hand2", activebackground="#37a066", activeforeground="white", bd=0,
              command=abrir_e_fechar).pack(pady=(22, 0))

    def mostrar(f):
        for fr in (f1, f2, f3):
            fr.pack_forget()
        f.pack(fill="both", expand=True)
    estado = {"pct": 0, "txt": "Preparando…", "fim": False}

    def atualizar(pct, txt):
        estado["pct"] = pct
        estado["txt"] = txt
    comeco = [time.time()]

    def verificar():
        pbar["value"] = estado["pct"]
        passo_var.set(estado["txt"])
        relogio_var.set("%d s" % int(time.time() - comeco[0]))
        if estado["fim"]:
            if exe_path[0]:
                mostrar(f3)
                if atualizando:
                    root.after(2500, abrir_e_fechar)
        else:
            root.after(150, verificar)

    def iniciar():
        btn.config(state="disabled")
        comeco[0] = time.time()
        mostrar(f2)

        def tarefa():
            atualizar(2, "Iniciando…")
            try:
                exe_path[0] = instalar_tudo(atualizar)
            except Exception as e:
                log("ERRO:", repr(e))
                atualizar(100, "Erro: " + str(e))
            finally:
                estado["fim"] = True
        threading.Thread(target=tarefa, daemon=True).start()
        root.after(150, verificar)

    btn.config(command=iniciar)
    if atualizando:
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        root.after(200, iniciar)
    else:
        mostrar(f1)
    root.mainloop()
    return 0 if exe_path[0] else 1


def principal(args):
    """--reabrir (o Atualizar de dentro do Sistema): a janela de progresso APARECE, mesmo com --silencioso junto (a 3.0.x
    manda os dois; a regra é a dela). Só --silencioso: sem janela. Sem nada: a janela com o botão Instalar."""
    if "--reabrir" in args:
        return janela(atualizando=True)
    if "--silencioso" in args:
        return 0 if instalar_tudo(lambda p, x: None) else 1
    return janela(atualizando=False)


if __name__ == "__main__":
    try:
        cod = principal(sys.argv[1:])
    except Exception as e:
        log("ERRO:", repr(e)); cod = 1
    try:
        with open(os.path.join(I.pasta_programa(), "instalar_o_sistema.log"), "a", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n")
    except OSError:
        pass
    sys.exit(cod)
