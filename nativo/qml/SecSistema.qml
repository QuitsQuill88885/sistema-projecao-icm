// SISTEMA (a <section data-sec="sistema"> da 3.0.13, a "2ª proposta" dele de 10/10/2026): quatro botões grandes que abrem
// um ASSISTENTE (Atualizar, Restaurar, Desinstalar, Sobre), a chave discreta "Louvores das CIAS abrem com a tela animada"
// (icm_anim_auto, a mesma da 3.0.13) e a assinatura. O "Completar o Sistema" fica escondido (o nativo leva tudo junto).
import QtQuick
import "Tema.js" as T

Column {
    id: ss
    signal assistente(string nome)
    readonly property var sg: T.estilo([".sis-botoes"], false)

    Item { width: 1; height: ss.sg.margin[0] }
    Grid {
        id: grade
        columns: 2; columnSpacing: ss.sg.gap; rowSpacing: ss.sg.gap
        readonly property real larg: (ss.width - ss.sg.gap) / 2
        Repeater {
            id: rep
            model: [["atualizar", "Atualizar", "Versão nova, busca automática e pendrive", false],
                    ["restaurar", "Restaurar", "Trazer de volta o que veio com o Sistema", false],
                    ["desinstalar", "Desinstalar", "Tirar o Sistema deste computador", true],
                    ["sobre", "Sobre o Sistema", "Quem fez, licença e contato", false]]
            Caixa {
                id: bt
                objectName: "sisBt_" + modelData[0]
                sels: [".sis-bt"].concat(modelData[3] ? [".sis-bt.perigo"] : []); texto: ""
                width: grade.larg
                readonly property real natural: pad[0] + col.height + pad[2] + 2 * bw
                height: Math.max(natural, rep.itemAt(index ^ 1) ? rep.itemAt(index ^ 1).natural : 0)   // a linha da grade estica
                Column {
                    id: col
                    x: bt.pad[3] + bt.bw; y: bt.pad[0] + bt.bw
                    width: bt.width - bt.pad[1] - bt.pad[3] - 2 * bt.bw
                    spacing: bt.st.gap
                    readonly property var sb: T.estilo([".sis-bt b"].concat(modelData[3] ? [".sis-bt.perigo b"] : []), false)
                    readonly property var sm: T.estilo([".sis-bt small"], false)
                    Letra { px: col.sb["font-size"]; weight: 700; color: col.sb.color || bt.corLetra; text: modelData[1] }
                    Letra { width: col.width; quebra: Text.WordWrap; px: col.sm["font-size"]; color: col.sm.color; linha: col.sm["line-height"]
                            text: modelData[2] }
                }
                onClicado: ss.assistente(modelData[0])
            }
        }
    }
    Item { width: 1; height: ss.sg.margin[2] }
    // a preferência (.sis-pref: borda em cima, o texto à esquerda e a chave à direita)
    Item {
        id: pref
        readonly property var s: T.estilo([".sis-pref"], false)
        width: ss.width; height: s.padding[0] + chave.height + s.padding[2]
        Rectangle { width: parent.width; height: 1; color: T.V.borda }
        Letra { x: pref.s.padding[3]; anchors.verticalCenter: parent.verticalCenter; px: pref.s["font-size"]; color: pref.s.color
                text: "Louvores das CIAS abrem com a tela animada" }
        // a CHAVE (.chave / .chave.on): ligada = a bolinha verde à DIREITA, como todo interruptor
        Caixa {
            id: chave
            objectName: "chaveAnim"
            readonly property bool on: controle.animAuto
            sels: [".chave"]; estados: on ? [".chave.on"] : []; texto: ""
            x: pref.width - pref.s.padding[1] - width; anchors.verticalCenter: parent.verticalCenter
            width: Math.max(st["min-width"] || 74, pad[1] + rot.implicitTextWidth + pad[3] + 2 * bw)
            height: pad[0] + rot.height + pad[2] + 2 * bw
            Letra { id: rot; x: chave.on ? chave.width - chave.pad[1] - chave.bw - implicitTextWidth : chave.pad[3] + chave.bw
                    anchors.verticalCenter: parent.verticalCenter; px: chave.tamLetra; color: chave.corLetra
                    text: chave.on ? "Ligado" : "Desligado" }
            Rectangle {   // a bolinha (::before): 16 px, a 6 da borda
                width: 16; height: 16; radius: 8; anchors.verticalCenter: parent.verticalCenter
                x: chave.on ? chave.width - 6 - width : 6
                color: chave.on ? T.V.verde : "#3a4a66"
                Behavior on color { ColorAnimation { duration: 150 } }
            }
            onClicado: controle.alternarAnimAuto()
        }
    }
    // a assinatura
    Item { width: 1; height: T.estilo([".sis-assina"], false).margin[0] }
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        readonly property var s: T.estilo([".sis-assina"], false)
        readonly property var sb: T.estilo([".sis-assina b"], false)
        Letra { px: parent.s["font-size"]; color: parent.s.color; lsCss: 0.02 * parent.s["font-size"]
                text: "Sistema Nativo · desenvolvido por " }
        Letra { px: parent.s["font-size"]; color: parent.sb.color; weight: parent.sb["font-weight"]; lsCss: 0.02 * parent.s["font-size"]
                text: "Samuel Mariano Ribeiro" }
    }
    Item { width: 1; height: T.estilo([".sis-assina"], false).margin[2] }
}
