// O MENU ☰ da 3.0.13 (#menu-overlay do index.html; abrirMenu/menuSecao/fecharMenu do app.js): o véu escuro na janela
// inteira e, à esquerda, a gaveta "Configurações" (.menu-lateral) com as 7 abas (.menu-aba) e o corpo de cada seção.
// Abre sempre no Início ("abre calmo"); clicar no véu ou Esc fecha. Medidas e cores: as regras .menu-* e .ini-* do app.css.
import QtQuick
import "Tema.js" as T
import "Icones.js" as Ic
import "Textos.js" as Tx

Rectangle {
    id: mn
    property string secao: "inicio"
    property string igreja: ""              // IGREJA.nome (o subtítulo do Início)
    property string versao: ""              // o rodapé do Início ("Versão ...")
    signal rever()                          // "Como funciona": rever a apresentação
    readonly property var abas: [["inicio", "Início"], ["igreja", "Minha igreja"], ["louvores", "Meus louvores"],
                                 ["celular", "Celular"], ["musica", "Música"], ["painel", "Painel"], ["sistema", "Sistema"]]
    property var rede: ({ url: "", qr: "" })  // o endereço e o QR do celular (lidos ao abrir, como o mostrarRede)
    signal copiado()
    signal salvouIgreja()
    signal abrirAssistente(string nome)       // a janela do assistente fica no painel, por cima do menu
    function abrir() { secao = "inicio"; corpo.contentY = 0; rede = controle.redeCelular(); secIg.carregar(); secLv.carregar(); visible = true; forceActiveFocus() }
    signal recado(string t)
    function fechar() { visible = false }
    function ir(s) { secao = s; corpo.contentY = 0 }
    onSecaoChanged: if (secao === "painel") secPn.carregar()       // o abrirPainel: lê o histórico ao entrar

    anchors.fill: parent
    visible: false; z: 150
    color: T.estilo([".menu-overlay"], false).background
    focus: visible
    Keys.onEscapePressed: fechar()
    MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: mn.fechar() }     // o clique no véu fecha

    // a gaveta (.menu-lateral): degradê de cima para baixo, borda à direita e a sombra para o lado
    Caixa {
        id: gaveta
        clicavel: false
        sels: [".menu-lateral"]
        width: Math.min(560, mn.width * 0.94); height: mn.height
        RectShadowCSS { z: -1; anchors.fill: parent; sombra: gaveta.st["box-shadow"] ? gaveta.st["box-shadow"][0] : null }
        MouseArea { anchors.fill: parent }                         // o clique na gaveta não fecha
        // só a borda da direita (border-right), por cima do fundo
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: T.V.borda }

        // .menu-topo: "Configurações" e o ✕
        Item {
            id: topo
            readonly property var s: T.estilo([".menu-topo"], false)
            width: parent.width - 1; height: s.padding[0] + 30 + s.padding[2] + 1
            Caixa {
                clicavel: false; alinhar: Qt.AlignLeft
                sels: [".menu-topo h2"]; herda: ({ "font-weight": 700 }); texto: "Configurações"
                x: topo.s.padding[3]; anchors.verticalCenter: x0.verticalCenter
            }
            Caixa {
                id: x0
                objectName: "menuFechar"
                sels: [".menu-x"]; texto: ""
                x: topo.width - topo.s.padding[1] - width; y: topo.s.padding[0]
                SinalFila { anchors.centerIn: parent; tipo: "x"; cor: x0.corLetra; px: x0.tamLetra }
                onClicado: mn.fechar()
            }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: T.V.borda }
        }
        // .menu-abas
        Item {
            id: barraAbas
            readonly property var s: T.estilo([".menu-abas"], false)
            y: topo.height; width: parent.width - 1; height: s.padding[0] + linhaAbas.height + 1
            // as abas não cabem nos 560 px: encolhem como o flex do navegador (flex-shrink 1, na proporção do tamanho
            // natural, sem passar da maior palavra) e o texto quebra ("Minha / igreja"); a linha fica com a mais alta
            readonly property var sa: T.estilo([".menu-aba"], false)
            readonly property real padH: sa.padding[1] + sa.padding[3]
            readonly property real livre: width - s.padding[1] - s.padding[3] - s.gap * (mn.abas.length - 1)
            property var larguras: []
            function medir() {
                var nat = [], min = [], k
                for (k = 0; k < mn.abas.length; k++) {
                    var m = medidas.itemAt(k)
                    if (!m) return
                    nat.push(m.cheio + padH); min.push(m.palavra + padH)
                }
                var w = nat.slice(), fixo = nat.map(function () { return false })
                for (var volta = 0; volta < nat.length; volta++) {
                    var soma = 0, base = 0
                    for (k = 0; k < nat.length; k++) { soma += fixo[k] ? w[k] : nat[k]; if (!fixo[k]) base += nat[k] }
                    var falta = soma - livre
                    if (falta <= 0 || base <= 0) { for (k = 0; k < nat.length; k++) if (!fixo[k]) w[k] = nat[k]; break }
                    var travou = false
                    for (k = 0; k < nat.length; k++) {
                        if (fixo[k]) continue
                        w[k] = nat[k] - falta * nat[k] / base
                        if (w[k] < min[k]) { w[k] = min[k]; fixo[k] = true; travou = true }
                    }
                    if (!travou) break
                }
                larguras = w
            }
            onLivreChanged: Qt.callLater(medir)
            Repeater {      // a régua: o texto inteiro e a maior palavra de cada aba (invisível)
                id: medidas
                model: mn.abas
                Item {
                    visible: false
                    readonly property real cheio: lc.implicitTextWidth
                    property real palavra: 0
                    Letra { id: lc; px: barraAbas.sa["font-size"]; weight: barraAbas.sa["font-weight"]; text: modelData[1] }
                    Repeater {
                        id: palavras
                        model: modelData[1].split(" ")
                        Letra { px: barraAbas.sa["font-size"]; weight: barraAbas.sa["font-weight"]; text: modelData
                                onImplicitTextWidthChanged: parent.palavra = Math.max(parent.palavra, implicitTextWidth)
                                Component.onCompleted: parent.palavra = Math.max(parent.palavra, implicitTextWidth) }
                    }
                    onPalavraChanged: Qt.callLater(barraAbas.medir)
                }
            }
            Row {
                id: linhaAbas
                x: barraAbas.s.padding[3]; y: barraAbas.s.padding[0]
                spacing: barraAbas.s.gap

                Repeater {
                    id: repAbas
                    model: mn.abas
                    Caixa {
                        id: aba
                        objectName: "menuAba_" + modelData[0]
                        sels: [".menu-aba"]; estados: mn.secao === modelData[0] ? [".menu-aba.ativo"] : []
                        texto: ""
                        width: barraAbas.larguras[index] !== undefined ? barraAbas.larguras[index] : implicitWidth
                        readonly property real natural: pad[0] + rot2.implicitHeight + pad[2]
                        onNaturalChanged: Qt.callLater(linhaAbas.recalc)
                        height: Math.max(natural, linhaAbas.alturaMax)
                        Letra {
                            id: rot2
                            anchors.centerIn: parent
                            width: aba.width - aba.pad[1] - aba.pad[3]
                            quebra: Text.WordWrap; alinhamento: Text.AlignHCenter
                            px: aba.tamLetra; weight: aba.st["font-weight"]; color: aba.corLetra; text: modelData[1]
                        }
                        onClicado: mn.ir(modelData[0])
                    }
                }
                // a linha estica todas até a mais alta (align-items: stretch); recalculada quando uma aba muda de altura
                property real alturaMax: 0
                function recalc() {
                    var m = 0
                    for (var k = 0; k < mn.abas.length; k++) { var a = repAbas.itemAt(k); if (a) m = Math.max(m, a.natural) }
                    alturaMax = m
                }
            }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: T.V.borda }
        }
        // .menu-corpo: rola; padding 20
        Flickable {
            id: corpo
            objectName: "menuCorpo"
            readonly property real pd: T.estilo([".menu-corpo"], false).padding[0]
            y: barraAbas.y + barraAbas.height; width: parent.width - 1; height: parent.height - y
            clip: true; boundsBehavior: Flickable.StopAtBounds
            contentWidth: width; contentHeight: secoes.height + 2 * pd
            Item {
                id: secoes
                x: corpo.pd; y: corpo.pd; width: corpo.width - 2 * corpo.pd
                height: mn.secao === "inicio" ? inicio.height : mn.secao === "celular" ? secCel.height
                      : mn.secao === "musica" ? secMus.height : mn.secao === "igreja" ? secIg.height : mn.secao === "louvores" ? secLv.height : mn.secao === "painel" ? secPn.height : mn.secao === "sistema" ? secSis.height : 0

                // ---- INÍCIO
                Column {
                    id: inicio
                    visible: mn.secao === "inicio"
                    width: parent.width
                    Item { width: 1; height: 14 }                                         // .ini-marca margin 14 0 10
                    Image {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 52; height: 52; sourceSize.width: 52 * Screen.devicePixelRatio; sourceSize.height: 52 * Screen.devicePixelRatio
                        source: Ic.marca(); smooth: true
                    }
                    Item { width: 1; height: 10 }
                    Caixa { clicavel: false; anchors.horizontalCenter: parent.horizontalCenter
                            sels: [".ini-tit"]; herda: ({ "font-weight": 700 }); texto: "Sistema" }
                    Caixa { clicavel: false; anchors.horizontalCenter: parent.horizontalCenter
                            sels: [".ini-sub"]; texto: mn.igreja || "Projeção para a sua igreja" }
                    Item { width: 1; height: T.estilo([".ini-sub"], false)["margin-bottom"] }
                    Grid {
                        id: cartoes
                        readonly property real vao: T.estilo([".ini-cards"], false).gap
                        columns: 2; columnSpacing: vao; rowSpacing: vao
                        readonly property real larg: (parent.width - vao) / 2
                        Repeater {
                            id: repCartoes
                            model: [["igreja", "Minha igreja", "Nome e horários dos cultos"],
                                    ["louvores", "Meus louvores", "Adicionar ou corrigir letras"],
                                    ["rever", "Como funciona", "Rever a apresentação"],
                                    ["sistema", "Sistema", "Restaurar o padrão"]]
                            Caixa {
                                id: card
                                objectName: "iniCard_" + modelData[0]
                                sels: [".ini-card"]; texto: ""
                                width: cartoes.larg
                                // a linha toda da grade fica com a altura do maior (grid: stretch)
                                height: Math.max(natural, repCartoes.itemAt(index ^ 1) ? repCartoes.itemAt(index ^ 1).natural : 0)
                                readonly property real natural: pad[0] + col.height + pad[2] + 2 * bw
                                Column {
                                    id: col
                                    x: card.pad[3] + card.bw; y: card.pad[0] + card.bw
                                    width: card.width - card.pad[1] - card.pad[3] - 2 * card.bw
                                    spacing: card.st.gap
                                    Letra { readonly property var s: T.estilo([".ini-card b"], false)
                                            px: s["font-size"]; weight: 700; color: s.color; text: modelData[1] }
                                    Letra { readonly property var s: T.estilo([".ini-card small"], false)
                                            width: col.width; quebra: Text.WordWrap
                                            px: s["font-size"]; color: s.color; linha: s["line-height"]; text: modelData[2] }
                                }
                                onClicado: modelData[0] === "rever" ? (mn.fechar(), mn.rever()) : mn.ir(modelData[0])
                            }
                        }
                    }
                    Item { width: 1; height: T.estilo([".ini-rodape"], false)["margin-top"] }
                    Caixa { clicavel: false; anchors.horizontalCenter: parent.horizontalCenter
                            sels: [".ini-rodape"]
                            texto: (mn.versao ? "Versão " + mn.versao : "Sistema Nativo") + " · Feito para a Igreja Cristã Maranata · funciona sem internet" }
                    Item { width: 1; height: T.estilo([".ini-autor"], false)["margin-top"] }
                    Row {
                        anchors.horizontalCenter: parent.horizontalCenter
                        readonly property var s: T.estilo([".ini-autor"], false)
                        readonly property var sb: T.estilo([".ini-autor b"], false)
                        Letra { px: parent.s["font-size"]; lsCss: parent.s["letter-spacing"]; color: parent.s.color; text: "Desenvolvido por " }
                        Letra { px: parent.s["font-size"]; lsCss: parent.s["letter-spacing"]; color: parent.sb.color; weight: parent.sb["font-weight"]
                                text: "Samuel Mariano Ribeiro" }
                    }
                }

                // ---- CELULAR (o texto vem do index.html; a caixa do QR é desenhada aqui)
                TextoMenu {
                    id: secCel
                    visible: mn.secao === "celular"
                    width: parent.width
                    blocos: Tx.SECOES.celular
                    especiais: ({ "cel-caixa": celCaixa })
                }
                // ---- MINHA IGREJA
                SecIgreja {
                    id: secIg
                    visible: mn.secao === "igreja"
                    width: parent.width
                    onSalvou: mn.salvouIgreja()
                }
                // ---- MEUS LOUVORES
                SecLouvores {
                    id: secLv
                    visible: mn.secao === "louvores"
                    width: parent.width
                    onRecado: (t) => mn.recado(t)
                }
                // ---- PAINEL DO CULTO
                SecPainel {
                    id: secPn
                    visible: mn.secao === "painel"
                    width: parent.width
                }
                // ---- SISTEMA
                SecSistema {
                    id: secSis
                    visible: mn.secao === "sistema"
                    width: parent.width
                    onAssistente: (n) => mn.abrirAssistente(n)
                }
                // ---- MÚSICA (só leitura)
                TextoMenu {
                    id: secMus
                    visible: mn.secao === "musica"
                    width: parent.width
                    blocos: Tx.SECOES.musica
                }
            }
        }
    }

    Component {
        id: celCaixa
        Caixa {
            id: cc
            clicavel: false; sels: [".cel-caixa"]; texto: ""
            width: parent ? parent.width : 0
            readonly property real vao: st.gap
            height: pad[0] + Math.max(qr.height, info.height) + pad[2] + 2 * bw
            // .cel-qr img: 140 x 140 com padding 6 em fundo branco (box-sizing: a imagem fica com 128)
            Rectangle {
                id: qr
                readonly property var s: T.estilo([".cel-qr img"], false)
                x: cc.pad[3] + cc.bw; anchors.verticalCenter: parent.verticalCenter
                width: s.width; height: s.height; radius: s["border-radius"]; color: "white"
                visible: mn.rede.qr !== ""
                Image {
                    x: qr.s.padding[3]; y: qr.s.padding[0]
                    width: qr.width - qr.s.padding[1] - qr.s.padding[3]; height: qr.height - qr.s.padding[0] - qr.s.padding[2]
                    source: mn.rede.qr; smooth: false; fillMode: Image.Stretch
                }
            }
            Caixa {   // sem QR: o traço (.cel-semqr)
                visible: mn.rede.qr === ""; clicavel: false; sels: [".cel-semqr"]; texto: "—"
                x: cc.pad[3] + cc.bw; anchors.verticalCenter: parent.verticalCenter
            }
            Column {
                id: info
                x: (qr.visible ? qr.x + qr.width : cc.pad[3] + cc.bw) + cc.vao
                width: cc.width - x - cc.pad[1] - cc.bw
                anchors.verticalCenter: parent.verticalCenter
                Caixa { clicavel: false; alinhar: Qt.AlignLeft; sels: [".campo-lbl"]; texto: "Endereço para abrir no celular" }
                Item { width: 1; height: T.estilo([".campo-lbl"], false)["margin-bottom"] }
                // .cel-url: mono 14 dourado, quebra em qualquer letra (word-break: break-all)
                Rectangle {
                    id: urlCx
                    readonly property var s: T.estilo([".cel-url"], false)
                    width: info.width; height: s.padding[0] + urlTx.height + s.padding[2]
                    radius: s["border-radius"]; color: s.background
                    Letra {
                        id: urlTx
                        x: urlCx.s.padding[3]; y: urlCx.s.padding[0]; width: urlCx.width - urlCx.s.padding[1] - urlCx.s.padding[3]
                        fonte: typeof fonteMono === "undefined" ? "monospace" : fonteMono
                        quebra: Text.WrapAnywhere
                        px: urlCx.s["font-size"]; color: urlCx.s.color
                        text: mn.rede.url || "—"
                    }
                }
                Item { width: 1; height: T.estilo([".cel-url"], false)["margin-bottom"] }
                Caixa {
                    objectName: "celCopiar"
                    sels: [".big-btn"]; texto: "Copiar endereço"
                    onClicado: if (mn.rede.url) { controle.copiar(mn.rede.url); mn.copiado() }
                }
            }
        }
    }
}
