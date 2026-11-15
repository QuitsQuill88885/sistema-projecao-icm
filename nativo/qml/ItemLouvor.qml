// UM LOUVOR na lista da esquerda (o .item do renderListaLouvores da 3.0.13): [♪ se já está na lista] <small>números</small>
// [<small class="etq-col">sigla</small>] título, numa linha só com reticências. As partes sentam na MESMA linha de base.
// 1 clique espera 230 ms (para não projetar o começo de um duplo clique), como o app.js.
import QtQuick
import "Tema.js" as T

Caixa {
    id: il
    property var item: ({})
    property bool sel: false
    sels: [".item"]
    estados: (item.cias ? [".item.cias"] : []).concat(item.naLista ? [".item.na-lista"] : []).concat(sel ? [".item.sel", ".item.cias.sel"] : [])
    clicavel: true
    atrasoClique: true
    texto: ""
    implicitHeight: pad[0] + tit.alturaLinha + pad[2] + (st["border-bottom"] ? st["border-bottom"].w : 0)
    readonly property real px: tamLetra
    readonly property real base: pad[0] + tit.ascPx           // a linha de base de todas as partes

    Item {
        x: il.pad[3]; width: il.width - il.pad[1] - il.pad[3]; height: il.height
        Row {
            id: linhaL
            spacing: 0
            Item {   // ♪ (.marca-lista, 11 px dourado, margem 5): já está na lista de projeção
                visible: !!il.item.naLista
                readonly property var s: T.estilo([".marca-lista"], false)
                // medido no Edge (07/11): a tinta do ♪ tem 6 px e começa no início do item; o número vem 11 px depois
                width: 11; height: 1
                Ico { x: -0.75; nome: "nota"; cor: parent.s.color; tam: 7.6; y: il.base - tam * 0.92 - 1 }
            }
            Letra {   // os números (<small>: 13 x 0,8333 = 10,83 px, cor #7f9ac0, margem 5)
                readonly property var s: T.estilo([".item small"], false)
                px: il.px / 1.2; color: s.color; text: il.item.nums || "—"
                y: il.base - ascPx; width: implicitWidth + s["margin-right"]
            }
            Letra {   // a sigla da coletânea, só na busca por palavras (.etq-col)
                visible: !!il.item.sigla
                readonly property var s: T.estilo([".item small.etq-col"], false)
                px: s["font-size"]; color: s.color; lsCss: s["letter-spacing"]; text: il.item.sigla || ""
                y: il.base - ascPx; width: visible ? implicitWidth + s["margin-right"] : 0
            }
            Letra {
                id: tit
                px: il.px; color: il.corLetra; weight: il.numOu(il.st["font-weight"], 400)
                linha: 1.3                          // .item{line-height:1.3}
                text: il.item.tit || ""
                y: il.pad[0]
                largura: Math.max(0, il.width - il.pad[1] - il.pad[3] - x)
            }
        }
    }
}
