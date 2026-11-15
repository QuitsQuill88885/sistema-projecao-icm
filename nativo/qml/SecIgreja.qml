// MINHA IGREJA (a <section data-sec="igreja"> da 3.0.13 + renderCultos/renderMoveis/marcarSalvo do app.js): o nome e
// o endereço, os cultos de cada dia (marcar e o horário), a Ceia e a Vigília com a data deste mês, e o Salvar.
// Grava na MESMA chave da 3.0.13 (icm_igreja: {nome, endereco, cultos: [{dia, nome, hora, on}], moveis: {ceia, vigilia}});
// marcar, a hora e a data gravam na hora (como o onchange de lá); nome e endereço só no Salvar.
// Medidas do Edge (07/11): linha 45 (padding 8 12), caixa 17, hora 79x29, data 127,5x28, dia: margem 16, h4 16 + 7.
import QtQuick
import "Tema.js" as T
import "Textos.js" as Tx

Column {
    id: sg
    property var ig: ({ nome: "", endereco: "", cultos: [], moveis: {} })
    property bool salvo: false                 // o selo "✓ Salvo automaticamente" (.ig-salvo.on)
    signal salvou()                            // o recado "Dados da igreja salvos."

    function carregar() {                      // o carregarDadosUsuario: a igreja guardada, ou os cultos de fábrica
        var g = controle.cfgLer("icm_igreja", {}) || {}
        var n = { nome: g.nome || "", endereco: g.endereco || "", moveis: g.moveis || {},
                  cultos: g.cultos && g.cultos.length ? g.cultos : Tx.CULTOS_PADRAO.map(function (c) { return Object.assign({}, c) }) }
        for (var k in g) if (!(k in n)) n[k] = g[k]          // o que a 3.0.13 guardar a mais, fica
        ig = n; nome.text = n.nome; endereco.text = n.endereco; salvo = false
        diasModelo = dias()                    // montado UMA vez: mexer num culto não refaz a lista (o foco do campo de hora fica)
    }
    function gravar() { controle.gravarIgreja(ig) }
    function marcarSalvo() { salvo = false; salvo = true; pisca.restart() }
    function mudarCulto(i, campo, v) {
        var c = ig.cultos.slice(); c[i] = Object.assign({}, c[i]); c[i][campo] = v
        var n = Object.assign({}, ig); n.cultos = c; ig = n; gravar(); marcarSalvo()
    }
    function mudarMovel(k, campo, v) {
        var m = Object.assign({}, ig.moveis || {}); m[k] = Object.assign({}, m[k] || {}); m[k][campo] = v
        var n = Object.assign({}, ig); n.moveis = m; ig = n; gravar(); marcarSalvo()
    }
    function dias() {                          // os dias que têm culto, na ordem de domingo a sábado
        var out = []
        for (var d = 0; d < 7; d++) {
            var l = []
            for (var i = 0; i < ig.cultos.length; i++) if (ig.cultos[i].dia === d) l.push(i)
            if (l.length) out.push({ dia: d, idx: l })
        }
        return out
    }
    property var diasModelo: []
    readonly property var sh4: T.estilo([".ig-dia h4"], false)
    readonly property var sl: T.estilo([".ig-linha"], false)

    // a dica
    Letra {
        readonly property var s: T.estilo([".dica"], false)
        width: sg.width; quebra: Text.WordWrap
        px: s["font-size"]; color: s.color; linha: s["line-height"]
        text: "Marque os cultos da sua igreja e o horário. O sistema usa isso para montar o aviso do dia sozinho."
    }
    Item { width: 1; height: T.estilo([".dica"], false)["margin-bottom"] }
    Entrada { id: nome; objectName: "igNome"; width: sg.width; sels: ["input[type=text]"]; navegador: false; placeholder: "Nome da igreja (ex.: ICM Iperó)" }
    Item { width: 1; height: 8 }
    Entrada { id: endereco; objectName: "igEndereco"; width: sg.width; sels: ["input[type=text]"]; navegador: false; placeholder: "Endereço (opcional)" }

    // os cultos de cada dia (.ig-dia: margem 16, h4 dourado; as linhas com margem 5 que colapsa na do próximo dia)
    Repeater {
        model: sg.diasModelo
        Column {
            id: dCol
            readonly property int n: modelData.idx.length
            width: sg.width
            Item { width: 1; height: T.estilo([".ig-dia"], false)["margin-top"] }
            Letra { px: sg.sh4["font-size"]; color: sg.sh4.color; weight: 700; lsCss: sg.sh4["letter-spacing"]; maiusculas: true
                    text: Tx.DIAS_NOME[modelData.dia] }
            Item { width: 1; height: sg.sh4["margin-bottom"] }
            Repeater {
                model: modelData.idx
                Column {
                    width: sg.width
                    readonly property int ci: modelData
                    readonly property var cul: sg.ig.cultos[ci]
                    Rectangle {
                        id: lin
                        objectName: "igLinha" + ci
                        width: sg.width; height: 45; radius: sg.sl["border-radius"]
                        color: maLin.containsMouse ? T.estilo([".ig-linha"], true).background : sg.sl.background
                        MouseArea { id: maLin; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: sg.mudarCulto(ci, "on", !cul.on) }     // o <label>: clicar na linha marca
                        MarcarChrome { x: 12; anchors.verticalCenter: parent.verticalCenter; marcada: !!cul.on }
                        Letra { x: 12 + 17 + 10; anchors.verticalCenter: parent.verticalCenter; px: sg.sl["font-size"]; color: T.V.txt
                                text: cul.nome }
                        CampoChrome { objectName: "igHora" + ci; x: lin.width - 12 - width; anchors.verticalCenter: parent.verticalCenter
                                      modo: "hora"; valor: cul.hora; onMudou: (v) => sg.mudarCulto(ci, "hora", v) }
                    }
                    // a margem de 5 da última linha do dia colapsa com os 16 do próximo (fica só a maior)
                    Item { width: 1; height: index < dCol.n - 1 ? sg.sl["margin-bottom"] : 0 }
                }
            }
        }
    }

    // Ceia e Vigília (#ig-moveis): a data deste mês e a hora; sem caixa de marcar
    Item { width: 1; height: T.estilo([".ig-dia"], false)["margin-top"] }
    Row {
        spacing: 0
        // o espaço do HTML entre "Vigília" e o <small> entra no título (por isso o " " no fim)
        Letra { id: h4m; px: sg.sh4["font-size"]; color: sg.sh4.color; weight: 700; lsCss: sg.sh4["letter-spacing"]; maiusculas: true; text: "Ceia e Vigília " }
        Item {
            readonly property var s: T.estilo([".ig-dia h4 small"], false)
            width: s["margin-left"] + pq.implicitTextWidth; height: h4m.height
            // na mesma linha de base do título (o <small> é inline)
            Letra { id: pq; x: parent.s["margin-left"]; y: h4m.ascPx - ascPx
                    px: parent.s["font-size"]; color: parent.s.color; weight: parent.s["font-weight"]; lsCss: parent.s["letter-spacing"]
                    text: "não têm dia fixo" }
        }
    }
    Item { width: 1; height: sg.sh4["margin-bottom"] }
    Repeater {
        model: [["ceia", "Ceia", "09:00"], ["vigilia", "Vigília", "22:00"]]
        Column {
            width: sg.width
            readonly property var mv: (sg.ig.moveis || {})[modelData[0]] || {}
            Rectangle {
                width: sg.width; height: 45; radius: sg.sl["border-radius"]
                color: maMv.containsMouse ? T.estilo([".ig-linha"], true).background : sg.sl.background
                MouseArea { id: maMv; anchors.fill: parent; hoverEnabled: true }
                Letra { x: 12; anchors.verticalCenter: parent.verticalCenter; px: sg.sl["font-size"]; color: T.V.txt; text: modelData[1] }
                CampoChrome { x: 12 + 74 + 10; anchors.verticalCenter: parent.verticalCenter
                              modo: "data"; valor: mv.data || ""; onMudou: (v) => sg.mudarMovel(modelData[0], "data", v) }
                CampoChrome { x: 12 + 74 + 10 + 127.5 + 10; anchors.verticalCenter: parent.verticalCenter
                              modo: "hora"; valor: mv.hora || modelData[2]; onMudou: (v) => sg.mudarMovel(modelData[0], "hora", v) }
            }
            Item { width: 1; height: index === 0 ? sg.sl["margin-bottom"] : 0 }
        }
    }
    Item { width: 1; height: 8 }
    Letra {
        readonly property var s: T.estilo([".dica"], false)
        width: sg.width; quebra: Text.WordWrap
        px: s["font-size"]; color: s.color; linha: s["line-height"]
        text: "Sem data marcada, o aviso sai só com o convite e você escreve o dia na hora."
    }
    // o rodapé: Salvar (verde) e o selo
    Item { width: 1; height: T.estilo([".ig-rodape"], false)["margin-top"] }
    Row {
        spacing: T.estilo([".ig-rodape"], false).gap
        Caixa {
            id: btSalvar
            objectName: "igSalvar"
            sels: [".big-btn", ".big-btn.verde"]; texto: "Salvar"
            onClicado: {
                var n = Object.assign({}, sg.ig); n.nome = nome.text.trim(); n.endereco = endereco.text.trim()
                sg.ig = n; sg.gravar(); sg.marcarSalvo(); sg.salvou()
            }
        }
        Row {
            id: selo
            anchors.verticalCenter: btSalvar.verticalCenter
            readonly property var s: T.estilo([".ig-salvo"].concat(sg.salvo ? [".ig-salvo.on"] : []), false)
            spacing: 0
            scale: pisca.running ? 1.04 : 1
            Behavior on scale { NumberAnimation { duration: 200 } }
            Ico { visible: sg.salvo; nome: "ok"; cor: selo.s.color; tam: selo.s["font-size"]; anchors.verticalCenter: parent.verticalCenter }
            Letra { px: selo.s["font-size"]; color: selo.s.color; weight: selo.s["font-weight"] || 400
                    text: sg.salvo ? " Salvo automaticamente" : "Alterações são salvas neste computador" }
            Timer { id: pisca; interval: 60 }
        }
    }
}
