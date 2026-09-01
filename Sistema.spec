# -*- mode: python ; coding: utf-8 -*-
import os as _os_spec
from PyInstaller.utils.hooks import collect_all

datas = [('index.html', '.'), ('projecao.html', '.'), ('carregando.html', '.'), ('controle.html', '.'), ('app.js', '.'), ('app.css', '.'), ('icones.js', '.'), ('sistema.png', '.'), ('sistema.ico', '.'), ('afinador.js', '.'), ('manifest.json', '.'), ('cacert.pem', '.'), ('fundos', 'fundos'), ('fontes', 'fontes')]

# A PASTA dados VAI ARQUIVO POR ARQUIVO, NUNCA INTEIRA.
# Em 31/08/2026 descobri 44 MB de backups meus (louvores_backup_*, *_antes_*)
# dentro do .exe: o instalador pequeno pesava 62 MB e 44 deles eram lixo que eu
# mesmo tinha deixado na pasta. Ja' tinha acontecido igual com as cifras. Pegar
# a pasta INTEIRA e' que abre essa porta - agora so' entra o que esta' na lista,
# e backup novo nao consegue mais pegar carona. Leveza e' lei nesta casa.
import os as _os
_DADOS = ['biblia.js', 'consertos_louvores.json', 'fundos.js', 'galeria.js',
          'louvores.js', 'repeticoes.js', 'sugestoes.js', 'temas.js',
          'tipologia.js']
for _nome in _DADOS:
    _cam = _os.path.join(SPECPATH, 'dados', _nome)
    if not _os.path.isfile(_cam):
        raise SystemExit('falta o arquivo de dados: %s' % _cam)
    datas.append((_cam, 'dados'))
_sobra = sorted(f for f in _os.listdir(_os.path.join(SPECPATH, 'dados'))
                if f not in _DADOS and not f.startswith('.'))
if _sobra:
    print('AVISO: dados/ tem arquivo fora da lista, NAO entra no programa: %s'
          % ', '.join(_sobra))

binaries = []
# 'tkinter' SAIU: entrava só pela janela de escolher arquivo e trazia
# 8 MB de Tcl/Tk. Agora a janela é a nativa do Windows, pelo pywin32.
hiddenimports = ['win32com.client', 'qrcode', 'webview', 'webview.platforms.edgechromium',
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
    excludes=['PIL', 'Pillow', 'tkinter', '_tkinter',
              'pymupdf', 'fitz', 'numpy', 'matplotlib', 'scipy', 'pandas'],
    noarchive=False,
    optimize=0,
)
# TCL/TK: 8 MB que NAO DA PARA TIRAR, e ja tentei.
# Depois que a janela de escolher arquivo virou a nativa do Windows, nada mais
# importa tkinter - conferido: `_tkinter.pyd` NAO entra no programa. Mesmo
# assim tcl86t.dll, tk86t.dll, _tcl_data e _tk_data continuam vindo.
#
# NAO SAO ORFAOS, e nao adianta filtrar a.binaries/a.datas (tentei: nao muda
# nada). Eles vem do **Splash** logo abaixo: a tela de carregamento do
# PyInstaller e desenhada em Tk. Sao o preco da barrinha dourada que aparece
# enquanto o Sistema abre - e o Sistema demora alguns segundos para subir
# (acha porta livre, libera no firewall, gera o certificado do afinador),
# entao a barrinha nao e enfeite: e o que diz ao operador que esta abrindo.
#
# Se um dia valer trocar 8 MB pela tela de carregamento, e so tirar o Splash
# daqui, do EXE() e do COLLECT(). E decisao do Samuel, nao minha.

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
