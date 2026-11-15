// A FOLHA DA CIFRA da 3.0.13 (#cifra-ov: .cifra-ov / .cifra-cx / .cifra-cab / .folha / .tom-painel do app.css): o véu da
// janela inteira com o app DESFOCADO atrás (backdrop-filter: blur(3px)), a caixa de 880 x min(92%, 940) com o cabeçalho
// (violão, título, o tom, A− A+ Telão, ✕), o painel dos doze tons e a folha em letra mono. O conteúdo (o texto colorido,
// os tracinhos do ritmo, os tons) é o MESMO que o Painel já monta (folhaHtml, folhaMarcas, tons, cifraDesloc).
// Medido no Edge (07/11): cabeçalho 50; A− A+ 30x28; o "Telão" também 30x28 (a regra dos botões do zoom pega ele): o ▶
// laranja em (6,5; 1) e o texto na 2ª linha em (1; 21), saindo do botão, como lá.
import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import QtQuick.Shapes
import "Tema.js" as T

Rectangle {
    id: cf
    property Item fundo: null
    property var pn: null                     // o Painel (as propriedades e funções da cifra)
    property alias lista: folhaList           // o Painel rola a folha (setas, PgUp/PgDown) e a abre no topo
    property alias fm: fmCif                  // a medida da letra mono (os tracinhos do ritmo)
    anchors.fill: parent
    visible: pn && pn.cifraAberta
    z: 320
    color: T.estilo([".cifra-ov"], false).background
    objectName: "folhaCifra"

    ShaderEffectSource { id: copia; anchors.fill: parent; sourceItem: cf.visible ? cf.fundo : null; live: cf.visible; visible: false }
    MultiEffect { anchors.fill: parent; z: -1; source: copia; blurEnabled: true; blur: 1.0; blurMax: 6; visible: cf.visible && cf.fundo !== null }
    Rectangle { anchors.fill: parent; color: cf.color }
    MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: cf.pn.fecharCifra() }    // clicar fora fecha (o onclick do véu)

    Rectangle {
        id: cx
        readonly property var s: T.estilo([".cifra-cx"], false)
        width: Math.min(880, cf.width * 0.96); height: Math.min(cf.height * 0.92, 940)
        anchors.centerIn: parent
        radius: s["border-radius"]; color: s.background; border.width: 1; border.color: T.V.borda
        clip: true
        RectShadowCSS { z: -1; anchors.fill: parent; radius: parent.radius; sombra: cx.s["box-shadow"] ? cx.s["box-shadow"][0] : null }
        MouseArea { anchors.fill: parent }

        // .cifra-cab: o violão, o título, o tom, A− A+ Telão e o ✕
        Rectangle {
            id: cab
            readonly property var s: T.estilo([".cifra-cab"], false)
            x: 1; y: 1; width: cx.width - 2; height: 50
            color: s.background
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: T.V.borda }
            Ico { x: 14; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: -0.5; nome: "violao"; tam: 17
                  cor: T.estilo([".cifra-cab .ico"], false).color }
            Letra {
                readonly property var s: T.estilo([".cifra-cab b"], false)
                x: 14 + 17 + 10; anchors.verticalCenter: parent.verticalCenter; anchors.verticalCenterOffset: -0.5
                px: s["font-size"]; weight: 700; color: s.color
                largura: direita.x - x - 10
                // o rotuloLouvor da 3.0.13 ("69  563 COLETÂNEA · TÍTULO"), o mesmo da Lista de projeção
                text: cf.pn && cf.pn.cifraIdx >= 0 ? (controle.tituloLouvor(cf.pn.cifraIdx) || cf.pn.folha.titulo || "Cifra") : ""
            }
            Row {
                id: direita
                x: cab.width - 14 - width; anchors.verticalCenter: parent.verticalCenter
                spacing: 10
                // o tom (.tom-btn): só quando a cifra declara o tom
                Caixa {
                    visible: cf.pn && cf.pn.tons.length > 0
                    sels: [".tom-btn"]; texto: cf.pn ? (cf.pn.folha.agora || "") : ""
                    anchors.verticalCenter: parent.verticalCenter
                    onClicado: cf.pn.tonsAbertos = !cf.pn.tonsAbertos
                }
                Row {
                    spacing: T.estilo([".cifra-zoom"], false).gap
                    anchors.verticalCenter: parent.verticalCenter
                    Caixa { sels: [".cifra-zoom button"]; texto: "A−"; onClicado: cf.pn.cifraFonte = Math.max(10, cf.pn.cifraFonte - 1) }
                    Caixa { sels: [".cifra-zoom button"]; texto: "A+"; onClicado: cf.pn.cifraFonte = Math.min(30, cf.pn.cifraFonte + 1) }
                    Caixa {
                        id: bTelao
                        objectName: "cifraTelao"
                        sels: [".cifra-zoom button"]; texto: ""
                        // 4.0 (decisão da HD 08/11, palavra dele 07/11 21h16: "o play está torto, embaixo"): na 3.0.x o botão
                        // tem 30 px (a regra do zoom) e o "▶ Telão" QUEBRA, o play em cima e a palavra embaixo. Aqui o play
                        // fica AO LADO da palavra, numa linha só, na altura do A− A+ (a 3.0.x fica como está: vai ao culto).
                        width: 8 + 15 + 4 + rotTelao.implicitWidth + 9
                        Row {
                            x: 8; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                            Ico { nome: "play"; tam: 15; anchors.verticalCenter: parent.verticalCenter; cor: T.estilo([".cifra-cab .ico"], false).color }
                            Letra { id: rotTelao; anchors.verticalCenter: parent.verticalCenter; px: bTelao.tamLetra; weight: 600; color: bTelao.corLetra; text: "Telão" }
                        }
                        onClicado: controle.projetarCifra(cf.pn.cifraIdx, cf.pn.cifraDesloc)
                    }
                }
                Caixa {
                    sels: [".cifra-x"]; texto: ""
                    width: 29.1; height: 29
                    anchors.verticalCenter: parent.verticalCenter
                    SinalFila { anchors.centerIn: parent; tipo: "x"; cor: parent.corLetra; px: 16 }
                    onClicado: cf.pn.fecharCifra()
                }
            }
        }
        // .tom-painel: −½ / +½, os doze, e o restaurar (abrirTons)
        Rectangle {
            id: tomPainel
            readonly property var s: T.estilo([".tom-painel"], false)
            visible: cf.pn && cf.pn.tonsAbertos && cf.pn.tons.length > 0
            x: 1; y: cab.y + cab.height; width: cx.width - 2
            height: visible ? s.padding[0] + tomCol.height + s.padding[2] + 1 : 0
            color: s.background
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: T.V.borda }
            Column {
                id: tomCol
                x: tomPainel.s.padding[3]; y: tomPainel.s.padding[0]; width: tomPainel.width - tomPainel.s.padding[1] - tomPainel.s.padding[3]
                spacing: tomPainel.s.gap
                Row {
                    spacing: 7
                    Repeater {
                        model: [["−½ tom", -1], ["+½ tom", 1]]
                        Caixa { sels: [".tom-linha button"]; texto: modelData[0]; width: (tomCol.width - 7) / 2
                                onClicado: { cf.pn.cifraDesloc += modelData[1]; cf.pn.tonsAbertos = false; cf.pn.redesenharCifra() } }
                    }
                }
                Grid {
                    columns: 12; columnSpacing: 6; rowSpacing: 6
                    Repeater {
                        model: cf.pn ? cf.pn.tons : []
                        Caixa { sels: [".tom-op"]; estados: modelData.on ? [".tom-op.on"] : []; texto: modelData.t; width: (tomCol.width - 6 * 11) / 12
                                onClicado: { cf.pn.cifraDesloc = modelData.d; cf.pn.tonsAbertos = false; cf.pn.redesenharCifra() } }
                    }
                }
                Caixa { visible: cf.pn && cf.pn.cifraDesloc !== 0; sels: [".tom-restaura"]; texto: "↺ Restaurar o tom impresso"; width: tomCol.width
                        onClicado: { cf.pn.cifraDesloc = 0; cf.pn.tonsAbertos = false; cf.pn.redesenharCifra() } }
            }
        }
        // .folha: rola; padding 14 16 26; a letra mono (o --cf) com linha de 1,45
        Rectangle {
            x: 1; y: tomPainel.y + tomPainel.height; width: cx.width - 2; height: cx.height - y - 1
            color: T.V.fundo
            Flickable {
                id: folhaList; objectName: "folhaList"
                anchors.fill: parent; clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar {}
                ScrollBar.horizontal: ScrollBar {}
                FontMetrics { id: fmCif; font.family: typeof fonteMono === "undefined" ? "monospace" : fonteMono; font.pixelSize: cf.pn ? cf.pn.cifraFonte : 14 }
                contentWidth: Math.max(width, 16 + fmCif.advanceWidth("M") * (cf.pn ? cf.pn.larguraFolha : 0) + 16)
                contentHeight: 14 + cabTx.height + folhaTxt.height + 26
                flickableDirection: Flickable.AutoFlickIfNeeded
                // o "+2 semitons do impresso (C)" (.folha .cab)
                Text {
                    id: cabTx
                    x: 16; y: 14; visible: cf.pn && !!cf.pn.folha.cab; height: visible ? implicitHeight + 10 : 0
                    textFormat: Text.StyledText; text: cf.pn ? (cf.pn.folha.cab || "") : ""
                    color: "#7f9ac0"; font.family: T.FONTE.familia; font.pixelSize: 12
                }
                Text {
                    id: folhaTxt; objectName: "folhaTexto"
                    x: 16; y: 14 + cabTx.height; textFormat: Text.StyledText; text: cf.pn ? cf.pn.folhaHtml : ""
                    color: "#e7edf7"; font.family: fmCif.font.family; font.pixelSize: fmCif.font.pixelSize
                    lineHeightMode: Text.FixedHeight; lineHeight: fmCif.font.pixelSize * 1.45
                }
                // o tracinho do ritmo: fio de 1 px no vão antes da sílaba, sem empurrar a grade
                Shape {
                    x: folhaTxt.x; y: folhaTxt.y; width: folhaTxt.width; height: folhaTxt.height
                    ShapePath { strokeColor: "#80f5d76e"; strokeWidth: 1; fillColor: "transparent"; PathMultiline { paths: cf.pn ? cf.pn.folhaMarcas : [] } }
                }
            }
        }
    }
}
