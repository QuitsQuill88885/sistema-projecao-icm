# -*- coding: utf-8 -*-
"""SISTEMA NATIVO (03/11/2026, ordem dele: "motor 100% dedicado, sem WebView, tudo local").

Python + Qt Quick (PySide6), SEM navegador nenhum dentro. Uma janela de PAINEL para o operador e o TELÃO numa
janela própria, na 2a tela se houver (QGuiApplication.screens(); a tela que chega ou sai vira aviso na hora).
O cérebro (cerebro.py) guarda o acervo e as regras; aqui é só o estado do que está no ar e as ordens.

uso:  python sistema_nativo.py                 (painel + telão; telão na 2a tela se existir, senão janela)
      python sistema_nativo.py --janela        (telão sempre em janela, para testar sem tomar a TV)
      python sistema_nativo.py --fotos <pasta> (sem tela nenhuma: projeta uma lista de louvores e grava PNG do telão)
"""
import glob, json, os, re, subprocess, sys, tempfile, threading, time, unicodedata
from collections import OrderedDict
from urllib.parse import unquote

AQUI = os.path.dirname(os.path.abspath(__file__))
# sem terminal (aberto pelo atalho, pythonw): o que seria impresso vai para nativo.log, ao lado do programa
if sys.stdout is None or sys.stderr is None:
    _log = open(os.path.join(AQUI, "nativo.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = _log
    print("---- aberto em", time.strftime("%d/%m/%Y %H:%M:%S"))
FOTOS =sys.argv[sys.argv.index("--fotos") + 1] if "--fotos" in sys.argv else None
if FOTOS and os.environ.get("NATIVO_REAL") != "1":     # NATIVO_REAL=1: fotos numa janela de verdade (vídeo)
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import Q_ARG, QEvent, QMetaObject, QObject, QRectF, Property, Qt, QSize, QTimer, QUrl, Signal, Slot, qInstallMessageHandler
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QImage, QImageReader, QSurfaceFormat, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickItem, QQuickView, QQuickWindow
from PySide6.QtQuickControls2 import QQuickStyle

import cerebro

def _avisos_do_qt(tipo, ctx, msg):        # no Windows o Qt fala para o depurador, não para o terminal
    sys.stderr.write("qt: %s\n" % msg)
# SÓ NO WINDOWS (08/11/2026, medido no Vaio): o repasse em Python precisa da trava do Python a cada aviso, e um aviso que
# nasce noutra thread do Qt enquanto a principal espera o QML TRAVA o programa para sempre (PYSIDE-1681; o PyQt6 tem o
# mesmo com o áudio do QtMultimedia). No Vaio, com o registro do QML ligado, o Nativo parou no setSource com 133 MB, sem
# janela. No Linux o Qt já escreve no terminal sozinho: o repasse não faz falta lá.
if sys.platform.startswith("win"):
    qInstallMessageHandler(_avisos_do_qt)

if sys.platform.startswith("linux"):
    # VÍDEO PELA PLACA NO LINUX (08/11/2026, medido no Vaio, Radeon HD 6320): com a integração GLX o Qt não consegue
    # entregar o quadro da VAAPI à placa, tenta copiá-lo para a memória ("Failed to sync surface: invalid VAContextID",
    # "Error transferring the data to system memory: -5") e TRAVA o programa no 1º vídeo das CIAS. Com EGL o quadro vai
    # direto: o mesmo vídeo das CIAS (H.264 1440x1080) toca com 13,6 s de CPU por minuto (no processador: 22,8).
    os.environ.setdefault("QT_XCB_GL_INTEGRATION", "xcb_egl")
    # 10/11/2026 (o banco do jeito dele no Vaio, aba Apresentações + telão no HDMI): pela placa, CADA vídeo que começa a
    # tocar trava a linha da interface ~220 ms logo depois de "BufferedMedia" (23 buracos > 150 ms em 23 cliques), e a
    # emenda do laço segura ~300 ms. Decodificando no PROCESSADOR: travada 81/279 -> 69/129 ms, 2 buracos, emenda 67-71 ms;
    # custa CPU (Vaio inteiro 37/53% -> 53/76%). CORREÇÃO DELE 10/11 11h48: "não é o contrário de tudo que a gente
    # estabeleceu?" A REGRA: o vídeo é decodificado pela PLACA, nunca formato que a CPU decodifique quadro a quadro (foi
    # por isso que o WebP saiu). O padrão segue a placa; o conserto dos ~220 ms é com a placa. NATIVO_VIDEO_CPU=1 = só medida.
    if os.environ.get("NATIVO_VIDEO_CPU"):
        os.environ.setdefault("QT_FFMPEG_DECODING_HW_DEVICE_TYPES", "none")
# o texto do TELÃO (Qt, campo de distância) em tons de CINZA, como o navegador desenha letra grande: o subpixel deixava
# franja azul/laranja na borda da letra branca, pior ainda dentro da camada da sombra (medido 08/11: 85 -> 60; Edge 52)
os.environ.setdefault("QSG_DISTANCEFIELD_ANTIALIASING", "gray")
fmt = QSurfaceFormat.defaultFormat()
fmt.setSwapInterval(int(os.environ.get("NATIVO_SWAP", "2")))   # 2 = teto de 30 quadros/s (medido na prova de fogo)
QSurfaceFormat.setDefaultFormat(fmt)


class DepositoApres(QQuickImageProvider):
    """O DEPÓSITO das imagens da apresentação (image://apres/<caminho>), 07/11/2026. No Vaio (E-450) abrir um slide
    custa 110-180 ms e as camadas animadas até 650 ms (medido, ferramentas/medir_imagens_apres.py); no PC de casa, 15-30 ms.
    O slide no ar, o de trás e o da frente ficam abertos na memória (QImage, que o telão e a prévia dividem); o da frente
    é aberto numa linha de fundo enquanto o atual está no ar. Nenhum efeito muda: só a hora em que a imagem é lida."""
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.imgs, self.manter, self.trava = {}, set(), threading.Lock()
        self.acertos = self.lidas = 0

    def requestImage(self, id_, size, pedido):
        p = unquote(id_)
        # 09/11 (Vaio, PySide 6.9.3): o QImage.scaled SEGURA a trava do Python (o painel parava 130 ms por imagem); a
        # leitura já encolhida pelo QImageReader solta (9 ms). A prévia pede menor: lê do disco já no tamanho dela.
        if pedido is not None and pedido.isValid() and pedido.width() > 0:
            r = QImageReader(p)
            t = r.size()
            if t.isValid() and pedido.width() < t.width():
                h = pedido.height() if pedido.height() > 0 else max(1, round(t.height() * pedido.width() / t.width()))
                esc = min(pedido.width() / t.width(), h / t.height())
                r.setScaledSize(QSize(max(1, round(t.width() * esc)), max(1, round(t.height() * esc))))
                r.setQuality(100)
                im = r.read(); self.lidas += 1
                if not im.isNull():
                    try: size.setWidth(im.width()); size.setHeight(im.height())
                    except Exception: pass
                    return im
        with self.trava:
            im = self.imgs.get(p)
        if im is None:
            im = QImage(p); self.lidas += 1
            with self.trava:
                if p in self.manter: self.imgs[p] = im
        else:
            self.acertos += 1
        # A5 (relato dele 07/11 21h16: "imagens das prévias mal renderizadas"): a PRÉVIA pede o tamanho dela; a imagem
        # inteira encolhida 6x na hora de desenhar saía serrilhada. Encolhe aqui, com qualidade (o deposito guarda a inteira)
        try:
            if pedido is not None and pedido.isValid() and 0 < pedido.width() < im.width():
                im = im.scaled(pedido.width(), max(1, pedido.height()) if pedido.height() > 0 else int(im.height() * pedido.width() / im.width()),
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception:
            pass
        try: size.setWidth(im.width()); size.setHeight(im.height())
        except Exception: pass
        return im

    def preparar(self, manter, abrir):
        """manter = os caminhos que ficam (o resto sai da memória); abrir = os que se abrem já, no fundo, nesta ordem."""
        with self.trava:
            self.manter = set(manter)
            for k in [k for k in self.imgs if k not in self.manter]: del self.imgs[k]
            falta = [p for p in abrir if p not in self.imgs]
        if not falta: return
        def ler():
            for p in falta:
                with self.trava:
                    if p in self.imgs or p not in self.manter: continue
                im = QImage(p)
                with self.trava:
                    if p in self.manter: self.imgs[p] = im
        threading.Thread(target=ler, name="deposito-apres", daemon=True).start()


# ---- O FORMATO LEVE (09/11/2026, teste dele no Vaio: o WebP é decodificado pelo PROCESSADOR, a placa não sabe VP8; "pode
# ser lento, só não pode travar"): ferramentas/apresentacoes_leves.py faz, à parte, o .mp4 H.264 de cada slide animado (a
# placa decodifica) e o .jpg de cada slide (abre 1,5x mais rápido que o WebP; a miniatura 4x). Os originais não mudam;
# faltou o leve, vale o original (como antes).
PASTAS_LEVE = [x for x in (os.environ.get("NATIVO_LEVE"), os.path.join(AQUI, "leve"),
                           os.path.join(os.path.dirname(cerebro.ANIM), "leve")) if x and not os.environ.get("NATIVO_SEM_LEVE")]
FMT_PARADO = os.environ.get("NATIVO_LEVE_PARADO", "jpg")      # "ktx" = a textura da placa (DXT1), para a medida no Vaio


def _linhas_da_tela(linhas):
    """A letra de uma tela 16:9 (textos.json) para a prévia: a linha "CORO" vira rótulo, e pedaço curto (a palavra que
    entra sozinha na animação: "NAQUELE / QUE / ME / FORTALECE") se junta à seguinte. Devolve (linhas, tem_coro)."""
    coro = any(l.strip(" :.").upper() == "CORO" for l in linhas)
    ls = [l for l in linhas if l.strip(" :.").upper() != "CORO"]
    out, acc = [], ""
    for l in ls:
        acc = (acc + " " + l).strip()
        if len(acc) >= 12:
            out.append(acc); acc = ""
    if acc:
        out.append(acc)
    return out, coro


def leve(p, ext):
    """O arquivo leve (.mp4/.jpg/.ktx) do slide `p`, se já foi feito; "" se não."""
    if not p:
        return ""
    partes = os.path.normpath(p).replace("\\", "/").split("/")
    sub = ""
    for k in range(len(partes) - 1, -1, -1):
        if partes[k] in ("apresentacoes", "slides_importados", "cache_cias169", "cias169", "animacoes"):
            sub = "cias169" if "cias169" in partes[k] else ("cias43" if partes[k] == "animacoes" else "")
            partes = partes[k + 1:]
            break
    else:
        partes = partes[-2:]
    nome = os.path.splitext("__".join(partes))[0] + "." + ext
    for d in PASTAS_LEVE:
        f = os.path.join(d, sub, nome)
        if os.path.exists(f):
            return f
    # 10/11: o pacote leva o ARQUIVO ÚNICO no lugar dos clipes soltos; o clipe "existe" se está no índice dele
    if ext == "mp4" and PASTAS_LEVE and nome in indice_unico():
        return os.path.join(PASTAS_LEVE[0], sub, nome)
    return ""


def tem_clipe(f):
    """o clipe de vídeo existe no disco ou dentro de um arquivo único (pacote sem os clipes soltos, 10/11)"""
    return bool(f) and (os.path.exists(f) or os.path.basename(f) in indice_unico())


# A ANIMAÇÃO EM IMAGEM (rumo dele 10/11 18h05: "a animação volta a ser imagem, não vídeo do slide inteiro"), PROTÓTIPO atrás
# de NATIVO_ANIM_FORMATO=B: onde o original animado tem FOLHA DE SPRITES (cache_sprites/, anim_sprites.py), o slide entra
# pelo JPEG parado + os recortes que mexem (uma textura, decodificada uma vez); nenhum MP4 abre. O slide com movimento
# volta às CAMADAS nativas (o filme por clique sai).
ANIM_IMAGEM = os.environ.get("NATIVO_ANIM_FORMATO") == "B"
# o anti-queima-roupa (11/11): no máximo 5 slides por segundo (palavra dele) e o teto da espera pelo aviso do telão
PORTAO_MIN = float(os.environ.get("NATIVO_PORTAO_MS", "200")) / 1000
PORTAO_TETO = 1.5
# nas APRESENTAÇÕES (os slides das crianças, com vídeo) o piso é 2 por segundo (palavra dele 11/11 01h10: "se 2 por segundo
# resolve, você deixa"): no Vaio, a 5/s, 3 de 9 slides eram cortados no meio do esmaecimento sem chegar a aparecer
PORTAO_MIN_APRES = float(os.environ.get("NATIVO_PORTAO_APRES_MS", "500")) / 1000
# o esmaecimento NÃO muda na metralhada (palavra dele 11/11 01h01: "um blur para cada coisa. O blur que já está
# estabelecido"): cada tipo segue com o seu (Bíblia 400, louvor e apresentação ESMAECER, clique de dentro 0) e o portão só
# dita o ritmo. NATIVO_FADE_RAPIDO=ms encurta o esmaecimento quando o clique chega com o telão trocando (só para medir)
FADE_RAPIDO = int(os.environ.get("NATIVO_FADE_RAPIDO", "0"))
# o PERDÃO do toque (11/11 11h56, palavra dele: "tem que ter um pouquinho mais de piedade"): quem toca de novo com o telão
# ainda trocando não perde o toque. Até 3 ficam guardados e saem em seguida, com o esmaecimento de 250 ms
PERDAO_TOQUES = 3
FADE_PERDAO = int(os.environ.get("NATIVO_FADE_PERDAO", "250"))
# os cultos de fábrica (CULTOS_PADRAO do app.js da 3.0.13; o mesmo do Tx.CULTOS_PADRAO do SecIgreja.qml), dia 0 = domingo
CULTOS_PADRAO = [
    {"dia": 0, "nome": "Escola Bíblica Dominical", "hora": "10:00", "on": True},
    {"dia": 0, "nome": "Culto Evangelístico", "hora": "19:00", "on": True},
    {"dia": 1, "nome": "Culto de Glorificação", "hora": "19:30", "on": False},
    {"dia": 2, "nome": "Culto de Doutrina", "hora": "19:30", "on": False},
    {"dia": 3, "nome": "Culto de Senhoras", "hora": "19:30", "on": True},
    {"dia": 4, "nome": "Culto de Oração", "hora": "19:30", "on": True},
    {"dia": 4, "nome": "Madrugada", "hora": "06:00", "on": True},
    {"dia": 5, "nome": "Culto no Lar", "hora": "19:30", "on": True},
    {"dia": 6, "nome": "Culto de Doutrina", "hora": "19:30", "on": True},
    {"dia": 6, "nome": "Madrugada", "hora": "06:00", "on": True},
]
# 10/11 (): a folha em BC7 pela textura nossa (textura_bc.py; o leitor de .ktx do Qt não desenha BC7).
# DESLIGADO por padrão: NATIVO_BC7=1 liga, e só vale onde o PySide expõe o QRhi (senão segue a folha em PNG).
TEX_BC = False
if os.environ.get("NATIVO_BC7") == "1":
    try:
        import textura_bc
        TEX_BC = True
    except Exception as _e:
        print("BC7 indisponível neste PySide:", repr(_e), flush=True)


def folha_de(caminho):
    """a folha de sprites do WebP animado `caminho` (<pasta>__<nome> ou <nome> em cache_sprites/), ou {}"""
    if not caminho:
        return {}
    base = os.path.splitext(os.path.basename(caminho))[0]
    raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_sprites")
    for nome in (os.path.basename(os.path.dirname(caminho)) + "__" + base, base):
        d = os.path.join(raiz, nome)
        if os.path.exists(os.path.join(d, "sprites.json")):
            try:
                j = json.load(open(os.path.join(d, "sprites.json"), encoding="utf-8"))
            except Exception:
                return {}
            u = lambda f: QUrl.fromLocalFile(os.path.join(d, f)).toString()
            if TEX_BC and os.path.exists(os.path.join(d, "folha.bc7.ktx")) and os.path.exists(os.path.join(d, "sprites_bc.json")):
                try:
                    jb = json.load(open(os.path.join(d, "sprites_bc.json"), encoding="utf-8"))
                    return dict(jb, fundo=u("fundo.png"), folha=u("folha.png"), folhaBC=os.path.join(d, "folha.bc7.ktx"))
                except Exception:
                    pass
            return dict(j, fundo=u("fundo.png"), folha=u("folha.png"))
    return {}


_CAUDAS = {}
def cauda_video(caminho):
    """A CAUDA (ms) do vídeo em laço: quanto do FIM do arquivo é o mesmo quadro parado em que ele começa (13/11, a emenda
    calada; apresentacoes_leves.py escreve "cauda=NNN" no comentário do .mp4, que fica no começo do arquivo). 0 = não tem
    (vídeo antigo, filme): o Palco dá a volta como antes. Lê 64 KB uma vez por arquivo."""
    c = _CAUDAS.get(caminho)
    if c is None:
        c = 0
        try:
            with open(caminho, "rb") as f:
                d = f.read(65536)
            i = d.find(b"cauda=")
            if i >= 0:
                k = 0
                while k < 5 and i + 6 + k < len(d) and 48 <= d[i + 6 + k] <= 57: k += 1
                c = min(2000, int(d[i + 6:i + 6 + k] or b"0"))
        except (OSError, ValueError):
            c = 0
        _CAUDAS[caminho] = c
    return c


def levar(a):
    """Na apresentação `a` (cerebro.apresentacoes): "mostra" (o que se desenha parado: o .jpg, ou o original) e "video"
    (o .mp4 do slide animado) por slide; no movimento, o fundo animado ganha "video" e o parado vira o .jpg."""
    a["mostra"], a["video"], a["filme"] = [], [], {}
    for k, s in enumerate(a["slides"]):
        a["video"].append("" if (ANIM_IMAGEM and folha_de(s)) else leve(s, "mp4"))
        a["mostra"].append(leve(s, FMT_PARADO) or leve(s, "jpg") or s)
        if str(k) in a["mov"] and not ANIM_IMAGEM:                 # 09/11: o slide com movimento FILMADO (um vídeo por clique, sem camadas)
            f = filme_ap(s)
            if f and len(f) == len(a["mov"][str(k)].get("passos") or [[]]):
                a["filme"][str(k)] = f
    for m in a["mov"].values():
        if "baseOrig" not in m:
            m["baseOrig"] = m["base"]
            m["video"] = "" if (ANIM_IMAGEM and folha_de(m["base"])) else leve(m["base"], "mp4")
            m["base"] = leve(m["base"], FMT_PARADO) or leve(m["base"], "jpg") or m["base"]
    return a


def leve_tela(t):
    """A tela das CIAS 16:9 (modo apres, cerebro.tela_louvor) no formato leve: o .jpg parado, o .mp4 do slide ou do fundo
    animado. Copia o movimento (o do cerebro fica em cache, intocado). E a tela 4:3 das CIAS (modo slide, só dos louvores
    sem 16:9): o .mp4/.jpg leve no lugar do WebP e do vídeo antigo de 1440x1080."""
    if t.get("modo") == "slide" and t.get("webp") and not t.get("leve"):
        v, j = leve(t["webp"], "mp4"), leve(t["webp"], "jpg")
        if v:                                    # o Palco: imgCias (parado, por baixo) lê "webp"; o vídeo lê "arquivo"
            t.update(tipo="video", arquivo=v, webp=j, leve=True)
        elif j:
            t.update(tipo="imagem", arquivo=j, webp=j, leve=True)
        return t
    if t.get("modo") != "apres" or not t.get("cias169") or "video" in t:
        return t
    f = filme_de(t.get("src", "")) if (t.get("mov") and not ANIM_IMAGEM) else None
    if f:                                        # 09/11: as camadas viraram vídeo (sem transparência, sem WebP)
        poe_filme(t, f, t.get("passo"))
        t["src"] = leve(t.get("src", ""), "jpg") or t.get("src", "")
        return t
    m = t.get("mov")
    if m:
        m = dict(m, baseOrig=m["base"], base=leve(m["base"], "jpg") or m["base"])
        t["mov"] = m
    if ANIM_IMAGEM and (folha_de((m or {}).get("baseOrig", "")) or (not m and folha_de(t.get("src", "")))):
        t["video"] = ""                          # a animação em imagem (protótipo): a folha no lugar do MP4
        if not m: t["animada"] = True; t["spr"] = t.get("src", "")
    else:
        t["video"] = leve((m or {}).get("baseOrig", ""), "mp4") or leve(t.get("src", ""), "mp4")
    t["src"] = leve(t.get("src", ""), "jpg") or t.get("src", "")
    return t


_FILMES = {}
TEMPOS = bool(os.environ.get("NATIVO_TEMPOS"))        # mede cada envio do _manda (o banco do Vaio)
# o pacote leva o 16:9 SEM o WebP (só os .json + a pasta leve): o cerebro aceita o slide que tem a versão leve (10/11)
cerebro.TEM_SLIDE = lambda p: os.path.exists(p) or bool(leve(p, "jpg") or leve(p, "mp4"))
SEM_FILME = bool(os.environ.get("NATIVO_SEM_FILME"))     # as provas do MOTOR das camadas (o filme sai dele)


def filme_de(src):
    """Os vídeos de cada clique do slide das CIAS 16:9 (ferramentas/filmar_movimento.py: <número>__filme.json na pasta
    leve/cias169): [{v: a entrada, laco: o laço ("" = fica parado no fim)}], ou None se o slide não foi filmado."""
    if not src or not PASTAS_LEVE or SEM_FILME:
        return None
    num = os.path.basename(os.path.dirname(src)); slide = os.path.splitext(os.path.basename(src))[0]
    if num not in _FILMES:
        _FILMES[num] = None
        for d in PASTAS_LEVE:
            j = os.path.join(d, "cias169", num + "__filme.json")
            if os.path.exists(j):
                try:
                    with open(j, encoding="utf-8") as fh:
                        _FILMES[num] = (os.path.dirname(j), json.load(fh))
                except (OSError, ValueError):
                    pass
                break
    if not _FILMES[num]:
        return None
    pasta, ind = _FILMES[num]
    cs = ind.get(slide)
    if not cs:
        return None
    ab = lambda x: os.path.join(pasta, x) if x and tem_clipe(os.path.join(pasta, x)) else ""
    out = [{"v": ab(c.get("mp4")), "laco": ab(c.get("laco"))} for c in cs]
    return out if all(c["v"] or c["laco"] for c in out) else None


def filme_ap(slide):
    """os vídeos por clique de um slide de APRESENTAÇÃO (<chave>.filme.json na pasta leve, filmar_movimento.py --apres)"""
    j = "" if SEM_FILME else leve(slide, "filme.json")
    if not j:
        return None
    try:
        with open(j, encoding="utf-8") as fh:
            cs = json.load(fh)
    except (OSError, ValueError):
        return None
    pasta = os.path.dirname(j)
    ab = lambda x: os.path.join(pasta, x) if x and tem_clipe(os.path.join(pasta, x)) else ""
    out = [{"v": ab(c.get("mp4")), "laco": ab(c.get("laco"))} for c in cs]
    return out if out and all(c["v"] or c["laco"] for c in out) else None


UNICO = None                                               # {nome do clipe leve: (o arquivo único, início ms, duração ms)}
# 10/11 13h10 (medido no Vaio, caso real): com o arquivo único os decodificadores abertos caíram de +42 para +0..4 no percurso,
# mas a travada quase não mudou (217/317 -> 160-198/267-311 ms) e o laço do slide animado passou a segurar ~860 ms no salto.
# Fica DESLIGADO até a causa da parada da placa ser achada: NATIVO_UNICO=1 liga (medida).
SEM_UNICO = not os.environ.get("NATIVO_UNICO")


def indice_unico():
    """O ARQUIVO ÚNICO (10/11, sim dele 12h38): os clipes de uma apresentação/louvor emendados num .mp4 só (ferramentas/
    empacotar_unico.py, pasta leve/unico). Abrir arquivo liga um decodificador da placa e isso PARA a placa ~220 ms no Vaio;
    saltar dentro do mesmo arquivo não liga nada."""
    global UNICO
    if UNICO is None:
        UNICO = {}
        for d in ([] if SEM_UNICO else PASTAS_LEVE):
            for j in glob.glob(os.path.join(d, "unico", "*.json")):
                try:
                    with open(j, encoding="utf-8") as fh:
                        ind = json.load(fh)
                except (OSError, ValueError):
                    continue
                arq = os.path.join(os.path.dirname(j), ind.get("arquivo", ""))
                if os.path.exists(arq):
                    for n, (ms, dur) in ind.get("clipes", {}).items():
                        UNICO.setdefault(n, (arq, ms, dur))
    return UNICO


def por_unico(t):
    """a tela de apresentação com vídeo passa a tocar o TRECHO dela no arquivo único: u (arquivo), uIni..uFim (o clipe),
    uLacoIni..uLacoFim (o que repete; -1 = para no fim). Sem o clipe no índice, fica como estava (o arquivo solto)."""
    if t.get("modo") != "apres" or not t.get("video"):
        return t
    ind = indice_unico()
    a = ind.get(os.path.basename(t["video"]))
    if not a:
        return t
    arq, ms, dur = a
    u = dict(u=arq, uIni=ms, uFim=ms + dur, uLacoIni=-1, uLacoFim=-1)
    if t.get("laco"):
        lc = ind.get(os.path.basename(t["laco"]))
        if not lc or lc[0] != arq:
            return t                                   # o laço fora do mesmo arquivo: fica o jeito antigo (2 tocadores)
        u.update(uLacoIni=lc[1], uLacoFim=lc[1] + lc[2])
    elif t.get("videoLaco") or not t.get("filme"):    # só o laço, ou o slide animado: o clipe inteiro repete
        u.update(uLacoIni=ms, uLacoFim=ms + dur)
    t.update(u)
    return t


PORTEIROS = []                                            # (os porteiros vivos: o Python segura as funções ligadas)


def ligar_porteiro(cam):
    """O PORTEIRO DO ARQUIVO ÚNICO (10/11): o tocador da câmera do telão entrega os quadros a uma saída escondida
    ("fonteCam"); aqui só passa para a tela ("saidaCam", e dela aos espelhos) o quadro cujo tempo cai no TRECHO do clique.
    O aviso de posição do Qt vem a cada 50-250 ms (medido): parar por ele mostraria pedaços do clipe seguinte. No fim do
    trecho: salta ao começo do laço, ou para no último quadro. Roda na linha que entrega o quadro (como os espelhos).
    Cada câmera pede o seu ao nascer (Palco.qml, Camada): o telão pode ser montado de novo e a câmera velha morre."""
    try:
        from PySide6.QtMultimedia import QVideoSink   # noqa: F401  (sem o import o PySide entrega a saída como QObject)
    except Exception:
        return
    fonte = cam.findChild(QObject, "fonteCam") if cam is not None else None
    saida = cam.findChild(QObject, "saidaCam") if cam is not None else None
    if fonte is None or saida is None:
        return
    g = {"ativo": False, "ini": 0.0, "fim": 0.0, "li": -1.0, "lf": -1.0, "saltando": False}
    def ler():
        try:
            g.update(ativo=bool(cam.property("uAtivo")), ini=float(cam.property("uIni")), fim=float(cam.property("uFim")),
                     li=float(cam.property("uLacoIni")), lf=float(cam.property("uLacoFim")), saltando=False)
        except RuntimeError:                           # a câmera já se foi
            g["ativo"] = False
    cam.uMudou.connect(ler)
    sk = saida.property("videoSink")
    def quadro(f):
        if not g["ativo"]:
            return
        try:
            ms = f.startTime() / 1000.0
            laco = g["lf"] > g["li"] >= 0
            fimj = g["lf"] if laco else g["fim"]
            if ms >= fimj - 16:                        # passou do trecho: este quadro (o do clipe seguinte) NÃO aparece
                if laco:
                    if not g["saltando"]:
                        g["saltando"] = True
                        QMetaObject.invokeMethod(cam, "saltar", Qt.QueuedConnection, Q_ARG("QVariant", g["li"]))
                else:
                    g["ativo"] = False
                    QMetaObject.invokeMethod(cam, "parar", Qt.QueuedConnection)
                return
            if ms < g["ini"] - 16:
                return
            if g["saltando"]:
                if not (g["li"] - 16 <= ms <= g["li"] + 400):
                    return                             # ainda os quadros de antes do salto
                g["saltando"] = False
            sk.setVideoFrame(f)
        except RuntimeError:
            g["ativo"] = False
    fonte.property("videoSink").videoFrameChanged.connect(quadro)
    PORTEIROS.append((ler, quadro))
    ler()


def poe_filme(t, f, k):
    """a tela `t` passa a tocar o filme `f` no clique `k` (sem as camadas): a entrada, o laço e o próximo clique"""
    k = max(0, min(len(f) - 1, int(k or 0)))
    # o "mov" FICA: a prévia do celular (a página) anima as camadas por ele; o Palco ignora o mov quando há filme
    t["filme"] = f
    t["video"] = f[k]["v"] or f[k]["laco"]
    t["laco"] = f[k]["laco"] if f[k]["v"] else ""
    t["videoLaco"] = not f[k]["v"]
    if k + 1 < len(f):
        t["proxVideo"] = f[k + 1]["v"] or f[k + 1]["laco"]
    t["animada"] = False
    return t


def ritmo_webp(caminho):
    """Os atrasos (ms) de cada quadro de um WebP animado, lidos do cabeçalho (os blocos ANMF), sem decodificar nada.
    Lista vazia = não é WebP animado."""
    try:
        with open(caminho, "rb") as f:
            b = f.read()
    except OSError:
        return []
    if b[:4] != b"RIFF" or b[8:12] != b"WEBP":
        return []
    out, i = [], 12
    while i + 8 <= len(b):
        tipo, n = b[i:i + 4], int.from_bytes(b[i + 4:i + 8], "little")
        if tipo == b"ANMF" and i + 8 + 15 <= len(b):
            out.append(int.from_bytes(b[i + 8 + 12:i + 8 + 15], "little"))
        i += 8 + n + (n & 1)
    return out


class QuadrosAnim(QQuickImageProvider):
    """Os QUADROS dos slides animados (image://anim/<largura>/<quadro>/<caminho>), 07/11/2026. O AnimatedImage do Qt
    decodifica no fio da janela: 20 ms para abrir e 8 ms por quadro, em 5-6 lugares a cada clique (telão, prévia, retorno,
    o grande, o próximo, o anterior) = +300 ms por clique (prova_retorno). Aqui cada arquivo é decodificado UMA vez, numa
    linha de fundo, já no tamanho em que aparece; o QML só troca de quadro. Memória com teto (os menos usados saem)."""
    # 08/11 21h (teste dele no PC da igreja: troca de 2-3 s e voltar também lento): o teto de 160 MB não guardava o slide no
    # ar e os vizinhos (um WebP de 1920 com 8 quadros = 66 MB); voltava e decodificava tudo de novo. Com o telão no tamanho
    # dele (1366 na igreja: 34 MB) e um tamanho por arquivo, 288 MB guardam o slide e os dois vizinhos (medido, prova_troca_rapida: 227 MB; com 200 voltava a decodificar). Eram 160: no máximo +128 MB.
    TETO = 288 * 1024 * 1024

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image, QQuickImageProvider.Flag.ForceAsynchronousImageLoading)
        self.cache, self.trava, self.decodifica = OrderedDict(), threading.Lock(), threading.Lock()
        # a largura CHEIA = a do telão (posta quando o telão acha a tela; 1920 até lá). Ninguém decodifica maior que isso,
        # e todo pedido menor sai dos quadros cheios encolhidos: UMA decodificação por arquivo (antes eram até 5 por clique:
        # telão, "No telão agora", prévia, anterior, próximo)
        self.largura_cheia = 1920
        self.decods = 0                      # quantas decodificações de arquivo (a prova conta)
        self._aquecer_ger = 0

    def aquecer(self, caminhos, espera=0.6):
        """Decodifica no fundo os quadros cheios dos slides vizinhos (o de trás e o da frente), um pouco DEPOIS do slide
        no ar ficar pronto: ao avançar ou voltar, os quadros já estão na memória. Um pedido novo cancela o anterior."""
        self._aquecer_ger += 1
        ger = self._aquecer_ger
        caminhos = [c for c in caminhos if c]
        if not caminhos:
            return
        def roda():
            time.sleep(espera)
            for c in caminhos:
                if ger != self._aquecer_ger:
                    return
                try:
                    if len(ritmo_webp(c)) > 1:
                        self._quadros(c, 0)
                except Exception:
                    pass
        threading.Thread(target=roda, name="aquecer-anim", daemon=True).start()

    def _quadros(self, p, w):
        cheia = self.largura_cheia
        if w <= 0 or w >= cheia * 0.9:           # o telão, e o "No telão agora" (1280 de 1366): os quadros cheios
            w = 0
        if w > 0:                                # menor: SEMPRE dos cheios, encolhidos (uma decodificação por arquivo)
            k = (p, w)
            with self.trava:
                if k in self.cache:
                    self.cache.move_to_end(k); return self.cache[k]
            cheio = self._quadros(p, 0)
            if not cheio or cheio[0].width() <= w:
                return cheio
            h = max(1, round(cheio[0].height() * w / cheio[0].width()))
            qs = [q.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation) for q in cheio]
            with self.trava:
                self.cache[k] = qs
            return qs
        return self._cheios(p, cheia)

    def _cheios(self, p, cheia):
        """Os quadros no tamanho do telão (no máximo `cheia` de largura), decodificados uma vez."""
        k = (p, 0)
        with self.trava:
            if k in self.cache:
                self.cache.move_to_end(k); return self.cache[k]
        with self.decodifica:                       # um de cada vez (e quem esperou acha pronto)
            with self.trava:
                if k in self.cache:
                    return self.cache[k]
            r = QImageReader(p)
            tam = r.size()
            if tam.width() > cheia:
                r.setScaledSize(QSize(cheia, max(1, round(tam.height() * cheia / tam.width()))))
            qs = []
            while True:
                im = r.read()
                if im.isNull(): break
                qs.append(im)
            self.decods += 1
            with self.trava:
                self.cache[k] = qs
                total = sum(q.sizeInBytes() for v in self.cache.values() for q in v)
                while total > self.TETO and len(self.cache) > 1:
                    _, saiu = self.cache.popitem(last=False)
                    total -= sum(q.sizeInBytes() for q in saiu)
            return qs

    def requestImage(self, id_, size, pedido):
        w, q, cam = id_.split("/", 2)
        cam = unquote(cam)
        if cam.startswith("file:"):
            cam = QUrl(cam).toLocalFile()
        qs = self._quadros(cam, int(w))
        im = qs[int(q) % len(qs)] if qs else QImage(1, 1, QImage.Format_ARGB32)
        try: size.setWidth(im.width()); size.setHeight(im.height())
        except Exception: pass
        return im


def preparar_motor(eng, ctl):
    """O que o QML do painel espera achar no motor: os fornecedores de imagem e as propriedades. O Sistema e as PROVAS
    chamam isto (antes cada prova montava o seu e esquecia peças: a prova_retorno media sem os quadros animados)."""
    ctx = eng.rootContext()
    if TEX_BC:
        textura_bc.registrar()
    ctx.setContextProperty("temTexBC", TEX_BC)
    # a forma B (folha de sprites) AQUI, não no main: os bancos e as provas mediam sem a folha desenhada (achado 10/11 23h25)
    ctx.setContextProperty("animFormatoB", ANIM_IMAGEM)
    # as imagens da apresentação (o slide no ar e os vizinhos já abertos); NATIVO_SEM_DEPOSITO=1 = o arquivo direto (provas)
    com_dep = os.environ.get("NATIVO_SEM_DEPOSITO") != "1"
    if com_dep:
        deposito = DepositoApres()
        eng.addImageProvider("apres", deposito)
        ctl.deposito = deposito
    ctx.setContextProperty("temImagensApres", com_dep)
    # 10/11: o JPEG até o clique firmar só EMPURRA a abertura do vídeo para 350 ms depois (medido: a placa para igual);
    # desligado por padrão, e a pré-abertura do próximo vídeo volta. NATIVO_JPG_FIRMAR=1 liga (medida).
    ctx.setContextProperty("jpgAteFirmar", bool(os.environ.get("NATIVO_JPG_FIRMAR")))
    # 11/11: nenhum vídeo anda durante o esmaecimento (Palco.paraNaTroca); NATIVO_VIDEO_NA_TROCA=1 volta ao de antes (medida)
    ctx.setContextProperty("videoParadoNaTroca", not os.environ.get("NATIVO_VIDEO_NA_TROCA"))
    ctx.setContextProperty("preAbreVideo", not os.environ.get("NATIVO_JPG_FIRMAR"))
    ctx.setContextProperty("spriteEspelhos", os.environ.get("NATIVO_SPRITE_ESPELHOS", "1") != "0")   # a folha também nas saídas do operador (medida)
    ctx.setContextProperty("depuraCauda", bool(os.environ.get("NATIVO_DEPURA_CAUDA")))
    ctx.setContextProperty("lacoJeito", os.environ.get("NATIVO_LACO", ""))     # o jeito de repetir o vídeo (Palco.lacoModo)
    quadros = QuadrosAnim()
    eng.addImageProvider("anim", quadros)            # os quadros dos slides animados, decodificados no fundo
    ctl.quadros = quadros
    ctx.setContextProperty("semSombra", os.environ.get("NATIVO_SOMBRA") == "0")
    ctx.setContextProperty("fonteMono", fonte_mono())
    # as boas-vindas abrem sozinhas na 1ª vez (o abrirBemVindo da 3.0.13); nunca nos testes nem nas fotos
    ctx.setContextProperty("primeiraVez", not ctl.A.config.ler("icm_bemvindo_ok", False)
                           and not os.environ.get("NATIVO_SO_LOCAL") and not FOTOS)


def qr_png(texto):
    """O QR do endereço do celular como PNG em data: URL. Igual ao qr_base64 da 3.0.13: a matriz do qrcode e o PNG em
    tons de cinza escrito à mão (cabeçalho + zlib + CRC), sem Pillow; 7 px por quadradinho e borda de 2."""
    try:
        import base64, struct, zlib
        import qrcode
        lado = 7
        q = qrcode.QRCode(box_size=1, border=2)
        q.add_data(texto); q.make(fit=True)
        m = q.get_matrix()
        larg = len(m) * lado
        cru = b""
        for linha in m:
            px = bytes(0 if c else 255 for c in linha for _ in range(lado))
            cru += (b"\x00" + px) * lado
        def bloco(tipo, dados):
            return (struct.pack(">I", len(dados)) + tipo + dados
                    + struct.pack(">I", zlib.crc32(tipo + dados) & 0xffffffff))
        png = (b"\x89PNG\r\n\x1a\n"
               + bloco(b"IHDR", struct.pack(">IIBBBBB", larg, larg, 8, 0, 0, 0, 0))
               + bloco(b"IDAT", zlib.compress(cru, 9))
               + bloco(b"IEND", b""))
        return "data:image/png;base64," + base64.b64encode(png).decode()
    except Exception:
        return ""


def focar_campo(painel, nome):
    """Testes: o foco no campo de digitação de um Entrada (como quem acabou de digitar). O campo é procurado pela árvore
    VISUAL: item.property("campo") não converte para o Python (QQuickTextInput*). O telão nasce depois e pega o teclado:
    a janela do painel é ativada antes."""
    painel.requestActivate()
    pilha = [painel.findChild(QQuickItem, nome)]
    while pilha:
        it = pilha.pop()
        if it is None: continue
        if it.metaObject().className().startswith("QQuickTextInput"):
            QMetaObject.invokeMethod(it, "forceActiveFocus"); return True
        pilha.extend(it.childItems())
    return False


def gravar_historico(registros):
    """O gravar_historico do sistema.py da 3.0.13 (o mesmo historico.json, na pasta do usuário, por troca atômica).
    TESTES (NATIVO_SO_LOCAL): nunca no histórico de verdade da igreja; só no arquivo que a prova der (SISTEMA_HISTORICO)."""
    if os.environ.get("NATIVO_SO_LOCAL") and not os.environ.get("SISTEMA_HISTORICO"):
        return
    try:
        sys.path.insert(0, cerebro.APP) if cerebro.APP not in sys.path else None
        import sistema as S
        S.gravar_historico(registros)
    except Exception as e:
        print("não gravei o histórico:", e, flush=True)


def tempo_curto(seg):
    """O tempoCurto da 3.0.13: 45s · 12 min · 1h05."""
    if seg < 60:
        return "%ds" % seg
    m = int(seg / 60 + 0.5)
    return "%d min" % m if m < 60 else "%dh%02d" % (m // 60, m % 60)


MESES_CURTOS = ["jan.", "fev.", "mar.", "abr.", "mai.", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]
DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]   # weekday() do Python: 0 = segunda


def painel_culto(registros, dias, agora=None):
    """O pintarPainel + pintarVersiculos da 3.0.13 (Configurações › Painel), linha por linha: o resumo, os mais cantados,
    o mais tempo no telão, os versículos, os livros e os últimos cultos. dias = 0 é "Tudo"."""
    import datetime as _dt
    agora = time.time() if agora is None else agora
    corte = agora - dias * 86400 if dias else 0
    periodo = [x for x in registros if (x.get("ini") or 0) >= corte]
    regs = [x for x in periodo if x.get("q") == "louvor"]
    vers = [x for x in periodo if x.get("q") == "verso"]

    def linhas(itens, texto, peso):
        mx = max([peso(v) for _, v in itens] + [1])
        return [{"nome": k, "vl": texto(v), "peso": peso(v) / mx} for k, v in itens]

    def ordenar(d, chave):                 # o sort do JS é estável: empate fica na ordem em que entrou
        return sorted(d.items(), key=chave)

    out = {"resumo": [], "mais": [], "tempo": [], "cultos": [], "vers": [], "livros": []}
    # a Palavra
    if vers:
        por_ref, por_livro = {}, {}
        for x in vers:
            ref = re.sub(r"\s*\(\+\d+\)$", "", x.get("rot") or "")
            r = por_ref.setdefault(ref, {"n": 0, "seg": 0}); r["n"] += 1; r["seg"] += x.get("seg") or 0
            livro = re.sub(r"\s+\d+:\d+.*$", "", ref) or ref
            l = por_livro.setdefault(livro, {"n": 0, "seg": 0}); l["n"] += 1; l["seg"] += x.get("seg") or 0
        out["vers"] = linhas(ordenar(por_ref, lambda kv: (-kv[1]["n"], -kv[1]["seg"]))[:10],
                             lambda v: "%d %s · %s" % (v["n"], "vez" if v["n"] == 1 else "vezes", tempo_curto(v["seg"])), lambda v: v["n"])
        out["livros"] = linhas(ordenar(por_livro, lambda kv: -kv[1]["n"])[:10],
                               lambda v: "%d %s" % (v["n"], "versículo" if v["n"] == 1 else "versículos"), lambda v: v["n"])
    if not regs:
        out["resumo"] = [[str(len(vers)), "versículos projetados"]] if vers else []
        return out
    dia = lambda ts: _dt.datetime.fromtimestamp(ts).date()
    dias_set = {dia(x["ini"]) for x in periodo}
    seg_total = sum(x.get("seg") or 0 for x in regs)
    out["resumo"] = ([[str(len(regs)), "louvores projetados"]] + ([[str(len(vers)), "versículos projetados"]] if vers else [])
                     + [[str(len(dias_set)), "culto" if len(dias_set) == 1 else "cultos"], [tempo_curto(seg_total), "no telão"]])
    por = {}
    for x in regs:
        k = x.get("rot") or x.get("chave")
        r = por.setdefault(k, {"n": 0, "seg": 0}); r["n"] += 1; r["seg"] += x.get("seg") or 0
    out["mais"] = linhas(ordenar(por, lambda kv: -kv[1]["n"])[:10],
                         lambda v: "%d %s" % (v["n"], "vez" if v["n"] == 1 else "vezes"), lambda v: v["n"])
    out["tempo"] = linhas(ordenar(por, lambda kv: -kv[1]["seg"])[:10], lambda v: tempo_curto(v["seg"]), lambda v: v["seg"])
    por_dia = {}
    for x in regs:
        k = dia(x["ini"])
        d = por_dia.setdefault(k, {"n": 0, "seg": 0, "ts": x["ini"]}); d["n"] += 1; d["seg"] += x.get("seg") or 0
        d["ts"] = min(d["ts"], x["ini"])
    cultos = sorted(por_dia.items(), key=lambda kv: -kv[1]["ts"])[:10]
    mx = max([v["n"] for _, v in cultos] + [1])
    for _, v in cultos:
        d = _dt.datetime.fromtimestamp(v["ts"])
        nome = "%02d de %s de %02d · %s" % (d.day, MESES_CURTOS[d.month - 1], d.year % 100, DIAS_SEMANA[d.weekday()])
        out["cultos"].append({"nome": nome, "vl": "%d louvores · %s" % (v["n"], tempo_curto(v["seg"])), "peso": v["n"] / mx})
    return out


def _md5(p):
    import hashlib
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# o que o operador criou (o restaurar_tudo da 3.0.13 + os arquivos próprios do nativo)
ALVOS_RESTAURAR = ["configuracoes.json", "historico.json", "Meus louvores", "Meus fundos", "Minhas apresentações",
                   "slides_importados", "nativo.json", "nativo_fundos"]


def restaurar_tudo_com_copia(pasta, agora=None):
    """O "Restaurar tudo" (decisão da HD 07/11: o da 3.0.13, SEMPRE com cópia de segurança antes). 1) copia cada alvo para
    <pasta>/Cópia de segurança/Restaurar AAAA-MM-DD HHhMM; 2) confere o md5 de CADA arquivo copiado; 3) só então apaga o
    original. Se uma cópia não confere, NADA é apagado. Devolve (pasta da cópia, [apagados]) ou levanta erro."""
    import shutil
    agora = agora or time.localtime()
    destino = os.path.join(pasta, "Cópia de segurança", time.strftime("Restaurar %Y-%m-%d %Hh%M", agora))
    n = 2
    while os.path.exists(destino):
        destino = destino.rstrip("0123456789 ()") + " (%d)" % n; n += 1
    os.makedirs(destino)
    feitos = []
    for nome in ALVOS_RESTAURAR:
        o = os.path.join(pasta, nome)
        if not os.path.exists(o):
            continue
        d = os.path.join(destino, nome)
        if os.path.isdir(o):
            shutil.copytree(o, d)
            pares = [(os.path.join(r, f), os.path.join(d, os.path.relpath(os.path.join(r, f), o))) for r, _, fs in os.walk(o) for f in fs]
        else:
            shutil.copy2(o, d)
            pares = [(o, d)]
        for a, b in pares:
            if _md5(a) != _md5(b):
                raise RuntimeError("a cópia de %s não conferiu (md5): nada foi apagado" % a)
        feitos.append(o)
    for o in feitos:                     # só depois de TODAS as cópias conferidas
        if os.path.isdir(o): shutil.rmtree(o)
        else: os.remove(o)
    return destino, [os.path.basename(o) for o in feitos]


def janela_312(tela):
    """O tamanho e o lugar da janela do operador ao abrir, os da 3.0.x (sistema.py:4699, create_window): 82% da largura
    (980 a 1180) por 84% da altura (620 a 760) da tela inteira, no meio. Ordem dele 08/11 08h20: "o sistema dá a entender
    que te respeita, não forra sua tela até você clicar no quadradinho". No Vaio (1366x768): 1120x645, 61 px de respiro em
    cima. Antes: 1280 x (altura útil - 30), que o Cinnamon maximizava. Em tela menor que o mínimo, cabe na área útil."""
    g, u = tela.geometry(), tela.availableGeometry()
    w = max(980, min(1180, int(g.width() * 0.82)))
    h = max(620, min(760, int(g.height() * 0.84)))
    w, h = min(w, u.width()), min(h, u.height())
    x, y = g.x() + (g.width() - w) // 2, g.y() + (g.height() - h) // 2
    x = max(u.x(), min(x, u.x() + u.width() - w)); y = max(u.y(), min(y, u.y() + u.height() - h))
    return x, y, w, h


def moldura_312(janela, x, y, w, h):
    """A 3.0.x (pywebview) põe a janela INTEIRA, com a barra de título e a borda, no retângulo; o Qt põe só o conteúdo.
    Medido 08/11 (prova_janela_abrir): sem isto a borda de cima ficava a 30 px do topo, não aos 61 da 3.0.x. A moldura só
    é conhecida com a janela já à vista: desconta e reposiciona."""
    m = janela.frameMargins()
    if m.left() or m.top() or m.right() or m.bottom():
        janela.setGeometry(x + m.left(), y + m.top(), max(200, w - m.left() - m.right()), max(200, h - m.top() - m.bottom()))


def _tela_interna(nome):
    """A tela do próprio notebook (Linux: LVDS, eDP, DSI). No Windows o nome não diz, e aí nenhuma é 'interna'."""
    return str(nome or "").upper().startswith(("LVDS", "EDP", "DSI"))


def _tampa_fechada():
    """Linux: a tampa do notebook está fechada (/proc/acpi/button/lid/*/state). Testes: NATIVO_TAMPA=fechada|aberta."""
    t = os.environ.get("NATIVO_TAMPA")
    if t: return t == "fechada"
    try:
        import glob
        for f in glob.glob("/proc/acpi/button/lid/*/state"):
            if "closed" in open(f).read(): return True
    except Exception:
        pass
    return False


def _por_na_frente(janela):
    """Põe a janela por cima das outras SEM ativar (o foco fica no painel do operador). No Windows o raise() de quem não
    está em primeiro plano não passa por cima de outro programa: o "sempre por cima" ligado e desligado sem ativar
    (SWP_NOACTIVATE) põe a janela no topo e devolve o normal. No Linux o raise() basta."""
    janela.raise_()
    # o show() do Qt só mostra de verdade na volta do laço de eventos: chamado logo depois dele, o SetWindowPos caía
    # numa janela ainda escondida e o telão aparecia ATRÁS do outro programa (medido 08/11 na prova). Repete depois.
    if not getattr(janela, "_na_frente_de_novo", False):
        janela._na_frente_de_novo = True
        def de_novo():
            janela._na_frente_de_novo = False; _por_na_frente_ja(janela)
        QTimer.singleShot(0, lambda: _por_na_frente_ja(janela)); QTimer.singleShot(150, de_novo)
    _por_na_frente_ja(janela)


def _por_na_frente_ja(janela):
    if os.name == "nt":
        try:
            import ctypes, ctypes.wintypes as W
            swp = ctypes.windll.user32.SetWindowPos
            # os TIPOS declarados: sem eles o -1 (HWND_TOPMOST) ia como inteiro de 32 bits e o Windows de 64 lia
            # 0x00000000FFFFFFFF -> "handle inválido" (erro 1400, medido 08/11) e o telão ficava atrás
            swp.argtypes = [W.HWND, W.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            swp.restype = W.BOOL
            h, f = W.HWND(int(janela.winId())), 0x0001 | 0x0002 | 0x0010   # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
            ok1 = swp(h, W.HWND(-1), 0, 0, 0, 0, f)                        # HWND_TOPMOST
            ok2 = swp(h, W.HWND(-2), 0, 0, 0, 0, f)                        # HWND_NOTOPMOST
            if not (ok1 and ok2): print("pôr o telão na frente: SetWindowPos falhou", ctypes.GetLastError(), flush=True)
        except Exception as e:
            print("pôr o telão na frente:", e, flush=True)


def memoria_mb():
    """A memória deste processo agora, em MB (RSS no Linux; working set no Windows). 12/11: para a faxina e as provas."""
    try:
        with open("/proc/self/status") as f:
            for l in f:
                if l.startswith("VmRSS"):
                    return int(l.split()[1]) / 1024
    except OSError:
        pass
    try:
        import ctypes, ctypes.wintypes as w
        class _P(ctypes.Structure):
            _fields_ = [("cb", w.DWORD), ("f", w.DWORD), ("pico", ctypes.c_size_t), ("ws", ctypes.c_size_t)] + \
                       [("x%d" % i, ctypes.c_size_t) for i in range(6)]
        p = _P(); p.cb = ctypes.sizeof(_P); k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = ctypes.c_void_p
        k.K32GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, w.DWORD]
        k.K32GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(p), p.cb)
        return p.ws / 2**20
    except Exception:
        return 0.0


def vigia_da_placa(controle):
    """O VERDE DO VAIO (11/11/2026): quando a placa recusa um quadro de vídeo, o Mesa escreve "kernel rejected CS" na saída
    de erro do processo, e mais nada avisa o programa. Aqui a saída de erro passa por um cano: tudo segue para onde ia (o
    nativo.log), e cada recusa vira o sinal placaRecusou, que o Palco usa para estacionar o tocador ruim. Só no Linux."""
    if os.name == "nt" or os.environ.get("NATIVO_SEM_VIGIA_PLACA") or getattr(vigia_da_placa, "ligado", False):
        return
    try:
        le, escreve = os.pipe(); real = os.dup(2); os.dup2(escreve, 2); os.close(escreve)
    except OSError:
        return
    vigia_da_placa.ligado = True
    def anda():
        while True:
            try:
                d = os.read(le, 8192)
            except OSError:
                break
            if not d:
                break
            try: os.write(real, d)
            except OSError: pass
            n = d.count(b"rejected CS")
            if n:
                controle.recusas_da_placa += n
                try: controle.placaRecusou.emit(n)
                except RuntimeError: break
    threading.Thread(target=anda, daemon=True, name="vigia-da-placa").start()


class Controle(QObject):
    """O estado do que está no ar e as ordens (o painel, o teclado e, depois, o celular chamam isto)."""
    tela = Signal("QVariant")          # a tela nova para o telão e a prévia
    escolhido = Signal(int)
    previa = Signal("QVariant")        # congelado: só a prévia do painel muda            # o celular abriu um louvor (o painel mostra as telas dele)
    mudou = Signal()                   # o painel redesenha o "no ar"
    esperaMudou = Signal()             # a galeria redesenha a estrela da espera
    filaMudou = Signal()               # a lista do culto mudou (o painel redesenha)
    trocaComecou = Signal()            # o telão começou uma troca (as prévias do painel esmaecem junto, 11/11)
    trocaTerminou = Signal()           # o telão terminou uma troca (o painel devolve o espelho do vídeo, 11/11)
    placaRecusou = Signal(int)         # a placa recusou quadro(s) de vídeo: o Palco estaciona o tocador (o verde do Vaio, 11/11)
    aviso = Signal(str)                # recado curto para o operador ("esse louvor já está na lista")
    apresMudou = Signal()              # entrou/saiu/importou apresentação (a aba redesenha)
    acervoMudou = Signal()             # os louvores do operador mudaram (a lista da aba Louvor se refaz)
    sugMudou = Signal()                # as sugestões de louvor do versículo no ar (a faixa da aba Bíblia)
    atualizacao = Signal(str)          # o resultado do "Verificar" (Configurações › Sistema › Atualizar)
    atuNova = Signal(str, str, int)    # existe versão mais nova (nova, atual, MB do instalador): o "Confirmar" da 3.0.13
    atuMelhor = Signal(bool)           # a linha dourada: "a melhor versão do Sistema: completa e atualizada"
    sairParaAtualizar = Signal()       # o instalador subiu: o Sistema fecha (a 3.0.13 fazia os._exit 3 s depois)
    retornoMudou = Signal()            # a TV de retorno (gestos) redesenha
    importou = Signal("QVariant")      # a conversão do PowerPoint terminou (vem de outra linha: o Qt entrega na principal)
    telasMudou = Signal()              # o telão mudou de lugar (projetor chegou/saiu, ensaio) ou o cartão abriu/fechou
    identificar = Signal(int, str)     # o número gigante no telão (o "Identificar" do Windows): 1 Telão / 2 Tela de retorno

    def __init__(self, acervo, biblia=None):
        super().__init__()
        self.A = acervo
        self.B = biblia
        self.rede = None
        self.url_celular = ""
        self.escala = {"louvor": 1.0, "biblia": 1.0}   # A+/A-: cada um guarda o seu (o app.js faz assim)
        self.congelado = False                         # congelar: o telão fica parado; o painel continua andando
        self.vivo = ""                     # o que está no ar: "louvor", "biblia" ou "" (espera/preta)
        self.bib = None                    # (livro, cap, v) da Bíblia no ar
        self.estilo = "limpo"
        # o est.modoAnim da 3.0.13: a escolha guardada (icm_anim_auto; de fábrica, ligada). Antes o nativo começava sempre
        # ligado e ignorava o que o operador tinha escolhido em Configurações › Sistema (achado 07/11)
        self.anim_ligada = self.A.config.ler("icm_anim_auto", True) is not False
        self.idx, self.slide = -1, 0
        self._no_ar = "tela de espera"
        self._fundo_no_ar = ""
        self.ultimo = acervo.tela_descanso()
        # a LISTA DO CULTO (a "Lista de Projeção" do app.js): fica na memória, como na 3.0.12 (não vai para o disco)
        self.fila = []                     # {"tipo": "louvor", "chave", "rotulo"} ou {"tipo": "verso", "livro", "cap", "v", "ref"}
        self.pos = -1                      # o item da lista que está no ar (-1 = fora da lista)
        self.cont_depois = 0               # passos de leitura contínua DEPOIS do último versículo da lista
        self.cont_antes = 0                # passos de leitura para trás ANTES do primeiro
        self.aguardando = False            # o louvor acabou e caiu na espera: o próximo "Próxima" abre o seguinte
        # APRESENTAÇÃO no ar (o SLIDES do app.js): a lista vem do servidor da 3.0.12 na 1a vez que a aba abre
        self._aps = None
        self.ap = None                     # a apresentação aberta (dict de cerebro.apresentacoes)
        self.ap_pos, self.ap_passo = -1, 0
        self.recusas_da_placa = 0
        vigia_da_placa(self)
        # ANTI-QUEIMA-ROUPA (protocolo dele 11/11): o portão do avançar/voltar da apresentação (ver _portao)
        self._pt_ocupado = False; self._pt_quer = 0; self._pt_ult = 0.0; self._pt_rapido = 0; self._pt_esperou = False; self._pt_rep = False; self._pt_perdao = False
        self._pt_telao = False          # vira True no 1º aviso do telão: só então o portão segura
        self._pt_mandas = 0; self._pt_n = 0; self._pt_t_quer = 0.0; self._pt_prontos = 0
        self._pt_relogio = QTimer(self); self._pt_relogio.setSingleShot(True); self._pt_relogio.timeout.connect(self._pt_tenta)
        self._pt_teto = QTimer(self); self._pt_teto.setSingleShot(True); self._pt_teto.setInterval(int(PORTAO_TETO * 1000))
        self._pt_teto.timeout.connect(self.telaoPronto)
        self.ap_vista = False              # aberta na aba (as miniaturas); fechar a vista não tira do ar
        self.importou.connect(self._importou)
        self.cif = cerebro.Cifras()        # a CIFRA: só o índice do acordes.json fica na memória (0,7 MB)
        self.cif_tela = None               # a cifra no telão: {"pags", "p", "titulo"}
        # ONDE ESTÁ O TELÃO (peça "escolher a tela", 07/11/2026): ver posicionar()
        self._telao = self._retjan = self._painel = None
        # "Fechar telão" pelo celular (fecharprojecao da 3.0.x): a janela some e o posicionar NÃO a reabre sozinho; o
        # "Abrir telão" desfaz (08/11, relato dele no culto: o celular abriu o telão por cima do Glorifica)
        self.telao_fechado = False
        self.deposito = None               # o depósito das imagens da apresentação (DepositoApres), posto pelo main
        self.quadros = None                # os quadros dos slides animados (QuadrosAnim), posto pelo preparar_motor
        self._forcar_janela = False        # testes (--janela) e fotos: o telão sempre em janela
        self.sem_projetor = False          # uma tela só: o telão fica ESCONDIDO (nunca na cara do operador)
        self.ensaio = False                # o operador escolheu "Continuar assim": o telão numa janela nesta tela
        self.aviso_proj = False            # o cartão "Projetor não encontrado" está aberto no painel
        self._aviso_ja = False             # já apareceu nesta falta de projetor (não insiste a cada tela)
        self.seguindo = False              # 13/11: este computador é a TELA SECUNDÁRIA de outro Sistema (seguir.py)
        self.seguindo_texto = ""           # o recado na tela secundária ("Procurando o computador principal…")
        self.outro_principal = {}          # ao abrir: outro Sistema já está nesta rede ({"nome", "base"}): o cartão pergunta
        self._onde = "—"
        # DUAS TELAS PELA REDE (o Vaio como TV de retorno): ver _vigiar_telas()
        self.dt_lista = []                 # os aparelhos que se apresentaram (apoios_lista do servidor da 3.0.12)
        self._procurando_telas = False     # o botão das duas telas da barra (procurarTelas): um de cada vez
        self.dt_modo, self.dt_chave, self.dt_a = "", "", {}   # o cartão aberto: "pergunta" | "como"
        self.dt_visto = {}                 # a pergunta já apareceu para este aparelho (não insiste)
        self.telao_apoio = False           # depois do Trocar: o HDMI daqui mostra a TV de retorno (o outro é o telão)
        self._dt_fim = QTimer(self); self._dt_fim.setSingleShot(True); self._dt_fim.setInterval(20000)
        self._dt_fim.timeout.connect(lambda: self._dt_fechar())
        # A FAXINA AUTOMÁTICA (ordem dele 12/11: "o sistema tem que estar SEMPRE LIMPANDO AUTOMATICAMENTE (...) o cache é o
        # elemento de risco do sistema inteiro explodir"): ver _faxina. Na abertura e a cada 2 min, só com o telão parado.
        self._ultima_tela = 0.0
        self.faxina_info = {"vezes": 0, "devolvido_mb": 0.0, "ultima": ""}
        self._faxina_t = QTimer(self); self._faxina_t.setInterval(int(float(os.environ.get("NATIVO_FAXINA_S", "120")) * 1000))
        self._faxina_t.timeout.connect(self._faxina); self._faxina_t.start()
        QTimer.singleShot(15000, self._faxina)

    def _faxina(self, forcar=False):
        """A FAXINA (12/11/2026), sem o operador fazer nada e sem travar a troca: (1) espera o telão ficar parado 5 s (se
        trocou agora, tenta na próxima volta); (2) Linux: devolve ao sistema a memória que o programa já soltou e o glibc
        segurava (malloc_trim; medido 12/11: 55-85 MB por chamada no Vaio); (3) apaga as pastas temporárias do Sistema com
        mais de 1 dia; (4) anota memória antes/depois (nativo.log e faxina_info, para as provas). Os caches de imagem já
        têm teto próprio (QuadrosAnim 288 MB; DepositoApres = o slide no ar e os vizinhos); o tocador recusado se solta no
        Palco (30 s); o nativo.log tem teto no lançador do Linux."""
        if not forcar and time.time() - self._ultima_tela < 5:
            # 12/11 (prova no Vaio: 1 faxina em 6 min): o relógio quase nunca caía numa pausa. Agora espera a PRÓXIMA
            # pausa: confere de 2 em 2 s (barato) e roda quando o telão ficar 5 s parado.
            if not getattr(self, "_faxina_espera", False):
                self._faxina_espera = True
                QTimer.singleShot(2000, self._faxina_de_novo)
            return
        try:
            antes = memoria_mb()
            if os.name != "nt":
                import ctypes
                ctypes.CDLL("libc.so.6").malloc_trim(0)
            tmp = tempfile.gettempdir()
            for d in glob.glob(os.path.join(tmp, "nativo_*")) + glob.glob(os.path.join(tmp, "prova_*")):
                try:
                    if os.path.isdir(d) and time.time() - os.path.getmtime(d) > 86400:
                        import shutil; shutil.rmtree(d, ignore_errors=True)
                except OSError:
                    pass
            depois = memoria_mb()
            fi = self.faxina_info
            fi["vezes"] += 1; fi["devolvido_mb"] += max(0.0, antes - depois)
            fi["ultima"] = "%s %.0f -> %.0f MB" % (time.strftime("%H:%M:%S"), antes, depois)
            print("faxina %d: memória %.0f -> %.0f MB (devolvido no total %.0f MB)" % (fi["vezes"], antes, depois, fi["devolvido_mb"]), flush=True)
        except Exception as e:
            print("faxina:", e, flush=True)

    def _faxina_de_novo(self):
        self._faxina_espera = False
        self._faxina()

    # ---- o HISTÓRICO do que foi ao telão (o abrirNoAr/fecharNoAr/enviarHistorico do app.js da 3.0.13), 07/11/2026:
    # o Painel do culto lê daqui. Louvor e versículo abrem o cronômetro; o mesmo item em outra tela não reabre; a tela de
    # espera (ou outro louvor/versículo) fecha; menos de 5 s foi engano de clique e não conta; telão desligado não é culto.
    # Grava no MESMO historico.json da 3.0.13 (a função gravar_historico dela: troca atômica), numa linha de fundo.
    MIN_SEG = 5

    def abrir_no_ar(self, q, rot, ch):
        cr = getattr(self, "_cron", None)
        if cr and cr["chave"] == ch:
            return
        self.fechar_no_ar()
        if self.semProjetor or self.seguindo:    # a tela secundária não escreve histórico (quem escreve é o principal)
            return
        self._cron = {"q": q, "rot": rot, "chave": ch, "ini": time.time()}

    def fechar_no_ar(self, esperar=False):
        cr = getattr(self, "_cron", None)
        if not cr:
            return
        self._cron = None
        seg = round(time.time() - cr["ini"])
        if seg >= self.MIN_SEG:
            reg = {"q": cr["q"], "rot": cr["rot"], "chave": cr["chave"], "ini": round(cr["ini"]), "seg": seg}
            th = threading.Thread(target=gravar_historico, args=([reg],), name="historico", daemon=not esperar)
            th.start()
            if esperar: th.join(5)

    def _manda(self, t):
        self._ultima_tela = time.time()    # a faxina espera o telão parado (12/11)
        self._pt_mandas += 1               # anti-queima-roupa: o portão sabe que saiu tela nova para o telão
        if self._pt_rapido:                # o toque que esperou (o "perdão") sai com o esmaecimento mais curto
            t["fade"] = min(t.get("fade", 700), self._pt_rapido)
        self.aguardando = False            # qualquer projeção nova cancela o "aguardando" (o fim do louvor religa)
        leve_tela(t)                       # as CIAS 16:9 no formato leve (.jpg/.mp4), quando já convertidas (09/11)
        por_unico(t)                       # 10/11: o trecho no arquivo único (o telão salta; não abre arquivo)
        t["estilo"] = self.estilo          # toda tela leva o estilo (app.js projetar: st.estilo = est.estilo); o Palco mede por ele
        self.ultimo = t
        if self.sem_projetor and not self.ensaio and not self._aviso_ja:
            # projetou sem projetor: o cartão da 3.0.12 (o "Projetar" com uma tela só), uma vez por falta de projetor
            self._aviso_ja = True; self.aviso_proj = True; self.telasMudou.emit()
        if self.congelado:
            self.previa.emit(t); self.mudou.emit(); return
        if TEMPOS:
            c0 = time.perf_counter(); self.tela.emit(t); c1 = time.perf_counter(); self.mudou.emit(); c2 = time.perf_counter()
            self.retornoMudou.emit(); c3 = time.perf_counter()
        else:
            self.tela.emit(t)
            self.mudou.emit()
            self.retornoMudou.emit()
        if self.rede:
            try:
                self.rede.publicar_tela(t)
                # 13/11: o estado sai NA HORA (antes só de segundo em segundo): a tela secundária acompanha sem atraso
                self.rede.publicar_estado(self.estado())
            except Exception as e: print("prévia do celular:", e)
        if TEMPOS:
            print("TEMPOS _manda %s: tela %.0f · mudou %.0f · retorno %.0f · celular %.0f ms" % (
                t.get("modo"), (c1 - c0) * 1000, (c2 - c1) * 1000, (c3 - c2) * 1000, (time.perf_counter() - c3) * 1000), flush=True)

    # ---- o CELULAR (controle.html, o mesmo da 3.0.12): as ordens chegam pela fila do servidor
    def executar(self, c):
        cmd = c.get("cmd")
        if cmd == "slide" and 0 <= int(c.get("idx", -1)) < len(self.A.louvores):
            self.projetar(int(c["idx"]), int(c.get("slide", 0)))
        elif cmd == "louvor" and 0 <= int(c.get("idx", -1)) < len(self.A.louvores):
            # o case 'louvor' da 3.0.12/3.0.13 é selecionarLouvor(idx): ESCOLHE e PROJETA o 1º slide. Aqui só escolhia:
            # tocar no louvor pelo celular não punha nada no ar, e o "Avançar" seguinte não tinha o que avançar (B10,
            # relato dele 07/11 21h16: "ele espera que você clique no louvor para projetar, isso que é um absurdo")
            self.escolhido.emit(int(c["idx"]))
            self.projetar(int(c["idx"]), 0)
        elif cmd == "verso" and self.B:
            try: self._verso_solto(c["livro"], int(c["cap"]), int(c["v"]))
            except Exception as e: print("verso do celular:", c, e)
        elif cmd == "guardar" and self.B:          # toque longo no versículo: guarda na lista, sem projetar
            try: self.addVerso(c["livro"], int(c["cap"]), int(c["v"]))
            except Exception as e: print("guardar do celular:", c, e)
        elif cmd == "addlouvor" and 0 <= int(c.get("idx", -1)) < len(self.A.louvores):
            self.addLouvor(int(c["idx"]))
        elif cmd == "tirardalista": self.tirar(int(c.get("i", -1)))
        elif cmd == "marcar": self.marcar(int(c.get("i", -1)))     # o ✓ da Lista pelo celular (08/11)
        elif cmd == "abrirprojecao": self.abrirTelao()
        elif cmd == "fecharprojecao": self.fecharTelao()
        elif cmd == "irpara": self.irPara(int(c.get("i", -1)))
        elif cmd == "prox": self.proximo()
        elif cmd == "ant": self.anterior()
        elif cmd == "descanso": self.descanso()
        elif cmd == "preto": self.preto()
        elif cmd == "anim": self.ligarAnimacao(not self.anim_ligada)
        elif cmd == "relogio": self.relogio()
        elif cmd == "mais": self.tamanho(1)
        elif cmd == "menos": self.tamanho(-1)
        elif cmd == "tampadrao": self.tamanho(0)
        elif cmd == "freeze": self.congelar(bool(c.get("on")) if "on" in c else not self.congelado)
        elif cmd == "timer": self.cronometro(float(c.get("min") or 5), str(c.get("rotulo") or ""))
        elif cmd == "timerpausar": self.pausarTimer()          # 12/11: não existia no nativo (caía no "ainda não feita")
        elif cmd == "timerparar": self.pararTimer()            # 12/11: o descanso() sozinho deixava o tempo guardado
        elif cmd == "texto": self.texto(str(c.get("titulo") or ""), str(c.get("corpo") or ""))
        elif cmd == "fundo": self.projetarFundo(int(c.get("i", -1)))
        elif cmd == "espera": self.definirEspera(int(c.get("i", -1)))
        elif cmd == "slidepp": self.projetarSlide(int(c.get("i", -1)))
        elif cmd == "estilo": self.trocarEstilo()
        else: print("ordem do celular ainda não feita no nativo:", cmd)

    def estado(self):
        return {"agora": self._no_ar, "projetando": not self.telao_fechado and not self.semProjetor, "congelado": self.congelado, "estilo": self.estilo,
                "tipo": {"apres": "slide"}.get(self.vivo, self.vivo or "espera"), "louvor": self.idx if self.vivo == "louvor" else -1, "slide": self.slide,
                "escala": self.escala.get(self._chave_esc(), 1),
                "fila": [{"tipo": x["tipo"], "rotulo": x.get("rotulo") or x.get("ref"), "on": bool(x.get("on"))} for x in self.fila],
                "pos": self.pos, "slides": len(self.ap["slides"]) if self.ap else 0, "apres": self.ap["nome"] if self.ap else "",
                "slidepp": self.ap_pos if self.vivo == "apres" else -1, "nativo": True,
                "fundos": self._fundos_celular(), "timer": self._timer_celular(), "avisos": self._avisos_celular()}

    # 12/11 (ele: "sincronizado com as minhas agendas e com o timer de tempo restante"): o celular da 3.0.13 lê e.timer
    # (o mesmo fim que o telão e o operador usam, para os três contarem juntos) e e.avisos (Próximo culto, Cultos da
    # semana, Ceia, Vigília calculados da agenda da igreja). O nativo não mandava nenhum dos dois.
    def _timer_celular(self):
        tm = getattr(self, "timer", None) or {}
        if self.vivo != "timer" or not tm:
            return {}
        if tm.get("pausadoMs") is not None:
            return {"rot": tm.get("rotulo", ""), "fim": 0, "parado": tm["pausadoMs"]}
        return {"rot": tm.get("rotulo", ""), "fim": tm.get("fimTs", 0), "parado": 0}

    def _avisos_celular(self):
        minuto = int(time.time() // 60)                         # a agenda muda por minuto; o celular pergunta por segundo
        if getattr(self, "_av_cel", (None,))[0] != minuto:
            try:
                self._av_cel = (minuto, [{"n": a["nome"], "t": a["titulo"], "c": a["corpo"]} for a in self.avisosProntos()])
            except Exception:
                self._av_cel = (minuto, [])
        return self._av_cel[1]

    # ---- FUNDOS: a galeria (o mesmo listaFundos da 3.0.12, na mesma ordem: o celular manda o número)
    def _fundos_celular(self):
        """O que o controle.html desenha: miniatura (endereço do servidor), nome, categoria, liso, é a espera."""
        if getattr(self, "_fc_chave", None) == (self.estilo, self._espera_arq()):
            return self._fc
        esp = self._espera_arq()
        out = []
        for f in self.A.lista_fundos(self.estilo):
            a = f["arquivo"]
            out.append({"a": "" if os.path.isabs(a) else a, "n": f.get("nome", ""), "c": f.get("cat") or "Base",
                        "l": bool(f.get("liso")), "e": a == esp})
        self._fc, self._fc_chave = out, (self.estilo, esp)
        return out

    def _espera_arq(self):
        e = self.A.config.espera()
        return e or (cerebro.ESPERA_ICM if self.estilo == "limpo" else (self.A.estilos.get(self.estilo) or {}).get("descanso"))

    @Slot(result="QVariantList")
    def fundos(self):
        esp = self._espera_arq()
        return [{"i": k, "nome": f.get("nome", ""), "cat": f.get("cat") or "Base",
                 "url": QUrl.fromLocalFile(self.A.caminho_fundo(f["arquivo"])).toString(),
                 "espera": f["arquivo"] == esp, "arquivo": f["arquivo"]}
                for k, f in enumerate(self.A.lista_fundos(self.estilo))]

    @Slot(result="QVariantList")
    def categoriasFundo(self):
        tem = {f.get("cat") or "Base" for f in self.A.lista_fundos(self.estilo)}
        return ["Todos"] + [c for c in cerebro.CATEGORIAS if c in tem]

    @Property(str, notify=mudou)
    def fundoNoAr(self):
        return self._fundo_no_ar if self.vivo == "fundo" else ""

    @Slot(int)
    def projetarFundo(self, k):
        L = self.A.lista_fundos(self.estilo)
        if not 0 <= k < len(L):
            return
        f = L[k]
        self.vivo = "fundo"
        self._fundo_no_ar = f["arquivo"]
        self._no_ar = "fundo: " + f.get("nome", "")
        self._manda({"modo": "fundo", "fundo": self.A.caminho_fundo(f["arquivo"]), "fade": cerebro.ESMAECER})

    @Slot(int)
    def definirEspera(self, k):
        """Define a tela de espera padrão, sem projetar nada agora (igual à 3.0.12). Fica gravada ao fechar."""
        L = self.A.lista_fundos(self.estilo)
        if not 0 <= k < len(L):
            return
        self.A.config.definir_espera(L[k]["arquivo"])
        self.esperaMudou.emit()
        self.mudou.emit()

    # ---- ADICIONAR / APAGAR FUNDO (mostrarAddFundo e apagarFundo do app.js). A lista dos "meus fundos" e a dos escondidos
    # são as da 3.0.12 (icm_fundos, icm_ocultos); o nativo grava no nativo.json dele e nunca escreve na config da 3.0.12.
    # A imagem acrescentada vira um ARQUIVO em nativo_fundos (nome = md5); apagar tira da lista e não apaga arquivo nenhum.
    def _fundos_mudaram(self):
        self.A.config._meus = None
        self._fc_chave = None
        self.esperaMudou.emit(); self.mudou.emit()

    def _meus_arquivos(self):
        return {f["arquivo"] for f in self.A.config.meus_fundos()}

    @Slot(str, str, result=bool)
    def adicionarFundo(self, url, nome):
        import hashlib, shutil
        p = QUrl(url).toLocalFile() if url.startswith("file:") else url
        if not p or QImage(p).isNull():
            self.aviso.emit("Não consegui abrir essa imagem."); return False
        with open(p, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()[:16]
        pasta = os.path.join(self.A.config.pasta, "nativo_fundos")
        os.makedirs(pasta, exist_ok=True)
        dest = os.path.join(pasta, md5 + (os.path.splitext(p)[1].lower() or ".jpg"))
        if dest in self._meus_arquivos():
            self.aviso.emit("Esse fundo já está na galeria."); return False
        if not os.path.exists(dest):
            shutil.copyfile(p, dest)
        lista = [dict(f) for f in self.A.config.meus_fundos()]
        lista.append({"arquivo": dest, "nome": (nome or "").strip()[:40] or "Meu fundo", "custom": True})
        self.A.config.gravar("icm_fundos", lista)
        self._fundos_mudaram()
        self.aviso.emit("Fundo adicionado.")
        return True

    @Slot(int, result="QVariant")
    def sobreFundo(self, k):
        """Para a pergunta antes de apagar: o nome e se foi ele que acrescentou (some) ou veio com o Sistema (esconde)."""
        L = self.A.lista_fundos(self.estilo)
        if not 0 <= k < len(L):
            return {}
        return {"nome": L[k].get("nome") or "este fundo", "meu": L[k]["arquivo"] in self._meus_arquivos()}

    @Slot(int)
    def apagarFundo(self, k):
        L = self.A.lista_fundos(self.estilo)
        if not 0 <= k < len(L):
            return
        arq = L[k]["arquivo"]
        meu = arq in self._meus_arquivos()
        if meu:
            self.A.config.gravar("icm_fundos", [dict(f) for f in self.A.config.meus_fundos() if f["arquivo"] != arq])
        else:
            ocs = list(self.A.config.ocultos())
            if arq not in ocs: ocs.append(arq)
            self.A.config.gravar("icm_ocultos", ocs)
        if self.A.config.espera() == arq:            # era a tela de espera: volta à de fábrica
            self.A.config.gravar("icm_espera", None)
        self._fundos_mudaram()
        self.aviso.emit("Fundo apagado." if meu else "Fundo escondido.")

    @Property(int, notify=mudou)
    def fundosEscondidos(self):
        return len(self.A.config.ocultos())

    @Slot()
    def restaurarFundos(self):
        """Restaurar › Fundos da 3.0.12: os de fábrica escondidos voltam."""
        self.A.config.gravar("icm_ocultos", [])
        self._fundos_mudaram()
        self.aviso.emit("Os fundos escondidos voltaram.")

    @Property(str, notify=mudou)
    def urlCelular(self):
        return self.url_celular

    # ---- consultas do painel
    @Slot(str, result="QVariantList")
    def buscar(self, q):
        return [{"i": i, "rotulo": self.A.rotulo(i), "anim": self.A.tem_telas_cias(i)} for i in self.A.buscar(q)]

    # ---- o painel 1:1 com a 3.0.12 (07/11): a lista agrupada, o título das telas, a tarja "agora" e o estado do telão
    @Slot(str, result="QVariantList")
    def listaLouvores(self, q):
        na = {x["chave"] for x in self.fila if x["tipo"] == "louvor"}
        out = self.A.lista312(q)
        for r in out:
            if "i" in r:
                r["naLista"] = self.A.chaves[r["i"]] in na
        return out

    @Slot(int, result=str)
    def tituloLouvor(self, i):
        return self.A.rotulo312(self.A.da_vez(i)) if i >= 0 else ""

    @Slot(int, result="QVariantList")
    def telasLouvor(self, i):
        """As telas na coluna do meio (desenharSlidesLouvor): o rótulo amarelo e as 2 primeiras linhas; animada = a miniatura."""
        if i < 0:
            return []
        p = self.A.da_vez(i)
        c169 = self.A.cias169(p) if self.anim_ligada else None
        if c169:                      # as telas 16:9 da fonte: a miniatura é o slide inteiro do PowerPoint
            n = len(c169)
            # 15/11 (ele na EBD): a prévia ESCRITA também, como nos outros louvores: as 2 primeiras linhas da tela
            out = []
            for k, t in enumerate(c169):
                ls, coro = _linhas_da_tela(t.get("linhas") or [])
                out.append({"rot": "Tela %d de %d · %s" % (k + 1, n, "coro" if coro else "animada"),
                            "txt": "\n".join(ls[:2]) + ("…" if len(ls) > 2 else ""),
                            "img": QUrl.fromLocalFile(leve(t["src"], "jpg") or t["src"]).toString()})      # o .jpg leve (09/11)
            return out
        an = self.A.animacao(p) if self.anim_ligada else None
        if an:
            n = len(an)
            return [{"rot": "Tela %d de %d · animada" % (k + 1, n), "txt": "",
                     "img": QUrl.fromLocalFile(os.path.join(cerebro.ANIM, a)).toString() if os.path.exists(os.path.join(cerebro.ANIM, a)) else ""}
                    for k, a in enumerate(an)]
        out = []
        for sl in self.A.louvores[p]["slides"]:
            ls = [l.replace("\x01", "") for l in cerebro.visiveis(sl.get("linhas") or [])]
            out.append({"rot": sl.get("label") or "", "txt": "\n".join(ls[:2]) + ("…" if len(ls) > 2 else ""), "img": ""})
        return out

    # ---- a aba Bíblia em grade (livros · capítulos · versículos), como a 3.0.13
    @Slot(str, result="QVariant")
    def bibBusca(self, q):
        r = self.B.ref_da_busca(q)
        if r:
            # a referência vem PRIMEIRO; os versículos com essas palavras, depois (08/11, relato dele no culto)
            letras = re.sub(r"[^a-z]", "", cerebro.so_letras(q or ""))
            n, tr = self.B.trechos(q) if len(letras) >= 4 else (0, [])
            return {"ref": r, "livros": [], "trechos": tr, "n": n, "porTrecho": False}
        livros = self.B.livros_da_busca(q)
        por = not livros and len(cerebro.so_letras(q or "")) >= 4
        n, tr = self.B.trechos(q) if por else (0, [])
        return {"ref": None, "livros": livros, "trechos": tr, "n": n, "porTrecho": por}

    @Slot(str, result=int)
    def bibCaps(self, livro):
        return len(self.B.livros.get(livro) or [])

    @Slot(str, int, result="QVariantList")
    def bibVers(self, livro, cap):
        if livro not in self.B.livros or not 1 <= cap <= len(self.B.livros[livro]):
            return []
        na = {x["v"] for x in self.fila if x["tipo"] == "verso" and x["livro"] == livro and x["cap"] == cap}
        return [{"v": v, "t": self.B.texto(livro, cap, v), "naFila": v in na} for v in self.B.versos(livro, cap)]

    @Slot(str, result=int)
    def caudaVideo(self, url):
        """A cauda (ms) do vídeo que o Palco vai repetir (cauda_video); 0 = sem cauda."""
        return cauda_video(QUrl(url).toLocalFile() if "://" in url or url.startswith("file:") else url)

    @Slot(str, int, int)
    def projetarVerso(self, livro, cap, v):
        self._verso_solto(livro, cap, v)

    @Slot(str, int, int)
    def guardarVersoRef(self, livro, cap, v):
        if self.addVerso(livro, cap, v):
            self.aviso.emit("Adicionado à lista de projeção.")

    @Property("QVariantList", notify=mudou)
    def bibNoAr(self):
        return list(self.bib) if self.bib and self.vivo in ("biblia", "bibmulti") else []

    # ---- os cards TIMER e TEXTO da 3.0.13 (iniciarTimer/pausarTimer/pararTimer, modelosAviso, fundosLisos, projetarTexto)
    @Property("QVariant", notify=mudou)
    def timerInfo(self):
        """O estado do cronômetro para o mostrador grande do card: correndo (com o fim), pausado (com o que falta) ou parado."""
        tm = getattr(self, "timer", None) or {}
        if self.vivo == "timer" and tm.get("pausadoMs") is not None:
            return {"estado": "pausado", "ms": tm["pausadoMs"], "rotulo": tm.get("rotulo", "")}
        if self.vivo == "timer" and tm.get("fimTs"):
            return {"estado": "correndo", "fimTs": tm["fimTs"], "rotulo": tm.get("rotulo", "")}
        return {"estado": "parado"}

    @staticmethod
    def _fmt_ms(ms):
        s = max(0, round(ms / 1000))
        h, m = s // 3600, (s // 60) % 60
        return "%d:%02d:%02d" % (h, m, s % 60) if h else "%d:%02d" % (s // 60, s % 60)

    @Slot()
    def pausarTimer(self):
        tm = getattr(self, "timer", None)
        if not tm or self.vivo != "timer":
            return
        if tm.get("pausadoMs") is not None:                 # "Continuar": volta a contar do que faltava
            return self.cronometro(tm["pausadoMs"] / 60000, tm.get("rotulo", ""))
        ms = max(0, tm["fimTs"] - time.time() * 1000)
        tm["pausadoMs"] = ms
        self._no_ar = "cronômetro pausado"
        self._manda({"modo": "timer", "fundo": self._plano(), "rotulo": tm.get("rotulo", ""), "parado": True,
                     "texto": self._fmt_ms(ms), "fade": 0})

    @Slot()
    def pararTimer(self):
        # parar APAGA o tempo guardado (senão o Pausar ressuscitava o antigo) e volta para a tela de espera
        self.timer = None
        self.descanso()

    @Slot(result="QVariantList")
    def avisosProntos(self):
        """Os avisos prontos do card Texto (modelosAviso do app.js), já com o título e o texto de hoje."""
        ig = self.A.config.ler("icm_igreja") or {}
        # 12/11: sem "Minha igreja" gravada, os cultos de FÁBRICA (o CULTOS_PADRAO do app.js, o mesmo que o SecIgreja.qml
        # mostra); antes os avisos saíam vazios ("Cultos da semana" sem nenhum culto) numa instalação nova
        cultos = [c for c in (ig.get("cultos") or CULTOS_PADRAO) if c.get("on")]
        DIAS = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
        agora = time.localtime()
        hoje = (agora.tm_wday + 1) % 7                    # o getDay() do JavaScript: 0 = domingo
        min_agora = agora.tm_hour * 60 + agora.tm_min
        def em_min(h):
            a, _, b = (h or "00:00").partition(":")
            return int(a or 0) * 60 + int(b or 0)
        def do_dia(d): return [c for c in cultos if c.get("dia") == d]
        def proximo():
            restam = sorted([c for c in do_dia(hoje) if em_min(c.get("hora")) > min_agora + 20], key=lambda c: em_min(c.get("hora")))
            if restam:
                return {"titulo": "HOJE", "corpo": "\n".join(c["nome"] + " — " + c["hora"] for c in restam)}
            for d in range(1, 8):
                dia = (hoje + d) % 7; lista = do_dia(dia)
                if lista:
                    quando = ("AMANHÃ — " + DIAS[dia].upper()) if d == 1 else DIAS[dia].upper()
                    return {"titulo": quando, "corpo": "\n".join(c["nome"] + " — " + c["hora"] for c in lista)}
            return {"titulo": "AVISO", "corpo": "Que Deus abençoe a todos!"}
        def semana():
            l = [DIAS[d] + " — " + c["hora"] + " — " + c["nome"] for d in range(7) for c in do_dia(d)]
            return {"titulo": "CULTOS DA SEMANA", "corpo": "\n".join(l)}
        def por_extenso(iso):
            try:
                y, mo, d = (int(x) for x in str(iso).split("-"))
                import datetime
                dt = datetime.date(y, mo, d)
                return DIAS[(dt.weekday() + 1) % 7] + ", " + str(d) + "/" + str(iso).split("-")[1]
            except Exception:
                return ""
        def sem_dia_fixo(chave, titulo, convite):
            m = (ig.get("moveis") or {}).get(chave) or {}
            dia = por_extenso(m.get("data"))
            quando = (dia + (" — " + m["hora"] if m.get("hora") else "")) if dia else ""
            return {"titulo": titulo, "corpo": (quando + "\n" if quando else "") + convite}
        nome = (ig.get("nome") or "").strip() or "Igreja Cristã Maranata"
        mods = [("Próximo culto", True, proximo()), ("Cultos da semana", True, semana()),
                ("Aniversariantes", False, {"titulo": "ANIVERSARIANTES", "corpo": "Vamos orar pelos irmãos que fazem aniversário nesta semana."}),
                ("Ceia", False, sem_dia_fixo("ceia", "CEIA", "Participemos todos!")),
                ("Vigília", False, sem_dia_fixo("vigilia", "VIGÍLIA", "Venhamos buscar ao Senhor.")),
                ("Bem-vindos", False, {"titulo": "SEJAM BEM-VINDOS", "corpo": nome + "\nA paz do Senhor!"}),
                ("Silêncio e oração", False, {"titulo": "MOMENTO DE ORAÇÃO", "corpo": "Pedimos silêncio e reverência."}),
                ("Desligue o celular", False, {"titulo": "ATENÇÃO", "corpo": "Por favor, desligue ou silencie o celular."})]
        return [{"nome": n, "auto": a, "titulo": m["titulo"], "corpo": m["corpo"]} for n, a, m in mods]

    @Slot(result="QVariantList")
    def fundosLisos(self):
        return [{"arquivo": f["arquivo"], "nome": f.get("nome", ""), "zona": f["zona"],
                 "url": QUrl.fromLocalFile(self.A.caminho_fundo(f["arquivo"])).toString()} for f in self.A.fundos_lisos(self.estilo)]

    @Slot(str, str, str, bool)
    def projetarTexto(self, titulo, corpo, arquivo, instantaneo):
        """O aviso do card Texto (projetarTexto do app.js): título amarelo, as linhas brancas, no fundo liso escolhido."""
        linhas = [l.strip() for l in (corpo or "").split("\n") if l.strip()]
        if titulo.strip():
            linhas.insert(0, chr(1) + titulo.strip() + chr(1))
        lisos = self.A.fundos_lisos(self.estilo)
        f = next((x for x in lisos if x["arquivo"] == arquivo), lisos[0] if lisos else None)
        fundo = self.A.caminho_fundo(f["arquivo"]) if f else self._plano()
        self.vivo = "texto"
        self._no_ar = "aviso: " + ((titulo.strip() or (linhas[0] if linhas else "")))[:40]
        self._manda({"modo": "texto", "fundo": fundo, "linhas": linhas, "zona": f["zona"] if f else "livre",
                     "tam": 6, "escala": self.escala.get("texto", 1) if isinstance(self.escala, dict) else 1,
                     "fade": 0 if instantaneo else 400})

    @Property(str, notify=mudou)
    def igreja(self):
        """O nome ao lado da marca (o #marca-igreja da 3.0.13: IGREJA.nome || 'Projeção'), da mesma configuração dela."""
        ig = self.A.config.ler("icm_igreja") or {}
        return (ig.get("nome") or "").strip() or "Projeção"

    @Slot(int, result=bool)
    def temAnimacao(self, i):
        """O louvor tem a versão animada das CIAS (o botão Animação da barra de extras só aparece então)."""
        return i >= 0 and self.A.tem_telas_cias(self.A.da_vez(i))

    @Property(str, notify=mudou)
    def vivoTipo(self):
        return self.vivo

    @Property(str, notify=mudou)
    def agora(self):
        """A tarja embaixo da prévia (atualizarAgora do app.js:2416), com as mesmas palavras."""
        v = self.vivo
        if v == "louvor" and self.idx >= 0:
            tot = self.A.telas_do_louvor(self.idx, self.anim_ligada)
            return "Slide %d/%d%s — %s" % (self.slide + 1, tot, " (fim)" if self.slide == tot - 1 else "", self.A.louvores[self.idx]["titulo"])
        if v == "biblia" and self.bib:
            return "%s %d:%d" % self.bib
        if v == "bibmulti":
            n = len(self._marcados())
            return "%d versículos juntos" % n
        if v == "timer":
            return "Timer — " + ((getattr(self, "timer", None) or {}).get("rotulo") or "")
        if v == "relogio":
            return "Relógio"
        if v == "texto":
            return "Texto livre"
        if v == "apres" and self.ap:
            return "Slide %d/%d — %s" % (self.ap_pos + 1, len(self.ap["slides"]), self.ap["nome"])
        if v == "fundo":
            return "Fundo"
        if v == "espera":
            return "Espera"
        if v == "preto":
            return "Tela preta"
        if v == "cifra":
            return "Cifra no telão"
        return "Pronto."

    @Slot(int, result="QVariantList")
    def slides(self, i):
        if i < 0:
            return []
        n = self.A.telas_do_louvor(self.A.da_vez(i), self.anim_ligada)
        txt = self.A.resumo_slides(i)
        if self.A.tem_telas_cias(self.A.da_vez(i)) and self.anim_ligada:
            return ["Tela %d de %d · animada" % (k + 1, n) for k in range(n)]
        return txt

    @Property(str, notify=mudou)
    def noAr(self):
        return self._no_ar

    @Property(int, notify=mudou)
    def idxNoAr(self):
        return self.idx

    @Property(int, notify=mudou)
    def slideNoAr(self):
        return self.slide

    @Property(bool, notify=mudou)
    def animacao(self):
        return self.anim_ligada

    # ---- ordens
    @Slot(int, int)
    def projetar(self, i, slide):
        i = self.A.da_vez(i)
        # outro louvor que não é o item da lista no ar = a lista fica de lado (o selecionarLouvor do app.js)
        it = self.fila[self.pos] if 0 <= self.pos < len(self.fila) else None
        if not (it and it["tipo"] == "louvor" and self._idx_item(it) == i):
            self.pos = -1
            self.filaMudou.emit()
        self.idx, self.slide = i, slide
        self.cias_passo = 0               # o clique de DENTRO da tela 16:9 das CIAS (o efeito "ao clicar" do PowerPoint)
        t = self.A.tela_louvor(i, slide, self.estilo, self.escala["louvor"], self.anim_ligada)
        self.slide = t["slide"]
        self.vivo = "louvor"
        self._no_ar = "%s · tela %d de %d" % (self.A.rotulo(i), self.slide + 1, t["de"])
        self.abrir_no_ar("louvor", self.A.rotulo312(i), self.A.chaves[i])       # o projetarLouvor: a principal (da_vez)
        self._manda(t)

    # ---- a CIFRA (05/11/2026): a folha do painel (abrirCifra/desenharFolha) e o ensaio no telão (projetarCifraTelao).
    # As regras moram no cerebro.py e saem iguais às do app.js (prova_cifra.py: 48 mil comparações, 0 diferentes).
    # o TAMANHO DA LETRA DA FOLHA fica gravado (icm_cifra_fonte da 3.0.12, 10..30, padrão 14): quem lê a folha está com o
    # violão na mão, um metro atrás do monitor. Sem nada gravado no Nativo, vale o que a 3.0.12 deixou.
    @Slot(result=int)
    def cifraFonteSalva(self):
        try: return max(10, min(30, int(self.A.config.ler("icm_cifra_fonte", 14))))
        except Exception: return 14

    @Slot(int)
    def guardarCifraFonte(self, px):
        self.A.config.gravar("icm_cifra_fonte", max(10, min(30, int(px))))

    @Slot(int, result=bool)
    def temCifra(self, i):
        return 0 <= i < len(self.A.louvores) and self.cif.tem(self.A.chaves[i])

    @Slot(int, int, result="QVariant")
    def folhaCifra(self, i, desloc):
        if not self.temCifra(i):
            return {"ok": False}
        f = self.cif.folha(self.A.chaves[i], desloc)
        f["titulo"] = self.A.rotulo(i)
        return f

    @Slot(int, int, result="QVariant")
    def tonsCifra(self, i, desloc):
        """A grade dos doze tons (abrirTons): [{t, on, d}], d = o deslocamento que o botão aplica. Sem tom impresso, vazia
        (igual à 3.0.12: o botão do tom só aparece quando a cifra declara o tom)."""
        reg = self.cif.ler(self.A.chaves[i]) if self.temCifra(i) else None
        tom = (reg or {}).get("tom") or ""
        if not tom:
            return []
        menor = tom.endswith("m")
        raiz = cerebro.tom_agora(tom, desloc).rstrip("m")
        return [{"t": t + ("m" if menor else ""), "on": cerebro.SEMI[t] == cerebro.SEMI.get(raiz), "d": cerebro.desloc_para(tom, t)}
                for t in cerebro.ESCALA_TONS]

    @Slot(int, int)
    def projetarCifra(self, i, desloc):
        pags = self.cif.paginas(self.A.chaves[i], desloc) if self.temCifra(i) else []
        if not pags:
            self.aviso.emit("Esta cifra não tem linhas para projetar.")
            return
        reg = self.cif.ler(self.A.chaves[i]) or {}
        agora = cerebro.tom_agora(reg.get("tom") or "", desloc)
        self.cif_tela = {"pags": pags, "p": 0, "titulo": self.A.rotulo(i) + (" — tom " + agora if agora else "")}
        self.vivo = "cifra"
        self._cifra_manda()

    def _cifra_manda(self):
        c = self.cif_tela
        self._no_ar = "Cifra · %s · página %d de %d" % (c["titulo"], c["p"] + 1, len(c["pags"]))
        self._manda({"modo": "cifra", "fundo": self.A.fundo(self.estilo, "louvor2"), "titulo": c["titulo"],
                     "pares": c["pags"][c["p"]], "pag": "%d de %d" % (c["p"] + 1, len(c["pags"])), "fade": 240})

    def _cifra_pag(self, d):
        c = self.cif_tela
        n = c["p"] + d
        if 0 <= n < len(c["pags"]):
            c["p"] = n
            self._cifra_manda()

    @Property(bool, notify=mudou)
    def cifraNoAr(self):
        return self.vivo == "cifra"

    # ---- PRÓXIMA / ANTERIOR (o proximo()/anterior() do app.js). O que está NO AR manda; com a lista, ela manda.
    # A lista tem dois grupos, LOUVORES e VERSÍCULOS, que não conversam: avançar nos versículos nunca cai num louvor.
    PARADOS = ("relogio", "timer", "texto", "fundo", "preto")

    def _vizinho(self, d):
        if not 0 <= self.pos < len(self.fila):
            return -1
        tipo = self.fila[self.pos]["tipo"]
        k = self.pos + d
        while 0 <= k < len(self.fila):
            if self.fila[k]["tipo"] == tipo:
                return k
            k += d
        return -1

    def _louvor_prox(self):
        # a tela 16:9 das CIAS com efeito "ao clicar": o Avançar toca o clique de dentro antes de ir à tela seguinte,
        # como o PowerPoint e a apresentação (slideProximo)
        c = self.A.cias169(self.idx) if self.anim_ligada else None
        if c and 0 <= self.slide < len(c) and c[self.slide]["mov"]:
            ult = len(c[self.slide]["mov"].get("passos") or [[]]) - 1
            if getattr(self, "cias_passo", 0) < ult:
                self.cias_passo = getattr(self, "cias_passo", 0) + 1
                t = self.A.tela_louvor(self.idx, self.slide, self.estilo, self.escala["louvor"], self.anim_ligada)
                t["passo"], t["fade"] = self.cias_passo, 0
                return self._manda(t)
        if self.slide < self.A.telas_do_louvor(self.idx, self.anim_ligada) - 1:
            self.projetar(self.idx, self.slide + 1)
        else:                                # acabou o louvor: tela de espera; o PRÓXIMO "Próxima" abre o seguinte
            self.descanso()
            self.aguardando = True

    @Slot()
    def proximo(self):
        self._portao(1)

    @Slot()
    def anterior(self):
        self._portao(-1)

    def _proximo_ja(self):
        if self.aguardando:
            # igual à 3.0.12 (app.js:1990): abre o item SEGUINTE da lista, louvor ou versículo. O versículo
            # guardado durante o louvor entra logo depois dele (ordem dele 03/11 15h12: "assim que terminar
            # o louvor, eu clico em avançar, ele começa a projetar o versículo")
            # (a 3.0.12 só abria se ainda houvesse OUTRO louvor adiante: versículo depois do último louvor não entrava)
            j = self.pos + 1 if 0 <= self.pos < len(self.fila) - 1 else -1
            if j >= 0:
                self.irPara(j)
            else:
                self.aviso.emit("Louvor concluído. Escolha o próximo, ou Anterior para voltar ao último slide.")
            return
        if self.vivo == "apres":
            return self._slide_prox_ja()
        if self.vivo == "cifra":             # ensaio: passa a página da cifra (app.js:1999)
            return self._cifra_pag(1)
        if self.vivo in self.PARADOS:
            return
        if self.pos >= 0:
            if self.fila[self.pos]["tipo"] == "apres":   # apresentação fora do ar (ex.: tela de espera): não sai lendo a Bíblia
                return
            if self.vivo == "louvor":
                return self._louvor_prox()
            if self.cont_antes > 0:          # voltando dos versículos antes do 1º escolhido: desanda até a lista
                self.cont_antes -= 1
                return self.irPara(self.pos) if self.cont_antes == 0 else self._bib(*self.B.proximo(*self.bib))
            j = self._vizinho(1)
            if j >= 0:
                return self.irPara(j)
            if self.vivo in ("biblia", "bibmulti") and self.bib:   # passou do último versículo da lista: leitura contínua, contando
                self.cont_depois += 1
                self._bib(*self.B.proximo(*self.bib))
            return
        if self.vivo == "louvor" and self.idx >= 0:
            self._louvor_prox()
        elif self.vivo in ("biblia", "bibmulti") and self.bib:
            self._bib(*self.B.proximo(*self.bib))
        elif self.vivo in ("espera", "descanso") and self.idx >= 0:     # o toast da 3.0.12/3.0.13 nesse caso
            self.aviso.emit("Selecione o próximo louvor para continuar.")

    def _anterior_ja(self):
        if self.aguardando or (self.vivo == "espera" and self.idx >= 0):   # volta ao ÚLTIMO slide do louvor
            self.aguardando = False
            return self.projetar(self.idx, self.A.telas_do_louvor(self.idx, self.anim_ligada) - 1)
        if self.vivo == "apres":
            return self._slide_ant_ja()
        if self.vivo == "cifra":
            return self._cifra_pag(-1)
        if self.vivo in self.PARADOS:
            return
        if self.pos >= 0:
            if self.fila[self.pos]["tipo"] == "apres":
                return
            ant = self._vizinho(-1)
            if self.vivo == "louvor":        # voltando para o louvor de trás, cai no ÚLTIMO slide dele
                if self.slide > 0: self.projetar(self.idx, self.slide - 1)
                elif ant >= 0: self.irPara(ant, True)
                return
            if self.cont_depois > 0:
                self.cont_depois -= 1
                return self.irPara(self.pos) if self.cont_depois == 0 else self._bib(*self.B.anterior(*self.bib))
            if self.cont_antes > 0 and self.bib:
                self.cont_antes += 1
                return self._bib(*self.B.anterior(*self.bib))
            if ant >= 0:
                return self.irPara(ant, True)
            if self.vivo in ("biblia", "bibmulti") and self.bib:   # antes do 1º escolhido: lê para trás CONTANDO (o caminho de volta existe)
                self.cont_antes += 1
                self._bib(*self.B.anterior(*self.bib))
            return
        if self.vivo == "louvor" and self.idx >= 0 and self.slide > 0:
            self.projetar(self.idx, self.slide - 1)
        elif self.vivo in ("biblia", "bibmulti") and self.bib:
            self._bib(*self.B.anterior(*self.bib))

    # ---- a LISTA DO CULTO
    def _idx_item(self, it):
        """O louvor pela CHAVE (nunca pelo índice cru); -1 = não existe mais (nunca projetar outro no lugar)."""
        try:
            return self.A.da_vez(self.A.chaves.index(it["chave"]))
        except ValueError:
            return -1

    def _mexeu(self):
        self.filaMudou.emit(); self.mudou.emit()

    @Slot(int, result=bool)
    def addLouvor(self, i):
        p = self.A.da_vez(i)                 # a cópia entra como a principal: uma letra só
        k = self.A.chaves[p]
        if any(x["tipo"] == "louvor" and x["chave"] == k for x in self.fila):
            self.aviso.emit("Esse louvor já está na lista."); return False
        self.fila.append({"tipo": "louvor", "chave": k, "rotulo": self.A.rotulo312(p)})
        self.cont_depois = 0
        self._mexeu(); return True

    def addVerso(self, livro, cap, v):
        if any(x["tipo"] == "verso" and (x["livro"], x["cap"], x["v"]) == (livro, cap, v) for x in self.fila):
            self.aviso.emit("Esse versículo já está na lista."); return False
        self.fila.append({"tipo": "verso", "livro": livro, "cap": cap, "v": v, "ref": "%s %d:%d" % (livro, cap, v), "on": False})
        self.cont_depois = 0
        self._mexeu(); return True

    @Slot(result=bool)
    def guardarVerso(self):
        if not self.bib:
            self.aviso.emit("Projete um versículo antes de guardá-lo."); return False
        return self.addVerso(*self.bib)

    @Slot(int)
    @Slot(int, bool)
    def irPara(self, i, ao_fim=False):
        if not 0 <= i < len(self.fila):
            return
        it = self.fila[i]
        self.pos, self.cont_depois, self.cont_antes = i, 0, 0
        if it["tipo"] == "louvor":
            k = self._idx_item(it)
            if k < 0:
                self.aviso.emit("Este louvor não está mais disponível."); self._mexeu(); return
            self.escolhido.emit(k)
            self.projetar(k, self.A.telas_do_louvor(k, self.anim_ligada) - 1 if ao_fim else 0)
        elif it["tipo"] == "apres":
            k = next((n for n, a in enumerate(self.listaApres()) if a["nome"] == it["nome"]), -1)
            if k < 0:
                self.aviso.emit("Esta apresentação não está mais disponível."); self._mexeu(); return
            self.entrarApresentacao(k, it.get("pos", 0))
        else:
            self._bib(it["livro"], it["cap"], it["v"])
        self._mexeu()

    @Slot(int)
    def tirar(self, i):
        if not 0 <= i < len(self.fila):
            return
        era = self.pos == i
        self.fila.pop(i)
        if self.pos == i: self.pos = min(i, len(self.fila) - 1) if self.fila else -1
        elif self.pos > i: self.pos -= 1
        self._mexeu()
        self._reprojetar_vista()
        if era:                            # tirou o que estava no ar: o telão concorda com a lista
            if self.fila: self.irPara(self.pos)
            else: self.pos = -1; self.descanso()

    @Slot(int, int)
    def mover(self, i, d):
        j = i + d
        if not (0 <= i < len(self.fila) and 0 <= j < len(self.fila)):
            return
        self.fila[i], self.fila[j] = self.fila[j], self.fila[i]
        if self.pos == i: self.pos = j
        elif self.pos == j: self.pos = i
        self._mexeu()
        self._reprojetar_vista()

    @Slot(int, int)
    def arrastar(self, de, para):
        """Arrastar e soltar (soltarFila do app.js): o item vai PARA a posição de destino; o realce segue o item no ar."""
        if de == para or not (0 <= de < len(self.fila) and 0 <= para < len(self.fila)):
            return
        atual = self.fila[self.pos] if 0 <= self.pos < len(self.fila) else None
        it = self.fila.pop(de)
        self.fila.insert(para, it)
        if atual is not None: self.pos = next(k for k, x in enumerate(self.fila) if x is atual)
        self._mexeu()
        self._reprojetar_vista()

    # ---- JUNTOS (projetarVersiculosJuntos do app.js:1761): o ✓ dos versículos da Lista projeta os marcados numa tela só
    def _marcados(self):
        return [x for x in self.fila if x["tipo"] == "verso" and x.get("on")]

    @Slot(int)
    def marcar(self, i):
        """O ✓ é pedido EXPLÍCITO de projetar: vai para o telão mesmo com louvor no ar (reordenar e tirar só organizam)."""
        if not (0 <= i < len(self.fila)) or self.fila[i]["tipo"] != "verso":
            return
        self.fila[i]["on"] = not self.fila[i].get("on")
        self._mexeu()
        if self._marcados(): self.projetarJuntos()
        else: self._reprojetar_vista()

    @Slot(int)
    def projetarSelecaoAtual(self, escolhido):
        """O "Projetar" (o botão em espera / tecla P) da 3.0.13, na MESMA ordem do projetarSelecaoAtual do app.js: a
        apresentação aberta (o slide em que está), os versículos marcados juntos, o item da Lista em uso, o ÚLTIMO
        VERSÍCULO da Bíblia, o louvor escolhido, o 1º da Lista; senão avisa. Antes ia sempre ao louvor escolhido: parar
        a Bíblia e projetar de novo pulava para um louvor (B8, relato dele 07/11 21h16)."""
        if self.ap and self.ap_vista and self.ap["slides"]:
            i = self.ap_pos if 0 <= self.ap_pos < len(self.ap["slides"]) else 0
            return self.projetarSlide(i)
        if any(x["tipo"] == "verso" and x.get("on") for x in self.fila):
            return self.projetarJuntos()
        if 0 <= self.pos < len(self.fila):
            return self.irPara(self.pos)
        if self.bib:
            return self._bib(*self.bib)
        if escolhido >= 0:
            return self.projetar(escolhido, 0)
        if self.fila:
            return self.irPara(0)
        self.aviso.emit("Escolha um louvor ou versículo para projetar.")

    @Slot()
    def projetarJuntos(self):
        vs = self._marcados()
        if not vs:
            self.aviso.emit("Marque (✓) os versículos que devem aparecer juntos" if any(x["tipo"] == "verso" for x in self.fila)
                            else "Adicione versículos à lista"); return
        if len(vs) == 1:                     # um só marcado: versículo normal, e a navegação volta a obedecer a lista
            s = vs[0]
            return self._verso_solto(s["livro"], s["cap"], s["v"])
        self.bib = (vs[-1]["livro"], vs[-1]["cap"], vs[-1]["v"])   # a leitura continua depois do ÚLTIMO
        self.pos, self.cont_depois, self.cont_antes = -1, 0, 0
        self.vivo = "bibmulti"
        self._no_ar = "%s (+%d)" % (vs[0]["ref"], len(vs) - 1)
        # vários juntos: conta o PRIMEIRO, com quantos foram juntos (o projetarJuntos da 3.0.13)
        p0 = vs[0]
        self.abrir_no_ar("verso", "%s %d:%d (+%d)" % (p0["livro"], p0["cap"], p0["v"], len(vs) - 1),
                         "v|%s|%d|%d" % (p0["livro"], p0["cap"], p0["v"]))
        self._manda(self.B.tela_juntos([(x["livro"], x["cap"], x["v"]) for x in vs], self.estilo, self.escala["biblia"]))
        self._mexeu()

    def _reprojetar_vista(self):
        """Mexeu na lista com VERSÍCULO no ar: o telão acompanha. Com louvor, apresentação ou aviso no ar, NÃO."""
        if self.vivo not in ("biblia", "bibmulti"):
            return
        if self._marcados(): self.projetarJuntos()
        elif self.vivo == "bibmulti" and self.bib: self._bib(*self.bib)

    @Slot()
    def limparLista(self):
        """Apagar tudo esquece também a última Bíblia (3.0.13, ele 25/10)."""
        self.fila, self.pos, self.cont_depois, self.cont_antes = [], -1, 0, 0
        self.bib = None if self.vivo not in ("biblia", "bibmulti") else self.bib
        self._mexeu()

    @Slot(result="QVariantList")
    def itensLista(self):
        return [{"tipo": x["tipo"], "rotulo": x.get("rotulo") or x.get("ref"), "on": bool(x.get("on")),
                 "det": ("%d/%d" % (x.get("pos", 0) + 1, x.get("n", 0))) if x["tipo"] == "apres" else ""} for x in self.fila]

    @Property(int, notify=mudou)
    def posLista(self):
        return self.pos

    def _verso_solto(self, livro, cap, v):
        """Versículo escolhido fora da lista: se ele ESTÁ na lista, a navegação volta a obedecer a lista."""
        self.pos = -1
        self._bib(livro, cap, v)
        for k, x in enumerate(self.fila):
            if x["tipo"] == "verso" and (x["livro"], x["cap"], x["v"]) == (livro, cap, v):
                self.pos, self.cont_depois, self.cont_antes = k, 0, 0
                break
        self._mexeu()

    @Slot()
    def descanso(self):
        self.fechar_no_ar()                  # saiu do ar: fecha o cronômetro
        self.vivo = "espera"
        self._no_ar = "tela de espera"
        self._manda(self.A.tela_descanso(self.estilo))

    @Slot()
    def preto(self):
        self.vivo = "preto"
        self._no_ar = "tela preta"
        self._manda({"modo": "preto", "fade": cerebro.ESMAECER})

    # ---- APRESENTAÇÕES (entrarApresentacao / projetarSlide / slideProximo do app.js)
    def listaApres(self, de_novo=False):
        if self._aps is None or de_novo:
            try: self._aps = cerebro.apresentacoes()
            except Exception as e: print("apresentações:", e); self._aps = []
            for a in self._aps:
                levar(a)
        return self._aps

    @Slot(result="QVariantList")
    def apresentacoes(self):
        """A grade. As escondidas (icm_ap_ocultas, a mesma lista da 3.0.12) saem só daqui: o número "i" de cada uma
        continua o da lista inteira, que é o que a Lista do culto, o celular e o entrarApresentacao usam."""
        oc = set(self.A.config.ler("icm_ap_ocultas", []) or [])
        esp = self._especiais()
        return [{"i": k, "nome": a["nome"], "n": len(a["slides"]), "demo": a["demo"],
                 "mini": QUrl.fromLocalFile(leve(a["slides"][0], "jpg") or a["slides"][0]).toString(), "anim": len(a["mov"]),
                 "especial": unicodedata.normalize("NFC", a["nome"]) in esp}
                for k, a in enumerate(self.listaApres()) if a["nome"] not in oc]

    def _especiais(self):
        """As apresentações ESPECIAIS (com gestos para a TV de retorno): as chaves "apres:<nome>" do dados/gestos.js, como
        o carregarEspeciais da 3.0.13. Ganham a moldura verde e o selo das duas telas na grade."""
        if not hasattr(self, "_esp_cache"):
            try:
                txt = open(cerebro.dado("gestos.js"), encoding="utf-8").read()
                self._esp_cache = {unicodedata.normalize("NFC", m) for m in re.findall(r'"apres:([^"]+)"', txt)}
            except Exception:
                self._esp_cache = set()
        return self._esp_cache

    # ---- ESCONDER / APAGAR APRESENTAÇÃO (apagarApresentacao do app.js): a que veio com o Sistema só se esconde; a que ele
    # importou sai da grade. A 3.0.12 apaga a pasta dela (rmtree); aqui a pasta é MUDADA para "apresentacoes_apagadas", ao
    # lado (dá para trazer de volta à mão). A que está no ar não sai: primeiro sai dela.
    @Slot(int, result="QVariant")
    def sobreApres(self, k):
        L = self.listaApres()
        return {"nome": L[k]["nome"], "demo": L[k]["demo"]} if 0 <= k < len(L) else {}

    @Slot(int)
    def apagarApres(self, k):
        import shutil
        L = self.listaApres()
        if not 0 <= k < len(L):
            return
        a = L[k]
        if a["demo"]:
            oc = list(self.A.config.ler("icm_ap_ocultas", []) or [])
            if a["nome"] not in oc: oc.append(a["nome"])
            self.A.config.gravar("icm_ap_ocultas", oc)
            if self.ap and self.ap["nome"] == a["nome"] and self.vivo != "apres": self.ap_vista = False
            self.apresMudou.emit(); self.mudou.emit()
            self.aviso.emit("Apresentação escondida."); return
        if self.ap and self.ap["nome"] == a["nome"] and self.vivo == "apres":
            self.aviso.emit("Essa apresentação está no ar: troque o telão antes de apagar."); return
        raiz = os.path.normpath(cerebro._servidor().SAIDA)
        alvo = os.path.normpath(os.path.join(raiz, a["nome"]))
        if os.path.dirname(alvo) != raiz or not os.path.isdir(alvo):        # só dentro da pasta das importadas
            self.aviso.emit("Apresentação não encontrada."); return
        lixo = os.path.join(os.path.dirname(raiz), "apresentacoes_apagadas")
        os.makedirs(lixo, exist_ok=True)
        shutil.move(alvo, os.path.join(lixo, "%s_%s" % (a["nome"], time.strftime("%Y%m%d_%H%M%S"))))
        if self.ap and self.ap["nome"] == a["nome"]:
            self.ap, self.ap_vista = None, False
        self.listaApres(de_novo=True)
        self.apresMudou.emit(); self.mudou.emit()
        self.aviso.emit("Apresentação apagada.")

    @Property(int, notify=mudou)
    def apresEscondidas(self):
        return len(self.A.config.ler("icm_ap_ocultas", []) or [])

    @Slot()
    def restaurarApres(self):
        self.A.config.gravar("icm_ap_ocultas", [])
        self.apresMudou.emit(); self.mudou.emit()
        self.aviso.emit("As apresentações escondidas voltaram.")

    @Slot(result="QVariantList")
    def slidesApres(self):
        a = self.ap
        if not a: return []
        if "mostra" not in a:
            levar(a)
        # o painel desenha o LEVE (.jpg: a miniatura sai 4x mais rápido que do WebP); o animado com .mp4 não anima aqui:
        # o "No telão agora" espelha o vídeo do telão (videoTelao)
        return [{"i": k, "url": QUrl.fromLocalFile(a["mostra"][k]).toString(),
                 "texto": (a["textos"][k] if k < len(a["textos"]) else "") or "",
                 "nota": (a["notas"][k] if k < len(a["notas"]) else "") or "",
                 "cliques": self._cliques(k), "animada": False if a["video"][k] else self._animada(s),
                 "video": bool(a["video"][k] or (a["mov"].get(str(k)) or {}).get("video"))} for k, s in enumerate(a["slides"])]

    @Property(str, notify=apresMudou)
    def apresAberta(self):
        return self.ap["nome"] if self.ap and self.ap_vista else ""

    @Property(int, notify=mudou)
    def slideApres(self):
        return self.ap_pos if self.vivo == "apres" else -1

    @Property(int, notify=mudou)
    def passoApres(self):
        return self.ap_passo

    def _cliques(self, i):
        m = self.ap["mov"].get(str(i)) if self.ap else None
        return len(m["passos"]) - 1 if m else 0

    @Slot(int)
    @Slot(int, int)
    def entrarApresentacao(self, k, pos=0):
        L = self.listaApres()
        if not 0 <= k < len(L) or not L[k]["slides"]:
            return
        self.ap = L[k]
        self.ap_pos, self.ap_vista = -1, True
        # a apresentação entra na lista do culto como UM item, e guarda onde parou
        j = next((n for n, x in enumerate(self.fila) if x["tipo"] == "apres" and x["nome"] == self.ap["nome"]), -1)
        if j < 0:
            self.fila.append({"tipo": "apres", "nome": self.ap["nome"], "rotulo": self.ap["nome"], "pos": 0,
                              "n": len(self.ap["slides"])})
            j = len(self.fila) - 1
        self.pos, self.cont_depois, self.cont_antes = j, 0, 0
        self.apresMudou.emit()
        self.projetarSlide(max(0, min(pos, len(self.ap["slides"]) - 1)))
        self._mexeu()

    @Slot()
    def sairApresentacao(self):
        """O "‹ Apresentações": volta para a grade; o telão continua no slide (a tela de espera é do painel)."""
        self.ap_vista = False
        self.apresMudou.emit()

    @Slot(int)
    @Slot(int, int)
    def projetarSlide(self, i, passo=-1):
        a = self.ap
        if not a or not 0 <= i < len(a["slides"]):
            return
        mesmo = self.vivo == "apres" and self.ap_pos == i and passo >= 0
        self.ap_pos, self.ap_passo = i, max(0, min(self._cliques(i), passo if passo >= 0 else 0))
        self.vivo = "apres"
        self._no_ar = "%s · tela %d de %d" % (a["nome"], i + 1, len(a["slides"]))
        if "mostra" not in a:
            levar(a)
        m = a["mov"].get(str(i))
        # o FORMATO LEVE (09/11): o telão desenha o .jpg parado e, no animado, toca o .mp4 por cima (a placa decodifica);
        # sem o leve, o original e a animação WebP como antes
        video = (m.get("video") if m else "") or a["video"][i]
        vid_de = lambda k: ("" if not 0 <= k < len(a["slides"]) else
                            (a["filme"][str(k)][0]["v"] or a["filme"][str(k)][0]["laco"]) if str(k) in a.get("filme", {}) else
                            ((a["mov"].get(str(k)) or {}).get("video") or a["video"][k]))
        t = {"modo": "apres", "src": a["mostra"][i], "url": a["urls"][i], "i": i,
             "animada": False if video else self._animada(a["slides"][i]), "video": video,
             "proxVideo": vid_de(i + 1),
             "spr": a["slides"][i] if (ANIM_IMAGEM and not video) else "",     # o original: a folha de sprites (protótipo)        # a câmera livre já abre o vídeo do próximo (Palco.preparaVideo)
             "fade": 0 if mesmo else cerebro.ESMAECER, "passo": self.ap_passo}
        if m:
            t["mov"], t["movUrl"] = m, a["movUrl"].get(str(i))
        fm = a.get("filme", {})
        if str(i) in fm:                              # 09/11: o slide FILMADO (um vídeo por clique, sem as camadas)
            poe_filme(t, fm[str(i)], self.ap_passo)
            if self.ap_passo >= len(fm[str(i)]) - 1:   # o último clique: o próximo vídeo é o do slide seguinte
                t["proxVideo"] = vid_de(i + 1)
        tem_cam = lambda k: str(k) in a["mov"] and str(k) not in fm     # camadas de verdade (não filmadas) para abrir
        if self.deposito is not None and not mesmo:   # este, o de trás e o da frente ficam abertos; o da frente abre já, no fundo
            cam = lambda k: ([] if not 0 <= k < len(a["slides"]) else
                             [a["mostra"][k]] + ([a["mov"][str(k)]["base"]] + [c["src"] for c in a["mov"][str(k)]["camadas"]]
                                                 if tem_cam(k) else []))
            self.deposito.preparar(cam(i - 1) + cam(i) + cam(i + 1), cam(i + 1) + cam(i - 1))
        if self.quadros is not None and not mesmo:    # e os quadros ANIMADOS dos vizinhos (antes só os parados): o da frente 1º
            viz = lambda k: ([] if not 0 <= k < len(a["slides"]) else
                             ([a["mov"][str(k)]["base"]] + [c["src"] for c in a["mov"][str(k)]["camadas"]] + [a["mostra"][k]]
                              if tem_cam(k) else [a["mostra"][k]]))      # o leve: .jpg parado = nada a aquecer
            # forma B: o que já tem folha de sprites não precisa dos quadros cheios (09/11, CPU do Vaio)
            self.quadros.aquecer([c for c in viz(i + 1) + viz(i - 1) if not self.spritesDe(c)])
        for n, x in enumerate(self.fila):
            if x["tipo"] == "apres" and x["nome"] == a["nome"]:
                x["pos"] = i; self.pos = n
        self._manda(t)
        self.filaMudou.emit()

    @Slot(QObject)
    def ligarPorteiro(self, cam):
        """a câmera do telão pede o porteiro do arquivo único ao nascer (Palco.qml)"""
        ligar_porteiro(cam)

    # ---- ANTI-QUEIMA-ROUPA (protocolo dele, 11/11/2026 ~00h50): "Enquanto ele continuar clicando em avançar, ele vai
    # jogar o próximo (...) Dá pra passar pro próximo, joga pro próximo. Soltou a teclinha, não joga pro próximo." Antes cada
    # clique mudava o slide na hora e o telão pulava direto para o último pedido (o "te joga pra tela final"). Agora:
    #  - o slide só anda quando o TELÃO avisou que o anterior ficou pronto (Palco.trocar -> telaoPronto);
    #  - nunca mais que 5 por segundo (PORTAO_MIN; 30 slides em 6 s, a conta dele), mesmo em máquina forte;
    #  - guarda NO MÁXIMO um pedido (o último); soltou a tecla (soltou()), o guardado é esquecido: não despeja fila depois;
    #  - o telão não avisou em PORTAO_TETO (sem projetor, janela escondida): libera assim mesmo, nunca fica preso.
    def _portao(self, d):
        if not self._pt_telao:          # nenhum telão avisou ainda (o controle sozinho, sem o QML): passa direto, como antes
            return self._proximo_ja() if d > 0 else self._anterior_ja()
        agora = time.monotonic()
        # TECLA SEGURADA x TOQUE (11/11 11h56). A repetição do teclado manda um pedido a cada ~33 ms; a mão que toca várias
        # vezes não passa de uns 8 por segundo. Pedido a menos de 70 ms do anterior = tecla segurada.
        self._pt_rep = (agora - self._pt_t_quer) < 0.07
        self._pt_t_quer = agora
        if self._pt_rep:                # segurada: um só guardado (o último), que some quando solta
            self._pt_quer = d
        elif self._pt_ocupado:          # toque com o telão trocando: CONTA (até PERDAO_TOQUES), e sai com o esmaecimento curto
            mesmo = (self._pt_quer > 0) == (d > 0) and self._pt_quer != 0
            self._pt_quer = max(-PERDAO_TOQUES, min(PERDAO_TOQUES, (self._pt_quer if mesmo else 0) + d))
            self._pt_perdao = True
        else:
            self._pt_quer = d
        self._pt_tenta()

    def _pt_tenta(self):
        if not self._pt_quer or self._pt_ocupado:
            return
        piso = PORTAO_MIN if (self._pt_perdao or self.vivo != "apres") else PORTAO_MIN_APRES
        falta = self._pt_ult + piso - time.monotonic()
        if falta > 0:
            self._pt_relogio.start(int(falta * 1000) + 1); return
        # a tecla segurada que SOLTOU sem avisar (as setas são Shortcut do Qt, que não dizem quando soltam): era repetição
        # e nenhum pedido chegou nos últimos 300 ms = soltou; o guardado é esquecido. O toque nunca é esquecido.
        if self._pt_rep and time.monotonic() - self._pt_t_quer > 0.3:
            self._pt_quer = 0; self._pt_rep = False
            return
        d = 1 if self._pt_quer > 0 else -1
        self._pt_quer -= d
        self._pt_ult = time.monotonic()
        antes = self._pt_mandas
        self._pt_rapido = FADE_PERDAO if self._pt_perdao else FADE_RAPIDO
        if not self._pt_quer: self._pt_perdao = False
        try:
            self._proximo_ja() if d > 0 else self._anterior_ja()
        finally:
            self._pt_rapido = 0
        if self._pt_mandas != antes:
            self._pt_ocupado = True; self._pt_teto.start()
        elif self._pt_quer:              # nada saiu (fim da lista): o que sobrou guardado não vale
            self._pt_quer = 0; self._pt_perdao = False

    @Slot()
    def telaoEntrando(self):
        """o telão avisa que a tela nova está pronta e COMEÇOU a entrar. Na Bíblia (só letra, leve) o portão já abre aqui,
        com o piso de 5 por segundo: ele quer ver os versículos passando rápido (HD 00h46: "é lindo de ver"). Louvor e
        apresentação (imagem e vídeo) esperam a troca terminar (telaoPronto)."""
        self._pt_entradas = getattr(self, "_pt_entradas", 0) + 1     # (o banco_verde marca aqui o começo do esmaecimento)
        self.trocaComecou.emit()           # as prévias do painel esmaecem junto com o telão
        if self.vivo in ("biblia", "bibmulti"):
            self.telaoPronto()

    @Slot()
    def telaoPronto(self):
        """o telão (Palco.trocar, o que não é prévia) avisa que o slide novo está pronto e entrando: o portão abre"""
        self._pt_telao = True; self._pt_prontos += 1
        self.trocaTerminou.emit()          # o painel do operador devolve o espelho do vídeo ao "No telão agora"
        self._pt_ocupado = False; self._pt_teto.stop()
        self._pt_tenta()

    @Slot()
    def soltou(self):
        """soltou a tecla (o passador, a seta, o espaço): se ela estava SEGURADA, o pedido guardado não vale mais. O toque
        (apertou e soltou) continua valendo: 11/11 11h56, o toque rápido era jogado fora aqui"""
        if self._pt_rep:
            self._pt_quer = 0; self._pt_rep = False; self._pt_relogio.stop()

    @Slot()
    def slideProximo(self):
        self._portao(1)

    @Slot()
    def slideAnterior(self):
        self._portao(-1)

    def _slide_prox_ja(self):
        if not self.ap: return
        i = self.ap_pos
        if i >= 0 and self.ap_passo < self._cliques(i):        # o clique seguinte DENTRO do slide (o barco, o coração)
            return self.projetarSlide(i, self.ap_passo + 1)
        if i < len(self.ap["slides"]) - 1:
            self.projetarSlide(i + 1)

    def _slide_ant_ja(self):
        if not self.ap: return
        i = self.ap_pos
        if i >= 0 and self.ap_passo > 0:                         # desfaz o último clique
            return self.projetarSlide(i, self.ap_passo - 1)
        if i > 0:                                                # o slide de trás volta ao FIM dele (o PowerPoint faz assim)
            self.projetarSlide(i - 1, self._cliques(i - 1))

    @Slot(str, result=int)
    def acharSlide(self, q):
        """A busca "nº ou palavra": número vai à tela; palavra acha a 1a tela cujo texto a contém."""
        q = (q or "").strip()
        if not self.ap or not q: return -1
        if q.isdigit():
            return int(q) - 1 if 0 < int(q) <= len(self.ap["slides"]) else -1
        alvo = cerebro.sem_acento(q).lower()
        for k, x in enumerate(self.ap["textos"]):
            if alvo in cerebro.sem_acento(x or "").lower():
                return k
        return -1

    def _tabelas_gestos(self):
        """As tabelas de gestos das apresentações (window.GESTOS["apres:<nome>"] do dados/gestos.js), por nome NFC."""
        if not hasattr(self, "_gestos_cache"):
            self._gestos_cache = {}
            try:
                txt = open(cerebro.dado("gestos.js"), encoding="utf-8").read()
                dec = json.JSONDecoder()
                for m in re.finditer(r'window\.GESTOS\["apres:([^"]+)"\]\s*=\s*', txt):
                    obj, _ = dec.raw_decode(txt[m.end():])
                    self._gestos_cache[unicodedata.normalize("NFC", m.group(1))] = obj
            except Exception as e:
                print("gestos.js:", e)
        return self._gestos_cache

    @Slot(result="QVariant")
    def painelB(self):
        """O "Painel B" do modo apresentação (pbLouvores da 3.0.13): os LOUVORES da apresentação (de-até, pela tabela de
        gestos) e os slides que têm gestos (o selo "gestos"). Sem tabela, listas vazias."""
        if not self.ap:
            return {"louvores": [], "gestos": []}
        t = self._tabelas_gestos().get(unicodedata.normalize("NFC", self.ap["nome"])) or {}
        seq = []
        for s in sorted(int(k) for k in t.keys() if str(k).isdigit()):
            l = (t[str(s)] or {}).get("louvor")
            if not seq or seq[-1]["nome"] != l:
                seq.append({"nome": l, "de": s, "ate": s})
            else:
                seq[-1]["ate"] = s
        return {"louvores": seq, "gestos": sorted(int(k) for k in t.keys() if str(k).isdigit())}

    def _animada(self, caminho):
        """O slide é uma imagem ANIMADA (WebP/GIF com vários quadros, ex.: as notinhas da "Louvores da Evangelização")?
        A 3.0.13 toca a animação no telão, na prévia e nas miniaturas (o <img> do navegador). Lê só o cabeçalho; guarda."""
        if os.environ.get("NATIVO_SEM_ANIM"):          # só para medir: o custo da animação
            return False
        cache = self.__dict__.setdefault("_anim_cache", {})
        if caminho not in cache:
            ritmo = ritmo_webp(caminho)
            if len(ritmo) < 2:                      # não é WebP animado: GIF e outros, pelo leitor do Qt (100 ms)
                r = QImageReader(caminho)
                n = r.imageCount() if r.supportsAnimation() else 1
                ritmo = [100] * n if n > 1 else []
            cache[caminho] = ritmo
        return len(cache[caminho]) > 1

    @Slot(result="QVariant")
    def redeCelular(self):
        """O endereço e o QR para o celular entrar (o /api/rede da 3.0.13: Configurações › Celular)."""
        u = self.url_celular or ""
        return {"url": u, "qr": qr_png(u) if u else ""}

    @Slot(str)
    def copiar(self, texto):
        """Para a área de transferência (o "Copiar endereço")."""
        QGuiApplication.clipboard().setText(texto)

    @Slot(str, result="QVariant")
    def spritesDe(self, caminho):
        """FORMA B (protótipo, 08/11): a folha de sprites do WebP animado, se já gerada em cache_sprites/ (anim_sprites.py):
        <nome> (CIAS) ou <pasta da apresentação>__<nome> (slide). {} = toca como hoje (WebP ou MP4)."""
        if os.environ.get("NATIVO_ANIM_FORMATO") != "B" or not caminho:
            return {}
        if caminho.startswith("file:"):
            caminho = QUrl(caminho).toLocalFile()
        return folha_de(caminho)
        base = os.path.splitext(os.path.basename(caminho))[0]
        raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_sprites")
        for nome in (os.path.basename(os.path.dirname(caminho)) + "__" + base, base):
            d = os.path.join(raiz, nome)
            if os.path.exists(os.path.join(d, "sprites.json")):
                try:
                    j = json.load(open(os.path.join(d, "sprites.json"), encoding="utf-8"))
                except Exception:
                    return {}
                u = lambda f: QUrl.fromLocalFile(os.path.join(d, f)).toString()
                return dict(j, fundo=u("fundo.png"), folha=u("folha.png"))
        return {}

    @Slot(str, result="QVariant")
    def ritmoAnim(self, caminho):
        """Os atrasos de cada quadro do slide animado (ms), para o QML andar no passo do arquivo."""
        if caminho.startswith("file:"):
            caminho = QUrl(caminho).toLocalFile()
        self._animada(caminho)
        return self.__dict__.get("_anim_cache", {}).get(caminho, [])

    @Slot(str, result="QVariant")
    def buscarSlides(self, q):
        """A busca da coluna do MODO APRESENTAÇÃO (aprBuscar do app.js): número = aquele slide; palavras = os slides cujo
        texto tem TODAS (ou o trecho junto, sem espaços). Devolve {achados: [k], sem: "mensagem" ou ""}."""
        t = cerebro.sem_acento(q or "").lower().strip()
        if not self.ap or not t:
            return {"achados": [], "sem": "", "busca": False}
        n = len(self.ap["slides"])
        if t.isdigit():
            k = int(t) - 1
            return {"achados": [k], "sem": "", "busca": True} if 0 <= k < n else {"achados": [], "sem": "São %d slides." % n, "busca": True}
        textos = self.ap.get("textos") or []
        palavras, junto = t.split(), re.sub(r"\s+", "", t)
        ach = []
        for i in range(n):
            tx = cerebro.sem_acento((textos[i] if i < len(textos) else "") or "").lower()
            if tx and (all(p in tx for p in palavras) or junto in re.sub(r"\s+", "", tx)):
                ach.append(i)
        sem = "" if ach else ("Nenhum slide com essa palavra." if any(textos) else
                              "Esta apresentação não tem o texto gravado. Procure pelo número do slide.")
        return {"achados": ach, "sem": sem, "busca": True}

    @Slot(str, "QVariant", result="QVariant")
    def cfgLer(self, k, padrao):
        """O Guardar.ler da 3.0.13 (a mesma chave, no nativo.json por cima da configuracoes.json)."""
        v = self.A.config.ler(k)
        return padrao if v is None else v

    @Slot(str, "QVariant")
    def cfgGravar(self, k, v):
        self.A.config.gravar(k, v)

    # ---- MEUS LOUVORES (Configurações › Meus louvores): o editor do app.js, na mesma chave icm_meus_louvores
    @Slot(result="QVariantList")
    def meusLouvores(self):
        """A lista do renderMeus: [{num, titulo}] na ordem guardada."""
        return [{"num": s.get("num") or "", "titulo": s.get("titulo") or ""} for s in self.A.meus()]

    @Slot(int, result="QVariant")
    def meuParaEditar(self, i):
        """O ✎: os campos do editor (o nº some quando é "MEU"; a letra volta com os rótulos e a linha em branco)."""
        m = self.A.meus()
        if not 0 <= i < len(m): return {}
        s = m[i]
        letra = "\n\n".join(((sl.get("label") + "\n") if sl.get("label") else "") + "\n".join(sl.get("linhas") or [])
                             for sl in s.get("slides") or [])
        return {"num": "" if s.get("num") == "MEU" else (s.get("num") or ""), "titulo": s.get("titulo") or "", "letra": letra}

    @Slot(int, str, str, str, result=str)
    def salvarMeu(self, editando, num, titulo, letra):
        """O salvarLouvorEditor: devolve o recado ("Louvor salvo." ou o que falta). editando = -1 acrescenta."""
        tit, letra = titulo.strip(), letra.strip()
        if not tit: return "Informe o título do louvor."
        if not letra: return "Informe a letra do louvor."
        slides = cerebro.parse_letra(letra)
        if not slides: return "Não foi possível interpretar a letra."
        novo = {"titulo": tit.upper(), "num": (num.strip() or "MEU").upper(), "col": "Meus louvores", "slides": slides, "meu": True}
        m = list(self.A.config.ler("icm_meus_louvores") or [])
        if 0 <= editando < len(m): m[editando] = novo
        else: m.append(novo)
        self._gravar_meus(m)
        return "Louvor salvo."

    @Slot(int, result=str)
    def apagarMeu(self, i):
        m = list(self.A.config.ler("icm_meus_louvores") or [])
        if not 0 <= i < len(m): return ""
        del m[i]
        self._gravar_meus(m)
        return "Louvor removido."

    def _gravar_meus(self, m):
        self.A.config.gravar("icm_meus_louvores", m)
        self.A.recarregar_meus()
        self.acervoMudou.emit()

    @Slot(int, result="QVariant")
    def painelCulto(self, dias):
        """Configurações › Painel: o histórico (o MESMO historico.json da 3.0.13) contado como o pintarPainel dela."""
        try:
            sys.path.insert(0, cerebro.APP) if cerebro.APP not in sys.path else None
            import sistema as S
            regs = S.ler_historico()
        except Exception:
            regs = []
        return painel_culto(regs, dias)

    @Property(bool, notify=mudou)
    def animAuto(self):
        """Configurações › Sistema: "Louvores das CIAS abrem com a tela animada" (o animAuto da 3.0.13)."""
        return self.A.config.ler("icm_anim_auto", True) is not False

    @Slot()
    def alternarAnimAuto(self):
        """O alternarAnimAuto: grava, vale já para o próximo louvor escolhido, e o recado."""
        novo = not self.animAuto
        self.A.config.gravar("icm_anim_auto", novo)
        self.anim_ligada = novo
        self.mudou.emit()
        self.aviso.emit("Louvor das CIAS abre com a animação." if novo else "Louvor das CIAS abre como texto.")

    # ---- RESTAURAR (Configurações › Sistema › Restaurar): o aplicarReset da 3.0.13
    @Slot(str, result=str)
    def restaurar(self, o):
        """'apagados': os fundos e a apresentação de exemplo escondidos voltam (o do operador fica). 'tamanhos': A−/A+ e a
        letra da folha da cifra ao padrão. 'tudo': cópia de segurança conferida, apaga o que o operador criou e reabre.
        Devolve o texto do passo "Pronto" (ou o recado)."""
        if o == "apagados":
            self.A.config.gravar("icm_ocultos", [])
            self.A.config.gravar("icm_ap_ocultas", [])
            self._fundos_mudaram(); self.apresMudou.emit(); self.mudou.emit()
            self.aviso.emit("Pronto: o que veio com o Sistema voltou. O que você acrescentou continua.")
            return "O que veio com o Sistema voltou. O que você acrescentou continua lá."
        if o == "tamanhos":
            for k in self.escala: self.escala[k] = 1.0
            self.A.config.gravar("icm_cifra_fonte", 14)
            self.mudou.emit()
            self.aviso.emit("Configurações restauradas ao padrão.")
            return "Os tamanhos de letra voltaram ao padrão."
        if o == "tudo":
            try:
                copia, _ = restaurar_tudo_com_copia(self.A.config.pasta)
            except Exception as e:
                self.aviso.emit("Não restaurei: " + str(e)); return ""
            self.aviso.emit("Restaurando… a cópia de segurança ficou em " + copia + ". O Sistema vai fechar e abrir sozinho.")
            if not os.environ.get("NATIVO_SEM_REABRIR"):     # provas: não reabre
                from PySide6.QtCore import QProcess
                QTimer.singleShot(1500, lambda: (QProcess.startDetached(sys.executable, sys.argv), QGuiApplication.quit()))
            return copia
        return ""

    # ---- SUGESTÕES DE LOUVOR para o versículo no ar (sugestoes.py: cópia do app.js da 3.0.13)
    def _sug_obj(self):
        if getattr(self, "_sug", None) is None:
            import sugestoes
            def hist():
                sys.path.insert(0, cerebro.APP) if cerebro.APP not in sys.path else None
                import sistema as S
                return S.ler_historico()
            self._sug = sugestoes.Sugestoes(self.A, self.B, hist)
        return self._sug

    def preparar_sugestoes(self):
        """Lê a tabela, o histórico e o índice temático numa linha de fundo ao abrir (~300 ms no PC de casa): o primeiro
        versículo do culto não espera por eles."""
        def ler():
            try:
                import sugestoes
                s = self._sug_obj()
                if s.tab is None: s.tab = sugestoes._js("sugestoes.js", "SUGESTOES")
                s._historico(); s._temas(); s.normas()
            except Exception as e:
                print("sugestões (fundo):", e, flush=True)
        threading.Thread(target=ler, name="sugestoes", daemon=True).start()

    def _sugerir(self, livro, cap, v):
        try:
            self._sug_vis = bool(self._sug_obj().sugerir(livro, cap, v))
        except Exception as e:
            print("sugestões:", e, flush=True); self._sug_vis = False
        self.sugMudou.emit()

    @Property("QVariant", notify=sugMudou)
    def sugestoes(self):
        """{visivel, mais, trio: [{i, num, sigla, titulo}]} (o pintarSug)."""
        if not getattr(self, "_sug_vis", False):
            return {"visivel": False, "mais": False, "trio": []}
        trio, mais = self._sug_obj().trio()
        return {"visivel": True, "mais": mais,
                "trio": [{"i": i, "num": cerebro.num_louvor(self.A.louvores[i]) or "—",
                          "sigla": cerebro.SIGLA_COL.get(self.A.louvores[i].get("col"), ""),
                          "titulo": self.A.louvores[i]["titulo"]} for i in trio]}

    @Slot(QObject, float)
    def linhaFixa(self, doc, altura):
        """O line-height do <textarea> no TextEdit (que não tem a propriedade): cada parágrafo do documento com a altura
        FIXA da linha do navegador (13,5 x 1,6 = 21,6 px, na escala ampliada do campo). Só mexe no que ainda não está
        certo (mexer no formato avisa "mudou" de novo: sem isso entraria em laço)."""
        from PySide6.QtGui import QTextBlockFormat, QTextCursor
        try:
            d = doc.textDocument()
        except Exception:
            return
        b = d.begin()
        while b.isValid():
            f = b.blockFormat()
            if f.lineHeightType() != 2 or abs(f.lineHeight() - altura) > 0.01:      # 2 = FixedHeight
                f.setLineHeight(altura, 2)
                QTextCursor(b).setBlockFormat(f)
            b = b.next()

    @Slot(int, result=int)
    def daVez(self, i):
        """A cópia (número antigo/avulso) abre a principal: uma letra só (o daVez da 3.0.13)."""
        return self.A.da_vez(i) if 0 <= i < len(self.A.louvores) else i

    @Slot()
    def maisSugestoes(self):
        self._sug_obj().mais(); self.sugMudou.emit()

    # ---- ATUALIZAR (08/11/2026): o verificarAtualizacao da 3.0.13, frase por frase, contra a release PRINCIPAL; o Sistema
    # 4.0 compara pelo número (atualizador.py). Mudam só as coisas da 3.0.13 que dependiam do servidor web.
    @Slot()
    def verificarAtualizacao(self):
        self._verificar(False)

    def verificar_ao_abrir(self):
        """ligarAtualizacao da 3.0.13: com o atu_auto ligado, 5 s depois de abrir, procura em SILÊNCIO (sem internet: nada)."""
        if self.A.config.ler("atu_auto", True) is not False:
            self._verificar(True)

    def _verificar(self, silenciosa):
        def ver():
            try:
                import atualizador as U
                r = U.verificar()
                if not r.get("ok"):
                    if not silenciosa:
                        self.atualizacao.emit("Sem internet agora. O Sistema segue funcionando normal.")
                    return
                if not r["tem"]:
                    # a melhor versão de todas, atualizada E completa, veste ouro (palavra dele, 10/10/2026)
                    if U.conteudo_completo():
                        self.atualizacao.emit("Você está com a melhor versão do Sistema: completa e atualizada (%s)." % r["atual"])
                        self.atuMelhor.emit(True)
                    elif not silenciosa:
                        self.atualizacao.emit("Você já está na versão mais nova (%s)." % r["atual"])
                        self.atuMelhor.emit(False)
                    return
                self.atualizacao.emit("Existe a versão %s (você está na %s)." % (r["nova"], r["atual"]))
                if silenciosa:
                    self.aviso.emit("Há uma versão nova do Sistema (%s) — veja em Configurações › Sistema." % r["nova"])
                    return
                self.atuNova.emit(r["nova"], r["atual"], int(round(r.get("bytes", 0) / 1048576.0)))
            except Exception as e:
                if not silenciosa:
                    self.atualizacao.emit("Não consegui verificar agora: " + str(e)[:80])
        threading.Thread(target=ver, name="atualizacao", daemon=True).start()

    @Slot(result=bool)
    def conexaoLimitada(self):
        """O avisoConexao da 3.0.13: a internet é limitada (celular, franquia)? O Windows responde (WinRT), 60 s de cache."""
        try:
            sys.path.insert(0, cerebro.APP) if cerebro.APP not in sys.path else None
            import sistema as S
            return bool(S.conexao_limitada().get("limitada"))
        except Exception:
            return False

    @Slot()
    def atualizarAgora(self):
        """O "Atualizar agora" do Confirmar: o _atualizar_thread da 3.0.13. Baixa (com %), roda o instalador com
        --silencioso --reabrir e, se ele seguir vivo 3 s depois, o Sistema fecha (o instalador reabre no fim)."""
        def vai():
            import atualizador as U
            def andamento(pct, txt):
                self.atualizacao.emit(txt + (" — %d%%" % pct if pct else ""))
            try:
                alvo = U.baixar(andamento)
                if U.linux():                       # o Vaio: troca o CÓDIGO no lugar (0,8 MB) e reabre pelo lançador
                    r = U.instalar_linux(alvo, andamento)
                    print("atualização no Linux:", r, flush=True)
                    try:                            # os dados à parte, só se algum md5 mudou (o código já trocou)
                        print("dados no Linux:", U.atualizar_dados_linux(andamento), flush=True)
                    except Exception as e:
                        print("dados no Linux: não troquei (%s)" % str(e)[:120], flush=True)
                    andamento(100, "Pronto. O Sistema vai reabrir sozinho…")
                    U.reabrir_linux()
                    time.sleep(1.5)
                    self.sairParaAtualizar.emit()
                    return
                andamento(96, "Abrindo o instalador…")
                inst = U.rodar_instalador(alvo)
                self.atualizacao.emit("Fechando o Sistema para instalar a versão nova…")
                time.sleep(3)
                if inst is None or inst.poll() is None:
                    self.sairParaAtualizar.emit()
                else:
                    self.atualizacao.emit("O instalador fechou antes da hora. Tente de novo, ou rode o instalador baixado.")
            except Exception as e:
                self.atualizacao.emit("Não consegui baixar a versão nova agora: " + str(e)[:80])
        threading.Thread(target=vai, name="atualizar", daemon=True).start()

    # ---- DESINSTALAR (Configurações › Sistema): desfaz o que o instalador anotou no instalacao.json
    @Slot(bool, result=str)
    def desinstalar(self, apagar_tudo):
        """Escreve um roteiro que roda DEPOIS que o Sistema fechar (um programa aberto não apaga a própria pasta): tira as
        regras do Firewall, os atalhos e a pasta do programa; os dados do operador só com "Apagar tudo". A pasta de dados é
        a MESMA da 3.0.13: com ela ainda instalada, o "Apagar tudo" do nativo leva só os arquivos do nativo.
        Provas: NATIVO_PROG (a pasta do programa), NATIVO_PROG_312 (a da 3.0.13), NATIVO_NETSH_ENSAIO e
        NATIVO_DESINSTALAR_ENSAIO=1 (roda o roteiro na hora, sem esperar, sem elevar e sem fechar)."""
        prog = os.environ.get("NATIVO_PROG") or (os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else "")
        reg_arq = os.path.join(prog, "instalacao.json") if prog else ""
        if not reg_arq or not os.path.exists(reg_arq):
            self.aviso.emit("Este Sistema não foi instalado pelo instalador (está rodando do código): nada a desinstalar.")
            return ""
        reg = json.load(open(reg_arq, encoding="utf-8"))
        ensaio = os.environ.get("NATIVO_DESINSTALAR_ENSAIO") == "1"
        linhas = ["@echo off", "chcp 65001 >nul"]
        if not ensaio:                                    # espera o Sistema fechar
            linhas += [":esperar", 'tasklist /fi "imagename eq SistemaNativo.exe" | find /i "SistemaNativo.exe" >nul',
                       "if not errorlevel 1 (timeout /t 1 /nobreak >nul & goto esperar)"]
        fw = ['netsh advfirewall firewall delete rule name="%s"' % n for n in reg.get("regras") or []]
        if os.environ.get("NATIVO_NETSH_ENSAIO"):
            with open(os.environ["NATIVO_NETSH_ENSAIO"], "a", encoding="utf-8") as f: f.write("\n".join(fw) + "\n")
        else:
            linhas += [l + " >nul" for l in fw]
        linhas += ['del /q "%s" 2>nul' % a for a in reg.get("atalhos") or []]
        linhas.append('rmdir /s /q "%s"' % reg["programa"])
        o_que = "O programa, os atalhos e as regras do Firewall saem; as suas coisas ficam guardadas."
        if apagar_tudo:
            p312 = os.environ.get("NATIVO_PROG_312") or os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Sistema")
            dados = self.A.config.pasta
            if os.path.isdir(p312):                        # a 3.0.13 usa a mesma pasta: só o que é do nativo
                linhas += ['del /q "%s" 2>nul' % os.path.join(dados, "nativo.json"),
                           'rmdir /s /q "%s" 2>nul' % os.path.join(dados, "nativo_fundos")]
                o_que = "A 3.0.13 ainda está instalada e usa a mesma pasta de dados: saem só os arquivos do Sistema Nativo."
            else:
                linhas.append('rmdir /s /q "%s"' % dados)
                o_que = "Saem o programa, os atalhos, as regras do Firewall e as suas coisas."
        linhas.append('(goto) 2>nul & del "%~f0"')      # o roteiro some depois de rodar
        cmd = os.path.join(tempfile.mkdtemp(prefix="nativo_saida_"), "desinstalar.cmd")
        with open(cmd, "w", encoding="utf-8") as f: f.write("\r\n".join(linhas) + "\r\n")
        if ensaio:
            subprocess.run(["cmd", "/c", cmd], capture_output=True, timeout=60, creationflags=0x08000000)
        else:
            ps = "Start-Process -FilePath cmd.exe -ArgumentList '/c \"%s\"' -Verb RunAs -WindowStyle Hidden" % cmd
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps], creationflags=0x08000000)
            QTimer.singleShot(1500, QGuiApplication.quit)
        self.aviso.emit("Desinstalando… " + o_que)
        return o_que

    @Slot("QVariant")
    def gravarIgreja(self, v):
        """O salvarIgreja + aplicarNomeIgreja da 3.0.13: a mesma chave icm_igreja, e o nome no cabeçalho troca na hora."""
        self.A.config.gravar("icm_igreja", v)
        self._av_cel = (None, [])                               # os avisos do celular se refazem já com a agenda nova
        self.mudou.emit()

    @Slot(str)
    def importarApresentacao(self, url):
        caminho = QUrl(url).toLocalFile() if url.startswith("file:") else url
        self.aviso.emit("Convertendo a apresentação… (o PowerPoint trabalha escondido)")
        def trabalho():
            try: r = cerebro.importar_apresentacao(caminho)
            except Exception as e: r = {"ok": False, "erro": str(e)}
            self.importou.emit(r)
        threading.Thread(target=trabalho, name="importar", daemon=True).start()

    def _importou(self, r):
        if not r or not r.get("ok"):
            self.aviso.emit("Não consegui abrir: " + str((r or {}).get("erro") or "arquivo estranho")); return
        L = self.listaApres(de_novo=True)
        self.apresMudou.emit()
        # o importar() da 3.0.12 devolve o nome do ARQUIVO ("CLAMO, Ó SENHOR"), mas grava a pasta com o que não é letra
        # trocado por "_" ("CLAMO_ Ó SENHOR"); a lista vem da pasta
        pasta = "".join(c if c.isalnum() or c in " -_" else "_" for c in (r.get("nome") or ""))
        k = next((n for n, a in enumerate(L) if a["nome"] in (pasta, r.get("nome")) and not a["demo"]), -1)
        self.aviso.emit("Apresentação pronta: %d telas." % len(r.get("slides") or []))
        if k >= 0: self.entrarApresentacao(k, 0)

    # ---- A TV DE RETORNO (os gestinhos, para a irmã que puxa os gestos): o mesmo modoDe/pintaApres do retorno.html
    # da 3.0.12. Espera = relógio; apresentação com tabela de gestos = AGORA + A SEGUIR; louvor com gesto = o gesto;
    # o resto = o espelho do telão.
    def _tab_gestos(self):
        if getattr(self, "_G", None) is None:
            self._G = cerebro.gestos()
        return self._G

    @staticmethod
    def _url(p):
        return QUrl.fromLocalFile(p).toString() if p else ""

    def _cartao_gesto(self, g, titulo=""):
        grupos = []
        for f in g.get("figs") or []:            # figuras seguidas com a mesma legenda: lado a lado, legenda uma vez
            if grupos and grupos[-1]["txt"] == f.get("txt") and len(grupos[-1]["imgs"]) < 2:
                grupos[-1]["imgs"].append(self._url(f["img"])); grupos[-1]["rs"].append(f.get("r") or 1)
            else:
                grupos.append({"txt": f.get("txt") or "", "imgs": [self._url(f["img"])], "rs": [f.get("r") or 1]})
        if grupos:
            return {"tipo": "figs", "grupos": grupos, "titulo": titulo, "k": "f:" + (g.get("img") or "") + titulo}
        return {"tipo": "img", "url": self._url(g.get("img")), "k": "i:" + (g.get("img") or "")}

    def _cartao_slide(self, n):
        # 10/11 (banco no Vaio): o cartão abria o WebP ORIGINAL (2x, síncrono, na linha da interface: o fundo desfocado e o
        # slide) e cada troca travava o painel 260-590 ms; o .jpg leve (o mesmo das prévias) abre já encolhido
        if self.ap and "mostra" not in self.ap:
            levar(self.ap)
        u = self._url(self.ap["mostra"][n]) if self.ap and 0 <= n < len(self.ap["slides"]) else ""
        return {"tipo": "slide", "url": u, "k": "s:" + u}

    def _proximo_louvor(self):
        for x in self.fila[max(-1, self.pos) + 1:]:
            if x["tipo"] == "louvor":
                return x.get("rotulo") or ""
        return ""

    @Slot(result="QVariant")
    def retorno(self):
        G = self._tab_gestos()
        if self.vivo in ("", "espera"):
            return {"modo": "relogio", "oque": "tela de espera"}
        if self.vivo == "apres" and self.ap and ("apres:" + self.ap["nome"]) in G:
            t, n, total = G["apres:" + self.ap["nome"]], self.ap_pos, len(self.ap["slides"])
            g = t.get(str(n))
            agora = {"rot": "Agora" if g else "Agora · slide %d de %d" % (n + 1, total),
                     "card": self._cartao_gesto(g) if g else self._cartao_slide(n)}
            prox = t.get(str(n + 1))
            if n + 1 >= total:
                seg = {"rot": "A seguir", "card": {"tipo": "texto", "txt": "Fim da apresentação", "k": "fim"}}
            elif prox:
                outro = not g or prox.get("louvor") != g.get("louvor")
                seg = {"rot": "Próximo louvor" if outro else "A seguir",
                       "card": self._cartao_gesto(prox, prox.get("louvor", "") if outro else "")}
            else:
                seg = {"rot": "A seguir · slide %d de %d" % (n + 2, total), "card": self._cartao_slide(n + 1)}
                # 13/11 (o esboço B, escolha dele): embaixo da prévia pequena, o PRÓXIMO LOUVOR com gestos e quanto falta
                atual = (g or {}).get("louvor")
                for j in range(n + 2, total):
                    gj = t.get(str(j))
                    if gj and gj.get("louvor") and gj.get("louvor") != atual:
                        seg["prox"] = {"nome": gj["louvor"], "em": j - n}; break
            return {"modo": "gestos", "agora": agora, "seguir": seg,
                    "oque": (g or {}).get("louvor") or self.ap["nome"]}
        if self.vivo == "louvor" and 0 <= self.idx < len(self.A.louvores):
            # 14/11 (pedido dele: "até no modo só o louvor normal (...) funcione tela de retorno dos gestinhos"): os gestos
            # das apresentações valem para o MESMO louvor projetado sozinho (ferramentas/gestos_dos_louvores.py casa cada
            # tela com o gesto pela letra). A conta das telas muda com o jeito de projetar: as telas 16:9 das CIAS têm a
            # tabela "louvor169:"; as estrofes em letra, a "louvor:"; a tela 4:3 animada não tem (fica o espelho).
            ch = cerebro.chave(self.A.louvores[self.idx])
            if self.anim_ligada and self.A.cias169(self.idx):
                t = G.get("louvor169:" + ch) or {}
            elif self.anim_ligada and self.A.tem_telas_cias(self.A.da_vez(self.idx)):
                t = {}
            else:
                t = G.get("louvor:" + ch) or {}
            g = t.get(str(self.slide))
            if g:
                prox = t.get(str(self.slide + 1))
                px = self._proximo_louvor()
                seg = ({"rot": "A seguir", "card": self._cartao_gesto(prox)} if prox else
                       {"rot": "Próximo louvor", "card": {"tipo": "texto", "sub": "Próximo louvor", "txt": px, "k": "l:" + px}} if px else None)
                return {"modo": "gestos", "agora": {"rot": "Agora", "card": self._cartao_gesto(g)}, "seguir": seg,
                        "oque": g.get("louvor") or self.A.rotulo(self.idx)}
        return {"modo": "espelho", "oque": self._no_ar}

    # ---- relógio, cronômetro e aviso (o fundo "plano" do app.js: o louvor2 do estilo, com a faixa)
    def _plano(self):
        return self.A.fundo(self.estilo, "louvor2")

    @Slot()
    def relogio(self):
        self.vivo = "relogio"
        self._no_ar = "relógio"
        self._manda({"modo": "relogio", "fundo": self._plano(), "fade": 400})

    @Slot(float, str)
    def cronometro(self, minutos, rotulo):
        self.vivo = "timer"
        self.timer = {"fimTs": time.time() * 1000 + max(0.1, minutos) * 60000, "rotulo": rotulo}
        self._no_ar = "cronômetro %g min%s" % (minutos, (" · " + rotulo) if rotulo else "")
        self._manda({"modo": "timer", "fundo": self._plano(), "rotulo": rotulo, "fimTs": self.timer["fimTs"], "fade": 500})

    @Slot(str, str)
    def texto(self, titulo, corpo):
        linhas = [l.strip() for l in (corpo or "").splitlines() if l.strip()]
        if titulo.strip():
            linhas.insert(0, chr(1) + titulo.strip() + chr(1))      # o título sai amarelo (marcador \x01)
        if not linhas:
            return
        self.vivo = "texto"
        self._no_ar = "aviso: " + (titulo.strip() or linhas[0])[:40]
        self._manda({"modo": "texto", "fundo": self._plano(), "linhas": linhas, "zona": "barra", "tam": 6, "escala": 1, "fade": 400})

    # ---- Bíblia
    def _bib(self, livro, cap, v):
        self.bib = (livro, cap, v)
        self.vivo = "biblia"
        self._no_ar = "%s %d:%d" % (livro, cap, v)
        self.abrir_no_ar("verso", "%s %d:%d" % (livro, cap, v), "v|%s|%d|%d" % (livro, cap, v))
        self._sugerir(livro, cap, v)          # o sugerirPara do projetarVerso: louvores que combinam com este versículo
        self._manda(self.B.tela(livro, cap, v, self.estilo, self.escala["biblia"]))

    @Slot(str, result=bool)
    def biblia(self, texto):
        r = self.B.ler(texto) if self.B else None
        if not r:
            return False
        self._verso_solto(*r)
        return True

    # ---- A+ / A- (8% por toque, entre 60% e 180%) e congelar
    def _reprojeta(self):
        if self.vivo == "louvor": self.projetar(self.idx, self.slide)
        elif self.vivo == "biblia" and self.bib: self._bib(*self.bib)
        elif self.vivo == "bibmulti": self.projetarJuntos()

    def _chave_esc(self):
        """Os versículos Juntos usam o MESMO A+/A- da Bíblia (escalaVers do app.js)."""
        return "biblia" if self.vivo == "bibmulti" else self.vivo

    @Slot(int)
    def tamanho(self, passo):
        k = self._chave_esc() if self._chave_esc() in self.escala else None
        if not k:
            return
        self.escala[k] = 1.0 if passo == 0 else max(0.6, min(1.8, round(self.escala[k] * (1.08 if passo > 0 else 1 / 1.08), 3)))
        self._reprojeta()

    @Property(str, notify=mudou)
    def rotuloTamanho(self):
        e = self.escala.get(self._chave_esc())
        if e is None: return ""
        return "Padrão" if abs(e - 1) < 0.005 else "%+d%%" % round((e - 1) * 100)

    @Property(bool, notify=mudou)
    def congeladoAgora(self):
        return self.congelado

    @Slot(bool)
    def congelar(self, sim):
        if sim == self.congelado:
            return
        self.congelado = sim
        if not sim:
            self.tela.emit(self.ultimo)          # descongelou: o telão pega o que está no painel
        self.mudou.emit()

    @Slot(bool)
    def ligarAnimacao(self, sim):
        self.anim_ligada = sim
        if self.idx >= 0 and self._no_ar.startswith(self.A.rotulo(self.idx)):
            self.projetar(self.idx, 0 if sim != self.anim_ligada else self.slide)
        self.mudou.emit()

    # ---- ESCOLHER A TELA (07/11/2026): o abrirProjecao/esperarProjetor da 3.0.12 e o vigia do sistema.py, sem navegador.
    # Regra dele (18/10 11h58): O TELÃO NUNCA NA CARA DO OPERADOR. Com 2 telas o telão vai para a que não é a principal,
    # em tela cheia; com 3, a terceira é a TV de retorno. Com UMA tela o telão fica escondido e, quando o operador põe algo
    # no ar, abre o cartão "Projetor não encontrado" (as palavras da 3.0.12). O HDMI que chega leva o telão para ele
    # sozinho; o que sai esconde o telão (o Windows o jogaria na tela do operador). Nunca chama o "estender" sozinho
    # (ele, 25/10 15h43): só quando o operador clica em "Procurar novamente".
    def posicionar(self, *_):
        self._posicionando = True              # o hide()/show() daqui não é o operador fechando a janela (B9)
        try:
            self._posicionar()
        finally:
            self._posicionando = False

    def telaoVisivel(self, visivel):
        """B9 (relato dele 07/11 21h16): sem projetor, depois do "Continuar assim" (ensaio numa janela), FECHAR a janela
        do telão deixava o ensaio ligado para sempre: o Projetar "fingia que projetava" numa janela escondida e nunca mais
        perguntava. Agora fechar a janela desfaz o ensaio: o próximo Projetar pergunta de novo, como na 3.0.13."""
        if not visivel and self.seguindo and not getattr(self, "_posicionando", False):
            print("tela secundária: janela fechada, saindo", flush=True)
            QGuiApplication.quit(); return               # fechar a janela da tela secundária encerra o modo
        if not visivel and self.ensaio and self.sem_projetor and not getattr(self, "_posicionando", False):
            self.ensaio = False
            self.descanso()
            self.telasMudou.emit()

    def _posicionar(self):
        tw, rj = self._telao, self._retjan
        if tw is None:
            return
        if self._forcar_janela:
            self._onde = "em janela (teste)"; self.telasMudou.emit(); return
        telas = QGuiApplication.screens()
        prim = QGuiApplication.primaryScreen()
        # NOTEBOOK (o Vaio, 01/11 em Araçoiaba): o autostart dele põe a HDMI como PRINCIPAL, e "o telão na que não é a
        # principal" mandou o telão para a tela do próprio notebook. Pela SAÍDA: a interna (LVDS/eDP) é a do operador e
        # a externa é o telão, seja qual for a principal; com a TAMPA FECHADA a interna não conta (ninguém a vê).
        # No Windows o nome não diz qual é a interna ("\\.\DISPLAY2"): lá vale a regra de sempre (a não principal).
        internas = [s for s in telas if _tela_interna(s.name())]
        if internas and _tampa_fechada():
            telas = [s for s in telas if s not in internas]; internas = []
            if prim not in telas and telas: prim = telas[0]
        externas = [s for s in telas if s not in internas]
        if internas and externas:
            prim = internas[0]                           # o painel fica na tela do notebook
            if self._painel is not None and self._painel.screen() is not prim:
                self._painel.setScreen(prim); self._painel.setGeometry(prim.availableGeometry()); self._painel.showMaximized()
        outras = [s for s in telas if s is not prim]
        outras.sort(key=lambda s: _tela_interna(s.name()))   # externa antes de interna
        # TAMPA FECHADA com UMA tela de fora (ele, 13/11: "fechar o computador e controlar pelo celular; a saída do HDMI
        # se torna a tela de projeção"): essa tela É o telão; o painel fica por baixo e o controle vai para o celular.
        # Medido 13/11 13h06 no Vaio (boot de tampa fechada, cabo real): caía em "nenhum projetor ligado" e escondia.
        so_fora = (not outras and len(telas) == 1 and sys.platform.startswith("linux")
                   and not _tela_interna(telas[0].name()) and _tampa_fechada())
        if so_fora:
            outras = [telas[0]]
        # TELA SECUNDÁRIA (13/11, seguir.py): este computador inteiro é a tela; com uma tela só, é nela
        if self.seguindo and not outras and telas:
            outras = [prim if prim in telas else telas[0]]
        if outras:
            alvo = outras[0]
            if self.telao_fechado:                       # fechado pelo celular: fica fechado até o "Abrir telão"
                if tw.isVisible(): tw.hide()
                self._onde = "fechado (Fechar telão)"
                print("telão:", self._onde, flush=True); self.telasMudou.emit(); return
            veio = self.sem_projetor or self.ensaio
            if tw.screen() is not alvo or not tw.isVisible() or veio:
                tw.hide(); tw.setScreen(alvo); tw.setGeometry(alvo.geometry()); tw.showFullScreen()
                if self.seguindo: _por_na_frente(tw); tw.requestActivate()   # a tela secundária é a tela: na frente de tudo
                self.tela.emit(self.ultimo)              # a janela que reaparece pega o que está no ar
            self.sem_projetor = self.ensaio = self.aviso_proj = self._aviso_ja = False
            self._onde = "na tela %s (%dx%d)" % (alvo.name(), alvo.geometry().width(), alvo.geometry().height())
            if so_fora: self._onde += " · tampa fechada: controle pelo celular"
            if self.quadros is not None:                 # os quadros animados no tamanho DESTE telão (1366 na igreja)
                self.quadros.largura_cheia = max(1280, int(alvo.geometry().width() * alvo.devicePixelRatio()))
            if veio: self.aviso.emit("Projetor detectado — projetando em tela cheia.")
            terc = outras[1] if len(outras) > 1 else None
            if rj is not None and terc is not None:
                rj.setScreen(terc); rj.setGeometry(terc.geometry()); rj.showFullScreen()
            elif rj is not None and os.environ.get("NATIVO_RETORNO") != "janela" and rj.isVisible():
                rj.hide()                                # a 3ª tela saiu: a TV de retorno não cai na tela do operador
        else:
            self.sem_projetor = True
            if self.ensaio:
                if tw.visibility() == QWindow.Visibility.FullScreen or not tw.isVisible():
                    tw.hide(); tw.setScreen(prim); tw.resize(960, 540); tw.showNormal()
                    self.tela.emit(self.ultimo)
                self._onde = "numa janela nesta tela (ensaio)"
            else:
                if tw.isVisible(): tw.hide()
                self._onde = "escondido: nenhum projetor ligado"
            if rj is not None and os.environ.get("NATIVO_RETORNO") != "janela" and rj.isVisible():
                rj.hide()
        print("telão:", self._onde, "· telas:", [s.name() for s in telas], flush=True)
        self.telasMudou.emit()

    @Property(bool, notify=telasMudou)
    def telaoFechado(self):
        return self.telao_fechado

    @Slot()
    def abrirTelao(self):
        """O "Abrir telão" (o abrirprojecao da 3.0.x, pelo celular ou pelo botão). Na 3.0.12 ele CRIA uma janela nova de
        tela cheia (WebView2 nascendo preta e carregando o projecao.html: os ~3-5 s de preto que ele viu no culto de
        08/11); aqui a janela do telão já existe, com a tela desenhada: só aparece. E vem para a FRENTE de quem estiver
        na tela do projetor (o Glorifica), sem roubar o foco do operador."""
        self.telao_fechado = False
        if self._forcar_janela and self._telao is not None:          # teste (--janela): a janela do telão, na frente
            self._telao.show(); self.tela.emit(self.ultimo); _por_na_frente(self._telao); self.telasMudou.emit(); return
        if self.sem_projetor and not self.ensaio:
            self.telasMudou.emit(); self.mostrarAvisoProjetor(); return
        self.posicionar()
        tw = self._telao
        if tw is not None and tw.isVisible():
            self.tela.emit(self.ultimo)
            _por_na_frente(tw)

    @Slot()
    def fecharTelao(self):
        """O "Fechar telão" (fecharprojecao): a janela some e devolve a tela a quem estava atrás (o Glorifica)."""
        self.telao_fechado = True
        if self._forcar_janela and self._telao is not None:          # teste (--janela)
            self._posicionando = True
            try: self._telao.hide()
            finally: self._posicionando = False
            self.telasMudou.emit(); return
        self.posicionar()

    @Property(str, notify=telasMudou)
    def telaoOnde(self):
        return self._onde

    @Property(bool, notify=telasMudou)
    def semProjetor(self):
        return self.sem_projetor and not self.ensaio

    @Property(bool, notify=telasMudou)
    def avisoProjetor(self):
        return self.aviso_proj

    # ---- este computador como TELA SECUNDÁRIA de outro Sistema (13/11, seguir.py)
    @Property(bool, notify=telasMudou)
    def ehSecundaria(self):
        return self.seguindo

    @Property(str, notify=telasMudou)
    def textoSecundaria(self):
        return self.seguindo_texto

    @Property(str, notify=telasMudou)
    def nomeSecundaria(self):
        return getattr(getattr(self, "_seguidor", None), "nome", "")

    # ao abrir, o ouvido achou outro Sistema na rede: "Ser a tela secundária" ou "Projetar daqui"
    @Property(str, notify=telasMudou)
    def outroPrincipal(self):
        return self.outro_principal.get("nome", "")

    def _lembrar_principal(self, nome, sim):
        if os.environ.get("NATIVO_AUTO_SECUNDARIA") or os.environ.get("NATIVO_LEMBRADOS") is not None:
            return                               # testes: nada é gravado na configuração de verdade
        try:
            L = [x for x in (self.A.config.ler("icm_secundaria_de", []) or []) if x != nome]
            if sim: L.append(nome)
            self.A.config.gravar("icm_secundaria_de", L)
        except Exception as e:
            print("lembrar o principal:", e, flush=True)

    @Slot()
    def virarSecundaria(self):
        o = self.outro_principal
        if not o: return
        import seguir
        self._lembrar_principal(o["nome"], True)       # par lembrado: da próxima vez vira calado
        print("tela secundária: o operador escolheu ser a tela de", o["nome"], flush=True)
        seguir.reabrir(["--retorno", o["base"].replace("http://", "")])
        QGuiApplication.quit()

    @Slot()
    def ficarPrincipal(self):
        self.outro_principal = {}; self.telasMudou.emit()

    @Slot()
    def projetarDaqui(self):
        """Na tela secundária (F2): este computador volta a ser um Sistema normal, e o par deixa de ser lembrado."""
        import seguir
        if not (os.environ.get("NATIVO_AUTO_SECUNDARIA") or os.environ.get("NATIVO_LEMBRADOS") is not None):
            try: self.A.config.gravar("icm_secundaria_de", [])     # esquece o par: da próxima vez, o cartão pergunta
            except Exception as e: print("esquecer o par:", e, flush=True)
        print("tela secundária: F2, voltando a projetar daqui", flush=True)
        seguir.reabrir(["--principal"])
        QGuiApplication.quit()

    @Slot()
    def sairSecundaria(self):
        print("tela secundária: Esc, saindo", flush=True)
        QGuiApplication.quit()

    @Slot()
    def procurarProjetor(self):
        """O "Procurar novamente": pede ao Windows para ESTENDER (o que o Windows+P > Estender faz; o Lenovo da igreja
        ficava em Duplicar) e o cartão segue esperando; quando a 2ª tela aparecer, o posicionar leva o telão."""
        if os.name == "nt":
            try:
                import subprocess
                exe = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "DisplaySwitch.exe")
                if os.environ.get("NATIVO_SEM_ESTENDER") != "1":     # testes: não mexe nas telas de verdade
                    subprocess.Popen([exe, "/extend"], creationflags=0x08000000)
            except Exception as e:
                print("estender:", e, flush=True)
        elif sys.platform.startswith("linux") and os.environ.get("NATIVO_SEM_ESTENDER") != "1":
            self._ligar_hdmi_linux()          # o estender_telas da 3.0.12 no Linux: o ligar_hdmi (xrandr)
        QTimer.singleShot(2500, self.posicionar)

    def _ligar_hdmi_linux(self):
        """O ligar_hdmi da 3.0.12 (linux_nativo.py): HDMI plugado mas desligado ou espelhado vira tela estendida à direita.
        Quando o X refaz as telas, o Qt avisa (screenAdded/geometria) e o posicionar leva o telão para lá."""
        try:
            import telas_linux
            s = telas_linux.ligar_hdmi()
            if s:
                print("HDMI", s, "estendido (estava desligado ou espelhado)", flush=True)
            return s
        except Exception as e:
            print("ligar_hdmi:", e, flush=True)
            return None

    @Slot()
    def continuarAssim(self):
        """O "Continuar assim": o telão numa janela NESTA tela (ensaio; em Duplicar o projetor mostra o mesmo)."""
        self.ensaio = True; self.aviso_proj = False
        self.posicionar()
        self.aviso.emit("Projeção aberta numa janela nesta tela (ensaio).")

    @Slot()
    def fecharAvisoProjetor(self):
        self.aviso_proj = False; self.telasMudou.emit()

    @Slot()
    def mostrarAvisoProjetor(self):
        if self.telao_fechado:                   # o telão foi fechado pelo celular: o Projetar do painel reabre
            return self.abrirTelao()
        if self.sem_projetor and not self.ensaio:
            # Linux: o _abrir_projecao_linux da 3.0.12 liga o HDMI desligado/espelhado ANTES de olhar as telas; se ligou,
            # o telão vai para ele (o posicionar) e o cartão nem aparece
            if sys.platform.startswith("linux") and os.environ.get("NATIVO_SEM_ESTENDER") != "1" and self._ligar_hdmi_linux():
                QTimer.singleShot(1500, self.posicionar)
                return
            self.aviso_proj = True; self.telasMudou.emit()

    # ---- DUAS TELAS PELA REDE (3.0.9-3.0.12: dtVigiar, dtCartao, dtAcao, dtPilula do app.js). O outro computador (o Vaio)
    # abre o retorno.html DESTE PC e se apresenta pelo /api/apoio; o servidor é o da 3.0.12 (apoio_ola, apoio_mudar e o
    # apoios.json que lembra o par: par lembrado volta CALADO). Aqui ficam a pílula, o cartão "Nova tela encontrada" /
    # "Como usar as duas telas?", o número gigante do Identificar e, depois do Trocar, o HDMI daqui vira a TV de retorno.
    # As palavras são as dele (18/10 00h12): nunca "monitor", "primário", "duplicar", "estender".
    def _vigiar_telas(self):
        if not self.rede:
            return
        try: L = self.rede.S.apoios_lista()
        except Exception as e: print("apoios:", e); return
        self.dt_lista = L
        ativo = next((a for a in L if a["estado"] == "aceito" and a["online"]), None)
        self._papel(bool(ativo and ativo["papel"] == 1))  # o retorno caiu depois do Trocar: o telão volta a ser telão
        if self.dt_modo == "pergunta":                   # respondido NA OUTRA TELA (o retorno também pergunta): acompanha
            a = next((x for x in L if x["chave"] == self.dt_chave), None)
            if not a or not a["online"] or a["estado"] == "dispensado": self._dt_fechar()
            elif a["estado"] == "aceito":
                if a["identificar"] > 0: self._dt_numeros(a)
                self._dt_abrir(a, "como")
        pend = next((a for a in L if a["estado"] == "pendente" and a["online"]), None)
        if pend and not self.dt_modo and self.dt_visto.get(pend["chave"]) != "visto":
            self.dt_visto[pend["chave"]] = "visto"; self._dt_abrir(pend, "pergunta")
        self.telasMudou.emit()

    def _dt_abrir(self, a, modo):
        self.dt_modo, self.dt_chave, self.dt_a = modo, a["chave"], dict(a)
        if modo == "como": self._dt_fim.start()           # o "como" fecha sozinho em 20 s; a pergunta espera a resposta
        else: self._dt_fim.stop()
        self.telasMudou.emit()

    def _dt_fechar(self):
        self._dt_fim.stop(); self.dt_modo, self.dt_chave, self.dt_a = "", "", {}
        self.telasMudou.emit()

    def _dt_numeros(self, a):                            # o telão mostra o número DELE: 1 enquanto é o telão; 2 depois do Trocar
        if a.get("papel") == 2: self.identificar.emit(1, "Telão")
        else: self.identificar.emit(2, "Tela de retorno")

    def _papel(self, apoio):
        if apoio != self.telao_apoio:
            self.telao_apoio = apoio; self.telasMudou.emit()

    @Property(bool, notify=telasMudou)
    def telaoApoio(self):
        return self.telao_apoio

    @Property("QVariant", notify=telasMudou)
    def cartaoTelas(self):
        a = self.dt_a
        return {"modo": self.dt_modo, "nome": a.get("nome", ""), "papel": a.get("papel", 2), "como": a.get("modo", "retorno")}

    @Property(str, notify=telasMudou)
    def pilula(self):
        """'on' (2 telas · vaio) | 'reconectando' (ligada e caiu: âmbar, volta sozinha) | 'conectar' | '' (nada na rede)."""
        L = self.dt_lista
        if any(x["estado"] == "aceito" and x["online"] for x in L): return "on"
        if any(x["estado"] == "aceito" and not x["online"] for x in L): return "reconectando"
        if any(x["online"] and (x["estado"] == "dispensado" or (x["estado"] == "pendente" and self.dt_modo != "pergunta")) for x in L):
            return "conectar"
        return ""

    @Property(str, notify=telasMudou)
    def pilulaTexto(self):
        L, p = self.dt_lista, self.pilula
        nome = lambda f: next((x["nome"] for x in L if f(x)), "")
        if p == "on": return "2 telas · " + nome(lambda x: x["estado"] == "aceito" and x["online"])
        if p == "reconectando": return "reconectando · " + nome(lambda x: x["estado"] == "aceito")
        if p == "conectar": return "Conectar a tela de retorno"
        return ""

    def _dt_acao(self, chave, acao):
        try: r = self.rede.S.apoio_mudar(chave, acao)
        except Exception as e: r = {"ok": False, "erro": str(e)}
        if r and r.get("ok"):
            if r.get("identificar", 0) > 0: self._dt_numeros(r)
            self.dt_visto[chave] = r.get("estado")
            self._papel(r.get("estado") == "aceito" and r.get("papel") == 1)
            try: self.dt_lista = self.rede.S.apoios_lista()
            except Exception: pass
        return r

    @Slot(str)
    def telasAcao(self, acao):
        """Os botões do cartão: sim | nao | trocar | modo:retorno | modo:igual | so_telao | ok."""
        if acao == "ok" or not self.dt_chave:
            return self._dt_fechar()
        a = dict(self.dt_a)
        r = self._dt_acao(self.dt_chave, acao)
        if not r or not r.get("ok"):
            self.aviso.emit((r or {}).get("erro") or "A tela de retorno não respondeu."); return self._dt_fechar()
        if acao in ("nao", "so_telao"):
            self._dt_fechar(); self.aviso.emit("Só o telão.")
        else:
            a.update(r); self._dt_abrir(a, "como")

    @Slot()
    def pilulaClique(self):
        lig = next((x for x in self.dt_lista if x["estado"] == "aceito"), None)
        if lig: return self._dt_abrir(lig, "como")
        fora = next((x for x in self.dt_lista if x["online"] and x["estado"] != "aceito"), None)
        if not fora: return
        r = self._dt_acao(fora["chave"], "pedir")         # "Agora não" sem querer: volta a perguntar
        a = dict(fora); a.update(r or {}); self._dt_abrir(a, "pergunta")

    @Slot()
    def procurarTelas(self):
        """O botão das duas telas da barra (#btn-procurar-telas, procurarTelas do app.js:4045 da 3.0.13). Relato dele 08/11
        08h13: "clica e não dá NENHUM retorno". Aqui ele chamava o "Procurar novamente" do projetor (o Estender do Windows,
        calado); o da 3.0.13 GRITA NA REDE na hora, avisa ("Procurando outras telas… avisando a rede"), espera até 6 s o
        outro aparelho aparecer e abre o cartão; ninguém respondeu: diz o que fazer. Não mexe nas telas do Windows."""
        if self._procurando_telas:
            return
        self._procurando_telas = True; self.telasMudou.emit()
        self.aviso.emit("Procurando outras telas… avisando a rede")
        try:
            if self.rede: self.rede.S.ANUNCIAR_JA.set()
        except Exception as e:
            print("procurar telas:", e, flush=True)
        n_telas = len(QGuiApplication.screens())
        conta = [0]

        def passo():
            self._vigiar_telas()
            if not any(x["online"] for x in self.dt_lista) and conta[0] < 12:       # até 6 s, de 0,5 em 0,5
                conta[0] += 1; QTimer.singleShot(500, passo); return
            self._procurando_telas = False; self.telasMudou.emit()
            lig = next((x for x in self.dt_lista if x["estado"] == "aceito" and x["online"]), None)
            if lig: return self._dt_abrir(lig, "como")
            fora = next((x for x in self.dt_lista if x["online"]), None)
            if fora:
                r = self._dt_acao(fora["chave"], "pedir")
                a = dict(fora); a.update(r or {}); return self._dt_abrir(a, "pergunta")
            self.aviso.emit(("Este computador tem %d telas ligadas. " % n_telas if n_telas >= 2 else "") +
                            "Nenhum outro aparelho respondeu. No outro computador, abra o Sistema ICM na mesma rede (Wi-Fi ou cabo).")
        QTimer.singleShot(500, passo)

    @Property(bool, notify=telasMudou)
    def procurandoTelas(self):
        return self._procurando_telas

    @Slot()
    def fecharCartaoTelas(self):
        self._dt_fechar()

    # ---- ESTILO (trocarEstilo do app.js:2149): Padrão <-> Mapa-múndi. Troca o jogo de fundos e reprojeta o que está
    # no ar com o fundo novo. Um fundo da galeria e a apresentação ficam como estão; a 3.0.12 sempre abre no Padrão.
    ESTILO_NOME = {"limpo": "Estilo Padrão", "mapa": "Estilo Mapa-múndi"}

    @Property(str, notify=mudou)
    def nomeEstilo(self):
        return self.ESTILO_NOME.get(self.estilo, self.estilo)

    @Slot()
    def trocarEstilo(self):
        self.estilo = "mapa" if self.estilo == "limpo" else "limpo"
        v = self.vivo
        if v == "louvor" and self.idx >= 0: self.projetar(self.idx, self.slide)
        elif v == "biblia" and self.bib: self._bib(*self.bib)
        elif v == "bibmulti": self.projetarJuntos()
        elif v == "espera": self.descanso()
        elif v in ("fundo", "apres", "preto", ""): pass
        elif isinstance(self.ultimo, dict) and self.ultimo.get("fundo"):
            # relógio, cronômetro, aviso e cifra: o mesmo quadro com o fundo "plano" do estilo novo (sem esmaecer)
            t = dict(self.ultimo); t["fundo"] = self._plano(); t.pop("fade", None)
            self._manda(t)
        self.esperaMudou.emit()                   # a galeria de fundos é a do estilo novo
        self.mudou.emit()

    @Slot(result="QVariant")
    def atual(self):
        return self.ultimo


def carrega_fontes():
    pasta = os.path.join(cerebro.APP, "fontes")
    QFontDatabase.addApplicationFont(os.path.join(pasta, "bebas.otf"))
    # A Outfit é VARIÁVEL (padrão 100). No Linux o Qt usa o padrão e a letra sai fina (Vaio, 07/11/2026): lá entram os
    # arquivos fixos de cada peso (ferramentas/outfit_por_peso.py). No Windows segue a variável, que ele lê certo.
    fixos = os.path.join(AQUI, "fontes_linux")
    if os.name != "nt" and os.path.isdir(fixos):
        for f in sorted(os.listdir(fixos)):
            QFontDatabase.addApplicationFont(os.path.join(fixos, f))
    else:
        QFontDatabase.addApplicationFont(os.path.join(pasta, "Outfit.ttf"))


def fonte_mono():
    """A cifra precisa de fonte MONOESPAÇADA (a coluna do acorde é o caractere). A 3.0.12 usa Consolas; ela vem do
    próprio Windows (não vai no pacote). Sem ela (Linux do Vaio), a fonte fixa do sistema."""
    win = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for f in ("consola.ttf", "consolab.ttf"):
        if os.path.exists(os.path.join(win, f)):
            QFontDatabase.addApplicationFont(os.path.join(win, f))   # no desenho sem tela ela não vem sozinha
    if "Consolas" in QFontDatabase.families():
        return "Consolas"
    return QFontDatabase.systemFont(QFontDatabase.FixedFont).family()


def carregar_fonte_ui(app):
    """A LETRA DO PAINEL (07/11/2026). A da 3.0.13 é a do app.css: 'Segoe UI'. A casa decide qual arquivo vai EMBUTIDO em
    Nativo/fontes/ui (todas as plataformas iguais; nenhuma fonte do sistema). Enquanto a pasta não existe, só para
    comparar com a 3.0.13 no Windows, a Segoe UI do próprio Windows."""
    pasta = os.path.join(AQUI, "fontes", "ui")
    fam = None
    if os.path.isdir(pasta):
        for f in sorted(os.listdir(pasta)):
            if f.lower().endswith((".ttf", ".otf")):
                i = QFontDatabase.addApplicationFont(os.path.join(pasta, f))
                if f.startswith("PainelICM"):          # a letra do painel; a Liberation Sans é só dos campos de texto
                    fam = fam or (QFontDatabase.applicationFontFamilies(i) or [None])[0]
    if not fam:
        win = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        for f in ("segoeui.ttf", "seguisb.ttf", "segoeuib.ttf", "segoeuil.ttf", "seguisli.ttf"):
            if os.path.exists(os.path.join(win, f)):
                QFontDatabase.addApplicationFont(os.path.join(win, f))
        fam = "Segoe UI"
    f = QFont(fam); f.setPointSizeF(9.75)       # em PONTOS: com setPixelSize o telão (que mede em pontos) gerava 77 mil avisos de tamanho 0
    # o desenho da letra do painel no Linux mora no Letra.qml (08/11/2026): mudá-lo para o programa inteiro serrilhava os
    # campos de texto (o "69" da busca), medido no Vaio
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)   # avanço em fração de px, como o Edge (posição das letras igual)
    app.setFont(f)
    return fam


class _SoltaBusca(QObject):
    """08/11 21h (teste dele na igreja, "item perigoso"): digitava "Maranata" na pílula, clicava no louvor e as SETAS
    continuavam no texto em vez de passar a projeção. Agora o campo de texto SOLTA o teclado quando: (1) clica-se fora dele
    (em qualquer lugar do painel); (2) Enter num campo de BUSCA (que projeta ou escolhe); (3) Esc. Enquanto se digita, as
    setas seguem no texto. Vale para todas as buscas e campos (louvores, Bíblia, apresentações, avisos)."""
    def __init__(self, janela):
        super().__init__(janela)
        self.j = janela

    def _campo(self):
        f = self.j.activeFocusItem()
        if f is not None and (f.inherits("QQuickTextInput") or f.inherits("QQuickTextEdit")):
            return f
        return None

    def soltar(self):
        f = self._campo()
        if f is not None:
            f.setFocus(False)
            raiz = self.j.contentItem()
            if raiz is not None:
                raiz.forceActiveFocus()            # o teclado volta para o painel: as setas passam a projeção

    def eventFilter(self, obj, ev):
        t = ev.type()
        if t == QEvent.Type.MouseButtonPress:
            f = self._campo()
            if f is not None:
                p = ev.position() if hasattr(ev, "position") else ev.localPos()
                caixa = f.mapRectToScene(QRectF(0, 0, f.width(), f.height()))
                if not caixa.adjusted(-2, -2, 2, 2).contains(p):
                    self.soltar()
        elif t == QEvent.Type.KeyPress:
            f = self._campo()
            if f is not None:
                k = ev.key()
                multilinha = f.inherits("QQuickTextEdit")
                if k == Qt.Key.Key_Escape or (k in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not multilinha):
                    QTimer.singleShot(0, self.soltar)       # depois do Enter fazer o dele (projetar, escolher)
        return False


def soltar_busca(painel):
    """Liga o _SoltaBusca na janela do painel (o Sistema e as provas)."""
    filtro = _SoltaBusca(painel)
    painel.installEventFilter(filtro)
    painel._solta_busca = filtro
    return filtro


def ligar_espelhos(painel):
    """UMA DECODIFICAÇÃO, VÁRIAS TELAS (08/11/2026, a promessa dele): o vídeo é decodificado SÓ no telão; cada quadro
    pronto vai também para a prévia do painel e para o espelho da TV de retorno (QVideoSink.setVideoFrame). Provado: 36
    quadros no telão, 36 no espelho, imagem idêntica. Religa quando qualquer palco troca de camada."""
    try:
        from PySide6.QtMultimedia import QVideoSink   # sem o import o PySide entrega a saída como QObject genérico
    except Exception:
        return
    telao = painel.findChild(QObject, "palcoTelao")
    espelhos = [o for o in (painel.findChild(QObject, "previaPalco"), painel.findChild(QObject, "espelhoRetorno")) if o is not None]
    if telao is None or not espelhos:
        return
    ligado = {"de": None, "para": []}
    # 08/11 21h (o nativo.log da igreja: 268 de 273 linhas eram "addMetaMethod setVideoFrame ... No Wrapper found"): ligar
    # o sinal ao MÉTODO do sink (para.setVideoFrame) fazia o PySide criar um "método dinâmico" e reclamar a cada troca de
    # slide. Ligado a uma função comum (que chama o setVideoFrame), não há método dinâmico nem aviso; o custo por quadro é
    # o mesmo (antes também passava pelo Python). Ligação por assinatura (SIGNAL/SLOT) NÃO serve: setVideoFrame não é slot
    # (provado: 0 quadros na prévia, prova_espelho_video). E só religa quando os sinks mudaram de verdade.
    ligado["fns"] = []
    def religar(*_):
      try:
          de = telao.property("sinkVideoAtivo"); paras = [e.property("sinkEspelhoAtivo") for e in espelhos]
          grande = painel.findChild(QObject, "espelhoGrande")          # o "No telão agora" das apresentações (09/11)
          paras.append(grande.property("videoSink") if grande is not None else None)
          paras = [x for x in paras if x is not None]
          if de is ligado["de"] and len(paras) == len(ligado["para"]) and all(a is b for a, b in zip(paras, ligado["para"])):
              return
          velho = ligado["de"]
          for fn in ligado["fns"]:
              try: velho.videoFrameChanged.disconnect(fn)
              except Exception: pass
          fns = []
          if de is not None:
              for para in paras:
                  fn = (lambda p: (lambda quadro: p.setVideoFrame(quadro)))(para)
                  de.videoFrameChanged.connect(fn); fns.append(fn)
          ligado.update(de=de, para=paras, fns=fns)
      except Exception as e:
        print("espelho do vídeo:", e, flush=True)
    for o in [telao] + espelhos:
        o.ativaChanged.connect(religar)
    religar()


def main():
    t0 = time.perf_counter()
    def _marca(o_que):                  # NATIVO_TEMPOS=1 (medida, 08/11): o tempo de cada etapa da subida
        if os.environ.get("NATIVO_TEMPOS"): print("  tempo %6.0f ms  %s" % ((time.perf_counter() - t0) * 1000, o_que), flush=True)
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Sistema Nativo")
    # 11/11 (ele no Vaio: "o símbolo tá aquele de programa SH, e tem que ser o símbolo do sistema"): a janela não levava
    # ícone nenhum e a barra do Linux mostrava o genérico. O ícone do Sistema na janela, e o nome do atalho (sistema-icm)
    # para a barra juntar a janela ao atalho dele
    try:
        from PySide6.QtGui import QIcon
        _ic = next((c for c in (os.path.join(cerebro.APP, "sistema.png"), os.path.join(AQUI, "sistema.png"),
                                os.path.join(os.path.dirname(AQUI), "sistema.png")) if os.path.exists(c)), "")
        if _ic: app.setWindowIcon(QIcon(_ic))
        app.setDesktopFileName("sistema-icm")
    except Exception:
        pass
    _marca('QGuiApplication')
    carrega_fontes()
    carregar_fonte_ui(app)              # a letra do painel (Painel ICM) e a dos campos (Liberation Sans), embutidas
    _marca('fontes')
    # A TELA DE CARREGAMENTO (o carregando.html da 3.0.12), 08/11/2026: na hora, no tamanho e no lugar do painel; a frase
    # troca por etapa e ela fecha quando o painel desenha o 1º quadro. Nos testes (fotos, fora da tela) não aparece.
    splash = None
    jx, jy, jw, jh = janela_312(app.primaryScreen())
    if not FOTOS and not os.environ.get("NATIVO_FORA_DA_TELA") and not os.environ.get("NATIVO_SEM_CARREGANDO"):
        # 08/11 17h (ordem dele pela HD): uma JANELINHA pequena e centrada, sem moldura, com a barra dourada de verdade
        # (anda por etapa da subida). Antes ela tinha o tamanho do painel.
        # 17h30 (HD): cantos redondos e sombra -> a janela é TRANSPARENTE fora do cartão (o cartão de 460 x 320 + 22 px de
        # sombra de cada lado, Carregando.qml)
        splash = QQuickView(); splash.setTitle("Sistema")
        fs = splash.format(); fs.setAlphaBufferSize(8); splash.setFormat(fs)
        splash.setColor(QColor(0, 0, 0, 0))
        # 13/11 (ele no Vaio, 12/11: "quando ele inicia o sistema, ele não aparece o símbolo"): a barra do Linux Mint não
        # lista janela do tipo SPLASH; nos ~5 s do Carregando não havia ícone nenhum lá embaixo (medido, foto da barra).
        # No Linux ela é uma janela comum sem moldura: entra na barra com o símbolo desde o primeiro instante.
        splash.setFlags((Qt.WindowType.Window if sys.platform.startswith("linux") else Qt.WindowType.SplashScreen)
                        | Qt.WindowType.FramelessWindowHint)
        splash.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        u = app.primaryScreen().availableGeometry()
        sw, sh = 460 + 44, 320 + 44
        splash.resize(sw, sh); splash.setPosition(u.x() + (u.width() - sw) // 2, u.y() + (u.height() - sh) // 2)
        splash.setSource(QUrl.fromLocalFile(os.path.join(AQUI, "qml", "Carregando.qml")))
        splash.show()
        ate = time.perf_counter() + 0.8
        while time.perf_counter() < ate and not splash.isExposed():
            app.processEvents(); time.sleep(0.01)
        if splash.rootObject() is not None:
            QMetaObject.invokeMethod(splash.rootObject(), "comecar")   # o brilho (Animator) segue na linha de desenho
        for _ in range(5): app.processEvents()
        _marca('tela de carregamento à vista')
    def frase(txt, progresso=None):
        if splash is not None and splash.rootObject() is not None:
            splash.rootObject().setProperty("msg", txt)
            if progresso is not None:
                splash.rootObject().setProperty("progresso", progresso)
            app.processEvents()
    frase("Preparando os louvores e a Bíblia…", 0.12)
    # 13/11: o OUVIDO da abertura (seguir.Ouvido): escuta a rede enquanto o Sistema sobe. Nunca nos testes fechados
    # (NATIVO_SO_LOCAL), nas fotos, nem quando o modo já foi dito (--retorno / --principal). NATIVO_OUVIR força.
    OUVIDO = None
    if (not FOTOS and "--retorno" not in sys.argv and "--principal" not in sys.argv and not os.environ.get("NATIVO_SEGUIR")
            and (os.environ.get("NATIVO_OUVIR") or not os.environ.get("NATIVO_SO_LOCAL"))):
        import seguir
        OUVIDO = seguir.Ouvido()
    A = cerebro.Acervo(adiar=True)        # os textos da busca começam com o painel de pé (preparar_busca, lá embaixo)
    _marca('Acervo')
    frase("Preparando os louvores e a Bíblia…", 0.25)
    ctl = Controle(A, cerebro.Biblia(A))
    _marca('Bíblia + Controle')
    frase("Ligando o celular…", 0.38)
    eng = QQmlApplicationEngine()
    ctx = eng.rootContext()
    ctx.setContextProperty("controle", ctl)
    # 13/11: "--retorno [endereço]" (ou NATIVO_SEGUIR=endereço|auto) = este computador é a TELA SECUNDÁRIA de outro
    # Sistema: não liga servidor nem grita na rede; acha o principal, se apresenta e acompanha (seguir.py)
    SEGUIR = None
    if "--retorno" in sys.argv:
        _k = sys.argv.index("--retorno")
        SEGUIR = sys.argv[_k + 1] if _k + 1 < len(sys.argv) and not sys.argv[_k + 1].startswith("--") else ""
    elif os.environ.get("NATIVO_SEGUIR"):
        SEGUIR = "" if os.environ["NATIVO_SEGUIR"] == "auto" else os.environ["NATIVO_SEGUIR"]
    if SEGUIR is None and OUVIDO is not None:
        lembrados = A.config.ler("icm_secundaria_de", []) or []
        if os.environ.get("NATIVO_LEMBRADOS") is not None:      # testes: a lista dos pares lembrados vem de fora
            lembrados = [x for x in os.environ["NATIVO_LEMBRADOS"].split(",") if x]
        if lembrados:                           # este computador já foi tela secundária: espera o ouvido (até 4,5 s, no "Carregando")
            OUVIDO.pronto.wait(5)
        o = OUVIDO.achou
        if o and o["nome"] in lembrados:         # par lembrado: vira a tela secundária CALADO (como o par no principal)
            SEGUIR = o["base"].replace("http://", "")
            print("tela secundária: par lembrado,", o["nome"], flush=True)
    if SEGUIR is not None and not FOTOS:
        import seguir
        ctl.seguindo = True
        ctl.seguindo_texto = "Procurando o computador principal…"
        ctl._seguidor = seguir.Seguidor(SEGUIR)
        t_seg = QTimer(app); t_seg.setInterval(80)
        t_seg.timeout.connect(lambda: ctl._seguidor.drenar(ctl))
        t_seg.start()
        print("tela secundária: ligada como", ctl._seguidor.nome, "· principal:", SEGUIR or "(procurar na rede)", flush=True)
    if not FOTOS and SEGUIR is None:
        try:
            import rede
            porta, ctl.url_celular = rede.ligar()
            ctl.rede = rede
            rede.publicar_tela(ctl.ultimo)
            t_cmd = QTimer(app); t_cmd.setInterval(120)
            t_cmd.timeout.connect(lambda: [ctl.executar(c) for c in rede.comandos()])
            t_cmd.start()
            t_est = QTimer(app); t_est.setInterval(1000)
            t_est.timeout.connect(lambda: rede.publicar_estado(ctl.estado()))
            t_est.start()
            rede.publicar_estado(ctl.estado())   # já na abertura: o celular que pergunta antes do 1º segundo não vê estado vazio
            t_dt = QTimer(app); t_dt.setInterval(1500)   # a tela de retorno pela rede (o Vaio): quem se apresentou
            t_dt.timeout.connect(ctl._vigiar_telas)
            t_dt.start()
            print("celular:", ctl.url_celular, flush=True)
        except Exception as e:
            print("ERRO ao ligar a rede (o telão segue sem celular):", e, flush=True)
    forcar_janela = bool("--janela" in sys.argv or FOTOS)     # testes e fotos: o telão sempre numa janela
    FORA = bool(os.environ.get("NATIVO_FORA_DA_TELA"))    # testes (08/11): janela real, desenhada pela PLACA, fora da tela
    # o telão só nasce visível aqui; senão quem mostra é o posicionar (fora da tela: quem mostra é o Python, já fora)
    ctx.setContextProperty("telaoEmJanela", forcar_janela and not FORA)
    ctx.setContextProperty("modoFotos", bool(FOTOS))
    ctx.setContextProperty("foraDaTela", FORA)
    # a janela do operador nasce no tamanho e no lugar da 3.0.x (janela_312) e, com a tela de carregamento, ESCONDIDA:
    # quem a mostra é o Python, transparente embaixo da de carregamento até o 1º quadro (nada de preto, nada de pular)
    ctx.setContextProperty("janelaInicial", {"x": jx, "y": jy, "w": jw, "h": jh})
    ctx.setContextProperty("painelEsperaCarregando", splash is not None)
    ctx.setContextProperty("letraAntiga", bool(os.environ.get("NATIVO_LETRA_ANTIGA")))   # só o par antes x depois (Letra.qml)
    ctx.setContextProperty("letraHint", os.environ.get("NATIVO_LETRA_HINT", ""))          # só a medida (Letra.qml): cheio|vertical|nenhum
    ctx.setContextProperty("modoTexto", os.environ.get("NATIVO_TEXTO", ""))               # só o par: "nativo" = a letra do sistema, sem a imitação
    _marca('rede (celular)')
    preparar_motor(eng, ctl)
    _marca('preparar_motor')
    frase("Carregando a coletânea…", 0.5)
    eng.load(QUrl.fromLocalFile(os.path.join(AQUI, "qml", "Painel.qml")))
    _marca('QML carregado (Painel.qml)')
    if not eng.rootObjects():
        print("ERRO: o QML não carregou"); return 1
    painel = eng.rootObjects()[0]
    if splash is not None:
        frase("Quase lá…", 0.85)
        # 08/11 (relato dele: "depois do carregando dá uma TELA PRETA e o layout se remonta mais para a esquerda"): o
        # painel aparecia JÁ no load, antes de desenhar (preto) e num lugar que depois mudava. Agora ele aparece
        # TRANSPARENTE no lugar da 3.0.x (janela_312), a moldura é descontada AINDA invisível, e só no 1º quadro desenhado
        # DEPOIS disso ele fica opaco e a janelinha fecha: nada de preto, nada de pular.
        painel.setOpacity(0.0)
        painel.create(); moldura_312(painel, jx, jy, jw, jh)    # a moldura ANTES de aparecer (Windows): nasce no lugar
        painel.show()
        ate = time.perf_counter() + 0.8
        while time.perf_counter() < ate and not painel.isExposed():
            app.processEvents(); time.sleep(0.01)
        moldura_312(painel, jx, jy, jw, jh)              # de novo, à vista (no Linux a moldura só se sabe agora)
        frase("Quase lá…", 1.0)
        fechou = []
        def _fecha_carregando():
            if not fechou:
                fechou.append(1)
                if ctl.seguindo:                 # tela secundária: o painel não vem para a frente (fica minimizado)
                    painel.showMinimized(); painel.setOpacity(1.0)
                else:
                    painel.setOpacity(1.0); painel.requestActivate()
                    if sys.platform == "win32" and not os.environ.get("NATIVO_SEM_EMPURRAO"):
                        # 15/11 (4.0.2 no PC da igreja, Win10, tela MACROSILICON): o conteúdo nascia ~30 px para CIMA (a
                        # faixa de cima atrás da barra de título, faixa preta embaixo). O painel é posto no lugar ainda
                        # invisível (opacidade 0, moldura_312) e o Qt fica com a superfície velha (QTBUG-113444; o remédio
                        # conhecido é maximizar/restaurar). Um empurrão de 1 px depois de opaco refaz a superfície.
                        _w = painel.width()
                        painel.setWidth(_w + 1)
                        QTimer.singleShot(60, lambda: painel.setWidth(_w))
                splash.close(); splash.deleteLater()
        painel.frameSwapped.connect(lambda: QTimer.singleShot(0, _fecha_carregando))
        QTimer.singleShot(4000, _fecha_carregando)    # garantia: nunca fica para trás
    if os.environ.get("NATIVO_JANELA"):          # testes: o tamanho da janela do operador (ex.: 1280x690, o do par)
        lw, lh = (int(x) for x in os.environ["NATIVO_JANELA"].lower().split("x"))
        painel.setWidth(lw); painel.setHeight(lh)
    if FORA:                                      # sem gerenciador de janelas, sem barra de tarefas, x = -3000: ninguém vê
        painel.setFlags(Qt.WindowType.Tool | Qt.WindowType.X11BypassWindowManagerHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        painel.setPosition(-3000, -3000); painel.show()
    telao = painel.findChild(QObject, "telao")
    if FORA and forcar_janela and telao is not None:   # o telão em janela também fora da tela (pela placa, ninguém vê)
        telao.setFlags(Qt.WindowType.Tool | Qt.WindowType.X11BypassWindowManagerHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        telao.setPosition(-3000, -1500); telao.show()
    # o telão na 2ª tela e a TV de retorno na 3ª (PC, projetor e TV); em janela quando o teste pede (NATIVO_RETORNO=janela)
    retorno = painel.findChild(QObject, "retorno")
    ctl._telao, ctl._retjan, ctl._forcar_janela, ctl._painel = telao, retorno, forcar_janela, painel
    if retorno is not None and os.environ.get("NATIVO_RETORNO") == "janela":
        retorno.show()
    if OUVIDO is not None and not ctl.seguindo:
        def _ouviu(n=[0]):                       # o cartão "Outro Sistema nesta rede" (uma vez, quando o ouvido terminar)
            if not OUVIDO.pronto.is_set() and n[0] < 20:
                n[0] += 1; QTimer.singleShot(400, _ouviu); return
            if OUVIDO.achou:
                ctl.outro_principal = dict(OUVIDO.achou); ctl.telasMudou.emit()
                print("outro Sistema nesta rede:", OUVIDO.achou["nome"], OUVIDO.achou["base"], flush=True)
                if os.environ.get("NATIVO_AUTO_SECUNDARIA") == "sim":     # testes: aperta o "Ser a tela secundária"
                    QTimer.singleShot(2500, ctl.virarSecundaria)
        QTimer.singleShot(600, _ouviu)
    if ctl.seguindo:
        # a tela secundária não tem operador: o painel fica minimizado. No Windows a janela do telão nasce "filha" do
        # painel e minimizar o pai ESCONDE a filha (medido 13/11 no PC de casa: a tela ficava atrás de tudo): solta antes
        if telao is not None: telao.setTransientParent(None)
        painel.showMinimized()
    ctl.posicionar()
    if ctl.seguindo and telao is not None:
        # o fim do "Carregando" ativa o painel (e no Linux isso o traz de volta, por cima da tela): de novo, depois
        def _so_a_tela():
            if painel.visibility() != QWindow.Visibility.Minimized: painel.showMinimized()
            telao.raise_(); telao.requestActivate()
        for _ms in (0, 700, 4400): QTimer.singleShot(_ms, _so_a_tela)
    if telao is not None and not forcar_janela:
        telao.visibleChanged.connect(ctl.telaoVisivel)     # fechar a janela do ensaio desfaz o ensaio (B9)
    try:
        ligar_espelhos(painel)
    except Exception as e:                   # o espelho é luxo: falhar nunca derruba a subida
        print("espelho do vídeo desligado:", e, flush=True)
    try:
        soltar_busca(painel)                 # clicar fora / Enter / Esc: o campo de texto solta as setas
    except Exception as e:
        print("soltar a busca:", e, flush=True)
    if os.environ.get("NATIVO_FPS"):             # medida (08/11): quadros por segundo do painel e do telão, a cada 10 s
        conta = {"painel": 0, "telao": 0}
        painel.frameSwapped.connect(lambda: conta.__setitem__("painel", conta["painel"] + 1))
        if telao is not None:
            telao.frameSwapped.connect(lambda: conta.__setitem__("telao", conta["telao"] + 1))
        def _fps():
            print("fps painel %.1f · telão %.1f" % (conta["painel"] / 10, conta["telao"] / 10), flush=True)
            conta["painel"] = conta["telao"] = 0
        t_fps = QTimer(app); t_fps.setInterval(10000); t_fps.timeout.connect(_fps); t_fps.start()

    # a tela que chega ou sai muda o telão de lugar na hora (sem vigiar a cada 1,5 s). A que SAI: esconde já (o Windows
    # jogaria o telão na tela do operador) e confere de novo quando o Windows terminar de arrumar as telas.
    def tela_saiu(s):
        if telao is not None and not forcar_janela and telao.screen() is s:
            telao.hide()
        QTimer.singleShot(400, ctl.posicionar)
    app.screenAdded.connect(lambda s: QTimer.singleShot(400, ctl.posicionar))
    app.screenRemoved.connect(tela_saiu)
    if os.name != "nt" and not forcar_janela:   # notebook: abrir/fechar a TAMPA muda quem é a tela do operador
        ultimo_lid = [_tampa_fechada()]
        def vigia_tampa():
            agora = _tampa_fechada()
            if agora != ultimo_lid[0]:
                ultimo_lid[0] = agora; ctl.posicionar()
        t_lid = QTimer(app); t_lid.setInterval(2000); t_lid.timeout.connect(vigia_tampa); t_lid.start()

    print("Sistema Nativo de pé em %.0f ms (telão %s)" % ((time.perf_counter() - t0) * 1000, ctl._onde), flush=True)
    # o índice das cifras (~220 ms, uma vez) é montado com o painel já de pé, e não no 1º clique de louvor
    QTimer.singleShot(1500, ctl.cif._indice)
    # 08/11/2026: os textos da busca e as sugestões também (no Vaio disputavam o Python com a subida: 11-15 s)
    QTimer.singleShot(300, A.preparar_busca)
    QTimer.singleShot(900, ctl.preparar_sugestoes)
    # o Atualizar: o instalador subiu -> o Sistema fecha (sinal vindo da linha de fundo: chega na fila do Qt)
    ctl.sairParaAtualizar.connect(app.quit)
    # ligarAtualizacao da 3.0.13: com o "procurar sozinho" ligado, 5 s depois de abrir procura em silêncio
    if os.environ.get("NATIVO_SO_LOCAL") != "1" and not FOTOS and not FORA and not ctl.seguindo:
        QTimer.singleShot(5000, ctl.verificar_ao_abrir)
    if FOTOS:
        QTimer.singleShot(300, lambda: fotos(app, ctl, telao, FOTOS))
    if os.environ.get("NATIVO_FOTO_PAINEL"):      # testes: abre a aba pedida e fotografa o PAINEL ("1:arquivo.png")
        aba, arq = os.environ["NATIVO_FOTO_PAINEL"].split(":", 1)
        def _foto_painel():
            ab = painel.findChild(QObject, "abas")
            if ab is not None: ab.setProperty("currentIndex", int(aba))
            if os.environ.get("NATIVO_FOTO_ABA"):                 # testes: a aba pela ordem do <nav> (0 Louvor ... 6 Fundos)
                painel.setProperty("aba", int(os.environ["NATIVO_FOTO_ABA"]))
            if os.environ.get("NATIVO_FOTO_BUSCA_BIB") is not None:  # testes: o que está digitado na busca da Bíblia
                bb = painel.findChild(QObject, "buscaLivro")
                if bb is not None:
                    bb.setProperty("text", os.environ["NATIVO_FOTO_BUSCA_BIB"])
                    focar_campo(painel, "buscaLivro")             # como quem acabou de digitar
            if os.environ.get("NATIVO_FOTO_TEXTO"):               # testes: o texto digitado no <textarea> da aba Texto
                ct = painel.findChild(QQuickItem, "corpoAviso")
                if ct is not None: ct.setProperty("text", os.environ["NATIVO_FOTO_TEXTO"].replace("|", chr(10)))
            if os.environ.get("NATIVO_FOTO_VERSO"):               # testes: o versículo projetado ("João|3|16") e os giros
                l, c, v = os.environ["NATIVO_FOTO_VERSO"].split("|")
                ctl.projetarVerso(l, int(c), int(v))
                for _ in range(int(os.environ.get("NATIVO_FOTO_GIROS", "0"))): ctl.maisSugestoes()
            if os.environ.get("NATIVO_FOTO_BUSCA") is not None:   # testes: o que está digitado na busca de louvor
                bl = painel.findChild(QObject, "buscaLouvor")
                if bl is not None:
                    bl.setProperty("text", os.environ["NATIVO_FOTO_BUSCA"])
                    if os.environ.get("NATIVO_FOTO_FOCO"):        # como quem acabou de digitar (o campo com o foco)
                        focar_campo(painel, "buscaLouvor")
            if os.environ.get("NATIVO_FOTO_CIFRA"):               # testes: a folha da cifra do 1º louvor achado ("69")
                r = ctl.A.lista312(os.environ["NATIVO_FOTO_CIFRA"])
                if r: QMetaObject.invokeMethod(painel, "abrirCifra", Q_ARG("QVariant", r[0]["i"]))
            if os.environ.get("NATIVO_FOTO_BV"):                  # testes: as boas-vindas abertas no passo pedido (0 a 4)
                b = painel.findChild(QObject, "bemVindo")
                if b is not None:
                    QMetaObject.invokeMethod(b, "abrir"); b.setProperty("passo", int(os.environ["NATIVO_FOTO_BV"]))
            if os.environ.get("NATIVO_FOTO_MENU"):                # testes: o menu ☰ aberto na seção pedida ("inicio", "celular"...)
                m = painel.findChild(QObject, "menu")
                if m is not None:
                    QMetaObject.invokeMethod(m, "abrirComIgreja")
                    if os.environ["NATIVO_FOTO_MENU"] != "inicio": m.setProperty("secao", os.environ["NATIVO_FOTO_MENU"])
                    if os.environ.get("NATIVO_FOTO_SOBRE_ABA"):  # testes (08/11): a aba do menu com o mouse em cima
                        def _sobre_aba():
                            # as abas nascem de um Repeater: só a árvore VISUAL as alcança (o findChild não)
                            alvo, pilha, ab = "menuAba_" + os.environ["NATIVO_FOTO_SOBRE_ABA"], [painel.contentItem()], None
                            while pilha and ab is None:
                                it = pilha.pop()
                                if it.objectName() == alvo: ab = it
                                pilha.extend(it.childItems())
                            print("aba com o mouse em cima:", ab is not None, flush=True)
                            if ab is not None: ab.setProperty("forcarSobre", True)
                        QTimer.singleShot(800, _sobre_aba)              # as abas nascem depois (o menu vem num Loader)
                    if os.environ.get("NATIVO_FOTO_ASSIST"):     # testes: o assistente aberto ("sobre")
                        n = os.environ["NATIVO_FOTO_ASSIST"]
                        a = painel.findChild(QObject, "assistPassos" if n in ("restaurar", "desinstalar") else "assist" + n.capitalize())
                        if a is not None and n in ("restaurar", "desinstalar"):
                            QMetaObject.invokeMethod(a, "iniciar", Q_ARG("QVariant", n))
                            if os.environ.get("NATIVO_FOTO_PASSO"):     # e um passo adiante ("restaurar:tudo")
                                QMetaObject.invokeMethod(a, "ir", Q_ARG("QVariant", os.environ["NATIVO_FOTO_PASSO"]))
                        elif a is not None:
                            QMetaObject.invokeMethod(a, "abrir")
                            if os.environ.get("NATIVO_FOTO_MAIS"): a.setProperty("mais", True)
                            if os.environ.get("NATIVO_FOTO_ATU") == "verificar":   # testes (08/11): o clique no Verificar
                                a.setProperty("status", "Procurando…"); ctl.verificarAtualizacao()
                    if os.environ.get("NATIVO_FOTO_ROLAR"):      # testes: o corpo do menu rolado até o fim
                        def _rolar():
                            c = painel.findChild(QObject, "menuCorpo")
                            if c is not None:
                                c.setProperty("contentY", max(0.0, c.property("contentHeight") - c.property("height")))
                        QTimer.singleShot(800, _rolar)
            if os.environ.get("NATIVO_FOTO_AVISO"):   # testes (08/11): o cartão "Projetor não encontrado" aberto
                ctl.aviso_proj = True; ctl.telasMudou.emit()
            if os.environ.get("NATIVO_FOTO_APRES"):  # "k:slide" = abre a apresentação k (a aba mostra as miniaturas)
                k, s = (os.environ["NATIVO_FOTO_APRES"] + ":0").split(":")[:2]
                ctl.entrarApresentacao(int(k), int(s))
            QTimer.singleShot(2500, lambda: (painel.grabWindow().save(arq), print("foto do painel:", arq, flush=True)))
            if os.environ.get("NATIVO_FOTO_TELA"):    # testes (08/11): a MESMA janela, mas os pixels do MONITOR (o que o olho vê)
                def _tela():
                    painel.raise_(); painel.requestActivate()
                    def _ja():                    # PrintWindow do DWM: a janela como o Windows a compõe, mesmo coberta
                        sys.path.insert(0, os.path.join(AQUI, "ferramentas"))
                        import captura_janela
                        print("foto da TELA:", arq[:-4] + "_tela.png", captura_janela.capturar(int(painel.winId()), arq[:-4] + "_tela.png"), flush=True)
                    QTimer.singleShot(700, _ja)
                QTimer.singleShot(3000, _tela)
            if os.environ.get("NATIVO_FOTO_DUPLA"):   # testes: a animação anda? mais uma foto do painel e duas do telão
                b = arq[:-4]
                QTimer.singleShot(2500, lambda: telao.grabWindow().save(b + "_telao_a.png"))
                QTimer.singleShot(2500 + int(os.environ["NATIVO_FOTO_DUPLA"]), lambda: (
                    painel.grabWindow().save(b + "_b.png"), telao.grabWindow().save(b + "_telao_b.png")))
        QTimer.singleShot(int(float(os.environ.get("NATIVO_FOTO_ESPERA", "1.5")) * 1000), _foto_painel)
    if os.environ.get("NATIVO_SAIR_EM"):          # testes: fecha sozinho (nunca matar processo)
        QTimer.singleShot(int(float(os.environ["NATIVO_SAIR_EM"]) * 1000), app.quit)
    app.aboutToQuit.connect(lambda: ctl.fechar_no_ar(esperar=True))     # o beforeunload da 3.0.13
    return app.exec()


def fotos(app, ctl, telao, pasta):
    """Sem tela: projeta louvores de referência e grava o telão em PNG (1280x720), para conferir contra a 3.0.12."""
    os.makedirs(pasta, exist_ok=True)
    A = ctl.A
    casos = []
    ANIM = "--anim" in sys.argv
    for q in [a for a in sys.argv[sys.argv.index("--fotos") + 2:] if a != "--anim"] or ["69", "218", "143", "quando ao fim da jornada", "no ceu nao entra pecado"]:
        if q.startswith(("bib:", "rel:", "tim:", "txt:", "fun:", "esp:", "apr:", "est:", "jun:", "tam:")):
            casos.append((q, None)); continue
        r = A.buscar(q)
        if r:
            casos.append((q, r[0]))
    fila = []
    for q, i in casos:
        if i is None:
            fila.append((q, None, 0)); continue
        for k in range(min(3, A.telas_do_louvor(A.da_vez(i), ANIM))):
            fila.append((q, i, k))
    ctl.anim_ligada = ANIM

    def passo():
        if not fila:
            print("fotos gravadas em", pasta, flush=True); app.quit(); return
        q, i, k = fila.pop(0)
        if i is None:
            if q.startswith("bib:"): ctl.biblia(q[4:])
            elif q.startswith("rel:"): ctl.relogio()
            elif q.startswith("tim:"): ctl.cronometro(float(q[4:].split("|")[0]), (q[4:].split("|") + [""])[1])
            elif q.startswith("txt:"): p = q[4:].split("|"); ctl.texto(p[0], chr(10).join(p[1:]))
            elif q.startswith("fun:"): ctl.projetarFundo(int(q[4:]))
            elif q.startswith("esp:"): ctl.descanso()
            elif q.startswith("est:"): ctl.trocarEstilo()      # troca o estilo e fotografa o que ficou no ar
            elif q.startswith("jun:"):        # jun:João 3:16|João 3:17 = estes versículos na lista, marcados (✓), Juntos
                ctl.limparLista()
                for r in q[4:].split("|"):
                    b = ctl.B.ler(r)
                    if b: ctl.addVerso(*b); ctl.fila[-1]["on"] = True
                ctl.projetarJuntos()
            elif q.startswith("tam:"):        # tam:+3 / tam:-2 / tam:0 = toques no A+/A- (0 = Padrão)
                n = int(q[4:])
                for _ in range(abs(n) or 1): ctl.tamanho((n > 0) - (n < 0))
            elif q.startswith("apr:"):        # apr:K:S:P@ms = apresentação K, slide S (0-based), clique P, foto depois de ms
                a = q[4:].split("@")[0].split(":") + ["0", "0"]
                k, s, pp = int(a[0]), int(a[1]), int(a[2])
                if ctl.ap is None or ctl.listaApres()[k]["nome"] != ctl.ap["nome"] or ctl.ap_pos != s: ctl.entrarApresentacao(k, s)
                if pp != ctl.ap_passo: ctl.projetarSlide(s, pp)
        else: ctl.projetar(i, k)
        def grava():
            img = telao.grabWindow()
            rot = q.replace(":", "_").replace("@", "_") if q.startswith("apr:") else ("jun%d_%s" % (len(q.split("|")), cerebro.so_letras(q[4:].split("|")[0]).replace(" ", "_")[:16])) if q.startswith("jun:") else ("tam_" + q[4:]) if q.startswith("tam:") else cerebro.so_letras(q.split("|")[0]).replace(" ", "_")[:30]
            nome = os.path.join(pasta, "%s_t%d.png" % (rot, k))
            img.save(nome)
            print("foto:", nome, img.width(), "x", img.height(), flush=True)
            rj = getattr(ctl, "_retjan", None)
            if rj is not None and rj.isVisible():
                r = rj.grabWindow(); rn = nome[:-4] + "_ret.png"; r.save(rn)
                print("foto do retorno:", rn, r.width(), "x", r.height(), flush=True)
            QTimer.singleShot(50, passo)
        espera = int(q.split("@")[1]) if q.startswith("apr:") and "@" in q else 900
        QTimer.singleShot(espera, grava)        # depois do esmaecer de 700 ms
    passo()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
