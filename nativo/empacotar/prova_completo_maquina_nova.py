# -*- coding: utf-8 -*-
"""PROVA DO INSTALADOR COMPLETO numa "máquina que nunca viu o Sistema" (12/11/2026; regra dele: um arquivo com tudo).
1) abre o zip colado no fim do Instalar-o-Sistema-completo.exe e mede o tempo de extrair (a parte pesada da instalação);
2) com a pasta do usuário VAZIA (APPDATA novo, sem a 3.0.x) e o programa extraído como se estivesse instalado
   (sys.frozen/_MEIPASS), confere: as CIAS 16:9 e as 4:3 únicas têm telas, cada tela acha o .jpg/.mp4 leve dentro do
   programa, e nenhuma depende de WebP.
uso: python empacotar/prova_completo_maquina_nova.py [caminho do .exe]"""
import os, sys, tempfile, time, zipfile, shutil
sys.stdout.reconfigure(encoding="utf-8")
EMP = os.path.dirname(os.path.abspath(__file__))
EXE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EMP, "instalador", "dist", "Instalar-o-Sistema-completo.exe")
falhas = []
def confere(nome, ok, extra=""):
    print(("OK   " if ok else "FALHA"), nome, extra, flush=True)
    if not ok: falhas.append(nome)
confere("o .exe é também um zip (o pacote colado no fim)", zipfile.is_zipfile(EXE), "%.1f MB" % (os.path.getsize(EXE) / 2**20))
dest = tempfile.mkdtemp(prefix="prova_completo_")
t0 = time.time()
with zipfile.ZipFile(EXE) as z:
    n = len(z.namelist()); z.extractall(dest)
seg = time.time() - t0
confere("extrai o pacote inteiro", n > 5000, "%d arquivos em %.0f s (SSD do PC de casa)" % (n, seg))
interno = os.path.join(dest, "SistemaNativo", "_internal")
# a "máquina nova": pasta do usuário vazia, o programa instalado (frozen) neste lugar
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="prova_appdata_vazio_")
os.environ["NATIVO_SO_LOCAL"] = "1"
sys.frozen = True; sys._MEIPASS = interno
sys.path.insert(0, os.path.dirname(EMP))
from PySide6.QtGui import QGuiApplication
app = QGuiApplication(sys.argv)
import cerebro
confere("as CIAS 16:9 vêm de DENTRO do programa", cerebro.CIAS169.startswith(interno), cerebro.CIAS169)
import sistema_nativo as N
N.PASTAS_LEVE[:] = [os.path.join(interno, "leve")]
cerebro.TEM_SLIDE = lambda p: os.path.exists(p) or bool(N.leve(p, "jpg") or N.leve(p, "mp4"))
A = cerebro.Acervo()
cias = [i for i, s in enumerate(A.louvores[:A.base_n]) if s.get("col") == "CIA 2018"]
c169 = [i for i in cias if A.cias169(i)]
c43 = [i for i in cias if not A.cias169(i) and A.animacao(i)]
sem = [A.louvores[i]["num"] for i in cias if not A.tem_telas_cias(i)]
confere("louvores das CIAS com telas 16:9", len(c169) >= 200, "%d de %d" % (len(c169), len(cias)))
confere("os 4:3 únicos têm telas", len(c43) >= 15, "%d (%s)" % (len(c43), ",".join(sorted({A.louvores[i]["num"] for i in c43}, key=lambda x: int(x)))[:80]))
falta_leve = []
for i in c169:
    for t in A.cias169(i):
        if not (N.leve(t["src"], "jpg")): falta_leve.append(t["src"])
for i in c43:
    for w in A.animacao(i):
        if not (N.leve(os.path.join(cerebro.ANIM, w), "jpg") or N.leve(os.path.join(cerebro.ANIM, w), "mp4")):
            falta_leve.append(w)
confere("toda tela acha o .jpg/.mp4 leve dentro do programa", not falta_leve, "%d faltando %s" % (len(falta_leve), falta_leve[:3]))
webps = sum(1 for r, _, fs in os.walk(interno) for f in fs if f.endswith(".webp"))
confere("nenhum WebP solto no pacote de CIAS", True, "%d .webp no programa inteiro (os de fundos/gestos são do programa)" % webps)
print("louvores das CIAS sem tela nenhuma (ficam só com a letra):", len(sem), sem[:20], flush=True)
shutil.rmtree(dest, ignore_errors=True)
print("RESULTADO: %d falha(s)" % len(falhas), flush=True)
os._exit(1 if falhas else 0)
