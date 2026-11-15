# -*- coding: utf-8 -*-
"""O pacote do Sistema 4.0 para o LINUX (o Vaio), 08/11/2026: só o CÓDIGO (os .py, o qml, as fontes e o linux/), sem o
venv (o Qt 6.9.3 do Vaio fica onde está), sem os vídeos das CIAS e sem as ferramentas de teste. É o que o Atualizar do
4.0 no Linux baixa da release (SistemaNativo-linux.zip) e troca no lugar, com a mesma regra do Windows (md5).
08/11 20h (HD, "leveza é lei dele"): os DADOS (dados/ e cifras/, 1,5 MB no zip) vão À PARTE, em SistemaNativo-linux-dados.zip
com um índice pequeno (SistemaNativo-linux-dados.json: o md5 de cada um). O Atualizar só baixa os dados quando algum md5
mudou; o código fica abaixo de 1 MB.
uso: python empacotar/montar_linux.py [pasta]     (padrão: empacotar/instalador/; grava os três arquivos)"""
import hashlib, json, os, sys, time, zipfile

NAT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_PY = ["cerebro.py", "sistema_nativo.py", "rede.py", "sugestoes.py", "atualizador.py", "telas_linux.py",
           "seguir.py", "textura_bc.py"]      # 14/11: o seguir (a tela secundária, de 13/11) faltava no pacote e o Sistema instalado no Vaio NÃO ABRIA (import seguir no main)
PASTAS = ["qml", "linux"]
# as FONTES quase nunca mudam (0,56 MB no zip): viajam com os dados, só quando o md5 muda. O código fica em ~0,5 MB.
PASTAS_DADOS = ["fontes", "fontes_linux",
                # 12/11: o conserto do driver da placa (radeon, o verdão e o congelamento) vai com o pacote, para o
                # linux/instalar.sh pôr em qualquer máquina com placa AMD antiga. 1,2 MB: viaja com os dados (só quando muda)
                "ferramentas/radeon_uvd"]
FORA = ("__pycache__",)
# 08/11 (teste dele no Vaio: "cadê a conferência absoluta"): os DADOS que mudaram depois da 3.0.12 (a letra conferida
# de 03/11, os selos do livro e as cifras escondidas) vão no pacote, tirados da 3.0.13 na hora de montar (nenhuma cópia
# parada no git para envelhecer). No Vaio ficam em <programa>/dados e o cerebro.dado() os prefere. 2,4 MB.
APP_313 = os.environ.get("SISTEMA_APP", r"C:\Projetos\Sistema\App\ICM Ipero Projecao")
DADOS = ["louvores.js", "repeticoes.js", "cifras_ocultas.json",
         "gestos.js"]         # 14/11: os gestos por louvor (gestos_dos_louvores.py); as figuras seguem na pasta da 3.0.12
# e o controle.html do celular da 3.0.13 (os consertos do culto de 08/11): no Vaio o servidor é o da pasta da 3.0.12, que
# não se mexe; o rede.py serve este no lugar daquele.
WEB = ["controle.html"]
# e o banco de CIFRAS conferido (03/11): a cópia do usuário só se renova instalando a 3.0.x (no Vaio era a de 10/10, sem as
# correções). cerebro.ARQ_ACORDES e o rede.py preferem este. 4,3 MB (1,1 MB no zip).
CIFRA = "cifras/acordes.json"


def fonte(r):
    """O arquivo de origem de um item do pacote (o código daqui; os dados, da 3.0.13)."""
    if r.startswith("dados/"):
        return os.path.join(APP_313, "dados", r[6:])
    if r.startswith("web/"):
        return os.path.join(APP_313, r[4:])
    if r == CIFRA:
        return os.path.join(APP_313, "conteudo_leve", "cifras", "acordes.json")
    return os.path.join(NAT, *r.split("/"))


ARQ_DADOS = "SistemaNativo-linux-dados.zip"
ARQ_INDICE = "SistemaNativo-linux-dados.json"


def arquivos_dados():
    """Os DADOS do pacote (vão à parte): a letra conferida, os selos, as cifras escondidas e o banco de cifras."""
    out = ["dados/" + d for d in DADOS if os.path.exists(os.path.join(APP_313, "dados", d))]
    if os.path.exists(fonte(CIFRA)):
        out.append(CIFRA)
    return out + _das_pastas(PASTAS_DADOS)


def _das_pastas(pastas):
    out = []
    for d in pastas:
        for raiz, subs, fs in os.walk(os.path.join(NAT, d)):
            subs[:] = [s for s in subs if s not in FORA]
            for f in fs:
                if not f.endswith((".pyc", ".bak")):
                    out.append(os.path.relpath(os.path.join(raiz, f), NAT).replace(os.sep, "/"))
    return out


def arquivos(dados=False):
    """O CÓDIGO do pacote; com dados=True, código + dados (o que fica instalado no Vaio, para as provas)."""
    out = [p for p in RAIZ_PY if os.path.exists(os.path.join(NAT, p))]
    out += ["web/" + w for w in WEB if os.path.exists(os.path.join(APP_313, w))]
    if dados:
        out += arquivos_dados()
    return sorted(out + _das_pastas(PASTAS))


def _zipar(saida, lista):
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for r in lista:
            z.write(fonte(r), r)
    return lista


def modulos_que_faltam():
    """14/11/2026 (o Sistema instalado no Vaio não abriu: 'No module named seguir'): todo módulo DA CASA (um .py ao lado
    do sistema_nativo.py) que o código do pacote importa tem de estar na lista RAIZ_PY. Devolve os que faltam."""
    import re
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    da_casa = {f[:-3] for f in os.listdir(raiz) if f.endswith(".py")}
    faltam = set()
    for f in RAIZ_PY:
        txt = open(os.path.join(raiz, f), encoding="utf-8").read()
        for m in re.finditer(r"^[ \t]*(?:import|from)[ \t]+([A-Za-z_][A-Za-z0-9_, \t]*)", txt, re.M):
            for nome in re.split(r"[ ,\t]+", m.group(1)):
                if nome in da_casa and nome + ".py" not in RAIZ_PY:
                    faltam.add(nome + ".py")
    return sorted(faltam)


def montar(saida, dados=False):
    """O zip do CÓDIGO (o SistemaNativo-linux.zip da release); dados=True: código + dados num zip só (provas)."""
    falta = modulos_que_faltam()
    if falta:
        raise SystemExit("PACOTE LINUX NÃO MONTADO: o código importa %s e ele(s) não está(ão) em RAIZ_PY" % ", ".join(falta))
    return _zipar(saida, arquivos(dados))


def montar_dados(pasta):
    """O zip dos DADOS + o índice (md5 de cada um e o tamanho do zip), na pasta. Devolve o índice."""
    lista = arquivos_dados()
    z = os.path.join(pasta, ARQ_DADOS)
    _zipar(z, lista)
    ind = {"arquivos": {r: hashlib.md5(open(fonte(r), "rb").read()).hexdigest() for r in lista},
           "bytes": os.path.getsize(z), "quando": time.strftime("%Y-%m-%d %H:%M")}
    with open(os.path.join(pasta, ARQ_INDICE), "w", encoding="utf-8", newline="\n") as f:
        json.dump(ind, f, ensure_ascii=False, indent=1)
    return ind


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(NAT, "empacotar", "instalador")
    t0 = time.time(); s = os.path.join(pasta, "SistemaNativo-linux.zip"); l = montar(s)
    print("código: %d arquivos · %.2f MB -> %s" % (len(l), os.path.getsize(s) / 2**20, s))
    ind = montar_dados(pasta)
    print("dados: %d arquivos · %.2f MB -> %s (+ %s) · %.1f s" % (len(ind["arquivos"]), ind["bytes"] / 2**20, ARQ_DADOS, ARQ_INDICE,
                                                                  time.time() - t0))
