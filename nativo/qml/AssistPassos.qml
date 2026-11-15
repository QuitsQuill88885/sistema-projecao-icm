// Os assistentes de PASSOS da página Sistema (o passo()/feito() do abrirAssistente da 3.0.13): "Restaurar" e
// "Desinstalar". Cada passo: o título, o texto, as opções grandes (.sis-op) e os botões à direita, com "Cancelar" (ou
// "Fechar" quando não há botão) no fim. O roteiro e os textos são os da 3.0.13, palavra por palavra.
// CASCA (decisão da HD 07/11): as ações finais (restaurar, desinstalar) só avisam; entram com prova em pasta temporária.
import QtQuick
import "Tema.js" as T

Aviso {
    id: ap
    largura: 560
    assistente: true
    property string tipo: ""                  // "restaurar" | "desinstalar"
    property var escolhas: []                 // [{rot, sub, perigo, id}]
    property var acoes: []                    // [{rot, cls, id}] (sem o Cancelar)
    signal recado(string t)

    function passo(tit, html, esc, bts) {
        titulo = tit; mensagem = html || ""; escolhas = esc || []; acoes = bts || []
        var b = acoes.map(function (o) { return { texto: o.rot, sels: [".big-btn"].concat(o.cls ? [".big-btn." + o.cls] : []), nome: "passo_" + o.id } })
        b.push({ texto: acoes.length ? "Cancelar" : "Fechar", sels: [".big-btn"], nome: "passo_cancelar" })
        botoes = b
    }
    function iniciar(t) { tipo = t; ir(t + ":inicio"); abrir() }
    function ir(id) {
        var R = "restaurar:", D = "desinstalar:"
        var voltar = { rot: "‹ Voltar", id: tipo + ":inicio" }
        switch (id) {
        case R + "inicio":
            return passo("Restaurar", "O que você quer trazer de volta?", [
                { rot: "O que foi apagado", sub: "Fundos e a apresentação de exemplo que vieram com o Sistema. O que você acrescentou fica.", id: R + "apagados" },
                { rot: "Tamanhos de letra", sub: "Volta A−/A+ ao padrão em tudo.", id: R + "tamanhos" },
                { rot: "Tudo", sub: "O Sistema volta a ser como acabou de ser instalado.", perigo: true, id: R + "tudo" }], [])
        case R + "apagados":
            return passo("Restaurar o que foi apagado", "Os fundos e a apresentação de exemplo que vieram com o Sistema e foram apagados voltam.<br><br><b>O que você acrescentou continua lá.</b>", [],
                         [voltar, { rot: "Restaurar", cls: "verde", id: "acao:apagados" }])
        case R + "tamanhos":
            return passo("Restaurar os tamanhos de letra", "Os tamanhos de louvor, Bíblia e texto voltam ao padrão (A−/A+).", [],
                         [voltar, { rot: "Restaurar", cls: "verde", id: "acao:tamanhos" }])
        case R + "tudo":
            return passo("Restaurar tudo", "Você perde o que acrescentou: os <b>louvores, fundos e apresentações</b> que trouxe, as <b>listas</b>, o <b>histórico dos cultos</b> e os <b>dados da igreja</b>. As animações, cifras e melodias ficam.", [],
                         [voltar, { rot: "Continuar", cls: "vermelho", id: R + "certeza" }])
        case R + "certeza":
            return passo("Tem certeza?", "<b>Isso não tem volta.</b> O Sistema volta a ser como acabou de ser instalado, fecha e abre sozinho.", [],
                         [{ rot: "‹ Voltar", id: R + "tudo" }, { rot: "Sim, restaurar tudo", cls: "vermelho", id: "acao:tudo" }])
        case D + "inicio":
            return passo("Desinstalar", "Antes de tirar o Sistema deste computador: o que fazer com as suas coisas?", [
                { rot: "Manter os meus arquivos", sub: "Louvores, fundos, apresentações, listas, animações e cifras ficam guardados. Uma instalação nova os encontra.", id: D + "manter" },
                { rot: "Apagar tudo", sub: "Remove o programa e as suas coisas, inclusive animações, cifras e melodias (cerca de 590 MB).", perigo: true, id: D + "apagar" }], [])
        case D + "manter":
            return passo("Desinstalar e manter os meus arquivos", "O programa e os atalhos saem deste computador. <b>As suas coisas ficam guardadas.</b> O Sistema fecha agora.", [],
                         [voltar, { rot: "Desinstalar", cls: "vermelho", id: "acao:desinstalar-manter" }])
        case D + "apagar":
            return passo("Desinstalar e apagar tudo", "Saem o programa, os atalhos <b>e</b> as suas coisas: louvores e fundos que você adicionou, apresentações, listas, histórico e as animações, cifras e melodias.", [],
                         [voltar, { rot: "Continuar", cls: "vermelho", id: D + "certeza" }])
        case D + "certeza":
            return passo("Tem certeza?", "<b>Isso não tem volta.</b> Depois, só baixando de novo ou trazendo o pendrive.", [],
                         [{ rot: "‹ Voltar", id: D + "apagar" }, { rot: "Sim, apagar tudo", cls: "vermelho", id: "acao:desinstalar-tudo" }])
        }
        if (id === "acao:apagados" || id === "acao:tamanhos") {      // o feito('Pronto', ...) da 3.0.13
            var txt = controle.restaurar(id.substr(5))
            return passo("Pronto", txt, [], [])
        }
        if (id === "acao:tudo") {                // fecha o assistente e restaura (cópia de segurança antes; reabre)
            fechar(); controle.restaurar("tudo"); return
        }
        if (id === "acao:desinstalar-manter" || id === "acao:desinstalar-tudo") {   // o feito('Desinstalando…')
            var o = controle.desinstalar(id === "acao:desinstalar-tudo")
            if (o) return passo("Desinstalando…", "O Sistema vai fechar agora. " + o, [], [])
            fechar(); return
        }
    }
    onBotao: (i) => { if (i >= acoes.length) fechar(); else ir(acoes[i].id) }

    // as opções grandes (.assist-escolhas: coluna com vão de 8; margem 4 0 16, que colapsa com os 20 do <p>)
    Column {
        visible: ap.escolhas.length > 0
        width: parent.width
        spacing: T.estilo([".assist-escolhas"], false).gap
        Repeater {
            id: repEsc
            model: ap.escolhas
            Caixa {
                id: op
                objectName: "op_" + modelData.id
                sels: [".sis-op"].concat(modelData.perigo ? [".sis-op.perigo"] : []); texto: ""
                width: parent.width; height: pad[0] + col.height + pad[2] + 2 * bw
                Column {
                    id: col
                    x: op.pad[3] + op.bw; y: op.pad[0] + op.bw
                    width: op.width - op.pad[1] - op.pad[3] - 2 * op.bw
                    spacing: op.st.gap
                    readonly property var sb: T.estilo([".sis-op b"].concat(modelData.perigo ? [".sis-op.perigo b"] : []), false)
                    readonly property var sm: T.estilo([".sis-op small"], false)
                    Letra { px: col.sb["font-size"]; weight: 700; color: col.sb.color || op.corLetra; text: modelData.rot }
                    Letra { width: col.width; quebra: Text.WordWrap; px: col.sm["font-size"]; color: col.sm.color; linha: col.sm["line-height"]
                            text: modelData.sub }
                }
                onClicado: ap.ir(modelData.id)
            }
        }
    }
    Item { visible: ap.escolhas.length > 0; width: 1; height: T.estilo([".assist-escolhas"], false).margin[2] }
}
