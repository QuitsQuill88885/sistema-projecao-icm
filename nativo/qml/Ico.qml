// UM ÍCONE da 3.0.13 (icones.js), desenhado em VETOR na cor do lugar, como o navegador desenha o SVG: traço de 2 (em 24),
// pontas e cantos redondos, nítido em qualquer fração de pixel (nada de imagem reamostrada). Nunca emoji nem caractere.
// Os caminhos vêm do conversor (Icones.js CAMINHOS: círculo e retângulo já viram caminho; todos juntos num PathSvg só).
import QtQuick
import QtQuick.Shapes
import "Icones.js" as Ic

Item {
    id: ico
    property string nome: ""
    property color cor: "#eaf0fb"
    property real tam: 15
    width: tam; height: tam
    readonly property var def: Ic.CAMINHOS[nome] || { tipo: "S", d: [] }
    readonly property bool cheio: def.tipo === "F"
    // o navegador PINTA o SVG encaixado no pixel inteiro (o layout fica em fração; medido no Edge: ícone em x=182,48 pintado
    // em 182). Aqui o desenho anda a fração que falta, sem mexer no lugar do item na linha.
    property real fx: 0
    property real fy: 0
    function encaixar() { var p = ico.mapToItem(null, 0, 0); fx = p.x - Math.round(p.x); fy = p.y - Math.round(p.y) }
    Component.onCompleted: Qt.callLater(encaixar)
    onXChanged: Qt.callLater(encaixar)
    onYChanged: Qt.callLater(encaixar)
    Shape {
        x: -ico.fx; y: -ico.fy
        width: 24; height: 24
        transformOrigin: Item.TopLeft
        scale: ico.tam / 24
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: ico.cheio ? "transparent" : ico.cor
            strokeWidth: ico.cheio ? 0 : 2
            fillColor: ico.cheio ? ico.cor : "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: ico.def.d.join(" ") }
        }
    }
}
