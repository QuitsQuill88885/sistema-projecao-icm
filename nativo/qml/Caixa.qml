// UM ELEMENTO do HTML da 3.0.13 (botão, aba, item...) desenhado pelas regras do app.css que valem para as classes dele.
// Nada de cor ou medida escrita aqui: tudo vem do Tema.js, que o conversor gera a partir do app.css.
//   sels: as classes, do geral ao específico (ex.: [".ctrl", ".nav2 .nav"]); estados: as que ligam e desligam (".tab.ativo")
import QtQuick
import QtQuick.Effects
import "Tema.js" as T

Rectangle {
    id: cx
    property var sels: []
    property var estados: []
    property string texto: ""
    property string icone: ""
    property real icoTam: 0                 // 0 = o font-size do ".ico" da classe (ou o da letra)
    property var herda: ({})                // o que o CSS herdaria do pai (cor e tamanho da letra)
    property bool clicavel: true
    property bool forcarSobre: false        // provas: desenhar como se o mouse estivesse em cima
    property alias rotulo: txt
    property alias area: ma
    property int alinhar: Qt.AlignHCenter   // justify-content
    property real larguraTexto: -1          // texto com reticências quando não cabe (text-overflow: ellipsis)
    property var bolinha: []
    property string rotuloAntes: ""         // um <small> antes do texto (o "no telão" / "próximo louvor" do chip)
    property bool pulso: false              // o "pulso" do clique da 3.0.13 (.pulso: encolhe a 94% e volta em 0,4 s)
    property bool atrasoClique: false       // listas: 1 clique espera 230 ms (não projeta o começo de um duplo clique)                // as classes de uma bolinha antes do texto (a .dot da barra de estado)
    readonly property bool sobre: (ma.containsMouse && clicavel) || forcarSobre
    readonly property var st: T.estilo(sels.concat(estados), sobre)
    readonly property var pad: st["padding"] || [0, 0, 0, 0]
    readonly property real tamLetra: typeof st["font-size"] === "number" ? st["font-size"] : (herda["font-size"] || 13.333)
    property string letraFixa: ""           // uma cor de letra que vence a do estilo (o "Abrir Projeção" dourado, 11/11)
    readonly property color corLetra: letraFixa || st["color"] || herda["color"] || T.V["txt"]
    signal clicado()
    signal duploClique()

    // (o nome é numOu, e não n: peças que usam a Caixa têm a PROPRIEDADE n, que escondia a função)
    function numOu(v, padrao) { return typeof v === "number" ? v : padrao }
    function ls() { var l = st["letter-spacing"]; return typeof l === "number" ? l : (l && l.em ? l.em * tamLetra : 0) }

    implicitWidth: numOu(st["width"], linha.implicitWidth + numOu(pad[1], 0) + numOu(pad[3], 0) + 2 * bw)
    implicitHeight: numOu(st["height"], linha.implicitHeight + numOu(pad[0], 0) + numOu(pad[2], 0) + 2 * bw)
    readonly property var borda: st["border"] || { w: 0, cor: "transparent" }
    readonly property real bw: numOu(borda.w, 0)
    radius: numOu(st["border-radius"], cantos ? Math.max(cantos[0], cantos[1], cantos[2], cantos[3]) : 0)
    // o border-radius de 2 a 4 valores do CSS ("8px 8px 0 0", a .menu-aba): um raio por canto (Qt 6.7+). Antes virava 0
    // e as abas do menu (Minha igreja, Meus louvores, Celular...) ficavam QUADRADAS (relato dele 07/11 21h16)
    readonly property var cantos: {
        var r = st["border-radius"]
        if (typeof r !== "string" || r === "inherit") return null
        var p = r.trim().split(/\s+/).map(function (v) { return parseFloat(v) || 0 })
        if (p.length === 1) p = [p[0], p[0], p[0], p[0]]
        else if (p.length === 2) p = [p[0], p[1], p[0], p[1]]
        else if (p.length === 3) p = [p[0], p[1], p[2], p[1]]
        return p                                       // sup. esq., sup. dir., inf. dir., inf. esq. (a ordem do CSS)
    }
    topLeftRadius: cantos ? cantos[0] : radius
    topRightRadius: cantos ? cantos[1] : radius
    bottomRightRadius: cantos ? cantos[2] : radius
    bottomLeftRadius: cantos ? cantos[3] : radius
    color: T.fundo(st["background"] !== undefined ? st["background"] : st["background-color"])
    gradient: (st["background"] && st["background"].paradas) ? grad : null
    Gradient {
        id: grad
        orientation: (st["background"] && st["background"].ang === 90) ? Gradient.Horizontal : Gradient.Vertical
        GradientStop { position: 0; color: cx.st["background"] && cx.st["background"].paradas ? cx.st["background"].paradas[0].c : "transparent" }
        GradientStop { position: 1; color: cx.st["background"] && cx.st["background"].paradas ? cx.st["background"].paradas[cx.st["background"].paradas.length - 1].c : "transparent" }
    }
    border.width: bw
    border.color: st["border-color"] || borda.cor
    opacity: numOu(st["opacity"], 1)
    Behavior on color { enabled: !!cx.st["transition"]; ColorAnimation { duration: 150 } }

    // box-shadow de fora: a sombra desenhada pela placa (RectangularShadow), atrás da caixa
    readonly property var sombras: st["box-shadow"] || []
    readonly property var fora: { for (var i = 0; i < sombras.length; i++) if (!sombras[i].inset) return sombras[i]; return null }
    readonly property var dentro: { for (var i = 0; i < sombras.length; i++) if (sombras[i].inset) return sombras[i]; return null }
    RectangularShadow {
        visible: !!cx.fora; z: -1
        anchors.fill: parent; radius: cx.radius
        offset.x: cx.fora ? cx.fora.x : 0; offset.y: cx.fora ? cx.fora.y : 0
        blur: cx.fora ? cx.fora.blur : 0; spread: cx.fora ? cx.fora.spread : 0
        color: cx.fora ? cx.fora.cor : "transparent"
    }
    // box-shadow "inset Xpx 0 0 cor": a barrinha de um lado (o item da lista no ar, o louvor que já está na lista)
    // 11/11 (ele: "tem uma barra que parece que não está no lugar correto (...) ali tá meio quadrado"): a barrinha era um
    // retângulo reto e os cantos dela saíam para fora da moldura redonda. No CSS a sombra de dentro acompanha o
    // border-radius: aqui é a própria forma da caixa (com o raio dela), cortada na largura da barrinha
    Item {
        id: faixaDentro
        visible: !!cx.dentro && (cx.dentro.x !== 0 || cx.dentro.y !== 0)
        clip: true
        x: cx.dentro && cx.dentro.x < 0 ? parent.width + cx.dentro.x : 0
        y: cx.dentro && cx.dentro.y < 0 ? parent.height + cx.dentro.y : 0
        width: cx.dentro ? (cx.dentro.x !== 0 ? Math.abs(cx.dentro.x) : parent.width) : 0
        height: cx.dentro ? (cx.dentro.y !== 0 ? Math.abs(cx.dentro.y) : parent.height) : 0
        Rectangle { x: -faixaDentro.x; y: -faixaDentro.y; width: cx.width; height: cx.height; radius: cx.radius
                    color: cx.dentro ? cx.dentro.cor : "transparent" }
    }
    // bordas de um lado só (border-top / border-bottom / border-left / border-right)
    Repeater {
        model: ["border-top", "border-bottom", "border-left", "border-right"]
        Rectangle {
            readonly property var b: cx.st[modelData]
            visible: !!b && b.w > 0
            color: b ? b.cor : "transparent"
            x: modelData === "border-right" ? parent.width - (b ? b.w : 0) : 0
            y: modelData === "border-bottom" ? parent.height - (b ? b.w : 0) : 0
            width: modelData === "border-left" || modelData === "border-right" ? (b ? b.w : 0) : parent.width
            height: modelData === "border-top" || modelData === "border-bottom" ? (b ? b.w : 0) : parent.height
        }
    }

    Row {
        id: linha
        spacing: cx.numOu(cx.st["gap"], 0)
        x: cx.alinhar === Qt.AlignLeft ? cx.numOu(cx.pad[3], 0) + cx.bw
           : cx.alinhar === Qt.AlignRight ? cx.width - width - cx.numOu(cx.pad[1], 0) - cx.bw
           : Math.round((cx.width - width) / 2)
        anchors.verticalCenter: parent.verticalCenter
        Rectangle {
            id: dot
            readonly property var s: T.estilo(cx.bolinha, false)
            visible: cx.bolinha.length > 0
            width: cx.numOu(s.width, 9); height: cx.numOu(s.height, 9); radius: width / 2
            color: T.fundo(s.background)
            anchors.verticalCenter: parent.verticalCenter
            // o brilho em volta (box-shadow 0 0 9px #e23 da bolinha ao vivo)
            RectShadowCSS { z: -1; anchors.fill: parent; radius: parent.radius; sombra: (dot.s["box-shadow"] || [null])[0] }
        }
        Ico {
            visible: cx.icone !== ""
            nome: cx.icone
            cor: cx.corLetra
            tam: cx.icoTam > 0 ? cx.icoTam : (cx.numOu(T.estilo(cx.sels.map(function (s) { return s + " .ico" }), false)["font-size"], cx.tamLetra))
            anchors.verticalCenter: parent.verticalCenter
        }
        Letra {
            visible: cx.rotuloAntes !== ""
            readonly property var s: T.estilo(cx.sels.map(function (x) { return x + " small" }), false)
            text: cx.rotuloAntes; color: cx.corLetra; opacity: s.opacity !== undefined ? s.opacity : 1
            px: cx.numOu(s["font-size"], cx.tamLetra * 0.84); weight: cx.numOu(s["font-weight"], 400); lsCss: cx.numOu(s["letter-spacing"], 0)
            maiusculas: s["text-transform"] === "uppercase"
            anchors.verticalCenter: parent.verticalCenter
        }
        Letra {
            id: txt
            visible: cx.texto !== ""
            text: cx.texto
            color: cx.corLetra
            px: cx.tamLetra
            weight: cx.numOu(cx.st["font-weight"], cx.herda["font-weight"] || 400)
            lsCss: cx.ls()
            maiusculas: cx.st["text-transform"] === "uppercase"
            italico: cx.st["font-style"] === "italic"
            largura: cx.larguraTexto
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Timer { id: tClique; interval: 230; onTriggered: cx.clicado() }
    SequentialAnimation {
        id: animPulso
        NumberAnimation { target: cx; property: "scale"; to: 0.94; duration: 152; easing.type: Easing.InOutQuad }
        NumberAnimation { target: cx; property: "scale"; to: 1; duration: 248; easing.type: Easing.InOutQuad }
    }
    MouseArea {
        id: ma
        anchors.fill: parent
        enabled: cx.clicavel
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: { if (cx.pulso) animPulso.restart(); cx.atrasoClique ? tClique.restart() : cx.clicado() }
        onDoubleClicked: { tClique.stop(); cx.duploClique() }
    }
}
