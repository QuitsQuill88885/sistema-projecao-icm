// FORMA B, "ESTILO JOGO" (PROTÓTIPO, 08/11/2026; ideia dele): a animação de um slide como o FUNDO PARADO + uma FOLHA DE
// QUADROS com só os pedaços que mudam (ferramentas/anim_sprites.py). A placa recebe as duas imagens UMA vez; a cada
// quadro só muda o recorte da folha em cada região: zero decodificação por quadro. Só entra com NATIVO_ANIM_FORMATO=B
// e onde a folha já foi gerada (cache_sprites/): é para a medida A/B/C no Vaio, não para o culto.
import QtQuick

Item {
    id: sp
    property var dados: null                 // {fundo, folha, w, h, quadros: [ms], regioes: [{x, y, w, h, fx: [..], fy}]}
    property bool tocando: visible
    property int k: 0
    // 10/11: o JPEG leve do slide já está embaixo (o mesmo 1º quadro): a folha desenha só os recortes, e o fundo.png (PNG
    // de 1920, 0,7-3,5 MB) nem abre
    property bool semFundo: false
    readonly property real esc: dados ? Math.min(width / dados.w, height / dados.h) : 1     // PreserveAspectFit
    readonly property real ox: dados ? (width - dados.w * esc) / 2 : 0
    readonly property real oy: dados ? (height - dados.h * esc) / 2 : 0
    // 10/11 (): a folha em BC7 pela textura nossa (SpriteBC.qml), onde o Sistema a oferece (dados.folhaBC)
    readonly property bool bc: temTexBC && !!dados && !!dados.folhaBC
    readonly property bool pronta: !!dados && (semFundo || fundoS.status === Image.Ready)
                                   && (bc ? (!!bcL.item && bcL.item.pronta) : folhaS.status === Image.Ready)
    Loader { id: bcL; anchors.fill: parent; z: 1; active: sp.bc; source: "SpriteBC.qml"; onLoaded: item.dono = sp }
    Image {
        id: fundoS
        x: sp.ox; y: sp.oy; width: sp.dados ? sp.dados.w * sp.esc : 0; height: sp.dados ? sp.dados.h * sp.esc : 0
        source: sp.dados && !sp.semFundo ? sp.dados.fundo : ""; asynchronous: true; cache: true; smooth: true
    }
    Image { id: folhaS; visible: false; source: sp.dados && !sp.bc ? sp.dados.folha : ""; asynchronous: true; cache: true }
    Repeater {
        model: sp.pronta && !sp.bc ? sp.dados.regioes : []
        Item {
            x: sp.ox + modelData.x * sp.esc; y: sp.oy + modelData.y * sp.esc
            width: modelData.w * sp.esc; height: modelData.h * sp.esc
            clip: true
            Image {                                   // a MESMA folha (uma textura só, o cache do Qt divide)
                source: sp.dados.folha; cache: true; smooth: true
                width: folhaS.implicitWidth * sp.esc; height: folhaS.implicitHeight * sp.esc
                x: -modelData.fx[sp.k] * sp.esc; y: -modelData.fy * sp.esc
            }
        }
    }
    // 10/11 (regra dele: o operador vê o MESMO quadro do telão): o quadro vem do RELÓGIO, não de uma contagem própria;
    // o telão, o "No telão agora" e o retorno, cada um com a sua cópia da folha, mostram o mesmo quadro no mesmo instante.
    // O ritmo é o do arquivo original (os ms de cada quadro do WebP).
    readonly property int total: { var t = 0; if (dados) for (var i = 0; i < dados.quadros.length; i++) t += (dados.quadros[i] || 100); return t }
    function acerta() {
        if (!dados || total <= 0) return
        var f = Date.now() % total, acc = 0
        for (var i = 0; i < dados.quadros.length; i++) {
            var d = dados.quadros[i] || 100
            if (f < acc + d) { k = i; relogio.interval = Math.max(1, acc + d - f); return }
            acc += d
        }
    }
    Timer {
        id: relogio
        running: sp.tocando && sp.pronta && sp.dados.quadros.length > 1
        repeat: true
        onRunningChanged: if (running) sp.acerta()
        onTriggered: sp.acerta()
    }
}
