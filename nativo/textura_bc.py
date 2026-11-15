# -*- coding: utf-8 -*-
"""TEXTURA COMPRIMIDA NOSSA (10/11/2026). O leitor de .ktx do Qt Quick só conhece
BC1/BC2/BC3 (qsgcompressedtexture.cpp, Qt 6.9 e atual: BC7 cai em UnknownFormat e não desenha, sem aviso). O item
TexBC lê o .ktx FORA da linha da interface, cria a textura na placa no formato do arquivo (BC7 0x8E8C, DXT5 0x83F3,
DXT1 0x83F0/1) e manda os bytes como estão: o processador não decodifica nada. Uma textura por (janela, arquivo),
dividida por todos os itens que a usam; `recorte` escolhe o pedaço (a célula do quadro) sem custo.
A COR DO ARQUIVO VEM MULTIPLICADA PELA TRANSPARÊNCIA (medido: erro na borda 2,3 x 11,0 sem multiplicar).
QML:  import Casa;  TexBC { fonte: "<caminho ou file:///...>"; recorte: Qt.rect(x, y, w, h) }   · pronta: bool"""
import os, struct, threading, time, ctypes
from collections import OrderedDict
from PySide6.QtCore import QObject, QSize, QByteArray, QRectF, QUrl, Property, Signal
from PySide6.QtGui import QGuiApplication, QRhiTexture, QRhiTextureUploadDescription, QRhiTextureUploadEntry, \
    QRhiTextureSubresourceUploadDescription
from PySide6.QtQuick import QQuickItem, QQuickWindow, QSGSimpleTextureNode, QSGTexture, QSGRendererInterface
from PySide6.QtQml import qmlRegisterType
import shiboken6

FORMATOS = {0x8E8C: QRhiTexture.BC7, 0x83F3: QRhiTexture.BC3, 0x83F1: QRhiTexture.BC1, 0x83F0: QRhiTexture.BC1}
TETO_BYTES = int(os.environ.get("NATIVO_BC_RAM_MB", "256")) * 1024 * 1024       # arquivos lidos, na memória comum
TETO_PLACA = int(os.environ.get("NATIVO_BC_PLACA_MB", "192")) * 1024 * 1024     # texturas vivas, na placa
_lidos = OrderedDict()        # caminho -> (formato, w, h, QByteArray)
_lendo = set()
_tex = {}                     # (janela, caminho) -> [QRhiTexture, QSGTexture, usos, quando ficou sem uso, bytes]
_trava = threading.Lock()
medidas = {"envios": 0, "ms_envio_max": 0.0, "ms_leitura_max": 0.0, "placa_bytes": 0, "soltas": 0}


def le_ktx(p):
    b = open(p, "rb").read()
    cab = struct.unpack("<13I", b[12:64])
    ini = 64 + cab[12]; n = struct.unpack("<I", b[ini:ini + 4])[0]
    return cab[4], cab[6], cab[7], QByteArray(b[ini + 4:ini + 4 + n])


class _Leitor(QObject):
    chegou = Signal(str)
_leitor = _Leitor()


def _le(p):
    t0 = time.perf_counter()
    try: d = le_ktx(p)
    except Exception: d = None
    with _trava:
        _lendo.discard(p)
        if d:
            _lidos[p] = d
            total = sum(x[3].size() for x in _lidos.values())
            while total > TETO_BYTES and len(_lidos) > 1:
                total -= _lidos.popitem(last=False)[1][3].size()
    medidas["ms_leitura_max"] = max(medidas["ms_leitura_max"], (time.perf_counter() - t0) * 1000)
    try: _leitor.chegou.emit(p)
    except RuntimeError: pass


def aquecer(caminho):
    """lê o arquivo no fundo (o próximo slide): quando o item pedir, os bytes já estão na memória"""
    p = _limpa(caminho)
    with _trava:
        if not p or p in _lidos or p in _lendo: return
        _lendo.add(p)
    threading.Thread(target=_le, args=(p,), daemon=True).start()


def _limpa(v):
    v = str(v or "")
    return QUrl(v).toLocalFile() if v.startswith("file:") else v


def _solta(chave):
    e = _tex.get(chave)
    if e:
        e[2] -= 1
        if e[2] <= 0: e[3] = time.perf_counter()


# ---- O CAMINHO DO OPENGL (Linux, o Vaio; 10/11 23h59). O Qt 6.9.3 no OpenGL NÃO entrega BC7 à placa ("Compressed
# format 28 not mappable to GL compressed format": a folha não aparece, medido por foto), embora a PALM aceite
# (GL_ARB_texture_compression_bptc). Então a textura é criada por NÓS no OpenGL (glCompressedTexImage2D, os bytes como
# estão) e o Qt só a recebe pela porta pública QNativeInterface::QSGOpenGLTexture::fromNative, que o PySide 6.9.3 não
# embrulha: chamada direto na libQt6Quick. No Windows (Direct3D) segue o caminho do QRhi, intocado.
_gl = {}
class _QSize(ctypes.Structure):
    _fields_ = [("w", ctypes.c_int), ("h", ctypes.c_int)]

def _gl_pronto():
    if not _gl:
        import PySide6
        g = None
        for n in ("libOpenGL.so.0", "libGL.so.1", "libGLESv2.so.2"):
            try: g = ctypes.CDLL(n); break
            except OSError: pass
        g.glGetIntegerv.argtypes = [ctypes.c_uint, ctypes.POINTER(ctypes.c_int)]
        g.glGenTextures.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]
        g.glDeleteTextures.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]
        g.glBindTexture.argtypes = [ctypes.c_uint, ctypes.c_uint]
        g.glTexParameteri.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_int]
        g.glCompressedTexImage2D.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_int,
                                             ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
        g.glGetError.restype = ctypes.c_uint
        q = ctypes.CDLL(os.path.join(os.path.dirname(PySide6.__file__), "Qt", "lib", "libQt6Quick.so.6"))
        f = q["_ZN16QNativeInterface16QSGOpenGLTexture10fromNativeEjP12QQuickWindowRK5QSize6QFlagsINS1_19CreateTextureOptionEE"]
        f.restype = ctypes.c_void_p; f.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.POINTER(_QSize), ctypes.c_int]
        _gl["g"] = g; _gl["capa"] = f
    return _gl["g"]

def _gl_cria(fmt, w, h, dados):
    """na linha do desenho, com o contexto do Qt ativo: cria a textura e devolve a ligação de antes (o Qt não percebe)"""
    g = _gl_pronto(); antes = ctypes.c_int(0); g.glGetIntegerv(0x8069, ctypes.byref(antes))
    t = ctypes.c_uint(0); g.glGenTextures(1, ctypes.byref(t)); g.glBindTexture(0x0DE1, t.value)
    for p, v in ((0x2801, 0x2601), (0x2800, 0x2601), (0x2802, 0x812F), (0x2803, 0x812F), (0x813D, 0)):
        g.glTexParameteri(0x0DE1, p, v)
    while g.glGetError(): pass
    b = dados.data()
    g.glCompressedTexImage2D(0x0DE1, 0, fmt, w, h, 0, len(b), b)
    erro = g.glGetError(); g.glBindTexture(0x0DE1, antes.value)
    if erro:
        g.glDeleteTextures(1, ctypes.byref(t)); raise RuntimeError("OpenGL recusou a textura 0x%X: erro 0x%X" % (fmt, erro))
    return _TexGL(t.value, w, h)

class _TexGL:
    def __init__(self, n, w, h): self.n = n; self.w = w; self.h = h
    def pixelSize(self): return QSize(self.w, self.h)
    def capa(self, win):
        p = _gl["capa"](self.n, shiboken6.getCppPointer(win)[0], ctypes.byref(_QSize(self.w, self.h)),
                        int(QQuickWindow.TextureHasAlphaChannel.value))
        return shiboken6.wrapInstance(p, QSGTexture)
    def apaga(self):
        t = ctypes.c_uint(self.n); _gl["g"].glDeleteTextures(1, ctypes.byref(t))

_api = []
def _e_opengl(win):
    if not _api:
        _api.append(win.rendererInterface().graphicsApi() == QSGRendererInterface.GraphicsApi.OpenGL)
    return _api[0]


def _janela_de(item):
    """a janela do item SEM perguntar item.window(): essa pergunta faz o Python amarrar a janela ao item, e quando o
    item morre (troca de slide) a JANELA é dada como morta no Python ("QQuickWindow already deleted": o telão e o painel
    sumiram do banco, isolado 10/11 23h53 com 13 itens destruídos). A procura pela lista de janelas não amarra nada."""
    for j in QGuiApplication.allWindows():
        if isinstance(j, QQuickWindow) and j.contentItem().isAncestorOf(item):
            return j
    return None


class TexBC(QQuickItem):
    fonteMudou = Signal(); recorteMudou = Signal(); prontaMudou = Signal()

    def __init__(self, parent=None):
        super().__init__(parent); self.setFlag(QQuickItem.ItemHasContents, True)
        self._fonte = ""; self._recorte = QRectF(); self._pronta = False; self._node = None; self._sg = None; self._tam = QSize()
        self._caixa = caixa = [None]                       # a chave da textura em uso (para soltar quando o item morre)
        self.destroyed.connect(lambda *_: _solta(caixa[0]))
        _leitor.chegou.connect(self._chegou)

    def _get_fonte(self): return self._fonte
    def _set_fonte(self, v):
        v = _limpa(v)
        if v == self._fonte: return
        self._fonte = v; self.fonteMudou.emit()
        tem = bool(v) and v in _lidos
        if v and not tem: aquecer(v)
        self._poe_pronta(tem); self.update()
    fonte = Property(str, _get_fonte, _set_fonte, notify=fonteMudou)

    def _get_recorte(self): return self._recorte
    def _set_recorte(self, r):
        if r == self._recorte: return
        self._recorte = QRectF(r); self.recorteMudou.emit(); self.update()
    recorte = Property(QRectF, _get_recorte, _set_recorte, notify=recorteMudou)

    def _get_pronta(self): return self._pronta
    pronta = Property(bool, _get_pronta, notify=prontaMudou)
    def _poe_pronta(self, v):
        if v != self._pronta: self._pronta = v; self.prontaMudou.emit()

    def _chegou(self, p):
        if p == self._fonte and p in _lidos:
            self._poe_pronta(True); self.update()

    def geometryChange(self, novo, velho):
        super().geometryChange(novo, velho); self.update()

    def updatePaintNode(self, velho, _d):          # na linha do desenho, com a interface parada: curto
        try:
            # o Qt apagou o nó (o item saiu da cena, entrou/saiu de um layer): a capa foi junto. Vale SEMPRE, antes de
            # qualquer uso (11/11: só valia com a folha lida, e o nó morto era usado adiante)
            if velho is None: self._node = None; self._sg = None
            win = _janela_de(self)
            d = _lidos.get(self._fonte) if self._fonte else None
            if d is not None and win is not None:
                chave = (int(win.winId()), self._fonte)
                e = _tex.get(chave)
                if e is None:
                    t0 = time.perf_counter(); fmt, w, h, dados = d
                    if _e_opengl(win):
                        tex = _gl_cria(fmt, w, h, dados)
                    else:
                        rhi = win.rhi()
                        tex = rhi.newTexture(FORMATOS[fmt], QSize(w, h), 1)
                        tex.create()
                        lote = rhi.nextResourceUpdateBatch()
                        lote.uploadTexture(tex, QRhiTextureUploadDescription(QRhiTextureUploadEntry(
                            0, 0, QRhiTextureSubresourceUploadDescription(dados))))
                        win.swapChain().currentFrameCommandBuffer().resourceUpdate(lote)
                    e = _tex[chave] = [tex, None, 0, 0.0, dados.size()]
                    medidas["envios"] += 1; medidas["placa_bytes"] += dados.size()
                    medidas["ms_envio_max"] = max(medidas["ms_envio_max"], (time.perf_counter() - t0) * 1000)
                    _varre(chave)
                if self._caixa[0] != chave or self._node is None:
                    if self._caixa[0] != chave:
                        _solta(self._caixa[0]); e[2] += 1; self._caixa[0] = chave
                    # a capa (QSGTexture) é DESTE item: dividida entre itens, morria com o nó do primeiro que saía
                    # (banco 10/11 23h28: "QSGTexture already deleted" 93x). O que se divide é só a textura da placa.
                    gl = isinstance(e[0], _TexGL)
                    sg = e[0].capa(win) if gl else win.createTextureFromRhiTexture(e[0], QQuickWindow.TextureHasAlphaChannel)
                    if self._node is None:
                        self._node = QSGSimpleTextureNode(); self._node.setFiltering(QSGTexture.Linear)
                        self._node.setOwnsTexture(gl)       # no OpenGL a capa é do Qt (o Python não é dono): morre com o nó
                    # no OpenGL o nó é DONO da capa: o setTexture abaixo já apaga a velha. O Python nunca toca nela
                    # (11/11 00h18, Vaio: o deleteLater daqui caía em capa já morta, "general protection fault" no QtCore)
                    self._node.setTexture(sg); self._sg = sg; self._tam = e[0].pixelSize()
            if self._node is None or self._sg is None: return None
            self._node.setRect(self.boundingRect())
            t = self._tam
            r = self._recorte
            self._node.setSourceRect(r if (r.width() > 0 and r.height() > 0) else QRectF(0, 0, t.width(), t.height()))
            return self._node
        except Exception as ex:
            print("TexBC:", repr(ex), flush=True)
            return self._node


def _varre(poupa):
    """passou do teto da placa: solta as texturas sem uso há mais de 3 s, a mais antiga primeiro (na linha do desenho)"""
    if medidas["placa_bytes"] <= TETO_PLACA: return
    agora = time.perf_counter()
    for chave, e in sorted(_tex.items(), key=lambda kv: kv[1][3]):
        if medidas["placa_bytes"] <= TETO_PLACA: break
        if chave == poupa or e[2] > 0 or agora - e[3] < 3: continue
        del _tex[chave]
        medidas["placa_bytes"] -= e[4]; medidas["soltas"] += 1
        try:
            if isinstance(e[0], _TexGL): e[0].apaga()
            else:
                e[0].deleteLater()
                shiboken6.Shiboken.invalidate(e[0])
        except Exception as ex:
            print("TexBC solta:", repr(ex), flush=True)


_registrado = False
def registrar():
    global _registrado
    if not _registrado:
        qmlRegisterType(TexBC, "Casa", 1, 0, "TexBC"); _registrado = True
