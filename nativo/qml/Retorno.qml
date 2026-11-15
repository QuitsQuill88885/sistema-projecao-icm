// A TV DE RETORNO (Sistema Nativo, 04/11/2026): o retorno.html da 3.0.12 desenhado aqui dentro, sem navegador.
// Para a irmã que puxa os gestos: AGORA (borda dourada) e A SEGUIR (tracejado verde) lado a lado, no cartão branco
// das figuras com a legenda embaixo. Na tela de espera, o relógio. No resto (Bíblia, aviso, louvor sem gesto), o
// espelho do telão. Medidas copiadas do retorno.html (vh = 1% da altura da TV, vw = 1% da largura).
// O cartão só é refeito quando o gesto MUDA (a chave "k"): o mesmo gesto não pisca, e as figuras são arquivos locais
// lidos na hora, então o cartão nunca fica vazio na troca (o defeito do Vaio de 24/10 não tem como acontecer aqui).
import QtQuick
import QtQuick.Shapes
import "Icones.js" as Ic

Item {
    id: ret
    property real vh: height / 100
    property real vw: width / 100
    property var dados: ({ modo: "relogio", oque: "" })
    property var cAgora: null
    property var cSeg: null
    property string rAgora: "Agora"
    property string rSeg: "A seguir"
    property var pSeg: null             // o próximo louvor, embaixo da prévia do slide ({nome, em})
    readonly property bool gestos: dados.modo === "gestos"
    readonly property string ui: "Outfit"     // a letra do Sistema, que vem no pacote (a "Segoe UI" do retorno.html falta no modo de fotos)

    function atualizar() {
        var r = controle.retorno()
        dados = r
        if (r.modo !== "gestos") return
        rAgora = r.agora.rot
        if (!cAgora || cAgora.k !== r.agora.card.k) cAgora = r.agora.card
        rSeg = r.seguir ? r.seguir.rot : ""
        var px = r.seguir && r.seguir.prox ? r.seguir.prox : null
        if (!px) pSeg = null
        else if (!pSeg || pSeg.nome !== px.nome || pSeg.em !== px.em) pSeg = px
        var s = r.seguir ? r.seguir.card : null
        if (!s) cSeg = null
        else if (!cSeg || cSeg.k !== s.k) cSeg = s
    }
    function mostrar(t) { espelho.mostrar(t) }
    // escondida não trabalha (07/11): a cópia que mora no telão (o "Trocar" das duas telas) só redesenha quando aparece;
    // ao aparecer, quem a chama é o onVisibleChanged de quem a usa
    Connections { target: controle; function onRetornoMudou() { if (ret.visible) ret.atualizar() } }
    Component.onCompleted: atualizar()

    // o fundo do Sistema (o azul do painel)
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#10203a" }
            GradientStop { position: 0.45; color: "#12223d" }
            GradientStop { position: 1.0; color: "#0b1526" }
        }
    }

    // ---- o espelho do telão (o mesmo Palco, sem tocar vídeo: o telão é que toca)
    Palco { id: espelho; objectName: "espelhoRetorno"; previa: true; anchors.fill: parent; visible: dados.modo === "espelho" }

    // ---- o relógio da tela de espera
    Column {
        anchors.centerIn: parent
        visible: dados.modo === "relogio"
        spacing: vh
        Text {
            id: rData; anchors.horizontalCenter: parent.horizontalCenter
            font.family: "Outfit"; font.weight: Font.Medium; font.pixelSize: 3.6 * vh; font.letterSpacing: 3.6 * vh * 0.42
            color: "#f5d76e"
        }
        Text {
            id: rHora; anchors.horizontalCenter: parent.horizontalCenter
            font.family: "Bebas Neue"; font.pixelSize: 30 * vh; color: "white"
        }
    }
    property var dias: ["DOMINGO", "SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "SÁBADO"]
    property var meses: ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
    function hora() {
        var d = new Date()
        var hm = ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2)
        rData.text = dias[d.getDay()] + " · " + d.getDate() + " DE " + meses[d.getMonth()] + " DE " + d.getFullYear()
        rHora.text = hm; topoHora.text = hm
    }
    // um toque por minuto (acorda no virar do minuto, não a cada segundo)
    Timer {
        id: tic; running: true; repeat: false
        interval: 1000
        onTriggered: { ret.hora(); var d = new Date(); interval = (60 - d.getSeconds()) * 1000 + 50; start() }
        Component.onCompleted: { ret.hora(); var d = new Date(); interval = (60 - d.getSeconds()) * 1000 + 50; start() }
    }

    // ---- o cabeçalho igual ao do painel (some no espelho, que é a tela inteira do telão)
    Rectangle {
        id: topo
        visible: dados.modo !== "espelho"
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: (gestos ? 4.6 : 7) * vh
        gradient: Gradient { GradientStop { position: 0; color: "#12294a" } GradientStop { position: 1; color: "#0d1f3a" } }
        Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 0.35 * vh; color: "#a31a1a" }
        Row {
            anchors { left: parent.left; leftMargin: 2 * vw; verticalCenter: parent.verticalCenter }
            spacing: 1.4 * vw
            Text { text: "ICM Iperó · Retorno"; color: "white"; font.bold: true; font.family: ret.ui; font.pixelSize: (gestos ? 2.2 : 2.8) * vh }
            Text {
                text: dados.oque || ""; color: "#9db3d6"; font.family: ret.ui; font.pixelSize: (gestos ? 2.2 : 2.8) * vh
                width: ret.width * 0.6; elide: Text.ElideRight
            }
        }
        Text {
            id: topoHora
            anchors { right: parent.right; rightMargin: 2 * vw; verticalCenter: parent.verticalCenter }
            color: "#eaf0fb"; font.family: "Outfit"; font.pixelSize: (gestos ? 2.2 : 2.8) * vh
        }
    }

    // ---- os gestos: AGORA e A SEGUIR, lado a lado
    Item {
        id: area
        visible: gestos
        anchors { fill: parent; topMargin: 4.6 * vh + 1.4 * vh; bottomMargin: 1.6 * vh; leftMargin: 1.6 * vw; rightMargin: 1.6 * vw }
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            height: parent.height
            spacing: 1.4 * vw
            Coluna {
                id: colAgora; rotulo: ret.rAgora; cartao: ret.cAgora; agora: true
                width: ret.cSeg ? area.width * 0.57 : area.width * 0.96; height: parent.height
            }
            Coluna {
                id: colSeg; rotulo: ret.rSeg; cartao: ret.cSeg; agora: false; visible: ret.cSeg !== null; prox: ret.pSeg
                width: area.width * 0.406; height: parent.height
            }
        }
    }

    // uma coluna: o rótulo em ouro e o cartão
    component Coluna: Item {
        id: col
        property string rotulo
        property var cartao
        property bool agora
        property var prox: null
        Text {
            id: rot
            width: parent.width; text: col.rotulo; color: "#f5d76e"; font.family: ret.ui
            font.pixelSize: 3 * ret.vh; font.weight: Font.ExtraBold; font.letterSpacing: 3 * ret.vh * 0.08
            font.capitalization: Font.AllUppercase; elide: Text.ElideRight; leftPadding: 0.4 * ret.vw
            fontSizeMode: Text.HorizontalFit; minimumPixelSize: 1.6 * ret.vh
        }
        Item {
            id: caixa
            // 13/11 (ele, vendo no Vaio: "o blur ali e nada e a mesma coisa ... ficasse menor, so o verdinho, borda
            // arredondada"): o cartao do SLIDE tem o tamanho do slide (deitado), colado no rotulo; nada de borrao
            readonly property bool deitado: !!col.cartao && col.cartao.tipo === "slide"
            readonly property real cheia: col.height - rot.height - 0.8 * ret.vh
            anchors { left: parent.left; right: parent.right; top: rot.bottom; topMargin: 0.8 * ret.vh }
            height: deitado ? Math.min(cheia, width * cartaoItem.proporcao) : cheia
            // AGORA: o anel dourado cheio ("no ar agora"); A SEGUIR: o tracejado verde, um pouco apagado
            Rectangle {
                visible: col.agora
                anchors.fill: parent; anchors.margins: -0.45 * ret.vh
                radius: 1.8 * ret.vh + 0.45 * ret.vh; color: "#f5d76e"
            }
            Shape {
                visible: !col.agora
                anchors.fill: parent; anchors.margins: -0.95 * ret.vh
                ShapePath {
                    // 13/11 (ele: "era um picotado mais suave, mais próximo, um traço mais fino"): na 3.0.x o traço ia a 82%
                    // com o cartão (.seguir .gcard { opacity:.82; outline:.45vh dashed }); o Qt desenhava cada traço com a
                    // ponta QUADRADA (meio traço a mais de cada lado), o que o deixava grosso e duro. Ponta reta, mais fino,
                    // traços mais curtos e mais juntos, e os 82% de volta só no traço (o cartão segue branco)
                    strokeColor: "#d12e8b57"; strokeWidth: 0.34 * ret.vh; fillColor: "transparent"
                    strokeStyle: ShapePath.DashLine; dashPattern: [2.4, 1.7]; capStyle: ShapePath.FlatCap
                    PathRectangle { x: 0; y: 0; width: caixa.width + 1.9 * ret.vh; height: caixa.height + 1.9 * ret.vh
                                    radius: 1.8 * ret.vh + 0.95 * ret.vh }
                }
            }
            Cartao { id: cartaoItem; anchors.fill: parent; dados: col.cartao; seguir: !col.agora; noAr: col.agora }
            // AGORA com o slide: o canto RETO da imagem passava por fora do arco dourado ("as quininhas", ele 13/11).
            // O cartao recorta os cantos na cor do fundo e o aro dourado e redesenhado POR CIMA, inteiro
            Rectangle {
                visible: col.agora && caixa.deitado
                anchors.fill: parent; anchors.margins: -0.45 * ret.vh
                radius: 1.8 * ret.vh + 0.45 * ret.vh; color: "transparent"
                border.color: "#f5d76e"; border.width: 0.45 * ret.vh + 1
            }
        }
        // 13/11: o balão do PRÓXIMO LOUVOR, no espaço que sobra embaixo da prévia do slide (o esboço B que ele escolheu:
        // "aprimora esse balãozinho"). O círculo quase preto com a nota em ouro, o nome grande e a pílula verde de
        // quanto falta (as cores do modo duas telas). Só texto: não abre imagem nenhuma na troca.
        Rectangle {
            id: balao
            readonly property real sobra: col.height - rot.height - 0.8 * ret.vh - caixa.height - 3.4 * ret.vh
            visible: !col.agora && caixa.deitado && !!col.prox && sobra >= 13 * ret.vh
            anchors { left: parent.left; right: parent.right; top: caixa.bottom; topMargin: 3.4 * ret.vh }
            height: Math.min(sobra, textoBalao.implicitHeight + 4.6 * ret.vh); radius: 1.8 * ret.vh
            gradient: Gradient { GradientStop { position: 0; color: "#1e2d49" } GradientStop { position: 1; color: "#16233c" } }
            border.color: "#2c3d5c"; border.width: Math.max(1, 0.12 * ret.vh)
            Rectangle {      // o círculo com a nota
                id: bola
                anchors { left: parent.left; leftMargin: 1.3 * ret.vw; verticalCenter: parent.verticalCenter }
                width: 8.6 * ret.vh; height: width; radius: width / 2
                color: "#07090e"; border.color: "#3affffff"; border.width: 1
                Image { anchors.centerIn: parent; width: parent.width * 0.5; height: width; source: Ic.url("louvor", "#f5d76e")
                        sourceSize.width: Math.round(width * 2); sourceSize.height: Math.round(height * 2) }
            }
            Column {
                anchors { left: bola.right; leftMargin: 1.1 * ret.vw; right: parent.right; rightMargin: 1.2 * ret.vw; verticalCenter: parent.verticalCenter }
                id: textoBalao; spacing: 0.9 * ret.vh
                Text { text: "PRÓXIMO LOUVOR"; color: "#f5d76e"; font.family: ret.ui; font.pixelSize: 2.1 * ret.vh; font.weight: Font.Bold
                       font.letterSpacing: 2.1 * ret.vh * 0.09 }
                Text {
                    width: parent.width; text: col.prox ? col.prox.nome : ""; color: "#eaf0fb"; font.family: ret.ui
                    font.pixelSize: 3.9 * ret.vh; font.weight: Font.ExtraBold; lineHeight: 1.08; wrapMode: Text.WordWrap
                    maximumLineCount: 2; elide: Text.ElideRight
                    font.capitalization: Font.AllUppercase
                }
                Rectangle {
                    width: quanto.implicitWidth + 2.2 * ret.vh; height: 3.4 * ret.vh; radius: height / 2
                    color: "#12331f"; border.color: "#2e8b57"; border.width: 1
                    Text { id: quanto; anchors.centerIn: parent; color: "#9fd3b4"; font.family: ret.ui; font.pixelSize: 1.9 * ret.vh; font.weight: Font.DemiBold
                           text: col.prox ? "daqui a " + col.prox.em + " slides" : "" }
                }
            }
        }
    }

    // o cartão: figuras com legenda, imagem pronta, o slide, ou um texto ("Fim da apresentação", "Próximo louvor")
    component Cartao: Rectangle {
        id: cart
        property var dados
        property bool seguir
        property bool noAr
        readonly property string tipo: dados ? dados.tipo : ""
        // a proporcao do slide que esta na frente (altura / largura); 16:9 ate a imagem chegar
        readonly property Image daFrente: frente === 0 ? imA : imB
        readonly property real proporcao: daFrente.status === Image.Ready && daFrente.implicitWidth > 0
                                          ? daFrente.implicitHeight / daFrente.implicitWidth : 9 / 16
        radius: 1.8 * ret.vh
        color: tipo === "slide" ? "black" : "white"
        clip: true
        gradient: tipo === "texto" ? gradTexto : null
        Gradient { id: gradTexto; GradientStop { position: 0; color: "#1e2d49" } GradientStop { position: 1; color: "#16233c" } }

        // o slide: o fundo "desfocado" sai de graça (a imagem lida em 32x18 e esticada) e o slide por cima
        // 10/11 (a travada de ~270 ms por clique no Vaio, e a prova_retorno 18): as duas imagens abriam NA LINHA DA
        // INTERFACE (asynchronous: false), 2 cartões x 2 = 4 JPEG por clique (~50 ms cada no Vaio). Agora abrem por fora, e o
        // slide anterior FICA no cartão até o novo estar pronto (duas imagens que se revezam: nunca pisca vazio)
        readonly property string urlSlide: tipo === "slide" && dados && dados.url ? String(dados.url) : ""
        property int frente: 0
        function poeSlide() {
            var tras = frente === 0 ? imB : imA
            tras.source = urlSlide
            if (urlSlide === "" || tras.status === Image.Ready) frente = (tras === imA ? 0 : 1)   // já no cache: vira na hora
        }
        onUrlSlideChanged: poeSlide()
        Component.onCompleted: poeSlide()
        Image {
            id: imA
            visible: cart.tipo === "slide" && cart.frente === 0; anchors.fill: parent
            fillMode: Image.PreserveAspectFit; sourceSize.width: Math.round(width); asynchronous: true
            onStatusChanged: if (status === Image.Ready && String(source) === cart.urlSlide) cart.frente = 0
        }
        Image {
            id: imB
            visible: cart.tipo === "slide" && cart.frente === 1; anchors.fill: parent
            fillMode: Image.PreserveAspectFit; sourceSize.width: Math.round(width); asynchronous: true
            onStatusChanged: if (status === Image.Ready && String(source) === cart.urlSlide) cart.frente = 1
        }
        Image {
            visible: cart.tipo === "img"; anchors.fill: parent; anchors.margins: 1.6 * ret.vh
            source: cart.tipo === "img" ? cart.dados.url : ""; fillMode: Image.PreserveAspectFit
        }
        Column {
            visible: cart.tipo === "texto"; anchors.centerIn: parent; width: parent.width - 4 * ret.vw
            spacing: 1.5 * ret.vh
            Text {
                visible: !!(cart.dados && cart.dados.sub); width: parent.width; horizontalAlignment: Text.AlignHCenter
                text: cart.dados && cart.dados.sub ? cart.dados.sub : ""; color: "#f5d76e"; font.family: ret.ui; font.pixelSize: 2.8 * ret.vh
                font.bold: true; font.capitalization: Font.AllUppercase; font.letterSpacing: 2.8 * ret.vh * 0.06
            }
            Text {
                width: parent.width; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
                text: cart.tipo === "texto" ? cart.dados.txt : ""; color: "#eaf0fb"; font.family: ret.ui; font.pixelSize: 6 * ret.vh
                font.weight: Font.ExtraBold; lineHeight: 1.15
            }
        }
        CantosRedondos {
            visible: cart.tipo === "slide"; anchors.fill: parent; raio: cart.radius; z: 3
            cor: "#11213c"; corBaixo: "#12223d"       // a cor do fundo da tela atras do cartao
        }
        Grade { visible: cart.tipo === "figs"; anchors.fill: parent; dados: cart.tipo === "figs" ? cart.dados : null; seguir: cart.seguir }
    }

    // A GRADE das figuras: o planoDaGrade do retorno.html (3.0.10). Cada figura é medida contra o tamanho que teria
    // SOZINHA no cartão; o arranjo de sempre (2 figuras = 2 colunas, até 4 = 2, mais = 3) só perde para outro em que
    // nenhuma figura fique menor e a mais prejudicada fique maior. A FIGURA MANDA: a legenda encolhe, a figura nunca.
    component Grade: Item {
        id: gr
        property var dados
        property bool seguir
        readonly property real pv: 1.6 * ret.vh
        readonly property real ph: 1 * ret.vw
        readonly property real tituloH: dados && dados.titulo ? 7 * ret.vh : 0
        readonly property real lw: width - 2 * ph
        readonly property real lh: height - 2 * pv - tituloH
        readonly property real base: (seguir ? 3.6 : 4) * ret.vh
        readonly property real gx: ret.vw
        readonly property real gy: 1.4 * ret.vh
        readonly property real legH: 2.12 * base * 1.06 + 8
        readonly property var plano: calcula(dados, lw, lh)

        function calcula(d, W, H) {
            if (!d || !d.grupos || W < 50 || H < 50) return { col: 1, lin: 1, linhas: [] }
            var grupos = d.grupos, n = 0
            for (var i = 0; i < grupos.length; i++) n += grupos[i].imgs.length
            var padrao = n <= 2 ? n : (n <= 4 ? 2 : 3)
            function sozinha(r) { var h = Math.min(H - legH, W * r); return h * h / r }
            function mede(col) {
                for (var i = 0; i < grupos.length; i++) if (grupos[i].imgs.length > col) return null
                var lin = 1, livre = col
                for (i = 0; i < grupos.length; i++) { if (grupos[i].imgs.length > livre) { lin++; livre = col } livre -= grupos[i].imgs.length }
                var cw = (W - (col - 1) * gx) / col
                var altImg = (H - (lin - 1) * gy) / lin - legH
                if (altImg < 6 * ret.vh) return null
                var pior = Infinity, menor = Infinity
                for (i = 0; i < grupos.length; i++) for (var j = 0; j < grupos[i].rs.length; j++) {
                    var r = grupos[i].rs[j], h = Math.min(altImg, cw * r), a = h * h / r
                    pior = Math.min(pior, a / sozinha(r)); menor = Math.min(menor, a)
                }
                return { col: col, lin: lin, nota: pior, menor: menor }
            }
            var ref = mede(padrao), melhor = ref
            for (var c = 1; c <= Math.min(n, 3); c++) {
                if (c === padrao) continue
                var m = mede(c)
                if (!m || (ref && m.menor < ref.menor * 0.97)) continue
                if (!melhor || m.nota > melhor.nota * 1.03) melhor = m
            }
            if (!melhor) melhor = { col: Math.min(n, 3), lin: Math.ceil(n / Math.min(n, 3)) }
            // as linhas do cartão (os grupos em ordem, quebrando quando não cabem)
            var linhas = [[]], resta = melhor.col
            for (i = 0; i < grupos.length; i++) {
                if (grupos[i].imgs.length > resta && linhas[linhas.length - 1].length) { linhas.push([]); resta = melhor.col }
                linhas[linhas.length - 1].push(grupos[i]); resta -= grupos[i].imgs.length
            }
            melhor.linhas = linhas
            melhor.lin = linhas.length
            return melhor
        }
        readonly property real cw: (lw - (plano.col - 1) * gx) / plano.col
        readonly property real ch: (lh - (plano.lin - 1) * gy) / plano.lin

        // o título do louvor (no A SEGUIR, quando é outro louvor)
        Text {
            id: titulo
            visible: gr.tituloH > 0
            anchors { top: parent.top; topMargin: gr.pv; horizontalCenter: parent.horizontalCenter }
            width: gr.lw; height: gr.tituloH - 1.2 * ret.vh
            text: gr.dados && gr.dados.titulo ? gr.dados.titulo : ""
            color: "#0f2f5e"; font.family: "Outfit"; font.weight: Font.ExtraBold; font.pixelSize: 4.4 * ret.vh
            font.capitalization: Font.AllUppercase; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            fontSizeMode: Text.Fit; minimumPixelSize: 2 * ret.vh; elide: Text.ElideRight
            Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom } height: 0.35 * ret.vh; color: "#f5d76e" }
        }
        Column {
            x: gr.ph
            y: gr.pv + gr.tituloH + topPadding
            readonly property real topPadding: Math.max(0, (gr.lh - gr.plano.lin * gr.ch - (gr.plano.lin - 1) * gr.gy) / 2)
            width: gr.lw
            spacing: gr.gy
            // ITENS FIXOS (05/11/2026): 6 linhas x 3 células x 2 figuras, só os usados aparecem. Repeater com
            // "model: lista" recriava figura e legenda a cada slide, e no Qt 6.12 cada Text recriado deixa memória
            // para trás (medido: +8 MB a cada 40 slides com a TV aberta). O maior cartão da tabela tem 5 grupos de até
            // 2 figuras (medido 05/11).
            Repeater {
                model: 6
                Row {
                    id: linhaG
                    readonly property var lin: gr.plano.linhas && index < gr.plano.linhas.length ? gr.plano.linhas[index] : null
                    visible: lin !== null
                    anchors.horizontalCenter: parent.horizontalCenter
                    // 13/11 (ele: "esse 'entao pude crer' ta muito pra baixo na imagem"): a figura encosta na legenda, e num
                    // cartao de UMA linha com figura larga sobrava um vazio so em cima. A sobra agora e dividida: o
                    // conjunto figura + legenda fica no meio do cartao (so com uma linha: as grades de varias nao mudam)
                    readonly property real folga: {
                        if (!lin || gr.plano.lin !== 1) return 0
                        var H = gr.ch - gr.legH, m = Infinity
                        for (var i = 0; i < lin.length; i++) {
                            var maior = 0
                            for (var j = 0; j < lin[i].rs.length; j++) maior = Math.max(maior, Math.min(H, gr.cw * lin[i].rs[j]))
                            m = Math.min(m, H - maior)
                        }
                        return m === Infinity ? 0 : Math.max(0, m)
                    }
                    transform: Translate { y: -linhaG.folga / 2 }
                    spacing: gr.gx
                    Repeater {
                        model: 3
                        // uma figura (ou duas lado a lado com a mesma legenda) e a legenda embaixo
                        Item {
                            id: cel
                            readonly property var g: linhaG.lin && index < linhaG.lin.length ? linhaG.lin[index] : null
                            visible: g !== null
                            readonly property int k: g ? g.imgs.length : 1
                            width: gr.cw * k + (k - 1) * gr.gx; height: gr.ch
                            Row {
                                id: imgs
                                width: parent.width; height: parent.height - gr.legH
                                spacing: gr.gx
                                Repeater {
                                    model: 2
                                    Image {
                                        readonly property string src: cel.g && index < cel.g.imgs.length ? cel.g.imgs[index] : ""
                                        visible: src !== ""
                                        width: (imgs.width - (cel.k - 1) * gr.gx) / cel.k; height: imgs.height
                                        source: src; fillMode: Image.PreserveAspectFit
                                        verticalAlignment: Image.AlignBottom; horizontalAlignment: Image.AlignHCenter
                                        sourceSize.height: Math.round(height); smooth: true; mipmap: true
                                    }
                                }
                            }
                            Text {
                                anchors { horizontalCenter: parent.horizontalCenter; top: imgs.bottom; topMargin: 8 }
                                width: parent.width * 0.92; height: gr.legH - 8
                                text: cel.g ? cel.g.txt : ""
                                color: "#1a1a1a"; font.family: "Outfit"; font.weight: Font.ExtraBold; font.pixelSize: gr.base
                                font.capitalization: Font.AllUppercase; lineHeight: 1.06
                                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignTop
                                wrapMode: Text.WordWrap; maximumLineCount: 3
                                fontSizeMode: Text.Fit; minimumPixelSize: 2.2 * ret.vh
                            }
                        }
                    }
                }
            }
        }
    }
}
