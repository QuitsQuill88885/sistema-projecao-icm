# -*- mode: python ; coding: utf-8 -*-
# O COMPLETO DE UM ARQUIVO SO: o instalador de sempre + a pasta Conteudo
# inteira (animacoes, cifras, melodias), tudo dentro de um unico .exe.
# Nada de zip para o usuario — o carregador do PyInstaller descompacta com a
# telinha de carregamento na frente, e o instalador real assume dali.
#
# ANTES de compilar este spec, compile o "Instalar o Sistema.spec" e confira
# que Desktop\Sistema\Pacote completo\Conteudo esta em dia — e' de la que o
# conteudo entra.

datas = [('dist/Instalar o Sistema.exe', '.')]

a = Analysis(
    ['instalador_completo.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Caminho RELATIVO ao .spec: a pasta do projeto já mudou de lugar uma vez
# (Desktop\Sistema -> Desktop\Projetos AI\Sistema) e o caminho fixo aqui fez o
# instalador completo falhar calado no meio da cadeia de build.
import os as _os
_raiz = _os.path.abspath(_os.path.join(SPECPATH, '..', '..'))
_conteudo = _os.path.join(_raiz, 'Pacote completo', 'Conteudo')
if not _os.path.isdir(_conteudo):
    raise SystemExit('nao achei a pasta Conteudo em: %s' % _conteudo)
conteudo = Tree(_conteudo, prefix='Conteudo')
pyz = PYZ(a.pure)
splash = Splash(
    'splash_instalador.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,          # onefile: o carregador escreve nomes de arquivo aqui
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    conteudo,
    splash,
    splash.binaries,
    [],
    name='Instalar o Sistema completo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # webp/PDF nao comprimem; UPX so atrasaria a abertura
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='versao_instalador.txt',
    icon=['sistema.ico'],
)
