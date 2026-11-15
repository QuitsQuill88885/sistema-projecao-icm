// AS ABAS DE GRADE da 3.0.13 (<div class="view centro"> com .card e .grid-fundos): FUNDOS (renderFundos) e APRESENTAÇÕES
// (renderApresentacoes). Cartões com a miniatura 16:9 e o nome; com o mouse em cima aparecem as ações no canto (Espera, ✕);
// o último cartão é o "+" tracejado. Fundos: 1 clique projeta, 2 cliques = tela de espera. Apresentação: 1 clique abre no telão.
import QtQuick
import "Tema.js" as T

Item {
    id: vg
    property string tipo: "fundos"           // "fundos" | "apres"
    property var itens: []                   // fundos: controle.fundos() · apres: controle.apresentacoes()
    property var categorias: []
    property string categoria: "Todos"
    property string noAr: ""                 // o arquivo do fundo no ar (fundo-card.projetando)
    property alias grade: gv
    signal clique(int i)
    signal duplo(int i)
    signal espera(int i)
    signal apagar(int i)
    signal adicionar()

    readonly property var sCentro: T.estilo([".centro"], false)
    readonly property var sCard: T.estilo([".card"], false)
    readonly property var sDica: T.estilo([".dica"], false)
    Rectangle { anchors.fill: parent; color: vg.sCentro.background }

    readonly property var visiveis: vg.tipo === "fundos"
        ? vg.itens.filter(function (f) { return vg.categoria === "Todos" || (f.cat || "Base") === vg.categoria })
        : vg.itens

    Flickable {
        id: rolo
        anchors.fill: parent
        contentWidth: width; contentHeight: Math.max(height, card.height + vg.sCentro.padding[0] + vg.sCentro.padding[2])
        clip: true; boundsBehavior: Flickable.StopAtBounds
        Rectangle {
            id: card; objectName: "card_" + vg.tipo
            width: Math.min(880, rolo.width * 0.96)                 // style="width:min(880px,96%)"
            height: corpo.height + vg.sCard.padding[0] + vg.sCard.padding[2] + 2 * vg.sCard.border.w
            x: Math.round((rolo.width - width) / 2)
            y: Math.max(vg.sCentro.padding[0], Math.round((rolo.contentHeight - height) / 2))
            radius: vg.sCard["border-radius"]; border.width: vg.sCard.border.w; border.color: vg.sCard.border.cor
            gradient: Gradient {
                GradientStop { position: 0; color: vg.sCard.background.paradas[0].c }
                GradientStop { position: 1; color: vg.sCard.background.paradas[1].c }
            }
            RectShadowCSS { z: -1; anchors.fill: parent; radius: parent.radius; sombra: vg.sCard["box-shadow"][0] }
            Column {
                id: corpo
                x: vg.sCard.padding[3] + vg.sCard.border.w; y: vg.sCard.padding[0] + vg.sCard.border.w
                width: card.width - vg.sCard.padding[1] - vg.sCard.padding[3] - 2 * vg.sCard.border.w
                Caixa { clicavel: false; alinhar: Qt.AlignLeft; sels: [".card h2"]; herda: ({ "font-weight": 700 })
                        texto: vg.tipo === "fundos" ? "Fundos" : "Apresentações" }
                Item { width: 1; height: T.estilo([".card h2"], false)["margin-bottom"] }
                // a dica (.dica; logo depois do h2 a margem de baixo é 18: .card h2+.dica)
                Letra {
                    width: corpo.width; quebra: Text.WordWrap; textFormat: Text.StyledText
                    px: vg.sDica["font-size"]; color: vg.sDica.color; linha: vg.sDica["line-height"]
                    readonly property string b1: "<b><font color=\"" + T.estilo([".dica b"], false).color + "\">"
                    text: vg.tipo === "fundos"
                        ? "Clique na imagem para projetar. Ao passar o mouse, defina a " + b1 + "tela de espera</font></b> — exibida automaticamente entre os louvores — ou remova o fundo."
                        : "Clique numa apresentação: ela abre " + b1 + "já no telão</font></b>, no slide 1, como um louvor. Ao passar o mouse, remova a que não usa mais. Para trazer uma nova, clique em " + b1 + "+</font></b> (PowerPoint, PDF ou imagem)."
                }
                Item { width: 1; height: T.estilo([".card h2+.dica"], false)["margin-bottom"] || 18 }
                // as categorias dos fundos (.fundo-cats > .fcat)
                Flow {
                    visible: vg.tipo === "fundos"
                    width: corpo.width; spacing: T.estilo([".fundo-cats"], false).gap
                    Repeater {
                        model: vg.tipo === "fundos" ? vg.categorias : []
                        Caixa { sels: [".fcat"]; estados: modelData === vg.categoria ? [".fcat.on"] : []; texto: modelData
                                onClicado: vg.categoria = modelData }
                    }
                }
                Item { visible: vg.tipo === "fundos"; width: 1; height: T.estilo([".fundo-cats"], false)["margin-bottom"] }
                // a grade (.grid-fundos: colunas de no mínimo 190, vão 12)
                // a grade (.grid-fundos: colunas de no mínimo 190, vão 12). Como o grid do CSS: cada FILEIRA tem a altura do
                // cartão mais alto dela (o nome comprido quebra em 2 linhas) e os cartões da fileira esticam até ela
                Column {
                    id: gv; objectName: vg.tipo === "fundos" ? "gradeFundos" : "gradeAp"
                    readonly property var sg: T.estilo([".grid-fundos"], false)
                    readonly property int colunas: Math.max(1, Math.floor((corpo.width + sg.gap) / (190 + sg.gap)))
                    readonly property real larg: (corpo.width - (colunas - 1) * sg.gap) / colunas
                    readonly property var todos: vg.visiveis.concat([{ add: true }])
                    property var xisItem: null                      // provas: o ✕ do 2º cartão
                    property real cellWidth: larg + sg.gap          // provas antigas
                    property real cellHeight: 0
                    width: corpo.width; spacing: sg.gap
                    Repeater {
                        model: Math.ceil(gv.todos.length / gv.colunas)
                        Row {
                            id: fileira
                            readonly property int linha: index
                            spacing: gv.sg.gap
                            readonly property real alto: { var m = 0; for (var k = 0; k < children.length; k++) if (children[k].alturaNatural !== undefined) m = Math.max(m, children[k].alturaNatural); return m }
                            Component.onCompleted: if (linha === 0) gv.cellHeight = Qt.binding(function () { return fileira.alto + gv.sg.gap })
                            Repeater {
                                model: gv.todos.slice(fileira.linha * gv.colunas, (fileira.linha + 1) * gv.colunas)
                                CartaoGrade {
                                    width: gv.larg; height: fileira.alto
                                    vista: vg; f: modelData; indice: fileira.linha * gv.colunas + index
                                    onXisPronto: (x) => { if (indice === 1) gv.xisItem = x }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
