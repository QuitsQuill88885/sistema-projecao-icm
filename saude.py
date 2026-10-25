# 3.0.12 — O VIGIA DE SAÚDE (ordem dele, 25/10, depois do crash na igreja: "o sistema ICM monitorar também o
# processamento do computador é ótimo (...) ele vai ter noção do que ele está fazendo").
# A cada 10 s mede, SÓ COM O QUE O WINDOWS JÁ TEM (ctypes, nenhuma biblioteca nova, nada pesado):
#   - a memória do computador: a física livre e a "virtual" que ainda cabe (o que acabou na igreja: evento 2004);
#   - quanto o PRÓPRIO Sistema gasta: o Sistema.exe e os msedgewebview2 que são dele (a árvore de processos);
#   - o processador (% de uso do computador) e a bateria (na tomada? quanto?).
# Grava uma linha por minuto em saude.log (ao lado dos dados do operador, até 512 KB, depois guarda 1 antigo):
# na próxima vez que algo cair, o registro diz o que cresceu e quando. O painel pergunta em /api/saude.
import ctypes, os, threading, time
from ctypes import wintypes

NIVEIS = ("ok", "atencao", "perigo")
ESTADO = {"nivel": "ok", "motivo": "", "em": 0}


class _MEM(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


class _BAT(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte), ("BatteryLifePercent", ctypes.c_ubyte),
                ("SystemStatusFlag", ctypes.c_ubyte), ("BatteryLifeTime", wintypes.DWORD), ("BatteryFullLifeTime", wintypes.DWORD)]


class _PME(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t), ("PrivateUsage", ctypes.c_size_t)]


class _PE32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                ("szExeFile", ctypes.c_wchar * 260)]


def _memoria():
    m = _MEM(); m.dwLength = ctypes.sizeof(m)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    mb = lambda v: int(v // 1048576)
    return {"ram_total": mb(m.ullTotalPhys), "ram_livre": mb(m.ullAvailPhys),
            "virtual_total": mb(m.ullTotalPageFile), "virtual_livre": mb(m.ullAvailPageFile)}


def _bateria():
    b = _BAT()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(b)) or b.BatteryFlag == 128:
        return {"tomada": True, "bateria": None}               # 128 = não tem bateria (PC de mesa)
    return {"tomada": b.ACLineStatus == 1, "bateria": None if b.BatteryLifePercent == 255 else int(b.BatteryLifePercent)}


_cpu_ant = None
def _cpu():
    global _cpu_ant
    ft = [wintypes.FILETIME() for _ in range(3)]
    ctypes.windll.kernel32.GetSystemTimes(*[ctypes.byref(f) for f in ft])
    v = [(f.dwHighDateTime << 32) | f.dwLowDateTime for f in ft]     # ocioso, núcleo (inclui ocioso), usuário
    ant, _cpu_ant = _cpu_ant, v
    if not ant: return None
    oc, tot = v[0] - ant[0], (v[1] - ant[1]) + (v[2] - ant[2])
    return round(100 * (1 - oc / tot)) if tot > 0 else None


def _arvore():
    """{pid: (nome, privado em MB)} do Sistema e de todos os processos filhos dele (os msedgewebview2)."""
    k = ctypes.windll.kernel32
    snap = k.CreateToolhelp32Snapshot(0x2, 0)
    if snap in (0, -1, ctypes.c_void_p(-1).value): return {}
    filhos, nomes = {}, {}
    try:
        e = _PE32(); e.dwSize = ctypes.sizeof(e)
        ok = k.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            filhos.setdefault(e.th32ParentProcessID, []).append(e.th32ProcessID); nomes[e.th32ProcessID] = e.szExeFile
            ok = k.Process32NextW(snap, ctypes.byref(e))
    finally:
        k.CloseHandle(snap)
    fila, meus = [os.getpid()], []
    while fila:
        p = fila.pop()
        if p in meus: continue
        meus.append(p); fila += filhos.get(p, [])
    psapi, saida = ctypes.windll.psapi, {}
    for p in meus:
        h = k.OpenProcess(0x1000, False, p)                    # PROCESS_QUERY_LIMITED_INFORMATION
        if not h: continue
        try:
            c = _PME(); c.cb = ctypes.sizeof(c)
            if psapi.GetProcessMemoryInfo(h, ctypes.byref(c), c.cb):
                saida[p] = (nomes.get(p, "?"), int(c.PrivateUsage // 1048576))
        finally:
            k.CloseHandle(h)
    return saida


def medir():
    d = _memoria(); d.update(_bateria()); d["cpu"] = _cpu()
    arv = _arvore()
    d["sistema_mb"] = sum(v[1] for v in arv.values())
    d["maior"] = max(arv.values(), key=lambda v: v[1]) if arv else None
    d["processos"] = len(arv)
    # o nível: a memória VIRTUAL é a que acabou na igreja (4 GB de RAM + 2,5 GB de paginação)
    # limite em MB, não em %: no Alpha (35 GB de virtual) 16% livres ainda são 5,9 GB e não é perigo nenhum
    vl = d["virtual_livre"]
    nivel, motivo = "ok", ""
    if vl < 500:
        nivel, motivo = "perigo", "memória quase no fim (%d MB livres)" % vl
    elif vl < 1000 or d["ram_livre"] < 250:
        nivel, motivo = "atencao", "memória baixa (%d MB livres)" % vl
    if d["bateria"] is not None and not d["tomada"] and d["bateria"] <= 15:
        nivel, motivo = "perigo", "bateria em %d%%, ligue na tomada" % d["bateria"]
    elif d["bateria"] is not None and not d["tomada"] and d["bateria"] <= 30 and nivel == "ok":
        nivel, motivo = "atencao", "bateria em %d%%" % d["bateria"]
    d["nivel"], d["motivo"], d["em"] = nivel, motivo, int(time.time())
    return d


def _grava(pasta, d):
    try:
        f = os.path.join(pasta, "saude.log")
        if os.path.exists(f) and os.path.getsize(f) > 512 * 1024:
            os.replace(f, f + ".1")
        maior = "%s %d MB" % d["maior"] if d.get("maior") else "-"
        with open(f, "a", encoding="utf-8") as a:
            a.write("%s | %s | Sistema %d MB em %d processos (maior: %s) | RAM livre %d/%d MB | virtual livre %d/%d MB | CPU %s%% | %s%s\n" % (
                time.strftime("%Y-%m-%d %H:%M:%S"), d["nivel"], d["sistema_mb"], d["processos"], maior, d["ram_livre"], d["ram_total"],
                d["virtual_livre"], d["virtual_total"], d["cpu"] if d["cpu"] is not None else "-",
                "tomada" if d["tomada"] else "bateria %s%%" % d["bateria"], (" | " + d["motivo"]) if d["motivo"] else ""))
    except Exception:
        pass


def ligar(pasta, seg=10):
    """Liga o vigia (uma vez). Grava no saude.log a 1ª medição, uma por minuto, e toda mudança de nível na hora."""
    if os.name != "nt" or getattr(ligar, "ligado", False): return
    ligar.ligado = True
    def roda():
        ultimo_log, nivel_ant = 0, None
        while True:
            try:
                d = medir(); ESTADO.clear(); ESTADO.update(d)
                if time.time() - ultimo_log >= 60 or d["nivel"] != nivel_ant:
                    _grava(pasta, d); ultimo_log, nivel_ant = time.time(), d["nivel"]
            except Exception:
                pass
            time.sleep(seg)
    threading.Thread(target=roda, name="vigia-saude", daemon=True).start()
