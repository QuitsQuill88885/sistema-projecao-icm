# -*- mode: python ; coding: utf-8 -*-
# O INSTALADOR LEVE.
#
# Diferenca para o "Instalar o Sistema.spec": aqui NAO entra build_inst/programa.
# E' exatamente isso que faz ele ser pequeno — ele nao carrega o Sistema dentro,
# vai buscar no GitHub na hora. Sem os louvores, a Biblia e os fundos, sobra so
# a janela e o motor do Edge.
from PyInstaller.utils.hooks import collect_all

# os certificados-raiz viajam DENTRO do programa: sem eles, no Windows
# novo da igreja o download falhava dizendo que era a internet
datas = [('icones.js', '.'), ('cacert.pem', '.')]
binaries = []
hiddenimports = ['webview', 'webview.platforms.edgechromium']
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['baixador.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
splash = Splash(
    'splash_instalador.png',
    binaries=a.binaries,
    datas=a.datas,
    # Sem texto: este .exe e ONEFILE, e o carregador do PyInstaller escreve o
    # nome de cada arquivo que descompacta neste campo. Nao da para disputar.
    text_pos=None,
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    splash,
    splash.binaries,
    [],
    name='Baixar o Sistema',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='versao_baixador.txt',
    icon=['instalador.ico'],
)
