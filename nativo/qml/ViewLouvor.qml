// A ABA LOUVOR da 3.0.13 (<div class="view" data-aba="louvor">): à esquerda a busca e a lista agrupada por coletânea
// (o cabeçalho da coletânea gruda no topo, como o position:sticky), à direita as telas do louvor escolhido.
// 1 clique escolhe e projeta (selecionarLouvor); 2 cliques põem na lista (adicionarLista). Tela: 1 clique projeta.
import QtQuick
import QtQuick.Controls as QC
import "Tema.js" as T

Item {
    id: vl
    property var lista: []                  // controle.listaLouvores(texto)
    property int escolhido: -1
    property string titulo: "Slides do louvor"
    property var telas: []                  // controle.telasLouvor(escolhido)
    property int telaNoAr: -1
    property alias busca: campoBusca
    signal buscar(string q)
    signal clique(int i)
    signal duplo(int i)
    signal tela(int k)
    signal telaDuplo(int k)
    signal teclaEnter()

    // grid-template-columns: minmax(220px,1fr) minmax(260px,1.3fr)
    readonly property real wEsq: Math.max(220, Math.min(width - 260, width / 2.3))
    readonly property var sCol: T.estilo([".col"], false)

    // ---- a coluna da lista (.col.col-lista)
    Rectangle {
        id: colEsq
        width: vl.wEsq; height: vl.height
        color: vl.sCol.background
        Rectangle { anchors.right: parent.right; width: vl.sCol["border-right"].w; height: parent.height; color: vl.sCol["border-right"].cor }
        // .busca (padding 8, fundo #101d33) com o input
        Rectangle {
            id: caixaBusca
            readonly property var s: T.estilo([".busca"], false)
            width: parent.width - vl.sCol["border-right"].w; height: campoBusca.height + s.padding[0] + s.padding[2]
            color: s.background
            Entrada {
                id: campoBusca; objectName: "buscaLouvor"
                sels: ["input", ".busca input"]
                x: caixaBusca.s.padding[3]; y: caixaBusca.s.padding[0]
                width: parent.width - caixaBusca.s.padding[1] - caixaBusca.s.padding[3]
                placeholder: "Buscar por nome, número ou trecho da letra…"
                onTextChanged: atraso.restart()
                onAceito: vl.teclaEnter()
                onTeclaBaixo: { lista.forceActiveFocus(); lista.currentIndex = Math.min(lista.count - 1, lista.currentIndex + 1) }
            }
            Timer { id: atraso; interval: 120; onTriggered: vl.buscar(campoBusca.text) }
        }
        ListView {
            QC.ScrollBar.vertical: BarraRolagem {}
            id: lista; objectName: "listaLouvores"
            y: caixaBusca.height; width: parent.width - vl.sCol["border-right"].w; height: parent.height - y
            clip: true; model: vl.lista; reuseItems: true
            boundsBehavior: Flickable.StopAtBounds
            section.property: "grp"
            section.labelPositioning: ViewSection.InlineLabels | ViewSection.CurrentLabelAtStart
            section.delegate: Caixa {
                required property string section
                visible: section !== ""
                height: section !== "" ? implicitHeight : 0
                width: lista.width; clicavel: false; alinhar: Qt.AlignLeft; z: 2
                // o 1º grupo não tem a linha de cima (.grupo-col:first-child{border-top:none})
                sels: [".grupo-col"]; estados: (section === "CIAS" ? [".grupo-col.cias"] : []).concat(section === (vl.lista.length ? vl.lista[0].grp : "") ? [".grupo-col:first-child"] : [])
                texto: section
            }
            delegate: ItemLouvor {
                width: lista.width
                item: modelData
                sel: modelData.i === vl.escolhido
                onClicado: vl.clique(modelData.i)
                onDuploClique: vl.duplo(modelData.i)
            }
        }
    }
    // ---- a coluna das telas (.col.col-slides)
    Rectangle {
        id: colDir
        x: vl.wEsq; width: vl.width - vl.wEsq; height: vl.height
        color: vl.sCol.background
        Caixa {
            id: tit; objectName: "titSlides"
            width: parent.width; clicavel: false; alinhar: Qt.AlignLeft
            sels: [".col h3"]; texto: vl.titulo
            herda: ({ "font-weight": 700 })          // <h3>: o navegador põe em negrito
            larguraTexto: width - pad[1] - pad[3]
        }
        Letra {
            visible: vl.telas.length === 0
            readonly property var sv: T.estilo([".vazio"], false)
            x: sv.padding[3]; y: tit.height + sv.padding[0]; width: parent.width - 2 * x
            text: "Escolha um louvor à esquerda"
            px: sv["font-size"]; color: sv.color; italico: true; quebra: Text.WordWrap; alinhamento: Text.AlignHCenter
        }
        ListView {
            QC.ScrollBar.vertical: BarraRolagem {}
            id: telasView; objectName: "telasLouvor"
            y: tit.height; width: parent.width; height: parent.height - y
            clip: true; model: vl.telas; reuseItems: true; boundsBehavior: Flickable.StopAtBounds
            delegate: ItemTela {
                width: telasView.width
                k: index; tela: modelData; sel: index === vl.telaNoAr
                onClicado: vl.tela(index)
                onDuploClique: vl.telaDuplo(index)
            }
        }
    }
}
