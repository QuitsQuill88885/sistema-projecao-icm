// AS ABAS DE CARD da 3.0.13 (<div class="view centro">): TIMER (o cronômetro), RELÓGIO e TEXTO & AVISOS. O card fica no
// meio da área (place-items:center), com o degradê, a borda, os cantos de 14 e a sombra do .card do app.css.
import QtQuick
import QtQuick.Effects
import "Tema.js" as T

Item {
    id: vc
    property string qual: "timer"            // "timer" | "relogio" | "texto"
    property var timerInfo: ({ estado: "parado" })
    property var avisos: []
    property var lisos: []
    property string fundoTexto: ""
    property bool textoNoAr: false
    property alias tituloAviso: campoTitulo
    property alias corpoAviso: campoTexto
    property alias rotTimer: campoRotulo
    signal iniciarTimer(real minutos, string rotulo)
    signal pausarTimer()
    signal pararTimer()
    signal projetarRelogio()
    signal projetarTexto(string titulo, string corpo, string fundo, bool instantaneo)
    signal escolherFundo(string arquivo)
    signal recado(string m)

    readonly property var sCentro: T.estilo([".centro"], false)
    readonly property var sCard: T.estilo([".card"], false)
    readonly property var sRow: T.estilo([".row"], false)
    Rectangle { anchors.fill: parent; color: vc.sCentro.background }

    // ---- o mostrador do timer e o do relógio (setInterval de 250 ms / 1 s do app.js)
    property int minutos: 5
    property string mostrador: fmt(minutos * 60000)
    function fmt(ms) {
        var s = Math.max(0, Math.round(ms / 1000)), h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60
        return h ? h + ":" + ("0" + m).slice(-2) + ":" + ("0" + (s % 60)).slice(-2) : Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2)
    }
    function rotuloMin(min) {
        var h = Math.floor(min / 60), m = min % 60
        if (!m) return h + (h === 1 ? " hora" : " horas")
        return h + "h" + ("0" + m).slice(-2)
    }
    function passo(min, sentido) {                       // passoDoTempo: 1 min no começo, 30 min depois das 3 horas
        var p = min < 15 ? 1 : (min < 60 ? 5 : (min < 180 ? 15 : 30))
        var bruto = min + sentido * p
        return Math.max(1, Math.min(600, sentido > 0 ? Math.floor(bruto / p) * p : Math.ceil(bruto / p) * p))
    }
    Timer {
        interval: 250; repeat: true; triggeredOnStart: true
        running: vc.visible && (vc.qual === "relogio" || vc.timerInfo.estado === "correndo")
        onTriggered: {
            var d = new Date()
            if (vc.qual === "relogio") horaAgora.text = ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2)
            else vc.mostrador = vc.fmt(vc.timerInfo.fimTs - d.getTime())
        }
    }
    onTimerInfoChanged: if (timerInfo.estado === "pausado") mostrador = fmt(timerInfo.ms); else if (timerInfo.estado === "parado") mostrador = fmt(minutos * 60000)
    onMinutosChanged: if (timerInfo.estado === "parado") mostrador = fmt(minutos * 60000)

    Flickable {
        id: rolo
        anchors.fill: parent
        contentWidth: width; contentHeight: Math.max(height, card.height + vc.sCentro.padding[0] + vc.sCentro.padding[2])
        clip: true; boundsBehavior: Flickable.StopAtBounds
        Rectangle {
            id: card; objectName: "card_" + vc.qual
            // .card{width:min(620px,88%)} · o do Texto: min(820px,96%)
            width: vc.qual === "texto" ? Math.min(820, rolo.width * 0.96) : Math.min(620, rolo.width * 0.88)
            height: corpo.height + vc.sCard.padding[0] + vc.sCard.padding[2] + 2 * vc.sCard.border.w
            x: Math.round((rolo.width - width) / 2)
            y: Math.max(vc.sCentro.padding[0], Math.round((rolo.contentHeight - height) / 2))
            radius: vc.sCard["border-radius"]
            border.width: vc.sCard.border.w; border.color: vc.sCard.border.cor
            gradient: Gradient {
                GradientStop { position: 0; color: vc.sCard.background.paradas[0].c }
                GradientStop { position: 1; color: vc.sCard.background.paradas[1].c }
            }
            RectShadowCSS { z: -1; anchors.fill: parent; radius: parent.radius; sombra: vc.sCard["box-shadow"][0] }
            Column {
                id: corpo
                x: vc.sCard.padding[3] + vc.sCard.border.w; y: vc.sCard.padding[0] + vc.sCard.border.w
                width: card.width - vc.sCard.padding[1] - vc.sCard.padding[3] - 2 * vc.sCard.border.w
                // <h2>: negrito do navegador; dourado 15,5 px; margem embaixo 4
                Caixa {
                    clicavel: false; alinhar: Qt.AlignLeft; sels: [".card h2"]; herda: ({ "font-weight": 700 })
                    texto: vc.qual === "timer" ? "Cronômetro" : (vc.qual === "relogio" ? "Relógio" : "Texto & Avisos")
                }
                // margens verticais vizinhas COLAPSAM no CSS (vale a maior): o h2 (4) antes do mostrador do relógio (18) não soma
                Item { width: 1; height: vc.qual === "relogio" ? 0 : T.estilo([".card h2"], false)["margin-bottom"] }

                // ======== TIMER
                Column {
                    visible: vc.qual === "timer"; width: parent.width
                    Flow {
                        width: parent.width; spacing: vc.sRow.gap
                        Caixa { sels: [".big-btn", ".big-btn.ouro"]; texto: "5 minutos"; pulso: true; onClicado: vc.minutos = 5 }
                        Caixa { sels: [".big-btn"]; texto: "3 min"; pulso: true; onClicado: vc.minutos = 3 }
                        Caixa { sels: [".big-btn"]; texto: "10 min"; pulso: true; onClicado: vc.minutos = 10 }
                        // o seletor de minutos (.passo-num): − [número] min +
                        Rectangle {
                            id: passo
                            readonly property var s: T.estilo([".passo-num"], false)
                            width: linhaPasso.width + s.padding[1] + s.padding[3] + 2 * s.border.w; height: s.height
                            radius: s["border-radius"]; color: s.background; border.width: s.border.w; border.color: s.border.cor
                            Row {
                                id: linhaPasso
                                x: passo.s.padding[3] + passo.s.border.w; anchors.verticalCenter: parent.verticalCenter; spacing: passo.s.gap
                                Caixa { objectName: "minMenos"; sels: [".pn-b"]; texto: "−"; anchors.verticalCenter: parent.verticalCenter
                                        onClicado: vc.minutos = vc.passo(vc.minutos, -1) }
                                Letra {
                                    readonly property var s: T.estilo([".passo-num input[type=number]"], false)
                                    largura: s.width; alinhamento: Text.AlignRight; px: s["font-size"]; weight: s["font-weight"]; color: T.V.txt
                                    text: String(vc.minutos); anchors.verticalCenter: parent.verticalCenter
                                }
                                Letra {
                                    readonly property var s: T.estilo([".pn-un"], false)
                                    px: s["font-size"]; weight: s["font-weight"]; color: s.color
                                    text: vc.minutos < 60 ? "min" : "min · " + vc.rotuloMin(vc.minutos)
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Item { width: Math.max(0, T.estilo([".pn-un"], false)["margin-right"] - parent.spacing); height: 1 }
                                Caixa { objectName: "minMais"; sels: [".pn-b"]; texto: "+"; anchors.verticalCenter: parent.verticalCenter
                                        onClicado: vc.minutos = vc.passo(vc.minutos, 1) }
                            }
                        }
                        Entrada {
                            id: campoRotulo; objectName: "rotuloTimer"
                            navegador: false; sels: ["input[type=text]", ".view[data-aba=\"timer\"] .row input[type=text]"]
                            alturaFixa: 36; text: "Oração"; placeholder: "Rótulo"
                            // style="flex:1;min-width:120px": o resto da fileira
                            width: Math.max(120, corpo.width - (passo.x + passo.width + vc.sRow.gap))
                        }
                    }
                    // (a margem de baixo da fileira, 12, colapsa com a de cima do mostrador, 18: vale 18, medido no Edge)
                    // o mostrador grande (.timer-display): 54 px, 800, dourado, com o brilho dourado embaixo
                    Item {
                        readonly property var s: T.estilo([".timer-display"].concat(vc.timerInfo.estado === "pausado" ? [".timer-display.pausado"] : []), false)
                        width: parent.width; height: mostradorTxt.height + s.margin[0] + s.margin[2]
                        Letra {
                            id: mostradorTxt; objectName: "mostradorTimer"
                            readonly property var s: parent.s
                            y: s.margin[0]; anchors.horizontalCenter: parent.horizontalCenter
                            px: s["font-size"]; weight: s["font-weight"]; color: s.color; lsCss: s["letter-spacing"]
                            opacity: s.opacity !== undefined ? s.opacity : 1
                            text: vc.mostrador
                            // text-shadow 0 4px 20px #f5d76e22: o brilho dourado embaixo do número
                            layer.enabled: true
                            layer.effect: MultiEffect {
                                readonly property var sh: (T.estilo([".timer-display"], false)["text-shadow"] || [null])[0]
                                // a cor do CSS tem transparência (#f5d76e22 = 13%): no MultiEffect ela vai como opacidade da sombra
                                readonly property color c: sh ? sh.cor : "transparent"
                                shadowEnabled: !!sh; shadowColor: Qt.rgba(c.r, c.g, c.b, 1); shadowOpacity: c.a
                                shadowVerticalOffset: sh ? sh.y : 0; shadowHorizontalOffset: sh ? sh.x : 0
                                blurMax: sh ? sh.blur : 0; shadowBlur: 1.0
                            }
                        }
                    }
                    Flow {
                        width: parent.width; spacing: vc.sRow.gap
                        Caixa { objectName: "timerIniciar"; sels: [".big-btn", ".big-btn.verde"]; texto: "Iniciar e Projetar"; pulso: true
                                onClicado: vc.iniciarTimer(vc.minutos, campoRotulo.text) }
                        Caixa { objectName: "timerPausar"; sels: [".big-btn"]; estados: vc.timerInfo.estado === "pausado" ? [".big-btn.ativo"] : []; pulso: true
                                texto: vc.timerInfo.estado === "pausado" ? "Continuar" : "Pausar"; onClicado: vc.pausarTimer() }
                        Caixa { objectName: "timerParar"; sels: [".big-btn", ".big-btn.vermelho"]; texto: "Parar"; pulso: true; onClicado: vc.pararTimer() }
                    }
                    Item { width: 1; height: vc.sRow["margin-bottom"] }
                }

                // ======== RELÓGIO
                Column {
                    visible: vc.qual === "relogio"; width: parent.width
                    Item {
                        readonly property var s: T.estilo([".timer-display"], false)
                        width: parent.width; height: horaAgora.height + s.margin[0] + s.margin[2]
                        Letra { id: horaAgora; objectName: "mostradorRelogio"; y: parent.s.margin[0]; anchors.horizontalCenter: parent.horizontalCenter
                                px: parent.s["font-size"]; weight: parent.s["font-weight"]; color: parent.s.color; lsCss: parent.s["letter-spacing"]; text: "--:--" }
                    }
                    Flow {
                        width: parent.width; spacing: vc.sRow.gap
                        Caixa { objectName: "relogioProjetar"; sels: [".big-btn", ".big-btn.verde"]; texto: "Projetar Relógio"; pulso: true; onClicado: vc.projetarRelogio() }
                    }
                    Item { width: 1; height: vc.sRow["margin-bottom"] }
                }

                // ======== TEXTO & AVISOS
                Column {
                    visible: vc.qual === "texto"; width: parent.width
                    readonly property var sl: T.estilo([".campo-lbl"], false)
                    Caixa { clicavel: false; alinhar: Qt.AlignLeft; sels: [".campo-lbl"]; texto: "Avisos prontos — clique para preencher" }
                    Item { width: 1; height: parent.sl["margin-bottom"] }
                    // .av-lista: a 1ª regra do app.css põe flex-direction:column e a 2ª não desfaz -> os chips EMPILHADOS, na
                    // largura toda (é assim que a 3.0.13 aparece; medido no Edge: 770 x 32, vão 7)
                    Column {
                        width: parent.width; spacing: T.estilo([".av-lista"], false).gap
                        Repeater {
                            model: vc.avisos
                            Caixa {
                                width: parent.width
                                sels: [".av-chip"]; estados: modelData.auto ? [".av-chip.auto"] : []
                                texto: modelData.nome
                                onClicado: {
                                    campoTitulo.text = modelData.titulo; campoTexto.text = modelData.corpo
                                    vc.projetarTexto(modelData.titulo, modelData.corpo, vc.fundoTexto, false)
                                    vc.recado("Aviso preenchido. Ajuste se desejar e projete.")
                                }
                            }
                        }
                    }
                    Item { width: 1; height: 18 }
                    Caixa { clicavel: false; alinhar: Qt.AlignLeft; sels: [".campo-lbl"]; texto: "Título" }
                    Item { width: 1; height: parent.sl["margin-bottom"] }
                    Entrada {
                        id: campoTitulo; objectName: "tituloAviso"; larguraPadrao: true
                        navegador: false; sels: ["input[type=text]"]; placeholder: "Ex.: AVISO"
                        onTextChanged: if (vc.textoNoAr) vc.projetarTexto(campoTitulo.text, campoTexto.text, vc.fundoTexto, true)   // ao vivo
                    }
                    Item { width: 1; height: 14 }
                    Caixa { clicavel: false; alinhar: Qt.AlignLeft; sels: [".campo-lbl"]; texto: "Texto" }
                    Item { width: 1; height: parent.sl["margin-bottom"] }
                    CaixaTexto {
                        id: campoTexto; objectName: "corpoAviso"; width: parent.width
                        placeholder: "Escreva aqui. Cada linha aparece numa linha da tela."
                        onTextChanged: if (vc.textoNoAr) vc.projetarTexto(campoTitulo.text, campoTexto.text, vc.fundoTexto, true)
                    }
                    // o <textarea> é um elemento em linha: deixa embaixo o espaço da linha de base (o descendente da letra de 16 px)
                    Item { width: 1; height: Math.round(T.FONTE.desc * 16) + 16 }
                    Caixa { clicavel: false; alinhar: Qt.AlignLeft; sels: [".campo-lbl"]; texto: "Fundo" }
                    Item { width: 1; height: parent.sl["margin-bottom"] }
                    // os fundos lisos (.fundos-liso: colunas de no mínimo 140, vão 10)
                    Grid {
                        id: gLiso
                        readonly property var sg: T.estilo([".fundos-liso"], false)
                        width: parent.width
                        columns: Math.max(1, Math.floor((width + sg.gap) / (140 + sg.gap)))
                        readonly property real cel: (width - (columns - 1) * sg.gap) / columns
                        spacing: sg.gap
                        Repeater {
                            model: vc.lisos
                            Rectangle {
                                readonly property bool sel: modelData.arquivo === vc.fundoTexto
                                readonly property var s: T.estilo([".liso-card"].concat(sel ? [".liso-card.sel"] : []), maLiso.containsMouse)
                                width: gLiso.cel; height: width * 9 / 16 + nomeLiso.height + T.estilo([".liso-card span"], false).padding[0] * 2
                                radius: s["border-radius"]; color: s.background; border.width: s.border.w; border.color: s["border-color"] || s.border.cor
                                clip: true
                                Image { x: parent.border.width; y: parent.border.width; width: parent.width - 2 * x; height: (parent.width) * 9 / 16 - x
                                        source: modelData.url; fillMode: Image.PreserveAspectCrop; asynchronous: true; sourceSize.width: 280 }
                                Caixa {
                                    id: nomeLiso; clicavel: false
                                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
                                    sels: [".liso-card span"].concat(parent.sel ? [".liso-card.sel span"] : []); texto: modelData.nome
                                }
                                MouseArea { id: maLiso; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                            onClicked: { vc.escolherFundo(modelData.arquivo); if (vc.textoNoAr) vc.projetarTexto(campoTitulo.text, campoTexto.text, modelData.arquivo, false) } }
                            }
                        }
                    }
                    Item { width: 1; height: 16 }
                    Flow {
                        width: parent.width; spacing: vc.sRow.gap
                        Caixa { objectName: "textoProjetar"; sels: [".big-btn", ".big-btn.verde"]; texto: "Projetar"; pulso: true
                                onClicado: vc.projetarTexto(campoTitulo.text, campoTexto.text, vc.fundoTexto, false) }
                    }
                    Item { width: 1; height: vc.sRow["margin-bottom"] }
                }
            }
        }
    }
}
