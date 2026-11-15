// UM ITEM da Lista de projeção (o .fila-item do renderFila da 3.0.13): o ✓ dos versículos (Juntos), o número da ordem,
// o rótulo (louvor em azul com a nota, versículo em ouro, apresentação com a tela) e ▲ ▼ ✕. Clique projeta; arrastar
// muda a ordem (soltarFila). Os sinais ▲ ▼ ✕ ♪ ✓ são DESENHO (nunca caractere: cada sistema desenha diferente).
import QtQuick
import QtQuick.Shapes
import "Tema.js" as T

Caixa {
    id: it
    property int linha: 0
    property var item: ({})
    property bool noAr: false
    property bool jaFoi: false
    property bool alvoArrasto: false
    property bool arrastando: false
    property var lista: null
    property bool pb: false                  // o modo apresentação (body.pb-on .fila-item: outro fundo e borda)
    signal ir()
    signal subir()
    signal descer()
    signal tirar()
    signal marcar()
    signal soltar(int de, int para)
    readonly property bool marcado: !!item.on
    readonly property bool verso: item.tipo === "verso"
    sels: [".fila-item"].concat(pb ? ["body.pb-on .fila-item"] : [])
    estados: (noAr ? [".fila-item.atual"].concat(pb ? ["body.pb-on .fila-item.atual"] : []) : []).concat(jaFoi ? [".fila-item.ja-foi"] : []).concat(marcado ? [".fila-item.agrupado"] : [])
             .concat(arrastando ? [".fila-item.arrastando"] : []).concat(alvoArrasto ? [".fila-item.drop-alvo"] : [])
    implicitHeight: pad[0] + Math.max(rot.implicitHeight, 25) + pad[2]
    clicavel: false                      // o clique e o arrastar são do MouseArea de baixo; o hover vem dele
    forcarSobre: maItem.containsMouse
    // opacidade de GRUPO, como a do CSS (.fila-item.ja-foi{opacity:.42}): o item vira uma camada e só ela é apagada; sem
    // isso o Qt apaga filho por filho e o fundo dos ▲ ▼ ✕ soma com o do item (quadradinhos que a 3.0.13 não tem)
    layer.enabled: opacity < 1
    texto: ""

    Row {
        id: conteudo
        x: it.pad[3]; anchors.verticalCenter: parent.verticalCenter
        width: it.width - it.pad[1] - it.pad[3]
        spacing: it.st.gap
        // o ✓ (.chk): só nos versículos; marcado = entra na projeção Juntos
        Rectangle {
            id: chk; objectName: "chk" + it.linha
            visible: it.verso
            readonly property var s: T.estilo([".fila-item .chk"].concat(it.marcado ? [".fila-item .chk.on", ".fila-item.agrupado .chk.on"] : []), chkMa.containsMouse)
            width: s.width; height: s.height; radius: s["border-radius"]
            color: T.fundo(s.background); border.width: s.border.w; border.color: s["border-color"] || s.border.cor
            anchors.verticalCenter: parent.verticalCenter
            Ico { visible: it.marcado; nome: "ok"; cor: chk.s.color || "#1a1a1a"; tam: 12; anchors.centerIn: parent }
            MouseArea { id: chkMa; anchors.fill: parent; anchors.margins: -3; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: it.marcar() }
        }
        // o número da ordem (.fila-num): largura fixa de 1,35 em, à direita, e margin-right 6 px. A margem vai DENTRO da
        // caixa: um espaçador de largura 0 é ignorado pela Row (não ganha o vão) e o rótulo começava 6 px antes (07/11)
        Item {
            width: numL.width + 6; height: numL.height
            anchors.verticalCenter: parent.verticalCenter
            Letra {
                id: numL
                readonly property var s: T.estilo([".fila-num"].concat(it.noAr ? [".fila-item.atual .fila-num"] : []), false)
                px: s["font-size"]; color: s.color
                text: String(it.linha + 1)
                largura: s["min-width"].em * s["font-size"]
                alinhamento: Text.AlignRight
            }
        }
        // o rótulo (.rot): louvor = ♪ + nome em azul-claro; versículo em ouro; apresentação com o ícone de tela
        Row {
            id: rotRow
            // o resto da linha (.rot{flex:1}): do começo do rótulo até os botões, com os vãos da fileira e, depois do
            // "agora", a margem de 6 px dos botões (.fila-agora+.fila-btns{margin-left:6px})
            width: conteudo.width - x - conteudo.spacing - botoes.width
                   - (agoraAp.visible ? agoraAp.width + conteudo.spacing + 6 : 0)
            spacing: 0
            anchors.verticalCenter: parent.verticalCenter
            readonly property color cor: it.item.tipo === "louvor" ? "#bfe6ff" : (it.item.tipo === "apres" ? "#dfe8f7" : "#f5d76e")
            // o "♪ " do louvor: na 3.0.13 é letra do próprio texto e a tinta do ♪ começa 1,3 px ANTES da caixa do rótulo;
            // o número vem 9,7 px depois do começo dela (medido no Edge, aba Texto, 07/11)
            Item {
                // medido na lista da aba Bíblia (07/11): tinta do ♪ de 6 px a começar 0,8 antes da caixa; o número a +10,7
                visible: it.item.tipo === "louvor"; width: 10.7; height: 10.5; anchors.verticalCenter: parent.verticalCenter
                Ico { x: -2.3; nome: "nota"; cor: rotRow.cor; tam: 9.2; anchors.verticalCenter: parent.verticalCenter }
            }
            Ico { visible: it.item.tipo === "apres"; nome: "slides"; cor: rotRow.cor; tam: 13; anchors.verticalCenter: parent.verticalCenter }
            Item { visible: it.item.tipo === "apres"; width: 4; height: 1 }        // .fila-item .rot .ico{margin-right:4px}
            Letra {
                id: rot
                px: T.n(".fila-item", "font-size", 13); color: rotRow.cor
                text: it.item.rotulo || ""
                largura: rotRow.width - (it.item.tipo === "louvor" ? 10.7 : (it.item.tipo === "apres" ? 13 + 4 : 0))
                anchors.verticalCenter: parent.verticalCenter

            }
        }
        // a apresentação no ar: "● agora · 9/22" (.fila-agora: 11 px verde-claro, a bolinha verde de 7 px)
        Row {
            id: agoraAp
            visible: it.item.tipo === "apres" && it.noAr && !!it.item.det
            anchors.verticalCenter: parent.verticalCenter; spacing: 4
            Rectangle { width: 7; height: 7; radius: 3.5; color: "#3ecf7a"; anchors.verticalCenter: parent.verticalCenter }
            Letra { px: 11; color: "#9fe3b9"; text: "agora · " + (it.item.det || ""); anchors.verticalCenter: parent.verticalCenter }
        }
        // ▲ ▼ ✕ (.fila-btns .fb): aparecem com 80% e acendem com o mouse
        Row {
            id: botoes
            readonly property var s: T.estilo([".fila-btns"], it.sobre)
            spacing: s.gap; opacity: it.sobre ? 1 : s.opacity
            anchors.verticalCenter: parent.verticalCenter
            Repeater {
                model: [["cima", "up"], ["baixo", "dn"], ["x", "x"]]
                Rectangle {
                    id: fb
                    readonly property var s: T.estilo([".fila-btns .fb"].concat(modelData[1] === "x" ? [".fila-btns .fb.x"] : []), fbMa.containsMouse)
                    width: s.width; height: s.height; radius: s["border-radius"]; color: T.fundo(s.background)
                    SinalFila { anchors.centerIn: parent; tipo: modelData[1]; cor: fb.s.color; px: fb.s["font-size"] }
                    MouseArea {
                        id: fbMa; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: modelData[1] === "up" ? it.subir() : (modelData[1] === "dn" ? it.descer() : it.tirar())
                    }
                }
            }
        }
    }
    // clicar projeta o item; arrastar muda a ordem (um toque sem arrastar = clique)
    // já cantado: o risco (.fila-item.ja-foi .rot{text-decoration:line-through #5d7ba8}) atravessa o RÓTULO inteiro,
    // ♪ incluído (na 3.0.13 o ♪ é letra do mesmo texto); fica fora da fileira para não empurrar nada
    Rectangle {
        visible: it.jaFoi; color: "#5d7ba8"; height: 1; z: 2
        x: conteudo.x + rotRow.x
        width: Math.min(rotRow.width, rot.x + Math.min(rot.width, rot.implicitTextWidth))
        y: conteudo.y + rotRow.y + rot.y + rot.ascPx - 4.4
    }
    MouseArea {
        id: maItem
        anchors.fill: parent; z: -1; preventStealing: true
        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
        property real y0: 0
        onPressed: function (m) { y0 = m.y }
        onPositionChanged: function (m) {
            if (!it.lista || !pressed) return          // só passar o mouse por cima não é arrastar
            if (it.lista.de < 0 && Math.abs(m.y - y0) > 8) it.lista.de = it.linha
            if (it.lista.de >= 0) {
                var p = mapToItem(it.lista.contentItem, m.x, m.y)
                var k = it.lista.indexAt(10, p.y)
                it.lista.alvo = k >= 0 ? k : (p.y < 0 ? 0 : it.lista.count - 1)
            }
        }
        onReleased: {
            if (!it.lista) { it.ir(); return }
            var de = it.lista.de, para = it.lista.alvo
            it.lista.de = -1; it.lista.alvo = -1
            if (de >= 0) { if (para >= 0 && para !== de) it.soltar(de, para) }
            else it.ir()
        }
        onCanceled: { if (it.lista) { it.lista.de = -1; it.lista.alvo = -1 } }
    }
}
