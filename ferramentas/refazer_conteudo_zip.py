# -*- coding: utf-8 -*-
"""Refaz o Conteudo.zip que o instalador copia para %APPDATA%\\Sistema Projecao.

As cifras, as melodias e as animacoes NAO viajam dentro do .exe: viajam neste
pacote. Quando o banco de cifras muda, o zip precisa sair de novo.

Por que nao e' um zip qualquer:
  - `.json` comprime de verdade (deflate) — o banco de cifras encolhe muito;
  - `.webp` entra SEM comprimir: ja' e' formato comprimido, e deflate por cima
    ganhava 1,8% e custava o tempo todo;
  - no fim ele CONFERE: que nenhum backup entrou no pacote e que o banco de
    cifras dentro do zip e' byte a byte o mesmo que esta' no App. Conferidor
    que perdoa nao avisa que quebrou.

Estava no scratchpad de uma sessao e se perdeu quando ela rotacionou; agora
mora aqui, junto do programa. (13/09/2026)
"""
import os, sys, zipfile, hashlib, shutil, time

RAIZ = r"C:\Projetos\Sistema"
FONTE = os.path.join(RAIZ, "Pacote completo", "Conteudo")
ZIP = os.path.join(RAIZ, "Pacote completo", "Conteudo.zip")
APP = os.path.join(RAIZ, "App", "ICM Ipero Projecao")
BANCO_APP = os.path.join(APP, "conteudo_leve", "cifras", "acordes.json")
BANCO_PKG = os.path.join(FONTE, "cifras", "acordes.json")
# Padroes de BACKUP. Cuidado: "antes_" sozinho e' largo demais e recusou
# "QUEM_ERA_EU_ANTES_DE_CONHECER.json", que e' um louvor de verdade.
SUSPEITO = ("_backup", "backup_", "acordes_antes", "_antes_do_", "_antigo",
            ".bak", "aposentado", ".anterior")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    # 1. o pacote tem de levar o banco que o App usa
    if md5(BANCO_APP) != md5(BANCO_PKG):
        shutil.copy2(BANCO_APP, BANCO_PKG)
        print("banco de cifras atualizado no pacote (%.2f MB)" % (os.path.getsize(BANCO_PKG) / 1048576))
    else:
        print("banco de cifras do pacote ja' esta' igual ao do App")

    # 2. varrer, recusando backup
    arquivos, lixo = [], []
    for dirp, _dirs, nomes in os.walk(FONTE):
        for n in nomes:
            p = os.path.join(dirp, n)
            rel = os.path.relpath(p, FONTE).replace("\\", "/")
            if any(s in rel.lower() for s in SUSPEITO):
                lixo.append(rel)
                continue
            arquivos.append((p, rel))
    if lixo:
        print("RECUSADOS (backup nao entra no pacote): %d" % len(lixo))
        for r in lixo[:6]:
            print("   %s" % r)
    print("arquivos a empacotar: %d" % len(arquivos))

    # 3. escrever
    tmp = ZIP + ".novo"
    t0 = time.time()
    with zipfile.ZipFile(tmp, "w") as z:
        for p, rel in sorted(arquivos, key=lambda x: x[1]):
            comp = zipfile.ZIP_STORED if rel.lower().endswith(".webp") else zipfile.ZIP_DEFLATED
            z.write(p, rel, compress_type=comp)
    print("zip escrito em %.0f s (%.1f MB)" % (time.time() - t0, os.path.getsize(tmp) / 1048576))

    # 4. A PROVA: o banco dentro do zip e' o mesmo do App?
    with zipfile.ZipFile(tmp) as z:
        dentro = z.read("cifras/acordes.json")
    if hashlib.md5(dentro).hexdigest() != md5(BANCO_APP):
        os.remove(tmp)
        print("ABORTADO: o banco dentro do zip NAO e' o do App")
        return 1
    print("PROVA OK: o banco dentro do zip e' byte a byte o do App")

    if os.path.exists(ZIP):
        ant = ZIP + ".anterior"
        if os.path.exists(ant):
            os.remove(ant)
        os.rename(ZIP, ant)
    os.rename(tmp, ZIP)
    print("pronto: %s (%.1f MB)" % (os.path.basename(ZIP), os.path.getsize(ZIP) / 1048576))
    return 0


if __name__ == "__main__":
    sys.exit(main())
