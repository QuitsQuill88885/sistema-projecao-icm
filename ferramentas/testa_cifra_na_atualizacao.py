# -*- coding: utf-8 -*-
"""PERGUNTA: o botao "Atualizar" do Sistema leva CIFRA NOVA para o computador
do operador, ou as cifras so entram pela instalacao / pelo "Completar"?

Nao basta ler o codigo: aqui a rotina de verdade do instalador roda contra uma
pasta de MENTIRA, com uma cifra velha dentro e um backup do operador ao lado.
Nada da instalacao real do Samuel e tocado.
"""
import os
import sys
import json
import shutil
import hashlib
import importlib.util

APP = r"C:\Projetos\Sistema\App\ICM Ipero Projecao"
TESTE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teste_dados")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------- pasta de mentira
if os.path.isdir(TESTE):
    shutil.rmtree(TESTE)
os.makedirs(os.path.join(TESTE, "cifras"), exist_ok=True)

velha = os.path.join(TESTE, "cifras", "acordes.json")
with open(velha, "w", encoding="utf-8") as f:
    json.dump({"VELHO|CIFRA DE MENTIRA|PRIMEIRA LINHA": {"linhas": []}}, f)
md5_velho = md5(velha)

# um backup datado, como o operador costuma ter na pasta
backup = os.path.join(TESTE, "cifras", "acordes_backup_do_operador.json")
with open(backup, "w", encoding="utf-8") as f:
    f.write('{"nao pode sumir": true}')
md5_backup = md5(backup)

# um arquivo que SO existe na pasta do operador (nao vem no instalador)
soDele = os.path.join(TESTE, "cifras", "anotacao_do_kevin.txt")
with open(soDele, "w", encoding="utf-8") as f:
    f.write("isto e do operador")

# ---------------------------------------------------- carrega o instalador
spec = importlib.util.spec_from_file_location("inst", os.path.join(APP, "instalador.py"))
inst = importlib.util.module_from_spec(spec)
sys.modules["inst"] = inst
spec.loader.exec_module(inst)

# desvia o alvo para a pasta de mentira e a origem para o repositorio
inst.DADOS = TESTE
inst.origem = lambda: APP

print("ANTES")
print("   acordes.json de mentira : %s" % md5_velho[:12])
print("   fonte no repositorio    : %s"
      % md5(os.path.join(APP, "conteudo_leve", "cifras", "acordes.json"))[:12])
print()

n = inst.copiar_conteudo_leve()
print("copiar_conteudo_leve() copiou %d arquivos" % n)
print()

md5_depois = md5(velha)
md5_fonte = md5(os.path.join(APP, "conteudo_leve", "cifras", "acordes.json"))

print("DEPOIS")
print("   acordes.json na pasta   : %s" % md5_depois[:12])
print("   trocou pela do repo?    : %s" % ("SIM" if md5_depois == md5_fonte else "NAO"))
print("   backup do operador vivo?: %s"
      % ("SIM" if os.path.exists(backup) and md5(backup) == md5_backup else "NAO"))
print("   arquivo so dele vivo?   : %s" % ("SIM" if os.path.exists(soDele) else "NAO"))
print()

# quantas cifras entraram
try:
    with open(velha, encoding="utf-8") as f:
        d = json.load(f)
    print("   cifras dentro do acordes.json que chegou: %d" % len(d))
except Exception as e:
    print("   nao consegui ler o acordes.json:", e)

print()
print("VEREDITO: %s" % (
    "o instalador SOBRESCREVE a cifra antiga -> atualizar LEVA cifra nova"
    if md5_depois == md5_fonte else
    "o instalador NAO trocou a cifra -> atualizar NAO leva cifra nova"))
