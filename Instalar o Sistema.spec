# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# conteudo_leve = cifras + melodias (11 MB de JSON). Vao DENTRO do
# instalador de proposito: sao dados pequenos, e sem eles quem instala na
# igreja fica sem acorde ate' baixar meio giga. O peso de verdade (as 488
# MB de animacoes das CIAS) e' que continua fora, no Conteudo.zip.
datas = [('build_inst/programa', 'programa'), ('icones.js', '.'),
         ('sistema.ico', '.'), ('conteudo_leve', 'conteudo_leve')]
binaries = []
hiddenimports = ['win32com.client']


a = Analysis(
    ['instalador.py'],
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
    # SEM texto de proposito. Este .exe e ONEFILE: o carregador do PyInstaller
    # escreve o nome de CADA arquivo que descompacta ("zlib1.dll"...) neste
    # campo, e nao da para disputar o campo com ele. Por isso o splash do
    # instalador nao tem trilho de barra — so o logo.
    # (O app principal e ONEDIR: nao descompacta nada, e la a barra anda.)
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
    name='Instalar o Sistema',
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
    version='versao_instalador.txt',   # nome do programa no firewall e nas propriedades
    icon=['sistema.ico'],
)
