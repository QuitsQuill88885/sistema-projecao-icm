// O <textarea> da 3.0.13 (o texto do card Texto & Avisos): as regras do app.css (fundo, borda, cantos 9, padding 10 12,
// letra 13,5 com line-height 1.6, no mínimo 130 de altura) e o foco dourado. A letra herda a da página (Painel ICM).
import QtQuick
import QtQuick.Window
import "Tema.js" as T

Rectangle {
    id: ta
    property alias text: ed.text
    property string placeholder: ""
    property alias campo: ed
    // a caixa inteira cabe na janela? (a alça só aparece então). A posição na janela não avisa quando muda: mede-se depois
    // de o layout assentar, ao nascer, ao mudar de altura, ao aparecer e quando a janela muda de tamanho
    property bool cabe: false
    function medir() {
        var h = ta.Window.height
        cabe = h > 0 && ta.height > 0 && ta.mapToItem(null, 0, ta.height).y <= h + 0.5
    }
    Component.onCompleted: Qt.callLater(medir)
    onHeightChanged: Qt.callLater(medir)
    onVisibleChanged: Qt.callLater(medir)
    Connections { target: ta.Window.window; ignoreUnknownSignals: true; function onHeightChanged() { Qt.callLater(ta.medir) } }
    Timer { running: ta.visible; interval: 400; onTriggered: ta.medir() }      // uma vez, quando o layout já assentou
    readonly property var st: T.estilo(["textarea"].concat(ed.activeFocus ? ["textarea:focus"] : []), false)
    readonly property var pad: st.padding
    readonly property real px: st["font-size"]
    readonly property real k: T.tam(px) / Math.round(T.tam(px) * 8)
    readonly property real lh: st["line-height"] * px
    implicitHeight: Math.max(st["min-height"], pad[0] + Math.max(1, ed.lineCount) * lh + pad[2] + 2 * st.border.w)
    radius: st["border-radius"]; color: T.fundo(st.background)
    border.width: st.border.w; border.color: st["border-color"] || st.border.cor
    // o placeholder: o navegador corta na BORDA da caixa, não no padding (a 6ª linha do editor de louvores aparece pela
    // metade embaixo); de várias linhas quebra, de uma corta com reticências
    Item {
        x: ta.border.width; y: ta.border.width; width: ta.width - 2 * ta.border.width; height: ta.height - 2 * ta.border.width
        clip: true
        Letra {
            visible: ed.text === "" && ta.placeholder !== ""
            readonly property bool varias: ta.placeholder.indexOf(String.fromCharCode(10)) >= 0
            x: ta.pad[3]; y: ta.pad[0]
            text: ta.placeholder; px: ta.px; color: "#757575"; linha: 1.6
            largura: varias ? -1 : fl.width; width: fl.width; quebra: varias ? Text.WordWrap : Text.NoWrap
        }
    }
    // a ALÇA de redimensionar do Chromium (textarea{resize:vertical}), medida pixel a pixel no Edge: dois riscos na
    // diagonal, cinza #9d9d9d com um pixel escuro à esquerda, a 2 px do canto de dentro (o longo de 6, o curto de 2)
    // (medido 07/11: na aba Texto o textarea passa 5 px do fim da janela e o Chromium NÃO pinta a alça; no editor de
    // louvores ela cabe inteira e aparece. A alça só aparece com a caixa inteira dentro da janela)
    Item {
        visible: ta.cabe
        x: ta.width - ta.border.width - 1; y: ta.height - ta.border.width - 1   // o último pixel de dentro
        Repeater {
            model: [[-2, -7], [-3, -6], [-4, -5], [-5, -4], [-6, -3], [-7, -2], [-2, -3], [-3, -2]]
            Item {
                x: modelData[0]; y: modelData[1]
                Rectangle { width: 1; height: 1; color: "#9d9d9d" }
                Rectangle { x: -1; width: 1; height: 1; color: "#040404" }
            }
        }
    }
    Flickable {
        id: fl
        x: ta.pad[3] + ta.border.width; y: ta.pad[0] + ta.border.width
        width: ta.width - x - ta.pad[1] - ta.border.width; height: ta.height - y - ta.pad[2] - ta.border.width
        clip: true; contentHeight: ed.height * ta.k; boundsBehavior: Flickable.StopAtBounds
        TextEdit {
            id: ed
            transformOrigin: Item.TopLeft; scale: ta.k
            width: fl.width / ta.k
            // com a altura FIXA por parágrafo o Qt põe toda a sobra da linha em cima da letra (o navegador divide meio a
            // meio): desconta essa sobra
            y: (ta.lh - (Math.round(T.FONTE.asc * ta.px) + Math.round(T.FONTE.desc * ta.px))) / 2 + Math.round(T.FONTE.asc * ta.px) - T.FONTE.asc * T.tam(ta.px)
               - (ta.lh - (T.FONTE.asc + T.FONTE.desc) * T.tam(ta.px))
            color: ta.st.color
            font.family: T.FONTE.familia; font.pixelSize: Math.max(1, Math.round(T.tam(ta.px) * 8))
            font.hintingPreference: Font.PreferNoHinting
            wrapMode: TextEdit.Wrap; selectByMouse: true; selectionColor: "#3b5680"
            // o line-height 1,6 do <textarea>: o TextEdit não tem a propriedade; o Python põe a altura FIXA em cada
            // parágrafo do documento (na escala ampliada do campo)
            onTextChanged: Qt.callLater(function () { controle.linhaFixa(ed.textDocument, ta.lh / ta.k) })
            Component.onCompleted: controle.linhaFixa(ed.textDocument, ta.lh / ta.k)
        }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.IBeamCursor; onPressed: (m) => { ed.forceActiveFocus(); m.accepted = false } }
}
