# -*- coding: utf-8 -*-
r"""O INSTALADOR do Sistema Nativo no Windows (07/11/2026, decisão da HD pela ordem dele). Faz o que o da 3.0.13 faz
(copiar o programa para %LOCALAPPDATA%\Programs, os atalhos na Área de Trabalho e no menu Iniciar) e o que ela NÃO fazia:
a REGRA DE ENTRADA DO FIREWALL para o .exe instalado (TCP e UDP, perfis Privado e Público). Sem ela o celular de fora
era barrado, ou a janela do Firewall caía no culto (o liberar_no_firewall da 3.0.13 existe e nunca é chamado).
Tudo o que ele cria fica anotado no instalacao.json do programa: o Desinstalar desfaz exatamente isso.

Desvios para as PROVAS (pasta temporária, nada no Windows de verdade):
  NATIVO_PROG          a pasta do programa
  NATIVO_ATALHO_DESK   a pasta da Área de Trabalho     NATIVO_ATALHO_MENU  a do menu Iniciar
  NATIVO_NETSH_ENSAIO  arquivo: os comandos do Firewall são GRAVADOS ali, não executados
uso: python empacotar/instalador_nativo.py [pasta do pacote]   (padrão: empacotar/dist15/SistemaNativo)"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, time

NOME = "Sistema Nativo"
EXE = "SistemaNativo.exe"
REGRAS = [(NOME + " (TCP)", "TCP"), (NOME + " (UDP)", "UDP")]
SEM_JANELA = {"creationflags": 0x08000000} if os.name == "nt" else {}
# o CONTEÚDO que só o instalador completo traz (12/11): a atualização leve não apaga (ver limpar_sobras)
CONTEUDO = ("_internal/leve/", "_internal/cias169/", "_internal/animacoes/", "_internal/video/")


def pasta_programa():
    return os.environ.get("NATIVO_PROG") or os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Programs", NOME)


def _pasta_especial(nome_ps, env, padrao):
    if os.environ.get(env):
        return os.environ[env]
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('%s')" % nome_ps],
                           capture_output=True, text=True, timeout=20, **SEM_JANELA)
        p = r.stdout.strip()
        if p: return p
    except Exception:
        pass
    return padrao


def pasta_desktop():
    return _pasta_especial("Desktop", "NATIVO_ATALHO_DESK", os.path.join(os.path.expanduser("~"), "Desktop"))


def pasta_menu():
    return _pasta_especial("Programs", "NATIVO_ATALHO_MENU",
                           os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"))


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def copiar(origem, destino):
    """Copia o pacote por cima (o que já está igual não é reescrito), conferindo o md5 de cada arquivo copiado."""
    n = iguais = 0
    for r, _, fs in os.walk(origem):
        for f in fs:
            a = os.path.join(r, f); b = os.path.join(destino, os.path.relpath(a, origem))
            os.makedirs(os.path.dirname(b), exist_ok=True)
            if os.path.exists(b) and os.path.getsize(a) == os.path.getsize(b) and md5(a) == md5(b):
                iguais += 1; continue
            shutil.copy2(a, b)
            if md5(a) != md5(b):
                raise RuntimeError("a cópia de %s não conferiu (md5)" % a)
            n += 1
    return n, iguais


def lista_do_pacote(pasta):
    """{caminho relativo: md5} de todos os arquivos do pacote (o instalacao.json nunca entra)."""
    out = {}
    for r, _, fs in os.walk(pasta):
        for f in fs:
            a = os.path.join(r, f); rel = os.path.relpath(a, pasta).replace(os.sep, "/")
            if rel != "instalacao.json":
                out[rel] = md5(a)
    return out


def limpar_sobras(dest, antes, agora):
    """O que era do pacote ANTERIOR e não está no novo sai, mas só se o arquivo ainda for o MESMO (md5 igual ao anotado):
    arquivo mexido, arquivo que não era do pacote e os dados do operador (que nem moram aqui) ficam. Pastas que
    ficaram vazias saem. Sem isto a atualização no clique ia engordando (medido 08/11: 431 MB instalados x 405 do pacote)."""
    tirados, mantidos = [], []
    # 12/11/2026: o CONTEÚDO do instalador completo (as apresentações das crianças, ~960 MB) só sai se o pacote novo
    # também traz aquela pasta. A atualização leve (sem conteúdo) nunca apaga o que o completo instalou.
    conteudo = [c for c in CONTEUDO if not any(r.startswith(c) for r in agora)]
    for rel, m in sorted(antes.items()):
        if rel in agora or rel == "instalacao.json" or any(rel.startswith(c) for c in conteudo):
            continue
        p = os.path.join(dest, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            continue
        if md5(p) == m:
            os.remove(p); tirados.append(rel)
        else:
            mantidos.append(rel)
    for r, ds, fs in sorted(os.walk(dest), key=lambda x: -len(x[0])):   # de baixo para cima
        if r != dest and not os.listdir(r):
            os.rmdir(r)
    return tirados, mantidos


def atalho(lnk, alvo, pasta_trabalho):
    """O .lnk pelo WScript.Shell do PowerShell (sem pywin32)."""
    os.makedirs(os.path.dirname(lnk), exist_ok=True)
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');$s.TargetPath='%s';$s.WorkingDirectory='%s';"
          "$s.IconLocation='%s,0';$s.Save()") % (lnk.replace("'", "''"), alvo.replace("'", "''"), pasta_trabalho.replace("'", "''"), alvo.replace("'", "''"))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=30, **SEM_JANELA)
    return os.path.exists(lnk)


def comandos_firewall(exe, tirar=False):
    """As linhas do netsh: tira as regras com o mesmo nome (o caminho pode ter mudado) e põe de novo."""
    c = []
    for nome, proto in REGRAS:
        c.append('netsh advfirewall firewall delete rule name="%s"' % nome)
        if not tirar:
            c.append('netsh advfirewall firewall add rule name="%s" dir=in action=allow program="%s" protocol=%s '
                     'profile=private,public enable=yes' % (nome, exe, proto))
    return c


def admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def rodar_firewall(linhas):
    """Executa as linhas do netsh. ENSAIO: grava no arquivo. Sem administrador: UM roteiro elevado (uma janela do Windows
    pedindo permissão, não uma por regra)."""
    ensaio = os.environ.get("NATIVO_NETSH_ENSAIO")
    if ensaio:
        with open(ensaio, "a", encoding="utf-8") as f:
            f.write("\n".join(linhas) + "\n")
        return "ensaio"
    if admin():
        for l in linhas:
            subprocess.run(l, shell=True, capture_output=True, timeout=30, **SEM_JANELA)
        return "feito"
    cmd = os.path.join(tempfile.mkdtemp(prefix="nativo_fw_"), "firewall.cmd")
    with open(cmd, "w", encoding="utf-8") as f:
        f.write("@echo off\n" + "\n".join(l + " >nul" for l in linhas) + "\n")
    ps = "Start-Process -FilePath cmd.exe -ArgumentList '/c \"%s\"' -Verb RunAs -WindowStyle Hidden -Wait" % cmd
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=300, **SEM_JANELA)
    return "feito" if r.returncode == 0 else "recusado"


def instalar(origem):
    dest = pasta_programa()
    os.makedirs(dest, exist_ok=True)
    # a lista do pacote ANTERIOR: a do instalacao.json; numa instalação antiga sem lista, a de um pacote de referência
    # (NATIVO_PACOTE_ANTERIOR: a pasta do pacote que foi instalado antes, conferido por md5)
    antes = {}
    try:
        antes = json.load(open(os.path.join(dest, "instalacao.json"), encoding="utf-8")).get("arquivos") or {}
    except Exception:
        pass
    if not antes and os.environ.get("NATIVO_PACOTE_ANTERIOR"):
        antes = lista_do_pacote(os.environ["NATIVO_PACOTE_ANTERIOR"])
    agora = lista_do_pacote(origem)
    n, iguais = copiar(origem, dest)
    tirados, mantidos = limpar_sobras(dest, antes, agora)
    exe = os.path.join(dest, EXE)
    atalhos = []
    for pasta in (pasta_desktop(), pasta_menu()):
        lnk = os.path.join(pasta, NOME + ".lnk")
        if atalho(lnk, exe, dest): atalhos.append(lnk)
    fw = rodar_firewall(comandos_firewall(exe))
    reg = {"programa": dest, "exe": exe, "atalhos": atalhos, "regras": [r[0] for r in REGRAS], "firewall": fw,
           "quando": time.strftime("%Y-%m-%d %H:%M"), "arquivos": agora}
    with open(os.path.join(dest, "instalacao.json"), "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)
    out = {k: v for k, v in reg.items() if k != "arquivos"}
    return {"copiados": n, "iguais": iguais, "tirados": len(tirados), "mantidos (mexidos)": mantidos, "no pacote": len(agora), **out}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    aqui = os.path.dirname(os.path.abspath(__file__))
    org = sys.argv[1] if len(sys.argv) > 1 else os.path.join(aqui, "dist15", "SistemaNativo")
    print(json.dumps(instalar(org), ensure_ascii=False, indent=1))
