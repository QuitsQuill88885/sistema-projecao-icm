# Prova no COMPILADO, nao no fonte: abre o instalador que a igreja baixa e confere o que vai dentro.
import hashlib, io, json, os, sys, zlib
from PyInstaller.archive.readers import CArchiveReader
APP = r"C:\Projetos\Sistema\App\ICM Ipero Projecao"
md5 = lambda b: hashlib.md5(b).hexdigest()
ok = True

def falha(msg):
    global ok
    ok = False
    print("FALHOU:", msg)

inst = os.path.join(APP, "dist", "Instalar-o-Sistema.exe")
arq = CArchiveReader(inst)
nomes = list(arq.toc.keys())
banco_fonte = open(os.path.join(APP, "conteudo_leve", "cifras", "acordes.json"), "rb").read()
k = [n for n in nomes if n.replace("\\", "/").endswith("conteudo_leve/cifras/acordes.json")]
if not k:
    falha("acordes.json nao esta no instalador")
else:
    b = arq.extract(k[0])
    print("cifras no instalador == fonte:", md5(b) == md5(banco_fonte))
    if md5(b) != md5(banco_fonte): falha("banco do instalador difere")
    A = json.loads(b)
    t = [x["t"] for x in A["MEU|TODO-PODEROSO ÉS|TODO-PODEROSO ÉS,"]["linhas"]]
    print("cifra: 'FINAL:' presente?", "FINAL:" in t, "| linhas:", len(t))
    if "FINAL:" in t or len(t) != 37: falha("cifra do Todo-Poderoso")

# o programa em si vai dentro do instalador como pasta 'programa'
pk = [n for n in nomes if n.replace("\\", "/").endswith("programa/_internal/app.js")]
lk = [n for n in nomes if n.replace("\\", "/").endswith("programa/_internal/dados/louvores.js")]
vk = [n for n in nomes if n.replace("\\", "/").endswith("programa/Sistema.exe")]
print("app.js no instalador:", bool(pk), "| louvores.js:", bool(lk), "| Sistema.exe:", bool(vk))
if pk:
    js = arq.extract(pk[0]).decode("utf-8")
    t1 = "s.num === 'MEU') ? '' : s.num" in js
    t2 = "s.num && s.num !== 'MEU' ? s.num + ' - '" in js
    print("conserto MEU MEU (lista):", t1, "| (telao):", t2)
    if not (t1 and t2): falha("app.js sem o conserto")
else:
    # pode estar dentro de um PYZ/pasta diferente; mostra onde esta
    print("amostra nomes:", [n for n in nomes if "app.js" in n][:5])
if lk:
    s = arq.extract(lk[0]).decode("utf-8")
    L = json.loads(s[s.index("=") + 1:].strip().rstrip(";"))
    lv = [l for l in L if l["titulo"] == "TODO-PODEROSO ÉS"][0]
    ordem = [(x["label"], x["linhas"][0][:12]) for x in lv["slides"]]
    print("slides no instalador:", ordem)
    if len(ordem) != 8 or ordem[5][0] != "" or ordem[3][0] != "CORO": falha("ordem dos slides")
if vk:
    exe = arq.extract(vk[0])
    print("Sistema.exe tem 2.9.4 na versao:", "2.9.4".encode("utf-16-le") in exe)
    if "2.9.4".encode("utf-16-le") not in exe: falha("versao do exe")
print("\nRESULTADO:", "TUDO CONFERE" if ok else "NAO PUBLICAR")
