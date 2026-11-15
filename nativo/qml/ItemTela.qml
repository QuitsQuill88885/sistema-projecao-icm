// UMA TELA do louvor na coluna do meio (o .item do desenharSlidesLouvor da 3.0.13): <small> rótulo dourado </small><br>
// as 2 primeiras linhas (… se tiver mais). Animada (CIAS): a miniatura 96x54 e "Tela k de n · animada".
// A tela no ar fica marcada (.item.sel). 1 clique projeta; 2 cliques põem o louvor na lista.
import QtQuick
import "Tema.js" as T

Caixa {
    id: tl
    property int k: 0
    property var tela: ({})
    property bool sel: false
    sels: [".item", "#lista-slides .item"]
    estados: (tela.img ? ["#lista-slides .item.anim"] : []).concat(sel ? [".item.sel"] : [])
    clicavel: true
    texto: ""
    readonly property real px: tamLetra
    readonly property real lh: 1.3 * px                     // .item{line-height:1.3}: a linha do item
    readonly property real conteudoH: tela.img ? 54 + 2 : (tela.rot ? lh : 0) + linhas.implicitHeight
    implicitHeight: pad[0] + conteudoH + pad[2] + (st["border-bottom"] ? st["border-bottom"].w : 0)

    // animada: a miniatura e o rótulo, lado a lado (flex, gap 10, centro)
    Row {
        visible: !!tl.tela.img
        x: tl.pad[3]; y: tl.pad[0]; spacing: 10
        Rectangle {
            readonly property var s: T.estilo(["#lista-slides .anim-mini"], false)
            width: s.width; height: s.height; radius: s["border-radius"]; color: s.background
            border.width: s.border.w; border.color: s.border.cor
            Image { anchors.fill: parent; anchors.margins: 1; source: tl.tela.img || ""; fillMode: Image.Stretch
                    sourceSize.width: 96; sourceSize.height: 54; asynchronous: true; cache: false }
        }
        Letra { px: tl.px / 1.2; color: "#f5d76e"; text: tl.tela.rot || ""; anchors.verticalCenter: parent.verticalCenter }
    }
    // texto: o rótulo (CORO, FINAL...) numa linha, e as linhas da letra
    Item {
        visible: !tl.tela.img
        x: tl.pad[3]; y: tl.pad[0]; width: tl.width - tl.pad[1] - tl.pad[3]
        Letra {   // o <small> na 1ª linha: senta na linha de base da linha de 13 px
            id: rotulo
            visible: !!tl.tela.rot
            px: tl.px / 1.2; color: "#f5d76e"; text: tl.tela.rot || ""
            readonly property real baseLinha: Math.round(T.FONTE.asc * tl.px) + (tl.lh - (Math.round(T.FONTE.asc * tl.px) + Math.round(T.FONTE.desc * tl.px))) / 2
            y: baseLinha - ascPx
        }
        Letra {
            id: linhas
            y: tl.tela.rot ? tl.lh : 0
            width: parent.width
            px: tl.px; color: tl.corLetra; weight: tl.numOu(tl.st["font-weight"], 400)
            linha: 1.3; quebra: Text.WordWrap
            text: tl.tela.txt || ""
        }
    }
}
