# -*- coding: utf-8 -*-
# O Instalar-o-Sistema.exe do Sistema 4.0 (08/11/2026): zipa o pacote (empacotar/<dist>/SistemaNativo) e monta o .exe
# (PyInstaller --onefile, sem console) com o instalar_o_sistema.py e o zip dentro. Sai em empacotar/instalador/dist.
# uso: python empacotar/montar_instalador.py [dist19]   (pelo python do App, que tem o PyInstaller do venv_qt)
import os, subprocess, sys, time, zipfile
EMP = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(EMP, "instalador")
os.makedirs(S, exist_ok=True)
args = [a for a in sys.argv[1:] if not a.startswith("--")]
COMPLETO = "--completo" in sys.argv          # 12/11/2026: o instalador COMPLETO (tudo dentro: as apresentações das crianças)
pac = os.path.join(EMP, args[0] if args else "dist19", "SistemaNativo")
zp = os.path.join(S, "SistemaNativo-completo.zip" if COMPLETO else "SistemaNativo.zip")
# a MÍDIA vai sem compressão (MP4/JPG já são comprimidos: ganharia 1-3% e a máquina fraca gastaria processador para
# abrir; regra dele 12/11: instalar em até 5 min). O programa (Qt, código) vai comprimido.
JA_COMPRIMIDO = (".mp4", ".jpg", ".jpeg", ".png", ".webp", ".zip", ".zst")
def poe(z, origem, nome):
    z.write(origem, nome, compress_type=zipfile.ZIP_STORED if origem.lower().endswith(JA_COMPRIMIDO) else zipfile.ZIP_DEFLATED)
t0 = time.time()
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for raiz, _, arqs in os.walk(pac):
        for a in arqs:
            p = os.path.join(raiz, a)
            poe(z, p, os.path.join("SistemaNativo", os.path.relpath(p, pac)))
    if COMPLETO:
        import conteudo_completo
        for origem, destino in conteudo_completo.itens():
            poe(z, origem, "SistemaNativo/_internal/" + destino)
print("zip %.1f MB em %.0f s" % (os.path.getsize(zp) / 2**20, time.time() - t0), flush=True)
t0 = time.time()
nome = "Instalar-o-Sistema-sem-pacote" if COMPLETO else "Instalar-o-Sistema"
cmd = [r"C:\Projetos\Sistema\App\venv_qt\Scripts\python.exe", "-m", "PyInstaller", "--noconfirm", "--onefile",
       "--noconsole", "--name", nome, "--distpath", os.path.join(S, "dist"),
       "--workpath", os.path.join(S, "work"), "--specpath", S, "--paths", EMP, "--paths", os.path.dirname(EMP)]
if not COMPLETO:
    cmd += ["--add-data", zp + os.pathsep + "."]
r = subprocess.run(cmd + [os.path.join(EMP, "instalar_o_sistema.py")], capture_output=True, text=True)
print(r.stderr[-600:] if r.returncode else "", flush=True)
exe = os.path.join(S, "dist", nome + ".exe")
if COMPLETO and r.returncode == 0:
    # o zip COLADO no fim do .exe (o instalar_o_sistema.py lê o zip do próprio arquivo; nada vai à pasta temporária)
    final = os.path.join(S, "dist", "Instalar-o-Sistema-completo.exe")
    with open(final, "wb") as f:
        for parte in (exe, zp):
            with open(parte, "rb") as g:
                while True:
                    b = g.read(8 << 20)
                    if not b: break
                    f.write(b)
    os.remove(exe); exe = final
print("exe", os.path.exists(exe) and "%.1f MB" % (os.path.getsize(exe) / 2**20), "em %.0f s" % (time.time() - t0), "código", r.returncode)
