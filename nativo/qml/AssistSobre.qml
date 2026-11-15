// O assistente "SOBRE O SISTEMA" (o abrirAssistente('sobre') da 3.0.13: a caixa .assist-box com o #sis-painel-sobre):
// o bloco de créditos com "ver mais ▾" (a licença, os direitos da ICM e as fontes), "Apresentação inicial · Ver de
// novo", o contato com "Copiar e-mail" e o "Fechar" à direita. Só leitura.
import QtQuick
import QtQuick.Shapes
import "Tema.js" as T

Aviso {
    id: as
    titulo: "Sobre o Sistema"
    largura: 560
    assistente: true
    botoes: [{ texto: "Fechar", sels: [".big-btn"], nome: "sobreFechar" }]
    property bool mais: false
    signal rever()
    signal copiado(string t)
    onBotao: (i) => fechar()
    onVisibleChanged: if (visible) mais = false

    readonly property var sc: T.estilo([".cred-bloco"], false)
    // o <p> e o <b> do bloco estão DENTRO da .ajuda-box: a cascata junta as duas regras (medido no Edge 07/11: a letra e a
    // cor do parágrafo são as da .ajuda-box p, 13,5 px #cdd9ee linha 1,65; a margem e o <b> são os do .cred-bloco)
    readonly property var sp: T.estilo([".ajuda-box p", ".cred-bloco p"], false)
    readonly property var scb: T.estilo([".ajuda-box b", ".cred-bloco b"], false)
    // o <b> do bloco é peso 600 (.cred-bloco b): a família SemiBold da Painel ICM, na cor dele
    readonly property string bo: "<span style=\"font-weight:600; color:" + scb.color + "\">"
    readonly property string bc: "</span>"

    // .cred-bloco
    Rectangle {
        id: cred
        width: parent.width; height: as.sc.padding[0] + credCol.height + as.sc.padding[2] + 2
        radius: as.sc["border-radius"]; color: as.sc.background; border.width: 1; border.color: as.sc.border ? as.sc.border.cor : "#1f2c40"
        Column {
            id: credCol
            x: as.sc.padding[3] + 1; y: as.sc.padding[0] + 1; width: cred.width - as.sc.padding[1] - as.sc.padding[3] - 2
            Letra { width: credCol.width; quebra: Text.WordWrap; textFormat: Text.RichText; px: as.sp["font-size"]; color: as.sp.color; linha: as.sp["line-height"]
                    text: as.bo + "Sistema" + as.bc + " — projeção para igrejas.<br>Desenvolvido por " + as.bo + "Samuel Mariano Ribeiro" + as.bc + ", 2026." }
            // é o último <p> do bloco (o "ver mais" é botão): .ajuda-box p:last-of-type{margin-bottom:20px}
            Item { width: 1; height: 20 }
            Column {
                visible: as.mais
                width: credCol.width
                Repeater {
                    model: ["O código é livre: pode ser copiado, modificado e usado por qualquer igreja, inclusive comercialmente. A única condição é que o nome do autor continue citado. Código sob licença MIT, conteúdo sob Creative Commons Atribuição 4.0.",
                            "As letras dos louvores, o texto bíblico, as cifras e as artes de fundo pertencem à Igreja Cristã Maranata e não fazem parte dessa licença.",
                            "Fontes: " + as.bo + "Outfit" + as.bc + " (Rodrigo Fuenzalida) e " + as.bo + "Bebas Neue" + as.bc + " (Dharma Type), ambas sob SIL Open Font License, distribuídas junto com o programa."]
                    Column {
                        width: credCol.width
                        Letra { width: credCol.width; quebra: Text.WordWrap; textFormat: Text.RichText; px: as.sp["font-size"]; color: as.sp.color
                                linha: as.sp["line-height"]; text: modelData }
                        Item { width: 1; height: index < 2 ? 9 : 0 }     // .cred-bloco p (9); o último: p:last-child (0)
                    }
                }
            }
            // .cred-mais-btn: "ver mais ▾" / "ver menos ▴" (o triângulo desenhado)
            Item {
                id: maisBt
                objectName: "credMais"
                readonly property var s: T.estilo([".cred-mais-btn"], false)
                width: maisTx.implicitTextWidth + 4 + 5; height: s.padding[0] + maisTx.height
                Letra { id: maisTx; y: maisBt.s.padding[0]; px: maisBt.s["font-size"]; lsCss: maisBt.s["letter-spacing"]
                        color: maMais.containsMouse ? T.estilo([".cred-mais-btn"], true).color : maisBt.s.color
                        text: as.mais ? "ver menos" : "ver mais" }
                Shape {
                    x: maisTx.implicitTextWidth + 4; y: maisTx.y + maisTx.ascPx - 5; width: 5; height: 4
                    preferredRendererType: Shape.CurveRenderer
                    ShapePath {
                        strokeColor: "transparent"; fillColor: maisTx.color
                        startX: 0; startY: as.mais ? 4 : 0
                        PathLine { x: 5; y: as.mais ? 4 : 0 }
                        PathLine { x: 2.5; y: as.mais ? 0 : 4 }
                    }
                }
                MouseArea { id: maMais; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: as.mais = !as.mais }
            }
        }
    }
    // as duas linhas (.reset-row)
    ResetRow {
        width: cred.width
        titulo: "Apresentação inicial"; sub: "Rever como o Sistema funciona e reconfigurar a igreja."
        botao: "Ver de novo"; nomeBotao: "sobreRever"
        onAcionado: { as.fechar(); as.rever() }
    }
    Item { width: 1; height: 8 }
    ResetRow {
        width: cred.width
        titulo: "Achou um defeito ou tem uma ideia?"; sub: "samuelsaxdiesel@gmail.com"
        botao: "Copiar e-mail"; nomeBotao: "sobreMail"
        onAcionado: { controle.copiar("samuelsaxdiesel@gmail.com"); as.copiado("E-mail copiado: samuelsaxdiesel@gmail.com") }
    }
    Item { width: 1; height: 8 }
    Item { width: 1; height: 14 - 8 }          // .assist-box .sis-painel{margin:0 0 14px} (o 8 da última linha colapsa)
}
