# -*- coding: utf-8 -*-
"""ENCOLHER O VENV DO VAIO (08/11/2026; palavra dele: "mais leve, senão não adianta"). O ~/.sistema-nativo/venv69 tem
698 MB, 673 do PySide6, e quase tudo é do que o Sistema não usa: o navegador do Qt (WebEngineCore 190 MB), as traduções
(54 MB), o Designer, o 3D, o Wayland e três cópias de cada biblioteca do ffmpeg.

MEDIDO, não suposto: o que FICA é o que o Sistema de verdade carregou numa volta completa (o /proc/<pid>/maps e o
QML_IMPORT_TRACE, gravados por `medir`) MAIS tudo de que essas bibliotecas precisam (o NEEDED de cada .so, lido do
próprio arquivo ELF). O resto é MOVIDO (nunca apagado) para ~/.sistema-nativo/venv69-tirados, com o mesmo caminho, e
`desfazer` devolve tudo. Depois de encolher: abrir o Sistema e rodar as provas; falhou, desfaz.

uso no Vaio (frio, nice):
  python3 encolher_venv.py medir    <arquivo de medida: maps + trace>   (o Sistema já aberto: lê o /proc dele)
  python3 encolher_venv.py ensaio   <medida>   -> diz o que sairia e quantos MB, sem mexer em nada
  python3 encolher_venv.py encolher <medida>   -> move
  python3 encolher_venv.py desfazer            -> devolve tudo"""
import json, os, re, shutil, struct, subprocess, sys

VENV = os.path.expanduser("~/.sistema-nativo/venv69")
TIRADOS = os.path.expanduser("~/.sistema-nativo/venv69-tirados")


def site():
    for raiz, subs, _ in os.walk(os.path.join(VENV, "lib")):
        if os.path.basename(raiz) == "site-packages":
            return raiz
    raise SystemExit("site-packages não achado em " + VENV)


def needed(caminho):
    """Os NEEDED (bibliotecas de que o .so precisa) lidos do ELF de 64 bits, sem readelf."""
    try:
        with open(caminho, "rb") as f:
            d = f.read()
    except OSError:
        return []
    if d[:4] != b"\x7fELF" or d[4] != 2:
        return []
    e_shoff, = struct.unpack_from("<Q", d, 0x28)
    e_shentsize, e_shnum = struct.unpack_from("<HH", d, 0x3A)
    secs = [struct.unpack_from("<IIQQQQIIQQ", d, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    dyn = next((s for s in secs if s[1] == 6), None)            # SHT_DYNAMIC
    if not dyn:
        return []
    strtab = secs[dyn[6]]                                         # sh_link -> a tabela de nomes
    out = []
    for k in range(0, dyn[5], 16):
        tag, val = struct.unpack_from("<qQ", d, dyn[4] + k)
        if tag == 0:
            break
        if tag == 1:                                              # DT_NEEDED
            o = strtab[4] + val
            out.append(d[o:d.index(b"\0", o)].decode())
    return out


def medir(saida):
    """Lê o /proc/<pid>/maps do Sistema aberto (as .so carregadas do venv) e junta ao QML_IMPORT_TRACE do log."""
    pids = [p for p in os.listdir("/proc") if p.isdigit()]
    usados = set()
    for p in pids:
        try:
            cmd = open("/proc/%s/cmdline" % p, "rb").read().decode(errors="ignore")
        except OSError:
            continue
        if "sistema_nativo.py" not in cmd:
            continue
        for l in open("/proc/%s/maps" % p):
            m = re.search(r"(/\S+\.so[\.\d]*)$", l.strip())
            if m and m.group(1).startswith(VENV):
                usados.add(os.path.realpath(m.group(1)))
    qml = set()
    # o log com o QML_IMPORT_TRACE: o do lançador, ou o da rodada de medida (ENCOLHER_LOG, ex. /tmp/medir_no_vaio.log)
    log = os.environ.get("ENCOLHER_LOG") or os.path.expanduser("~/.sistema-nativo/nativo.log")
    if os.path.exists(log):
        for l in open(log, errors="ignore"):
            # Qt 6.9 (o do Vaio) escreve o caminho do qmldir de cada módulo; as versões antigas, importPlugin/Module path
            for m in re.finditer(r'importPlugin.*?"(/[^"]+\.so)"|Module path: "(/[^"]+)"|"(/[^"]+)/qmldir"', l):
                qml.add(m.group(1) or m.group(2) or m.group(3))
    json.dump({"so": sorted(usados), "qml": sorted(qml)}, open(saida, "w"), indent=1)
    print("medida:", len(usados), "bibliotecas carregadas,", len(qml), "módulos QML ->", saida)


def plano(medida):
    sp = site()
    m = json.load(open(medida))
    fica = set()
    todos = {}                                                    # nome do arquivo -> caminhos (para o NEEDED)
    for raiz, _, fs in os.walk(sp):
        for f in fs:
            todos.setdefault(f, []).append(os.path.join(raiz, f))
    fila = [p for p in m["so"] if os.path.exists(p)]
    for d in m["qml"]:                                            # o módulo QML inteiro que foi importado fica
        base = d if os.path.isdir(d) else os.path.dirname(d)
        if base.startswith(VENV) and os.path.isdir(base):
            for raiz, _, fs in os.walk(base):
                for f in fs:
                    fila.append(os.path.join(raiz, f))
    while fila:
        p = os.path.realpath(fila.pop())
        if p in fica:
            continue
        fica.add(p)
        for n in needed(p):
            fila.extend(todos.get(n, []))
    sai = []
    for raiz, _, fs in os.walk(os.path.join(sp, "PySide6", "Qt")):
        for f in fs:
            p = os.path.join(raiz, f)
            if os.path.realpath(p) in fica:
                continue
            grande = f.endswith((".so", ".qm")) or re.search(r"\.so\.\d", f) or "/qml/" in p or "/translations/" in p
            if grande and not re.match(r"q(t|tbase)_pt", f):           # as traduções em português ficam
                sai.append(p)
    return sai


def mb(ps):
    return sum(os.path.getsize(p) for p in ps if os.path.exists(p)) / 2**20


if __name__ == "__main__":
    o = sys.argv[1] if len(sys.argv) > 1 else ""
    if o == "medir":
        medir(sys.argv[2])
    elif o in ("ensaio", "encolher"):
        s = plano(sys.argv[2])
        print("sairiam %d arquivos, %.0f MB (de %.0f MB do venv)" % (len(s), mb(s), mb([os.path.join(r, f) for r, _, fs in os.walk(VENV) for f in fs])))
        if o == "encolher":
            for p in s:
                d = os.path.join(TIRADOS, os.path.relpath(p, VENV))
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.move(p, d)
            json.dump([os.path.relpath(p, VENV) for p in s], open(os.path.join(TIRADOS, "lista.json"), "w"), indent=0)
            print("movidos para", TIRADOS, "(desfazer: python3 encolher_venv.py desfazer)")
    elif o == "desfazer":
        lista = json.load(open(os.path.join(TIRADOS, "lista.json")))
        for r in lista:
            if os.path.exists(os.path.join(TIRADOS, r)):
                os.makedirs(os.path.dirname(os.path.join(VENV, r)), exist_ok=True)
                shutil.move(os.path.join(TIRADOS, r), os.path.join(VENV, r))
        print("devolvidos", len(lista), "arquivos")
    else:
        print(__doc__)
