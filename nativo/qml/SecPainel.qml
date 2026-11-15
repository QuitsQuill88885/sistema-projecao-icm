// PAINEL DO CULTO (a <section data-sec="painel"> da 3.0.13 + abrirPainel/pintarPainel/pintarVersiculos do app.js): o que
// foi ao telão e quanto tempo, lido do MESMO historico.json. Os filtros de período (30 dias, 3 meses, 1 ano, Tudo), o
// resumo em caixinhas e as listas com a barra proporcional atrás. As contas vêm prontas do Python (painel_culto).
import QtQuick
import "Tema.js" as T

Column {
    id: sp
    property int dias: 30                       // o histDias (o filtro "Últimos 30 dias" vem ligado)
    property var d: ({ resumo: [], mais: [], tempo: [], cultos: [], vers: [], livros: [] })
    function carregar() { d = controle.painelCulto(dias) }
    onDiasChanged: carregar()

    // "Painel do culto" (<h3> sem classe: negrito, 1,17 em) e o texto (<p class="menu-p">, sem regra: a letra do body,
    // 16 px). Medido no Edge: 18,72 px / 25 de altura; 16 px em linhas de 21
    Letra { px: 16 * 1.17; weight: 700; color: T.V.txt; text: "Painel do culto" }
    Letra { width: sp.width; quebra: Text.WordWrap; px: 16; color: T.V.txt
            text: "Os louvores e a Palavra que foram ao telão, e quanto tempo cada um ficou." }
    // os filtros
    Item { width: 1; height: T.estilo([".pn-filtros"], false).margin[0] }
    Flow {
        width: sp.width; spacing: T.estilo([".pn-filtros"], false).gap
        Repeater {
            model: [[30, "Últimos 30 dias"], [90, "3 meses"], [365, "1 ano"], [0, "Tudo"]]
            Caixa { objectName: "pnFiltro" + modelData[0]; sels: [".pn-f"]; estados: sp.dias === modelData[0] ? [".pn-f.ativo"] : []
                    texto: modelData[1]; onClicado: sp.dias = modelData[0] }
        }
    }
    Item { width: 1; height: T.estilo([".pn-filtros"], false).margin[2] }
    // o resumo: caixinhas lado a lado (flex 1, mínimo 120, quebram)
    Flow {
        id: resumo
        visible: sp.d.resumo.length > 0
        width: sp.width
        readonly property real vao: T.estilo([".pn-resumo"], false).gap
        // quantas cabem por linha com o mínimo de 120, e todas da linha dividem o resto (flex: 1)
        readonly property int porLinha: Math.max(1, Math.min(sp.d.resumo.length, Math.floor((width + vao) / (120 + vao))))
        spacing: vao
        // a linha estica todas até a mais alta (flex: align-items stretch); recalculada quando uma muda
        property real alta: 0
        function recalc() {
            var m = 0
            for (var k = 0; k < repRes.count; k++) { var c = repRes.itemAt(k); if (c) m = Math.max(m, c.natural) }
            alta = m
        }
        Repeater {
            id: repRes
            model: sp.d.resumo
            Caixa {
                id: cx
                clicavel: false; sels: [".pn-cx"]; texto: ""
                width: (resumo.width - resumo.vao * (resumo.porLinha - 1)) / resumo.porLinha
                readonly property real natural: pad[0] + col.height + pad[2] + 2 * bw
                onNaturalChanged: Qt.callLater(resumo.recalc)
                Component.onCompleted: Qt.callLater(resumo.recalc)
                height: Math.max(natural, resumo.alta)
                Column {
                    id: col
                    x: cx.pad[3] + cx.bw; y: cx.pad[0] + cx.bw
                    readonly property var sb: T.estilo([".pn-cx b"], false)
                    readonly property var ss: T.estilo([".pn-cx span"], false)
                    Letra { px: col.sb["font-size"]; weight: 700; color: col.sb.color; linha: col.sb["line-height"]; text: modelData[0] }
                    // o rótulo (<span> de 11 px) quebra na largura da caixa, mas cada linha tem a altura da letra 16 do
                    // .pn-cx (21 px; o span senta na linha de base dela, 2 px abaixo do meio): medido, 2 linhas = 42
                    Item {
                        width: cx.width - cx.pad[1] - cx.pad[3] - 2 * cx.bw; height: rotCx.height
                        Letra { id: rotCx; y: 2; width: parent.width; quebra: Text.WordWrap
                                px: col.ss["font-size"]; color: col.ss.color; lsCss: col.ss["letter-spacing"]; linha: 21 / col.ss["font-size"]
                                text: modelData[1] }
                    }
                }
            }
        }
    }
    // a margem de baixo do resumo (6) COLAPSA com a de cima do primeiro título (16): fica a maior, que o título já põe

    // as cinco listas
    Repeater {
        model: [["Mais cantados", "mais", "Nada registrado neste período."],
                ["Mais tempo no telão", "tempo", "Nada registrado neste período."],
                ["Versículos mais projetados", "vers", "Nenhum versículo projetado neste período."],
                ["Livros mais usados", "livros", "Nenhum versículo projetado neste período."],
                ["Últimos cultos", "cultos", "Nada registrado neste período."]]
        Column {
            width: sp.width
            readonly property var st: T.estilo([".pn-tit"], false)
            readonly property var itens: sp.d[modelData[1]] || []
            readonly property bool numerada: modelData[1] !== "cultos"
            Item { width: 1; height: st.margin[0] }
            Letra { px: st["font-size"]; weight: 700; color: st.color; lsCss: st["letter-spacing"]; maiusculas: true; text: modelData[0] }
            Item { width: 1; height: st.margin[2] }
            Caixa { visible: itens.length === 0; clicavel: false; sels: [".pn-vazio"]; texto: modelData[2]; width: sp.width
                    rotulo.italico: true }
            Column {
                visible: itens.length > 0
                width: sp.width
                spacing: T.estilo([".pn-lista"], false).gap
                Repeater {
                    model: itens
                    Caixa {
                        id: ln
                        clicavel: false; sels: [".pn-l"]; texto: ""
                        width: sp.width; height: pad[0] + 16 + pad[2]          // 12,5 px: linha de 16 (medido: 30)
                        clip: true
                        // a barra proporcional atrás (.pn-l .bar: azul translúcido, cantos de 8)
                        Rectangle { width: ln.width * modelData.peso; height: ln.height; radius: 8; color: "#5514487a" }
                        Row {
                            x: ln.pad[3]; anchors.verticalCenter: parent.verticalCenter
                            spacing: ln.st.gap
                            readonly property var sp0: T.estilo([".pn-l .pos"], false)
                            readonly property var sv: T.estilo([".pn-l .vl"], false)
                            Letra { visible: numerada; px: parent.sp0["font-size"]; color: parent.sp0.color; largura: parent.sp0["min-width"]
                                    text: String(index + 1); anchors.verticalCenter: parent.verticalCenter }
                            Letra { id: nm; px: ln.tamLetra; color: T.V.txt; text: modelData.nome; anchors.verticalCenter: parent.verticalCenter
                                    largura: ln.width - ln.pad[1] - ln.pad[3] - (numerada ? parent.sp0["min-width"] + ln.st.gap : 0) - vl.implicitTextWidth - ln.st.gap }
                            Letra { id: vl; px: ln.tamLetra; weight: 700; color: parent.sv.color; text: modelData.vl
                                    anchors.verticalCenter: parent.verticalCenter }
                        }
                    }
                }
            }
        }
    }
}
