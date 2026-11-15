// O MODO APRESENTAÇÃO da 3.0.13 (#apr, "Limpo B", aprovado por ele em 12/10): ocupa a área da aba. À esquerda a COLUNA dos
// slides (busca "nº ou palavra", o alfinete que fixa, a lista com o número); recolhida, sobra o TRILHO "Mostrar slides".
// No meio o PALCO: anterior | NO TELÃO AGORA (contorno dourado) | próximo — clicar num lado projeta. Teclado como o aprTecla:
// números + Enter vão ao slide, B = tela preta, Esc sai. Medidas: o app.css (.apr*), com as unidades cqw/cqh do palco.
import QtQuick
import QtQuick.Shapes
import QtQuick.Effects
import QtQuick.Controls as QC
import QtMultimedia
import "Tema.js" as T

Item {
    id: ap
    property string nome: ""                // controle.apresAberta
    property var slides: []                 // controle.slidesApres(): [{i, url, texto, nota, cliques}]
    property int pos: 0                     // controle.slideApres
    property int passo: 0                   // controle.passoApres
    property bool preto: false              // a tela preta no ar
    property bool fixa: false               // icm_ap_fixa2: a coluna fica aberta
    property bool escondida: !fixa
    property bool porMouse: false
    property var busca: ({ achados: [], sem: "", busca: false })
    property string num: ""                 // o número sendo digitado (apr-num)
    property bool videoNoAr: true           // o telão terminou a troca: o espelho do vídeo pode voltar ao "No telão agora"
    // 11/11 11h37 (ele: "cada esmaecimento tá numa velocidade diferente (...) quem tá respeitando todos os blurs com perfeição
    // é a tela de retorno e a saída"): o "No telão agora", o próximo e o anterior esmaecem JUNTOS e no tempo do telão. A
    // imagem nova de cada um fica pronta, parada, e todas entram quando o telão começa a troca dele (controle.trocaComecou);
    // sem aviso em 1,2 s (telão fora), entram assim mesmo
    property bool aguardaTelao: false
    readonly property int msPainel: 600
    onIChanged: { aguardaTelao = true; soltaPainel.restart(); if (!escondida) listaApr.rolar(i) }     // a rolagem da lateral: ver o comentário no fim do arquivo
    onPassoChanged: { aguardaTelao = true; soltaPainel.restart() }
    property bool quadroNovo: true          // e já chegou um quadro do vídeo depois disso
    property var louvores: []               // controle.painelB().louvores: [{nome, de, ate}]
    property var gestos: []                 // controle.painelB().gestos: os slides com gestos
    // o que a faixa de baixo mostra (os mesmos estados do #painel)
    property bool projetando: false
    property bool noArTelao: false
    property bool congelado: false
    property string tamRotulo: "Padrão"
    signal projetarClique()
    signal congelar()
    signal menor()
    signal maior()
    signal padrao()
    signal procurarTelas()
    signal sair()
    signal projetar(int i)
    signal passar(int d)                    // aprPasso: +1 / -1 (o próximo clique ou slide)
    signal alternarPreto()
    signal buscar(string q)
    signal gravarFixa(bool v)

    readonly property int n: slides.length
    readonly property int i: Math.max(0, Math.min(pos, n - 1))
    readonly property int falta: n ? (slides[i] ? slides[i].cliques : 0) - passo : 0
    readonly property bool temPx: falta > 0 || i + 1 < n
    readonly property bool temAn: passo > 0 || i > 0
    function src(k) { return slides[k] ? slides[k].url : "" }
    function anim(k) { return !!(slides[k] && slides[k].animada) }
    function col(esc, mouse) { escondida = !!esc; porMouse = !esc && !!mouse }
    function escolher(k) { ap.projetar(k); if (!ap.fixa) col(true) }      // aprEscolher: projeta e a coluna recolhe
    function numLimpa() { num = ""; tNum.stop() }
    function tecla(e) {
        if (campoBusca.campo.activeFocus) {
            if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) { buscaIr(); e.accepted = true }
            else if (e.key === Qt.Key_Escape) { if (campoBusca.text) campoBusca.text = ""; else campoBusca.campo.focus = false; e.accepted = true }
            return
        }
        if (e.modifiers & (Qt.ControlModifier | Qt.AltModifier)) return
        if (e.text >= "0" && e.text <= "9" && e.text.length === 1) { num = (num + e.text).slice(-3); tNum.restart(); e.accepted = true; return }
        if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) {
            if (num) { var k = parseInt(num, 10); numLimpa(); if (k >= 1 && k <= n) ap.projetar(k - 1) } else ap.passar(1)
            e.accepted = true; return
        }
        if (e.key === Qt.Key_Backspace && num) { num = num.slice(0, -1); tNum.restart(); e.accepted = true; return }
        if (e.key === Qt.Key_B) { ap.alternarPreto(); e.accepted = true; return }
    }
    function buscaIr() {
        var a = busca.achados || []; if (!a.length) return
        var depois = a.filter(function (k) { return k > ap.pos }), alvo = depois.length ? depois[0] : a[0]
        if (/^\d+$/.test(campoBusca.text.trim())) campoBusca.text = ""
        campoBusca.campo.focus = false
        escolher(alvo)
    }
    Timer { id: tNum; interval: 4000; onTriggered: ap.num = "" }
    Timer { id: soltaPainel; interval: 1200; onTriggered: ap.aguardaTelao = false }
    Connections { target: typeof controle !== "undefined" ? controle : null; ignoreUnknownSignals: true
                  function onTrocaComecou() { ap.aguardaTelao = false; soltaPainel.stop() } }

    // .apr{background:radial-gradient(ellipse at 50% 50%, #18305a 0%, #0b1526 70%)}: a elipse do CSS vai até os cantos
    // (raios = metade de cada lado x raiz de 2). O degradê do Qt é redondo: desenho num quadrado e achato a altura.
    Rectangle { anchors.fill: parent; color: "#0b1526" }
    Shape {
        width: ap.width; height: ap.width
        transform: Scale { yScale: ap.height / Math.max(1, ap.width) }
        ShapePath {
            strokeColor: "transparent"
            fillGradient: RadialGradient {
                centerX: ap.width / 2; centerY: ap.width / 2; focalX: centerX; focalY: centerY
                centerRadius: ap.width / 2 * Math.SQRT2
                GradientStop { position: 0; color: "#18305a" }
                GradientStop { position: 0.7; color: "#0b1526" }
            }
            PathRectangle { width: ap.width; height: ap.width }
        }
    }

    // ---- o PALCO do "Painel B" (body.pb-on #apr .apr-palco, a geometria da HD 18/10): uma grade de 2 colunas, 60% e 35%
    // (vão 4%), áreas "g p" / "g a" / "c a": o NO TELÃO grande à esquerda (g), o PRÓXIMO à direita (p), o ANTERIOR pequeno
    // embaixo dele (a, 60% da coluna, margem 8) e os LOUVORES da apresentação embaixo do grande (c). Centrado na vertical,
    // acima da faixa de 64 px.
    Item {
        id: palco
        x: ap.escondida ? 46 : 236; width: ap.width - x; height: ap.height - 64
        Behavior on x { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
        readonly property real wc: width - 24                       // o padding 0 12
        readonly property real colG: wc * 0.60
        readonly property real colP: wc * 0.35
        readonly property real vao: wc * 0.04
        readonly property real x0: 12 + (wc - colG - colP - vao) / 2  // justify-content:center
        readonly property real hg: colG * 9 / 16
        readonly property real hp: colP * 9 / 16
        readonly property real wa: colP * 0.6
        readonly property real ha: wa * 9 / 16
        readonly property real r1: hp
        readonly property real r2: Math.max(0, hg - r1 - 26)
        readonly property real r3: Math.max(chips.height, 8 + ha - r2 - 26)
        readonly property real alto: r1 + 26 + r2 + 26 + r3
        readonly property real y0: Math.max(0, (height - alto) / 2)

        // NO TELÃO AGORA (g)
        Item {
            x: palco.x0; y: palco.y0; width: palco.colG; height: palco.hg
            Letra { anchors.horizontalCenter: parent.horizontalCenter; y: -22; px: 12.5; lsCss: 0.8; maiusculas: true; weight: 600; color: T.V.ouro
                    text: "No telão agora · Slide " + (ap.i + 1) + " de " + ap.n + (ap.falta > 0 ? " · falta" + (ap.falta > 1 ? "m " + ap.falta + " animações" : " 1 animação") : "") }
            Rectangle { anchors.fill: parent; anchors.margins: -6; radius: 16; color: "transparent"; border.width: 3; border.color: T.V.ouro }
            RectShadowCSS { anchors.fill: parent; radius: 10; sombra: ({ x: 0, y: 18, blur: 60, spread: 0, cor: "#cc000000", inset: false }) }
            Rectangle { anchors.fill: parent; radius: 10; color: "black" }
            // o "No telão agora" grande ANIMA (regra dele 02/11: o operador vê o MESMO quadro do telão); largura 1280 =
            // os quadros cheios do telão (QuadrosAnim: >= 90% da largura do telão), sem encolher nem decodificar de novo.
            // Parados (09/11, "animação em todas as telas não tem necessidade"): a grade, o anterior/próximo e o canto.
            ImgSlide { anchors.fill: parent; fonte: ap.src(ap.i); animada: ap.anim(ap.i); largura: 1280; esmaece: ap.msPainel; segura: ap.aguardaTelao }
            // o slide em VÍDEO (o .mp4 leve, 09/11): o MESMO quadro que o telão decodificou (ligar_espelhos), por cima do parado
            VideoOutput { id: espG; objectName: "espelhoGrande"; anchors.fill: parent; fillMode: VideoOutput.PreserveAspectFit
                          visible: !!(ap.slides[ap.i] && ap.slides[ap.i].video)
                          opacity: ap.videoNoAr && ap.quadroNovo ? 1 : 0
                          Behavior on opacity { enabled: ap.videoNoAr; NumberAnimation { duration: 250; easing.type: Easing.InOutQuad } } }
            // 11/11 (o esmaecimento no "telão agora"; ele no Vaio: o operador "via só a travada, tela preta e a troca").
            // Filmado no Vaio: o espelho do vídeo ficava PRETO entre o vídeo velho parar e o 1º quadro do novo, por cima da
            // imagem (o brilho da área caía de 146 para 56 no meio da troca). Agora, na troca de slide: o espelho do vídeo
            // some na hora, a imagem parada esmaece da velha para a nova (ImgSlide.esmaece) e o vídeo só volta quando o
            // TELÃO terminou a troca E já chegou um quadro do vídeo novo ("pare o MP4, jogue o JPEG, transite").
            Connections { target: ap; function onIChanged() { ap.videoNoAr = false; ap.quadroNovo = false; voltaVideo.restart() } }
            Connections { target: espG.videoSink; function onVideoFrameChanged() { if (ap.videoNoAr) ap.quadroNovo = true } }
            Connections { target: typeof controle !== "undefined" ? controle : null; ignoreUnknownSignals: true
                          function onTrocaTerminou() { ap.videoNoAr = true; voltaVideo.stop() } }
            Timer { id: voltaVideo; interval: 2500; onTriggered: ap.videoNoAr = true }      // sem telão que avise: volta assim mesmo
            CantosRedondos { anchors.fill: parent; raio: 10; cor: "#132a4e"; corBaixo: "#132a4e" }
            SeloGestos { visible: ap.gestos.indexOf(ap.i) >= 0 }
            Rectangle {   // .apr-preto: "Tela preta no telão"
                visible: ap.preto; anchors.fill: parent; radius: 10; color: Qt.rgba(0, 0, 0, 0.86)
                Letra { anchors.centerIn: parent; text: "Tela preta no telão"; px: 17; weight: 700; lsCss: 0.3; color: T.V.ouro }
            }
        }
        // PRÓXIMO (p): contorno claro de 2 px
        LadoApr {
            x: palco.x0 + palco.colG + palco.vao; y: palco.y0; width: palco.colP
            esmaece: ap.msPainel; segura: ap.aguardaTelao
            ant: false; vazio: false; fim: !ap.temPx; fonte: ap.temPx ? ap.src(ap.falta > 0 ? ap.i : ap.i + 1) : ""
            animada: ap.temPx && ap.anim(ap.falta > 0 ? ap.i : ap.i + 1)
            tag: ap.falta > 0 ? "próximo: animação" : "próximo"
            pb: true; gestos: ap.temPx && ap.falta <= 0 && ap.gestos.indexOf(ap.i + 1) >= 0
            onClicado: if (!fim) ap.passar(1)
        }
        // ANTERIOR (a): 60% da coluna, centrado, 8 abaixo do começo da área
        LadoApr {
            x: palco.x0 + palco.colG + palco.vao + (palco.colP - palco.wa) / 2; y: palco.y0 + palco.r1 + 26 + 8; width: palco.wa
            esmaece: ap.msPainel; segura: ap.aguardaTelao
            ant: true; vazio: !ap.temAn; fonte: ap.temAn ? ap.src(ap.passo > 0 ? ap.i : ap.i - 1) : ""
            animada: ap.temAn && ap.anim(ap.passo > 0 ? ap.i : ap.i - 1)
            tag: ap.passo > 0 ? "anterior: animação" : "anterior"
            pb: true
            onClicado: if (!vazio) ap.passar(-1)
        }
        // os LOUVORES da apresentação (#pb-louvores, área c): clique projeta o começo daquele louvor
        Flow {
            id: chips
            x: palco.x0; y: palco.y0 + palco.r1 + 26 + palco.r2 + 26; width: palco.colG
            spacing: 10
            Repeater {
                model: ap.louvores
                Caixa {
                    readonly property int iAgora: { for (var k = 0; k < ap.louvores.length; k++) if (ap.i >= ap.louvores[k].de && ap.i <= ap.louvores[k].ate) return k; return -1 }
                    readonly property int iProx: { for (var k = 0; k < ap.louvores.length; k++) if (ap.louvores[k].de > ap.i) return k; return -1 }
                    sels: ["#pb-louvores .lv"]
                    estados: (index === iAgora ? ["#pb-louvores .lv.agora"] : []).concat(index === iProx ? ["#pb-louvores .lv.prox"] : [])
                             .concat(iAgora >= 0 && index < iAgora ? ["#pb-louvores .lv.foi"] : [])
                    texto: modelData.nome
                    rotuloAntes: index === iAgora ? "no telão" : (index === iProx ? "próximo louvor" : "")
                    onClicado: ap.projetar(modelData.de)
                }
            }
        }
    }

    // ---- a FAIXA de baixo (#pb-faixa, 64 px): os MESMOS ‹ Projetar › e barra do painel, e "No telão: Slide i/n"
    Rectangle {
        id: faixa
        x: palco.x; width: ap.width - x; height: 64; y: ap.height - 64; z: 5
        color: T.V.painel
        Rectangle { width: parent.width; height: 1; color: T.V.borda }
        // 3.0.10: a faixa encolhe por etapas (apertada < 760, muito < 560) e nenhum botão some
        readonly property bool apertada: width < 760
        readonly property bool muito: width < 560
        // (o padding 0 18 e o vão 12 da "body.pb-on #pb-faixa" vencem os da "#pb-faixa.apertada", que é menos específica:
        // apertada muda só o ‹ Projetar › e o Congelar; medido no Edge: nav2 em x+18, 250 de largura, vão 12)
        Row {
            id: linhaFaixa
            x: 18; anchors.verticalCenter: parent.verticalCenter
            spacing: 12
            readonly property real livre: faixa.width - 2 * x - barraF.width - 2 * spacing - (agoraF.visible ? agoraF.implicitTextWidth : 0)
            Nav2 {
                id: navF
                width: Math.min(faixa.muito ? 240 : (faixa.apertada ? 250 : 320), Math.max(120, linhaFaixa.livre))
                larguraNav: faixa.muito ? 40 : 46
                projetando: ap.projetando; noAr: ap.noArTelao
                anchors.verticalCenter: parent.verticalCenter
                onProjetar: ap.projetarClique(); onAnterior: ap.passar(-1); onProximo: ap.passar(1)
            }
            // "No telão: Slide i/n" (.pb-agora 12 px; o <b> com peso 600 e ouro: #pb-faixa .pb-agora b)
            Row {
                id: agoraF
                visible: !faixa.muito
                readonly property real implicitTextWidth: width
                anchors.verticalCenter: parent.verticalCenter
                Letra { px: 12; weight: 600; color: T.V.ouro; text: "No telão:" }
                Letra { px: 12; color: "#b9c6dc"; text: " Slide " + (ap.i + 1) + "/" + ap.n }
            }
            BarraFerr {
                id: barraF
                natural: true; soIcone: faixa.apertada
                anchors.verticalCenter: parent.verticalCenter
                congelado: ap.congelado; tamRotulo: ap.tamRotulo
                onCongelar: ap.congelar(); onMenor: ap.menor(); onMaior: ap.maior(); onPadrao: ap.padrao(); onProcurarTelas: ap.procurarTelas()
            }
        }
    }

    // ---- o TRILHO (.apr-trilho): só com a coluna recolhida; passar o mouse (180 ms) ou clicar abre
    Rectangle {
        id: trilho
        visible: ap.escondida
        width: 46; height: ap.height; z: 9
        color: T.V.painel
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: T.V.borda }
        Column {
            anchors.horizontalCenter: parent.horizontalCenter; y: 14; spacing: 12
            Rectangle {
                width: 32; height: 32; radius: 8; anchors.horizontalCenter: parent.horizontalCenter
                color: maTrilho.containsMouse ? T.V.hover : T.V.painel2
                border.width: 1; border.color: maTrilho.containsMouse ? T.V.ouro : T.V.borda
                Ico { anchors.centerIn: parent; nome: "painelAbre"; tam: 17; cor: maTrilho.containsMouse ? T.V.ouro : "#dfe8f7" }
            }
            Letra { anchors.horizontalCenter: parent.horizontalCenter; rotation: -90; transformOrigin: Item.Center
                    width: implicitTextWidth; px: 13; weight: 600; lsCss: 0.4; color: "#dfe8f7"; text: "Mostrar slides"
                    // writing-mode vertical: o texto de pé, lido de baixo para cima
                    height: implicitTextWidth }
        }
        MouseArea {
            id: maTrilho; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onEntered: tAbrir.restart(); onExited: tAbrir.stop()
            onClicked: { tAbrir.stop(); ap.col(false, !ap.fixa) }
            Timer { id: tAbrir; interval: 180; onTriggered: if (ap.escondida) ap.col(false, true) }
        }
    }

    // ---- a COLUNA (.apr-col): 236 px; recolhida sai para a esquerda (translateX(-102%))
    Rectangle {
        id: coluna
        width: 236; height: ap.height; z: 10
        x: ap.escondida ? -width * 1.02 : 0
        Behavior on x { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
        color: T.V.painel
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: T.V.borda }
        // 09/11 (ele no Vaio: "a barra lateral é quase impossível de fixar, ela some quando eu chego com o mouse perto"): o
        // onExited do MouseArea disparava ao passar POR CIMA de um botão de dentro (o alfinete rouba o hover), e a coluna
        // fugia na hora de fixar. Agora: HoverHandler (os filhos não roubam) e 700 ms de folga antes de recolher
        MouseArea { anchors.fill: parent }                 // o clique no vazio da coluna não vaza para o slide de trás
        HoverHandler { id: hvCol; onHoveredChanged: if (hovered) tFechar.stop(); else if (ap.porMouse && !ap.fixa) tFechar.restart() }
        Timer { id: tFechar; interval: 700; onTriggered: if (ap.porMouse && !ap.fixa && !hvCol.hovered) ap.col(true) }
        Column {
            id: topo
            x: 10; y: 10; width: coluna.width - 20 - 1; spacing: 9
            // "‹ Apresentações" (.apr-lk)
            Caixa { x: -3; sels: [".apr-lk"]; icone: "voltar"; texto: "Apresentações"; onClicado: ap.sair() }
            // o nome + o alfinete (.apr-l1)
            Item {
                width: parent.width; height: Math.max(nomeAp.implicitHeight, 30)
                Letra { id: nomeAp; width: parent.width - 30 - 6; quebra: Text.WrapAnywhere; px: 13; weight: 600; linha: 1.25; color: "#eaf0fb"
                        text: ap.nome; anchors.verticalCenter: parent.verticalCenter }
                Rectangle {
                    id: alfinete
                    width: 30; height: 30; radius: 8; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                    color: maAlf.containsMouse && !ap.fixa ? "#10ffffff" : "transparent"
                    Ico { anchors.centerIn: parent; nome: "alfinete"; tam: 17; cor: ap.fixa ? T.V.ouro : (maAlf.containsMouse ? "#dfe8f7" : "#8fa2c2") }
                    MouseArea { id: maAlf; anchors.fill: parent; anchors.margins: -7; hoverEnabled: true; cursorShape: Qt.PointingHandCursor   // alvo 44 px (09/11)
                                onClicked: { ap.fixa = !ap.fixa; ap.gravarFixa(ap.fixa); if (ap.fixa) ap.col(false); else ap.porMouse = true } }
                }
            }
            // a busca "nº ou palavra" (.apr-achar)
            Rectangle {
                width: parent.width; height: 12 + 17 + 2
                radius: 8; color: "#0a1526"; border.width: 1; border.color: campoBusca.campo.activeFocus ? T.V.ouro : T.V.borda
                Ico { id: lupa; x: 9; anchors.verticalCenter: parent.verticalCenter; nome: "busca"; tam: 14; cor: "#7f90ad" }
                Entrada {
                    id: campoBusca; objectName: "buscaApr"
                    x: lupa.x + lupa.width + 6; width: parent.width - x - 9; anchors.verticalCenter: parent.verticalCenter
                    navegador: false; sels: [".apr-achar input"]; placeholder: "nº ou palavra"; corPlaceholder: "#7f90ad"
                    color: "transparent"; border.width: 0
                    onTextChanged: ap.buscar(text)
                }
            }
        }
        Rectangle { y: topo.y + topo.height + 9; width: coluna.width - 1; height: 1; color: T.V.borda }
        // a lista das miniaturas (.apr-lista: padding 10 6, vão 9)
        ListView {
            id: listaApr; objectName: "listaApr"
            y: topo.y + topo.height + 10; width: coluna.width - 1; height: coluna.height - y
            clip: true; spacing: 9; topMargin: 10; bottomMargin: 10; boundsBehavior: Flickable.StopAtBounds
            model: ap.slides; reuseItems: true
            // B6 (relato dele 07/11 21h16: "as miniaturas da barra lateral não carregam todas"): sem isto só nascia a
            // miniatura que entrava na tela, e no Vaio ela chegava atrasada. Agora todas nascem (e decodificam no fundo) ao
            // abrir, como o <img> da 3.0.13; a ANIMAÇÃO só anda nas que estão à vista (o navegador também pausa as de fora)
            cacheBuffer: Math.max(0, (ap.slides || []).length * 120)
            // 11/11 (ele: "tem que colocar a barra lateral de scroll (...) que eu não tô conseguindo achar nada aqui")
            QC.ScrollBar.vertical: QC.ScrollBar {
                policy: QC.ScrollBar.AlwaysOn; width: 9; minimumSize: 0.08
                contentItem: Rectangle { radius: 4; color: parent.pressed ? T.V.ouro : (parent.hovered ? "#9fb0cc" : "#5a6f93") }
                background: Rectangle { color: "#0a1526" }
            }
            header: Letra { visible: !!ap.busca.sem; x: 12; width: listaApr.width - 24; height: visible ? implicitHeight + 6 : 0
                            px: 12; linha: 1.35; color: "#9fb0cc"; quebra: Text.WordWrap; text: ap.busca.sem || "" }
            delegate: Item {
                id: th
                readonly property bool on: index === ap.i
                readonly property bool achou: (ap.busca.achados || []).indexOf(index) >= 0
                readonly property bool fora: ap.busca.busca && !achou && !/^\d+$/.test(campoBusca.text.trim())
                width: listaApr.width; height: im.height
                opacity: fora ? 0.28 : 1
                Behavior on opacity { NumberAnimation { duration: 150 } }
                Letra { x: 6; y: 2; largura: 20; alinhamento: Text.AlignRight; px: 11; weight: th.on ? 700 : 400
                        color: th.on ? T.V.ouro : "#9fb0cc"; text: String(index + 1) }
                Rectangle {
                    id: im
                    readonly property bool sobre: maTh.containsMouse
                    // 14/11 (ele no Vaio 12/11: "uma bordinha cinzinha bonitinha nas áreas das laterais, dos slides"): a miniatura que
                    // não é a atual ganha o contorno claro do PRÓXIMO (#e6eefb), mais suave (30%); a atual segue em ouro
                    readonly property color cinza: "#4de6eefb"
                    x: 6 + 20 + 6 + (sobre ? 0 : 8); width: sobre ? 194 : 172; height: (width - 4) * 9 / 16 + 4
                    Behavior on width { NumberAnimation { duration: 150 } }
                    Behavior on x { NumberAnimation { duration: 150 } }
                    radius: 10; color: "transparent"        // 11/11: cantos arredondados que se VEEM (eram 5 e 3: quadrado a olho)
                    border.width: 2; border.color: sobre ? "white" : (th.on ? T.V.ouro : im.cinza)
                    // 11/11 (ele: "a SOMBRA é quadrada"): a transparência dos que já passaram valia para a miniatura INTEIRA, e
                    // a tampa dos cantos, meio transparente, deixava o canto quadrado da imagem aparecer por baixo. Agora só a
                    // IMAGEM clareia/escurece (sobre o preto de trás); a tampa e a moldura ficam inteiras. E os de trás
                    // ficam em 72% ("estão escuros demais"; eram 50%)
                    RectShadowCSS { visible: im.sobre || th.achou; anchors.fill: parent; radius: 10
                                    sombra: th.achou ? ({ x: 0, y: 0, blur: 0, spread: 3, cor: T.V.ouro, inset: false }) : ({ x: 0, y: 8, blur: 24, spread: 0, cor: "#aa000000", inset: false }) }
                    Rectangle { x: 2; y: 2; width: parent.width - 4; height: parent.height - 4; radius: 8; color: "black"
                        ImgSlide { anchors.fill: parent; fonte: modelData.url; animada: false; largura: 388     // parada (09/11)
                                   opacity: !im.sobre && index < ap.i ? 0.72 : 1
                                   tocando: th.y + th.height > listaApr.contentY && th.y < listaApr.contentY + listaApr.height } }
                    // 11/11 (ele: "cantinhos arredondados em cada quadradinho da prévia do slide"): os 4 cantos da imagem são
                    // cobertos na cor da coluna (fundo liso: fica exato, sem camada nem máscara, barato no Vaio) e a moldura
                    // (raio 10 fora, 8 dentro) vai por cima
                    CantosRedondos { x: 2; y: 2; width: parent.width - 4; height: parent.height - 4; raio: 8; cor: T.V.painel; corBaixo: T.V.painel }
                    Rectangle { anchors.fill: parent; radius: 10; color: "transparent"; border.width: 2
                                border.color: im.sobre ? "white" : (th.on ? T.V.ouro : im.cinza) }
                    // o aviso do mouse, no estilo do "clique para projetar" do PRÓXIMO (11/11, pedido dele): véu azul-escuro,
                    // contorno e letra dourados, no meio, SEM a setinha
                    Rectangle {
                        visible: im.sobre; anchors.fill: parent; radius: 10; color: "#b00b1526"; border.width: 2; border.color: T.V.ouro
                        Letra { anchors.centerIn: parent; px: 12; weight: 600; color: T.V.ouro; linha: 1.2
                                quebra: Text.WordWrap; alinhamento: Text.AlignHCenter; width: implicitTextWidth; text: "clique para\nprojetar" }
                    }
                    MouseArea { id: maTh; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: ap.escolher(index) }
                }
            }
            // 11/11 11h37 (ele: a lateral "vai dando uns trancos" ao acompanhar o slide): o pulo seco virou deslize. A lista
            // calcula para onde iria (positionViewAtIndex), volta e desliza até lá em 300 ms
            function rolar(k) {
                desliza.stop()
                // (11h43, ele: "manter sempre o slide atual em evidência, praticamente no meio, um pouquinho para cima"; com o
                // "só o bastante para aparecer" ele ia parar lá embaixo, na beirada.) O atual fica no meio, 10% acima do centro;
                // no começo e no fim da lista, até onde a lista deixa
                var de = contentY; positionViewAtIndex(k, ListView.Center)
                var para = Math.max(originY - topMargin, Math.min(contentY + height * 0.10, originY + contentHeight + bottomMargin - height))
                if (Math.abs(para - de) < 1) return
                contentY = de; desliza.from = de; desliza.to = para; desliza.restart()
            }
            NumberAnimation { id: desliza; target: listaApr; property: "contentY"; duration: 300; easing.type: Easing.InOutQuad }
        }
    }
    // 13/11: era onPosChanged, que dispara ANTES de o "i" (que depende de pos) se atualizar: a lista rolava para o slide
    // ANTERIOR. Medido (mede_lateral_apres.py): indo, o atual parava em 58% da lista; voltando, em 22% (ele 12/11: "pega mais
    // ou menos onde eu parei (...) quero uma espécie de um meio, mais padronizado"). Agora sempre 40%, ida e volta.
    onEscondidaChanged: if (!escondida) listaApr.rolar(i)

    // ---- o número digitado (.apr-num)
    Rectangle {
        visible: ap.num !== ""; z: 20
        anchors.centerIn: parent
        width: Math.max(numBig.implicitTextWidth, numSm.implicitTextWidth) + 52; height: 14 + 44 + numSm.alturaLinha + 14
        radius: 14; color: "#ee0b1526"; border.width: 1; border.color: T.V.ouro
        RectShadowCSS { z: -1; anchors.fill: parent; radius: 14; sombra: ({ x: 0, y: 10, blur: 40, spread: 0, cor: "#000000", inset: false }) }
        Column {
            anchors.centerIn: parent
            Letra { id: numBig; anchors.horizontalCenter: parent.horizontalCenter; px: 44; weight: 700; linha: 1; color: T.V.ouro; text: ap.num }
            Letra { id: numSm; anchors.horizontalCenter: parent.horizontalCenter; px: 12.5; color: "#c8d3e6"
                    text: { var k = parseInt(ap.num, 10); return k >= 1 && k <= ap.n ? "de " + ap.n : "são " + ap.n + " slides" } }
        }
    }
}
