// A ABA BÍBLIA da 3.0.13 (<div class="view" data-aba="biblia">): à esquerda a busca e os LIVROS (ou, quando o que se
// digita não é livro, os versículos que têm aquele TRECHO); à direita os CAPÍTULOS e os VERSÍCULOS em grade.
// Livro: 1 clique abre os capítulos. Capítulo: abre os versículos. Versículo: 1 clique projeta, 2 cliques guardam na lista.
// A referência digitada ("jo 3 16") abre o livro e o capítulo sozinha e marca o versículo (alvo-busca).
import QtQuick
import QtQuick.Controls as QC
import "Tema.js" as T

Item {
    id: vb
    signal abrirLouvor(int i)                  // a sugestão: abre o louvor na aba Louvor (sem projetar)
    property string livro: ""
    property int cap: 0
    property var noAr: []                    // controle.bibNoAr: [livro, cap, v] no ar
    property var busca: ({ ref: null, livros: [], trechos: [], n: 0, porTrecho: false })
    property int alvoV: -1                   // o versículo da referência digitada
    property alias campo: campoBusca
    property var versos: []                  // controle.bibVers(livro, cap): [{v, t, naFila}]
    property int nCaps: 0
    signal buscar(string q)
    signal escolherLivro(string nome)
    signal escolherCap(int c)
    signal projetar(string livro, int cap, int v)
    signal guardar(string livro, int cap, int v)

    readonly property real wEsq: 210                    // grid-template-columns: 210px 1fr

    // 15/11 (ele na EBD): o versículo achado na busca "não vai direto pra caixa de versículos": 1 ou 2 cliques no
    // resultado também abrem o livro e o capítulo à direita, com o versículo marcado (o próximo segue dali)
    function abrirAoLado(l, c, v) {
        if (vb.livro !== l) vb.escolherLivro(l)
        if (vb.cap !== c) vb.escolherCap(c)
        vb.alvoV = v
    }
    readonly property var sCol: T.estilo([".col"], false)

    // ---- os livros (.col.col-livros)
    Rectangle {
        id: colEsq
        width: vb.wEsq; height: vb.height; color: vb.sCol.background
        Rectangle { anchors.right: parent.right; width: vb.sCol["border-right"].w; height: parent.height; color: vb.sCol["border-right"].cor }
        Rectangle {
            id: caixaBusca
            readonly property var s: T.estilo([".busca"], false)
            width: parent.width - vb.sCol["border-right"].w; height: campoBusca.height + s.padding[0] + s.padding[2]
            color: s.background
            Entrada {
                id: campoBusca; objectName: "buscaLivro"
                sels: ["input", ".busca input"]
                x: caixaBusca.s.padding[3]; y: caixaBusca.s.padding[0]
                width: parent.width - caixaBusca.s.padding[1] - caixaBusca.s.padding[3]
                placeholder: "Livro, ou um trecho do versículo…"
                onTextChanged: atraso.restart()
            }
            Timer { id: atraso; interval: 120; onTriggered: vb.buscar(campoBusca.text) }
        }
        // a referência digitada: um item só, já escolhido (1 clique projeta, 2 guardam)
        Caixa {
            id: itemRef
            visible: !!vb.busca.ref
            y: caixaBusca.height; width: parent.width - vb.sCol["border-right"].w
            sels: [".item"]; estados: [".item.sel"]; alinhar: Qt.AlignLeft; atrasoClique: true
            texto: vb.busca.ref ? vb.busca.ref.livro + " " + vb.busca.ref.cap + (vb.busca.ref.v ? ":" + vb.busca.ref.v + (vb.busca.ref.ate ? "-" + vb.busca.ref.ate : "") : "") : ""
            onClicado: if (vb.busca.ref && vb.busca.ref.v) vb.projetar(vb.busca.ref.livro, vb.busca.ref.cap, vb.busca.ref.v)
            // 2 cliques guardam; o trecho ("Atos 15:3-5", 08/11) entra inteiro, um versículo por item
            onDuploClique: if (vb.busca.ref && vb.busca.ref.v) {
                for (var v = vb.busca.ref.v; v <= (vb.busca.ref.ate || vb.busca.ref.v); v++) vb.guardar(vb.busca.ref.livro, vb.busca.ref.cap, v)
            }
        }
        ListView {
            QC.ScrollBar.vertical: BarraRolagem {}
            id: listaLivros; objectName: "listaLivros"
            visible: !vb.busca.ref && !vb.busca.porTrecho
            y: caixaBusca.height; width: parent.width - vb.sCol["border-right"].w; height: parent.height - y
            clip: true; reuseItems: true; boundsBehavior: Flickable.StopAtBounds
            model: vb.busca.livros
            delegate: Caixa {
                width: listaLivros.width
                sels: [".item"]; estados: modelData === vb.livro ? [".item.sel"] : []; alinhar: Qt.AlignLeft
                texto: modelData
                onClicado: vb.escolherLivro(modelData)
            }
        }
        // a busca por TRECHO (.busca-trecho): "N versículos encontrados" e cada um com a referência e o começo do texto
        ListView {
            QC.ScrollBar.vertical: BarraRolagem {}
            id: listaTrechos; objectName: "listaTrechos"
            // 08/11: com referência ela vem PRIMEIRO (o itemRef) e os versículos com essas palavras vêm logo abaixo
            visible: vb.busca.porTrecho || (!!vb.busca.ref && vb.busca.n > 0)
            y: caixaBusca.height + (itemRef.visible ? itemRef.height : 0); width: parent.width - vb.sCol["border-right"].w; height: parent.height - y
            clip: true; reuseItems: true; boundsBehavior: Flickable.StopAtBounds
            model: vb.busca.trechos
            header: Caixa {
                width: listaTrechos.width; clicavel: false; alinhar: Qt.AlignLeft
                sels: vb.busca.n ? [".busca-trecho .trecho-cab"] : [".vazio"]
                texto: (vb.busca.ref ? "Também com essas palavras · " : "") + (vb.busca.n ? vb.busca.n + (vb.busca.n === 1 ? " versículo encontrado" : " versículos encontrados") : "Nenhum versículo com esse trecho.")
            }
            delegate: Caixa {
                id: tr
                width: listaTrechos.width
                sels: [".item", ".item-trecho"]; atrasoClique: true
                texto: ""
                readonly property var sb: T.estilo([".item-trecho b"], false)
                readonly property var ss: T.estilo([".item-trecho small"], false)
                implicitHeight: pad[0] + refL.alturaLinha + sb["margin-bottom"] + txL.implicitHeight + pad[2] + (st["border-bottom"] ? st["border-bottom"].w : 0)
                Letra { id: refL; x: tr.pad[3]; y: tr.pad[0]; px: tr.sb["font-size"]; weight: 700; color: tr.sb.color
                        text: modelData.livro + " " + modelData.cap + ":" + modelData.v }
                Letra { id: txL; x: tr.pad[3]; y: refL.y + refL.alturaLinha + tr.sb["margin-bottom"]; width: tr.width - tr.pad[1] - tr.pad[3]
                        px: tr.ss["font-size"]; color: tr.ss.color; linha: tr.ss["line-height"]; quebra: Text.WordWrap; text: modelData.txt }
                onClicado: { vb.abrirAoLado(modelData.livro, modelData.cap, modelData.v); vb.projetar(modelData.livro, modelData.cap, modelData.v) }
                onDuploClique: { vb.abrirAoLado(modelData.livro, modelData.cap, modelData.v); vb.guardar(modelData.livro, modelData.cap, modelData.v) }
            }
        }
    }

    // ---- capítulos e versículos (.col.col-cv)
    Rectangle {
        id: colDir
        x: vb.wEsq; width: vb.width - vb.wEsq; height: vb.height; color: vb.sCol.background
        Caixa {
            id: titCaps
            width: parent.width; clicavel: false; alinhar: Qt.AlignLeft; herda: ({ "font-weight": 700 })
            sels: [".col h3", ".col-cv h3", ".col-cv h3:first-child"]
            texto: vb.livro ? vb.livro + " — Capítulos · 2 cliques projeta o versículo 1" : "Capítulos"
        }
        GradeNum {
            id: gradeCaps; objectName: "gradeCaps"
            y: titCaps.height; width: parent.width
            // #grid-caps{flex:0 0 auto;max-height:38%}
            height: Math.min(implicitHeight, colDir.height * 0.38)
            modelo: vb.nCaps
            selecionado: vb.cap
            onClique: (n) => vb.escolherCap(n)
            // pedido dele 12/11 (Vaio): "se o camarada clica duas vezes no capítulo, já chegue projetando no primeiro versículo".
            // Um clique segue só mostrando os versículos (sai na hora, sem atraso); o segundo projeta o versículo 1.
            onDuplo: (n) => { if (vb.cap !== n) vb.escolherCap(n); vb.projetar(vb.livro, n, 1) }
        }
        Caixa {
            id: titVers
            y: gradeCaps.y + gradeCaps.height
            width: parent.width; clicavel: false; alinhar: Qt.AlignLeft; herda: ({ "font-weight": 700 })
            sels: [".col h3", ".col-cv h3"]
            texto: vb.livro && vb.cap ? vb.livro + " " + vb.cap + " — 1 clique projeta · 2 cliques guarda na lista" : "Versículos"
            larguraTexto: width - pad[1] - pad[3]
        }
        Letra {
            visible: vb.versos.length === 0
            readonly property var sv: T.estilo([".vazio"], false)
            x: sv.padding[3] + 12; y: titVers.y + titVers.height + 10 + sv.padding[0]; width: parent.width - 2 * x
            text: vb.livro ? "Escolha um capítulo" : "Escolha um livro e capítulo"
            px: sv["font-size"]; color: sv.color; italico: true; quebra: Text.WordWrap; alinhamento: Text.AlignHCenter
        }
        GradeNum {
            id: gradeVers; objectName: "gradeVers"
            y: titVers.y + titVers.height; width: parent.width; height: colDir.height - y - sugB.height   // #grid-vers{flex:1}
            modelo: vb.versos
            selecionado: vb.noAr.length === 3 && vb.noAr[0] === vb.livro && vb.noAr[1] === vb.cap ? vb.noAr[2] : -1
            alvo: vb.alvoV
            onClique: (n) => vb.projetar(vb.livro, vb.cap, n)
            onDuplo: (n) => vb.guardar(vb.livro, vb.cap, n)
        }
        // as sugestões de louvor do versículo no ar (#sug: flex 0 0 auto, embaixo da grade)
        SugBiblia {
            id: sugB
            width: parent.width; y: colDir.height - height
            onAbrir: (i) => vb.abrirLouvor(i)
        }
    }
}
