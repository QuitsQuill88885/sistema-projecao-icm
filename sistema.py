# -*- coding: utf-8 -*-
"""Sistema — projeção da igreja.
Sobe o servidor local, converte PowerPoint/PDF em slides e abre o app em janela limpa.
Feito para rodar como .EXE em Windows, sem internet."""
import http.server, socketserver, threading, webbrowser, subprocess, os, sys, json, shutil, glob, time, socket, re, io

VERSAO = "2.6.0"
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
    melodia, melodia1, instrumentos = {}, {}, []
    try:
        with io.open(os.path.join(pasta_melodias(), "indice.json"), encoding="utf-8") as f:
            idx = json.load(f)
        instrumentos = idx.get("instrumentos", [])
        repetidas = set()
        for chave, v in idx.get("louvores", {}).items():
            melodia[chave] = v.get("tons", {})
            # segundo mapa, pela PRIMEIRA LINHA da letra: e' por ele que se
            # reencontram as melodias cujo titulo difere do catalogo do app
            # ("ALELUIA", "SOMENTE PELA FE"...). So entra linha inequivoca:
            # os cinco arranjos do Salmo 23 comecam iguais, e ai nenhum vale.
            l1 = v.get("l1") or ""
            if l1:
                if l1 in melodia1:
                    repetidas.add(l1)
                melodia1[l1] = v.get("tons", {})
        for l1 in repetidas:
            del melodia1[l1]
    except FileNotFoundError:
        pass
    except Exception as e:
        sys.stderr.write("catalogo do musico, melodia: %s" % e + chr(10))
    d = {"violao": violao, "melodia": melodia, "melodia1": melodia1,
         "instrumentos": instrumentos}
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
        partes = chave.split("|")
        titulo = partes[1] if len(partes) > 1 else chave
        alvo = None
        for k, v in idx.get("louvores", {}).items():
            if k == _simples(titulo):
                alvo = v
                break
        if alvo is None and len(partes) > 2:
            # titulo diferente entre a Melodica e o catalogo: reencontra pela
            # PRIMEIRA LINHA da letra (que vem na chave do app) — mas so' se
            # ela apontar para UMA melodia, senao e' Salmo 23 contra Salmo 23
            l1 = _simples("|".join(partes[2:]))[:30]
            iguais = [v for v in idx.get("louvores", {}).values()
                      if l1 and v.get("l1") == l1]
            if len(iguais) == 1:
                alvo = iguais[0]
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
    # espacos repetidos recolhidos, IGUAL ao so_letras do extrair_melodia.py e
    # ao simples() do controle.html — uma virgula de diferenca no titulo
    # ("MESTRE, O MAR...") gerava chave com espaco duplo e o casamento morria
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]+", " ", t)).strip()


# ------------------------------------------------- atualização e exportação
DONO_GITHUB = "QuitsQuill88885"
REPO_GITHUB = "sistema-projecao-icm"
ARQ_INSTALADOR = "Instalar-o-Sistema.exe"

# andamento das tarefas demoradas, para a tela ir perguntando
ATUALIZA = {"pct": 0, "txt": "", "erro": "", "fim": False, "rodando": False}
EXPORTA = {"pct": 0, "txt": "", "erro": "", "fim": False, "rodando": False}
COMPLETA = {"pct": 0, "txt": "", "erro": "", "fim": False, "rodando": False}


def _versao_tupla(v):
    try:
        return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4])
    except Exception:
        return ()


def versao_mais_nova():
    """Pergunta ao GitHub qual é a versão mais nova, SEM baixar nada.

    O endereço /releases/latest responde com um redirecionamento cujo destino
    termina em /tag/vX.Y.Z — lemos só esse cabeçalho e desligamos. Sem
    internet devolve None, e quem chamou decide o que dizer. A igreja muitas
    vezes NÃO tem internet: isso nunca pode virar erro na cara do operador."""
    import urllib.request
    import urllib.error

    class SemRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    url = "https://github.com/%s/%s/releases/latest" % (DONO_GITHUB, REPO_GITHUB)
    try:
        urllib.request.build_opener(SemRedirect).open(
            urllib.request.Request(url, headers={"User-Agent": "Sistema"}), timeout=8)
    except urllib.error.HTTPError as e:
        m = re.search(r"/tag/v?([0-9][0-9.]*)", e.headers.get("Location") or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _atualizar_thread():
    """Baixa o instalador mais novo e entrega a ele o serviço.

    O download são ~58 MB só do PROGRAMA. O conteúdo pesado (animações,
    cifras, melodias) mora nos dados do usuário e a atualização NÃO toca
    nele — é o que impede o "baixar 500 MB toda vez"."""
    import tempfile
    import urllib.request
    try:
        ATUALIZA.update({"pct": 3, "txt": "Baixando a versão nova…", "erro": ""})
        url = ("https://github.com/%s/%s/releases/latest/download/%s"
               % (DONO_GITHUB, REPO_GITHUB, ARQ_INSTALADOR))
        alvo = os.path.join(tempfile.mkdtemp(), "Instalar o Sistema.exe")
        req = urllib.request.Request(url, headers={"User-Agent": "Sistema"})
        with urllib.request.urlopen(req, timeout=60) as r, open(alvo, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            feito = 0
            while True:
                peda = r.read(256 * 1024)
                if not peda:
                    break
                f.write(peda)
                feito += len(peda)
                if total:
                    ATUALIZA["pct"] = 3 + int(90.0 * feito / total)
        ATUALIZA.update({"pct": 96, "txt": "Instalando… o Sistema vai fechar e reabrir sozinho.",
                         "fim": True})
        # --reabrir: o instalador novo reabre o Sistema no fim. Um instalador
        # antigo ignora a bandeira — aí o operador reabre pelo atalho.
        subprocess.Popen([alvo, "--silencioso", "--reabrir"], **SEM_JANELA)
    except Exception:
        ATUALIZA.update({"erro": "Não consegui baixar a atualização. Confira a internet e "
                                 "tente de novo — nada foi mexido.",
                         "fim": True, "rodando": False})


def conteudo_falta():
    """True se as animações/cifras/melodias ainda não estão neste computador.

    É o que decide se o botão "Completar o Sistema" aparece: quem instalou o
    essencial vê o botão; quem já tem tudo, não."""
    for nome in ("animacoes", "cifras", "melodias"):
        try:
            tem = any(a for a in os.listdir(pasta_usuario(nome))
                      if a != "LEIA-ME.txt")
        except OSError:
            tem = False
        if not tem:
            return True
    return False


def _completar_thread():
    """Baixa o Conteudo.zip da nuvem e abre direto nos dados do usuário.

    É o caminho do "Completar o Sistema": o essencial vira completo sem
    pendrive, sem reinstalar e sem baixar o programa de novo."""
    import tempfile
    import zipfile
    import urllib.request
    try:
        url = ("https://github.com/%s/%s/releases/latest/download/Conteudo.zip"
               % (DONO_GITHUB, REPO_GITHUB))
        zt = os.path.join(tempfile.mkdtemp(), "Conteudo.zip")
        req = urllib.request.Request(url, headers={"User-Agent": "Sistema"})
        COMPLETA.update({"pct": 1, "txt": "Baixando as animações e cifras…", "erro": ""})
        with urllib.request.urlopen(req, timeout=60) as r, open(zt, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            feito = 0
            while True:
                peda = r.read(262144)
                if not peda:
                    break
                f.write(peda)
                feito += len(peda)
                if total:
                    COMPLETA.update({"pct": int(feito * 90.0 / total),
                                     "txt": "Baixando… %d de %d MB"
                                            % (feito // 1048576, total // 1048576)})
        COMPLETA.update({"pct": 93, "txt": "Guardando o conteúdo…"})
        with zipfile.ZipFile(zt) as z:
            z.extractall(DADOS_USUARIO)
        try:
            os.remove(zt)
        except OSError:
            pass
        _CATALOGO["dados"] = None      # o catálogo do músico renasce com as melodias
        COMPLETA.update({"pct": 100, "txt": "Pronto! Animações, cifras e melodias instaladas.",
                         "fim": True, "rodando": False})
    except Exception:
        COMPLETA.update({"erro": "Não consegui baixar. Confira a internet e tente de "
                                 "novo — nada foi mexido.",
                         "fim": True, "rodando": False})


def restaurar_tudo(apagar_conteudo=False):
    """Devolve o Sistema ao estado de fábrica.

    Apaga o que o OPERADOR criou — configurações, histórico, louvores, fundos e
    apresentações importadas. O conteúdo pesado (animações, cifras, melodias)
    só sai se for pedido: são 590 MB que levaram um pendrive para chegar aqui,
    e apagar isso por engano seria cruel.
    """
    alvos = ["configuracoes.json", "historico.json", "Meus louvores",
             "Meus fundos", "Minhas apresentações", "slides_importados"]
    if apagar_conteudo:
        alvos += ["animacoes", "cifras", "melodias"]
    apagados = []
    for nome in alvos:
        p = os.path.join(DADOS_USUARIO, nome)
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
                apagados.append(nome)
            elif os.path.isfile(p):
                os.remove(p)
                apagados.append(nome)
        except Exception:
            pass
    return apagados


def _roteiro_de_saida(comandos, reabrir=None):
    """Escreve um .bat que roda DEPOIS que o Sistema fechar.

    O Windows não deixa um programa apagar a si mesmo enquanto roda. Então quem
    apaga é um roteirinho solto, que espera o processo morrer, faz o serviço e
    some — é assim que todo desinstalador de verdade funciona.
    """
    import tempfile
    linhas = ["@echo off", "chcp 65001 >nul",
              ":esperar",
              'tasklist /fi "imagename eq Sistema.exe" | find /i "Sistema.exe" >nul',
              "if not errorlevel 1 (timeout /t 1 /nobreak >nul & goto esperar)"]
    linhas += comandos
    if reabrir:
        linhas.append('start "" "%s"' % reabrir)
    bat = os.path.join(tempfile.mkdtemp(), "sistema_servico.bat")
    with io.open(bat, "w", encoding="utf-8") as f:
        f.write("\r\n".join(linhas) + "\r\n(goto) 2>nul & del \"%~f0\"\r\n")
    subprocess.Popen(["cmd", "/c", bat], **SEM_JANELA)
    return bat


def desinstalar(apagar_dados=False):
    """Tira o Sistema do computador.

    O programa mora em Programas\\Sistema; os atalhos, na Área de Trabalho e no
    menu Iniciar. Os DADOS do operador só somem se ele mandar — e a tela
    pergunta isso com todas as letras antes.
    """
    prog = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Sistema")
    cmds = ['rmdir /s /q "%s"' % prog]
    for pasta in (os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
                  os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows",
                               "Start Menu", "Programs")):
        cmds.append('del /q "%s" 2>nul' % os.path.join(pasta, "Sistema.lnk"))
    if apagar_dados:
        cmds.append('rmdir /s /q "%s"' % DADOS_USUARIO)
    _roteiro_de_saida(cmds)
    return True


def pendrives_plugados():
    """[{letra, nome, livre}] das unidades removíveis acessíveis agora."""
    import ctypes
    achados = []
    try:
        k = ctypes.windll.kernel32
        bits = k.GetLogicalDrives()
        for i in range(26):
            if not (bits & (1 << i)):
                continue
            letra = "%s:\\" % chr(65 + i)
            if k.GetDriveTypeW(letra) != 2:            # 2 = DRIVE_REMOVABLE
                continue
            livre = ctypes.c_ulonglong(0)
            if not k.GetDiskFreeSpaceExW(letra, ctypes.byref(livre), None, None):
                continue                               # leitor de cartão vazio
            nome = ""
            buf = ctypes.create_unicode_buffer(261)
            if k.GetVolumeInformationW(letra, buf, 260, None, None, None, None, 0):
                nome = (buf.value or "").strip()
            achados.append({"letra": letra, "nome": nome or "Pendrive",
                            "livre": int(livre.value)})
    except Exception:
        pass
    return achados


def _exportar_usb_thread(letra):
    """Grava no pendrive tudo o que outro computador precisa para virar ESTE:
    o instalador guardado + a pasta Conteudo (animações, cifras, melodias E as
    coisas pessoais: configurações, histórico, louvores e fundos próprios).
    O instalador do outro lado copia a pasta inteira sozinho."""
    import ctypes
    try:
        EXPORTA.update({"pct": 1, "txt": "Conferindo o pendrive…", "erro": ""})
        pasta_inst = os.path.join(DADOS_USUARIO, "Instalador")
        exes = sorted(glob.glob(os.path.join(pasta_inst, "*.exe")), key=os.path.getmtime)
        if not exes:
            raise RuntimeError("Não achei o instalador guardado nos dados do Sistema. "
                               "Instale o Sistema uma vez pelo instalador que ele fica guardado.")
        exe = exes[-1]

        itens = [(exe, "Instalar o Sistema.exe")]
        pastas = ["animacoes", "cifras", "melodias",
                  "Meus louvores", "Meus fundos", "Minhas apresentações"]
        for nome in pastas:
            p = os.path.join(DADOS_USUARIO, nome)
            if not os.path.isdir(p):
                continue
            for raiz_c, _sub, arqs in os.walk(p):
                rel = os.path.relpath(raiz_c, DADOS_USUARIO)
                for a in arqs:
                    itens.append((os.path.join(raiz_c, a),
                                  os.path.join("Conteudo", rel, a)))
        for nome in ("configuracoes.json", "historico.json"):
            p = os.path.join(DADOS_USUARIO, nome)
            if os.path.isfile(p):
                itens.append((p, os.path.join("Conteudo", nome)))

        total = 0
        for origem_c, _d in itens:
            try:
                total += os.path.getsize(origem_c)
            except OSError:
                pass
        livre = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(letra, ctypes.byref(livre), None, None)
        if livre.value and livre.value < total + 20 * 1024 * 1024:
            raise RuntimeError("Não cabe: o pacote tem %d MB e o pendrive só tem %d MB livres."
                               % (total // 1048576, livre.value // 1048576))

        feito = 0
        for origem_c, destino_rel in itens:
            alvo = os.path.join(letra, destino_rel)
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            shutil.copy2(origem_c, alvo)
            try:
                feito += os.path.getsize(origem_c)
            except OSError:
                pass
            EXPORTA.update({"pct": max(2, int(96.0 * feito / (total or 1))),
                            "txt": "Copiando… (%d de %d MB)" % (feito // 1048576,
                                                                total // 1048576)})

        with io.open(os.path.join(letra, "LEIA - Como instalar o Sistema.txt"),
                     "w", encoding="utf-8") as f:
            f.write("SISTEMA — projecao para a igreja\r\n"
                    "================================\r\n\r\n"
                    "1. De dois cliques em \"Instalar o Sistema.exe\"\r\n"
                    "2. Espere a barrinha encher\r\n\r\n"
                    "A pasta \"Conteudo\" vai junto e o instalador copia tudo\r\n"
                    "sozinho: animacoes, cifras, melodias e as configuracoes\r\n"
                    "de quem gravou este pendrive. Nao precisa de internet.\r\n\r\n"
                    "Se o Windows avisar \"protegeu o computador\": clique em\r\n"
                    "\"Mais informacoes\" e \"Executar assim mesmo\".\r\n\r\n"
                    "Desenvolvido por Samuel Mariano Ribeiro.\r\n")
        EXPORTA.update({"pct": 100, "txt": "Pronto! Pode tirar o pendrive.",
                        "fim": True, "rodando": False})
    except Exception as e:
        EXPORTA.update({"erro": str(e) or "Não consegui exportar.",
                        "fim": True, "rodando": False})


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
        # somente leitura): slides convertidos, animações das CIAS e as cifras
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
        if self.path.startswith("/api/atualizacao"):     # existe versão mais nova?
            nova = versao_mais_nova()
            tem = bool(nova) and _versao_tupla(nova) > _versao_tupla(VERSAO)
            return self._json({"ok": nova is not None, "atual": VERSAO,
                               "nova": nova, "tem": tem})
        if self.path.startswith("/api/atualizar"):       # andamento da atualização
            return self._json({"ok": True, **ATUALIZA})
        if self.path.startswith("/api/pendrives"):
            return self._json({"ok": True, "pendrives": pendrives_plugados()})
        if self.path.startswith("/api/conteudo"):       # falta conteúdo? e o andamento
            return self._json({"ok": True, "falta": conteudo_falta(), **COMPLETA})
        if self.path.startswith("/api/exportar-usb"):    # andamento da exportação
            return self._json({"ok": True, **EXPORTA})
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
        if self.path.startswith("/api/atualizar"):       # começa a atualização
            with TRAVA:
                if not ATUALIZA["rodando"]:
                    ATUALIZA.update({"rodando": True, "pct": 0, "txt": "Começando…",
                                     "erro": "", "fim": False})
                    threading.Thread(target=_atualizar_thread, daemon=True).start()
            return self._json({"ok": True})
        if self.path.startswith("/api/restaurar"):       # estado de fábrica
            try:
                n = int(self.headers.get("Content-Length", 0))
                d = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
                apagados = restaurar_tudo(bool(d.get("conteudo")))
                # reabrir depois de fechar: restaurar sem reiniciar deixava o
                # programa na tela com as coisas antigas na memória
                exe = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs",
                                   "Sistema", "Sistema.exe")
                _roteiro_de_saida([], reabrir=exe if os.path.exists(exe) else None)
                return self._json({"ok": True, "apagados": apagados})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/desinstalar"):
            try:
                n = int(self.headers.get("Content-Length", 0))
                d = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
                desinstalar(bool(d.get("dados")))
                return self._json({"ok": True})
            except Exception as e:
                return self._json({"ok": False, "erro": str(e)})
        if self.path.startswith("/api/conteudo"):        # começa a completar
            with TRAVA:
                if not COMPLETA["rodando"]:
                    COMPLETA.update({"rodando": True, "pct": 0, "txt": "Começando…",
                                     "erro": "", "fim": False})
                    threading.Thread(target=_completar_thread, daemon=True).start()
            return self._json({"ok": True})
        if self.path.startswith("/api/exportar-usb"):    # começa a exportação
            try:
                n = int(self.headers.get("Content-Length", 0))
                letra = (json.loads(self.rfile.read(n).decode("utf-8")) or {}).get("letra", "")
                if not letra or not os.path.isdir(letra):
                    return self._json({"ok": False, "erro": "O pendrive foi retirado."})
                with TRAVA:
                    if not EXPORTA["rodando"]:
                        EXPORTA.update({"rodando": True, "pct": 0, "txt": "Começando…",
                                        "erro": "", "fim": False})
                        threading.Thread(target=_exportar_usb_thread, args=(letra,),
                                         daemon=True).start()
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
