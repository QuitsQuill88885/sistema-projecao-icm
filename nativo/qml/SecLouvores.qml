// MEUS LOUVORES (a <section data-sec="louvores"> da 3.0.13 + salvarLouvorEditor/limparEditor/renderMeus do app.js):
// o editor (nº, título, letra) e a lista dos que o operador adicionou, com ✎ (editar) e ✕ (apagar). Grava na MESMA chave
// da 3.0.13 (icm_meus_louvores); o louvor entra no fim da lista da aba Louvor, em "Meus louvores".
import QtQuick
import "Tema.js" as T

Column {
    id: sl
    property int editando: -1                 // o data-editando do botão Salvar (-1 = louvor novo)
    property var lista: []
    signal recado(string t)

    function carregar() { lista = controle.meusLouvores() }
    function limpar() { num.text = ""; titulo.text = ""; letra.text = ""; editando = -1 }
    function salvar() {
        var r = controle.salvarMeu(editando, num.text, titulo.text, letra.text)
        if (r === "Louvor salvo.") { carregar(); limpar() }
        recado(r)
    }
    function editar(i) {
        var e = controle.meuParaEditar(i)
        num.text = e.num || ""; titulo.text = e.titulo || ""; letra.text = e.letra || ""; editando = i
    }
    function apagar(i) {
        var r = controle.apagarMeu(i)
        if (editando === i) editando = -1; else if (editando > i) editando--
        carregar(); if (r) recado(r)
    }
    readonly property var sd: T.estilo([".dica"], false)
    readonly property var srow: T.estilo([".row"], false)

    // a dica (o <b> mais claro: .dica b)
    Letra {
        width: sl.width; quebra: Text.WordWrap; textFormat: Text.StyledText
        px: sl.sd["font-size"]; color: sl.sd.color; linha: sl.sd["line-height"]
        readonly property string b0: "<b><font color=\"" + T.estilo([".dica b"], false).color + "\">"
        text: "Adicione um louvor que não está na lista, ou corrija a letra de um existente. Separe os slides com "
              + b0 + "uma linha em branco</font></b>. Escreva " + b0 + "CORO</font></b>, " + b0 + "FINAL</font></b> ou "
              + b0 + "BIS</font></b> sozinho numa linha para virar rótulo amarelo."
    }
    Item { width: 1; height: sl.sd["margin-bottom"] }
    // .row: o nº (80) e o título (o resto, flex 1)
    Row {
        spacing: sl.srow.gap
        Entrada { id: num; objectName: "edNum"; width: 80; sels: ["input[type=text]"]; navegador: false; placeholder: "Nº" }
        Entrada { id: titulo; objectName: "edTitulo"; width: sl.width - 80 - sl.srow.gap; sels: ["input[type=text]"]; navegador: false
                  placeholder: "Título do louvor" }
    }
    Item { width: 1; height: sl.srow["margin-bottom"] }
    CaixaTexto {
        id: letra
        objectName: "edLetra"
        width: sl.width; height: implicitHeight
        placeholder: "CORO\nPRIMEIRA LINHA DO CORO,\nSEGUNDA LINHA.\n\nPRIMEIRA LINHA DO SEGUNDO SLIDE,\nSEGUNDA LINHA."
    }
    Item { width: 1; height: 4 + 12 }        // o <textarea> é inline (sobram 4 px embaixo) e a .row tem margin-top:12px
    Row {
        spacing: sl.srow.gap
        Caixa { objectName: "edSalvar"; sels: [".big-btn", ".big-btn.verde"]; texto: "Salvar louvor"; onClicado: sl.salvar() }
        Caixa { objectName: "edLimpar"; sels: [".big-btn"]; texto: "Limpar campos"; onClicado: sl.limpar() }
    }
    // a margem de baixo da .row (12) colapsa com a de cima do título (22)
    Item { width: 1; height: Math.max(sl.srow["margin-bottom"], 22) }
    Item {
        readonly property var s: T.estilo([".menu-h3"], false)
        width: sl.width; height: h3t.height + s["padding-bottom"] + 1
        Letra { id: h3t; px: parent.s["font-size"]; color: parent.s.color; weight: 700; lsCss: parent.s["letter-spacing"]; maiusculas: true
                text: "Louvores que você adicionou" }
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: T.V.borda }
    }
    Item { width: 1; height: 10 }
    // a lista (.ed-lista: vão 6) ou "Nenhum ainda."
    Caixa {
        visible: sl.lista.length === 0
        clicavel: false; sels: [".vazio"]; texto: "Nenhum ainda."; width: sl.width
        rotulo.italico: true
    }
    Column {
        visible: sl.lista.length > 0
        width: sl.width
        spacing: T.estilo([".ed-lista"], false).gap
        Repeater {
            model: sl.lista
            Caixa {
                id: it
                objectName: "edItem" + index
                clicavel: false; sels: [".ed-item"]; texto: ""
                width: sl.width; height: pad[0] + 24 + pad[2]
                readonly property var ss: T.estilo([".ed-item small"], false)
                Row {
                    x: it.pad[3]; anchors.verticalCenter: parent.verticalCenter
                    Letra { visible: modelData.num !== ""; px: it.tamLetra; weight: 700; color: it.ss.color; text: modelData.num }
                    Item { visible: modelData.num !== ""; width: it.ss["margin-right"]; height: 1 }
                    Letra { px: it.tamLetra; color: T.V.txt; text: (modelData.num !== "" ? " " : "") + modelData.titulo
                            largura: it.width - it.pad[1] - it.pad[3] - 60 - (modelData.num !== "" ? 40 : 0) }
                }
                Row {
                    x: it.width - it.pad[1] - width; anchors.verticalCenter: parent.verticalCenter
                    spacing: T.estilo([".ed-btns"], false).gap
                    Repeater {
                        model: [["lapis", "edit"], ["x", "x"]]
                        Caixa {
                            objectName: (modelData[1] === "x" ? "edApagar" : "edEditar") + it.indice
                            sels: [".ed-btns .fb"].concat(modelData[1] === "x" ? [".ed-btns .fb.x"] : []); texto: ""
                            Ico { anchors.centerIn: parent; nome: modelData[0]; tam: 13; cor: parent.corLetra }
                            onClicado: modelData[1] === "x" ? sl.apagar(index_item) : sl.editar(index_item)
                            readonly property int index_item: it.indice
                        }
                    }
                }
                readonly property int indice: index
            }
        }
    }
}
