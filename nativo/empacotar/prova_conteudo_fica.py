# -*- coding: utf-8 -*-
"""PROVA (12/11/2026): a atualização LEVE não apaga o conteúdo que o instalador COMPLETO pôs (as apresentações das
crianças); o resto da regra de limpar_sobras continua (arquivo velho do programa, igual ao anotado, sai).
uso: python empacotar/prova_conteudo_fica.py"""
import os, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instalador_nativo as I
d = tempfile.mkdtemp(prefix="prova_conteudo_")
def poe(rel, txt):
    p = os.path.join(d, *rel.split("/")); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(txt); return I.md5(p)
antes = {r: poe(r, r) for r in ("SistemaNativo.exe", "_internal/velho.dll", "_internal/leve/cias169/1__Slide0002.jpg",
                                 "_internal/cias169/1/pronto.json", "_internal/animacoes/indice.json")}
agora_leve = {"SistemaNativo.exe": antes["SistemaNativo.exe"]}            # a atualização leve: sem conteúdo, sem velho.dll
tirados, _ = I.limpar_sobras(d, antes, agora_leve)
falhas = []
def confere(nome, ok):
    print(("OK   " if ok else "FALHA"), nome, flush=True)
    if not ok: falhas.append(nome)
confere("o arquivo velho do programa sai", "_internal/velho.dll" in tirados)
confere("o vídeo/imagem das crianças fica", os.path.exists(os.path.join(d, "_internal", "leve", "cias169", "1__Slide0002.jpg")))
confere("o índice 16:9 fica", os.path.exists(os.path.join(d, "_internal", "cias169", "1", "pronto.json")))
confere("o índice 4:3 fica", os.path.exists(os.path.join(d, "_internal", "animacoes", "indice.json")))
# e um COMPLETO novo, que traz a pasta leve: o que sobrou de conteúdo velho ali dentro pode sair
agora_comp = dict(agora_leve); agora_comp["_internal/leve/cias169/2__Slide0001.jpg"] = "x"
tirados2, _ = I.limpar_sobras(d, antes, agora_comp)
confere("completo novo limpa o conteúdo velho da pasta que ele traz", "_internal/leve/cias169/1__Slide0002.jpg" in tirados2)
print("RESULTADO: %d falha(s)" % len(falhas))
