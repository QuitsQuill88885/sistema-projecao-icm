// O PAINEL do operador (Sistema Nativo), 1:1 com o index.html da 3.0.13 (07/11/2026, ordem dele: "idêntico, de nem eu
// reparar"): o <header> (Cabecalho.qml), o #conteudo com as 7 abas e o <aside id="painel"> da direita (PainelDireito.qml).
// Medidas, cores, cantos, sombras e letra: o app.css convertido (Tema.js, ferramentas/conversor_312.py).
// O TELÃO é a janela "telao" aqui dentro; o Python põe ela na 2a tela (ou deixa em janela).
// Teclado (nas duas janelas): → / PageDown / espaço = próxima; ← / PageUp = anterior; Esc = tela de espera; Ctrl+B = preta.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Dialogs
import QtQuick.Shapes
import "Tema.js" as T

ApplicationWindow {
    id: painel
    // cabe na tela do operador (o PC de casa tem 800x600; PC de igreja 1024x768): nada fica para fora da janela
    // 08/11: o tamanho e o lugar da 3.0.x (janela_312 no Python); sem ele (provas que montam o QML sozinhas), o de antes
    width: typeof janelaInicial !== "undefined" ? janelaInicial.w : Math.min(1280, Screen.desktopAvailableWidth)
    height: typeof janelaInicial !== "undefined" ? janelaInicial.h : Math.min(760, Screen.desktopAvailableHeight - 30)
    x: typeof janelaInicial !== "undefined" ? janelaInicial.x : 0
    y: typeof janelaInicial !== "undefined" ? janelaInicial.y : 0
    // foraDaTela (testes no Vaio) e a tela de carregamento: quem mostra é o Python (sem preto, sem pular de lugar)
    visible: !modoFotos && !foraDaTela && !(typeof painelEsperaCarregando !== "undefined" && painelEsperaCarregando)
    title: "Sistema"
    color: T.V.fundo

    property int aba: 0                  // Louvor, Bíblia, Timer, Relógio, Texto, Apresentações, Fundos (a ordem do <nav>)
    // as provas antigas trocam a aba por "abas".currentIndex (0 telas, 1 fundos, 2 apresentações)
    QtObject { objectName: "abas"; property int currentIndex: 0; onCurrentIndexChanged: painel.aba = [0, 6, 5][currentIndex] || 0 }
    property int escolhido: -1          // o louvor aberto na coluna do meio
    property var resultados: []

    // a CIFRA aberta (abrirCifra/fecharCifra do app.js): o louvor, o tom escolhido e o tamanho da letra da folha
    property bool cifraAberta: false
    property int cifraIdx: -1
    property int cifraDesloc: 0          // semitons acima/abaixo do impresso (só desta folha; o telão leva junto)
    property int cifraFonte: controle.cifraFonteSalva()   // gravado (icm_cifra_fonte), como na 3.0.12
    property var folha: ({})
    property var tons: []
    property bool tonsAbertos: false
    property int larguraFolha: 0         // a linha mais comprida, em caracteres (a folha rola de lado se não couber)
    property string folhaHtml: ""        // a folha inteira num texto só (StyledText): acorde dourado, Coro/bis/Introdução pintados
    property var folhaMarcas: []         // os tracinhos do ritmo: [[ponto de cima, ponto de baixo], ...]
    property int folhaLinhas: 0          // quantas linhas a folha desenha (acordes + letra)
    function abrirCifra(i) { cifraIdx = i; cifraDesloc = 0; tonsAbertos = false; cifraAberta = true; redesenharCifra(); cifraFolha.lista.contentY = 0 }
    function escF(t) { return String(t).split("&").join("&amp;").split("<").join("&lt;").split(">").join("&gt;").split(" ").join("&nbsp;") }
    function montarFolha() {
        var L = folha.linhas || [], linhas = [], marcas = [], m = 0
        var lin = cifraFonte * 1.45, cw = cifraFolha.fm.advanceWidth("M"), alto = cifraFonte * 1.05
        for (var k = 0; k < L.length; k++) {
            var l = L[k]
            m = Math.max(m, l.ac.length, l.t.length)
            if (l.ac !== "") linhas.push("<font color=\"#f5d76e\"><b>" + escF(l.ac) + "</b></font>")
            var t = l.tipo === "rot" ? escF(l.t.toUpperCase()) : escF(l.t)
            // .folha .rot{font-weight:700;letter-spacing:.08em;text-transform:uppercase} (o espaço faltava, 08/11)
            if (l.tipo === "rot") t = "<span style='letter-spacing:" + (cifraFonte * 0.08).toFixed(2) + "px'><font color=\"#f5d76e\"><b>" + t + "</b></font></span>"
            else if (l.tipo === "intro") t = "<font color=\"#79c0ff\"><i>" + t + "</i></font>"
            else if (l.tipo === "rep") t = "<font color=\"#f5d76e\"><i>" + t + "</i></font>"
            var y0 = linhas.length * lin + (lin - alto) / 2
            for (var j = 0; j < l.tr.length; j++) {
                var x = Math.round(cw * l.tr[j]) - 0.5
                marcas.push([Qt.point(x, y0), Qt.point(x, y0 + alto)])
            }
            linhas.push(t === "" ? "&nbsp;" : t)
        }
        larguraFolha = m; folhaLinhas = linhas.length
        folhaHtml = linhas.join("<br>"); folhaMarcas = marcas
    }
    onCifraFonteChanged: { controle.guardarCifraFonte(cifraFonte); if (cifraAberta) montarFolha() }   // A−/A+ grava e refaz os tracinhos
    function redesenharCifra() {
        // trocar de tom no meio do 3º verso não volta a folha para o começo (o redesenhar do app.js guarda o lugar)
        var y = cifraFolha.lista.contentY
        folha = controle.folhaCifra(cifraIdx, cifraDesloc); tons = controle.tonsCifra(cifraIdx, cifraDesloc)
        montarFolha()
        cifraFolha.lista.contentY = y
    }
    function fecharCifra() { cifraAberta = false; tonsAbertos = false; folha = ({}); tons = []; folhaHtml = ""; folhaMarcas = [] }   // solta a folha da memória
    // com a folha aberta e o slide passando, o louvor vira: a folha acompanha (seguirCifraDoSlide). Louvor sem cifra
    // não apaga a folha: o operador pode estar lendo de propósito enquanto projeta um versículo.
    Connections {
        target: controle
        function onMudou() {
            var i = controle.idxNoAr
            if (painel.cifraAberta && i >= 0 && i !== painel.cifraIdx && controle.temCifra(i)) { abrirCifra(i) }
        }
    }
    // a lista da esquerda (renderListaLouvores): vazia = todas, agrupadas; refeita quando a lista do culto muda (o ♪)
    property var listaLouvores: controle.listaLouvores("")
    // um louvor do operador entrou, mudou ou saiu (Configurações › Meus louvores): a lista se refaz com a mesma busca
    Connections { target: controle; function onAcervoMudou() { painel.listaLouvores = controle.listaLouvores(painel.textoBusca) } }
    property string textoBusca: ""
    function buscar(q) { textoBusca = q; listaLouvores = controle.listaLouvores(q) }
    function abrir(i) { escolhido = i; telasDoLouvor = controle.telasLouvor(i) }
    property var telasDoLouvor: []
    property var fila: controle.itensLista()
    property string louvoresNaFila: ""
    // o que muda as grades de fundo: só quando MUDA DE VALOR (o controle avisa "mudou" a cada clique; recarregar a galeria
    // e os fundos lisos ali custava tempo em todo clique, medido na prova_retorno)
    property string estiloAtual: controle.nomeEstilo
    property int escondidosAtual: controle.fundosEscondidos

    Connections {
        target: controle
        function onTela(t) { palcoTelao.mostrar(t); previa.mostrar(t); if (retornoJanela.visible) palcoRet.mostrar(t); if (controle.telaoApoio) retTelao.mostrar(t) }
        function onIdentificar(n, rotulo) { identNum.n = n; identNum.rotulo = rotulo; identNum.opacity = 1; identFim.restart() }
        function onEscolhido(i) { abrir(i) }
        function onPrevia(t) { previa.mostrar(t) }
        function onAviso(m) { toast.mostrar(m) }
        function onFilaMudou() {
            painel.fila = controle.itensLista()
            // a lista da esquerda só muda o ♪ quando ENTRA ou SAI um louvor: o slide da apresentação avisa a fila a cada
            // clique, e refazer os 1.854 louvores ali custava ~30 ms por clique (medido, prova_retorno)
            var k = painel.fila.filter(function (x) { return x.tipo === "louvor" }).map(function (x) { return x.rotulo }).join("|")
            if (k !== painel.louvoresNaFila) { painel.louvoresNaFila = k; painel.listaLouvores = controle.listaLouvores(painel.textoBusca) }
        }
    }

    // ---------------- o <header>
    // o FUNDO DO APP (o cabeçalho, o conteúdo, o painel da direita e a folha da cifra): um pai comum, do tamanho da
    // janela, para o véu das boas-vindas poder DESFOCAR o que está atrás (o backdrop-filter:blur(3px) da 3.0.13)
    Item {
    id: fundoApp
    anchors.fill: parent
    Cabecalho {
        id: cab
        width: parent.width; z: 2
        aba: painel.aba
        igreja: controle.igreja
        nomeEstilo: controle.nomeEstilo
        mostrarEstilo: !(painel.aba === 5 && controle.apresAberta !== "")      // body.modo-apr #btn-estilo{display:none}
        pilula: controle.pilula === "on" ? "on" : (controle.pilula === "reconectando" ? "reconectando" : (controle.pilula !== "" ? "conectar" : ""))
        pilulaTexto: controle.pilulaTexto
        onEscolheu: (i) => painel.aba = i
        onEstilo: controle.trocarEstilo()
        onPilulaClique: controle.pilulaClique()
        onMenu: painel.pegar(menuCfgL).abrirComIgreja()
    }

    // ---------------- o #conteudo (esquerda, muda por aba)
    Item {
        id: conteudo
        y: cab.height; width: parent.width - painelDir.width; height: parent.height - y
        clip: true
        // LOUVOR
        ViewLouvor {
            id: vLouvor
            anchors.fill: parent; visible: painel.aba === 0
            lista: painel.listaLouvores
            escolhido: painel.escolhido
            titulo: painel.escolhido >= 0 ? controle.tituloLouvor(painel.escolhido) : "Slides do louvor"
            telas: painel.telasDoLouvor
            telaNoAr: painel.escolhido === controle.idxNoAr && controle.vivoTipo === "louvor" ? controle.slideNoAr : -1
            onBuscar: (q) => painel.buscar(q)
            onClique: (i) => { painel.abrir(i); controle.projetar(i, 0) }        // selecionarLouvor: escolhe e projeta
            onDuplo: (i) => { painel.abrir(i); if (controle.addLouvor(i)) toast.mostrar("Adicionado à lista de projeção.") }
            onTela: (k) => controle.projetar(painel.escolhido, k)
            onTelaDuplo: (k) => { if (controle.addLouvor(painel.escolhido)) toast.mostrar("Adicionado à lista de projeção.") }
            onTeclaEnter: if (painel.listaLouvores.length) { var i = painel.listaLouvores[0].i; painel.abrir(i); controle.projetar(i, 0); vLouvor.busca.campo.focus = false }
        }
        // BÍBLIA (livros · capítulos · versículos em grade, e a busca por trecho)
        ViewBiblia {
            id: vBiblia
            anchors.fill: parent; visible: painel.aba === 1
            onAbrirLouvor: (i) => { painel.aba = 0; painel.abrir(controle.daVez ? controle.daVez(i) : i) }   // o selecionarLouvor(i, true) + trocarAba("louvor")
            busca: controle.bibBusca("")
            noAr: controle.bibNoAr
            onBuscar: (q) => {
                busca = controle.bibBusca(q)
                var r = busca.ref
                if (r) {
                    if (livro !== r.livro) { livro = r.livro; nCaps = controle.bibCaps(r.livro) }
                    cap = r.cap; versos = controle.bibVers(r.livro, r.cap); alvoV = r.v ? r.v : -1
                } else alvoV = -1
            }
            onEscolherLivro: (n) => { livro = n; cap = 0; nCaps = controle.bibCaps(n); versos = [] }
            onEscolherCap: (c) => { cap = c; versos = controle.bibVers(livro, c) }
            onProjetar: (l, c, v) => controle.projetarVerso(l, c, v)
            onGuardar: (l, c, v) => controle.guardarVersoRef(l, c, v)
            Connections {
                target: controle
                function onFilaMudou() { if (vBiblia.livro && vBiblia.cap) vBiblia.versos = controle.bibVers(vBiblia.livro, vBiblia.cap) }
            }
        }
        // TIMER · RELÓGIO · TEXTO & AVISOS (os cards)
        ViewCards {
            id: vCards
            anchors.fill: parent; visible: painel.aba >= 2 && painel.aba <= 4
            qual: ["timer", "relogio", "texto"][painel.aba - 2] || "timer"
            timerInfo: controle.timerInfo
            avisos: { painel.aba; return controle.avisosProntos() }         // refeitos ao abrir (o "próximo culto" muda com a hora)
            lisos: { painel.estiloAtual; return controle.fundosLisos() }     // o fundo liso e o da Bíblia são do estilo
            fundoTexto: lisos.length ? lisos[0].arquivo : ""
            textoNoAr: controle.vivoTipo === "texto"
            onIniciarTimer: (m, r) => controle.cronometro(m, r)
            onPausarTimer: controle.pausarTimer()
            onPararTimer: controle.pararTimer()
            onProjetarRelogio: controle.relogio()
            onProjetarTexto: (t, c, f, i) => controle.projetarTexto(t, c, f, i)
            onEscolherFundo: (a) => vCards.fundoTexto = a
            onRecado: (m) => toast.mostrar(m)
        }
        // APRESENTAÇÕES: DENTRO de uma apresentação (o MODO APRESENTAÇÃO #apr da 3.0.13)
        ViewApr {
            id: vApr; objectName: "apres"
            anchors.fill: parent; visible: painel.aba === 5 && controle.apresAberta !== ""
            focus: visible
            nome: controle.apresAberta
            pos: controle.slideApres
            passo: controle.passoApres
            preto: controle.vivoTipo === "preto"
            Keys.onPressed: (e) => vApr.tecla(e)
            Keys.onReleased: (e) => { if (!e.isAutoRepeat) controle.soltou() }     // anti-queima-roupa: soltou, para
            Connections { target: controle; function onApresMudou() { vApr.slides = controle.slidesApres(); var b = controle.painelB(); vApr.louvores = b.louvores; vApr.gestos = b.gestos } }
            onNomeChanged: if (nome !== "") {              // entrarApresentacao: a coluna fixada ou não (icm_ap_fixa2), a busca limpa
                slides = controle.slidesApres()
                var b = controle.painelB(); louvores = b.louvores; gestos = b.gestos
                fixa = controle.cfgLer("icm_ap_fixa2", false) === true
                escondida = !fixa; porMouse = false; num = ""; busca = ({ achados: [], sem: "", busca: false })
                Qt.callLater(vApr.forceActiveFocus)
            }
            onSair: controle.sairApresentacao()
            onProjetar: (k) => controle.projetarSlide(k)
            onPassar: (d) => { if (preto) controle.projetarSlide(Math.max(0, pos)); else if (d > 0) controle.proximo(); else controle.anterior() }
            onAlternarPreto: preto ? controle.projetarSlide(Math.max(0, pos)) : controle.preto()
            onBuscar: (q) => vApr.busca = controle.buscarSlides(q)
            onGravarFixa: (v) => controle.cfgGravar("icm_ap_fixa2", v)
            // a faixa de baixo: os mesmos estados e ações do #painel
            projetando: painelDir.projetando
            noArTelao: painelDir.noAr
            congelado: controle.congeladoAgora
            tamRotulo: controle.rotuloTamanho || "Padrão"
            onProjetarClique: painelDir.projetarClique()
            onCongelar: controle.congelar(!controle.congeladoAgora)
            onMenor: controle.tamanho(-1)
            onMaior: controle.tamanho(1)
            onPadrao: controle.tamanho(0)
            onProcurarTelas: controle.procurarTelas()
        }
        // APRESENTAÇÕES: a grade (renderApresentacoes)
        ViewGrade {
            id: vApres
            anchors.fill: parent; visible: painel.aba === 5 && controle.apresAberta === ""
            tipo: "apres"
            itens: []
            Connections { target: controle; function onApresMudou() { vApres.itens = controle.apresentacoes() } }
            Connections { target: painel; function onAbaChanged() { if (painel.aba === 5) vApres.itens = controle.apresentacoes() } }
            onClique: (i) => controle.entrarApresentacao(i, 0)
            onDuplo: (i) => controle.entrarApresentacao(i, 0)
            onApagar: (i) => { avApagarAp.k = i; avApagarAp.info = controle.sobreApres(i); avApagarAp.abrir() }
            onAdicionar: abrirApGrade.open()
        }
        FileDialog {
            id: abrirApGrade; title: "Abrir apresentação"
            nameFilters: ["Apresentações (*.pptx *.ppt *.pps *.ppsx *.odp *.pdf)", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp)"]
            onAccepted: controle.importarApresentacao(selectedFile.toString())
        }
        // FUNDOS: a galeria (renderFundos)
        ViewGrade {
            id: vFundos
            anchors.fill: parent; visible: painel.aba === 6
            tipo: "fundos"
            itens: { painel.escondidosAtual; painel.estiloAtual; return controle.fundos() }
            categorias: { painel.estiloAtual; return controle.categoriasFundo() }
            noAr: controle.fundoNoAr
            Connections { target: controle; function onEsperaMudou() { vFundos.itens = controle.fundos(); vFundos.categorias = controle.categoriasFundo() } }
            onClique: (i) => { controle.projetarFundo(i); toast.mostrar("Fundo: " + (controle.sobreFundo(i).nome || "")) }
            onDuplo: (i) => { controle.definirEspera(i); toast.mostrar("★ Tela de espera: " + (controle.sobreFundo(i).nome || "")) }
            onEspera: (i) => { controle.definirEspera(i); toast.mostrar("Tela de espera: " + (controle.sobreFundo(i).nome || "")) }
            onApagar: (i) => { avApagarFundo.k = i; avApagarFundo.info = controle.sobreFundo(i); avApagarFundo.abrir() }
            onAdicionar: { addNome.text = ""; avAddFundo.arquivo = ""; avAddFundo.abrir() }
        }
    }

    // ---------------- o <aside id="painel"> (direita, sempre visível)
    PainelDireito {
        id: painelDir
        x: parent.width - width; y: cab.height
        width: 348; height: parent.height - y
        projetando: !controle.semProjetor && !controle.telaoFechado
        modoApr: painel.aba === 5 && controle.apresAberta !== ""     // o "Painel B" (body.pb-on) da 3.0.13
        congelado: controle.congeladoAgora
        vivo: controle.vivoTipo
        agora: controle.agora
        tamRotulo: controle.rotuloTamanho || "Padrão"
        temCifra: painel.escolhido >= 0 && controle.temCifra(painel.escolhido)
        cifraOn: painel.cifraAberta
        temAnim: painel.escolhido >= 0 && controle.temAnimacao(painel.escolhido)
        animOn: controle.animacao
        fila: painel.fila
        posLista: controle.posLista
        previa: Palco { id: previa; objectName: "previaPalco"; previa: true; anchors.fill: parent }
        onProjetarClique: {
            if (!projetando) { controle.mostrarAvisoProjetor(); return }
            if (noAr) { controle.descanso(); toast.mostrar("Tela de espera no telão."); return }
            controle.projetarSelecaoAtual(painel.escolhido)    // o projetarSelecaoAtual da 3.0.13 (B8: não pula para o louvor)
        }
        onAnterior: controle.anterior()
        onProximo: controle.proximo()
        onCongelar: controle.congelar(!controle.congeladoAgora)
        onMenor: controle.tamanho(-1)
        onMaior: controle.tamanho(1)
        onPadrao: controle.tamanho(0)
        onProcurarTelas: controle.procurarTelas()
        onCifra: painel.cifraAberta ? painel.fecharCifra() : painel.abrirCifra(painel.escolhido)
        onAnimacao: { controle.ligarAnimacao(!controle.animacao); if (painel.escolhido >= 0) painel.telasDoLouvor = controle.telasLouvor(painel.escolhido) }
        onLimpar: controle.limparLista()
        onIrPara: (i) => controle.irPara(i)
        onMover: (i, d) => controle.mover(i, d)
        onTirar: (i) => controle.tirar(i)
        onMarcar: (i) => controle.marcar(i)
        onArrastar: (de, para) => controle.arrastar(de, para)
    }

    // ---------------- os AVISOS (o confirmar() e o mostrarAddFundo() da 3.0.13): cobrem a janela inteira
    }   // fim do fundoApp

    // a FOLHA DA CIFRA (o #cifra-ov da 3.0.13): por cima da janela inteira, com o app desfocado atrás
    CifraFolha {
        id: cifraFolha
        fundo: fundoApp
        pn: painel
    }

    // o MENU ☰, as BOAS-VINDAS e os ASSISTENTES nascem DEPOIS da subida (08/11/2026): no Vaio (E-450) montar os cinco junto
    // com o painel custava ~1,9 s da abertura (MenuCfg sozinho 1,08 s). Um por vez, em segundo plano (Loader assíncrono),
    // logo depois de o painel aparecer; quem for usado antes de pronto termina de montar na hora (pegar). Nas provas
    // (modoFotos) nascem já de saída, como antes.
    function pegar(l) { if (!l.item) { l.asynchronous = false; l.active = true } return l.item }
    function vis(l) { return !!l.item && l.item.visible }
    readonly property var carregarDepois: [bemVindoL, menuCfgL, assistSobreL, assistAtualizarL, assistPassosL]
    Timer {
        interval: 350; repeat: true; running: !modoFotos
        onTriggered: {
            for (var i = 0; i < painel.carregarDepois.length; i++) {
                var l = painel.carregarDepois[i]
                if (!l.active) { l.asynchronous = true; l.active = true; return }
                if (l.status === Loader.Loading) return          // um de cada vez
            }
            stop()
        }
    }
    // o MENU ☰ (Configurações): o véu e a gaveta da 3.0.13
    Loader {
        id: menuCfgL; anchors.fill: parent; active: modoFotos
        sourceComponent: Component {
            MenuCfg {
                objectName: "menu"
                function abrirComIgreja() { igreja = (controle.cfgLer("icm_igreja", {}) || {}).nome || ""; abrir() }
                onCopiado: toast.mostrar("Endereço copiado.")
                onSalvouIgreja: toast.mostrar("Dados da igreja salvos.")
                onRecado: (t) => toast.mostrar(t)
                onAbrirAssistente: (n) => { if (n === "sobre") painel.pegar(assistSobreL).abrir(); else if (n === "atualizar") painel.pegar(assistAtualizarL).abrir(); else painel.pegar(assistPassosL).iniciar(n) }
                onRever: painel.pegar(bemVindoL).abrir()
            }
        }
    }
    // as BOAS-VINDAS ("Como funciona"): na 1ª vez abre sozinha (icm_bemvindo_ok, a mesma chave da 3.0.13)
    Loader {
        id: bemVindoL; anchors.fill: parent; active: modoFotos
        sourceComponent: Component {
            BemVindo {
                objectName: "bemVindo"
                fundo: fundoApp
                onPronto: toast.mostrar("Tudo pronto. Que Deus abençoe o culto.")
                Component.onCompleted: if (typeof primeiraVez !== "undefined" && primeiraVez) Qt.callLater(abrir)
            }
        }
    }
    Loader {
        id: assistAtualizarL; anchors.fill: parent; active: modoFotos
        sourceComponent: Component { AssistAtualizar { objectName: "assistAtualizar"; onRecado: (t) => toast.mostrar(t) } }
    }
    Loader {
        id: assistPassosL; anchors.fill: parent; active: modoFotos
        sourceComponent: Component { AssistPassos { objectName: "assistPassos"; onRecado: (t) => toast.mostrar(t) } }
    }
    Loader {
        id: assistSobreL; anchors.fill: parent; active: modoFotos
        sourceComponent: Component {
            AssistSobre {
                objectName: "assistSobre"
                onRever: { painel.pegar(menuCfgL).fechar(); painel.pegar(bemVindoL).abrir() }
                onCopiado: (t) => toast.mostrar(t)
            }
        }
    }
    Aviso {
        id: avApagarFundo; objectName: "dialogoApagarFundo"
        property int k: -1
        property var info: ({})
        largura: 430; titulo: "Confirmar"
        mensagem: info.meu ? "Apagar <b>" + (info.nome || "este fundo") + "</b>?<br><br>Ele foi você que adicionou — some de vez, e só volta se você adicionar de novo."
                           : "Esconder <b>" + (info.nome || "este fundo") + "</b>?<br><br>Ele veio com o Sistema, então não some de verdade: volta em Configurações › Sistema › Restaurar › <b>Fundos</b>."
        botoes: [{ texto: info.meu ? "Sim, apagar" : "Sim, esconder", sels: [".big-btn", ".big-btn.vermelho"], nome: "confirmaApagarFundo" },
                 { texto: "Cancelar", sels: [".big-btn"] }]
        onBotao: (i) => { if (i === 0) controle.apagarFundo(k); fechar() }
    }
    Aviso {
        id: avApagarAp; objectName: "dialogoApagarApres"
        property int k: -1
        property var info: ({})
        largura: 430; titulo: "Confirmar"
        mensagem: info.demo ? "Esconder <b>" + (info.nome || "") + "</b>?<br><br>Ela veio com o Sistema, então não some de verdade: volta em Configurações › Sistema › Restaurar."
                            : "Apagar <b>" + (info.nome || "") + "</b>?<br><br>Foi você que trouxe — some de vez, e só volta se você abrir o arquivo de novo."
        botoes: [{ texto: info.demo ? "Sim, esconder" : "Sim, apagar", sels: [".big-btn", ".big-btn.vermelho"], nome: "confirmaApagarApres" },
                 { texto: "Cancelar", sels: [".big-btn"] }]
        onBotao: (i) => { if (i === 0) { controle.apagarApres(k); vApres.itens = controle.apresentacoes() } fechar() }
    }
    Aviso {
        id: avAddFundo; objectName: "dialogoAddFundo"
        property string arquivo: ""
        titulo: "Adicionar fundo"; mensagem: "Escolha uma imagem (de preferência larga, 16:9) e dê um nome."
        botoes: [{ texto: "Adicionar", sels: [".big-btn", ".big-btn.verde"] }, { texto: "Cancelar", sels: [".big-btn"] }]
        onBotao: (i) => {
            if (i === 1) { fechar(); return }
            if (!arquivo) { toast.mostrar("Selecione uma imagem."); return }
            if (controle.adicionarFundo(arquivo, addNome.text)) fechar()
        }
        // .add-form: o arquivo, o nome e a prévia
        Column {
            width: parent.width; spacing: 10
            Row {
                spacing: 8
                Caixa { sels: [".big-btn"]; texto: "Escolher arquivo"; onClicado: escolherFundo.open() }
                Letra { anchors.verticalCenter: parent.verticalCenter; px: 13; color: "#cdd9ee"
                        text: avAddFundo.arquivo ? decodeURIComponent(avAddFundo.arquivo.split("/").pop()) : "Nenhum arquivo escolhido" }
            }
            Entrada { id: addNome; objectName: "addNome"; width: parent.width; navegador: false; sels: ["input[type=text]"]
                      placeholder: "Nome do fundo (ex.: Aviso, Ceia, Batismo…)" }
            Image { visible: !!avAddFundo.arquivo; source: avAddFundo.arquivo; width: parent.width; height: width * 9 / 16
                    fillMode: Image.PreserveAspectCrop; sourceSize.width: 480; asynchronous: true }
            Item { width: 1; height: 6 }
        }
    }
    FileDialog {
        id: escolherFundo; title: "Escolha a imagem do fundo"
        nameFilters: ["Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.gif)"]
        onAccepted: { avAddFundo.arquivo = selectedFile.toString()
                      if (!addNome.text) addNome.text = decodeURIComponent(avAddFundo.arquivo.split("/").pop()).replace(/\.[^.]+$/, "") }
    }

    // ---------------- o #toast (o recado curto): embaixo, no meio, some sozinho
    Rectangle {
        id: toast
        readonly property var s: T.estilo(["#toast"], false)
        function mostrar(m) { toastTxt.text = m; opacity = 1; toastFim.restart() }
        z: 99; opacity: 0; visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 300 } }
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: s.bottom }
        width: toastTxt.implicitWidth + s.padding[1] + s.padding[3]; height: toastTxt.implicitHeight + s.padding[0] + s.padding[2]
        radius: s["border-radius"]; color: s.background
        Letra { id: toastTxt; objectName: "recado"; x: toast.s.padding[3]; y: toast.s.padding[0]; px: toast.s["font-size"]; color: T.V.txt }
        Timer { id: toastFim; interval: 1800; onTriggered: toast.opacity = 0 }
    }

    // ---- "Projetor não encontrado" (o esperarProjetor da 3.0.12/3.0.13, palavra por palavra, 08/11/2026): a .ajuda-box com a
    // aura dourada (.pj-aura), as teclas desenhadas (o kbd do Windows com o logo e o kbd P) e os dois .big-btn (o 1º .ouro).
    // Antes era feito à mão (letra do sistema, botão branco, "Windows + P" escrito). Abre quando o operador põe algo no ar
    // com uma tela só; quando a 2ª tela aparece, o telão vai para ela e isto fecha. O véu NÃO fecha (como lá); o Esc fecha.
    Aviso {
        id: veuProj; objectName: "avisoProjetor"
        visible: controle.avisoProjetor
        titulo: "Projetor não encontrado"; largura: 430; aura: true; fechaNoVeu: false
        readonly property var pp: T.estilo([".ajuda-box p"], false)
        readonly property var pb: T.estilo([".ajuda-box b"], false)
        readonly property real alturaLinha: pp["font-size"] * pp["line-height"]
        readonly property real espaco: medeEsp1.implicitWidth - medeEsp0.implicitWidth   // a largura de um espaço da letra
        function negrito(s) { return s.split("<b>").join("<b><font color=\"" + pb.color + "\">").split("</b>").join("</font></b>") }
        botoes: [{ texto: procurando.running ? "Procurando…" : "Procurar novamente", sels: [".big-btn", ".big-btn.ouro"], nome: "procurarProjetor" },
                 { texto: "Continuar assim", sels: [".big-btn"], nome: "continuarAssim" }]
        onBotao: (i) => { if (i === 0) { if (!procurando.running) { procurando.start(); controle.procurarProjetor() } }
                          else controle.continuarAssim() }
        Timer { id: procurando; interval: 1500 }
        Letra { id: medeEsp0; visible: false; px: veuProj.pp["font-size"]; text: "xx" }
        Letra { id: medeEsp1; visible: false; px: veuProj.pp["font-size"]; text: "x x" }
        Letra {
            width: parent.width; quebra: Text.WordWrap; px: veuProj.pp["font-size"]; color: veuProj.pp.color; linha: veuProj.pp["line-height"]
            text: "Conecte o cabo do projetor (HDMI) ao computador."
        }
        Item { width: 1; height: veuProj.pp["margin-bottom"] }
        // "No teclado, pressione [Windows] + [P] e escolha Estender.": palavra por palavra, quebrando como o navegador; a
        // linha das teclas fica da altura delas (o navegador cresce a linha), as outras na altura normal do parágrafo
        Flow {
            id: fluxoTeclas
            width: parent.width; spacing: veuProj.espaco
            Repeater {
                model: ["No", "teclado,", "pressione", "#teclas", "e", "escolha", "<b>Estender</b>."]
                Item {
                    readonly property bool ehTeclas: modelData === "#teclas"
                    width: ehTeclas ? teclas.width : palavra.implicitWidth
                    height: Math.abs(y - fluxoTeclas.yTeclas) < 1 ? fluxoTeclas.hTeclas : veuProj.alturaLinha
                    Row {
                        id: teclas; visible: parent.ehTeclas; anchors.verticalCenter: parent.verticalCenter
                        anchors.verticalCenterOffset: 1
                        spacing: T.estilo([".teclas"], false).gap
                        Component.onCompleted: if (parent.ehTeclas) { fluxoTeclas.itemTeclas = parent; fluxoTeclas.hTeclas = Qt.binding(() => height - 3) }
                        Tecla { win: true; texto: "Windows" }
                        Letra { anchors.verticalCenter: parent.verticalCenter; text: "+"; px: veuProj.pp["font-size"]
                                color: T.estilo([".teclas .mais"], false).color; weight: 600 }
                        Tecla { texto: "P" }
                    }
                    Letra {
                        id: palavra; visible: !parent.ehTeclas; anchors.verticalCenter: parent.verticalCenter
                        textFormat: Text.StyledText; px: veuProj.pp["font-size"]; color: veuProj.pp.color
                        text: parent.ehTeclas ? "" : veuProj.negrito(modelData)
                    }
                }
            }
            property Item itemTeclas: null
            property real hTeclas: veuProj.alturaLinha
            readonly property real yTeclas: itemTeclas ? itemTeclas.y : -100
        }
        Item { width: 1; height: veuProj.pp["margin-bottom"] }
        Letra {
            width: parent.width; quebra: Text.WordWrap; textFormat: Text.StyledText
            px: veuProj.pp["font-size"]; color: veuProj.pp.color; linha: veuProj.pp["line-height"]
            text: veuProj.negrito("Depois, clique em <b>Procurar novamente</b> — a projeção será enviada automaticamente.")
        }
        Item { width: 1; height: T.estilo([".ajuda-box p:last-of-type"], false)["margin-bottom"] }
    }
    // ---- 13/11: ao abrir, OUTRO SISTEMA já está nesta rede (o ouvido da abertura, seguir.Ouvido): o mesmo cartão das
    // duas telas, do outro lado. "Ser a tela secundária" reabre este computador como a tela de retorno daquele.
    Rectangle {
        id: veuOutro; objectName: "cartaoOutroSistema"
        anchors.fill: parent; z: 19; color: "#8c050a14"
        visible: controle.outroPrincipal !== ""
        MouseArea { anchors.fill: parent; onClicked: controle.ficarPrincipal() }
        MouseArea { anchors.centerIn: parent; width: cartaoOutro.width; height: cartaoOutro.height }   // o clique no cartão não fecha
        CartaoOutroSistema {
            id: cartaoOutro
            anchors.centerIn: parent; width: Math.min(470, parent.width - 40)
            nome: controle.outroPrincipal
            onSim: controle.virarSecundaria()
            onNao: controle.ficarPrincipal()
        }
    }
    // ---- o cartão das DUAS TELAS (dtCartao da 3.0.12, as palavras dele de 18/10): "Nova tela encontrada" (pergunta) e
    // "Como usar as duas telas?" (como: 1 Telão / 2 Tela de retorno, três desenhos sem palavras, Trocar e Pronto).
    // Clicar no véu ou Esc fecha SEM responder (a pílula continua oferecendo).
    Rectangle {
        id: veuTelas; objectName: "cartaoTelas"
        readonly property var c: controle.cartaoTelas
        anchors.fill: parent; z: 19; color: "#8c050a14"
        visible: c.modo !== ""
        MouseArea { anchors.fill: parent; onClicked: controle.fecharCartaoTelas() }
        Rectangle {
            anchors.centerIn: parent
            width: Math.min(470, parent.width - 40); height: colTelas.implicitHeight + 40; radius: 14
            // 13/11 (ele: o modo duas telas tem "essa estética de verde escuro"): a moldura do #dt-cartao da 3.0.12, que o
            // nativo tinha perdido (era #101b30 com fio azul): o fundo #1e2d49 -> #16233c e a borda verde de 2 px
            gradient: Gradient { GradientStop { position: 0; color: "#22324f" } GradientStop { position: 0.45; color: "#1b2944" } GradientStop { position: 1; color: "#16233c" } }
            border.color: "#2e8b57"; border.width: 2
            MouseArea { anchors.fill: parent }                         // o clique no cartão não fecha
            ColumnLayout {
                id: colTelas
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                spacing: 10
                Label { text: veuTelas.c.modo === "como" ? "Como usar as duas telas?" : "Nova tela encontrada"
                        color: "#f5d76e"; font.pixelSize: 19; font.bold: true }
                // pergunta
                Label { visible: veuTelas.c.modo === "pergunta"; textFormat: Text.StyledText
                        text: "O computador <b>" + veuTelas.c.nome + "</b> também está com o Sistema ICM nesta rede. Ele pode ser a tela de retorno."
                        color: "#e8eef8"; font.pixelSize: 14; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                RowLayout {
                    visible: veuTelas.c.modo === "pergunta"; Layout.fillWidth: true; Layout.topMargin: 4; spacing: 10
                    Button { objectName: "telasNao"; text: "Agora não"; Layout.fillWidth: true; focusPolicy: Qt.NoFocus; onClicked: controle.telasAcao("nao") }
                    Button {
                        id: botaoSim; objectName: "telasSim"; text: "Usar as duas telas"; Layout.fillWidth: true; focusPolicy: Qt.NoFocus
                        background: Rectangle { radius: 8; color: botaoSim.down ? "#2f8a52" : "#3aa864" }
                        contentItem: Text { text: botaoSim.text; color: "white"; font.bold: true; font.pixelSize: 14
                                            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        onClicked: controle.telasAcao("sim")
                    }
                }
                // como
                Repeater {
                    model: veuTelas.c.modo === "como" ? 2 : 0
                    RowLayout {
                        spacing: 8
                        Rectangle { width: 22; height: 22; radius: 6; color: "#14487a"; border.color: "#f5d76e"
                                    Text { anchors.centerIn: parent; text: index + 1; color: "#f5d76e"; font.bold: true; font.pixelSize: 13 } }
                        Label { textFormat: Text.StyledText; color: "#e8eef8"; font.pixelSize: 14
                                text: (index === 0 ? "Telão: " : "Tela de retorno: ") +
                                      ((index === 0) === (veuTelas.c.papel === 1) ? "<b>" + veuTelas.c.nome + "</b>" : "<b>este computador</b>") }
                    }
                }
                RowLayout {
                    visible: veuTelas.c.modo === "como"; spacing: 8; Layout.alignment: Qt.AlignHCenter
                    Repeater {
                        model: [["modo:retorno", "gesto", "O telão e, na tela de retorno, os gestos"],
                                ["modo:igual", "igual", "As duas telas iguais"],
                                ["so_telao", "apagada", "Só o telão (desliga a tela de retorno)"]]
                        Rectangle {
                            readonly property bool on: (modelData[0] === "modo:retorno" && veuTelas.c.como !== "igual") ||
                                                       (modelData[0] === "modo:igual" && veuTelas.c.como === "igual")
                            objectName: "telasOp_" + modelData[1]
                            width: 132; height: 58; radius: 10; color: on ? "#1b3a63" : "#0c1526"
                            border.color: on ? "#f5d76e" : "#33476b"; border.width: on ? 2 : 1
                            Image { anchors.centerIn: parent; source: "telas_" + modelData[1] + ".svg"; sourceSize.width: 118; sourceSize.height: 44 }
                            MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: controle.telasAcao(modelData[0])
                                        ToolTip.visible: containsMouse; ToolTip.text: modelData[2] }
                        }
                    }
                }
                RowLayout {
                    visible: veuTelas.c.modo === "como"; spacing: 14; Layout.alignment: Qt.AlignHCenter; Layout.topMargin: 2
                    // 13/11: os desenhos em traço da 3.0.12 (ICO_TROCAR e ICO_PRONTO do app.js), no lugar das letras
                    BotaoRedondo { objectName: "telasTrocar"; dica: "Trocar 1 e 2"; onClicked: controle.telasAcao("trocar")
                                   desenho: "M8 3 4 7l4 4 M4 7h16 M16 21l4-4-4-4 M20 17H4"; traco: 2.2; lado: 22 }
                    BotaoRedondo { objectName: "telasPronto"; dica: "Pronto"; verde: true; onClicked: controle.telasAcao("ok")
                                   desenho: "M20 6 9 17l-5-5"; traco: 3; lado: 24 }
                }
            }
        }
    }
    Component.onCompleted: { var t = controle.atual(); t.fade = 0; palcoTelao.mostrar(t); previa.mostrar(t) }

    // com a FOLHA DA CIFRA aberta (app.js:3668): ←/→ seguem passando o slide; espaço e PgUp/PgDn rolam a folha; Esc fecha a folha
    readonly property bool digitando: vLouvor.busca.campo.activeFocus || vBiblia.campo.campo.activeFocus || vCards.corpoAviso.campo.activeFocus || vCards.tituloAviso.campo.activeFocus || vCards.rotTimer.campo.activeFocus
    Shortcut { sequence: "Right"; context: Qt.ApplicationShortcut; enabled: !digitando; onActivated: controle.proximo() }
    Shortcut { sequences: ["PgDown", "Space"]; context: Qt.ApplicationShortcut; enabled: !digitando
               onActivated: cifraAberta ? rolarFolha(cifraFolha.lista.height * 0.9) : controle.proximo() }
    Shortcut { sequence: "Left"; context: Qt.ApplicationShortcut; enabled: !digitando; onActivated: controle.anterior() }
    Shortcut { sequence: "PgUp"; context: Qt.ApplicationShortcut; enabled: !digitando
               onActivated: cifraAberta ? rolarFolha(-cifraFolha.lista.height * 0.9) : controle.anterior() }
    function rolarFolha(d) { cifraFolha.lista.contentY = Math.max(0, Math.min(Math.max(0, cifraFolha.lista.contentHeight - cifraFolha.lista.height), cifraFolha.lista.contentY + d)) }
    Shortcut { sequence: "Up"; context: Qt.ApplicationShortcut; enabled: cifraAberta && !digitando; onActivated: rolarFolha(-cifraFonte * 2.9) }
    Shortcut { sequence: "Down"; context: Qt.ApplicationShortcut; enabled: cifraAberta && !digitando; onActivated: rolarFolha(cifraFonte * 2.9) }
    Shortcut { sequence: "Esc"; context: Qt.ApplicationShortcut; onActivated: { if (vis(bemVindoL)) { bemVindoL.item.fechar(); return } if (vis(assistSobreL)) { assistSobreL.item.fechar(); return } if (vis(assistAtualizarL)) { assistAtualizarL.item.fechar(); return } if (vis(assistPassosL)) { assistPassosL.item.fechar(); return } if (vis(menuCfgL)) { menuCfgL.item.fechar(); return } vLouvor.busca.campo.focus = false; if (controle.avisoProjetor) controle.fecharAvisoProjetor(); else if (controle.cartaoTelas.modo !== "") controle.fecharCartaoTelas(); else if (cifraAberta) fecharCifra(); else if (painel.aba === 5 && controle.apresAberta !== "") { if (vApr.num) vApr.numLimpa(); else controle.sairApresentacao() } else controle.descanso() } }
    Shortcut { sequence: "Ctrl+B"; context: Qt.ApplicationShortcut; onActivated: controle.preto() }
    // F11 = tela cheia e volta (o tela_cheia da 3.0.x, toggle_fullscreen). Relato dele 08/11: "depois de maximizar, o F11
    // NÃO enche a tela": aqui não havia F11. Volta ao que era antes (maximizada ou em janela).
    property int visAntesF11: Window.Windowed
    Shortcut { sequence: "F11"; context: Qt.ApplicationShortcut
               onActivated: { if (painel.visibility === Window.FullScreen) painel.visibility = painel.visAntesF11
                              else { painel.visAntesF11 = painel.visibility === Window.Maximized ? Window.Maximized : Window.Windowed; painel.showFullScreen() } } }
    // o TECLADO da 3.0.13 que faltava (08/11/2026; as boas-vindas já ensinavam a tecla P): ↓/↑ andam pela LISTA DE
    // PROJEÇÃO (projeta o próximo item / o anterior), +/= e − mudam o tamanho, P tela de espera, B tela preta, F congela
    function listaPasso(d) {
        var n = painel.fila.length; if (!n) return
        var p = controle.posLista
        var alvo = d > 0 ? Math.min(n - 1, (p < 0 ? -1 : p) + 1) : Math.max(0, (p < 0 ? 0 : p) - 1)
        if (alvo !== p) controle.irPara(alvo)
    }
    Shortcut { sequence: "Down"; context: Qt.ApplicationShortcut; enabled: !cifraAberta && !digitando; onActivated: listaPasso(1) }
    Shortcut { sequence: "Up"; context: Qt.ApplicationShortcut; enabled: !cifraAberta && !digitando; onActivated: listaPasso(-1) }
    Shortcut { sequences: ["+", "=", "Shift+="]; context: Qt.ApplicationShortcut; enabled: !digitando; onActivated: controle.tamanho(1) }
    Shortcut { sequence: "-"; context: Qt.ApplicationShortcut; enabled: !digitando; onActivated: controle.tamanho(-1) }
    Shortcut { sequence: "P"; context: Qt.ApplicationShortcut; enabled: !digitando; onActivated: controle.descanso() }
    Shortcut { sequence: "B"; context: Qt.ApplicationShortcut; enabled: !digitando; onActivated: controle.preto() }
    Shortcut { sequence: "F"; context: Qt.ApplicationShortcut; enabled: !digitando; onActivated: controle.congelar(!controle.congeladoAgora) }
    Shortcut { sequence: "Ctrl+F"; context: Qt.ApplicationShortcut; onActivated: { painel.aba = 0; vLouvor.busca.campo.forceActiveFocus(); vLouvor.busca.campo.selectAll() } }

    // ---- o TELÃO
    Window {
        id: telao
        objectName: "telao"
        width: modoFotos ? 1280 : 960; height: modoFotos ? 720 : 540
        // fora dos testes quem mostra é o posicionar() (nunca na cara do operador); quem carrega o QML sem o Python
        // do Sistema (as provas que montam o painel sozinhas) não define telaoEmJanela: aí nasce visível, como antes
        visible: typeof telaoEmJanela === "undefined" ? true : telaoEmJanela
        color: "black"
        title: "Sistema Nativo · telão"
        Palco { id: palcoTelao; objectName: "palcoTelao"; width: telao.width; height: telao.height; sombra: !semSombra }
        // depois do "Trocar" (o outro computador é o telão): este HDMI vira a TV de RETORNO (o papel-apoio da 3.0.12)
        Retorno {
            id: retTelao; anchors.fill: parent; z: 5; visible: controle.telaoApoio
            onVisibleChanged: if (visible) { var t = controle.atual(); t.fade = 0; retTelao.mostrar(t); retTelao.atualizar() }
        }
        // 13/11: a TELA SECUNDARIA enquanto procura o principal, espera o Sim ou reconecta (EsperaSecundaria.qml)
        EsperaSecundaria {
            objectName: "recadoSecundaria"; anchors.fill: parent; z: 8
            visible: controle.ehSecundaria && controle.textoSecundaria !== ""
            recado: controle.textoSecundaria; nome: controle.nomeSecundaria
        }
        // o "Identificar" (1 Telão / 2 Tela de retorno) por 3 s, só quando o operador aperta Sim ou Trocar
        Rectangle {
            id: identNum; objectName: "identificar"
            property int n: 1; property string rotulo: ""
            anchors.fill: parent; z: 9; color: "#8c05070d"; opacity: 0; visible: opacity > 0
            Behavior on opacity { NumberAnimation { duration: 350 } }
            Timer { id: identFim; interval: 3000; onTriggered: identNum.opacity = 0 }
            Rectangle {
                anchors.centerIn: parent; width: telao.height * 0.46; height: width; radius: telao.height * 0.06
                border.color: "#f5d76e"; border.width: telao.height * 0.007
                gradient: Gradient { GradientStop { position: 0; color: "#14487a" } GradientStop { position: 1; color: "#0f2f5e" } }
                Column {
                    anchors.centerIn: parent
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: identNum.n; color: "#f5d76e"
                           font.pixelSize: telao.height * 0.30; font.weight: Font.ExtraBold }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: identNum.rotulo; color: "#eaf0fb"
                           font.pixelSize: telao.height * 0.036; font.letterSpacing: 1 }
                }
            }
        }
        Item {
            anchors.fill: parent; focus: true
            Keys.onPressed: (e) => {
                // 13/11: na TELA SECUNDARIA as setas nao projetam (quem manda e o principal); Esc encerra o modo
                if (controle.ehSecundaria) { if (e.key === Qt.Key_Escape) controle.sairSecundaria(); else if (e.key === Qt.Key_F2) controle.projetarDaqui(); e.accepted = true; return }
                if (e.key === Qt.Key_Right || e.key === Qt.Key_PageDown || e.key === Qt.Key_Space) { controle.proximo(); e.accepted = true }
                else if (e.key === Qt.Key_Left || e.key === Qt.Key_PageUp) { controle.anterior(); e.accepted = true }
                else if (e.key === Qt.Key_Escape) { controle.descanso(); e.accepted = true }
            }
            Keys.onReleased: (e) => { if (!e.isAutoRepeat) controle.soltou() }     // anti-queima-roupa: soltou, para
        }
    }

    // ---- a TV DE RETORNO (os gestinhos): o Python põe numa 3a tela, se houver; NATIVO_RETORNO=janela abre em janela
    Window {
        id: retornoJanela
        objectName: "retorno"
        width: modoFotos ? 1280 : 960; height: modoFotos ? 720 : 540
        visible: false
        color: "#0b1526"
        title: "Sistema Nativo · retorno"
        Retorno { id: palcoRet; anchors.fill: parent }
        onVisibleChanged: if (visible) { var t = controle.atual(); t.fade = 0; palcoRet.mostrar(t); palcoRet.atualizar() }
    }
}
