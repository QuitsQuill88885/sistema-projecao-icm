// As BOAS-VINDAS / "Como funciona" da 3.0.13 (#bemvindo: BV_PASSOS, renderBV, bvAvancar do app.js): o véu escuro que
// DESFOCA o app atrás (backdrop-filter: blur(3px)), a caixa em degradê com os pontinhos dos 5 passos, o título, o
// subtítulo, o conteúdo do passo (a marca e o versículo; as listas; a igreja) e o rodapé "Pular / Voltar / Continuar".
// Medidas do Edge (07/11): caixa 680, centrada na altura; corpo 14 34 8; listas de 46ch (396,8 px: o ch da letra 16);
// o versículo de 44ch (320,2 px); o ✓ (a Painel ICM não tem) desenhado a 61,6 px do começo do item, 10,1 de largura.
import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
import "Tema.js" as T
import "Textos.js" as Tx
import "Icones.js" as Ic

Rectangle {
    id: bv
    property Item fundo: null                 // o que fica atrás (desfocado)
    property int passo: 0
    property var ig: ({ nome: "", cultos: [] })   // a igreja sendo editada no último passo (grava só no "Iniciar")
    signal pronto()                           // "Tudo pronto. Que Deus abençoe o culto."
    readonly property int total: 5
    readonly property bool ultimo: passo === total - 1
    anchors.fill: parent
    visible: false; z: 300
    color: T.estilo([".bv-overlay"], false).background

    function abrir() {
        passo = 0
        var g = controle.cfgLer("icm_igreja", {}) || {}
        var n = JSON.parse(JSON.stringify(g)); n.nome = g.nome || ""
        n.cultos = g.cultos && g.cultos.length ? JSON.parse(JSON.stringify(g.cultos)) : Tx.CULTOS_PADRAO.map(function (c) { return Object.assign({}, c) })
        ig = n
        nomeIg.text = n.nome
        visible = true; forceActiveFocus()
    }
    function fechar() { controle.cfgGravar("icm_bemvindo_ok", true); visible = false }     // fecharBemVindo
    function avancar() {
        if (!ultimo) { passo++; return }
        var n = Object.assign({}, ig); n.nome = nomeIg.text
        controle.gravarIgreja(n)                 // salvarIgreja + aplicarNomeIgreja
        fechar(); pronto()
    }
    focus: visible
    Keys.onEscapePressed: fechar()

    // o FUNDO desfocado (backdrop-filter: blur(3px)) por baixo da cor do véu
    ShaderEffectSource {
        id: copia
        anchors.fill: parent
        sourceItem: bv.visible ? bv.fundo : null
        live: bv.visible; visible: false
    }
    MultiEffect {
        anchors.fill: parent; z: -1
        source: copia
        blurEnabled: true; blur: 1.0; blurMax: 6          // ~ o desvio de 3 px do navegador
        visible: bv.visible && bv.fundo !== null
    }
    Rectangle { anchors.fill: parent; color: bv.color }    // a cor do véu POR CIMA do fundo desfocado
    MouseArea { anchors.fill: parent; hoverEnabled: true }  // o véu não deixa clicar atrás (e não fecha: igual à 3.0.13)

    // a caixa (.bv-box)
    Rectangle {
        id: caixa
        readonly property var s: T.estilo([".bv-box"], false)
        width: Math.min(680, bv.width * 0.96)
        height: rodape.y + rodape.height + 1          // o corpo começa 14 abaixo dos pontinhos (o padding de cima)
        anchors.centerIn: parent
        radius: s["border-radius"]; border.width: 1; border.color: T.V.borda
        gradient: Gradient {
            GradientStop { position: 0; color: caixa.s.background && caixa.s.background.paradas ? caixa.s.background.paradas[0].c : "#18263f" }
            GradientStop { position: 1; color: caixa.s.background && caixa.s.background.paradas ? caixa.s.background.paradas[caixa.s.background.paradas.length - 1].c : "#111c31" }
        }
        RectShadowCSS { z: -1; anchors.fill: parent; radius: parent.radius; sombra: caixa.s["box-shadow"] ? caixa.s["box-shadow"][0] : null }
        MouseArea { anchors.fill: parent }

        // os pontinhos (.bv-passos: padding 18 0 4, vão 7; o do passo atual com 20 de largura e cantos de 4)
        Item {
            id: passosRow
            x: 1; y: 1; width: caixa.width - 2; height: 18 + 7 + 4
            Row {
                y: 18; anchors.horizontalCenter: parent.horizontalCenter; spacing: 7
                Repeater {
                    model: bv.total
                    Rectangle {
                        width: index === bv.passo ? 20 : 7; height: 7; radius: index === bv.passo ? 4 : 3.5
                        color: index === bv.passo ? T.V.ouro : "#2c3d5c"
                        Behavior on width { NumberAnimation { duration: 200 } }
                        Behavior on color { ColorAnimation { duration: 200 } }
                    }
                }
            }
        }
        // o corpo (.bv-corpo: padding 14 34 8, tudo centrado)
        Column {
            id: corpo
            x: 1 + 34; y: passosRow.y + passosRow.height + 14
            width: caixa.width - 2 - 68
            readonly property var sp: T.estilo([".bv-corpo p"], false)
            readonly property var sh: T.estilo([".bv-corpo h2"], false)
            readonly property var ss: T.estilo([".bv-corpo p", ".bv-sub"], false)
            readonly property real ch16: 0.5391 * 16      // o "0" da Segoe a 16 px (46ch = 396,8 px, medido)
            Letra { anchors.horizontalCenter: parent.horizontalCenter; px: corpo.sh["font-size"]; weight: 700; color: corpo.sh.color
                    lsCss: corpo.sh["letter-spacing"]; text: ["Bem-vindo ao Sistema", "Louvores", "Bíblia", "Durante o culto", "Sua igreja"][bv.passo] }
            Item { width: 1; height: corpo.sh["margin-bottom"] }
            Letra { anchors.horizontalCenter: parent.horizontalCenter; px: corpo.ss["font-size"]; color: corpo.ss.color; linha: corpo.ss["line-height"]
                    text: ["A projeção da sua igreja, simples de operar.", "Toda a coletânea, na hora.", "Do versículo ao capítulo inteiro.",
                           "Você sempre sabe o que está no telão.", "Para os avisos saírem prontos."][bv.passo] }
            Item { width: 1; height: corpo.ss["margin-bottom"] }

            // PASSO 0: a marca, o versículo e o convite
            Column {
                visible: bv.passo === 0
                width: corpo.width
                Image { anchors.horizontalCenter: parent.horizontalCenter; width: 74; height: 74; source: Ic.marca(); smooth: true
                        sourceSize.width: 74 * Screen.devicePixelRatio; sourceSize.height: 74 * Screen.devicePixelRatio }
                Item { width: 1; height: 16 }
                // .bv-verso: itálico, borda dourada à esquerda, 44ch; letra e linha do .bv-corpo p (13,5 / 1,65), que vence
                Item {
                    readonly property var sv: T.estilo([".bv-corpo p", ".bv-verso"], false)
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 320.2; height: versoTx.height + 6 + versoRef.height
                    Rectangle { width: 2; height: parent.height; color: T.V.ouro }
                    Letra { id: versoTx; x: 16; width: parent.width - 16; quebra: Text.WordWrap; italico: true
                            px: parent.sv["font-size"]; color: parent.sv.color; linha: parent.sv["line-height"]
                            text: "“Escreve a visão e torna-a bem legível sobre tábuas, para que a possa ler quem passa correndo.”" }
                    Letra { id: versoRef; x: 16; y: versoTx.height + 6; px: 11; lsCss: 1.4; maiusculas: true; color: T.V.ouro
                            linha: 1.65 * 13.5 / 11; text: "Habacuque 2:2" }
                }
                Item { width: 1; height: 16 }
                Letra { width: corpo.width; quebra: Text.WordWrap; alinhamento: Text.AlignHCenter; px: corpo.sp["font-size"]; color: corpo.sp.color
                        linha: corpo.sp["line-height"]; text: "Em poucos passos você vê como tudo funciona. Se preferir, pode pular e começar direto." }
            }
            // PASSOS 1 a 3: as listas (.bv-lista: 46ch, vão 10; o ponto dourado de 7 px)
            Column {
                visible: bv.passo >= 1 && bv.passo <= 3
                anchors.horizontalCenter: parent.horizontalCenter
                width: 46 * corpo.ch16
                spacing: 10
                readonly property string bo: "<b><font color=\"#ffffff\">"
                readonly property string bc: "</font></b>"
                readonly property var itens: [
                    [],
                    [bo + "Um clique" + bc + " no louvor já mostra os slides.", bo + "Dois cliques" + bc + " mandam ele para a Lista de projeção.",
                     "Procure por " + bo + "número, nome ou um trecho da letra" + bc + ".", "A letra " + bo + "se ajusta sozinha" + bc + " para caber na tela."],
                    [bo + "Um clique" + bc + " no versículo projeta na hora.", bo + "Dois cliques" + bc + " guardam ele na Lista de projeção.",
                     bo + "Avançar" + bc + " segue a ordem que você montou e depois continua sozinho pelo capítulo.",
                     "Marque o <font color=\"#00000000\">a|</font> dos versículos na Lista e eles aparecem " + bo + "juntos" + bc + " numa tela só."],
                    ["A " + bo + "faixa vermelha" + bc + " avisa quando está " + bo + "AO VIVO" + bc + ".",
                     bo + "Congelar" + bc + " segura a imagem para você preparar o próximo sem ninguém ver.",
                     bo + "Parar de projetar" + bc + " (ou a tecla " + bo + "P" + bc + ") volta para a tela de espera.",
                     "As " + bo + "setas do teclado" + bc + " avançam e voltam."]][bv.passo] || []
                Repeater {
                    model: parent.itens
                    Item {
                        width: parent.width; height: li.height
                        Rectangle { y: 7; width: 7; height: 7; radius: 3.5; color: T.V.ouro }
                        Letra { id: li; x: 20; width: parent.width - 20; quebra: Text.WordWrap; textFormat: Text.StyledText
                                px: 13.5; color: "#cdd9ee"; linha: 1.5; text: modelData }
                        // o ✓ (negrito, branco) no lugar reservado do item "Marque o ✓": 61,6 px depois do começo, 10,1 de largura
                        Shape {
                            visible: modelData.indexOf("Marque o") === 0
                            x: 20 + 61.6; y: li.ascPx - 9.5; width: 10.1; height: 10
                            preferredRendererType: Shape.CurveRenderer
                            ShapePath { strokeColor: "white"; strokeWidth: 1.9; fillColor: "transparent"; capStyle: ShapePath.RoundCap
                                        joinStyle: ShapePath.RoundJoin
                                        startX: 1; startY: 5.6; PathLine { x: 3.8; y: 8.6 } PathLine { x: 9.4; y: 1.2 } }
                        }
                    }
                }
            }
            // PASSO 4: a igreja (o texto, o nome e os cultos numa caixa que rola, 230 no máximo)
            Column {
                visible: bv.ultimo
                width: corpo.width
                Letra { width: corpo.width; quebra: Text.WordWrap; alinhamento: Text.AlignHCenter; px: corpo.sp["font-size"]; color: corpo.sp.color
                        linha: corpo.sp["line-height"]; text: "Diga o nome da sua igreja e marque os cultos. O Sistema monta os avisos do dia sozinho." }
                Item { width: 1; height: 16 }
                Entrada { id: nomeIg; objectName: "bvNome"; width: corpo.width; sels: ["input[type=text]"]; navegador: false
                          placeholder: "Nome da igreja (ex.: ICM Iperó)" }     // posto ao abrir (ligado à igreja, sumia ao marcar um culto)
                Item { width: 1; height: 6 }
                Flickable {
                    width: corpo.width; height: Math.min(230, cultosCol.height); clip: true
                    contentHeight: cultosCol.height; boundsBehavior: Flickable.StopAtBounds
                    Column {
                        id: cultosCol
                        width: corpo.width - 4                 // .bv-cultos{padding-right:4px}
                        Repeater {
                            model: [0, 1, 2, 3, 4, 5, 6].filter(function (d) { return bv.ig.cultos.some(function (c) { return c.dia === d }) })
                            Column {
                                width: cultosCol.width
                                readonly property int dia: modelData
                                Item { width: 1; height: 12 }
                                Letra { px: 11.5; weight: 700; color: T.V.ouro; lsCss: 1; maiusculas: true; text: Tx.DIAS_NOME[dia] }
                                Item { width: 1; height: 6 }
                                Repeater {
                                    id: repDia
                                    model: bv.ig.cultos.map(function (c, i) { return i }).filter(function (i) { return bv.ig.cultos[i].dia === dia })
                                    Column {
                                        width: cultosCol.width
                                        readonly property int ci: modelData
                                        Rectangle {
                                            width: parent.width; height: 45; radius: 8
                                            color: maL.containsMouse ? "#12203a" : "#0c1830"
                                            MouseArea { id: maL; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                                        onClicked: { var c = bv.ig.cultos.slice(); c[ci] = Object.assign({}, c[ci], { on: !c[ci].on }); var n = Object.assign({}, bv.ig); n.cultos = c; bv.ig = n } }
                                            MarcarChrome { x: 12; anchors.verticalCenter: parent.verticalCenter; marcada: !!bv.ig.cultos[ci].on }
                                            Letra { x: 39; anchors.verticalCenter: parent.verticalCenter; px: 13; color: T.V.txt; text: bv.ig.cultos[ci].nome }
                                            CampoChrome { x: parent.width - 12 - width; anchors.verticalCenter: parent.verticalCenter; modo: "hora"
                                                          valor: bv.ig.cultos[ci].hora
                                                          onMudou: (v) => { var c = bv.ig.cultos.slice(); c[ci] = Object.assign({}, c[ci], { hora: v }); var n = Object.assign({}, bv.ig); n.cultos = c; bv.ig = n } }
                                        }
                                        // a margem de 5 da última linha do dia colapsa com os 12 do título do próximo (fica a maior)
                                        Item { width: 1; height: index < repDia.count - 1 ? 5 : 0 }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            Item { width: 1; height: 8 }
        }
        // o rodapé (.bv-rodape: borda em cima, padding 16 26 20)
        Item {
            id: rodape
            x: 1; y: corpo.y + corpo.height + 8; width: caixa.width - 2; height: 1 + 16 + 36 + 20
            Rectangle { width: parent.width; height: 1; color: T.V.borda }
            // "Pular apresentação" / "Deixar para depois" (sublinhado)
            Item {
                id: pular
                objectName: "bvPular"
                x: 26; y: 1 + 16 + (36 - 28) / 2; width: pularTx.implicitTextWidth + 4; height: 28
                Letra { id: pularTx; x: 2; anchors.verticalCenter: parent.verticalCenter; px: 12.5
                        color: maPular.containsMouse ? "#cdd9ee" : "#7f96b8"; text: bv.ultimo ? "Deixar para depois" : "Pular apresentação" }
                Rectangle { x: 2; y: pularTx.y + pularTx.ascPx + 1.5; width: pularTx.implicitTextWidth; height: 1; color: pularTx.color }
                MouseArea { id: maPular; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: bv.fechar() }
            }
            Row {
                x: parent.width - 26 - width; y: 1 + 16
                spacing: 8
                Caixa { objectName: "bvVoltar"; sels: [".big-btn"]; texto: "Voltar"; opacity: bv.passo === 0 ? 0 : 1; enabled: bv.passo > 0
                        onClicado: bv.passo-- }
                Caixa { objectName: "bvAvancar"; sels: [".big-btn", ".big-btn.verde"]; texto: bv.ultimo ? "Iniciar o Sistema" : "Continuar"
                        onClicado: bv.avancar() }
            }
        }
    }
}
