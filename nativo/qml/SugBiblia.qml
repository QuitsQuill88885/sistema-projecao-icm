// A faixa "LOUVORES PARA ESTE VERSÍCULO" da aba Bíblia (o #sug da 3.0.13: .sug / .sug-cab / .sug-mais / .sug-l): o trio de
// louvores que combinam com o versículo no ar, "ver mais" que gira a roda, clique abre o louvor na aba Louvor (sem
// projetar) e "+" guarda na Lista de projeção. A roda vem pronta do Python (controle.sugestoes).
import QtQuick
import "Tema.js" as T

Rectangle {
    id: sg
    readonly property var d: controle.sugestoes
    readonly property var s: T.estilo([".sug"], false)
    signal abrir(int i)
    visible: d.visivel
    height: visible ? 1 + s.padding[0] + cab.height + 7 + lista.height + s.padding[2] : 0
    color: s.background
    Rectangle { width: parent.width; height: 1; color: T.V.borda }

    // .sug-cab: o ícone, o título e o "ver mais"
    Item {
        id: cab
        readonly property var sc: T.estilo([".sug-cab"], false)
        x: sg.s.padding[3]; y: 1 + sg.s.padding[0]; width: sg.width - sg.s.padding[1] - sg.s.padding[3]
        height: Math.max(17, mais.height)
        Ico { id: ic; nome: "louvor"; tam: 13; cor: T.V.ouro; anchors.verticalCenter: parent.verticalCenter }
        Letra { x: ic.width + 7; anchors.verticalCenter: parent.verticalCenter; px: cab.sc["font-size"]; weight: 700; maiusculas: true
                lsCss: cab.sc["letter-spacing"]; color: cab.sc.color; text: "Louvores para este versículo" }
        Caixa {
            id: mais
            objectName: "sugMais"
            visible: sg.d.mais
            sels: [".sug-mais"]; texto: "mais sugestões"
            x: cab.width - width; anchors.verticalCenter: parent.verticalCenter
            onClicado: controle.maisSugestoes()
        }
    }
    // .sug-lista: o trio (vão 4)
    Column {
        id: lista
        x: cab.x; y: cab.y + cab.height + 7; width: cab.width
        spacing: T.estilo([".sug-lista"], false).gap
        Repeater {
            model: sg.d.trio
            Caixa {
                id: l
                objectName: "sugL" + index
                sels: [".sug-l"]; texto: ""
                width: lista.width; height: pad[0] + Math.max(16, add.height) + pad[2]   // o "+" (13 px, linha 1,2) manda na altura
                readonly property var sm: T.estilo([".sug-l small"], false)
                Letra { id: num; x: l.pad[3]; anchors.verticalCenter: parent.verticalCenter; px: l.sm["font-size"] || 10.8; color: l.sm.color
                        largura: Math.max(58, implicitTextWidth); text: modelData.num + " " + modelData.sigla }
                Letra { x: num.x + num.width + 8; anchors.verticalCenter: parent.verticalCenter; px: l.tamLetra; color: T.V.txt
                        largura: add.x - x - 8; text: modelData.titulo }
                Caixa {
                    id: add
                    objectName: "sugAdd" + index
                    sels: [".sug-l .add"]; texto: "+"
                    height: pad[0] + 13 * 1.2 + pad[2]            // .add{line-height:1.2}: 2 + 15,6 + 2 (a Caixa usaria a linha normal)
                    x: l.width - l.pad[1] - width; anchors.verticalCenter: parent.verticalCenter
                    onClicado: controle.addLouvor(modelData.i)
                }
                onClicado: sg.abrir(modelData.i)
            }
        }
    }
}
