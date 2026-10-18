# -*- coding: utf-8 -*-

"""Sistema — projeção da igreja.

Sobe o servidor local, converte PowerPoint/PDF em slides e abre o app em janela limpa.

Feito para rodar como .EXE em Windows, sem internet."""

import http.server, socketserver, threading, webbrowser, subprocess, os, sys, json, shutil, glob, time, socket, re, io



VERSAO = "3.0.9"
# 0.0.0.0 = o celular controla pela rede. SISTEMA_SO_LOCAL=1 (so as PROVAS usam) abre so em 127.0.0.1: cada instalacao
# de teste roda de uma pasta nova, e o Firewall do Windows perguntava "Permitir?" na tela da casa (11/10 14h11).
ENDERECO_REDE = "127.0.0.1" if os.environ.get("SISTEMA_SO_LOCAL") else "0.0.0.0"

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

# Quando a tela do Sistema veio buscar comandos pela última vez. Ela busca a

# cada 600ms; se passou muito disso, ela não está acordada — ver o vigia

# `acordar_janela()`, lá embaixo, e a medição que o obrigou a existir.

BUSCA = {"t": 0.0}

# "ts" já nasce carimbado: sem isso o celular que estivesse aberto acusava

# "O computador parou de responder" durante toda a subida do Sistema

ESTADO = {"agora": "Pronto.", "projetando": False, "congelado": False, "ts": time.time()}

TELA = {"payload": None, "n": 0}       # o que está no telão agora (para a prévia do celular)

TRAVA = threading.Lock()

# ===== 3.0.9: PROJETAR COM DUAS TELAS (pedido dele, 17/10/2026: "estilo AirDrop") =====
# Um segundo computador (o Vaio) abre o retorno.html DESTE PC e se apresenta a cada segundo (GET /api/apoio).
# O painel pergunta, num cartão no canto: "Projetar com duas telas?". O SIM fica lembrado em apoios.json
# (o par volta calado se o Wi-Fi piscar ou no culto seguinte); o NÃO vale até fechar o Sistema.
# Arquivo separado do configuracoes.json porque o painel regrava aquele inteiro.
APOIOS = {}             # chave (nome do computador, ou o IP) -> o que se sabe dele
APOIO_ONLINE_SEG = 6    # sem notícia há mais que isto = desligou
APOIO_IDENT_SEG = 3     # o "1" e o "2" gigantes ficam este tanto
PORTA_ANUNCIO = 8766    # UDP: "existe um Sistema aqui" (o apoio acha sem varrer a rede)
ARQ_APOIOS = os.path.join(DADOS_USUARIO, "apoios.json")





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

    # ESCREVO O PNG NA MAO, sem Pillow. O `qrcode.make()` devolve imagem do

    # PIL, e por isso o Pillow inteiro (13 MB) viajava dentro do programa - para

    # desenhar um quadriculado preto e branco.

    #

    # Um QR e' uma matriz de quadradinhos: `get_matrix()` da' os True/False, e um

    # PNG em tons de cinza sem filtro e' cabecalho + zlib + CRC. Conferido pixel

    # a pixel contra o Pillow: sai IDENTICO, e menor (613 contra 770 bytes).

    #

    # (Fiz antes em SVG, que tambem dispensa o PIL, e medi: 13 KB contra 770

    # bytes. Nao adianta trocar um peso por outro.)

    try:

        import base64, struct, zlib

        import qrcode

        lado = 7

        q = qrcode.QRCode(box_size=1, border=2)

        q.add_data(texto); q.make(fit=True)

        m = q.get_matrix()

        larg = len(m) * lado

        cru = b""

        for linha in m:

            px = bytes(0 if c else 255 for c in linha for _ in range(lado))

            cru += (b"\x00" + px) * lado         # \x00 = linha sem filtro

        def bloco(tipo, dados):

            return (struct.pack(">I", len(dados)) + tipo + dados

                    + struct.pack(">I", zlib.crc32(tipo + dados) & 0xffffffff))

        png = (b"\x89PNG\r\n\x1a\n"

               + bloco(b"IHDR", struct.pack(">IIBBBBB", larg, larg, 8, 0, 0, 0, 0))

               + bloco(b"IDAT", zlib.compress(cru, 9))

               + bloco(b"IEND", b""))

        return "data:image/png;base64," + base64.b64encode(png).decode()

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


def cifras_ocultas():
    """CIFRA SO' SE FOR VERIFICADA (pedido dele, 18/10/2026 13h08: "Se o louvor nao tiver uma cifra verificada, nem
    apareca o botao de cifra"). dados/cifras_ocultas.json = {chave: motivo}, gerado por
    ferramentas/gera_cifras_ocultas.py: a cifra cobre menos de 90% da letra do telao, ou esta' na lista negra a mao.
    Sem o arquivo, nada some (o jeito de antes)."""
    try:
        with io.open(os.path.join(BASE, "dados", "cifras_ocultas.json"), encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()





def catalogo_do_musico():

    """A lista do que existe, sem o conteúdo. Fica em memória: o celular pede

    isto uma vez ao abrir, e o disco não é lido de novo a cada toque."""

    if _CATALOGO["dados"] is not None and time.time() - _CATALOGO["ts"] < 30:

        return _CATALOGO["dados"]

    violao = {}

    try:

        cam = os.path.join(pasta_usuario("cifras"), "acordes.json")

        with io.open(cam, encoding="utf-8") as f:

            ocultas = cifras_ocultas()

            for chave, reg in json.load(f).items():

                if chave in ocultas:

                    continue      # 3.0.10: cifra nao verificada nao aparece (nem no painel nem no celular)

                violao[chave] = reg.get("tom") or ""

    except FileNotFoundError:

        pass

    except Exception as e:

        sys.stderr.write("catalogo do musico, violao: %s" % e + chr(10))

    # NAO HA' MAIS DOIS NIVEIS. A coletanea agora e' uma so' (acordes.json):
    # o Basico 1 como fonte, remendado pelo Basico 2 so' onde ele estava mudo.
    # O seletor "Nivel 1 / Nivel 2" saiu junto - era uma escolha a mais para
    # o instrumentista fazer no meio do culto, sem ganho nenhum.

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

    d = {"violao": violao, "melodia": melodia,

         "melodia1": melodia1, "instrumentos": instrumentos}

    _CATALOGO.update({"ts": time.time(), "dados": d})

    return d





def material_do_louvor(chave, afinacao="C"):
    """A cifra de violao e/ou o caderno melodico de UM louvor.

    A cifra vem da COLETANEA UNICA (acordes.json). Ate' 31/08/2026 havia
    dois bancos e um seletor "Nivel 1 / Nivel 2"; hoje ha' um so'.
    """
    saida = {"ok": True, "chave": chave, "em": afinacao}
    try:
        with io.open(os.path.join(pasta_usuario("cifras"), "acordes.json"),
                     encoding="utf-8") as f:
            reg = json.load(f).get(chave)
        if reg and reg.get("linhas"):
            saida["violao"] = {"tom": reg.get("tom"),
                               "linhas": reg.get("linhas", [])}
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



# Onde os downloads moram enquanto acontecem. PASTA FIXA — é o que deixa

# fechar o Sistema no meio dos 610 MB e continuar depois, em vez de recomeçar.

# Escrita UMA VEZ SÓ: este caminho já esteve copiado em três lugares deste

# arquivo, e num quarto ele divergiu e quebrou a retomada na igreja.

PASTA_BAIXANDO = os.path.join(__import__("tempfile").gettempdir(), "Sistema-baixando")



# andamento das tarefas demoradas, para a tela ir perguntando

ATUALIZA = {"pct": 0, "txt": "", "erro": "", "fim": False, "rodando": False}

EXPORTA = {"pct": 0, "txt": "", "erro": "", "fim": False, "rodando": False}

COMPLETA = {"pct": 0, "txt": "", "erro": "", "fim": False, "rodando": False}





def _versao_tupla(v):

    try:

        return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4])

    except Exception:

        return ()





# ---------------------------------------------------------------------------

# PROVAR QUEM E' O GITHUB

#

# O DEFEITO, contado pelo Samuel em 30/08/2026: no computador da IGREJA, tanto

# "Atualizar" quanto "Completar o Sistema" diziam que **nao conseguiam se

# conectar com a internet** - e no mesmo computador o NAVEGADOR baixava o

# instalador do site do GitHub sem reclamar.

#

# A causa: o programa compilado nao levava certificado nenhum dentro dele.

# Sem `cacert.pem`, o Python cai no deposito de certificados do WINDOWS. Nesta

# maquina, que e' velha de guerra, esse deposito tem dezenas de certificados e

# tudo funciona. O computador da igreja e' **maquina do zero**: o Windows

# comeca com o deposito quase vazio e vai buscando os certificados-raiz sob

# demanda - busca que falha justamente em rede fraca, tipo hotspot de celular.

# O `urlopen` levantava erro de certificado, o `except Exception` engolia, e

# sobrava a frase generica sobre internet, que mandou ele procurar no lugar

# errado.

#

# Navegador nao sofre disso porque Chrome e Edge carregam os proprios

# certificados-raiz. Por isso baixar pelo site funcionava e o botao nao.

#

# Agora os certificados VIAJAM DENTRO do programa e sao usados explicitamente.

# O Sistema deixa de depender do que a maquina tem instalado.

def _pacote_de_certificados():

    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

    p = os.path.join(base, "cacert.pem")

    if os.path.exists(p):

        return p

    try:                                  # rodando do codigo-fonte, sem empacotar

        import certifi

        return certifi.where()

    except Exception:

        return None





_CTX_SSL = None





def contexto_ssl():

    """O contexto TLS que todo download do Sistema usa. Montado uma vez so.



    SOMA as duas fontes de confianca, em vez de escolher uma:

      - o `cacert.pem` que viaja dentro do programa (resolve a maquina nova,

        de deposito vazio, que era o caso da igreja);

      - o deposito do proprio Windows (resolve a rede que inspeciona o trafego

        e assina com um certificado PROPRIO - escola, empresa, alguns

        provedores. Esse certificado so' existe na maquina, nunca no cacert.pem,

        e ficar so' com o pacote nosso QUEBRARIA onde hoje funciona).

    Somando, nenhum dos dois mundos fica de fora.

    """

    global _CTX_SSL

    if _CTX_SSL is None:

        import ssl

        _CTX_SSL = ssl.create_default_context()

        ca = _pacote_de_certificados()

        if ca:

            try:

                _CTX_SSL.load_verify_locations(cafile=ca)

            except Exception:

                pass

        try:

            _CTX_SSL.load_default_certs()      # o que a maquina ja' confia

        except Exception:

            pass

    return _CTX_SSL





def hora_da_rede():

    """A hora CERTA, pega na rede sem depender de HTTPS.



    Ideia do Samuel: se o computador esta' na internet, a hora certa esta'

    passando por ali de qualquer jeito - e' so' pegar. E ele tem razao: da'

    para saber a hora sem conseguir abrir uma pagina segura, que e' exatamente

    a situacao de quem esta' com o relogio errado.



    Dois caminhos, nessa ordem:

      1. NTP (porta 123) - e' o servico feito para isso, responde em bytes

         crus, e nao tem certificado nenhum no meio;

      2. o cabecalho `Date` de uma pagina em HTTP simples - todo servidor web

         manda a sua hora em toda resposta, de gra'a. Vale quando a rede

         bloqueia o NTP.



    Devolve segundos desde 1970 (UTC), ou None se nao deu para saber.

    """

    import socket

    import struct

    try:

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.settimeout(5)

        s.sendto(b"\x1b" + 47 * b"\0", ("pool.ntp.org", 123))

        msg, _ = s.recvfrom(1024)

        s.close()

        return struct.unpack("!12I", msg)[10] - 2208988800

    except Exception:

        pass

    import email.utils

    for host in ("www.microsoft.com", "www.google.com"):

        try:

            c = socket.create_connection((host, 80), timeout=6)

            # o fim de linha do HTTP entra como VARIAVEL: escrito como

            # escape dentro da string, ele ja' foi processado a mais uma vez

            # por um script e virou quebra de linha de verdade no arquivo

            fl = chr(13) + chr(10)

            pedido = ("HEAD / HTTP/1.1" + fl + "Host: " + host + fl +

                      "User-Agent: Sistema" + fl + "Connection: close" + fl + fl)

            c.sendall(pedido.encode())

            b = b""

            while (fl + fl).encode() not in b and len(b) < 4096:

                p = c.recv(1024)

                if not p:

                    break

                b += p

            c.close()

            for linha in b.decode("latin-1").split(fl):

                if linha.lower().startswith("date:"):

                    return email.utils.parsedate_to_datetime(linha[5:].strip()).timestamp()

        except Exception:

            continue

    return None





def relogio_errado():

    """Quantos segundos o relogio deste computador esta' fora. None se nao sei.



    Maquina que ficou guardada, ou com a pilha da placa-mae gasta, volta com a

    data errada - e ai' TODO certificado parece vencido, mesmo os que viajam

    dentro do programa. E' o unico caso de certificado que o pacote nao

    resolve, e o mais provavel num computador de igreja.

    """

    certa = hora_da_rede()

    if certa is None:

        return None

    return time.time() - certa





def acertar_relogio():

    """Poe o relogio na hora certa. Devolve (deu_certo, o_que_dizer).



    Mexer no relogio do Windows exige ADMINISTRADOR - nao da' para fazer

    calado. Entao: se o Sistema estiver rodando com permissao, ele acerta e

    pronto; se nao estiver, ABRE a tela de Data e hora do Windows, que nao

    exige permissao nenhuma e tem o botao "Sincronizar agora" ali mesmo.

    Nao insistimos com pedido de permissao no meio do culto.

    """

    if os.name != "nt":

        return False, "Só sei acertar o relógio no Windows."

    certa = hora_da_rede()

    if certa is None:

        return False, "Não consegui descobrir a hora certa pela internet."

    import ctypes

    import ctypes.wintypes



    class SYSTEMTIME(ctypes.Structure):

        _fields_ = [("wYear", ctypes.wintypes.WORD), ("wMonth", ctypes.wintypes.WORD),

                    ("wDayOfWeek", ctypes.wintypes.WORD), ("wDay", ctypes.wintypes.WORD),

                    ("wHour", ctypes.wintypes.WORD), ("wMinute", ctypes.wintypes.WORD),

                    ("wSecond", ctypes.wintypes.WORD), ("wMilliseconds", ctypes.wintypes.WORD)]



    t = time.gmtime(certa)                       # SetSystemTime fala em UTC

    st = SYSTEMTIME(t.tm_year, t.tm_mon, 0, t.tm_mday,

                    t.tm_hour, t.tm_min, t.tm_sec, 0)

    if ctypes.windll.kernel32.SetSystemTime(ctypes.byref(st)):
        return True, "Relógio acertado pela internet."

    # Sem permissão. NÃO desistimos: pedimos ao Windows para reabrir SÓ esta
    # tarefa com permissão. O operador vê um aviso e clica Sim, uma vez — é o
    # mais perto de "o programa se vira sozinho" que o Windows deixa chegar.
    try:
        r = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, "--acertar-relogio", None, 0)
        if int(r) > 32:
            for _ in range(40):                   # espera a outra cópia acertar
                time.sleep(0.25)
                if abs(time.time() - certa) < 120:
                    return True, "Relógio acertado pela internet."
            return False, ("Pedi permissão para acertar o relógio. Se você "
                           "clicou Sim, tente baixar de novo.")
    except Exception:
        pass

    try:                                          # último recurso: a tela do Windows
        subprocess.Popen(["cmd", "/c", "start", "", "ms-settings:dateandtime"], **SEM_JANELA)
    except Exception:
        pass
    return False, ("Abri a tela de Data e hora do Windows. Ligue "

                   "\"Definir horário automaticamente\" e feche — depois é só "

                   "tentar baixar de novo.")





def explicar_falha_de_rede(e):

    """Diz A VERDADE sobre por que o download nao foi.



    Antes, qualquer tropeco virava "confira a internet" - e foi essa frase que

    fez o Samuel procurar defeito na rede da igreja quando o problema era

    certificado. Erro que nao se explica custa culto.

    """

    if "CERTIFICATE" in str(e).upper():

        # Antes de falar qualquer coisa, PERGUNTA a rede que horas sao. Assim a

        # mensagem deixa de ser palpite: ou o relogio esta' fora e a gente diz

        # quanto, ou ele esta' certo e o problema e' outro.

        fora = relogio_errado()

        if fora is not None and abs(fora) > 86400:

            dias = int(abs(fora) // 86400)

            return ("A data deste computador está %s de %d dia%s. "

                    "Enquanto ela estiver errada, não dá para baixar. "

                    "Acerte a data e a hora e tente de novo."

                    % ("adiantada" if fora > 0 else "atrasada", dias,

                       "s" if dias > 1 else ""))

        if fora is not None:

            # relogio certo: entao quem esta' no meio e' a REDE. Sem jargao -

            # o Samuel disse que nem ele sabia o que era "rede inspecionada".

            return ("A internet deste lugar não deixa o programa baixar "

                    "sozinho. Não é defeito do Sistema nem do computador. "

                    "Baixe a versão nova no site do Sistema e instale por "

                    "cima: dá no mesmo, e funciona.")

        # Com o pacote de certificados dentro do programa isto virou raro. Quando

        # acontecer, o suspeito numero um NAO e' a rede: e' o RELOGIO do

        # computador. Maquina que ficou guardada, ou com a pilha da placa-mae

        # gasta, volta com a data errada - e ai' todo certificado do mundo

        # parece vencido. Por isso a frase fala do relogio, que o operador

        # consegue conferir, e nao de certificado, que ele nao tem como.

        return ("Nao consegui confirmar o servidor. Confira se a DATA e a HORA "

                "deste computador estao certas - e' quase sempre isso. Se "

                "estiverem, baixe o instalador pelo site e rode por cima.")

    if isinstance(e, TimeoutError) or "timed out" in str(e).lower():

        return ("A internet esta muito lenta e o download expirou. Pode tentar "

                "de novo: o que ja' baixou nao se perde.")

    return ("Nao consegui falar com o GitHub. Confira a internet e tente de "

            "novo - nada foi mexido.")





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

        # o contexto vai junto: sem ele, este era o PRIMEIRO lugar a falhar na

        # maquina nova da igreja, e a tela nem dizia que estava desatualizada

        urllib.request.build_opener(

            SemRedirect, urllib.request.HTTPSHandler(context=contexto_ssl())).open(

            urllib.request.Request(url, headers={"User-Agent": "Sistema"}), timeout=15)

    except urllib.error.HTTPError as e:

        m = re.search(r"/tag/v?([0-9][0-9.]*)", e.headers.get("Location") or "")

        if m:

            return m.group(1)

    except Exception:

        pass

    return None





def _mesmo_arquivo(resposta, parcial, feito, recuo):

    """Os bytes que voltaram batem com os que já estão no disco?



    Se batem, é o mesmo arquivo e a emenda é segura. Se não batem, saiu versão

    nova enquanto o download dormia e o que está no disco não presta mais."""

    veio = b""

    while len(veio) < recuo:

        p = resposta.read(recuo - len(veio))

        if not p:

            return False

        veio += p

    try:

        with open(parcial, "rb") as f:

            f.seek(feito - recuo)

            nosso = f.read(recuo)

    except OSError:

        return False

    return veio == nosso





def baixar_retomando(url, destino, avisar, tentativas=10):

    """Baixa `url` para `destino` e RETOMA de onde parou quando a rede cai.



    Quem instala na igreja usa a internet de lá ou o celular roteado, e são

    ~610 MB no pacote de conteúdo. Recomeçar do zero a cada oscilação pode

    significar não terminar nunca. O que já veio fica num `.parte` e o pedido

    seguinte pede `Range: bytes=N-` para continuar do byte N. O `.parte` mora

    ao lado do destino e NÃO é apagado entre as tentativas — ele é a retomada.



    `avisar(feito, total, tentativa, resta)` recebe o andamento; `tentativa`

    vem 0 enquanto está baixando e >0 quando está esperando para retomar, e

    `resta` são os segundos que faltam para a próxima tentativa (conta

    regressiva, para a tela nunca parecer travada).



    Se o servidor ignorar o Range (responde 200 no lugar de 206), recomeça do

    zero de propósito: um 200 traz o arquivo INTEIRO, e continuar gravando no

    fim do que já existia corromperia o arquivo em silêncio.



    E CONFERE SE O ARQUIVO É O MESMO antes de emendar: um download parado por

    dias pode acordar depois de sair uma versão nova, e aí o servidor manda

    alegremente os bytes do arquivo NOVO a partir do ponto pedido — começo de um

    colado no fim do outro, tamanho final batendo, arquivo podre. O `If-Range`

    existe para isso, mas MEDIDO: o servidor do GitHub o ignora. Então a

    conferência é feita aqui, pedindo 64 KB a mais e comparando com o disco."""

    import urllib.error

    import urllib.request

    CONFERE = 65536

    parcial = destino + ".parte"

    pasta = os.path.dirname(destino)

    if pasta and not os.path.isdir(pasta):

        os.makedirs(pasta, exist_ok=True)

    total = 0

    espera = 2

    ultimo = "rede indisponível"

    secas = 0            # tentativas seguidas que não trouxeram nenhum byte



    for tentativa in range(1, tentativas + 1):

        feito = os.path.getsize(parcial) if os.path.exists(parcial) else 0

        antes = feito

        recuo = min(CONFERE, feito)      # bytes pedidos a mais, como prova

        cab = {"User-Agent": "Sistema"}

        if feito:

            cab["Range"] = "bytes=%d-" % (feito - recuo)

        try:

            req = urllib.request.Request(url, headers=cab)

            with urllib.request.urlopen(req, timeout=60, context=contexto_ssl()) as r:

                codigo = getattr(r, "status", None) or r.getcode()

                faixa = r.headers.get("Content-Range") or ""

                if feito and codigo == 206 and "/" in faixa:

                    total = int(faixa.rsplit("/", 1)[-1])

                    if recuo and not _mesmo_arquivo(r, parcial, feito, recuo):

                        try:

                            os.remove(parcial)     # versão nova: o velho não serve

                        except OSError:

                            pass

                        ultimo = "a versão mudou no meio do caminho"

                        continue      # sem espera: não foi a rede que falhou

                    modo = "ab"

                else:

                    feito = 0

                    total = int(r.headers.get("Content-Length") or 0)

                    modo = "wb"

                with open(parcial, modo) as f:

                    while True:

                        peda = r.read(262144)

                        if not peda:

                            break

                        f.write(peda)

                        feito += len(peda)

                        avisar(feito, total, 0, 0)

            if not total or os.path.getsize(parcial) >= total:

                if os.path.exists(destino):

                    os.remove(destino)

                os.replace(parcial, destino)

                return destino

            ultimo = "a conexão fechou antes do fim"

        except urllib.error.HTTPError as e:

            # 416 = pedi um pedaço que não existe (o .parte ficou maior que o

            # arquivo, porque a versão trocou no meio). Joga fora e recomeça.

            if e.code == 416 and os.path.exists(parcial):

                os.remove(parcial)

            ultimo = "o servidor respondeu %s" % e.code

        except Exception as e:

            ultimo = str(e) or e.__class__.__name__



        ja = os.path.getsize(parcial) if os.path.exists(parcial) else 0

        # tentar de novo perdoa INTERRUPÇÃO, não perdoa AUSÊNCIA: se não veio

        # um byte em três tentativas, a rede não está entregando e insistir só

        # deixa a tela parada por minutos em vez de dizer o que houve

        secas = 0 if ja > antes else secas + 1

        if secas >= 3:

            ultimo = ("a internet não está entregando o arquivo "

                      "(nenhum byte chegou em 3 tentativas)")

            break

        if tentativa < tentativas:

            for resta in range(espera, 0, -1):   # conta regressiva visível

                avisar(ja, total, tentativa + 1, resta)

                time.sleep(1)

            espera = min(30, espera * 2)      # não martelar a rede que já caiu



    raise RuntimeError(ultimo)





def acordar_janela():

    """Vigia: se o celular mandou e a tela do Sistema está dormindo, acorda ela.



    O DEFEITO, medido nesta máquina com o programa de verdade (não em aba de

    navegador): com a janela do Sistema MINIMIZADA, os comandos do celular

    ficavam parados na fila **57 segundos**. Com ela só atrás de outra janela,

    obedecia em 1s — o problema é a minimização.



    A causa é o motor de tela (o mesmo do Edge/Chrome): janela minimizada é

    considerada invisível, e ele suspende os temporizadores da página. Quem

    busca os comandos do celular é um temporizador. O operador na igreja

    minimiza o Sistema depois de abrir o telão, pega o celular, e nada responde.



    TENTEI PRIMEIRO pelas bandeiras do Chromium

    (`--disable-background-timer-throttling` e as irmãs, via

    WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS). **PARA ESTE CASO NÃO RESOLVEM** —

    medido: 53 a 57 segundos com elas ligadas, igualzinho a sem. A suspensão de

    janela minimizada acontece num nível que essas bandeiras não alcançam.

    Elas SEGUEM no `main()`, mas servindo ao outro caso — janela apenas COBERTA

    por outra, onde funcionam. São dois estrangulamentos diferentes e cada um

    tem o seu remédio: coberta, bandeira resolve; minimizada, este vigia.



    O que funciona é isto: **o Python não é estrangulado**. Este vigia é uma

    linha de Python comum, roda sempre, e quando vê comando parado com a tela

    dormindo, desminimiza a janela — o que acorda a página, que então drena a

    fila sozinha. Não interfere no telão: quem projeta é a OUTRA janela.



    Só age quando há comando ESPERANDO e a tela está muda há mais de 3s (ela

    busca a cada 600ms). Com folga de 10s entre uma restauração e outra, para

    nunca ficar pulando na cara de quem está no computador.



    E DESMINIMIZA PELO WINDOWS, não pelo `restore()` do pywebview: aquele só

    vale se chamado de dentro da thread da interface, e desta aqui ele não faz

    nada — medido, a janela continuava minimizada e o defeito seguia igual.

    O `ShowWindow` do Windows pode ser chamado de qualquer thread."""

    if os.name != "nt":

        return                       # o defeito é do motor de tela no Windows

    import ctypes

    u32 = ctypes.windll.user32

    # OS TIPOS PRECISAM SER DECLARADOS. Sem isto o ctypes trata o retorno do

    # FindWindowW como inteiro de 32 bits, e no Windows 64 bits o identificador

    # da janela é de 64 — vinha truncado, virava lixo, e o ShowWindow não achava

    # nada. Silenciosamente: nenhum erro, só não funcionava.

    u32.FindWindowW.restype = ctypes.c_void_p

    u32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]

    u32.IsIconic.restype = ctypes.c_bool

    u32.IsIconic.argtypes = [ctypes.c_void_p]

    u32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]

    titulo = "Sistema v" + VERSAO

    ultima = [0.0]

    while True:

        time.sleep(1.0)

        try:

            if not COMANDOS:

                continue

            agora = time.time()

            if agora - BUSCA["t"] < 3.0:      # a tela está acordada, tudo bem

                continue

            if agora - ultima[0] < 10.0:      # já acordei há pouco; espera

                continue

            h = u32.FindWindowW(None, titulo)

            if not h or not u32.IsIconic(h):  # só mexe se estiver MINIMIZADA

                continue

            ultima[0] = agora

            u32.ShowWindow(h, 9)              # 9 = SW_RESTORE

        except Exception:

            pass          # janela fechada no meio: sem drama





def limpar_baixados():

    """Varre o que sobrou dos downloads e joga fora o que já cumpriu o serviço.



    A atualização baixa o instalador (63 MB) para uma pasta temporária FIXA e

    depois entrega o serviço a ele — mas o Sistema fecha no meio disso, então

    não sobra ninguém para limpar. Sem esta varredura na abertura seguinte, o

    arquivo fica no disco para sempre, e uma atualização por mês vira meio giga

    de lixo num computador de igreja.



    O `.parte` NUNCA é tocado: ele é um download pela metade esperando a rede

    voltar, e apagá-lo desfaria a retomada. Só sai arquivo inteiro, e só se

    estiver parado há mais de uma hora — assim uma limpeza não atropela um

    download que outro programa nosso esteja fazendo agora."""

    p = PASTA_BAIXANDO

    if not os.path.isdir(p):

        return

    limite = time.time() - 3600



    def mexido_em(caminho):

        """A data mais recente do que há aí dentro.



        A data da PASTA não serve: a pasta Conteudo nasce no começo da extração

        e fica com a hora de agora, mesmo que tudo lá dentro seja de semanas

        atrás. Perguntando aos arquivos, uma extração abandonada é reconhecida

        como velha e sai; uma acontecendo agora se defende sozinha."""

        if not os.path.isdir(caminho):

            return os.path.getmtime(caminho)

        recente = 0

        for raiz, _sub, arqs in os.walk(caminho):

            for a in arqs:

                try:

                    recente = max(recente, os.path.getmtime(os.path.join(raiz, a)))

                except OSError:

                    pass

        return recente



    try:

        nomes = os.listdir(p)

    except OSError:

        return

    for nome in nomes:

        if nome.lower().endswith(".parte"):

            continue

        alvo = os.path.join(p, nome)

        try:

            if mexido_em(alvo) > limite:

                continue

            if os.path.isdir(alvo):

                shutil.rmtree(alvo, ignore_errors=True)

            else:

                os.remove(alvo)

        except OSError:

            pass          # em uso agora: fica para a próxima abertura

    try:

        os.rmdir(p)

    except OSError:

        pass





def baixar_se_recuperando(url, destino, avisar):
    """Baixa e, se o tropeço for o RELÓGIO, acerta o relógio e tenta de novo.

    Uma tentativa só de recuperação, de propósito: se acertar o relógio não
    resolveu, insistir vira aquela tela parada que já custou uma instalação
    na igreja. Falhou duas vezes, o operador tem de saber.
    """
    try:
        return baixar_retomando(url, destino, avisar)
    except Exception as e:
        if "CERTIFICATE" not in str(e).upper():
            raise
        fora = relogio_errado()
        if fora is None or abs(fora) <= 86400:
            raise
        avisar and avisar(0, 0, 0, 0)
        ok, _ = acertar_relogio()
        if not ok:
            raise
        global _CTX_SSL
        _CTX_SSL = None            # contexto novo: o antigo nasceu na data errada
        return baixar_retomando(url, destino, avisar)


# 3.0.5: o PC da igreja na internet do CELULAR dele gastou mais de 9 GB num dia (11/10/2026).
# O Sistema nunca baixa nada grande sem clique, mas o botão tem de AVISAR antes, quando o Windows
# diz que a conexão é limitada (Configurações > Rede > "Conexão limitada"; o hotspot do iPhone
# costuma vir marcado assim). Pergunta ao próprio Windows (WinRT, sem biblioteca nova), 60 s de cache.
_CONEXAO = {"t": 0.0, "r": {"limitada": False, "sabe": False}}
_PS_CONEXAO = (
    "[void][Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime];"
    "$p=[Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile();"
    "if($p){$c=$p.GetConnectionCost();'' + [int]$c.NetworkCostType + '|' + $c.Roaming + '|' + $c.OverDataLimit}else{'sem'}")


def conexao_limitada():
    """{"limitada": bool, "sabe": bool}. NetworkCostType: 0 desconhecido, 1 sem limite, 2 fixo (franquia), 3 variável (paga por MB)."""
    if time.time() - _CONEXAO["t"] < 60:
        return _CONEXAO["r"]
    r = {"limitada": False, "sabe": False}
    if os.name == "nt":
        try:
            s = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_CONEXAO],
                               capture_output=True, text=True, timeout=8, **SEM_JANELA).stdout.strip()
            if s and s != "sem":
                tipo, roaming, estourou = s.split("|")[:3]
                r = {"limitada": tipo in ("2", "3") or roaming == "True" or estourou == "True", "sabe": tipo != "0"}
        except Exception:
            pass
    _CONEXAO.update({"t": time.time(), "r": r})
    return r


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

        # pasta FIXA (não uma temporária nova a cada vez): é o que deixa fechar

        # o Sistema no meio e continuar o download depois, em vez de recomeçar

        guarda = PASTA_BAIXANDO

        os.makedirs(guarda, exist_ok=True)

        alvo = os.path.join(guarda, "Instalar o Sistema.exe")



        def andamento(feito, total, tentativa, resta=0):

            if tentativa:

                ATUALIZA["txt"] = ("A internet oscilou. Tento de novo em %ds "

                                   "(tentativa %d)…" % (resta, tentativa))

            elif total:

                ATUALIZA.update({"pct": 3 + int(90.0 * feito / total),

                                 "txt": "Baixando a versão nova…"})



        baixar_se_recuperando(url, alvo, andamento)

        ATUALIZA.update({"pct": 96, "txt": "Abrindo o instalador…"})
        # --reabrir: o instalador novo reabre o Sistema no fim E MOSTRA A JANELA
        # DE PROGRESSO (a partir da 2.9.7). --silencioso vai junto só para um
        # instalador antigo, que não conhece --reabrir, não abrir a tela de boas-vindas.
        inst = subprocess.Popen([alvo, "--silencioso", "--reabrir"], **SEM_JANELA)
        # ORDEM DELE (10/10/2026): o Sistema fecha ANTES de instalar, não no último
        # instante. Antes ele ficava aberto enquanto o instalador se desempacotava
        # (60 MB) e só caía quando o instalador o matava. Agora: o instalador subiu
        # e continua vivo 3 s depois -> este Sistema sai sozinho. O instalador novo
        # reabre o Sistema no fim (--reabrir).
        ATUALIZA["txt"] = "Fechando o Sistema para instalar a versão nova…"
        time.sleep(3)
        if inst.poll() is None:
            os._exit(0)
        # O instalador leva um tempo para aparecer (ele se desempacota e depois
        # fecha este Sistema). Antes a frase congelava aqui com "fim": a tela
        # parava de perguntar, parecia travado, e o Samuel quase abriu o Sistema
        # de novo (26/09/2026). Agora o relógio anda até o instalador nos fechar.
        inicio = time.time()
        while time.time() - inicio < 180:
            ATUALIZA["txt"] = ("Abrindo o instalador… %d s — não feche nem abra o "
                               "Sistema: ele reabre sozinho." % int(time.time() - inicio))
            time.sleep(1)
        ATUALIZA.update({"txt": "O instalador não fechou o Sistema em 3 minutos. "
                                "Feche o Sistema e abra de novo pelo atalho da Área de Trabalho.",
                         "fim": True, "rodando": False})

    except Exception as e:

        ATUALIZA.update({"erro": explicar_falha_de_rede(e),

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





ARQ_MARCA_CONTEUDO = "conteudo_versao.txt"





def marca_animacoes(pasta):

    """Assinatura das animações: nome e tamanho de cada arquivo, num md5 só.

    BURACO (10/10/2026, ordem dele: "atualiza conforme a versão de sistema que ele tem"):

    o Atualizar baixa só o instalador LEVE, e as animações das CIAS viajam à parte, no

    Conteudo.zip — quem tem a versão completa nunca recebia animação nova pelo Atualizar.

    Cada release publica esta marca (conteudo_versao.txt); o Sistema compara com a dele."""

    # Conta SÓ o que o indice.json usa (e o próprio índice): o Completar abre o zip POR CIMA

    # e não apaga arquivo velho que saiu — contar a pasta inteira deixaria a marca diferente

    # para sempre, e o Sistema ofereceria baixar de novo a cada abertura.

    import hashlib

    try:

        with open(os.path.join(pasta, "indice.json"), encoding="utf-8") as f:

            indice = json.load(f)

    except Exception:

        return ""

    nomes = {"indice.json"}

    for v in indice.values():

        nomes.update(v if isinstance(v, list) else [v])

    def tam(f):

        try: return os.path.getsize(os.path.join(pasta, f))

        except OSError: return -1

    linhas = "".join("%s:%d\n" % (f, tam(f)) for f in sorted(nomes))

    return hashlib.md5(linhas.encode("utf-8")).hexdigest()





def animacoes_novas(ler_marca_da_nuvem=None):

    """True se a nuvem tem animações diferentes das deste computador — só para quem tem a

    versão COMPLETA (quem tem a leve continua leve: o "Completar" é escolha dele)."""

    if conteudo_falta():

        return False

    if ler_marca_da_nuvem is None:

        def ler_marca_da_nuvem():

            import urllib.request

            url = ("https://github.com/%s/%s/releases/latest/download/%s"

                   % (DONO_GITHUB, REPO_GITHUB, ARQ_MARCA_CONTEUDO))

            with urllib.request.urlopen(url, timeout=8) as r:

                return r.read(200).decode("ascii", "ignore").strip()

    try:

        nuvem = ler_marca_da_nuvem()

    except Exception:

        return False                      # sem internet: nada a oferecer, sem erro na tela

    return bool(nuvem) and nuvem != marca_animacoes(pasta_usuario("animacoes"))





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

        # pasta FIXA: são 610 MB. Fechar o Sistema no meio (ou ele cair) não

        # pode custar o download inteiro de novo — o .parte espera aqui.

        guarda = PASTA_BAIXANDO

        os.makedirs(guarda, exist_ok=True)

        zt = os.path.join(guarda, "Conteudo.zip")



        # ESPAÇO ANTES, NÃO DEPOIS: são 488 MB de zip que viram 496 MB abertos,

        # e o zip só sai do disco depois de aberto — pico de ~1 GB. Descobrir

        # que não cabia DEPOIS de meia hora de download na internet do celular

        # é a pior hora possível para dar essa notícia. (Era 1,3 GB quando as

        # cifras vinham aqui; agora elas vêm dentro do instalador.)

        import ctypes

        livre = ctypes.c_ulonglong(0)

        try:

            ctypes.windll.kernel32.GetDiskFreeSpaceExW(

                ctypes.c_wchar_p(guarda), ctypes.byref(livre), None, None)

        except Exception:

            livre.value = 0

        precisa = 1100 * 1024 * 1024

        if 0 < livre.value < precisa:

            COMPLETA.update({"erro": "Não vai caber: são precisos 1,1 GB livres e há "

                                     "só %d MB. Libere espaço e tente de novo — nada "

                                     "foi mexido." % (livre.value // 1048576),

                             "fim": True, "rodando": False})

            return



        COMPLETA.update({"pct": 1, "txt": "Baixando as animações das CIAS…", "erro": ""})



        def andamento(feito, total, tentativa, resta=0):

            if tentativa:

                COMPLETA["txt"] = ("A internet oscilou. Tento de novo em %ds "

                                   "(tentativa %d) — já vieram %d MB"

                                   % (resta, tentativa, feito // 1048576))

            elif total:

                COMPLETA.update({"pct": int(feito * 90.0 / total),

                                 "txt": "Baixando… %d de %d MB"

                                        % (feito // 1048576, total // 1048576)})



        baixar_se_recuperando(url, zt, andamento)

        COMPLETA.update({"pct": 93, "txt": "Guardando o conteúdo…"})

        with zipfile.ZipFile(zt) as z:

            z.extractall(DADOS_USUARIO)

        try:

            os.remove(zt)

        except OSError:

            pass

        _CATALOGO["dados"] = None      # o catálogo do músico renasce com as melodias

        COMPLETA.update({"pct": 100, "txt": "Pronto! As animações das CIAS estão instaladas.",

                         "fim": True, "rodando": False})

    except Exception as e:

        COMPLETA.update({"erro": explicar_falha_de_rede(e), "fim": True, "rodando": False})





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



# ===== 3.0.9: o par com o computador de apoio =====
def apoios_lembrados():
    try:
        with open(ARQ_APOIOS, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _gravar_apoios(d):
    try:
        os.makedirs(DADOS_USUARIO, exist_ok=True)
        tmp = ARQ_APOIOS + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(tmp, ARQ_APOIOS)
    except Exception:
        pass


def _apoio_publico(chave, a, agora):
    return {"chave": chave, "nome": a["nome"], "ip": a["ip"], "estado": a["estado"], "papel": a["papel"],
            "modo": a.get("modo", "retorno"), "pc": socket.gethostname(),
            "online": agora - a.get("visto", 0) <= APOIO_ONLINE_SEG,
            "identificar": max(0.0, round(a.get("ident_ate", 0) - agora, 2))}


def apoio_ola(nome, ip, denovo=False):
    """O apoio deu sinal de vida. Devolve o que ele deve mostrar (pendente, aceito ou dispensado)."""
    nome = (nome or "").strip()[:40]
    chave = nome or ip or "?"
    agora = time.time()
    with TRAVA:
        a = APOIOS.get(chave)
        if a is None:
            lem = apoios_lembrados().get(chave)
            # par lembrado: volta CALADO (sem pergunta e sem o "1" gigante no meio do culto)
            a = {"nome": nome or ip, "ip": ip, "estado": "aceito" if lem else "pendente",
                 "papel": (lem or {}).get("papel", 2), "modo": (lem or {}).get("modo", "retorno"), "ident_ate": 0}
            APOIOS[chave] = a
        if denovo and a["estado"] == "dispensado":
            a["estado"] = "pendente"
        a["ip"] = ip
        a["visto"] = agora
        return dict(_apoio_publico(chave, a, agora), ok=True)


def apoios_lista():
    agora = time.time()
    with TRAVA:
        return [_apoio_publico(k, a, agora) for k, a in APOIOS.items()]


def apoio_mudar(chave, acao):
    """sim (Usar as duas telas) | nao (Agora não) | pedir (Conectar a tela de retorno) | identificar | trocar |
    modo:retorno (Telão e retorno) | modo:igual (Retorno igual ao telão) | so_telao (Só o telão) | desligar.
    Só o Sim, o Identificar e o Trocar acendem o 1 e o 2."""
    agora = time.time()
    with TRAVA:
        a = APOIOS.get(chave)
        if a is None:
            return {"ok": False, "erro": "esse computador não está na rede"}
        if acao == "sim":
            a["estado"] = "aceito"
            a["ident_ate"] = agora + APOIO_IDENT_SEG
        elif acao == "nao":
            a["estado"] = "dispensado"
        elif acao == "pedir":
            if a["estado"] == "dispensado":
                a["estado"] = "pendente"
        elif acao in ("modo:retorno", "modo:igual"):
            a["modo"] = acao.split(":", 1)[1]
        elif acao == "identificar":
            a["ident_ate"] = agora + APOIO_IDENT_SEG
        elif acao == "trocar":
            a["papel"] = 1 if a["papel"] == 2 else 2
            a["ident_ate"] = agora + APOIO_IDENT_SEG
        elif acao in ("desligar", "so_telao"):
            a["estado"] = "dispensado"
            a["papel"] = 2
        else:
            return {"ok": False, "erro": "ação desconhecida"}
        r = _apoio_publico(chave, a, agora)
    lem = apoios_lembrados()
    if r["estado"] == "aceito":
        lem[chave] = {"nome": r["nome"], "papel": r["papel"], "modo": r["modo"], "em": time.strftime("%Y-%m-%d %H:%M")}
    else:
        lem.pop(chave, None)
    _gravar_apoios(lem)
    return dict(r, ok=True)


def anunciar_na_rede(porta):
    """A cada 2 s grita na rede local que existe um Sistema aqui. O modo gestos do Vaio escuta e
    vem direto, sem varrer 254 endereços. Sobre o Tailscale não há broadcast: lá a varredura continua."""
    if os.environ.get("SISTEMA_SO_LOCAL"):
        return
    msg = json.dumps({"sistema": "icm-projecao", "porta": porta, "nome": socket.gethostname(),
                      "versao": VERSAO}).encode("utf-8")
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
            try:
                s.sendto(msg, (a, PORTA_ANUNCIO))
            except Exception:
                pass
        time.sleep(2)





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





def _grava_png(caminho, largura, altura, linhas_rgb):

    """PNG sem PIL (o PIL fica fora do pacote): só zlib, que vem com o Python."""

    import zlib, struct

    def bloco(tipo, dados):

        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados) & 0xffffffff)

    cru = b"".join(b"\x00" + l for l in linhas_rgb)          # filtro 0 em cada linha

    with open(caminho, "wb") as f:

        f.write(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))

                + bloco(b"IDAT", zlib.compress(cru, 3)) + bloco(b"IEND", b""))





def converter_pdf(caminho, destino, larg=1920, alt=1080):

    """PDF -> uma tela (PNG) por página, com o motor de PDF que vai DENTRO do Sistema.

    HISTÓRIA (10/10/2026, ele testando no Vaio: "não consegui converter esse arquivo.

    Imagina isso na hora do vamos ver"): esta função só COPIAVA o PDF e contava as

    páginas, mas importar() procura PNG/JPG na pasta — não achava nenhum e respondia

    "Não consegui converter". Importar PDF nunca funcionou, nem no Windows.

    Regra dele: o Sistema roda em qualquer máquina, sem programa de fora. O pypdfium2

    traz o PDFium (o leitor de PDF do Chrome) dentro da própria biblioteca, ~6 MB,

    para Windows e Linux. Teste: ferramentas\\testes\\test_sistema_importar.py

    """

    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(caminho)

    try:

        for i in range(len(pdf)):

            pg = pdf[i]

            w, h = pg.get_size()

            esc = min(larg / w, alt / h)                     # cabe INTEIRA no telão, sem esticar

            bm = pg.render(scale=esc, rev_byteorder=True, fill_color=(255, 255, 255, 255))

            bw, bh, passo, n = bm.width, bm.height, bm.stride, bm.n_channels

            buf = bytes(bm.buffer)

            if n == 3:

                linhas = [buf[y * passo: y * passo + bw * 3] for y in range(bh)]

            else:                                            # RGBx: tira o 4º canal, em fatias

                linhas = []

                for y in range(bh):

                    l = buf[y * passo: y * passo + bw * n]; o = bytearray(bw * 3)

                    o[0::3] = l[0::n]; o[1::3] = l[1::n]; o[2::3] = l[2::n]

                    linhas.append(bytes(o))

            _grava_png(os.path.join(destino, "Slide%03d.png" % (i + 1)), bw, bh, linhas)

    finally:

        pdf.close()

    return True





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

    notas = []
    if ext in (".pptx", ".ppsx"):
        try:
            notas = notas_do_pptx(caminho)
            if any(notas):
                with open(os.path.join(destino, ARQ_NOTAS), "w", encoding="utf-8") as f:
                    json.dump(notas, f, ensure_ascii=False)
        except Exception:
            notas = []                      # nota é ajuda do operador: falhar aqui não derruba a importação

    textos = gravar_textos(caminho, ext, destino, len(rel))

    return {"ok": True, "nome": nome, "slides": rel, "notas": _alinha_notas(notas, len(rel)), "textos": textos}


# ===== TEXTO DE CADA PÁGINA (nova tela de apresentação, 12/10/2026): a busca "nº ou palavra" =====
# Palavra dele (12/10 01h38): "insano de tão bom, é a cara do sistema". O número vai direto à página;
# a PALAVRA procura no texto que fica gravado aqui, na importação, num textos.json ao lado das telas.
# PDF: o texto das páginas pelo mesmo motor que desenha as telas (pypdfium2, que já vai dentro do Sistema).
# PowerPoint: o texto das formas de cada slide, lido do próprio pptx (é um zip; não precisa do PowerPoint).
# Texto que está DENTRO de uma imagem não sai daqui: a apresentação continua achando a página pelo número.
ARQ_TEXTOS = "textos.json"


def textos_do_pptx(caminho):
    """Lista com o texto das formas de cada slide, na ORDEM DA APRESENTAÇÃO ("" = slide sem texto)."""
    import zipfile, posixpath
    import xml.etree.ElementTree as ET
    P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    with zipfile.ZipFile(caminho) as z:
        nome_rels = "ppt/_rels/presentation.xml.rels"
        alvo = {r.get("Id"): posixpath.normpath(posixpath.join("ppt", r.get("Target", "")))
                for r in ET.fromstring(z.read(nome_rels)).iter(REL + "Relationship")} if nome_rels in z.namelist() else {}
        textos = []
        for s in ET.fromstring(z.read("ppt/presentation.xml")).iter(P + "sldId"):
            parte = alvo.get(s.get(R + "id"))
            if not parte or parte not in z.namelist():
                textos.append("")
                continue
            xml = ET.fromstring(z.read(parte))
            if xml.get("show") == "0":       # slide escondido: o PowerPoint não exporta tela dele
                continue
            linhas = ["".join(t.text or "" for t in par.iter(A + "t")).strip() for par in xml.iter(A + "p")]
            textos.append("\n".join(l for l in linhas if l))
        return textos


def textos_do_pdf(caminho):
    """Lista com o texto de cada página do PDF ("" = página só de imagem)."""
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(caminho)
    textos = []
    try:
        for i in range(len(pdf)):
            pg = pdf[i]
            tp = pg.get_textpage()
            try:
                textos.append((tp.get_text_range() or "").replace("\r", "").strip())
            finally:
                tp.close()
                pg.close()
    finally:
        pdf.close()
    return textos


def gravar_textos(caminho, ext, destino, n):
    """Lê o texto de cada página e grava o textos.json. Falhar aqui NUNCA derruba a importação."""
    try:
        if ext in (".pptx", ".ppsx"):
            textos = textos_do_pptx(caminho)
        elif ext == ".pdf":
            textos = textos_do_pdf(caminho)
        else:
            return [""] * n
        textos = _alinha_notas(textos, n)
        if any(textos):
            with open(os.path.join(destino, ARQ_TEXTOS), "w", encoding="utf-8") as f:
                json.dump(textos, f, ensure_ascii=False)
        return textos
    except Exception:
        return [""] * n


def _textos_da_pasta(pasta, n):
    """As apresentações antigas, sem textos.json, voltam com "" em cada página (a busca por número segue valendo)."""
    try:
        with open(os.path.join(pasta, ARQ_TEXTOS), encoding="utf-8") as f:
            return _alinha_notas([str(x) for x in json.load(f)], n)
    except Exception:
        return [""] * n


# ===== NOTAS DO APRESENTADOR (3.0.3): as "anotações" de cada slide do PowerPoint =====
# Pedido dele (11/10/2026 09h30): o Modo Apresentador "idêntico ao PowerPoint" — e o PowerPoint
# mostra, embaixo do slide seguinte, as anotações do slide atual.
ARQ_NOTAS = "notas.json"


def notas_do_pptx(caminho):
    """Lista com o texto das anotações de cada slide, na ORDEM DA APRESENTAÇÃO ("" = sem nota).
    Lê direto do pptx (é um zip): não precisa do PowerPoint."""
    import zipfile, posixpath
    import xml.etree.ElementTree as ET
    P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    def rels(z, parte):
        nome = posixpath.join(posixpath.dirname(parte), "_rels", posixpath.basename(parte) + ".rels")
        if nome not in z.namelist():
            return []
        return [(r.get("Id"), r.get("Type", ""), posixpath.normpath(posixpath.join(posixpath.dirname(parte), r.get("Target", ""))))
                for r in ET.fromstring(z.read(nome)).iter(REL + "Relationship")]
    with zipfile.ZipFile(caminho) as z:
        alvo = {i: t for i, _, t in rels(z, "ppt/presentation.xml")}
        ordem = [alvo.get(s.get(R + "id")) for s in ET.fromstring(z.read("ppt/presentation.xml")).iter(P + "sldId")]
        notas = []
        for sl in ordem:
            texto = ""
            nota = [t for _, tipo, t in rels(z, sl or "") if tipo.endswith("/notesSlide")] if sl else []
            if nota and nota[0] in z.namelist():
                for sp in ET.fromstring(z.read(nota[0])).iter(P + "sp"):
                    ph = sp.find(".//" + P + "ph")
                    if ph is None or ph.get("type") != "body":
                        continue           # só o corpo da anotação (fora: número do slide, miniatura)
                    texto = "\n".join("".join(t.text or "" for t in par.iter(A + "t")) for par in sp.iter(A + "p")).strip()
            notas.append(texto)
        return notas


def _alinha_notas(notas, n):
    """Uma nota por tela: completa com "" ou corta para o número de telas."""
    notas = list(notas or [])[:n]
    return notas + [""] * (n - len(notas))


def _notas_da_pasta(pasta, n):
    try:
        with open(os.path.join(pasta, ARQ_NOTAS), encoding="utf-8") as f:
            return _alinha_notas([str(x) for x in json.load(f)], n)
    except Exception:
        return [""] * n





# APRESENTAÇÕES SALVAS — ordem dele, 10/10/2026 15h11: a página de slides fica "igual a

# Fundos": quadradinhos com miniatura, apagáveis, e a da Evangelização de outubro já vem

# DENTRO do Sistema como exemplo ("para quando baixarem da nuvem, ela já vir como DEMO").

# As que vêm com o Sistema moram em BASE/apresentacoes (só leitura: esconder é do lado da

# tela, como os fundos de fábrica); as que o operador importou, em SAIDA (essas apagam).

APRESENTACOES_DEMO = os.path.join(BASE, "apresentacoes")





def _telas_da_pasta(pasta):

    # 3.0.7: pasta que começa com "_" é peça de dentro da tela (as camadas do _movimento), não tela
    fs = []
    for r, subs, nomes in os.walk(pasta):
        subs[:] = [d for d in subs if not d.startswith("_")]
        fs += [os.path.join(r, f) for f in nomes if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))]

    def chave(p):

        b = os.path.basename(p)

        dig = "".join(c for c in b if c.isdigit())

        return (int(dig) if dig else 0, b)

    return sorted(fs, key=chave)





def _movimento_da_pasta(pasta, url_pasta, n):
    """3.0.7 — a animação DENTRO da tela (o (4/5), ordem dele 11/10 17h20). movimento.json, feito pelo
    ferramentas/movimento_do_pptx.py, diz por slide: o fundo parado, as camadas que se mexem e a linha do tempo
    exata do PowerPoint. Devolve {índice da tela (0-based, em texto): dados com os endereços já prontos}.
    Sem o arquivo (ou com ele estragado) a apresentação toca do jeito de antes: uma imagem por tela."""
    from urllib.parse import quote
    try:
        with open(os.path.join(pasta, "movimento.json"), encoding="utf-8") as f:
            m = json.load(f)
        saida = {}
        for k, sl in (m.get("slides") or {}).items():
            i = int(k) - 1
            if not 0 <= i < n:
                continue
            sl = dict(sl, base=url_pasta + quote(sl["base"]),
                      camadas=[dict(c, src=url_pasta + quote(c["src"])) for c in sl.get("camadas", [])])
            sl.pop("confere", None)
            saida[str(i)] = sl
        return saida
    except Exception:
        return {}


def listar_apresentacoes():

    from urllib.parse import quote

    lista = []

    for base, prefixo, demo in ((APRESENTACOES_DEMO, "apresentacoes/", True), (SAIDA, "slides_importados/", False)):

        if not os.path.isdir(base):

            continue

        # o louvor toca ANTES da aula, então vem antes na lista (ordem dele 10/10 18h36). Até a 3.0.5 isso saía do
        # alfabeto ("— Período" < "— Você"); com os nomes da 3.0.6 ("Louvores da Evangelização..." e "Evangelização...")
        # o alfabeto inverteria, então a regra fica escrita.
        for nome in sorted(os.listdir(base), key=lambda n: (not n.startswith("Louvores"), n)):

            pasta = os.path.join(base, nome)

            telas = _telas_da_pasta(pasta) if os.path.isdir(pasta) else []

            if telas:

                lista.append({"nome": nome, "demo": demo, "slides": [

                    quote(prefixo + os.path.relpath(p, base).replace("\\", "/")) for p in telas],

                    "notas": _notas_da_pasta(pasta, len(telas)),
                    "textos": _textos_da_pasta(pasta, len(telas)),
                    "mov": _movimento_da_pasta(pasta, quote(prefixo + nome + "/"), len(telas))})

    return lista





def apagar_apresentacao(nome):

    """Só apaga o que o OPERADOR importou, e só dentro da pasta dele."""

    raiz_ = os.path.normpath(SAIDA)

    alvo = os.path.normpath(os.path.join(raiz_, nome or ""))

    if not nome or os.path.dirname(alvo) != raiz_ or not os.path.isdir(alvo):

        return {"ok": False, "erro": "Apresentação não encontrada."}

    shutil.rmtree(alvo)

    return {"ok": True}





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

                BUSCA["t"] = time.time()     # marca que a tela está acordada

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

        if self.path.startswith("/api/apoios"):          # 3.0.9: o painel quer saber quem quer ser a 2ª tela
            return self._json({"ok": True, "apoios": apoios_lista()})
        if self.path.startswith("/api/apoio"):           # 3.0.9: o apoio (retorno.html) dá sinal de vida
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            return self._json(apoio_ola((q.get("nome") or [""])[0], self.client_address[0],
                                        denovo=bool(q.get("denovo"))))
        if self.path.startswith("/api/estado"):          # o celular pergunta o que está no telão

            with TRAVA:

                # "idade" = há quantos segundos a tela do Sistema não publica nada.

                # Quem responde aqui é o Python, que continua de pé mesmo se a

                # tela do computador travar ou for fechada — sem isto o celular

                # ficaria mostrando "AO VIVO" para sempre.

                idade = time.time() - ESTADO.get("ts", 0) if ESTADO.get("ts") else 999

                return self._json({"ok": True, "estado": dict(ESTADO), "idade": round(idade, 1)})

        # ANTES de "/api/animacoes": aquela rota começa igual e engoliria esta

        if self.path.startswith("/api/animacoes-novas"):   # a completa tem animação nova na nuvem?

            return self._json({"ok": True, "novas": animacoes_novas()})

        if self.path.startswith("/api/apresentacoes"):   # as salvas + a demo que vem junto

            return self._json({"ok": True, "lista": listar_apresentacoes()})

        if self.path.startswith("/api/animacoes"):       # louvores de CIAS com animação

            return self._json({"ok": True, "indice": ler_indice("animacoes")})

        if self.path.startswith("/api/afinador"):

            # Onde mora o afinador. O celular pergunta isto para saber se pode

            # oferecer o botão: sem a porta segura, o microfone não abre lá.

            # 0 = não subiu (o Sistema segue normal; o afinador fica só aqui).

            return self._json({"ok": True, "porta": PORTAS.get("segura", 0),

                               "seguro": bool(PORTAS.get("segura"))})

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

            q = parse_qs(u.query)

            afinacao = (q.get("em") or ["C"])[0]

            return self._json(material_do_louvor(chave, afinacao))

        if self.path.startswith("/api/atualizacao"):     # existe versão mais nova?

            nova = versao_mais_nova()

            tem = bool(nova) and _versao_tupla(nova) > _versao_tupla(VERSAO)

            return self._json({"ok": nova is not None, "atual": VERSAO,

                               "nova": nova, "tem": tem})

        if self.path.startswith("/api/atualizar"):       # andamento da atualização

            return self._json({"ok": True, **ATUALIZA})

        if self.path.startswith("/api/conexao"):         # 3.0.5: a internet é "limitada" (celular)?

            return self._json({"ok": True, **conexao_limitada()})

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

        if self.path.startswith("/api/apoio"):            # 3.0.9: a resposta do operador (do painel OU do próprio retorno)
            try:
                n = int(self.headers.get("Content-Length", 0))
                c = json.loads(self.rfile.read(n).decode("utf-8"))
                return self._json(apoio_mudar(str(c.get("chave", "")), str(c.get("acao", ""))))
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

        if self.path.startswith("/api/apagar-apresentacao"):

            try:

                n = int(self.headers.get("Content-Length", 0) or 0)

                corpo = json.loads(self.rfile.read(n) or b"{}")

                return self._json(apagar_apresentacao(corpo.get("nome")))

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



def monitor_do_painel():
    """O retângulo {x, y, w, h} do monitor onde está a janela do painel ("Sistema v..."), ou None."""
    try:
        import win32api
        hs = janelas_do_processo("Sistema v")
        if not hs:
            return None
        info = win32api.GetMonitorInfo(win32api.MonitorFromWindow(hs[0], 2))   # 2 = o mais próximo
        x1, y1, x2, y2 = info["Monitor"]
        return {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1}
    except Exception:
        return None


def telao_externo(telas=None, painel=None):

    """O monitor do telão: a tela onde o PAINEL NÃO ESTÁ (3.0.10, regra dele: "o telão nunca na cara do operador").
    Antes era "a primeira que não é a principal": se o operador deixava o painel na tela do HDMI, o telão abria
    por cima dele. Sem saber onde está o painel, fica o jeito de antes."""

    telas = monitores() if telas is None else telas

    if len(telas) < 2:

        return None

    painel = monitor_do_painel() if painel is None else painel

    if painel:

        mesma = lambda m: (m["x"], m["y"], m["w"], m["h"]) == (painel["x"], painel["y"], painel["w"], painel["h"])

        livres = [m for m in telas if not mesma(m)]

        if livres and len(livres) < len(telas):

            return next((m for m in livres if not m["principal"]), livres[0])

    return next((m for m in telas if not m["principal"]), None)


def estender_telas():
    """Pede ao Windows "estender" a área de trabalho (o que o operador faria com Windows+P > Estender). Não precisa de
    administrador. Roda escondido (SEM_JANELA). O Lenovo da igreja ficava em DUPLICAR e o telão não tinha para onde ir."""
    if os.name != "nt":
        return False
    try:
        exe = os.path.join(os.environ.get("SystemRoot", "C:" + os.sep + "Windows"), "System32", "DisplaySwitch.exe")
        subprocess.Popen([exe, "/extend"], **SEM_JANELA)
        return True
    except Exception as e:
        sys.stderr.write("estender telas: %s" % e + chr(10))
        return False



def janelas_do_processo(prefixo):

    """As janelas DESTE programa cujo título começa com o prefixo (visíveis ou não)."""

    import win32gui, win32process

    achadas = []

    def cada(h, _):

        try:

            if (win32process.GetWindowThreadProcessId(h)[1] == os.getpid()

                    and win32gui.GetWindowText(h).startswith(prefixo)):

                achadas.append(h)

        except Exception:

            pass

        return True

    win32gui.EnumWindows(cada, None)

    return achadas





class Ponte:

    """O que a tela do Sistema pode pedir ao Windows."""

    # O VIGIA DO TELÃO (15/10/2026, culto de quinta: "do nada para de identificar o
    # HDMI e joga a tela pra trás da tela de controle"). Quando o projetor ou a TV
    # perde o sinal um instante, o Windows refaz o arranjo das telas e manda a
    # janela da Projeção para o monitor principal, atrás do Sistema. O Sistema só
    # escolhia o HDMI uma vez, ao abrir, e nunca mais olhava. Agora um vigia olha a
    # cada VIGIA_SEG: HDMI sumiu -> esconde o telão (não fica atrás do controle nem
    # cobre o controle depois); HDMI voltou ou a janela está na tela errada -> leva
    # de volta ao HDMI em tela cheia. Mede e move pelo MESMO caminho do Windows
    # (win32), sem a conta de escala do pywebview, que multiplica a posição pela
    # escala da tela principal (125%/150% num notebook) e erra o HDMI.

    VIGIA_SEG = 1.5

    def __init__(self):

        self.projecao = None

        self.url = ""

        self._vigia = None

        self._no_hdmi = False       # a Projeção foi aberta no HDMI (só então o vigia esconde quando ele some)

        self._escondida = False     # quem escondeu foi o vigia (só ele mostra de novo)



    def monitores(self):

        return monitores()

    def estender(self):
        """3.0.10: uma tela só no Projetar = pede ao Windows para estender (o painel espera a 2ª tela aparecer)."""
        return {"ok": estender_telas()}

    def tela_cheia(self):
        """F11 no painel (vídeo dele, 17/10): o WebView2 não repassa a tecla à janela, então o painel pede aqui."""
        import webview
        for j in webview.windows:
            if (j.title or "").startswith("Sistema v"):
                j.toggle_fullscreen()
                return True
        return False



    def abrir_projecao(self):

        import webview

        if self.projecao is not None:

            try:

                if os.name == "nt" and self._no_hdmi and telao_externo() is None:

                    # o HDMI sumiu e o vigia escondeu o telão: mostrar agora seria
                    # cobrir a tela de controle. Ele volta sozinho quando o sinal voltar.

                    return {"ok": True, "externa": False, "sumiu": True}

                self.projecao.show()

                self._escondida = False

                return {"ok": True, "externa": self.por_no_telao() if os.name == "nt" else True}

            except Exception: self.projecao = None

        telas = monitores()

        externa = telao_externo(telas)

        alvo = externa or (telas[0] if telas else {"x": 0, "y": 0, "w": 1280, "h": 720})

        self._no_hdmi = bool(externa)

        self._escondida = False

        self.projecao = webview.create_window(

            "Projeção", self.url + "projecao.html?nativo=1",

            x=alvo["x"], y=alvo["y"], width=alvo["w"], height=alvo["h"],

            frameless=bool(externa), fullscreen=bool(externa), background_color="#000000")

        self.projecao.events.closed += self._fechou

        self._ligar_vigia()

        return {"ok": True, "externa": bool(externa)}



    def _ligar_vigia(self):

        if os.name != "nt" or (self._vigia is not None and self._vigia.is_alive()):

            return

        def roda():

            while self.projecao is not None:

                try: self.por_no_telao()

                except Exception: pass

                time.sleep(self.VIGIA_SEG)

        self._vigia = threading.Thread(target=roda, name="vigia-telao", daemon=True)

        self._vigia.start()



    def por_no_telao(self):

        """Põe a janela da Projeção no HDMI se ela não estiver lá. True = está no HDMI."""

        if os.name != "nt" or self.projecao is None:

            return False

        import win32gui, win32con

        hs = janelas_do_processo("Proje")

        if not hs:

            return False                       # ainda nascendo

        h = hs[0]

        ext = telao_externo()

        if ext is None:

            # HDMI sumiu: o Windows jogou o telão para a tela principal. Esconde.

            if self._no_hdmi and win32gui.IsWindowVisible(h):

                win32gui.ShowWindow(h, win32con.SW_HIDE)

                self._escondida = True

            return False

        x1, y1, x2, y2 = win32gui.GetWindowRect(h)

        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        no_lugar = (ext["x"] <= cx < ext["x"] + ext["w"] and ext["y"] <= cy < ext["y"] + ext["h"]

                    and x2 - x1 >= ext["w"] * 0.95 and y2 - y1 >= ext["h"] * 0.95)

        visivel = win32gui.IsWindowVisible(h)

        if no_lugar and (visivel or not self._escondida):

            return visivel

        if not visivel and not self._escondida:

            return False                       # escondida por outro motivo: não é com o vigia

        # leva ao HDMI: tira do "maximizado" da tela velha e cobre o HDMI inteiro

        win32gui.ShowWindow(h, win32con.SW_SHOWNOACTIVATE)

        estilo = win32gui.GetWindowLong(h, win32con.GWL_STYLE)

        if estilo & (win32con.WS_CAPTION | win32con.WS_THICKFRAME):

            # foi aberta sem HDMI (janela comum): sem borda, como a tela cheia faz

            win32gui.SetWindowLong(h, win32con.GWL_STYLE,

                                   estilo & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME))

        win32gui.SetWindowPos(h, 0, ext["x"], ext["y"], ext["w"], ext["h"],

                              win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE

                              | win32con.SWP_FRAMECHANGED | win32con.SWP_SHOWWINDOW)

        self._no_hdmi = True

        self._escondida = False

        return True



    def _fechou(self):

        self.projecao = None

        self._no_hdmi = False

        self._escondida = False



    def projecao_aberta(self):

        """A janela do telão ainda existe?



        Sem isto, se alguém fechasse a janela da Projeção, o painel continuava

        dizendo "ao vivo" e o celular ficava com a bolinha vermelha para sempre —

        o operador achava que estava projetando sem telão nenhum.

        """

        return {"ok": True, "aberta": self.projecao is not None}



    # 3.0.9: DUAS SAÍDAS NO MESMO PC. Com duas telas externas (telão + TV de apoio), a apresentação
    # especial abre o retorno na 2ª sozinha. "Só desliga quando puxar o HDMI": o vigia fecha quando
    # a 2ª tela some. Com uma tela externa só, não faz nada (o normal de sempre).
    def segunda_tela(self):
        externas = [m for m in monitores() if not m["principal"]]
        return externas[1] if len(externas) >= 2 else None

    def abrir_apoio_local(self):
        import webview
        alvo = self.segunda_tela()
        if alvo is None:
            return {"ok": True, "aberto": False}
        if getattr(self, "apoio_local", None) is not None:
            return {"ok": True, "aberto": True}
        self.apoio_local = webview.create_window(
            "Retorno", self.url + "retorno.html?local=1",
            x=alvo["x"], y=alvo["y"], width=alvo["w"], height=alvo["h"],
            frameless=True, fullscreen=True, background_color="#000000")
        def fechou():
            self.apoio_local = None
        self.apoio_local.events.closed += fechou
        def vigia():
            while getattr(self, "apoio_local", None) is not None:
                time.sleep(self.VIGIA_SEG)
                if self.segunda_tela() is None and self.apoio_local is not None:
                    try:
                        self.apoio_local.destroy()
                    except Exception:
                        pass
                    self.apoio_local = None
        threading.Thread(target=vigia, name="vigia-apoio", daemon=True).start()
        return {"ok": True, "aberto": True}

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

    # A JANELA NATIVA DO WINDOWS, nao o tkinter. O tkinter entrava aqui so' para

    # esta janelinha e arrastava 8 MB de Tcl/Tk para dentro do programa. O

    # pywin32 ja' viaja junto (e' ele que converte o PowerPoint), e a janela que

    # ele abre e' a que o operador ja' conhece de todo programa do Windows.

    import win32con

    import win32gui

    filtro = ("Apresentações e PDF\0*.pptx;*.ppt;*.ppsx;*.pps;*.odp;*.pdf\0"

              "Imagens\0*.png;*.jpg;*.jpeg\0"

              "Todos os arquivos\0*.*\0")

    try:

        cam, _, _ = win32gui.GetOpenFileNameW(

            InitialDir=os.path.expanduser("~"),

            Title="Escolha a apresentação",

            Filter=filtro,

            Flags=(win32con.OFN_EXPLORER | win32con.OFN_FILEMUSTEXIST

                   | win32con.OFN_HIDEREADONLY))

        return cam or ""

    except Exception:

        return ""            # fechou a janela sem escolher





def porta_livre(p):

    with socket.socket() as s:

        return s.connect_ex(("127.0.0.1", p)) != 0





# ---------------------------------------------------------------------------

# A SEGUNDA PORTA — a segura, e por que ela existe

#

# O afinador precisa do microfone, e o navegador só entrega o microfone a uma

# página que chegou por endereço SEGURO (https). Não é sobre o que a página faz

# com o áudio — o afinador nem manda áudio para lugar nenhum — é sobre PODER

# CONFIAR que a página que chegou é a que o Sistema mandou. Em http qualquer um

# na mesma rede poderia trocá-la no caminho, e o navegador não tem como saber.

#

# Por que DUAS portas e não só a segura:

#   - a porta de todo dia (http) NUNCA pode falhar. Ela não avisa nada e não

#     quebra quando o roteador troca o IP do computador.

#   - o certificado é assinado pelo próprio Sistema (não há autoridade dentro da

#     igreja para assinar), então o celular pergunta uma vez se confia. Quem vai

#     afinar é músico e chega antes; o operador no meio do culto não pode topar

#     com essa pergunta.

#

# O certificado é gerado UMA VEZ e guardado nos dados do usuário. Ele leva no

# corpo todos os endereços do computador na rede, para o celular não reclamar de

# nome trocado.

# ---------------------------------------------------------------------------

PORTA_SEGURA = 8766

PORTAS = {"comum": 0, "segura": 0}





def _meus_enderecos():

    """Todos os IPs deste computador na rede local, mais localhost."""

    ips = {"127.0.0.1"}

    try:

        for inf in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):

            ips.add(inf[4][0])

    except Exception:

        pass

    try:                                     # o IP que sai para a rede de fato

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.connect(("8.8.8.8", 80)); ips.add(s.getsockname()[0]); s.close()

    except Exception:

        pass

    return sorted(ips)





def certificado(pasta):

    """Devolve (arquivo_cert, arquivo_chave), gerando se ainda não existir ou se

    o computador ganhou um endereço novo."""

    from cryptography import x509

    from cryptography.x509.oid import NameOID

    from cryptography.hazmat.primitives import hashes, serialization

    from cryptography.hazmat.primitives.asymmetric import rsa

    import datetime, ipaddress



    os.makedirs(pasta, exist_ok=True)

    cert = os.path.join(pasta, "sistema.crt")

    chave = os.path.join(pasta, "sistema.key")

    ips = _meus_enderecos()

    marca = os.path.join(pasta, "sistema.enderecos")



    # o certificado vale para os endereços que ele tinha quando nasceu; se a

    # rede mudou, refaz — senão o celular acusa nome trocado

    antigo = ""

    try:

        with open(marca, encoding="utf-8") as f:

            antigo = f.read().strip()

    except Exception:

        pass

    if os.path.exists(cert) and os.path.exists(chave) and antigo == ",".join(ips):

        return cert, chave



    k = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    nome = x509.Name([

        x509.NameAttribute(NameOID.COMMON_NAME, "Sistema - Projecao da igreja"),

        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Sistema"),

    ])

    alt = [x509.DNSName("localhost")]

    for ip in ips:

        try: alt.append(x509.IPAddress(ipaddress.ip_address(ip)))

        except Exception: pass

    agora = datetime.datetime.now(datetime.timezone.utc)

    c = (x509.CertificateBuilder()

         .subject_name(nome).issuer_name(nome).public_key(k.public_key())

         .serial_number(x509.random_serial_number())

         .not_valid_before(agora - datetime.timedelta(days=1))

         .not_valid_after(agora + datetime.timedelta(days=3650))

         .add_extension(x509.SubjectAlternativeName(alt), critical=False)

         .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)

         .sign(k, hashes.SHA256()))

    with open(chave, "wb") as f:

        f.write(k.private_bytes(serialization.Encoding.PEM,

                                serialization.PrivateFormat.TraditionalOpenSSL,

                                serialization.NoEncryption()))

    with open(cert, "wb") as f:

        f.write(c.public_bytes(serialization.Encoding.PEM))

    with open(marca, "w", encoding="utf-8") as f:

        f.write(",".join(ips))

    return cert, chave





def subir_porta_segura(pasta):

    """Sobe a MESMA aplicação numa porta https, só para quem precisa do

    microfone. Se der errado, o Sistema segue normal — a porta de todo dia não

    depende desta em nada."""

    try:

        import ssl

        cert, chave = certificado(pasta)

        p = PORTA_SEGURA

        while not porta_livre(p) and p < PORTA_SEGURA + 20:

            p += 1

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        ctx.load_cert_chain(cert, chave)

        srv = socketserver.ThreadingTCPServer((ENDERECO_REDE, p), Handler)

        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)

        threading.Thread(target=liberar_no_firewall, args=(p,), daemon=True).start()

        threading.Thread(target=srv.serve_forever, daemon=True).start()

        return p

    except Exception as e:

        print("porta segura indisponivel (%s) - o afinador so vai funcionar no computador" % e)

        return 0





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





def tarefa_acertar_relogio():
    """O programa reaberto COM permissão, só para isto: acertar e sair."""
    ok, _ = acertar_relogio()
    return 0 if ok else 1


def main():

    marcar_splash(0.10)                        # Python de pé

    threading.Thread(target=_rastejar, daemon=True).start()

    # a faxina do que a atualização anterior deixou para trás vai em segundo

    # plano: mexe em disco e não pode atrasar a abertura nem um décimo

    threading.Thread(target=limpar_baixados, daemon=True).start()

    os.makedirs(SAIDA, exist_ok=True)

    porta = PORTA

    while not porta_livre(porta) and porta < PORTA + 20:

        porta += 1

    socketserver.TCPServer.allow_reuse_address = True

    # 0.0.0.0 = aceita também o celular na mesma rede (hotspot ou wi-fi da igreja)

    srv = socketserver.ThreadingTCPServer((ENDERECO_REDE, porta), Handler)

    marcar_splash(0.25)                        # porta achada e servidor criado

    threading.Thread(target=liberar_no_firewall, args=(porta,), daemon=True).start()
    threading.Thread(target=anunciar_na_rede, args=(porta,), name="anuncio-udp", daemon=True).start()

    threading.Thread(target=srv.serve_forever, daemon=True).start()

    raiz_url = "http://127.0.0.1:%d/" % porta

    # a porta segura sobe junto, em segundo plano: gerar o certificado leva

    # cerca de um segundo e não pode atrasar a abertura do programa

    threading.Thread(target=lambda: PORTAS.update(

        {"segura": subir_porta_segura(pasta_usuario("certificado"))}), daemon=True).start()

    PORTAS["comum"] = porta

    time.sleep(0.3)

    marcar_splash(0.35)                        # servidor no ar



    # JANELA PRÓPRIA DO SISTEMA (sem Edge, com o nosso ícone na barra de tarefas)

    try:

        if os.environ.get("SISTEMA_NAVEGADOR") == "1":

            raise RuntimeError("modo navegador escolhido")



        # SÃO DOIS ESTRANGULAMENTOS DIFERENTES, e cada um pede um remédio.

        # (1) Janela COBERTA por outra: o motor de tela a considera escondida e,

        #     depois de alguns minutos, deixa os temporizadores acordarem uma

        #     vez por MINUTO. Quem busca os comandos do celular é um

        #     temporizador. Estas bandeiras desligam isso. A da occlusion é a

        #     que impede o Windows de declarar a janela "tapada".

        # (2) Janela MINIMIZADA: aí a suspensão é mais funda e bandeira nenhuma

        #     alcança (medido — ver acordar_janela, que é o remédio desse caso).

        os.environ.setdefault("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS",

                              "--disable-background-timer-throttling "

                              "--disable-backgrounding-occluded-windows "

                              "--disable-renderer-backgrounding "

                              "--disable-features=CalculateNativeWinOcclusion")

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

        # o vigia que desminimiza a janela quando o celular fala e a tela está

        # dormindo. Ele acha a janela pelo TÍTULO, no Windows — não precisa

        # deste objeto aqui (ver acordar_janela).

        threading.Thread(target=acordar_janela, daemon=True).start()

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

    # antes de tudo: se o Windows nos reabriu com permissão só para acertar o
    # relógio, faz isso e sai. Nenhuma janela, nenhum servidor.
    if "--acertar-relogio" in sys.argv:
        sys.exit(tarefa_acertar_relogio())
    main()

