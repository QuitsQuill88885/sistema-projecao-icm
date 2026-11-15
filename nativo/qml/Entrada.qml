// UM CAMPO DE TEXTO (<input>) da 3.0.13, desenhado pelas regras do app.css (fundo, borda, cantos, padding, letra) e
// com o foco como o navegador (input:focus: borda dourada). A letra segue a regra única (Letra: Painel ICM, x 1,032,
// montada 8x e reduzida para o tamanho em fração de px não se perder).
import QtQuick
import "Tema.js" as T

Rectangle {
    id: en
    property var sels: ["input"]
    property alias text: campo.text
    property string placeholder: ""
    property color corPlaceholder: "#757575"      // o ::placeholder do Edge (medido: rgb 117,117,117)
    property bool navegador: true                 // <input> sem type: a letra do navegador (Arial -> Liberation Sans)
    property alias campo: campo
    signal aceito()
    signal teclaBaixo()
    readonly property var st: T.estilo(sels.concat(campo.activeFocus ? ["input:focus"] : []), false)
    readonly property var pad: st.padding || [0, 0, 0, 0]
    readonly property real px: typeof st["font-size"] === "number" ? st["font-size"] : 13.333
    readonly property real tamReal: navegador ? px : T.tam(px)
    readonly property real fAsc: navegador ? T.FONTE.campo.asc : T.FONTE.asc
    readonly property real fDesc: navegador ? T.FONTE.campo.desc : T.FONTE.desc
    readonly property real k: tamReal / Math.round(tamReal * 8)
    readonly property real conteudo: Math.round(fAsc * px) + Math.round(fDesc * px)
    // <input> sem width no CSS: a regra do Chromium (size=20): conteúdo = 20 x a largura média + (a maior letra - a média).
    // Na Segoe: média 1103/2048 em (OS/2) e a "maior letra" que ele usa = 1,111 em, arredondada (medido: 179 px a 13,5 px)
    property bool larguraPadrao: false
    readonly property real mediaPx: 1103 / 2048 * px
    implicitWidth: larguraPadrao ? 19 * mediaPx + Math.round(1.111 * px) + pad[1] + pad[3] + 2 * (st.border ? st.border.w : 0) : 0
    property real alturaFixa: 0                    // ex.: o rótulo do timer (height:36px; padding-top/bottom:0)
    implicitHeight: alturaFixa > 0 ? alturaFixa : pad[0] + conteudo + pad[2] + 2 * (st.border ? st.border.w : 0)
    radius: st["border-radius"] || 0
    color: T.fundo(st.background !== undefined ? st.background : st["background-color"])
    border.width: st.border ? st.border.w : 0
    border.color: st["border-color"] || (st.border ? st.border.cor : "transparent")

    Item {
        id: area
        x: en.pad[3] + en.border.width; y: en.alturaFixa > 0 ? (en.height - en.conteudo) / 2 : en.pad[0] + en.border.width
        width: en.width - x - en.pad[1] - en.border.width; height: en.conteudo
        clip: true
        Letra {
            visible: campo.text === "" && en.placeholder !== ""
            text: en.placeholder; px: en.px; color: en.corPlaceholder; largura: area.width; navegador: en.navegador
        }
        TextInput {
            id: campo
            transformOrigin: Item.TopLeft; scale: en.k
            y: Math.round(en.fAsc * en.px) - en.fAsc * en.tamReal
            width: area.width / en.k
            color: en.st.color || "#ffffff"
            font.family: en.navegador ? T.FONTE.campo.familia : T.FONTE.familia; font.pixelSize: Math.max(1, Math.round(en.tamReal * 8) || 1)
            font.hintingPreference: Font.PreferNoHinting
            selectByMouse: true; clip: true
            selectionColor: "#3b5680"
            cursorDelegate: Rectangle { width: 1 / en.k; color: campo.color; visible: campo.activeFocus && campo.cursorVisible }
            onAccepted: en.aceito()
            Keys.onDownPressed: en.teclaBaixo()
        }
    }
    MouseArea { anchors.fill: parent; cursorShape: Qt.IBeamCursor; onPressed: (m) => { campo.forceActiveFocus(); m.accepted = false } }
}
