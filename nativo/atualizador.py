# -*- coding: utf-8 -*-
"""O ATUALIZAR do Sistema 4.0 (o Nativo), 08/11/2026. Decisão da HD pela ordem dele (23h23 de 07/11): o Nativo é o
PRÓXIMO Sistema, versão 4.0.0, publicado na release PRINCIPAL (releases/latest) com o mesmo "Instalar-o-Sistema.exe"
que a 3.0.12/3.0.13 já baixam. Então:
  - quem tem a 3.0.x clica Atualizar (o código DELA, intocado) e recebe o 4.0;
  - o 4.0 lê o mesmo latest, compara pelo NÚMERO e, se houver mais novo, baixa e roda o instalador com
    "--silencioso --reabrir" (o mesmo contrato da 3.0.x) e fecha.
As regras são as da 3.0.13 (sistema.versao_mais_nova e _atualizar_thread); o download é o baixar_se_recuperando DELA
(retoma, tenta de novo, acerta o relógio). Só o endereço é montado aqui, para a prova trocar pelo servidor FALSO:
  NATIVO_GITHUB   a raiz (padrão https://github.com; nas provas, http://127.0.0.1:porta)
  NATIVO_ATU_SEM_RODAR=1   baixa mas NÃO roda o instalador (grava os argumentos em NATIVO_ATU_ARGS, se houver)"""
import os, re, subprocess, sys, tempfile, time

VERSAO = "4.0.3.4"
DONO, REPO = "QuitsQuill88885", "sistema-projecao-icm"        # os mesmos DONO_GITHUB e REPO_GITHUB da 3.0.13
ARQ_INSTALADOR = "Instalar-o-Sistema.exe"                      # o mesmo nome que a 3.0.x baixa
ARQ_LINUX = "SistemaNativo-linux.zip"                          # no Linux (o Vaio): só o CÓDIGO, ~1 MB (montar_linux.py)
# os DADOS do Linux vão à parte (08/11 20h, "leveza é lei dele"): o índice pequeno diz o md5 de cada um, e o zip dos dados
# só se baixa quando algum mudou. Nunca saem da pasta numa troca de código.
ARQ_LINUX_DADOS = "SistemaNativo-linux-dados.zip"
ARQ_LINUX_INDICE = "SistemaNativo-linux-dados.json"
PREFIXOS_DADOS = ("dados/", "cifras/", "fontes/", "fontes_linux/", "ferramentas/radeon_uvd/", "fundos/", "cache_cias169/")     # as fontes também: quase nunca mudam. 22/11: o conserto da placa (radeon_uvd) viaja com os dados e a troca de código o APAGAVA (10 arquivos no Vaio, restaurados do tar) 22/11 14h40: e os textos.json das CIAS (cache_cias169/, no pacote de dados desde a 4.0.3): a troca de código tirava os 206


def linux():
    return (os.environ.get("NATIVO_ATU_PLATAFORMA") or ("linux" if sys.platform.startswith("linux") else "windows")) == "linux"


def arquivo_da_release():
    return ARQ_LINUX if linux() else ARQ_INSTALADOR
SEM_JANELA = {"creationflags": 0x08000000} if os.name == "nt" else {}


def raiz():
    return (os.environ.get("NATIVO_GITHUB") or "https://github.com").rstrip("/")


def numero(v):
    """'4.0.10' -> (4, 0, 10): compara número com número (texto poria 4.0.10 antes de 4.0.9)."""
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4]) or (0,)


def _S():
    """O sistema.py da 3.0.13 (o servidor do celular, que viaja no pacote): o contexto TLS e o download que se recupera."""
    import cerebro
    if cerebro.APP not in sys.path:
        sys.path.insert(0, cerebro.APP)
    import sistema
    return sistema


def _ctx():
    try:
        return _S().contexto_ssl()
    except Exception:
        return None


def versao_mais_nova():
    """O versao_mais_nova da 3.0.13: pede /releases/latest SEM seguir o redirecionamento e lê o número no /tag/vX.Y.Z.
    Sem internet devolve None (a igreja muitas vezes não tem internet: isso nunca vira erro na cara do operador)."""
    import urllib.request, urllib.error

    class SemRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    url = "%s/%s/%s/releases/latest" % (raiz(), DONO, REPO)
    manip = [SemRedirect]
    c = _ctx()
    if c is not None:
        manip.append(urllib.request.HTTPSHandler(context=c))
    try:
        urllib.request.build_opener(*manip).open(urllib.request.Request(url, headers={"User-Agent": "Sistema"}), timeout=15)
    except urllib.error.HTTPError as e:
        m = re.search(r"/tag/v?([0-9][0-9.]*)", e.headers.get("Location") or "")
        if m:
            return m.group(1).rstrip(".")
    except Exception:
        return None
    return None


def tamanho_instalador():
    """O tamanho MEDIDO do instalador na release (só o cabeçalho, sem baixar), em bytes; 0 se não deu para saber.
    O Confirmar diz esse número (a 3.0.13 dizia "cerca de 85 MB" fixo)."""
    import urllib.request
    url = "%s/%s/%s/releases/latest/download/%s" % (raiz(), DONO, REPO, arquivo_da_release())
    manip = []
    c = _ctx()
    if c is not None:
        manip.append(urllib.request.HTTPSHandler(context=c))
    try:
        r = urllib.request.build_opener(*manip).open(urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Sistema"}), timeout=15)
        return int(r.headers.get("Content-Length") or 0)
    except Exception:
        return 0


def verificar():
    """{"ok": tem internet, "tem": há versão mais nova, "atual", "nova", "bytes"}: o /api/atualizacao da 3.0.13."""
    v = versao_mais_nova()
    if not v:
        return {"ok": False, "atual": VERSAO}
    tem = numero(v) > numero(VERSAO)
    b = tamanho_instalador() if tem else 0
    if tem and linux():                                # o Confirmar soma os dados só se algum mudou
        ind, falta = dados_pendentes()
        if falta:
            b += int(ind.get("bytes") or 0)
    return {"ok": True, "tem": tem, "atual": VERSAO, "nova": v, "bytes": b}


def conteudo_completo():
    """A linha dourada ("a melhor versão: completa e atualizada") pede o conteúdo inteiro: o conteudo_falta da 3.0.13."""
    if os.environ.get("NATIVO_ATU_CONTEUDO"):          # provas e pares: "completo" | "falta"
        return os.environ["NATIVO_ATU_CONTEUDO"] == "completo"
    try:
        return not _S().conteudo_falta()
    except Exception:
        return False


def baixar(andamento):
    """Baixa o instalador para a pasta FIXA da 3.0.13 (Sistema-baixando: fechar no meio e voltar CONTINUA o download).
    andamento(pct, txt) com as frases dela. Devolve o caminho do instalador."""
    S = _S()
    url = "%s/%s/%s/releases/latest/download/%s" % (raiz(), DONO, REPO, arquivo_da_release())
    guarda = os.environ.get("NATIVO_ATU_PASTA") or S.PASTA_BAIXANDO     # provas: nunca a pasta de verdade da 3.0.13
    os.makedirs(guarda, exist_ok=True)
    alvo = os.path.join(guarda, ARQ_LINUX if linux() else "Instalar o Sistema.exe")
    andamento(3, "Baixando a versão nova…")

    def avisar(feito, total, tentativa, resta=0):
        if tentativa:
            andamento(None, "A internet oscilou. Tento de novo em %ds (tentativa %d)…" % (resta, tentativa))
        elif total:
            andamento(3 + int(90.0 * feito / total), "Baixando a versão nova…")
    S.baixar_se_recuperando(url, alvo, avisar)
    return alvo


def rodar_instalador(alvo):
    """O mesmo contrato da 3.0.x: --silencioso --reabrir. Devolve o processo (ou None no ensaio)."""
    args = [alvo, "--silencioso", "--reabrir"]
    if os.environ.get("NATIVO_ATU_SEM_RODAR") == "1":
        if os.environ.get("NATIVO_ATU_ARGS"):
            with open(os.environ["NATIVO_ATU_ARGS"], "w", encoding="utf-8") as f:
                f.write("\n".join(args))
        return None
    return subprocess.Popen(args, **SEM_JANELA)


# ---- LINUX (o Vaio): o Sistema roda do CÓDIGO (~/Sistema-ICM/nativo) com o venv à parte (~/.sistema-nativo/venv69).
# Atualizar = trocar o código no lugar, com a regra do instalador do Windows: só o que mudou é reescrito (md5), o que era
# do pacote anterior e continua igual sai, e o que não é do pacote (cache_cias, venv, dados, o que ele pôs) NUNCA é
# tocado. Antes de mexer em qualquer arquivo: o zip conferido inteiro e todo .py compilado (um pacote ruim não entra).
MANIFESTO = ".pacote.json"


def _md5(p):
    import hashlib
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pasta_do_programa():
    return os.environ.get("NATIVO_PROG_LINUX") or os.path.dirname(os.path.abspath(__file__))


def instalar_linux(zip_path, andamento=lambda p, t: None):
    """Troca o código no lugar. Devolve {"trocados", "iguais", "tirados", "mantidos", "no pacote"}."""
    import json, py_compile, shutil, zipfile
    prog = pasta_do_programa()
    andamento(94, "Conferindo a versão nova…")
    with zipfile.ZipFile(zip_path) as z:
        ruim = z.testzip()
        if ruim:
            raise RuntimeError("pacote estragado (%s): nada foi trocado" % ruim)
        tmp = tempfile.mkdtemp(prefix="sistema_novo_")
        z.extractall(tmp)
    try:
        agora = {}
        for raiz_, _, fs in os.walk(tmp):
            for f in fs:
                a = os.path.join(raiz_, f)
                r = os.path.relpath(a, tmp).replace(os.sep, "/")
                if r.endswith(".py"):
                    py_compile.compile(a, cfile=os.path.join(tempfile.gettempdir(), "sistema_conf.pyc"), doraise=True)
                agora[r] = _md5(a)
        try:
            antes = json.load(open(os.path.join(prog, MANIFESTO), encoding="utf-8")).get("arquivos") or {}
        except Exception:
            antes = {}
        andamento(96, "Trocando o programa…")
        trocados = iguais = 0
        for r, m in agora.items():
            d = os.path.join(prog, *r.split("/"))
            if os.path.exists(d) and _md5(d) == m:
                iguais += 1
                continue
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copyfile(os.path.join(tmp, *r.split("/")), d + ".novo")
            os.replace(d + ".novo", d)                 # troca atômica: nenhum arquivo fica pela metade
            trocados += 1
        tirados, mantidos = 0, []
        for r, m in antes.items():
            if r in agora or r.startswith(PREFIXOS_DADOS):   # os dados viajam à parte: a troca de código nunca os tira
                continue
            d = os.path.join(prog, *r.split("/"))
            if os.path.exists(d):
                if _md5(d) == m:
                    os.remove(d); tirados += 1
                else:
                    mantidos.append(r)                 # mexido depois de instalado: não é mais só do pacote, fica
        _gravar_manifesto(prog, {"versao": _versao_do(tmp), "quando": time.strftime("%Y-%m-%d %H:%M"), "arquivos": agora})
        return {"trocados": trocados, "iguais": iguais, "tirados": tirados, "mantidos": mantidos, "no pacote": len(agora)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _ler_manifesto(prog):
    import json
    try:
        return json.load(open(os.path.join(prog, MANIFESTO), encoding="utf-8"))
    except Exception:
        return {}


def _gravar_manifesto(prog, novo):
    """Grava o manifesto mantendo a parte dos DADOS (a do código não apaga a dos dados, nem o contrário). Na passagem
    do pacote antigo (dados dentro do código), os dados anotados em "arquivos" passam para "dados"."""
    import json
    m = _ler_manifesto(prog)
    dados = dict(m.get("dados") or {})
    for r, md in (m.get("arquivos") or {}).items():
        if r.startswith(PREFIXOS_DADOS):
            dados.setdefault(r, md)
    m.update(novo)
    m["dados"] = dict(dados, **(novo.get("dados") or {}))
    with open(os.path.join(prog, MANIFESTO) + ".novo", "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    os.replace(os.path.join(prog, MANIFESTO) + ".novo", os.path.join(prog, MANIFESTO))


def _ler_url(arq, timeout=15):
    import urllib.request
    url = "%s/%s/%s/releases/latest/download/%s" % (raiz(), DONO, REPO, arq)
    manip = []
    c = _ctx()
    if c is not None:
        manip.append(urllib.request.HTTPSHandler(context=c))
    return urllib.request.build_opener(*manip).open(urllib.request.Request(url, headers={"User-Agent": "Sistema"}),
                                                     timeout=timeout).read()


def dados_pendentes():
    """(índice da release, [os dados cujo md5 difere do que está na pasta]). Sem índice (sem internet, ou release antiga
    sem os dados à parte): ({}, []) e nada se baixa."""
    import json
    try:
        ind = json.loads(_ler_url(ARQ_LINUX_INDICE).decode("utf-8"))
    except Exception:
        return {}, []
    prog = pasta_do_programa()
    falta = []
    for r, md in (ind.get("arquivos") or {}).items():
        if not r.startswith(PREFIXOS_DADOS) or ".." in r.split("/"):
            continue
        d = os.path.join(prog, *r.split("/"))
        if not os.path.exists(d) or _md5(d) != md:
            falta.append(r)
    return ind, falta


def instalar_dados_linux(zip_path, indice, andamento=lambda p, t: None):
    """Troca só os dados que mudaram. Cada um tem de bater com o md5 do índice, senão NADA é trocado."""
    import shutil, zipfile
    prog = pasta_do_programa()
    esperado = {r: md for r, md in (indice.get("arquivos") or {}).items() if r.startswith(PREFIXOS_DADOS) and ".." not in r.split("/")}
    andamento(97, "Conferindo os louvores e as cifras novas…")
    tmp = tempfile.mkdtemp(prefix="sistema_dados_")
    try:
        with zipfile.ZipFile(zip_path) as z:
            if z.testzip():
                raise RuntimeError("dados estragados: nada foi trocado")
            for r in esperado:
                z.extract(r, tmp)
        for r, md in esperado.items():
            if _md5(os.path.join(tmp, *r.split("/"))) != md:
                raise RuntimeError("dados não conferem (%s): nada foi trocado" % r)
        trocados = iguais = 0
        for r, md in esperado.items():
            d = os.path.join(prog, *r.split("/"))
            if os.path.exists(d) and _md5(d) == md:
                iguais += 1
                continue
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copyfile(os.path.join(tmp, *r.split("/")), d + ".novo")
            os.replace(d + ".novo", d)
            trocados += 1
        _gravar_manifesto(prog, {"dados": esperado})
        return {"dados trocados": trocados, "dados iguais": iguais}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def atualizar_dados_linux(andamento=lambda p, t: None):
    """Depois da troca do código: baixa os dados SÓ se algum md5 mudou. {"dados": "iguais"} quando não precisa."""
    ind, falta = dados_pendentes()
    if not falta:
        return {"dados": "iguais" if ind else "sem índice"}
    S = _S()
    url = "%s/%s/%s/releases/latest/download/%s" % (raiz(), DONO, REPO, ARQ_LINUX_DADOS)
    guarda = os.environ.get("NATIVO_ATU_PASTA") or S.PASTA_BAIXANDO
    os.makedirs(guarda, exist_ok=True)
    alvo = os.path.join(guarda, ARQ_LINUX_DADOS)
    andamento(95, "Baixando os louvores e as cifras novas…")
    S.baixar_se_recuperando(url, alvo, lambda feito, total, tentativa, resta=0: None)
    r = instalar_dados_linux(alvo, ind, andamento)
    r["pendentes"] = len(falta)
    return r


def _versao_do(pasta):
    try:
        m = re.search(r'^VERSAO = "([^"]+)"', open(os.path.join(pasta, "atualizador.py"), encoding="utf-8").read(), re.M)
        return m.group(1) if m else "?"
    except Exception:
        return "?"


def reabrir_linux():
    """Abre o Sistema de novo 3 s depois (este processo fecha antes): pelo lançador dele, como o ícone faz."""
    if os.environ.get("NATIVO_ATU_SEM_RODAR") == "1":
        return None
    lanc = os.environ.get("NATIVO_LANCADOR") or os.path.expanduser("~/sistema-nativo.sh")
    # o lançador não abre outro se o Sistema ainda estiver de pé: espera ESTE processo terminar (até 15 s) antes de abrir.
    # (08/11: era pelo título "Sistema Nativo · painel", que o painel não tem mais: agora pelo pid, exato)
    espera = ('sleep 1; for i in $(seq 1 30); do kill -0 %d 2>/dev/null || break; sleep 0.5; done; ' % os.getpid())
    cmd = espera + ('exec "%s"' % lanc if os.path.exists(lanc) else
                    'cd "%s" && exec "%s" sistema_nativo.py' % (pasta_do_programa(), sys.executable))
    return subprocess.Popen(["sh", "-c", cmd], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
