// UM LADO do palco do modo apresentação (.apr-lado da 3.0.13): o slide anterior (apagado e menos saturado) ou o próximo,
// com a etiqueta em cima; com o mouse, o aviso dourado "clique para projetar". Sem anterior some; no fim, "Fim da apresentação".
import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
import "Tema.js" as T

Item {
    id: l
    property bool ant: false
    property bool vazio: false
    property bool fim: false
    property string fonte: ""
    property bool animada: false
    property string tag: ""
    property bool pb: false                 // o modo apresentação (body.pb-on): etiqueta 12,5 / 600 e o anterior a 55%
    property bool gestos: false             // o selo "gestos" no canto (o slide tem gestos)
    property int esmaece: 250               // o tempo do esmaecimento da imagem (o modo apresentação passa o do telão)
    property bool segura: false             // a imagem nova espera o telão começar a troca (todo mundo junto, 11/11)
    signal clicado()
    height: width * 9 / 16
    visible: !vazio
    Letra { anchors.horizontalCenter: parent.horizontalCenter; y: -22; px: l.pb ? 12.5 : 11; lsCss: 0.8; maiusculas: true
            weight: l.pb ? 600 : 400
            color: l.pb ? (l.ant ? "#d5deec" : "#ffffff") : (l.ant ? "#9fb0cc" : "#e6eefb"); text: l.tag }
    // body.pb-on #apr .apr-lado.px .apr-q{outline:2px solid #e6eefb66;outline-offset:3px;border-radius:8px}
    Rectangle { visible: l.pb && !l.ant && !l.fim; anchors.fill: parent; anchors.margins: -5; radius: 10; color: "transparent"
                border.width: 2; border.color: "#66e6eefb" }
    RectShadowCSS { visible: !l.fim; anchors.fill: parent; radius: 6; sombra: ({ x: 0, y: 6, blur: 18, spread: 0, cor: "#99000000", inset: false }) }
    Rectangle { visible: !l.fim; anchors.fill: parent; radius: 6; color: "black" }
    ImgSlide {
        id: img
        // 08/11 21h (teste dele no PC da igreja, "aquele bug do loop"): o anterior e o próximo ficam PARADOS. Só o telão, a
        // prévia e o "No telão agora" animam; os dois quadrinhos entravam na mesma fila de decodificação do slide no ar
        visible: !l.fim; anchors.fill: parent; fonte: l.fonte; animada: false; largura: 400
        esmaece: l.esmaece; segura: l.segura
        opacity: l.ant ? (l.pb ? 0.55 : 0.38) : 1
        // 11/11 (ele: "arredondamento falso"): os cantos eram pintados por cima numa cor fixa, que não batia com o degradê
        // do fundo. Agora a imagem é RECORTADA redonda de verdade (máscara), no mesmo efeito do filter:saturate(.6) do anterior
        layer.enabled: true
        layer.effect: MultiEffect { saturation: l.ant ? -0.4 : 0; maskEnabled: true; maskSource: masc
                                    maskThresholdMin: 0.5; maskSpreadAtMin: 1.0 }
    }
    Item { id: masc; anchors.fill: parent; layer.enabled: true; visible: false
           Rectangle { anchors.fill: parent; radius: 6; color: "black" } }
    SeloGestos { visible: l.gestos && !l.fim }
    // o fim (.apr-fim-q): a caixa tracejada
    Rectangle {
        visible: l.fim; anchors.fill: parent; radius: 6; color: "#0b1526"
        Shape {   // border:1px dashed
            anchors.fill: parent; preferredRendererType: Shape.CurveRenderer
            ShapePath { strokeColor: T.V.borda; strokeWidth: 1; fillColor: "transparent"; strokeStyle: ShapePath.DashLine; dashPattern: [3, 3]
                        PathRectangle { x: 0.5; y: 0.5; width: l.width - 1; height: l.height - 1; radius: 5.5 } }
        }
        Letra { anchors.centerIn: parent; px: 11; color: "#8396b6"; text: "Fim da apresentação" }
    }
    // o aviso "clique para projetar" (.apr-hint), só com o mouse e só com slide
    Rectangle {
        visible: ma.containsMouse && !l.fim
        anchors.fill: parent; radius: 6; color: "#b00b1526"; border.width: 2; border.color: T.V.ouro
        Column {
            anchors.centerIn: parent; spacing: 2
            Ico { anchors.horizontalCenter: parent.horizontalCenter; nome: l.ant ? "ant" : "prox"; tam: 24; cor: T.V.ouro }
            Letra { anchors.horizontalCenter: parent.horizontalCenter; px: 12; weight: 600; color: T.V.ouro; linha: 1.2
                    quebra: Text.WordWrap; alinhamento: Text.AlignHCenter; width: implicitTextWidth; text: "clique para\nprojetar" }
        }
    }
    MouseArea { id: ma; anchors.fill: parent; hoverEnabled: true; cursorShape: l.fim ? Qt.ArrowCursor : Qt.PointingHandCursor; onClicked: l.clicado() }
}
