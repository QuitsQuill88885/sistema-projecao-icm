// UMA TECLA desenhada, como o <kbd> da .ajuda-box da 3.0.13 (o "Projetor não encontrado"): fundo escuro, borda fina com o
// pé mais grosso (border-bottom-width 2) e o texto em negrito. win = a tecla do Windows (kbd.win): o logo + "Windows".
import QtQuick
import QtQuick.Shapes
import "Tema.js" as T

Rectangle {
    id: k
    property string texto: ""
    property bool win: false
    readonly property var s: T.estilo(win ? [".ajuda-box kbd", ".ajuda-box kbd.win"] : [".ajuda-box kbd"], false)
    readonly property var sp: T.estilo([".ajuda-box kbd.win span"], false)
    readonly property real bw: s.border.w
    readonly property real bb: s["border-bottom-width"]
    readonly property real conteudoH: (win ? sp["font-size"] : s["font-size"]) * s["line-height"]
    width: 2 * bw + s.padding[1] + s.padding[3] + linha.width
    height: bw + bb + s.padding[0] + s.padding[2] + conteudoH
    radius: s["border-radius"]; color: s.border.cor
    Rectangle {
        anchors { fill: parent; leftMargin: k.bw; rightMargin: k.bw; topMargin: k.bw; bottomMargin: k.bb }
        radius: Math.max(0, k.radius - k.bw); color: k.s.background
    }
    Row {
        id: linha
        x: k.bw + k.s.padding[3]; y: k.bw + k.s.padding[0]; height: k.conteudoH
        spacing: k.win ? k.s.gap : 0
        Item {
            visible: k.win; width: 14; height: 14; anchors.verticalCenter: parent.verticalCenter
            Shape {                                   // o LOGO_WIN do app.js (viewBox 24), em 14 px, na cor do svg
                width: 24; height: 24; scale: 14 / 24; transformOrigin: Item.TopLeft
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                    strokeWidth: 0; strokeColor: "transparent"
                    fillColor: T.estilo([".ajuda-box kbd.win svg"], false).color
                    PathSvg { path: "M2.4 5.1 10.3 4v7.5H2.4zM11.4 3.85 21.6 2.4v9.1h-10.2zM2.4 12.5h7.9V20L2.4 18.9zM11.4 12.5h10.2v9.1l-10.2-1.45z" }
                }
            }
        }
        Letra {
            anchors.verticalCenter: parent.verticalCenter
            text: k.texto; color: k.s.color; weight: 700
            px: k.win ? k.sp["font-size"] : k.s["font-size"]
            lsCss: k.win ? (k.sp["letter-spacing"] || 0) : 0
        }
    }
}
