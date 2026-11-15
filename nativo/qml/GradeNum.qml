// A GRADE DE NÚMEROS da Bíblia (.grid-num: auto-fill de colunas com no mínimo 44 px, vão de 6, borda de 10 x 12),
// os capítulos ou os versículos. Cada número é um .gnum: o escolhido em vermelho (.sel), o que já está na lista com a
// barrinha dourada embaixo (.na-fila), o da referência digitada com o contorno dourado (.alvo-busca).
// GridView reaproveita os itens (o Repeater que recria Text vaza memória no Qt 6.12).
import QtQuick
import "Tema.js" as T

Item {
    id: g
    property var modelo: []                 // número de capítulos (int) ou a lista de versículos [{v, t, naFila}]
    property int selecionado: -1
    property int alvo: -1
    signal clique(int n)
    signal duplo(int n)
    readonly property var sg: T.estilo([".grid-num"], false)
    readonly property real gap: sg.gap
    readonly property real util: width - sg.padding[1] - sg.padding[3]
    // repeat(auto-fill, minmax(44px, 1fr)): quantas colunas de 44 cabem, e cada uma estica igual
    readonly property int colunas: Math.max(1, Math.floor((util + gap) / (44 + gap)))
    readonly property real celula: (util + gap) / colunas
    readonly property var sn: T.estilo([".gnum"], false)
    readonly property real alturaNum: sn.padding[0] + Math.round(T.FONTE.asc * sn["font-size"]) + Math.round(T.FONTE.desc * sn["font-size"]) + sn.padding[2]
    readonly property int quantos: typeof modelo === "number" ? modelo : modelo.length
    implicitHeight: sg.padding[0] + Math.ceil(quantos / colunas) * (alturaNum + gap) - gap + sg.padding[2]
    clip: true
    GridView {
        id: gv
        x: g.sg.padding[3]; y: g.sg.padding[0]
        width: g.util + g.gap; height: g.height - g.sg.padding[0]
        cellWidth: g.celula; cellHeight: g.alturaNum + g.gap
        model: g.modelo
        reuseItems: true; boundsBehavior: Flickable.StopAtBounds; clip: true
        bottomMargin: g.sg.padding[2]
        delegate: Caixa {
            readonly property int n: typeof g.modelo === "number" ? index + 1 : modelData.v
            width: g.celula - g.gap; height: g.alturaNum
            sels: [".gnum"]
            estados: (n === g.selecionado ? [".gnum.sel"] : []).concat(typeof g.modelo !== "number" && modelData.naFila ? [".gnum.na-fila"] : [])
            texto: String(n)
            atrasoClique: typeof g.modelo !== "number"
            onClicado: g.clique(n)
            onDuploClique: g.duplo(n)
            Rectangle {   // .gnum.alvo-busca{outline:2px solid ouro; outline-offset:-2px}
                visible: n === g.alvo
                anchors.fill: parent; radius: parent.radius; color: "transparent"; border.width: 2; border.color: T.V.ouro
            }
        }
    }
}
