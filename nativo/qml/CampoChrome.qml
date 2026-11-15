// O campo de HORA e o de DATA do Chromium (<input type=time> / <input type=date>) como a 3.0.13 os mostra na
// Minha igreja (.ig-linha input[type=time|date]): fundo #0b1729, borda var(--borda), cantos 6, padding 4 8, letra 12,5
// branca. Medido no Edge: hora 79 x 29 com o relógio PRETO (o campo de hora não tem color-scheme:dark, então o ícone
// sai escuro sobre o fundo escuro); data 127,5 x 28 com o calendário CLARO (color-scheme:dark) e "dd/mm/aaaa" vazia.
// Digitar: os números com a máscara; o valor sai no formato do navegador ("19:30", "2026-11-14").
import QtQuick
import QtQuick.Shapes
import "Tema.js" as T

Rectangle {
    id: c
    property string modo: "hora"            // "hora" ou "data"
    property string valor: ""               // "19:30" / "2026-11-14" ("" = sem data)
    signal mudou(string v)
    readonly property bool ehData: modo === "data"
    width: ehData ? 127.5 : 79
    height: ehData ? 28 : 29
    radius: 6
    color: "#0b1729"
    border.width: 1; border.color: campo.activeFocus ? T.V.ouro : T.V.borda

    function mostrar(v) {                   // o valor do navegador -> o que aparece no campo
        if (!ehData) return v || "--:--"
        var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || "")
        return m ? m[3] + "/" + m[2] + "/" + m[1] : ""
    }
    function ler(t) {                       // o que foi digitado -> o valor do navegador ("" se incompleto)
        if (!ehData) {
            var h = /^(\d{2}):(\d{2})$/.exec(t)
            return h && +h[1] < 24 && +h[2] < 60 ? t : ""
        }
        var d = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(t)
        return d && +d[1] >= 1 && +d[1] <= 31 && +d[2] >= 1 && +d[2] <= 12 ? d[3] + "-" + d[2] + "-" + d[1] : ""
    }

    // o texto à mostra (a Letra: mesma regra de todo o painel)
    Letra {
        id: vis
        visible: !campo.activeFocus
        x: 9; anchors.verticalCenter: parent.verticalCenter
        px: 12.5; color: "white"
        text: c.mostrar(c.valor) || "dd/mm/aaaa"
    }
    // a digitação (só com o foco)
    TextInput {
        id: campo
        objectName: c.objectName + "_digitar"
        x: 9; anchors.verticalCenter: parent.verticalCenter
        width: c.width - 9 - 28
        opacity: activeFocus ? 1 : 0
        color: "white"; selectionColor: "#2b4a7a"
        font.family: T.FONTE.familia; font.pixelSize: Math.round(12.5 * 1.032)
        inputMask: c.ehData ? "99/99/9999;_" : "99:99;_"
        onActiveFocusChanged: if (activeFocus) { text = c.mostrar(c.valor) || ""; selectAll() }
        onEditingFinished: {
            var v = c.ler(text)
            if (v !== "" && v !== c.valor) { c.valor = v; c.mudou(v) }
        }
    }
    // o clique fica no campo (não vaza para a linha de baixo, que marcaria o culto)
    MouseArea { anchors.fill: parent; cursorShape: Qt.IBeamCursor; onPressed: campo.forceActiveFocus() }

    // o RELÓGIO (hora): círculo de 15 px e os ponteiros, preto
    Shape {
        visible: !c.ehData
        x: c.width - 26; y: (c.height - 15) / 2; width: 15; height: 15
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: "black"; strokeWidth: 1.3; fillColor: "transparent"
            PathAngleArc { centerX: 7.5; centerY: 7.5; radiusX: 6.8; radiusY: 6.8; startAngle: 0; sweepAngle: 360 }
        }
        ShapePath {
            strokeColor: "black"; strokeWidth: 1.4; fillColor: "transparent"; capStyle: ShapePath.FlatCap
            startX: 7; startY: 3.4
            PathLine { x: 7; y: 8 }
            PathLine { x: 10.2; y: 8 }
        }
    }
    // o CALENDÁRIO (data): 12 x 11, contorno arredondado claro, a faixa de cima e os pontinhos dos dias
    Item {
        visible: c.ehData
        x: c.width - 1 - 8 - 13; y: (c.height - 12) / 2; width: 12; height: 12
        Rectangle { y: 1; width: 12; height: 11; radius: 1.5; color: "transparent"; border.width: 1; border.color: "#d6d6d6" }
        Rectangle { x: 1; y: 3; width: 10; height: 1; color: "#c6c6c6" }
        Repeater {
            model: [[3, 6], [5, 6], [7, 6], [9, 6], [3, 8], [5, 8]]
            Rectangle { x: modelData[0] - 0.5; y: modelData[1] - 0.5; width: 1.4; height: 1.4; color: "#b8b8b8" }
        }
    }
}
