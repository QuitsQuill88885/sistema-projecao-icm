# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('index.html', '.'), ('projecao.html', '.'), ('carregando.html', '.'), ('controle.html', '.'), ('app.js', '.'), ('app.css', '.'), ('icones.js', '.'), ('sistema.png', '.'), ('sistema.ico', '.'), ('afinador.js', '.'), ('manifest.json', '.'), ('dados', 'dados'), ('fundos', 'fundos'), ('fontes', 'fontes')]
binaries = []
hiddenimports = ['win32com.client', 'tkinter', 'qrcode', 'webview', 'webview.platforms.edgechromium',
                 # a porta segura (https) do afinador: o Sistema emite o proprio
                 # certificado, entao a biblioteca precisa viajar dentro do programa
                 'cryptography', 'cryptography.hazmat.backends.openssl', 'cryptography.x509']
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['sistema.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # nunca engordar o instalador por acidente: o PDF quem abre e o navegador
    excludes=['pymupdf', 'fitz', 'numpy', 'matplotlib', 'scipy', 'pandas'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
splash = Splash(
    'splash.png',
    binaries=a.binaries,
    datas=a.datas,
    # barra dourada: escrita bloco a bloco por marcar_splash() em cima do
    # trilho vazio do splash.png. Consolas e monoespacada, entao os blocos
    # emendam sem falha; 31 blocos de 6px = os 186px exatos do trilho.
    # O caractere e U+2584 (meio-bloco): no tamanho 8 ele emenda LISO.
    # Bloco cheio U+2588 no tamanho 5 serrilhava (36 colunas com dente).
    text_pos=(117, 227),
    text_size=8,
    text_color='#e8b93c',
    text_font='Consolas',
    # sem isto o PyInstaller escreve 'Initializing' em ingles
    # no lugar da barra; comeca com 2 blocos ja acesos
    text_default='▄▄',
    minify_script=True,
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    [],
    exclude_binaries=True,
    name='Sistema',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='versao_exe.txt',   # nome do programa no firewall e nas propriedades
    icon=['sistema.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    splash.binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Sistema',
)
