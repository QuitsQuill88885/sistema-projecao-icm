// O TEXTO de uma seção do menu ☰ (Celular, Música...): os blocos que o conversor tirou do index.html (Textos.js),
// desenhados pelas regras do app.css de cada classe (.dica, .menu-h3, .mus-bloco, .cel-passos, .mus-lista).
// Margens colapsam como no navegador (vale a maior entre a de baixo de um e a de cima do próximo).
// Os pedaços "especiais" (a caixa do QR) vêm de fora: especiais = {"cel-caixa": Component}.
import QtQuick
import "Tema.js" as T

Column {
    id: tm
    property var blocos: []
    property var especiais: ({})
    readonly property string mono: typeof fonteMono === "undefined" ? "monospace" : fonteMono

    function sty(cls, extra) { return T.estilo(["." + cls + (extra ? " " + extra : "")], false) }
    function mg(s, lado) {                       // margin: [cima, dir, baixo, esq] ou margin-top/-bottom soltos
        var k = lado === 0 ? "margin-top" : "margin-bottom"
        if (typeof s[k] === "number") return s[k]
        if (s.margin && s.margin.length) return s.margin[lado === 0 ? 0 : 2]
        return 0
    }
    function margens(b) {                        // [cima, baixo] de um bloco
        if (b.t === "especial") { var e = sty(b.id); return [mg(e, 0), mg(e, 2)] }
        if (b.t === "p" && b.cls === "") return [0, 0]
        var s = sty(b.cls)
        return [b.mt !== undefined ? b.mt : mg(s, 0), mg(s, 2)]
    }
    function vao(i) {
        var m = margens(blocos[i])
        return i === 0 ? m[0] : Math.max(margens(blocos[i - 1])[1], m[0])
    }
    // o html do conversor (só <b> e <code>) no texto rico do Qt, com a cor do <b> da classe e o <code> mono com fundo
    function rico(html, corB, letra) {
        var h = html.split("<b>").join("<b><font color=\"" + corB + "\">").split("</b>").join("</font></b>")
        if (h.indexOf("<code>") < 0) return h
        var sc = T.estilo([".mus-bloco code"], false)
        var tam = Math.round(sc["font-size"] * (letra.tamReal / letra.px) * letra.ampl)
        return h.split("<code>").join("<span style=\"font-family:'" + mono + "'; font-size:" + tam + "px; color:" + sc.color
                                      + "; background-color:" + T.fundo(sc.background) + "\">&nbsp;")
                .split("</code>").join("&nbsp;</span>")
    }

    Repeater {
        model: tm.blocos
        Column {
            width: tm.width
            Item { width: 1; height: tm.vao(index) }
            Loader {
                width: tm.width
                readonly property var b: modelData
                sourceComponent: b.t === "especial" ? (tm.especiais[b.id] || null)
                               : b.t === "h3" ? cH3 : b.t === "bloco" ? cBloco : (b.t === "ol" || b.t === "ul") ? cLista : cP
            }
        }
    }
    // a margem de baixo do último (o .menu-corpo rola: ela fica dentro)
    Item { width: 1; height: tm.blocos.length ? tm.margens(tm.blocos[tm.blocos.length - 1])[1] : 0 }

    Component {
        id: cP
        Letra {
            id: lp
            readonly property var b: parent && parent.b ? parent.b : ({ t: "p", cls: "", html: "", itens: [] })
            readonly property var s: tm.sty(b.cls || "mus-bloco", b.cls ? "" : "p")
            readonly property var sb: tm.sty(b.cls || "mus-bloco", "b")
            width: parent ? parent.width : 0
            quebra: Text.WordWrap
            textFormat: b.html.indexOf("<code>") >= 0 ? Text.RichText : Text.StyledText
            px: s["font-size"]; color: s.color; linha: s["line-height"] || 0
            text: tm.rico(b.html, sb.color || "#ffffff", lp)
        }
    }
    Component {
        id: cH3
        Item {
            readonly property var b: parent && parent.b ? parent.b : ({ t: "p", cls: "", html: "", itens: [] })
            readonly property var s: tm.sty(b.cls)
            width: parent ? parent.width : 0
            height: t3.height + s["padding-bottom"] + 1
            Letra { id: t3; px: s["font-size"]; color: s.color; weight: 700; lsCss: s["letter-spacing"]; maiusculas: s["text-transform"] === "uppercase"
                    text: b.html }
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: T.V.borda }
        }
    }
    Component {
        id: cBloco
        Caixa {
            readonly property var b: parent && parent.b ? parent.b : ({ t: "p", cls: "", html: "", itens: [] })
            id: bx
            clicavel: false; sels: ["." + b.cls]; texto: ""
            width: parent ? parent.width : 0
            height: pad[0] + colB.height + pad[2] + 2 * bw
            Column {
                id: colB
                x: bx.pad[3] + bx.bw; y: bx.pad[0] + bx.bw
                width: bx.width - bx.pad[1] - bx.pad[3] - 2 * bx.bw
                Repeater {
                    model: b.itens
                    Column {
                        width: colB.width
                        readonly property bool ultimo: index === b.itens.length - 1
                        Loader {
                            width: colB.width
                            readonly property var b: modelData
                            sourceComponent: (b.t === "ol" || b.t === "ul") ? cLista : cP
                        }
                        // p:last-child sem margem; a lista guarda a dela (.mus-lista{margin:0 0 9px})
                        Item { width: 1; height: modelData.t === "p" ? (parent.ultimo ? 0 : tm.mg(tm.sty("mus-bloco", "p"), 2))
                                                                     : tm.mg(tm.sty(modelData.cls), 2) }
                    }
                }
            }
        }
    }
    Component {
        id: cLista
        Column {
            readonly property var b: parent && parent.b ? parent.b : ({ t: "p", cls: "", html: "", itens: [] })
            readonly property var sl: tm.sty(b.cls)
            readonly property var si: b.t === "ul" ? tm.sty(b.cls, "li") : sl
            readonly property var sb: tm.sty(b.cls, b.t === "ul" ? "li b" : "b").color ? tm.sty(b.cls, b.t === "ul" ? "li b" : "b") : tm.sty("mus-bloco", "b")
            readonly property real recuo: sl.margin && sl.margin[3] ? sl.margin[3] : (sl["padding-left"] || 0)
            width: parent ? parent.width : 0
            Repeater {
                model: b.itens
                Item {
                    width: parent.width; height: li.height + (index < b.itens.length - 1 ? tm.mg(si, 2) : 0)
                    Letra {
                        id: li
                        x: recuo; width: parent.width - recuo
                        quebra: Text.WordWrap; textFormat: Text.StyledText
                        px: si["font-size"]; color: si.color; linha: si["line-height"] || 0
                        text: tm.rico(modelData, sb.color || "#ffffff", li)
                    }
                    // o marcador fica FORA do texto, encostado nele (list-style-position: outside)
                    Letra {
                        visible: b.t === "ol"
                        x: recuo - implicitTextWidth; y: li.y
                        px: li.px; color: li.color; linha: li.linha; text: (index + 1) + ". "
                    }
                    Rectangle {          // o disco do <ul> (o Chromium desenha um círculo, não uma letra)
                        visible: b.t === "ul"
                        readonly property real d: Math.round(li.px * 0.36)
                        width: d; height: d; radius: d / 2; color: li.color
                        x: recuo - d - Math.round(li.px * 0.5); y: li.ascPx - Math.round(li.px * 0.32) - d / 2
                    }
                }
            }
        }
    }
}
