// O PALCO do telão (Sistema Nativo, 03/11/2026): 16:9 fixo e centralizado (letterbox), igual ao #tela do projecao.html.
// Duas camadas que se revezam: a nova entra com esmaecer (opacidade, na placa de vídeo) e a velha sai.
// Medidas copiadas do projecao.html da 3.0.12 (estilo limpo): título 2,2%..16,7% a partir de 14,5% da largura; letra
// 5,75% da altura, avanço 1,815, bloco a 19% da largura com 67,6% de largura, scaleY 1,06; "fim" no canto.
import QtQuick
import QtQuick.Effects
import QtMultimedia

Item {
    id: raiz
    property bool depurar: false
    property bool sombra: true
    // A SOMBRA DO LOUVOR (08/11/2026): o .txt da 3.0.13 tem text-shadow 0 2px 8px #000a (preta 67%, 2 px abaixo, 8 px
    // de desfoque). Pela placa (MultiEffect, desenhada uma vez por tela, em cache). Sem placa (desenho por software, onde
    // o MultiEffect sumia com a letra, 03/11) fica a sombra dura do próprio Text: telão sem letra nunca.
    readonly property bool temPlaca: GraphicsInfo.api !== GraphicsInfo.Software && GraphicsInfo.api !== GraphicsInfo.Unknown
    readonly property bool sombraPlaca: sombra && temPlaca
    property bool previa: false
    // a camada no ar: a saída de vídeo (telão) e a do espelho (prévia/retorno), que o Python liga uma à outra
    readonly property var sinkVideoAtivo: ativa === 0 ? camA.sinkVideo : camB.sinkVideo
    readonly property var sinkEspelhoAtivo: ativa === 0 ? camA.sinkEspelho : camB.sinkEspelho          // a prévia do painel não toca vídeo (só o 1º quadro): economia
    property int ativa: 0
    clip: true

    Rectangle { anchors.fill: parent; color: "black" }

    Item {
        id: tela
        width: Math.min(parent.width, parent.height * 16 / 9)
        height: Math.min(parent.height, parent.width * 9 / 16)
        anchors.centerIn: parent
        clip: true
        Camada { id: camA; objectName: "camA" }
        Camada { id: camB; objectName: "camB" }
    }

    // as imagens da APRESENTAÇÃO vêm do depósito do Python (image://apres): o slide no ar e o próximo já ficam abertos
    // (o E-450 do Vaio leva 110-650 ms para abrir um slide com camadas). Sem o depósito (provas que montam o QML
    // sozinhas), o arquivo direto, como antes.
    // caminho -> url (no Linux o caminho já começa com "/": file:// + /home/...)
    function urlDe(p) { p = String(p).replace(/\\/g, "/"); return p.charAt(0) === "/" ? "file://" + p : "file:///" + p }
    function imgApres(p) {
        p = String(p || ""); if (!p) return ""
        if (typeof temImagensApres !== "undefined" && temImagensApres) return "image://apres/" + encodeURIComponent(p)
        return "file:///" + p.replace(/\\/g, "/")
    }
    function mostrar(t) {
        // APRESENTAÇÃO, o MESMO slide com outro clique: não troca a tela. +1 toca o clique seguinte; outro número vai
        // direto ao estado pedido (voltar desfaz o último clique, como no PowerPoint). O projecao.html faz assim.
        var cur = ativa === 0 ? camA : camB
        // 08/11: vale para a PRÉVIA também (regra dele: o operador vê o mesmo clique, no mesmo instante)
        if (t.modo === "apres" && t.mov && !t.filme && cur.modo === "apres" && cur.t.src === t.src && cur.movAtual) {
            cur.garantirEntrada()
            if (t.passo === cur.passoAp + 1) cur.tocarPasso(t.passo, false)
            else if (t.passo !== cur.passoAp) cur.montarApres(t.passo, 0)
            cur.t = t
            return
        }
        // a PRÉVIA mostra o slide parado: o clique da animação no mesmo slide não reabre a imagem (no Vaio, 120 ms a cada clique)
        if (t.modo === "apres" && raiz.previa && cur.modo === "apres" && cur.t.src === t.src) { cur.t = t; return }
        // REGRA DELE (07/11 23h32): "eu travo, mas não te deixo na mão". O quadro no ar FICA até o próximo estar 100%
        // pronto (imagem decodificada, 1º quadro do vídeo, 1º quadro da animação); só então troca, de uma vez. Pedido
        // que chega enquanto o próximo se prepara SUBSTITUI o que esperava: o telão vai direto ao último. Nunca preto.
        if (coreo.running) acabarTroca()        // a troca anterior termina antes (a velha libera)
        t0Troca = Date.now(); rotTroca = (t.modo || "") + (t.i !== undefined ? " " + (t.i + 1) : "")
        var nova = ativa === 0 ? camB : camA
        nova.opacity = 0; nova.conteudo = 1; nova.z = 1
        nova.carregar(t)
        esperando = nova; msTroca = t.fade !== undefined ? t.fade : 700
        limite.restart()
        Qt.callLater(conferir)
    }
    property var esperando: null
    // os tocadores que a placa recusou, estacionados (ver "OS TOCADORES SÃO TROCÁVEIS" na Camada); teto de 8 por sessão
    property var estacionados: []
    property var estacionadosEm: []         // a hora (ms) em que cada um foi estacionado
    property int vagas: 0                   // quantos estão estacionados agora (para as provas e o registro)
    property int descartados: 0             // quantos já foram soltos (12/11)
    property double ultimaVaga: 0
    // 12/11/2026 (ordem dele: "o sistema tem que estar SEMPRE LIMPANDO AUTOMATICAMENTE"): estacionar para sempre segurava
    // a memória do decodificador até fechar (prova de 1.160 trocas: +86 MB). O buraco ruim que o estacionado tapava era o
    // defeito do driver (consertado: radeon-uvd); agora o tocador recusado fica só 30 s, o bastante para o novo pegar
    // memória noutro lugar, e depois é PARADO, ESVAZIADO e DESTRUÍDO (a memória volta sozinha).
    function guardarEstacionado(p) { estacionados.push(p); estacionadosEm.push(Date.now()); vagas = estacionados.length }
    Timer {
        // pela contagem (vagas): o push na lista não avisa o QML, e o relógio nunca ligava (prova 12/11 15h08: 7 presos)
        interval: 10000; repeat: true; running: raiz.vagas > 0
        onTriggered: {
            var agora = Date.now(), fica = [], ficaEm = []
            for (var i = 0; i < raiz.estacionados.length; i++) {
                var p = raiz.estacionados[i]
                if (agora - raiz.estacionadosEm[i] < 30000) { fica.push(p); ficaEm.push(raiz.estacionadosEm[i]); continue }
                try { p.stop(); p.source = ""; p.destroy() } catch (e) {}
                raiz.descartados++
            }
            raiz.estacionados = fica; raiz.estacionadosEm = ficaEm; raiz.vagas = fica.length
            console.log("tocadores recusados soltos: " + raiz.descartados + " no total, " + fica.length + " ainda estacionado(s)")
        }
    }
    Connections {
        target: (!raiz.previa && typeof controle !== "undefined") ? controle : null; ignoreUnknownSignals: true
        function onPlacaRecusou(n) {
            var agora = Date.now()
            if (agora - raiz.ultimaVaga < 700 || raiz.estacionados.length >= 8) return
            raiz.ultimaVaga = agora
            // fora da volta em que o aviso chegou: criar tocador no meio de um sinal derrubava o teste no Windows
            Qt.callLater(function () {
                var k = camA.estacionar() + camB.estacionar()
                raiz.vagas = raiz.estacionados.length
                if (k) console.log("placa recusou " + n + " quadro(s): " + k + " tocador(es) estacionado(s), " + raiz.estacionados.length + " no total")
            })
        }
    }
    // o esmaecimento só compõe: nenhum vídeo anda enquanto a tela troca (11/11; o contexto videoParadoNaTroca desliga)
    readonly property bool paraNaTroca: !raiz.previa && (typeof videoParadoNaTroca === "undefined" || videoParadoNaTroca)
    property int msTroca: 700
    // quanto tempo sem clique novo para o slide "firmar" e o vídeo abrir (10/11; medido: rajada de 10 cliques em 2 s = 200 ms
    // entre cliques; 350 ms cobre a mão do operador sem atrasar o movimento de quem parou)
    property int firmarMs: 350
    // VIGIA DE BURACOS (10/11, só no banco: contexto depurarBuraco): cada evento dos tocadores com a hora, e todo buraco
    // de mais de 150 ms na linha da interface; o banco cruza um com o outro
    readonly property bool vigiando: !raiz.previa && typeof depurarBuraco !== "undefined" && depurarBuraco
    function ev(s) { if (vigiando) console.log("EV " + (Date.now() % 1000000) + " " + s) }
    Timer { interval: 16; repeat: true; running: raiz.vigiando; property double ult: 0
            onTriggered: { var a = Date.now(); if (ult > 0 && a - ult > 150) console.log("BURACO " + (a - ult) + " ms de " + ((ult) % 1000000) + " a " + (a % 1000000)); ult = a } }
    // O QUE SAIU NO TELÃO, QUADRO A QUADRO (10/11 18h, só no banco: contexto depurarTelao). A cada quadro, antes de a placa
    // copiar a cena: qual slide domina a tela (a câmera de cima com opacidade >= 0,5, senão a de baixo) e a LUZ da tela
    // (0 = preto, 1 = slide inteiro; a de cima por cima da de baixo, sobre o preto). O banco (banco_metralhada.py) conta.
    signal quadroTelao(int slide, int passo, real luz)
    FrameAnimation {
        running: !raiz.previa && typeof depurarTelao !== "undefined" && depurarTelao
        onTriggered: {
            var c = camA.z >= camB.z ? camA : camB, b = c === camA ? camB : camA
            var vis = (c.opacity >= 0.5 || b.modo !== "apres") ? c : b
            var luz = c.opacity * c.conteudo + (1 - c.opacity) * b.opacity * b.conteudo
            raiz.quadroTelao(vis.modo === "apres" && vis.t.i !== undefined ? vis.t.i : -1, vis.t.passo || 0, luz)
        }
    }
    // 08/11 21h (a prova no PC da igreja): o TELÃO anota no nativo.log quanto cada troca esperou o slide novo ficar pronto
    // (clique -> pronto) e se entrou pelo limite de 4 s (que é quando pode aparecer incompleto)
    // O JEITO DE REPETIR O VÍDEO (10/11 18h, o teste dele no Vaio 17h46: com a volta "à mão" o telão inteiro PISCA PRETO 2
    // quadros a cada volta e a CIA 7 sai VERDE uma volta sim, outra não). Os jeitos, para medir no telão do Vaio
    // (banco_laco.py), escolhidos por NATIVO_LACO: "mao" (a de c62bba5: no fim, volta ao 0 e toca), "infinito" (o laço do
    // próprio tocador, o de antes de c62bba5), "reabre" (no fim, fecha e reabre o arquivo: decodificador novo, sem salto),
    // "antes" (salta ao 0 a 120 ms do fim, sem nunca chegar ao fim do arquivo).
    readonly property string lacoModo: typeof lacoJeito !== "undefined" && lacoJeito ? String(lacoJeito).split(":")[0] : "mao"
    // 13/11, A EMENDA CALADA (ele no Vaio 12/11: "tá meio travada a exibição das notinhas, dá tipo umas pausas (...) era mais
    // legal quando era fluido"). Medido quadro a quadro no Vaio (ferramentas/mede_emenda.py): a cada volta do arquivo a PLACA
    // leva ~300 ms para recomeçar o vídeo e depois solta ~12 quadros espremidos para alcançar o relógio (para e dispara).
    // Os vídeos novos (apresentacoes_leves.py) começam e terminam no quadro que a animação já segura parado e trazem escrito
    // quanto dura essa CAUDA (controle.caudaVideo). Ao chegar na cauda: pausa (a imagem que está na tela é a mesma do
    // 1º quadro), manda recomeçar e só TOCA quando o tempo da cauda passou. O recomeço da placa fica atrás de uma imagem que
    // já estava parada; depois os quadros saem certos, de 33 em 33 ms. No PC de casa o ritmo é exato. Vídeo sem cauda (os
    // antigos, os filmados) segue na volta "à mão". NATIVO_LACO=segura:ms força a espera em qualquer vídeo (só medida);
    // NATIVO_LACO=seco desliga a cauda (a volta de antes, para comparar).
    readonly property int seguraMs: typeof lacoJeito !== "undefined" && String(lacoJeito).split(":").length > 1 ? parseInt(String(lacoJeito).split(":")[1]) : 230
    property var caudas: ({})
    function caudaDe(p) {
        if (lacoModo === "segura") return seguraMs
        if (lacoModo !== "mao" || typeof controle === "undefined" || !controle) return 0
        var u = String(p.source)
        if (!u) return 0
        var c = caudas[u]
        if (c === undefined) { c = controle.caudaVideo(u); caudas[u] = c }
        return c
    }
    property var seguras: []
    // a câmera congelou ou descarregou no meio de uma cauda: a espera dela não vale mais (senão o "toca" da cauda
    // descongelaria o vídeo sozinho)
    function largaCaudas(c) {
        if (!seguras.length) return
        var r = []
        for (var i = 0; i < seguras.length; i++) if (!(c.player === seguras[i].p || c.playerLaco === seguras[i].p)) r.push(seguras[i])
        seguras = r
    }
    // um quadro chegou à saída de vídeo de uma câmera (só escuta enquanto há cauda esperando): o recomeço dela está pronto.
    function quadroDe(c) {
        if (typeof depuraCauda !== "undefined" && depuraCauda && seguras.length) console.log("CAUDA quadro aos " + (seguras[0].pedido ? Date.now() - seguras[0].pedido : -1) + " ms do pedido (faltam " + (seguras[0].quando - Date.now()) + " ms da cauda)")
        var agora = Date.now()
        for (var i = 0; i < seguras.length; i++) {
            var s = seguras[i]
            if (!s.pronto && s.pedido > 0 && (c.player === s.p || c.playerLaco === s.p)) s.pronto = true
        }
    }
    Timer {
        id: seguraT; interval: 10; repeat: true
        onTriggered: {
            var agora = Date.now(), resto = []
            for (var i = 0; i < raiz.seguras.length; i++) {
                var s = raiz.seguras[i]
                // toca quando o tempo da cauda passou E a placa já entregou o 1º quadro do recomeço (s.pronto, o quadroDe);
                // tocar antes disso faz o relógio andar sem imagem e os quadros saem espremidos depois (medido no Vaio com a
                // cauda de 200 ms: 5 quadros em 10 ms). Sem quadro nenhum em 300 ms além do tempo, toca assim mesmo.
                if (agora < s.quando || (!s.pronto && agora < s.quando + 300)) { resto.push(s); continue }
                try { if (s.p.playbackState === MediaPlayer.PausedState && String(s.p.source) === s.u) { raiz.ev("cauda toca" + (s.pronto ? "" : " SEM QUADRO")); s.p.play() } } catch (e) {}
            }
            raiz.seguras = resto
            if (!resto.length) stop()
        }
    }
    function lacoLoops(rep) { return (rep && lacoModo === "infinito") ? MediaPlayer.Infinite : 1 }
    function voltaLaco(p) {
        ev("volta laco " + lacoModo)
        if (lacoModo === "reabre") { var u = p.source; p.source = ""; p.source = u; p.play() }
        else { p.setPosition(0); p.play() }
    }
    function antesDoFim(p, rep) {
        var c = rep ? caudaDe(p) : 0
        if (c > 0 && p.duration > c + 200 && p.position >= p.duration - c && p.playbackState === MediaPlayer.PlayingState) {
            var falta = Math.max(1, p.duration - p.position)
            ev("cauda segura " + falta)
            // pausa JÁ; o recomeço é pedido na volta seguinte da fila (callLater): um quadro de antes da pausa que ainda
            // estivesse a caminho chega primeiro e não é confundido com o 1º quadro do recomeço (medido: no PC de casa o do
            // recomeço chega em 1 a 9 ms; no Vaio, pela placa, em 303 a 376 ms)
            p.pause()
            var item = { p: p, u: String(p.source), pedido: 0, quando: Date.now() + falta, pronto: false }
            var l = seguras.slice(); l.push(item); seguras = l
            seguraT.start()
            Qt.callLater(function () { try { item.pedido = Date.now(); item.p.setPosition(0) } catch (e) {} })
            return
        }
        if (lacoModo === "antes" && rep && p.duration > 0 && p.position >= p.duration - 120 && p.playbackState === MediaPlayer.PlayingState)
            { ev("volta laco antes"); p.setPosition(0) }
    }
    property double t0Troca: 0
    property string rotTroca: ""
    property bool peloLimite: false
    function conferir() { if (esperando && esperando.pronta) trocar() }
    function trocar() {
        var nova = esperando; if (!nova) return
        ev("trocar fade=" + msTroca)
        if (!raiz.previa && t0Troca > 0)
            console.log("troca " + rotTroca + ": pronto em " + (Date.now() - t0Troca) + " ms" + (peloLimite ? " PELO LIMITE DE 4 s" : ""))
        peloLimite = false
        esperando = null; limite.stop()
        if (!raiz.previa && typeof controle !== "undefined" && controle) controle.telaoEntrando()   // a Bíblia anda já daqui
        var velha = nova === camA ? camB : camA
        nova.z = 2; velha.z = 1
        if (msTroca <= 0) { nova.opacity = 1; velha.opacity = 0; velha.descarregar(); velha.preparaVideo(nova.t.proxVideo); velha.preparaUnico(nova.t.u)
                            avisaPronto() }
        else {
            // 08/11/2026 (relato dele 07/11 21h16: "as transições estão violentas"). Antes a velha sumia junto com a nova:
            // o FUNDO escurecia 25% no meio e as duas LETRAS se sobrepunham. A coreografia do projecao.html da 3.0.13:
            //  - o FUNDO novo entra POR CIMA do velho (fade ms, curva ease): o fundo nunca mergulha;
            //  - a LETRA velha sai (até ~20% na metade do fade) e some; a nova entra dali (fade ms): nunca duas letras.
            entrando = nova; saindo = velha
            if (raiz.paraNaTroca) velha.congelar()          // o vídeo que sai para no quadro em que estava
            aFundo.duration = msTroca; aSai.duration = msTroca / 2; pausaMeio.duration = msTroca / 2; aEntra.duration = msTroca
            nova.conteudo = 0
            coreo.restart()
        }
        ativa = nova === camA ? 0 : 1
    }
    // garantia: o que não ficou pronto em 4 s (arquivo quebrado, vídeo que não decodifica) entra assim mesmo
    Timer { id: limite; interval: 4000; onTriggered: { if (raiz.depurar) console.log("DEP troca pelo limite de 4 s"); raiz.peloLimite = true; trocar() } }
    Connections { target: camA; function onProntaChanged() { if (raiz.esperando === camA) raiz.conferir() } }
    Connections { target: camB; function onProntaChanged() { if (raiz.esperando === camB) raiz.conferir() } }
    // a coreografia da troca (a .camada e o #fx do projecao.html), com a curva "ease" do CSS: cubic-bezier(.25,.1,.25,1)
    property var saindo: null
    property var entrando: null
    readonly property var ease: [0.25, 0.1, 0.25, 1, 1, 1]
    function acabarTroca() {
        ev("acabarTroca")
        coreo.stop()
        if (entrando) { entrando.opacity = 1; entrando.conteudo = 1; entrando = null }
        if (saindo) { saindo.opacity = 0; saindo.conteudo = 1; saindo.descarregar(); saindo.preparaVideo(ativa === 0 ? camA.t.proxVideo : camB.t.proxVideo)
                      saindo.preparaUnico(ativa === 0 ? camA.t.u : camB.t.u); saindo = null }
        avisaPronto()
    }
    // o anti-queima-roupa (11/11): o TELÃO avisa o controle quando a troca TERMINOU de verdade (o slide novo inteiro na
    // tela, o velho solto). Só então o avançar seguinte passa: quem dita o ritmo é a máquina, não um número (ele no Vaio,
    // 09h00: avisando no começo da troca "parece 2 slides por segundo, e não necessariamente verificando se o processo de
    // carregamento terminou"; segurando, o painel piscava e depois quebrava). Aviso interno: nada aparece na tela.
    function avisaPronto() { if (!raiz.previa && typeof controle !== "undefined" && controle) controle.telaoPronto() }
    ParallelAnimation {
        id: coreo
        NumberAnimation { id: aFundo; target: raiz.entrando; property: "opacity"; from: 0; to: 1
                          easing.type: Easing.Bezier; easing.bezierCurve: raiz.ease }
        NumberAnimation { id: aSai; target: raiz.saindo; property: "conteudo"; from: 1; to: 0.2; easing.type: Easing.OutQuad }
        SequentialAnimation {
            PauseAnimation { id: pausaMeio }
            ScriptAction { script: { if (raiz.saindo) raiz.saindo.conteudo = 0; if (raiz.entrando) raiz.entrando.conteudo = 0.2 } }
            NumberAnimation { id: aEntra; target: raiz.entrando; property: "conteudo"; to: 1
                              easing.type: Easing.Bezier; easing.bezierCurve: raiz.ease }
        }
        onFinished: raiz.acabarTroca()
    }

    // ---------------------------------------------------------------- uma camada
    component Camada: Item {
        id: cam
        parent: tela
        anchors.fill: parent
        opacity: 0
        // a opacidade da LETRA/conteúdo (a "#cam" do projecao.html), separada da do fundo (a camada inteira): a troca faz
        // o fundo cruzar e o conteúdo sair e entrar (ver coreo). Vale para todo filho direto, menos o fundo.
        property real conteudo: 1
        // 11/11 (ele viu no Vaio: "enquanto esmaece o JPEG, fica um quadrado todo troncho das notas"): sem isto a
        // transparência da troca vale para CADA peça em separado, e onde o recorte animado cobre o JPEG a soma fica mais
        // forte que o resto (o retângulo aparece só durante a troca). Enquanto a camada esmaece, o JPEG e os recortes são
        // achatados numa imagem só (layer) e é ELA que esmaece. Parado (opacidade 1) não há layer nenhum.
        readonly property bool esmaecendo: opacity > 0 && (opacity < 1 || conteudo < 1)
        Component.onCompleted: {
            tocadores()
            for (var k = 0; k < children.length; k++) {
                var c = children[k]
                if (c !== fundoImg && c !== fonte && c !== video) (function (x) { x.opacity = Qt.binding(function () { return cam.conteudo }) })(c)
            }
            // o vídeo: o conteúdo E, no jpg-primeiro, escondido até o 1º quadro NOVO (nunca o último quadro de outro slide)
            video.opacity = Qt.binding(function () { return cam.conteudo * (cam.jpgPrimeiro && !cam.quadroVideo ? 0 : 1) })
            // Qt 6.9+: o fim do vídeo deixa o último quadro (KeepLastFrame; antes apagava); num Qt mais velho não faz nada
            if (video.endOfStreamPolicy !== undefined) video.endOfStreamPolicy = 1
            // o porteiro do arquivo único (10/11): a câmera do TELÃO pede o seu ao nascer
            if (!raiz.previa && typeof controle !== "undefined" && controle && controle.ligarPorteiro) controle.ligarPorteiro(cam)
        }
        property var t: ({})
        property string modo: ""
        readonly property real lw: tela.width
        readonly property real lh: tela.height
        // ESTILO MAPA-MÚNDI (07/11/2026): as caixas do projecao.html da 3.0.12 (.e-mapa): a faixa da Bíblia é mais baixa
        // (referência 16,5%..26,5%, versículo 27,5%..97,5%) e a do louvor mais fina (título 3%..12% a partir de 13,5%,
        // letra 16%..94%); a etiqueta "Louvor" pequena do mapa termina em 14,9%, então o título pode começar em 16,1%.
        readonly property bool mapa: t.estilo === "mapa"

        // PRONTA = tudo o que vai aparecer já está na placa (imagem carregada, 1º quadro do vídeo, 1º quadro animado)
        property bool quadroVideo: false
        function ok(img) { return !img.visible || img.source == "" || img.status === Image.Ready || img.status === Image.Error }
        readonly property bool pronta: ok(fundoImg) && ok(imgCias) && ok(imgApres) && (!video.visible || quadroVideo || jpgPrimeiro)
                                       && (!animAp.visible || animAp.pronta || animAp.arquivo === "")
        function carregar(x) {
            tocadores()
            raiz.ev(objectName + " carregar " + (x.video ? "video" : "") + (x.filme ? " filme" : "") + (x.laco ? " laco" : ""))
            quadroVideo = false
            t = x; modo = x.modo || ""
            var vid = (modo === "slide" && x.tipo === "video") ? x.arquivo : (modo === "apres" && x.video ? x.video : "")
            fase = 0; fimFilme = false; filmeEspera.stop(); firmar.stop()
            filaDesc = []; desmonta.stop(); abreLaco.stop()          // o que a desmontagem anterior deixou na fila não vale mais
            if (String(playerLaco.source) !== "") { playerLaco.stop(); playerLaco.source = "" }
            // O JPEG ATÉ O CLIQUE FIRMAR (ideia dele 10/11 11h56: "ele joga primeiro um JPEG (...) quando vê que o cara realmente
            // firmou naquele slide, ele mete o MP4"). Medido no Vaio: cada arquivo de vídeo que abre liga um decodificador da
            // placa, e isso PARA a placa inteira ~220 ms (o painel junto). Na ENTRADA de um slide com vídeo o telão troca já com o
            // .jpg leve (o mesmo 1º quadro); o vídeo só abre quando nenhum clique novo chega em FIRMAR_MS (e depois do fade da
            // entrada). Em rajada nenhum decodificador liga. Os cliques DENTRO do slide (passo > 0) seguem tocando na hora.
            // O ARQUIVO ÚNICO (10/11, sim dele 12h38): a apresentação inteira num .mp4 (empacotar_unico.py). O tocador desta
            // câmera abre o arquivo UMA vez e salta para o trecho do clique; o porteiro (sistema_nativo.ligar_porteiro) só
            // deixa passar à tela os quadros do trecho. Nenhum decodificador novo liga no clique (medido: é isso que para a placa).
            var unico = !!(vid && x.u && !raiz.previa && modo === "apres")
            unicoEspera.stop()
            if (unico) {
                usaUnico = true
                jpgPrimeiro = !!(!x.passo && x.src)        // a tela entra com o .jpg; o vídeo aparece no 1º quadro do trecho
                uIni = x.uIni; uFim = x.uFim; uLacoIni = x.uLacoIni; uLacoFim = x.uLacoFim; uAtivo = true; uMudou()
                if (uArq !== String(x.u)) { uArq = String(x.u); player.source = raiz.urlDe(x.u) }
                var esperaU = (x.filme && !x.passo) ? (x.fade !== undefined ? x.fade : cerebroFade) : 0
                if (esperaU > 0) { unicoEspera.interval = esperaU; unicoEspera.restart() } else comecarTrecho()
                vid = ""
            } else if (vid) { usaUnico = false; uArq = ""; uAtivo = false; uMudou() }
            jpgPrimeiro = unico ? jpgPrimeiro : !!(vid && !raiz.previa && modo === "apres" && !x.passo && x.src
                                                   && typeof jpgAteFirmar !== "undefined" && jpgAteFirmar)
            if (jpgPrimeiro && !unico) {
                if (String(player.source) !== "") { player.stop(); player.source = "" }
                var esperaJ = x.filme ? (x.fade !== undefined ? x.fade : cerebroFade) : 0
                firmar.interval = Math.max(raiz.firmarMs, esperaJ); firmar.restart()
                vid = ""                                   // nada abre agora
            }
            if (vid && !raiz.previa) {
                var u = "file:///" + vid.replace(/\\/g, "/")
                // o filme toca a entrada UMA vez (o laço é o outro tocador). Acertado aqui, à mão: o vídeo pré-aberto pela
                // câmera livre (preparaVideo) nasceu com Infinite e a ligação não mudava a tempo (a entrada repetia, 09/11)
                // 10/11 (medido no Vaio, Qt 6.9): o loop do PRÓPRIO tocador (MediaPlayer.Infinite) trava a linha da interface
                // ~230 ms a CADA volta (o painel do operador parava; 7 vezes em 8 s num laço de 1,1 s). Tocando UMA vez e
                // voltando ao começo à mão no fim (o "pulo"): maior travada 41-57 ms, nenhuma acima de 100. Todo vídeo vai assim.
                repete = !(modo === "apres" && x.filme && !x.videoLaco)
                player.loops = raiz.lacoLoops(repete)
                if (String(player.source) !== u) player.source = u      // já pré-carregado (preparaVideo): só toca
                // o FILME do clique (09/11): o laço fica aberto, parado (a troca no fim da entrada não abre arquivo).
                // 10/11 (a travada de ~240 ms nos cliques com vídeo, Vaio): abrir, parar e trocar tocadores custa 17-55 ms
                // CADA na linha da interface, e o clique fazia 4-5 na mesma volta. O laço abre DEPOIS do 1º quadro da
                // entrada (abreLaco), e a câmera velha desmonta um tocador por vez (desmonta). PC de casa: 83-151 ms -> 35-49.
                lacoPendente = (modo === "apres" && x.filme && x.laco) ? "file:///" + String(x.laco).replace(/\\/g, "/") : ""
                // a entrada do 1º clique espera a tela terminar de entrar, como o PowerPoint (e como o montarApres)
                // 11/11: com o vídeo parado na troca (paraNaTroca), TODO vídeo que entra por troca de slide espera o fim do
                // esmaecimento no 1º quadro (antes só a entrada filmada): a placa não decodifica enquanto compõe as duas telas
                var espera = (((modo === "apres" && (x.filme || raiz.paraNaTroca)) || (modo === "slide" && raiz.paraNaTroca)) && !x.passo)
                             ? (x.fade !== undefined ? x.fade : cerebroFade) : 0
                // (toca até o 1º quadro chegar e pausa nele: o "pronta" da troca conta o quadro que chegou tocando)
                pausarNoPrimeiro = espera > 0
                if (espera > 0) { filmeEspera.interval = espera; filmeEspera.restart() }
                player.play()
            }
            else if (unico) {}
            else if (uArq !== "") { player.pause(); uAtivo = false; uMudou() }     // slide sem vídeo: o arquivo único fica aberto
            else if (!jpgPrimeiro) { player.stop(); player.source = "" }
            Qt.callLater(ajustar)
            pararEfs(); movAtual = null
            // a montagem fica para o instante seguinte (o Repeater cria as camadas antes); se um CLIQUE chegou nesse meio
            // tempo (o celular manda "entrar" e "clique 2" juntos), monta direto no passo MAIS NOVO, sem voltar ao 0 (07/11)
            if (modo === "apres" && x.mov && !x.filme) {      // com o FILME, o "mov" fica só para o celular (09/11)
                movAtual = x.mov
                // 08/11 (teste dele: "1º Avançar não faz nada"): a conferência era movAtual !== x.mov, e a property var guarda
                // uma CÓPIA do objeto: dava sempre diferente, o palco nunca era montado e o clique não achava as camadas.
                // Agora pela carga (um número): outro carregar no meio tempo = esta montagem não vale mais.
                var minha = ++carga
                Qt.callLater(function() { if (carga !== minha || !movAtual) return; var u = cam.t; montarApres(u.passo || 0, u === x ? (x.fade || 0) : 0) })
            }
            if (raiz.depurar) Qt.callLater(function() { console.log("DEP carregar modo=" + modo + " lw=" + lw + " lh=" + lh + " op=" + opacity + " z=" + z + " raiz=" + raiz.width + "x" + raiz.height + " px=" + bloco.px + " fundoVis=" + fundoImg.visible + " st=" + fundoImg.status) })
        }
        // a câmera que saiu: o tocador principal para JÁ (o som some na hora); o laço e o vídeo do próximo, um por volta
        // o clique FIRMOU: abre o vídeo agora (a entrada do filme já esperou o fade dentro do intervalo do firmar)
        property bool jpgPrimeiro: false
        Timer { id: firmar
                onTriggered: { var x = cam.t; if (!cam.jpgPrimeiro || !x.video) return
                               raiz.ev(cam.objectName + " firmou")
                               cam.repete = !(cam.modo === "apres" && x.filme && !x.videoLaco); player.loops = raiz.lacoLoops(cam.repete)
                               cam.lacoPendente = (x.filme && x.laco) ? "file:///" + String(x.laco).replace(/\\/g, "/") : ""
                               cam.pausarNoPrimeiro = false
                               player.source = "file:///" + String(x.video).replace(/\\/g, "/"); player.play() } }
        // o arquivo único: os trechos, o porteiro (Python) lê por uMudou; a saída escondida recebe tudo o que o tocador decodifica
        signal uMudou()
        property bool usaUnico: false
        property string uArq: ""
        property bool uAtivo: false
        property real uIni: 0
        property real uFim: 0
        property real uLacoIni: -1
        property real uLacoFim: -1
        function congelar() { tocadores(); raiz.ev(objectName + " congela"); filmeEspera.stop(); abreLaco.stop()
                              if (player.playing) player.pause(); if (playerLaco.playing) playerLaco.pause(); raiz.largaCaudas(cam) }
        function comecarTrecho() { raiz.ev(objectName + " trecho " + uIni); player.setPosition(uIni); player.play() }
        function saltar(ms) { raiz.ev(objectName + " salta " + ms); player.setPosition(ms); if (!player.playing) player.play() }
        function parar() { raiz.ev(objectName + " para no fim"); player.pause(); fimFilme = true }
        Timer { id: unicoEspera; onTriggered: cam.comecarTrecho() }
        // a câmera livre já abre o arquivo único do grupo (uma vez; o próximo clique só salta)
        function preparaUnico(u) {
            if (raiz.previa || !u || uArq === String(u)) return
            tocadores()
            raiz.ev(objectName + " abre unico"); usaUnico = true; uArq = String(u); uAtivo = false; uMudou()
            player.source = raiz.urlDe(u); player.pause()
        }
        VideoOutput { id: fonte; objectName: raiz.previa ? "" : "fonteCam"; width: 2; height: 2; opacity: 0 }
        function descarregar() { tocadores(); raiz.largaCaudas(cam); raiz.ev(objectName + " descarregar"); filmeEspera.stop(); firmar.stop(); jpgPrimeiro = false; abreLaco.stop(); lacoPendente = ""; fase = 0
                                 unicoEspera.stop()
                                 if (uArq !== "") { player.pause(); uAtivo = false; uMudou() }     // o arquivo único fica ABERTO
                                 else if (String(player.source) !== "") { player.stop(); player.source = "" }
                                 filaDesc = String(playerLaco.source) !== "" ? ["laco"] : []
                                 if (filaDesc.length) desmonta.restart()
                                 pararEfs(); movAtual = null; modo = ""; t = ({}) }
        // 09/11 (ele: "o próximo não precisa rodar a animação, mas é bom que esteja pré-carregado, para a passagem ser
        // instantânea"; medido: abrir o .mp4 no clique custava 280 ms na linha da interface): a câmera LIVRE abre já o vídeo
        // do PRÓXIMO slide, parado no 1º quadro; no clique ele só começa a tocar (10/11: entra na fila, depois do laço)
        function preparaVideo(p) {
            // 10/11: com o JPEG até firmar, pré-abrir o próximo vídeo só ligava mais um decodificador (= mais uma parada da placa,
            // no meio da rajada). O próximo entra pelo JPEG e o vídeo abre quando firmar. NATIVO_PREABRE=1 (contexto) volta.
            if (typeof preAbreVideo === "undefined" || !preAbreVideo) return
            if (raiz.previa || !p) return
            tocadores()
            var u = "file:///" + String(p).replace(/\\/g, "/")
            if (String(player.source) === u) return
            filaDesc = filaDesc.concat([u]); desmonta.restart()
        }
        property var filaDesc: []
        property string lacoPendente: ""
        Timer { id: desmonta; interval: 120
                onTriggered: { var f = cam.filaDesc; if (!f.length) return; var op = f[0]; cam.filaDesc = f.slice(1); raiz.ev(cam.objectName + " desmonta " + (op === "laco" ? "laco" : "prepara"))
                               if (op === "laco") { playerLaco.stop(); playerLaco.source = "" }
                               else if (String(player.source) !== op) { player.source = op; player.pause() }
                               if (cam.filaDesc.length) desmonta.restart() } }
        // o laço do filme abre um pouco depois do 1º quadro da entrada (nunca na mesma volta da troca)
        Timer { id: abreLaco; interval: 150
                onTriggered: if (cam.lacoPendente !== "" && String(playerLaco.source) === "") { raiz.ev(cam.objectName + " abreLaco"); playerLaco.source = cam.lacoPendente; playerLaco.pause() } }
        onFaseChanged: raiz.ev(objectName + " fase " + fase)

        // fundo do louvor / tela de espera: a imagem inteira, esticada no 16:9 (center/100% 100%)
        Image {
            id: fundoImg
            anchors.fill: parent
            visible: ["louvor", "fundo", "biblia", "bibmulti", "relogio", "timer", "texto", "cifra"].indexOf(cam.modo) >= 0
            source: visible && cam.t.fundo ? "file:///" + cam.t.fundo.replace(/\\/g, "/") : ""
            fillMode: Image.Stretch; asynchronous: true; cache: true; smooth: true
            // A5 (08/11): na PRÉVIA a imagem vem a 1,5x o tamanho dela, encolhida com qualidade na leitura (1,5x deu a nitidez
            // do Edge: 27,0 x 27,4; 1x ficava mole, 2x serrilhada); a de 1920
            // desenhada a 1/6 saía serrilhada
            sourceSize.width: raiz.previa ? Math.max(64, Math.round(cam.lw * 1.5)) : 1920
        }
        // tela pronta das CIAS: inteira, sem esticar (4:3 no 16:9, sobra preta dos lados)
        Image {
            id: imgCias
            anchors.fill: parent
            visible: cam.modo === "slide" && (cam.t.tipo === "imagem" || raiz.previa)
            source: visible && cam.t.webp ? "file:///" + cam.t.webp.replace(/\\/g, "/") : ""
            sourceSize.width: raiz.previa ? Math.max(64, Math.round(cam.lw * 1.5)) : 0
            fillMode: Image.PreserveAspectFit; asynchronous: true; cache: true
        }
        // a tela das CIAS SEM vídeo convertido (08/11/2026, ordem da HD: "quem atualiza pelo clique não pode ficar com as
        // CIAS paradas"): o WebP ANIMADO que a 3.0.x já tem na pasta do usuário toca, como o <img> do projecao.html dela.
        // Por cima da imagem parada (até os quadros ficarem prontos aparece o 1º, nunca preto). Na prévia fica parado.
        // FORMA B (protótipo, só com NATIVO_ANIM_FORMATO=B e a folha gerada): o fundo parado + a folha de sprites
        readonly property var spCias: (typeof animFormatoB !== "undefined" && animFormatoB && cam.t.tipo === "imagem" && cam.t.webp)
                                      ? controle.spritesDe(String(cam.t.webp)) : ({})
        SpriteAnim {
            id: spriteCias; objectName: raiz.previa ? "" : "spriteCias"
            anchors.fill: parent
            visible: cam.modo === "slide" && cam.t.tipo === "imagem" && !raiz.previa && !!cam.spCias.fundo
            layer.enabled: cam.esmaecendo && visible
            dados: cam.spCias.fundo ? cam.spCias : null
        }
        AnimSlide {
            id: animCias; objectName: raiz.previa ? "" : "animCias"
            anchors.fill: parent
            // 08/11 (regra dele: "o operador vê EXATAMENTE o que sai, no mesmo instante e com a mesma animação"): a prévia
            // toca também, com os MESMOS quadros do telão (largura 0 = a mesma decodificação, nada a mais)
            // 09/11 (ordem dele, teste no Vaio: "forçando a animação em todas as telas, não tem necessidade"): a animação
            // toca SÓ no telão; a prévia e o espelho do retorno mostram o slide parado (no Vaio, cada quadro da prévia
            // encolhido segurava a trava do Python e o painel travava 2-3 s)
            visible: cam.modo === "slide" && cam.t.tipo === "imagem" && !raiz.previa && !spriteCias.visible
            arquivo: visible && cam.t.webp ? String(cam.t.webp) : ""
            largura: raiz.previa ? 640 : 0
        }
        // O FILME (09/11, as camadas viraram vídeo): a ENTRADA toca uma vez; no fim, o LAÇO (outro tocador, já aberto e
        // parado no 1º quadro, que é o último da entrada) assume a MESMA saída de vídeo (os espelhos seguem recebendo) e
        // repete; sem laço, a entrada PAUSA no último quadro (o slide fica parado no estado final, como o PowerPoint).
        readonly property bool filmeAtivo: cam.modo === "apres" && !!cam.t.filme
        property int fase: 0                 // 0 = a entrada (ou o vídeo de sempre), 1 = o laço
        property bool fimFilme: false
        property bool pausarNoPrimeiro: false
        Timer { id: filmeEspera; onTriggered: player.play() }
        // ---- OS TOCADORES SÃO TROCÁVEIS (11/11/2026, o "verdão" do Vaio). Medido lá: a placa (Radeon PALM) tem 384 MB de
        // memória de vídeo e a região compartilhada começa logo depois (0x18000000), que não é múltiplo de 256 MB. O
        // decodificador da placa (UVD) só aceita bloco que não atravesse uma linha de 256 MB; o driver confere a posição
        // DENTRO da região, mas a linha é contada do zero. Um bloco do decodificador que caia em cima dos 512 MB é
        // recusado em TODO quadro ("kernel rejected CS" / "reloc ... crossing 256MB boundary"): o vídeo fica com lixo
        // verde e pisca. Fechar e abrir de novo devolve o MESMO buraco ao decodificador seguinte.
        // O conserto: o tocador recusado NÃO é fechado. Fica ESTACIONADO (parado, sem tela), segurando o bloco ruim
        // pelo resto da sessão, e um tocador novo assume o vídeo: os blocos dele caem noutro lugar. O ruim vira a tampa.
        property var player: null
        property var playerLaco: null
        // (nascem na 1ª vez que alguém precisa: o carregar pode chegar antes de a câmera terminar de nascer)
        function tocadores() { if (!player) { player = compPlayer.createObject(cam); playerLaco = compLaco.createObject(cam) } }
        function estacionar() {
            var n = 0
            if (player && !usaUnico && player.playbackState === MediaPlayer.PlayingState) {
                var u = player.source, lp = player.loops, velho = player
                velho.pause(); raiz.guardarEstacionado(velho)
                player = compPlayer.createObject(cam); player.loops = lp; player.source = u; player.play(); n++
            }
            if (playerLaco && playerLaco.playbackState === MediaPlayer.PlayingState) {
                var ul = playerLaco.source, velhoL = playerLaco
                velhoL.pause(); raiz.guardarEstacionado(velhoL)
                playerLaco = compLaco.createObject(cam); playerLaco.source = ul; playerLaco.play(); n++
            }
            return n
        }
        Component { id: compPlayer
        MediaPlayer {
            id: eu
            loops: 1                           // a volta é à mão (repete), nunca o Infinite (trava a interface no Vaio)
            videoOutput: cam.player !== eu ? null : (cam.usaUnico ? fonte : (cam.fase === 0 ? video : null))
            onPlaybackStateChanged: if (cam.player === eu) raiz.ev(cam.objectName + " eu estado " + playbackState)
            onPositionChanged: { if (cam.player !== eu) return; raiz.antesDoFim(eu, cam.repete && !cam.usaUnico); if (!cam.usaUnico && cam.filmeAtivo && !cam.t.laco && !cam.t.videoLaco && eu.duration > 0 && eu.position >= eu.duration - 70
                                   && eu.playbackState === MediaPlayer.PlayingState) { eu.pause(); cam.fimFilme = true } }
            onMediaStatusChanged: { if (cam.player !== eu) return; raiz.ev(cam.objectName + " eu midia " + mediaStatus); if (mediaStatus === MediaPlayer.EndOfMedia) {
                // o arquivo único acabou (o trecho era o último): o laço volta, o resto fica no último quadro
                if (cam.usaUnico) { if (cam.uAtivo && cam.uLacoFim > cam.uLacoIni && cam.uLacoIni >= 0) cam.saltar(cam.uLacoIni); else cam.fimFilme = true }
                else if (cam.filmeAtivo && cam.t.laco) {
                    // entrada mais curta que a espera do abreLaco: abre aqui mesmo (raro; custa a abertura neste instante)
                    if (String(playerLaco.source) === "") { abreLaco.stop(); playerLaco.source = cam.lacoPendente || ("file:///" + String(cam.t.laco).replace(/\\/g, "/")) }
                    cam.fase = 1; playerLaco.play() }
                else if (cam.repete) raiz.voltaLaco(eu)      // o vídeo em laço: volta (o jeito: lacoModo)
                else cam.fimFilme = true
            } }
        }
        }
        property bool repete: true            // o vídeo de agora volta ao começo no fim (o carregar acerta)
        Component { id: compLaco
        MediaPlayer { id: euL; loops: raiz.lacoLoops(true); videoOutput: cam.playerLaco !== euL ? null : (cam.fase === 1 ? video : null)
                      onPlaybackStateChanged: if (cam.playerLaco === euL) raiz.ev(cam.objectName + " laco estado " + playbackState)
                      onMediaStatusChanged: { if (cam.playerLaco !== euL) return; raiz.ev(cam.objectName + " laco midia " + mediaStatus)
                                              if (mediaStatus === MediaPlayer.EndOfMedia) raiz.voltaLaco(euL) }
                      onPositionChanged: if (cam.playerLaco === euL) raiz.antesDoFim(euL, true) }
        }
        // 09/11: o slide de APRESENTAÇÃO animado também vem em vídeo (o .mp4 leve, H.264 pela placa), por cima do .jpg
        // parado (imgApres) e por baixo das camadas do movimento (palcoAp, z 2)
        readonly property bool videoApres: cam.modo === "apres" && !!cam.t.video
        Connections { target: video.videoSink; enabled: raiz.seguras.length > 0; function onVideoFrameChanged() { raiz.quadroDe(cam) } }
        VideoOutput { id: video; objectName: raiz.previa ? "" : "saidaCam"; anchors.fill: parent; z: cam.videoApres ? 1 : 0
                      visible: ((cam.modo === "slide" && cam.t.tipo === "video") || cam.videoApres) && !raiz.previa
                      fillMode: VideoOutput.PreserveAspectFit }
        Connections { target: video.videoSink; function onVideoFrameChanged() {
            if (!cam.quadroVideo && player.playing) { cam.quadroVideo = true; if (cam.lacoPendente !== "") abreLaco.restart() }
            if (cam.pausarNoPrimeiro && cam.quadroVideo) { cam.pausarNoPrimeiro = false; if (filmeEspera.running) player.pause() } } }
        // UMA decodificação, várias telas (08/11/2026): na PRÉVIA (e no espelho do retorno) o vídeo não é tocado de novo;
        // o Python repassa a esta saída o MESMO quadro que o telão decodificou. Por cima da imagem parada: até o 1º
        // quadro chegar, aparece a imagem, nunca preto.
        VideoOutput { id: espelho; anchors.fill: parent; fillMode: VideoOutput.PreserveAspectFit; z: cam.videoApres ? 1 : 0
                      visible: raiz.previa && ((cam.modo === "slide" && cam.t.tipo === "video") || cam.videoApres) }
        readonly property var sinkVideo: video.videoSink
        readonly property var sinkEspelho: espelho.videoSink

        // ---- APRESENTAÇÃO (o modo "slide" das apresentações do projecao.html): a tela pronta, inteira e sem esticar.
        // Com animação dentro (movimento.json, feito do pptx): o fundo parado + as camadas que se mexem, com a linha do
        // tempo EXATA do PowerPoint (esmaecer, aparecer, revelar, girar, crescer, caminho) e os nossos (pulsar, pop).
        // Cada camada: caminho (mexe a caixa inteira) > giro e escala (no centro da forma) > recorte do revelar > imagem.
        // Tudo desenhado pela placa de vídeo; a animação é um número de 0 a 1 que o Qt anda, e cada efeito o aplica.
        // A prévia do painel mostra a tela parada (as camadas só no telão: economia de memória).
        readonly property var spAp: (typeof animFormatoB !== "undefined" && animFormatoB && cam.modo === "apres" && !!cam.t.animada)
                                    ? controle.spritesDe(String(cam.t.spr || cam.t.src || "")) : ({})
        Item {
            id: grupoAp
            anchors.fill: parent
            layer.enabled: cam.esmaecendo && spriteAp.visible
            Image {
                id: imgApres
                anchors.fill: parent
                visible: cam.modo === "apres"
                source: !visible ? "" : raiz.imgApres(cam.movAtual ? cam.movAtual.base : (cam.t.src || ""))
                sourceSize.width: raiz.previa ? Math.max(64, Math.round(cam.lw * 1.5)) : 0
                fillMode: Image.PreserveAspectFit; asynchronous: true; cache: true; smooth: true
            }
            // o slide que é IMAGEM ANIMADA (WebP com vários quadros, 49 dos 95 do acervo): toca, como o <img> do projecao.html
            // da 3.0.13 (antes ficava parado no 1º quadro). Por cima da imagem parada; quadros decodificados no fundo (AnimSlide).
            SpriteAnim {
                id: spriteAp; objectName: raiz.previa ? "" : "spriteAp"; semFundo: true
                anchors.fill: parent
                visible: cam.modo === "apres" && !!cam.t.animada && !cam.movAtual && !!cam.spAp.fundo && (!raiz.previa || typeof spriteEspelhos === "undefined" || spriteEspelhos)     // 10/11: em TODAS as saídas (a folha não decodifica nada)
                dados: cam.spAp.fundo ? cam.spAp : null
            }
            AnimSlide {
                id: animAp
                anchors.fill: parent
                visible: cam.modo === "apres" && !!cam.t.animada && !cam.movAtual && !raiz.previa && !spriteAp.visible   // só no telão (09/11)
                arquivo: visible ? String(cam.t.src || "") : ""
                // 08/11: na prévia, 640 TIRADOS dos quadros do telão (QuadrosAnim: encolhe os já decodificados, sem 2ª
                // decodificação nem fila; antes o operador via a animação ~3 s depois da saída, medido por ele no Vaio)
                largura: raiz.previa ? 640 : 0
            }
        }
        property var movAtual: null
        property int carga: 0
        property int passoAp: 0
        property var efs: []
        property var cams: ({})
        Item {
            id: palcoAp
            anchors.fill: parent; z: 2                    // por cima do vídeo do fundo (09/11)
            visible: cam.modo === "apres" && !!cam.movAtual
            // o FUNDO do slide com movimento também pode ser animado (s10, s19, s21 da Evangelização): toca por cima do
            // parado (imgApres), como o <img> do projecao.html
            readonly property var spBase: (typeof animFormatoB !== "undefined" && animFormatoB && cam.movAtual)
                                          ? controle.spritesDe(String(cam.movAtual.baseOrig || cam.movAtual.base || "")) : ({})
            SpriteAnim { id: spriteBase; anchors.fill: parent; semFundo: true; visible: !raiz.previa && !!palcoAp.spBase.fundo; dados: palcoAp.spBase.fundo ? palcoAp.spBase : null }
            AnimSlide { anchors.fill: parent; arquivo: cam.movAtual && !raiz.previa && !spriteBase.visible ? String(cam.movAtual.base || "") : ""; largura: 0; tempo: cam.tempoFilme }
            Repeater {
                id: repCam
                model: cam.movAtual ? cam.movAtual.camadas : []
                Item {
                    id: pm
                    width: palcoAp.width; height: palcoAp.height
                    property var c: modelData
                    property real tx: 0; property real ty: 0; property real rot: 0
                    property real sx: 1; property real sy: 1; property real pulso: 1; property real popf: 1
                    property real ciT: 0; property real ciB: 0; property real ciL: 0; property real ciR: 0
                    // o "Círculo" do PowerPoint (08/11): circ = tamanho da elipse (1 = cobre a caixa inteira; -1 = sem
                    // máscara); circDentro = o que aparece é o lado de DENTRO da elipse (out) ou o de FORA (in)
                    property real circ: -1; property bool circDentro: true
                    property bool vis: true
                    x: tx * palcoAp.width; y: ty * palcoAp.height
                    visible: vis
                    Item {
                        id: pr
                        x: pm.c.x * pm.width; y: pm.c.y * pm.height
                        width: pm.c.w * pm.width; height: pm.c.h * pm.height
                        transform: [
                            Scale { origin.x: pm.c.cx * pr.width; origin.y: pm.c.cy * pr.height
                                    xScale: pm.sx * pm.pulso * pm.popf; yScale: pm.sy * pm.pulso * pm.popf },
                            Rotation { origin.x: pm.c.cx * pr.width; origin.y: pm.c.cy * pr.height; angle: pm.rot }
                        ]
                        // a máscara do Círculo: uma elipse no centro da caixa, do tamanho circ x a diagonal (circ 1 = cobre
                        // até os cantos). Só existe na placa enquanto o efeito anda (layer desligado no resto do tempo)
                        Item {
                            id: mascara
                            width: pr.width; height: pr.height; visible: false
                            layer.enabled: pm.circ >= 0
                            // "out": um disco branco que cresce. "in": um ANEL (borda grossa, miolo vazio) do tamanho que
                            // cobre a caixa, com o furo de tamanho circ fechando. Sem maskInverted: invertido não mostrava
                            // nada no meio do efeito (medido 08/11 11h25)
                            Rectangle {
                                id: elipse
                                readonly property real esc: pm.circDentro ? Math.max(0.0001, pm.circ) : 1
                                width: 100; height: 100; radius: 50; antialiasing: true
                                color: pm.circDentro ? "white" : "transparent"
                                border.color: "white"; border.width: pm.circDentro ? 0 : 50 * (1 - Math.max(0, Math.min(1, pm.circ)))
                                x: (mascara.width - width) / 2; y: (mascara.height - height) / 2
                                transform: Scale { origin.x: 50; origin.y: 50
                                    xScale: elipse.esc * mascara.width * Math.SQRT2 / 100
                                    yScale: elipse.esc * mascara.height * Math.SQRT2 / 100 }
                            }
                        }
                        layer.enabled: pm.circ >= 0
                        layer.effect: MultiEffect {
                            maskEnabled: true; maskSource: mascara
                            maskThresholdMin: 0.5; maskSpreadAtMin: 0.2
                        }
                        Item {
                            id: corte
                            clip: pm.ciT > 0 || pm.ciB > 0 || pm.ciL > 0 || pm.ciR > 0
                            x: pm.ciL * pr.width; y: pm.ciT * pr.height
                            width: Math.max(0, pr.width * (1 - pm.ciL - pm.ciR)); height: Math.max(0, pr.height * (1 - pm.ciT - pm.ciB))
                            Image {
                                x: -corte.x; y: -corte.y; width: pr.width; height: pr.height
                                source: raiz.imgApres(pm.c.src)
                                fillMode: Image.Stretch; asynchronous: false; cache: false; smooth: true
                            }
                            // 08/11 (teste dele: "a chuva não cai"; as letrinhas do "Você sabe o que é salvação" paradas):
                            // a camada que é WebP ANIMADO toca, por cima da parada (1 quadro = não carrega nada)
                            AnimSlide {
                                x: -corte.x; y: -corte.y; width: pr.width; height: pr.height
                                fillMode: Image.Stretch
                                arquivo: raiz.previa ? "" : String(pm.c.src || "")     // só no telão (09/11)
                                largura: 0; tempo: cam.tempoFilme
                            }
                        }
                    }
                }
            }
        }
        // um efeito = espera o atraso, avisa que começou e anda p de 0 a 1 com a curva do PowerPoint
        Component {
            id: efeitoC
            SequentialAnimation {
                id: ef
                property real p: 0
                property int atraso: 0
                property int dur: 1
                property int curva: Easing.Linear
                property var bez: [0.42, 0, 0.58, 1, 1, 1]
                property var aoComecar: null
                property var aoAndar: null
                property bool comecou: false
                PauseAnimation { duration: ef.atraso }
                ScriptAction { script: { ef.comecou = true; if (ef.aoComecar) ef.aoComecar() } }
                NumberAnimation { target: ef; property: "p"; from: 0; to: 1; duration: ef.dur
                                  easing.type: ef.curva; easing.bezierCurve: ef.bez }
                onPChanged: if (comecou && aoAndar) aoAndar(p)
            }
        }
        Component {
            id: pulsoC          // NOSSO (pedido dele 11/10 17h21): o coração vermelho bate, sem parar
            SequentialAnimation {
                id: pu
                property var alvo
                property real e: 1.08
                property int meio: 550
                property int atraso: 0
                loops: 1
                PauseAnimation { duration: pu.atraso }
                SequentialAnimation {
                    loops: Animation.Infinite
                    NumberAnimation { target: pu.alvo; property: "pulso"; from: 1; to: pu.e; duration: pu.meio; easing.type: Easing.InOutQuad }
                    NumberAnimation { target: pu.alvo; property: "pulso"; from: pu.e; to: 1; duration: pu.meio; easing.type: Easing.InOutQuad }
                }
            }
        }
        function pararEfs() {
            esperaEntrar.stop()                  // o passo 0 que esperava a tela entrar não dispara depois de outro (07/11)
            for (var i = 0; i < efs.length; i++) { try { efs[i].a.stop(); efs[i].a.destroy() } catch (e) {} }
            efs = []
        }
        // clicou ANTES de a tela terminar de entrar (700 ms): o passo 0 (o que roda sozinho) fica completo na hora e o
        // clique pedido vem depois, na ordem. Antes o passo 0 tocava por cima do clique quando o relógio disparava.
        function garantirEntrada() {
            if (esperaEntrar.running) { esperaEntrar.stop(); tocarPasso(0, true) }
        }
        // clique no meio da animação anterior: ela termina na hora (o PowerPoint faz assim); o pulsar continua
        function terminarEfs() {
            var fica = []
            for (var i = 0; i < efs.length; i++) {
                var x = efs[i]
                if (x.infinito) { fica.push(x); continue }
                if (x.a.running) { x.a.stop(); if (!x.a.comecou && x.aoComecar) x.aoComecar(); if (x.aoAndar) x.aoAndar(1) }
                x.a.destroy()
            }
            efs = fica
        }
        function efeitosDoPasso(k) {
            var m = movAtual, out = (m.passos[k] || []).slice()
            var ex = m.extras || []
            for (var i = 0; i < ex.length; i++) if (ex[i].passo === k) out.push(ex[i])
            return out
        }
        function lerpCaminho(pts, p) {
            if (pts.length < 2) return pts[0] || [0, 0]
            var s = p * (pts.length - 1), i = Math.min(pts.length - 2, Math.floor(s)), f = s - i
            return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f]
        }
        readonly property var insetEntra: ({ up: "ciT", down: "ciB", left: "ciL", right: "ciR" })
        readonly property var insetSai: ({ up: "ciB", down: "ciT", left: "ciR", right: "ciL" })
        // cada efeito do PowerPoint vira: o que acontece ao começar, e como fica no ponto p (0..1)
        function regras(f, m) {
            var com = null, anda = null
            if (f.classe === "entr") {
                if (f.efeito === "esmaecer") { com = function() { m.vis = true; m.opacity = 0 }; anda = function(p) { m.opacity = p } }
                else if (f.efeito === "revelar") {
                    var lado = insetEntra[f.lado] || "ciT"
                    com = function() { m.vis = true; m.opacity = 1; m[lado] = 1 }; anda = function(p) { m[lado] = 1 - p }
                } else if (f.efeito === "voar") {
                    // 08/11 (CIAS 16:9): o "Voar para dentro" do PowerPoint: vem de fora (f.de, fração do slide) até o lugar
                    var de = f.de || [0, 0]
                    com = function() { m.vis = true; m.opacity = 1; m.tx = de[0]; m.ty = de[1] }
                    anda = function(p) { m.tx = de[0] * (1 - p); m.ty = de[1] * (1 - p) }
                } else if (f.efeito === "circulo" && !raiz.temPlaca) {
                    // sem placa (desenho por software) a máscara do MultiEffect some com a camada inteira: esmaecer
                    com = function() { m.vis = true; m.opacity = 0 }; anda = function(p) { m.opacity = p }
                } else if (f.efeito === "circulo") {
                    // 08/11 (CIAS 16:9): "in" = o círculo fecha das bordas ao centro (aparece o lado de fora dele);
                    // "out" = abre do centro (aparece o de dentro). No fim a máscara sai (circ -1: sem camada na placa)
                    var dentro = f.dir === "out"
                    com = function() { m.vis = true; m.opacity = 1; m.circDentro = dentro; m.circ = dentro ? 0 : 1 }
                    anda = function(p) { m.circ = p >= 1 ? -1 : (dentro ? p : 1 - p) }
                } else { com = function() { m.vis = true; m.opacity = 1 }; anda = function(p) {} }
            } else if (f.classe === "exit") {
                // sai = opacidade 0 a partir do fim do efeito
                if (f.efeito === "esmaecer") { anda = function(p) { m.opacity = 1 - p } }
                else if (f.efeito === "revelar") { var l2 = insetSai[f.lado] || "ciB"; anda = function(p) { m[l2] = p; if (p >= 1) m.opacity = 0 } }
                else if (f.efeito === "voar") { var at = f.ate || [0, 0]; anda = function(p) { m.tx = at[0] * p; m.ty = at[1] * p } }   // "Voar para fora"
                else anda = function(p) { if (p >= 1) m.opacity = 0 }
                var a0 = anda; anda = function(p) { a0(p); if (p >= 1) m.opacity = 0 }
            } else if (f.efeito === "girar") {
                var r0 = 0; com = function() { r0 = m.rot }; anda = function(p) { m.rot = r0 + (f.graus || 0) * p }
            } else if (f.efeito === "crescer") {
                var e = f.escala || [1, 1], x0 = 1, y0 = 1
                com = function() { x0 = m.sx; y0 = m.sy }
                anda = function(p) { m.sx = x0 * (1 + (e[0] - 1) * p); m.sy = y0 * (1 + (e[1] - 1) * p) }
            } else if (f.efeito === "caminho") {
                var pts = f.caminho && f.caminho.length ? f.caminho : [[0, 0]], bx = 0, by = 0
                com = function() { bx = m.tx; by = m.ty }
                anda = function(p) { var q = lerpCaminho(pts, p); m.tx = bx + q[0]; m.ty = by + q[1] }
            } else if (f.efeito === "pop") {
                var de = f.de || 0.85
                com = function() { m.popf = de }; anda = function(p) { m.popf = de + (1 - de) * p }
            }
            return { com: com, anda: anda }
        }
        function tocarPasso(k, direto) {
            if (!movAtual) return
            terminarEfs()
            passoAp = k
            var lista = efeitosDoPasso(k)
            for (var i = 0; i < lista.length; i++) {
                var f = lista[i], m = cams[f.alvo]
                if (!m) continue
                if (f.efeito === "pulsar") {
                    var pu = pulsoC.createObject(cam, { alvo: m, e: f.escala || 1.08, meio: Math.round((f.dur || 1100) / 2), atraso: direto ? 0 : (f.ini || 0) })
                    pu.start(); efs.push({ a: pu, infinito: true }); continue
                }
                var r = regras(f, m)
                if (direto) { if (r.com) r.com(); if (r.anda) r.anda(1); continue }
                var a = efeitoC.createObject(cam, { atraso: f.ini || 0, dur: Math.max(1, f.dur || 1), aoComecar: r.com, aoAndar: r.anda,
                    curva: f.efeito === "pop" || f.suave ? Easing.Bezier : Easing.Linear,
                    bez: f.efeito === "pop" ? [0.34, 1.56, 0.64, 1, 1, 1] : [0.42, 0, 0.58, 1, 1, 1] })
                efs.push({ a: a, aoComecar: r.com, aoAndar: r.anda, infinito: false })
                a.start()
            }
        }
        // monta o palco do zero no clique pedido: quem ENTRA em algum momento começa escondido; o resto, à vista
        function montarApres(passo, ms) {
            if (!movAtual) return
            pararEfs()
            zerarCamadas()
            var P = movAtual.passos
            var alvo = Math.max(0, Math.min(P.length - 1, passo | 0))
            if (alvo > 0) { for (var k = 0; k <= alvo; k++) tocarPasso(k, true); return }
            // o que roda sozinho começa quando a tela terminou de entrar (o PowerPoint espera a transição)
            passoAp = 0
            if (ms > 0) esperaEntrar.restart(); else tocarPasso(0, false)
        }
        // todas as camadas no começo do slide: quem ENTRA em algum momento escondida; o resto, à vista
        function zerarCamadas() {
            var primeiro = {}, P = movAtual.passos
            for (var a = 0; a < P.length; a++) for (var b = 0; b < P[a].length; b++) if (!(P[a][b].alvo in primeiro)) primeiro[P[a][b].alvo] = P[a][b].classe
            var mapa = {}
            for (var i = 0; i < repCam.count; i++) {
                var m = repCam.itemAt(i); if (!m) continue
                m.tx = 0; m.ty = 0; m.rot = 0; m.sx = 1; m.sy = 1; m.pulso = 1; m.popf = 1
                m.ciT = 0; m.ciB = 0; m.ciL = 0; m.ciR = 0; m.opacity = 1; m.circ = -1
                m.vis = !(m.c.id !== null && primeiro[m.c.id] === "entr")
                if (m.c.id !== null) mapa[m.c.id] = m
            }
            cams = mapa
        }
        // ---- A FILMAGEM (09/11, palavra dele: "você vai abolir as camadas de transparência"): cada clique vira um vídeo
        // feito AQUI, com as mesmas regras do telão. posar(passo, ms) = o slide EXATO no instante ms do clique 'passo'
        // (os anteriores completos), sem relógio nenhum; os quadros dos WebP animados também pelo tempo (AnimSlide.tempo).
        // Quem filma (ferramentas/filmar_movimento.py) chama, espera os quadros ficarem em dia e fotografa.
        property real tempoFilme: -1
        function bezierY(b, x) {            // a curva do PowerPoint (cubic-bezier p1=(b0,b1), p2=(b2,b3)) em x
            if (x <= 0) return 0; if (x >= 1) return 1
            var lo = 0, hi = 1, t = x
            for (var i = 0; i < 40; i++) {
                t = (lo + hi) / 2
                var bx = 3 * (1 - t) * (1 - t) * t * b[0] + 3 * (1 - t) * t * t * b[2] + t * t * t
                if (bx < x) lo = t; else hi = t
            }
            return 3 * (1 - t) * (1 - t) * t * b[1] + 3 * (1 - t) * t * t * b[3] + t * t * t
        }
        function pulsoEm(m, f, local) {     // o nosso pulsar (InOutQuad, ida e volta), parado em 'local' ms
            var meio = Math.max(1, Math.round((f.dur || 1100) / 2)), e = f.escala || 1.08
            var ph = local % (2 * meio), x = ph < meio ? ph / meio : 1 - (ph - meio) / meio
            var q = x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2
            m.pulso = 1 + (e - 1) * q
        }
        function posar(passo, ms) {
            if (!movAtual) return
            pararEfs()
            zerarCamadas()
            for (var k = 0; k < passo; k++) {
                var ant = efeitosDoPasso(k)
                for (var j = 0; j < ant.length; j++) {
                    var g = ant[j], mg = cams[g.alvo]; if (!mg) continue
                    if (g.efeito === "pulsar") { pulsoEm(mg, g, ms + 100000); continue }
                    var rg = regras(g, mg); if (rg.com) rg.com(); if (rg.anda) rg.anda(1)
                }
            }
            passoAp = passo
            var lista = efeitosDoPasso(passo).slice().sort(function(a, b) { return (a.ini || 0) - (b.ini || 0) })
            for (var i = 0; i < lista.length; i++) {
                var f = lista[i], m = cams[f.alvo]
                if (!m) continue
                var local = ms - (f.ini || 0)
                if (local < 0) continue
                if (f.efeito === "pulsar") { pulsoEm(m, f, local); continue }
                var r = regras(f, m), p = Math.min(1, local / Math.max(1, f.dur || 1))
                if (f.efeito === "pop") p = bezierY([0.34, 1.56, 0.64, 1], p)
                else if (f.suave) p = bezierY([0.42, 0, 0.58, 1], p)
                if (r.com) r.com(); if (r.anda) r.anda(p)
            }
            tempoFilme = ms
        }
        Timer { id: esperaEntrar; interval: cerebroFade; onTriggered: if (cam.movAtual) cam.tocarPasso(0, false) }
        readonly property int cerebroFade: 700

        // ---- texto do louvor. Sombra: o próprio Text do Qt (style Raised), que desenha em qualquer placa; o efeito
        // MultiEffect sumia com a letra inteira no desenho sem tela (medido 03/11 11h10), e telão sem letra não pode.
        // ---- RELÓGIO e CRONÔMETRO (#grande do projecao.html): número Bebas 24% da altura, rótulo dourado espaçado em cima
        Column {
            anchors.centerIn: parent
            visible: cam.modo === "relogio" || cam.modo === "timer"
            spacing: cam.lh * 0.026
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: text !== ""
                text: cam.modo === "relogio" ? cam.dataHoje : (cam.t.rotulo || "")
                color: "#f5d76e"; opacity: 0.93; font.family: "Outfit"; font.weight: Font.Medium
                font.pixelSize: cam.lh * 0.036; font.letterSpacing: cam.lh * 0.036 * 0.42; font.capitalization: Font.AllUppercase
                style: Text.Raised; styleColor: "#99000000"
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: cam.modo === "relogio" ? cam.horaAgora : cam.textoTimer
                color: "white"; font.family: "Bebas Neue"; font.pixelSize: cam.lh * 0.24; font.letterSpacing: 2
                style: Text.Raised; styleColor: "#cc000000"
            }
        }
        property string horaAgora: ""
        property string dataHoje: ""
        property string textoTimer: ""
        Timer {
            interval: 250; repeat: true; triggeredOnStart: true
            running: cam.modo === "relogio" || cam.modo === "timer"
            onTriggered: {
                var d = new Date()
                if (cam.modo === "relogio") {
                    var DIAS = ["DOMINGO","SEGUNDA-FEIRA","TERÇA-FEIRA","QUARTA-FEIRA","QUINTA-FEIRA","SEXTA-FEIRA","SÁBADO"]
                    var MES = ["JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO","JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"]
                    cam.dataHoje = DIAS[d.getDay()] + " · " + d.getDate() + " DE " + MES[d.getMonth()] + " DE " + d.getFullYear()
                    cam.horaAgora = ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2)
                } else if (cam.t.parado) {          // pausado: o tempo que faltava, parado (o "parado"/"texto" da 3.0.13)
                    cam.textoTimer = cam.t.texto || "0:00"
                } else {
                    var s = Math.max(0, Math.round((cam.t.fimTs - d.getTime()) / 1000))
                    cam.textoTimer = Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2)
                }
            }
        }

        // ---- AVISO / TEXTO LIVRE (#livre): título amarelo (entre \x01), corpo branco centrado, cresce até 1,15x
        Item {
            id: caixaLivre
            visible: cam.modo === "texto"
            x: cam.lw * 0.09; width: cam.lw * 0.82
            y: cam.lh * (cam.t.zona === "barra" ? 0.22 : 0.10); height: cam.lh * (cam.t.zona === "barra" ? 0.72 : 0.80)
            property real px: 20
            Column {
                id: colLivre
                width: parent.width
                anchors.verticalCenter: parent.verticalCenter
                spacing: caixaLivre.px * 0.22
                Repeater {
                    id: repLivre
                    model: 24                                  // itens fixos (ver o louvor, mais abaixo)
                    Text {
                        readonly property var linha: cam.modo === "texto" && cam.t.linhas && index < cam.t.linhas.length ? String(cam.t.linhas[index]) : null
                        visible: linha !== null
                        readonly property bool titulo: linha !== null && linha.indexOf("\x01") >= 0
                        width: colLivre.width
                        text: linha === null ? "" : (titulo ? linha.split("\x01").join("") : linha)
                        color: titulo ? "#ffff00" : "white"
                        font.family: "Outfit"; font.weight: titulo ? Font.Black : Font.Bold
                        font.pixelSize: caixaLivre.px * (titulo ? 1.25 : 1); font.letterSpacing: titulo ? 1 : caixaLivre.px * 0.005
                        bottomPadding: titulo ? caixaLivre.px * 0.42 : 0
                        wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter
                        style: Text.Raised; styleColor: "#cc000000"
                    }
                }
            }
        }

        // ---- CIFRA no telão (o ensaio do grupo, #cifra-tela do projecao.html): o título no lugar do título do louvor
        // (Bebas 6,4% #fff3a3), os pares acorde+letra em fonte MONOESPAÇADA (a coluna do acorde É o caractere), 3,05% da
        // altura, entrelinha 1,32, negrito branco com sombra, acorde #ffd75e; caixa 12%/6%/6%/6%; "1 de 3" no canto.
        Item {
            anchors.fill: parent
            id: caixaCif
            visible: cam.modo === "cifra"
            readonly property real px: cam.lh * 0.0305
            Text {
                x: cam.lw * 0.145; width: cam.lw * 0.84; y: cam.lh * 0.022; height: cam.lh * 0.145
                text: cam.modo === "cifra" ? (cam.t.titulo || "") : ""
                color: "#fff3a3"; font.family: "Bebas Neue"; font.pixelSize: cam.lh * 0.064; font.letterSpacing: 0.3
                font.capitalization: Font.AllUppercase; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                style: Text.Raised; styleColor: "#99000000"; clip: true
            }
            Item {
                x: cam.lw * 0.06; y: cam.lh * 0.12; width: cam.lw * 0.88; height: cam.lh * 0.82; clip: true
                Column {
                    Repeater {
                        model: 8                                // itens fixos: os 8 pares da página (ver o louvor)
                        Column {
                            readonly property var par: cam.modo === "cifra" && cam.t.pares && index < cam.t.pares.length ? cam.t.pares[index] : ["", ""]
                            visible: cam.modo === "cifra" && !!cam.t.pares && index < cam.t.pares.length
                            Text {
                                visible: !!parent.par[0]; height: visible ? caixaCif.px * 1.32 : 0
                                text: parent.par[0]; color: "#ffd75e"; textFormat: Text.PlainText
                                font.family: typeof fonteMono !== "undefined" ? fonteMono : "Consolas"; font.bold: true
                                font.pixelSize: caixaCif.px; verticalAlignment: Text.AlignVCenter
                                style: raiz.sombra ? Text.Raised : Text.Normal; styleColor: "#aa000000"
                            }
                            Text {
                                height: caixaCif.px * 1.32
                                text: parent.par[1]; color: "white"; textFormat: Text.PlainText
                                font.family: typeof fonteMono !== "undefined" ? fonteMono : "Consolas"; font.bold: true
                                font.pixelSize: caixaCif.px; verticalAlignment: Text.AlignVCenter
                                style: raiz.sombra ? Text.Raised : Text.Normal; styleColor: "#aa000000"
                            }
                        }
                    }
                }
            }
            Text {
                anchors { right: parent.right; rightMargin: cam.lw * 0.026; bottom: parent.bottom; bottomMargin: cam.lh * 0.024 }
                text: cam.modo === "cifra" ? (cam.t.pag || "") : ""
                color: "white"; opacity: 0.8; font.family: "Outfit"; font.bold: true; font.pixelSize: cam.lh * 0.026
            }
        }

        // ---- BÍBLIA (estilo limpo): referência dourada na faixa (2,2%..16,7%), versículo em itálico de 22% a 96%
        Item {
            anchors.fill: parent
            visible: cam.modo === "biblia"
            Text {
                y: cam.lh * (cam.mapa ? 0.165 : 0.022); height: cam.lh * (cam.mapa ? 0.10 : 0.145); width: cam.lw
                text: cam.t.ref || ""; color: "#f5d76e"; font.family: "Bebas Neue"; font.pixelSize: cam.lh * 0.069
                font.letterSpacing: 0.3; font.capitalization: Font.AllUppercase
                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                style: Text.Raised; styleColor: "#99000000"
            }
            Item {
                id: caixaBib
                x: cam.lw * 0.055; width: cam.lw * 0.89
                y: cam.lh * (cam.mapa ? 0.275 : 0.22); height: cam.lh * (cam.mapa ? 0.70 : 0.74)
                property real px: 20
                // ESCOLHA DELE (03/11 11h32, vendo lado a lado com a 3.0.12): o versículo em ITÁLICO e com mais respiro
                // entre as linhas, "muito mais clara", e "um pouquinho mais de sombrinha no fundo da letra".
                // A sombra é uma cópia preta da letra, um tico abaixo (desenha em qualquer placa, custo de um texto a mais).
                Text {
                    id: bibSombra
                    x: bibTxt.x + Math.max(1, cam.lh * 0.0015); y: bibTxt.y + Math.max(2, cam.lh * 0.0042)
                    width: bibTxt.width
                    transform: Scale { yScale: 1.06; origin.y: bibTxt.implicitHeight / 2 }
                    text: bibTxt.text; color: "black"; opacity: 0.62
                    font: bibTxt.font; wrapMode: bibTxt.wrapMode; horizontalAlignment: bibTxt.horizontalAlignment
                    lineHeightMode: bibTxt.lineHeightMode; lineHeight: bibTxt.lineHeight
                }
                Text {
                    id: bibTxt
                    width: caixaBib.width
                    y: (caixaBib.height - implicitHeight * 1.06) / 2 + implicitHeight * 0.03
                    transform: Scale { yScale: 1.06; origin.y: bibTxt.implicitHeight / 2 }
                    text: (cam.t.linhas || []).join("\n")
                    color: "white"; font.family: "Outfit"; font.weight: Font.Bold; font.italic: true
                    font.pixelSize: caixaBib.px; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter
                    font.letterSpacing: caixaBib.px * 0.005; font.wordSpacing: caixaBib.px * 0.018
                    lineHeight: 1.3
                }
            }
        }

        // ---- VÁRIOS VERSÍCULOS JUNTOS (o #bib-multi da 3.0.12): cada um com a referência dourada em cima e o texto branco
        // em itálico, alinhados à esquerda num bloco centrado. A 3.0.12 usa a tela de 6% a 96%, e com muitos versículos a
        // letra subia por cima da faixa "TEXTO BÍBLICO"; aqui a caixa começa abaixo da faixa (17,5% a 96%; mapa 28% a 97%).
        // Os espaçamentos são os da 3.0.12 em em (1,18 entre linhas, 0,5 entre versículos, o A+ aperta os dois).
        // UM Text só (rich text): Text recriado por Repeater vaza no Qt 6.12 (reference_qt612_repeater_vaza).
        Item {
            id: caixaMulti
            anchors.fill: parent
            visible: cam.modo === "bibmulti"
            property real px: 20
            readonly property real es: Math.max(1, cam.t.escala || 1)
            readonly property real bx: cam.lw * 0.05
            readonly property real bw: cam.lw * 0.91
            readonly property real by: cam.lh * (cam.mapa ? 0.28 : 0.175)
            readonly property real bh: cam.lh * (cam.mapa ? 0.69 : 0.785)
            // no rich text do Qt, line-height em % é da altura NATURAL da linha da fonte (~1,26 em na Outfit), não do
            // tamanho da letra como no navegador: converte o em da 3.0.12 pela medida da própria fonte
            FontMetrics { id: fmMulti; font.family: "Outfit"; font.weight: Font.Bold; font.italic: true; font.pixelSize: 100 }
            function pct(em) { return Math.round(em * 100 / fmMulti.height * 100) }
            function esc(s) { return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") }
            function html(px, sombra) {
                if (cam.modo !== "bibmulti") return ""
                var lh = Math.max(1.04, 1.18 / Math.pow(es, 0.6)), gap = Math.max(0.2, 0.5 / Math.pow(es, 1.5)) * px
                var ouro = sombra ? "#000000" : "#f5d76e", br = sombra ? "#000000" : "#ffffff"
                var it = cam.t.itens || [], h = ""
                for (var i = 0; i < it.length; i++) {
                    h += '<p style="margin-top:' + (i === 0 ? 0 : Math.round(gap)) + 'px; margin-bottom:0px; line-height:' + pct(1.1) + '%">'
                       + '<span style="color:' + ouro + '; font-weight:900; font-style:normal">' + esc(it[i].ref) + '</span></p>'
                       + '<p style="margin-top:' + Math.round(px * 0.05) + 'px; margin-bottom:0px; line-height:' + pct(lh) + '%">'
                       + '<span style="color:' + br + '; font-style:italic">' + esc(it[i].texto) + '</span></p>'
                }
                return h
            }
            Text {
                id: multiSombra
                x: multiTxt.x + Math.max(1, cam.lh * 0.0015); y: multiTxt.y + Math.max(2, cam.lh * 0.0042)
                width: multiTxt.width
                transform: Scale { yScale: 1.06; origin.y: multiTxt.implicitHeight / 2 }
                textFormat: Text.RichText; text: caixaMulti.html(caixaMulti.px, true); opacity: 0.62
                font: multiTxt.font; wrapMode: Text.WordWrap
            }
            Text {
                id: multiTxt
                objectName: "multiTxt"
                width: caixaMulti.bw
                // o bloco tem a largura da linha mais comprida e fica no meio (flex centrado da 3.0.12); dentro, à esquerda
                x: caixaMulti.bx + Math.max(0, (caixaMulti.bw - contentWidth) / 2)
                y: caixaMulti.by + (caixaMulti.bh - implicitHeight * 1.06) / 2 + implicitHeight * 0.03
                transform: Scale { yScale: 1.06; origin.y: multiTxt.implicitHeight / 2 }
                textFormat: Text.RichText; text: caixaMulti.html(caixaMulti.px, false)
                color: "white"; font.family: "Outfit"; font.weight: Font.Bold
                font.pixelSize: caixaMulti.px; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignLeft
                font.letterSpacing: caixaMulti.px * 0.005; font.wordSpacing: caixaMulti.px * 0.018
            }
        }

        Item {
            id: textos
            anchors.fill: parent
            visible: cam.modo === "louvor"
            layer.enabled: raiz.sombraPlaca
            layer.effect: MultiEffect {
                shadowEnabled: true; shadowColor: "#000000"; shadowOpacity: 0.78
                shadowHorizontalOffset: 0; shadowVerticalOffset: 2; blurMax: 16; shadowBlur: 1.0
            }

            // TÍTULO (só na 1a tela): "69 / 9990 | TÍTULO" no Glorifica dourado
            Item {
                id: caixaTit
                visible: !!cam.t.titulo
                x: cam.lw * (cam.mapa ? 0.135 : 0.145); y: cam.lh * (cam.mapa ? 0.03 : 0.022)
                width: cam.lw * (1 - (cam.mapa ? 0.135 : 0.145) - 0.015); height: cam.lh * (cam.mapa ? 0.09 : 0.145)
                property real px: cam.lh * 0.064
                Row {
                    id: linhaTit
                    anchors.verticalCenter: parent.verticalCenter
                    x: (caixaTit.width - width) / 2 + caixaTit.recuo
                    spacing: 0
                    Text { visible: !!cam.t.num1; text: cam.t.num1 || ""; color: "#f5d76e"; style: raiz.sombraPlaca ? Text.Normal : Text.Raised; styleColor: "#99000000"; font.family: "Bebas Neue"; font.pixelSize: caixaTit.px; font.letterSpacing: 0.3 }
                    Text { visible: !!cam.t.num2; text: "/"; color: "#f5d76e"; opacity: 0.85; style: raiz.sombraPlaca ? Text.Normal : Text.Raised; styleColor: "#99000000"; font.family: "Bebas Neue"; font.pixelSize: caixaTit.px; leftPadding: caixaTit.px * 0.06; rightPadding: caixaTit.px * 0.06 }
                    Text { visible: !!cam.t.num2; text: cam.t.num2 || ""; color: "#fff3a3"; opacity: 0.8; style: raiz.sombraPlaca ? Text.Normal : Text.Raised; styleColor: "#99000000"; font.family: "Bebas Neue"; font.pixelSize: caixaTit.px; font.letterSpacing: 0.3 }
                    Item { visible: !!cam.t.num1; width: caixaTit.px * 1.06; height: caixaTit.px
                           Rectangle { anchors.centerIn: parent; width: Math.max(1, caixaTit.px * 0.06); height: caixaTit.px * 0.9; color: "#f5d76e"; opacity: 0.7 } }
                    Text { text: (cam.t.num1 ? cam.t.tituloSo : cam.t.titulo) || ""; color: "#fff3a3"; style: raiz.sombraPlaca ? Text.Normal : Text.Raised; styleColor: "#99000000"; font.family: "Bebas Neue"; font.pixelSize: caixaTit.px; font.letterSpacing: 0.3; font.capitalization: Font.AllUppercase }
                }
                property real recuo: 0
            }

            // LETRA
            Item {
                id: caixaLou
                x: cam.lw * 0.055; width: cam.lw * 0.89
                y: cam.lh * (cam.t.titulo ? (cam.mapa ? 0.16 : 0.18) : 0.09)
                height: cam.lh * (cam.t.titulo ? (cam.mapa ? 0.78 : 0.76) : 0.82)
                Column {
                    id: bloco
                    x: caixaLou.width * 0.152
                    width: caixaLou.width * 0.76
                    y: (caixaLou.height - height * 1.06) / 2 + height * 0.03
                    transform: Scale { yScale: 1.06; origin.y: bloco.height / 2 }
                    property real px: 20
                    property real lh: 1.815
                    Text {
                        id: rotulo
                        visible: text !== ""
                        text: cam.textoRotulo()
                        color: "#ffff00"; font.family: "Outfit"; font.weight: Font.Bold; font.italic: true
                        font.pixelSize: bloco.px * 0.72; font.letterSpacing: 1
                        bottomPadding: bloco.px * 0.12
                    }
                    // ITENS FIXOS (05/11/2026): Repeater com "model: lista" recria os Text a cada tela, e no Qt 6.12 cada
                    // Text recriado deixa memória para trás (medido: +5 MB a cada 40 telas, sem parar). Com 16 itens
                    // fixos só o texto muda: 0 MB. O slide mais comprido do acervo tem 6 linhas (medido 05/11).
                    Repeater {
                        id: rep
                        model: 16
                        Text {
                            readonly property var linha: cam.modo === "louvor" && cam.t.linhas && index < cam.t.linhas.length ? cam.t.linhas[index] : null
                            visible: linha !== null
                            width: bloco.width
                            text: linha !== null ? cam.marcar(linha) : ""
                            textFormat: Text.StyledText
                            color: "white"; font.family: "Outfit"; font.weight: Font.Bold
                            font.pixelSize: bloco.px; font.letterSpacing: bloco.px * 0.005; font.wordSpacing: bloco.px * 0.018
                            font.capitalization: Font.AllUppercase
                            wrapMode: Text.WordWrap
                            style: raiz.sombraPlaca ? Text.Normal : Text.Raised; styleColor: "#99000000"
                            lineHeightMode: Text.FixedHeight; lineHeight: bloco.px * bloco.lh
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }
            Text {
                visible: !!cam.t.fim && (cam.t.linhas || []).length > 0
                text: "fim"; color: "white"; opacity: 0.72
                font.family: "Outfit"; font.weight: Font.Bold; font.pixelSize: cam.lh * 0.034; font.letterSpacing: 0.5
                anchors.right: parent.right; anchors.rightMargin: cam.lw * 0.026
                anchors.bottom: parent.bottom; anchors.bottomMargin: cam.lh * 0.024
            }
        }

        // ---- regras do projecao.html
        function textoRotulo() {
            var l = t.label || "", s = t.selo || ""
            if (!l && !s) return ""
            var vezes = s === "bis" ? "2x" : s
            if (s === "hino") return (l ? l + " · " : "") + "repete o hino"
            if (l && s) return l + " " + vezes
            if (l) return l
            return "cantar " + vezes
        }
        function marcar(str) {        // trechos entre \x01 saem AMARELOS
            var p = String(str).split("\x01"), out = ""
            for (var i = 0; i < p.length; i++) {
                var x = p[i].replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
                out += (i % 2) ? "<font color=\"#ffff00\">" + x + "</font>" : x
            }
            return out
        }
        function avanco(e) { e = e || 1; return e <= 1 ? 1.815 : Math.max(1.5, 1.815 / Math.pow(e, 0.55)) }
        // a Column só se reorganiza depois; o Text se mede na hora. Então a altura é a SOMA dos textos.
        function alturaBloco() {
            var h = rotulo.visible ? rotulo.implicitHeight : 0
            for (var i = 0; i < rep.count; i++) { var it = rep.itemAt(i); if (it && it.visible) h += it.implicitHeight }
            return h
        }
        function larguraTitulo() {
            var w = 0, ch = linhaTit.children
            for (var i = 0; i < ch.length; i++) if (ch[i].visible) w += ch[i].width
            return w
        }
        function cabe() {
            if (alturaBloco() * 1.06 - caixaLou.height > 1) return false
            for (var i = 0; i < rep.count; i++) { var it = rep.itemAt(i); if (it && it.visible && it.contentWidth - bloco.width > 1) return false }
            return true
        }
        function ajustar() {
            if (modo === "texto") {              // cabe na caixa; aviso curto cresce até 1,15x (nunca vira letreiro)
                var tb = Math.max(6, (t.tam || 6) / 100 * lh * (t.escala || 1))
                var altL = function() { var h = 0; for (var q = 0; q < repLivre.count; q++) { var it = repLivre.itemAt(q); if (it && it.visible) h += it.implicitHeight + colLivre.spacing } return h }
                caixaLivre.px = tb
                if (altL() > caixaLivre.height) {
                    var tlo = 6, thi = tb
                    for (var tk = 0; tk < 16 && thi - tlo > 0.5; tk++) { var tm = (tlo + thi) / 2; caixaLivre.px = tm; if (altL() <= caixaLivre.height) tlo = tm; else thi = tm }
                    caixaLivre.px = tlo
                } else {
                    for (var tg = 0; tg < 18; tg++) {
                        var tt = caixaLivre.px * 1.06; if (tt > tb * 1.15) break
                        caixaLivre.px = tt
                        var quebrou = false
                        for (var qq = 0; qq < repLivre.count; qq++) { var li2 = repLivre.itemAt(qq); if (li2 && li2.visible && li2.lineCount > 1) quebrou = true }
                        if (altL() > caixaLivre.height || quebrou) { caixaLivre.px = tt / 1.06; break }
                    }
                }
                return
            }
            if (modo === "biblia") {             // o MAIOR tamanho até o pedido que cabe na caixa (bissecção)
                var bb = Math.max(6, (t.tam || 5.55) / 100 * lh * (t.escala || 1))
                caixaBib.px = bb
                if (bibTxt.implicitHeight * 1.06 > caixaBib.height) {
                    var blo = 6, bhi = bb
                    for (var bk = 0; bk < 16 && bhi - blo > 0.5; bk++) {
                        var bm = (blo + bhi) / 2; caixaBib.px = bm
                        if (bibTxt.implicitHeight * 1.06 <= caixaBib.height) blo = bm; else bhi = bm
                    }
                    caixaBib.px = blo
                }
                return
            }
            if (modo === "bibmulti") {           // o maior tamanho até o pedido que cabe (fit do #bib-multi); nunca corta
                var mb = Math.max(6, (t.tam || 5.55) / 100 * lh * (t.escala || 1))
                caixaMulti.px = mb
                if (multiTxt.implicitHeight * 1.06 > caixaMulti.bh) {
                    var mlo = 6, mhi = mb
                    for (var mk = 0; mk < 16 && mhi - mlo > 0.5; mk++) {
                        var mm = (mlo + mhi) / 2; caixaMulti.px = mm
                        if (multiTxt.implicitHeight * 1.06 <= caixaMulti.bh) mlo = mm; else mhi = mm
                    }
                    caixaMulti.px = mlo
                }
                return
            }
            if (modo !== "louvor") return
            var esc = t.escala || 1
            bloco.lh = avanco(esc)
            var base = Math.max(6, (t.tam || 5.75) / 100 * lh * esc)
            if (t.linhasRef > 0) {
                var teto = caixaLou.height / (t.linhasRef * bloco.lh) * esc
                if (teto < base) base = Math.max(6, teto)
            }
            for (var r = 0; r < rep.count; r++) { var li = rep.itemAt(r); if (li) li.width = bloco.width }
            bloco.px = base
            if (!cabe()) {                       // o MAIOR tamanho que cabe (bissecção), nunca corta
                var lo = 6, hi = base
                for (var k = 0; k < 16 && hi - lo > 0.5; k++) {
                    var meio = (lo + hi) / 2; bloco.px = meio
                    if (cabe()) lo = meio; else hi = meio
                }
                bloco.px = lo
            }
            // PALAVRA SOLTA (o text-wrap:balance do projecao.html): a linha que quebra em N pedaços fica com a MENOR
            // largura que ainda dá N pedaços, e as metades saem parelhas em vez de uma palavra sozinha embaixo.
            for (var j = 0; j < rep.count; j++) {
                var x = rep.itemAt(j); if (!x || !x.visible || x.lineCount < 2) continue
                var n0 = x.lineCount, a = bloco.width * 0.3, b = bloco.width
                for (var q = 0; q < 14 && b - a > 1; q++) {
                    var m = (a + b) / 2; x.width = m
                    if (x.lineCount > n0) a = m; else b = m
                }
                x.width = b
            }
            // título: não começa antes de 34,8% da largura (a ponta da etiqueta LOUVOR; no mapa 16,1%) nem passa de 98,5%
            caixaTit.px = lh * 0.064; caixaTit.recuo = 0
            var titMin = mapa ? 0.161 : 0.348
            for (var n = 0; n < 30 && t.titulo; n++) {
                var lw2 = larguraTitulo()
                var esq = caixaTit.x + (caixaTit.width - lw2) / 2
                var falta = titMin * lw - esq
                caixaTit.recuo = falta > 0 ? falta : 0
                var dir = esq + caixaTit.recuo + lw2
                if (raiz.depurar) console.log("DEP tit n=" + n + " lw=" + lw + " larg=" + lw2 + " esq=" + esq + " dir=" + dir + " px=" + caixaTit.px)
                if (dir <= 0.985 * lw) break
                caixaTit.px *= 0.96
            }
        }
        onLwChanged: Qt.callLater(ajustar)
        onLhChanged: Qt.callLater(ajustar)
    }
}
