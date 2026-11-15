# -*- mode: python ; coding: utf-8 -*-
# O PACOTE do Sistema Nativo (03/11/2026, ordem dele: "tá aqui o código binário, o sistema inteiro funciona").
# Tudo DENTRO: Python, Qt Quick, as telas QML, os dados (louvores, Bíblia, selos, fundos, fontes) e as páginas que o
# CELULAR abre (controle.html, projecao.html da prévia). Nada instalado na máquina, nenhum navegador dentro.
# uso: python -m PyInstaller --noconfirm SistemaNativo.spec   (pelo python do App\venv_qt)
import os

APP = r"C:\Projetos\Sistema\App\ICM Ipero Projecao"
NAT = r"C:\Projetos\Sistema\Nativo"

datas = [(os.path.join(NAT, "qml"), "qml")]
# a LETRA DO PAINEL embutida (Painel ICM, Liberation Sans e as licenças OFL; 07/11): sem ela o pacote caía na fonte do
# sistema (Segoe no Windows, outra no Vaio), justo o que a paridade 1:1 não pode
datas.append((os.path.join(NAT, "fontes", "ui"), os.path.join("fontes", "ui")))
# os VÍDEOS das CIAS (623 MP4 H.264, 08/11/2026): sem eles o programa instalado mostrava a tela parada (auditoria)
# os vídeos das CIAS DENTRO do pacote só com NATIVO_COM_VIDEO=1 (08/11, HD: fora do .exe da atualização; o 4.0 toca o WebP
# animado que a 3.0.x já tem na pasta do usuário, e o MP4 quando houver)
if os.environ.get("NATIVO_COM_VIDEO") == "1":
  datas += [(os.path.join(NAT, "cache_cias", f), "video") for f in sorted(os.listdir(os.path.join(NAT, "cache_cias")))
          if f.endswith(".mp4") or f == "mapa.json"]
# o QtQuick.Effects (o desfoque e as sombras do visual 1:1, 07/11): o empacotador NÃO leva sozinho (o pacote não abria:
# "module QtQuick.Effects is not installed"). A pasta do plugin e a biblioteca de que ele depende
PYSIDE = os.path.join(r"C:\Projetos\Sistema\App\venv_qt\Lib\site-packages", "PySide6")
datas.append((os.path.join(PYSIDE, "qml", "QtQuick", "Effects"), os.path.join("PySide6", "qml", "QtQuick", "Effects")))
binarios_extra = [(os.path.join(PYSIDE, "Qt6QuickEffects.dll"), "PySide6")]
# o que o celular abre (servido pelo sistema.py de dentro do pacote) e o que o telão desenha
for nome in ("controle.html", "projecao.html", "retorno.html", "afinador.js", "icones.js", "manifest.json",
             "sistema.png", "sistema.ico", "cacert.pem"):
    datas.append((os.path.join(APP, nome), "."))
for pasta in ("fundos", "fontes", "gestos", "apresentacoes"):   # apresentacoes: as que vêm junto (25 MB, 03/11)
    datas.append((os.path.join(APP, pasta), pasta))
# A PASTA dados VAI ARQUIVO POR ARQUIVO, NUNCA INTEIRA (a lição de 31/08: 44 MB de backups pegavam carona)
for nome in ("biblia.js", "fundos.js", "galeria.js", "louvores.js", "repeticoes.js", "repetidos.js", "sugestoes.js",
             "temas.js", "tipologia.js", "gestos.js", "cifras_ocultas.json"):
    cam = os.path.join(APP, "dados", nome)
    if not os.path.isfile(cam):
        raise SystemExit("falta o arquivo de dados: %s" % cam)
    datas.append((cam, "dados"))

a = Analysis(
    [os.path.join(NAT, "sistema_nativo.py")],
    pathex=[NAT, APP],
    binaries=binarios_extra,
    datas=datas,
    hiddenimports=["sistema", "rede", "cerebro", "sugestoes", "PySide6.QtMultimedia", "win32com.client", "pythoncom"],   # o PowerPoint (COM) só é chamado ao abrir apresentação   # o vídeo das CIAS só aparece no QML: o empacotador não vê sozinho
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick", "webview",
              "tkinter", "PySide6.QtOpenGLWidgets", "PySide6.QtWidgets", "PySide6.QtPdf",
              "PySide6.Qt3DCore", "PySide6.QtCharts", "PySide6.QtDataVisualization"],
    noarchive=False,
    optimize=1,
)

# O QUE NÃO ENTRA. O empacotador puxa o Qt inteiro; o motor de navegador do Qt (QtWebEngine, 195 MB) é justamente
# o WebView que não pode existir aqui. O opengl32sw (20 MB) é o desenho por software do OpenGL: o Qt Quick no
# Windows desenha pelo Direct3D 11 e, sem placa, tem o desenho por software próprio dele.
FORA = ("webengine", "webview", "webchannel", "quick3d", "qt3d", "3dcore", "3drender", "3dinput", "3danimation",
        "3dextras", "3dlogic", "qt6pdf", "qtpdf", "charts", "datavis", "graphs", "location", "positioning",
        "bluetooth", "nfc", "sensors", "serialport", "scxml", "virtualkeyboard", "spatialaudio", "texttospeech",
        "remoteobjects", "qt6help", "qthelp", "designer", "uitools", "qt6test", "qttest", "quicktest", "sql",
        "/translations/", "qtquick/scene3d", "qtquick3d", "lottie", "httpserver", "opengl32sw",
        "qtopenglwidgets", "shadertools", "qt6widgets", "quickwidgets", "/qtquick/pdf",   # o QtQuick.Effects ENTRA (07/11: o desfoque e as sombras)
        "/qtquick/shapes/designhelpers", "/qtquick/timeline", "/qtquick/particles", "particles",
        "/qtquick/controls/fusion", "/qtquick/controls/imagine", "/qtquick/controls/material",
        "/qtquick/controls/universal", "/qtquick/controls/fluentwinui3", "/qtquick/controls/windows",
        # 08/11/2026 (enxugar, medido no dist16): as DLLs dos estilos que o Nativo não usa (ele usa o Basic), os módulos
        # Python que ele nunca importa (QtOpenGL/QtNetwork .pyd: as DLLs Qt6OpenGL/Qt6Network ficam, o Qt Quick precisa),
        # QML e plugins sem uso
        "quickcontrols2fluentwinui3", "quickcontrols2imagine", "quickcontrols2material", "quickcontrols2universal",
        "quickcontrols2fusion", "quickcontrols2windows", "labsstylekit",
        "/qt5compat", "qt6core5compat", "websockets", "qmltooling", "statemachine", "vectorimage",
        "/tls/", "networkinformation", "qtiff", "qwbmp", "qtga", "qicns", "qoffscreen", "qminimal", "qdirect2d")
def _fica(t):
    n = (t[0] + "|" + t[1]).lower().replace("\\", "/")
    return not any(f in n for f in FORA)
a.binaries = [t for t in a.binaries if _fica(t)]
a.datas = [t for t in a.datas if _fica(t) or t[0].startswith(("dados", "fundos", "fontes", "gestos", "qml", "apresentacoes"))]

pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="SistemaNativo", debug=False, strip=False, upx=False,
          console=False, icon=os.path.join(APP, "sistema.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="SistemaNativo")
