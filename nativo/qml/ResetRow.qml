// UMA LINHA de assistente/configuração (.reset-row da 3.0.13): o título em negrito e o texto miúdo à esquerda, o botão à
// direita. O texto miúdo (11,5 px) fica numa linha de letra 16 (a caixa herda a do body): 21 px por linha, 2 px abaixo do
// meio (medido no Edge: a linha toda tem 68 px).
import QtQuick
import "Tema.js" as T

Caixa {
    id: rr
    property string titulo: ""
    property string sub: ""
    property string botao: ""
    property var botaoSels: [".big-btn"]
    property string nomeBotao: ""
    property var classes: []                  // ".reset-row.perigo", ".reset-row.destaque"...
    property bool subOuro: false              // o <b class="st-ouro"> da linha dourada ("a melhor versão do Sistema")
    signal acionado()
    clicavel: false; sels: [".reset-row"].concat(classes); texto: ""
    height: pad[0] + Math.max(txtCol.height, bt.height) + pad[2] + 2 * bw
    Column {
        id: txtCol
        x: rr.pad[3] + rr.bw; anchors.verticalCenter: parent.verticalCenter
        width: rr.width - rr.pad[1] - rr.pad[3] - 2 * rr.bw - bt.width - rr.st.gap
        readonly property var sb: T.estilo([".reset-row b"].concat(rr.classes.map(function (c) { return c + " b" })), false)
        readonly property var sm: T.estilo([".reset-row small"], false)
        Letra { width: txtCol.width; quebra: Text.WordWrap; px: txtCol.sb["font-size"]; weight: 700; color: txtCol.sb.color || T.V.txt; text: rr.titulo }
        Item { width: 1; height: txtCol.sb["margin-bottom"] }
        Item {
            width: txtCol.width; height: smTx.height
            Letra { id: smTx; y: 2; width: parent.width; quebra: Text.WordWrap; px: txtCol.sm["font-size"]; color: rr.subOuro ? T.estilo([".st-ouro"], false).color : txtCol.sm.color
                    weight: rr.subOuro ? T.estilo([".st-ouro"], false)["font-weight"] : 400
                    linha: 21 / txtCol.sm["font-size"]; text: rr.sub }
        }
    }
    Caixa {
        id: bt
        objectName: rr.nomeBotao
        sels: rr.botaoSels.concat(rr.classes.map(function (c) { return c + " .big-btn" })); texto: rr.botao
        x: rr.width - rr.pad[1] - rr.bw - width; anchors.verticalCenter: parent.verticalCenter
        onClicado: rr.acionado()
    }
}
