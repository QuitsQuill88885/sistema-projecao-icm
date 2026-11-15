// O AVISO MODAL da 3.0.13 (o confirmar()/mostrarAddFundo do app.js: .ajuda-overlay + .ajuda-box): o véu escuro na janela
// inteira, a caixa no meio com o título dourado, o texto e os botões grandes. Clicar no véu fecha sem responder.
import QtQuick
import "Tema.js" as T

Rectangle {
    id: av
    property string titulo: "Confirmar"
    property string mensagem: ""            // aceita <b> (fica branco e negrito, .ajuda-box b)
    property real largura: 520              // max-width (o confirmar usa 430)
    property var botoes: []                 // [{texto, sels, nome}] na ordem; o 1º é o de confirmar
    default property alias conteudo: extra.data
    property alias corpo: extra
    signal botao(int i)
    property var botaoConfirmar: null       // provas: o 1º botão (o de confirmar)
    property bool assistente: false         // a janela do ASSISTENTE (.assist-box): botões à direita, com vão de 8
    property bool aura: false               // .ajuda-box.pj-aura (o "Projetor não encontrado"): borda e brilho dourados
    property bool fechaNoVeu: true          // o esperarProjetor da 3.0.13 NÃO fecha no véu (veu.onmousedown preventDefault)
    readonly property var sa: T.estilo([".ajuda-box", ".ajuda-box.pj-aura"], false)
    readonly property var sb: T.estilo([".ajuda-box"], false)
    readonly property var sp: T.estilo([".ajuda-box p"], false)
    function abrir() { visible = true }
    function fechar() { visible = false }
    anchors.fill: parent
    visible: false; z: 200
    color: T.estilo([".ajuda-overlay"], false).background
    MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: if (av.fechaNoVeu) av.fechar() }   // o clique no véu fecha
    Rectangle {
        id: caixa
        width: Math.min(av.largura, av.width - 40)
        height: col.height + av.sb.padding[0] + av.sb.padding[2] + 2 * av.sb.border.w
        anchors.centerIn: parent
        radius: av.sb["border-radius"]; color: av.sb.background
        border.width: av.sb.border.w; border.color: av.aura ? av.sa["border-color"] : av.sb.border.cor
        // as sombras do CSS, a 1ª por cima (no navegador a primeira da lista fica na frente)
        Repeater {
            model: (av.aura ? av.sa["box-shadow"] : av.sb["box-shadow"]).slice().reverse()
            RectShadowCSS { z: -1; parent: caixa; anchors.fill: parent; radius: caixa.radius; sombra: modelData }
        }
        MouseArea { anchors.fill: parent }                         // o clique na caixa não fecha
        Column {
            id: col
            x: av.sb.padding[3] + av.sb.border.w; y: av.sb.padding[0] + av.sb.border.w
            width: caixa.width - av.sb.padding[1] - av.sb.padding[3] - 2 * av.sb.border.w
            Caixa { clicavel: false; alinhar: Qt.AlignLeft; sels: [".ajuda-box h3"]; herda: ({ "font-weight": 700 }); texto: av.titulo }
            Item { width: 1; height: T.estilo([".ajuda-box h3"], false)["margin-bottom"] }
            Letra {
                visible: av.mensagem !== ""
                width: col.width; quebra: Text.WordWrap; textFormat: Text.StyledText
                px: av.sp["font-size"]; color: av.sp.color; linha: av.sp["line-height"]
                text: av.mensagem.split("<b>").join("<b><font color=\"#ffffff\">").split("</b>").join("</font></b>")
            }
            Item { visible: av.mensagem !== ""; width: 1; height: T.estilo([".ajuda-box p:last-of-type"], false)["margin-bottom"] }
            Column { id: extra; width: col.width }
            Flow {
                // .assist-box .ajuda-btns{gap:8px;justify-content:flex-end}: a fileira encostada à direita, na ordem
                width: av.assistente ? Math.min(col.width, implicitW) : col.width
                x: av.assistente ? col.width - width : 0
                readonly property real implicitW: { var w = 0; for (var k = 0; k < children.length; k++) if (children[k].width) w += children[k].width + spacing; return Math.max(0, w - spacing) }
                spacing: av.assistente ? T.estilo([".assist-box .ajuda-btns"], false).gap : T.estilo([".ajuda-btns"], false).gap
                Repeater {
                    model: av.botoes
                    Caixa { objectName: modelData.nome || ""; sels: modelData.sels; texto: modelData.texto; onClicado: av.botao(index)
                            Component.onCompleted: if (index === 0) av.botaoConfirmar = this }
                }
            }
        }
    }
}
