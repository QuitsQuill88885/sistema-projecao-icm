// UM CARTÃO da grade de Fundos/Apresentações (.fundo-card da 3.0.13): a miniatura 16:9 (borda de 2, cantos de 10), o nome
// embaixo (quebra em 2 linhas se for comprido), nas apresentações "Exemplo · N slides"; com o mouse, as ações no canto
// (Espera, ✕); o selo "★ Espera" no fundo que é a tela de espera; o último é o "+" tracejado (.add-card).
import QtQuick
import QtQuick.Shapes
import "Tema.js" as T

Item {
    id: c
    property var vista: null
    property var f: ({})
    property int indice: 0
    signal xisPronto(var item)
    readonly property bool add: !!f.add
    readonly property bool eEspera: vista && vista.tipo === "fundos" && !!f.espera
    readonly property bool eAtivo: vista && vista.tipo === "fundos" && !add && f.arquivo === vista.noAr
    readonly property bool apres: vista && vista.tipo === "apres"
    readonly property bool especial: apres && !!f.especial
    readonly property var s: T.estilo([".fundo-card"].concat(add ? [".add-card"] : []).concat(eEspera ? [".fundo-card.espera"] : [])
                                      .concat(eAtivo ? [".fundo-card.projetando"] : [])
                                      .concat(especial ? ["#ap-grade .fundo-card.especial"] : []), ma.containsMouse)
    readonly property real bw: s.border.w
    readonly property real altImg: (width - 2 * bw) * 9 / 16
    readonly property var sn: T.estilo([".fundo-card .nome"], false)
    // a altura que o cartão pede (a fileira estica todos até a do mais alto); o "+" pede no mínimo 130
    readonly property real alturaNatural: add ? Math.max(T.n(".add-card", "min-height", 130), 0)
                                              : bw + altImg + sn.padding[0] + nome.implicitHeight + (apres ? 3 + info.alturaLinha : 0) + sn.padding[2] + bw

    Rectangle {
        id: cartao
        anchors.fill: parent
        radius: c.s["border-radius"]; clip: true
        color: T.fundo(c.s.background)
        border.width: c.add ? 0 : c.bw; border.color: c.s["border-color"] || c.s.border.cor
        // .fundo-card.projetando{box-shadow:0 0 0 1px verde}: o anel de 1 px por fora
        Rectangle { visible: c.eAtivo; z: -1; anchors.fill: parent; anchors.margins: -1; radius: parent.radius + 1; color: T.V.verde }
        Image {
            visible: !c.add
            x: c.bw; y: c.bw; width: parent.width - 2 * c.bw; height: c.altImg
            source: c.add ? "" : (c.apres ? c.f.mini : c.f.url)
            fillMode: Image.PreserveAspectCrop; asynchronous: true; cache: true
            sourceSize.width: 380; sourceSize.height: 214
        }
        Column {
            visible: !c.add
            x: c.bw + c.sn.padding[3]; y: c.bw + c.altImg + c.sn.padding[0]
            width: cartao.width - 2 * c.bw - c.sn.padding[1] - c.sn.padding[3]
            Letra { id: nome; width: parent.width; quebra: Text.WordWrap; alinhamento: Text.AlignHCenter
                    px: c.sn["font-size"]; color: T.V.txt; text: c.f.nome || "" }
            Item { visible: c.apres; width: 1; height: 3 }
            Letra { id: info; visible: c.apres; width: parent.width; largura: parent.width; alinhamento: Text.AlignHCenter
                    readonly property var si: T.estilo([".fundo-card .ap-info"], false)
                    px: si["font-size"]; color: T.V.txt; opacity: si.opacity; lsCss: si["letter-spacing"].em * si["font-size"]
                    text: c.apres && !c.add ? (c.f.demo ? "Exemplo · " : "") + c.f.n + " slides" : "" }
        }
        // a borda TRACEJADA do "+" (.add-card{border:2px dashed})
        Shape {
            visible: c.add; anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: c.s["border-color"] || c.s.border.cor; strokeWidth: c.bw; fillColor: "transparent"
                strokeStyle: ShapePath.DashLine; dashPattern: [3, 3]
                PathRectangle { x: c.bw / 2; y: c.bw / 2; width: c.width - c.bw; height: c.height - c.bw; radius: c.s["border-radius"] - c.bw / 2 }
            }
        }
        // a apresentação ESPECIAL: o selo das duas telas no canto da miniatura (.selo-ultra)
        Rectangle {
            visible: c.especial
            readonly property var ss: T.estilo([".selo-ultra"], false)
            width: ss.width; height: ss.height; radius: width / 2
            x: c.width - c.bw - ss.right - width; y: c.bw + c.altImg - ss.bottom - height
            color: ss.background; border.width: ss.border.w; border.color: ss.border.cor
            RectShadowCSS { z: -1; anchors.fill: parent; radius: parent.radius; sombra: parent.ss["box-shadow"][0] }
            Ico { anchors.centerIn: parent; nome: "telas"; cor: parent.ss.color; tam: 15 }
        }
        Caixa { visible: c.eEspera; clicavel: false; x: 8; y: 8; sels: [".badge-espera"]; icone: "estrela"; icoTam: 11; texto: " Espera" }
        Column {
            visible: c.add; anchors.centerIn: parent; spacing: T.estilo([".add-inner"], false).gap
            Letra { anchors.horizontalCenter: parent.horizontalCenter; text: "+"; weight: 300; color: T.V.verde
                    px: T.estilo([".add-inner .plus"], false)["font-size"] || 36; linha: 0.9 }
            Letra { anchors.horizontalCenter: parent.horizontalCenter; px: 13; color: T.estilo([".add-inner"], false).color
                    text: c.apres ? "Abrir apresentação" : "Adicionar fundo" }
        }
        MouseArea {
            id: ma; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            Timer { id: umClique; interval: c.apres ? 230 : 220; onTriggered: c.vista.clique(c.f.i) }
            onClicked: c.add ? c.vista.adicionar() : umClique.restart()
            onDoubleClicked: { if (c.add) return; umClique.stop(); c.vista.duplo(c.f.i) }
        }
        // as ações no canto (.fundo-acoes, top 7 right 7): aparecem com o mouse em cima
        Row {
            visible: !c.add
            opacity: ma.containsMouse || xis.sobre || bEsp.sobre ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 150 } }
            anchors { top: parent.top; right: parent.right; topMargin: 7; rightMargin: 7 }
            spacing: T.estilo([".fundo-acoes"], false).gap
            Caixa { id: bEsp; visible: !c.apres && !c.eEspera; sels: [".fa", ".fa-espera"]; texto: "Espera"; onClicado: c.vista.espera(c.f.i) }
            Caixa { id: xis; objectName: "xisFundo"; sels: [".fa", ".fa-del"]; icone: "x"; icoTam: 9; texto: ""; onClicado: c.vista.apagar(c.f.i)
                    Component.onCompleted: c.xisPronto(xis) }
        }
    }
}
